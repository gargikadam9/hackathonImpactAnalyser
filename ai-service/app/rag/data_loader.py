"""
Data loader for RAG sources.
Loads and indexes all data sources: cmdb, incidents, change_requests, architecture, runbooks, source_registry.
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent.parent / "data"


class DataLoader:
    """Loads and provides access to all RAG data sources."""

    def __init__(self):
        self.data: Dict[str, Any] = {}
        self._load_all()

    def _load_all(self):
        """Load all data sources."""
        self._load_json("cmdb", "cmdb.json")
        self._load_json("incidents", "incidents.json")
        self._load_json("change_requests", "change_requests.json")
        self._load_json("source_registry", "source_registry.json")
        self._load_markdown("architecture", "architecture.md")
        self._load_runbooks()

    def _load_json(self, key: str, filename: str):
        """Load a JSON file."""
        filepath = DATA_DIR / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                self.data[key] = json.load(f)
        else:
            self.data[key] = []
            print(f"Warning: {filename} not found at {filepath}")

    def _load_markdown(self, key: str, filename: str):
        """Load a markdown file."""
        filepath = DATA_DIR / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                content = f.read()
            self.data[key] = {
                "filename": filename,
                "content": content,
                "sections": self._parse_markdown_sections(content)
            }
        else:
            self.data[key] = {"filename": filename, "content": "", "sections": []}
            print(f"Warning: {filename} not found at {filepath}")

    def _load_runbooks(self):
        """Load all runbook markdown files."""
        runbooks_dir = DATA_DIR / "runbooks"
        self.data["runbooks"] = []
        if runbooks_dir.exists():
            for md_file in runbooks_dir.glob("*.md"):
                with open(md_file, 'r') as f:
                    content = f.read()
                service_name = md_file.stem.replace("-runbook", "").replace("-", " ")
                self.data["runbooks"].append({
                    "service": service_name,
                    "filename": md_file.name,
                    "content": content,
                    "sections": self._parse_markdown_sections(content)
                })

    def _parse_markdown_sections(self, content: str) -> List[Dict[str, str]]:
        """Parse markdown into sections."""
        sections = []
        lines = content.split('\n')
        current_section = {"title": "overview", "content": ""}
        
        for line in lines:
            if line.startswith('## '):
                if current_section["content"].strip():
                    sections.append(current_section)
                current_section = {"title": line.strip('# ').strip(), "content": ""}
            else:
                current_section["content"] += line + '\n'
        
        if current_section["content"].strip():
            sections.append(current_section)
        
        return sections

    def get_services(self) -> List[Dict[str, Any]]:
        """Get all CMDB services."""
        return self.data.get("cmdb", [])

    def get_incidents(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get all incidents."""
        incidents = self.data.get("incidents", [])
        if limit:
            return incidents[:limit]
        return incidents

    def get_change_requests(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get all change requests."""
        crs = self.data.get("change_requests", [])
        if limit:
            return crs[:limit]
        return crs

    def get_architecture(self) -> Dict[str, Any]:
        """Get architecture document."""
        return self.data.get("architecture", {"content": ""})

    def get_runbooks(self) -> List[Dict[str, Any]]:
        """Get all runbooks."""
        return self.data.get("runbooks", [])

    def get_source_registry(self) -> List[Dict[str, Any]]:
        """Get source registry."""
        return self.data.get("source_registry", [])

    def search_all(self, query: str, embedding_service=None) -> Dict[str, List]:
        """Search across all data sources."""
        results = {}
        
        # Search services
        services = self.get_services()
        if embedding_service and services:
            service_docs = [
                {"id": s["id"], "content": f"{s['name']}: {s['description']} ({s['type']})", "type": "service",
                 "name": s["name"], "criticality": s.get("criticality", "unknown")}
                for s in services
            ]
            results["services"] = embedding_service.search(query, service_docs, top_k=5)
        else:
            results["services"] = self._keyword_search(
                services, query, fields=["name", "description"]
            )

        # Search incidents
        incidents = self.get_incidents()
        if embedding_service and incidents:
            incident_docs = [
                {"id": inc["id"], "content": f"{inc['title']}: {inc['description']} (root cause: {inc.get('rootCause', 'unknown')})",
                 "type": "incident", "severity": inc.get("severity", "unknown")}
                for inc in incidents
            ]
            results["incidents"] = embedding_service.search(query, incident_docs, top_k=5)
        else:
            results["incidents"] = self._keyword_search(
                incidents, query, fields=["title", "description", "rootCause"]
            )

        # Search change requests
        crs = self.get_change_requests()
        if embedding_service and crs:
            cr_docs = [
                {"id": cr["id"], "content": f"{cr['title']}: {cr['description']} (type: {cr.get('type', 'unknown')})",
                 "type": "change_request", "status": cr.get("status", "unknown")}
                for cr in crs
            ]
            results["change_requests"] = embedding_service.search(query, cr_docs, top_k=5)
        else:
            results["change_requests"] = self._keyword_search(
                crs, query, fields=["title", "description", "justification"]
            )

        # Search runbooks
        runbooks = self.get_runbooks()
        if embedding_service and runbooks:
            rb_docs = [
                {"id": rb["service"], "content": rb["content"], "type": "runbook",
                 "service": rb["service"]}
                for rb in runbooks
            ]
            results["runbooks"] = embedding_service.search(query, rb_docs, top_k=3)
        else:
            results["runbooks"] = self._keyword_search(
                runbooks, query, fields=["service", "content"]
            )

        # Search architecture
        arch = self.get_architecture()
        if embedding_service and arch.get("content"):
            arch_docs = [
                {"id": "architecture", "content": arch["content"], "type": "architecture"}
            ]
            results["architecture"] = embedding_service.search(query, arch_docs, top_k=2)
        else:
            results["architecture"] = []
            if query.lower() in arch.get("content", "").lower():
                results["architecture"] = [{"id": "architecture", "type": "architecture"}]

        return results

    def _keyword_search(self, items: List[Dict], query: str, fields: List[str]) -> List[Dict]:
        """Simple keyword-based search fallback."""
        query_lower = query.lower()
        results = []
        for item in items:
            score = 0
            for field in fields:
                if field in item and isinstance(item[field], str):
                    if query_lower in item[field].lower():
                        score += 1
            if score > 0:
                results.append({**item, "similarity_score": score / len(fields)})
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:5]

    def get_counts(self) -> Dict[str, int]:
        """Get counts of loaded data."""
        return {
            "services": len(self.get_services()),
            "incidents": len(self.get_incidents()),
            "change_requests": len(self.get_change_requests()),
            "source_registry": len(self.get_source_registry()),
            "runbooks": len(self.get_runbooks()),
            "architecture": 1 if self.get_architecture().get("content") else 0
        }

