"""
Summary Agent - Seventh and final agent in the pipeline.
Generates executive summary and comprehensive analysis report.
"""

from typing import Dict, Any, List
from datetime import datetime
import uuid
import time
from app.agents.base_agent import BaseAgent
from app.models import AgentType, ChangeImpactResponse, RiskLevel


class SummaryAgent(BaseAgent):
    """Agent responsible for generating the final summary report."""

    def __init__(self, data_loader, embedding_service=None):
        super().__init__(AgentType.SUMMARY, data_loader, embedding_service)

    def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the final comprehensive analysis report."""
        intake = context.get("intake", {})
        dependency = context.get("dependency", {})
        knowledge = context.get("knowledge", {})
        incident = context.get("incident", {})
        risk = context.get("risk", {})
        notification = context.get("notification", {})
        agent_traces = context.get("agent_traces", [])
        start_time = context.get("start_time", time.time())

        # Build the final report
        analysis_id = f"analysis-{uuid.uuid4().hex[:8]}"
        mock_mode = self.provider == "mock"

        # Compile impacted services
        impacted_services = dependency.get("all_impacted_services", [])
        if not impacted_services:
            impacted_services = intake.get("primary_services", [])

        # Compile teams
        teams_to_notify = notification.get("teams_to_notify", ["Operations"])

        # Compile potential risks
        potential_risks = risk.get("potential_risks", ["Unknown risks"])

        # Compile recommended tests
        recommended_tests = risk.get("recommended_tests", ["Standard testing"])

        # Compile similar incidents
        similar_incidents = incident.get("similar_incidents", [])

        # Compile mitigation plan
        mitigation_plan = risk.get("mitigation_plan", ["Standard mitigation"])

        # Compile evidence from knowledge agent
        retrieved_evidence = knowledge.get("retrieved_evidence", [])
        data_sources_used = knowledge.get("data_sources_used", ["cmdb.json"])

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Interpreted intent
        interpreted_intent = intake.get("interpretation", input_data.get("change_title", ""))

        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            intake, dependency, risk, notification, impacted_services, mock_mode
        )

        # Build agent traces from context
        traces = []
        for trace in agent_traces:
            traces.append({
                "agent": trace.agent.value,
                "status": trace.status,
                "input": trace.input,
                "output": trace.output,
                "processingTimeMs": trace.processingTimeMs,
                "error": trace.error,
                "evidence": trace.evidence if hasattr(trace, 'evidence') else []
            })

        result = {
            "analysis_id": analysis_id,
            "risk_score": risk.get("risk_score", 0.5),
            "risk_level": risk.get("risk_level", RiskLevel.MEDIUM),
            "confidence": risk.get("confidence", 0.7),
            "impacted_services": impacted_services,
            "teams_to_notify": teams_to_notify,
            "potential_risks": potential_risks,
            "recommended_tests": recommended_tests,
            "similar_incidents": similar_incidents,
            "mitigation_plan": mitigation_plan,
            "executive_summary": executive_summary,
            "agent_traces": traces,
            "interpreted_intent": interpreted_intent,
            "retrieved_evidence": retrieved_evidence,
            "data_sources_used": data_sources_used,
            "processing_time_ms": processing_time_ms,
            "mock_mode": mock_mode
        }

        return result

    def _generate_executive_summary(self, intake: Dict, dependency: Dict,
                                      risk: Dict, notification: Dict,
                                      impacted_services: List[str],
                                      mock_mode: bool) -> str:
        """Generate an executive summary of the analysis."""
        change_title = intake.get("change_title", "Unknown change")
        risk_score = risk.get("risk_score", 0.5)
        risk_level = risk.get("risk_level", "medium")
        confidence = risk.get("confidence", 0.7)

        summary = (
            f"## Change Impact Analysis Summary\n\n"
            f"**Change:** {change_title}\n\n"
            f"**Risk Assessment:** The proposed change has been evaluated with a "
            f"risk score of **{risk_score:.2f}** ({risk_level.upper()}) "
            f"with **{confidence:.0%}** confidence.\n\n"
        )

        if impacted_services:
            summary += (
                f"**Impact Scope:** This change will impact **{len(impacted_services)}** "
                f"service(s): {', '.join(impacted_services)}.\n\n"
            )

        risk_detail = risk.get("potential_risks", [])
        if risk_detail:
            summary += "**Key Risks Identified:**\n"
            for r in risk_detail[:3]:
                summary += f"- {r}\n"
            summary += "\n"

        teams = notification.get("teams_to_notify", [])
        if teams:
            summary += f"**Teams Notified:** {', '.join(teams)}\n\n"

        if mock_mode:
            summary += (
                "\n*⚠️ This analysis was performed in **mock mode**. "
                "For AI-powered analysis, configure a provider in .env*\n"
            )

        return summary

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Override to provide specific summary generation."""
        # For summary, generate a formatted report
        return self._mock_agent_response(user_prompt)

    def _mock_agent_response(self, prompt: str) -> str:
        return """[Mock Summary]
        Analysis complete. Change impacts 3 critical services.
        Risk Score: 0.65 (HIGH) - Proceed with caution.
        Mitigation plan includes: maintenance window, staged rollout, monitoring.
        """

