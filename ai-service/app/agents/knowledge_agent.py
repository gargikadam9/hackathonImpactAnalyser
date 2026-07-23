"""
Knowledge Agent - Third agent in the pipeline.
Retrieves relevant knowledge from RAG sources: architecture, runbooks, source_registry.
"""

from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.models import AgentType


class KnowledgeAgent(BaseAgent):
    """Agent responsible for retrieving relevant knowledge from documentation."""

    def __init__(self, data_loader, embedding_service=None):
        super().__init__(AgentType.KNOWLEDGE, data_loader, embedding_service)

    def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve relevant knowledge from RAG sources."""
        change_title = input_data.get("change_title", "")
        change_description = input_data.get("change_description", "")
        affected_services = context.get("dependency", {}).get("all_impacted_services", [])

        # Build search query from change info
        search_query = f"{change_title}. {change_description}"

        # Search across all RAG sources
        search_results = self.data_loader.search_all(search_query, self.embeddings)

        # Collect and rank evidence
        evidence = []
        data_sources_used = set()

        # Process architecture
        for arch in search_results.get("architecture", []):
            evidence.append({
                "source": "architecture.md",
                "type": "documentation",
                "content": arch.get("content", "")[:500],
                "relevance": arch.get("similarity_score", 0.0)
            })
            data_sources_used.add("architecture.md")

        # Process runbooks
        for rb in search_results.get("runbooks", []):
            evidence.append({
                "source": f"runbook/{rb.get('filename', rb.get('service', 'unknown'))}",
                "type": "runbook",
                "content": rb.get("content", "")[:500],
                "service": rb.get("service", "unknown"),
                "relevance": rb.get("similarity_score", 0.0)
            })
            data_sources_used.add("runbooks")

        # Process incidents
        for inc in search_results.get("incidents", []):
            evidence.append({
                "source": inc.get("id", "unknown"),
                "type": "incident",
                "content": f"{inc.get('title', '')}: {inc.get('description', '')}",
                "severity": inc.get("severity", "unknown"),
                "relevance": inc.get("similarity_score", 0.0)
            })
            data_sources_used.add("incidents.json")

        # Process change requests
        for cr in search_results.get("change_requests", []):
            evidence.append({
                "source": cr.get("id", "unknown"),
                "type": "change_request",
                "content": f"{cr.get('title', '')}: {cr.get('description', '')}",
                "status": cr.get("status", "unknown"),
                "relevance": cr.get("similarity_score", 0.0)
            })
            data_sources_used.add("change_requests.json")

        # Process services
        for svc in search_results.get("services", []):
            evidence.append({
                "source": svc.get("name", "unknown"),
                "type": "service",
                "content": f"{svc.get('name', '')}: {svc.get('description', '')}",
                "criticality": svc.get("criticality", "unknown"),
                "relevance": svc.get("similarity_score", 0.0)
            })
            data_sources_used.add("cmdb.json")

        # Sort by relevance
        evidence.sort(key=lambda x: x.get("relevance", 0), reverse=True)

        # Get LLM synthesis
        system_prompt = """You are a knowledge retrieval agent.
        Synthesize the retrieved evidence to provide actionable knowledge
        for the change impact analysis."""

        evidence_summary = "\n".join([
            f"- [{e['type']}] {e['source']}: {e.get('content', '')[:200]}"
            for e in evidence[:5]
        ])

        user_prompt = f"""
        Change: {change_title}
        Impacted Services: {affected_services}
        
        Retrieved Knowledge:
        {evidence_summary}
        """

        llm_synthesis = self._call_llm(system_prompt, user_prompt)

        result = {
            "evidence": evidence[:10],  # Top 10 evidence items
            "data_sources_used": list(data_sources_used),
            "llm_synthesis": llm_synthesis,
            "retrieved_evidence": evidence,
            "total_evidence_found": len(evidence)
        }

        return result

    def _mock_agent_response(self, prompt: str) -> str:
        return """[Mock Knowledge Retrieval]
        Retrieved from architecture.md: Payment gateway architecture and DB config
        Retrieved from runbook: Similar issue with connection pool exhaustion (inc-001)
        Retrieved from change_requests: cr-001 - Pool size upgrade completed successfully
        Knowledge Sources Used: cmdb, incidents, change_requests, architecture, runbooks
        """

