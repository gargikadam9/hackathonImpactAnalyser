"""
Incident Agent - Fourth agent in the pipeline.
Finds similar past incidents and learns from historical patterns.
"""

from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.models import AgentType


class IncidentAgent(BaseAgent):
    """Agent responsible for finding similar past incidents."""

    def __init__(self, data_loader, embedding_service=None):
        super().__init__(AgentType.INCIDENT, data_loader, embedding_service)

    def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Find similar past incidents based on change description."""
        change_title = input_data.get("change_title", "")
        change_description = input_data.get("change_description", "")
        affected_services = context.get("dependency", {}).get("all_impacted_services", [])

        # Search for similar incidents
        search_query = f"{change_title} {change_description} {' '.join(affected_services)}"
        all_incidents = self.data_loader.get_incidents()

        similar_incidents = []
        if self.embeddings:
            incident_docs = [
                {"id": inc["id"], "content": f"{inc['title']} {inc['description']} {inc.get('rootCause', '')}",
                 "type": "incident", "severity": inc.get("severity", ""),
                 "service": inc.get("service", ""), "resolution": inc.get("resolution", "")}
                for inc in all_incidents
            ]
            similar_incidents = self.embeddings.search(search_query, incident_docs, top_k=5)
        else:
            # Keyword fallback
            for inc in all_incidents:
                score = 0
                text = f"{inc['title']} {inc['description']} {inc.get('rootCause', '')}"
                for word in change_title.lower().split() + change_description.lower().split():
                    if word.lower() in text.lower():
                        score += 1
                if score > 0:
                    similar_incidents.append({**inc, "similarity_score": score / 10})
            
            similar_incidents.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
            similar_incidents = similar_incidents[:5]

        # Analyze patterns from similar incidents
        patterns = []
        for inc in similar_incidents:
            pattern = {
                "id": inc.get("id", ""),
                "title": inc.get("title", ""),
                "severity": inc.get("severity", ""),
                "service": inc.get("service", ""),
                "resolution": inc.get("resolution", ""),
                "root_cause": inc.get("rootCause", ""),
                "similarity_score": inc.get("similarity_score", 0)
            }
            patterns.append(pattern)

        # LLM analysis of incident patterns
        system_prompt = """You are an incident pattern analysis agent.
        Identify recurring patterns in past incidents and assess if the proposed change
        might trigger similar issues."""

        patterns_summary = "\n".join([
            f"- {p['title']} (severity: {p['severity']}, resolved via: {p['resolution']})"
            for p in patterns[:3]
        ])

        user_prompt = f"""
        Proposed Change: {change_title} - {change_description}
        Affected Services: {affected_services}
        
        Similar Past Incidents:
        {patterns_summary}
        
        Assess risk based on historical patterns.
        """

        llm_analysis = self._call_llm(system_prompt, user_prompt)

        result = {
            "similar_incidents": patterns,
            "total_similar_found": len(patterns),
            "high_severity_count": len([p for p in patterns if p.get("severity") in ["critical", "high"]]),
            "pattern_analysis": llm_analysis,
            "common_failure_patterns": self._extract_patterns(patterns)
        }

        return result

    def _extract_patterns(self, incidents: List[Dict]) -> List[str]:
        """Extract common failure patterns from incidents."""
        patterns = []
        root_causes = [inc.get("root_cause", "") for inc in incidents if inc.get("root_cause")]
        
        pattern_keywords = {
            "database": "Database configuration or connection issues",
            "memory": "Memory or resource exhaustion",
            "timeout": "Timeout or latency issues",
            "configuration": "Configuration or deployment issues",
            "network": "Network or connectivity issues"
        }
        
        for keyword, pattern_desc in pattern_keywords.items():
            if any(keyword in rc.lower() for rc in root_causes):
                patterns.append(pattern_desc)
        
        return patterns[:5]

    def _mock_agent_response(self, prompt: str) -> str:
        return """[Mock Incident Analysis]
        Found 3 similar past incidents:
        - inc-001: Payment Gateway Outage (critical) - Connection pool exhaustion
        - inc-009: Payment Refund Errors (critical) - Missing database index
        - inc-023: SSL Certificate Expiry (critical) - Certificate renewal failure
        Pattern: 2 of 3 incidents database-related. Recommend testing DB connection pooling.
        """

