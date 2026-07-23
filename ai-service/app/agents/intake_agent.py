"""
Intake Agent - First agent in the pipeline.
Analyzes the change request to understand scope, type, and basic info.
"""

from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.models import AgentType


class IntakeAgent(BaseAgent):
    """Agent responsible for analyzing change intake information."""

    def __init__(self, data_loader, embedding_service=None):
        super().__init__(AgentType.INTAKE, data_loader, embedding_service)

    def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the change request and extract key information."""
        change_title = input_data.get("change_title", "")
        change_description = input_data.get("change_description", "")
        change_type = input_data.get("change_type", "enhancement")
        affected_services_input = input_data.get("affected_services", [])
        priority = input_data.get("priority", "medium")

        # Use LLM or rule-based to interpret the change
        system_prompt = """You are an intake agent analyzing a change request. 
        Extract structured information about the change.
        Identify: change type category, primary service affected, scope of impact."""

        user_prompt = f"""
        Change Title: {change_title}
        Description: {change_description}
        Type: {change_type}
        Affected Services: {affected_services_input}
        Priority: {priority}
        """

        # Get LLM interpretation
        interpretation = self._call_llm(system_prompt, user_prompt)

        # Identify affected services from CMDB
        services = self.data_loader.get_services()
        matched_services = []
        for svc in services:
            svc_name_lower = svc["name"].lower()
            change_lower = (change_title + " " + change_description).lower()
            if any(word in change_lower for word in svc_name_lower.replace("-", " ").split()):
                matched_services.append(svc["name"])
            if svc["name"] in affected_services_input:
                matched_services.append(svc["name"])

        # If no services matched, use the input or a default
        if not matched_services and affected_services_input:
            matched_services = affected_services_input
        elif not matched_services:
            matched_services = ["unknown"]

        matched_services = list(set(matched_services))

        result = {
            "change_title": change_title,
            "change_description": change_description,
            "change_type": change_type,
            "priority": priority,
            "primary_services": matched_services,
            "interpretation": interpretation,
            "scope": self._determine_scope(change_type, matched_services)
        }

        return result

    def _determine_scope(self, change_type: str, services: List[str]) -> str:
        """Determine the scope of the change."""
        if len(services) > 3:
            return "enterprise-wide"
        elif len(services) > 1:
            return "multi-service"
        elif change_type == "infrastructure":
            return "infrastructure"
        else:
            return "single-service"

    def _mock_agent_response(self, prompt: str) -> str:
        """Mock response for intake agent."""
        return """[Mock Intake Analysis]
        Change Type: Enhancement
        Primary Impact: payment-gateway service
        Scope: Single-service change affecting payment processing
        Key Concern: Database configuration changes require careful migration planning
        """

