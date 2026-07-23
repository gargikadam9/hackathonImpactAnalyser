"""
Notification Agent - Sixth agent in the pipeline.
Determines teams to notify based on impacted services and change scope.
"""

from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.models import AgentType


class NotificationAgent(BaseAgent):
    """Agent responsible for determining notification targets."""

    def __init__(self, data_loader, embedding_service=None):
        super().__init__(AgentType.NOTIFICATION, data_loader, embedding_service)

    def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine which teams to notify."""
        dependency = context.get("dependency", {})
        risk = context.get("risk", {})
        impacted_details = dependency.get("impacted_details", [])
        risk_level = risk.get("risk_level", "medium")

        # Collect teams from impacted services
        teams = set()
        for svc in impacted_details:
            owner = svc.get("owner", "")
            if owner and owner.startswith("team-"):
                teams.add(owner.replace("team-", "").replace("-", " ").title())

        # Add teams based on risk level
        if risk_level in ["critical", "high"]:
            teams.add("Platform")
            teams.add("Security")
            teams.add("Infrastructure")

        # Always add operations
        teams.add("Operations")

        # Determine notification priority
        notification_priority = "immediate" if risk_level in ["critical", "high"] else "standard"

        # LLM analysis
        system_prompt = """You are a notification agent.
        Determine the appropriate teams to notify and the communication channels to use."""

        user_prompt = f"""
        Impacted Services: {[s.get('name', '') for s in impacted_details]}
        Teams to Notify: {list(teams)}
        Risk Level: {risk_level}
        Notification Priority: {notification_priority}
        """

        llm_analysis = self._call_llm(system_prompt, user_prompt)

        result = {
            "teams_to_notify": sorted(list(teams)),
            "notification_priority": notification_priority,
            "llm_analysis": llm_analysis,
            "impacted_teams_count": len(teams),
            "requires_immediate_notification": risk_level in ["critical", "high"]
        }

        return result

    def _mock_agent_response(self, prompt: str) -> str:
        return """[Mock Notification Plan]
        Teams to Notify: Payments, Platform, Orders, Operations, Security
        Notification Channel: PagerDuty + Slack #change-notifications
        Priority: High - Immediate notification required
        Message: Database configuration change affecting payment-gateway
        """

