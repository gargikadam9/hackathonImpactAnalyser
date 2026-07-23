"""
Risk Agent - Fifth agent in the pipeline.
Assesses risk score, confidence, and generates mitigation plan.
"""

from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.models import AgentType, RiskLevel


class RiskAgent(BaseAgent):
    """Agent responsible for risk assessment and mitigation planning."""

    def __init__(self, data_loader, embedding_service=None):
        super().__init__(AgentType.RISK, data_loader, embedding_service)

    def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk and generate mitigation plan."""
        # Gather context from previous agents
        intake = context.get("intake", {})
        dependency = context.get("dependency", {})
        knowledge = context.get("knowledge", {})
        incident = context.get("incident", {})

        change_type = intake.get("change_type", "enhancement")
        priority = intake.get("priority", "medium")
        impacted_services = dependency.get("all_impacted_services", [])
        impacted_details = dependency.get("impacted_details", [])
        similar_incidents = incident.get("similar_incidents", [])
        high_severity_count = incident.get("high_severity_count", 0)

        # Calculate risk score (0.0 to 1.0)
        risk_score = self._calculate_risk_score(
            change_type, priority, impacted_services, impacted_details,
            similar_incidents, high_severity_count
        )

        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)

        # Calculate confidence
        confidence = self._calculate_confidence(
            change_type, impacted_details, similar_incidents
        )

        # Generate potential risks
        potential_risks = self._generate_potential_risks(
            change_type, impacted_services, impacted_details, similar_incidents
        )

        # Generate recommended tests
        recommended_tests = self._generate_recommended_tests(
            change_type, impacted_services, impacted_details
        )

        # Generate mitigation plan
        mitigation_plan = self._generate_mitigation_plan(
            risk_level, change_type, impacted_services, potential_risks
        )

        # LLM analysis
        system_prompt = """You are a risk assessment agent.
        Provide a comprehensive risk analysis with specific mitigation recommendations."""

        user_prompt = f"""
        Change Type: {change_type}
        Priority: {priority}
        Risk Score: {risk_score:.2f}
        Risk Level: {risk_level}
        Impacted Services: {impacted_services}
        """

        llm_analysis = self._call_llm(system_prompt, user_prompt)

        result = {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "confidence": confidence,
            "potential_risks": potential_risks,
            "recommended_tests": recommended_tests,
            "mitigation_plan": mitigation_plan,
            "llm_analysis": llm_analysis
        }

        return result

    def _calculate_risk_score(self, change_type: str, priority: str,
                              impacted_services: List[str],
                              impacted_details: List[Dict],
                              similar_incidents: List[Dict],
                              high_severity_count: int) -> float:
        """Calculate risk score based on multiple factors."""
        score = 0.3  # Base risk

        # Change type factor
        change_type_risk = {
            "infrastructure": 0.3,
            "security": 0.25,
            "rollback": 0.15,
            "enhancement": 0.1,
            "bugfix": 0.1,
            "data": 0.15,
            "policy": 0.05,
            "research": 0.05
        }
        score += change_type_risk.get(change_type, 0.1)

        # Priority factor
        priority_risk = {"critical": 0.2, "high": 0.15, "medium": 0.1, "low": 0.05}
        score += priority_risk.get(priority, 0.1)

        # Impacted services factor
        score += min(len(impacted_services) * 0.05, 0.2)

        # Critical services factor
        critical_count = sum(
            1 for d in impacted_details if d.get("criticality") == "critical"
        )
        score += min(critical_count * 0.1, 0.2)

        # Past incidents factor
        score += min(high_severity_count * 0.1, 0.2)

        # Clamp between 0 and 1
        return min(max(score, 0.0), 1.0)

    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level from score."""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _calculate_confidence(self, change_type: str,
                              impacted_details: List[Dict],
                              similar_incidents: List[Dict]) -> float:
        """Calculate confidence in the analysis."""
        confidence = 0.7  # Base confidence

        # More info = higher confidence
        if len(impacted_details) > 0:
            confidence += 0.1
        if len(similar_incidents) > 0:
            confidence += 0.1
        if change_type in ["bugfix", "rollback"]:
            confidence += 0.1

        return min(confidence, 0.95)

    def _generate_potential_risks(self, change_type: str,
                                   impacted_services: List[str],
                                   impacted_details: List[Dict],
                                   similar_incidents: List[Dict]) -> List[str]:
        """Generate list of potential risks."""
        risks = []

        # Generic risks
        risks.append("Service disruption during deployment")
        risks.append("Rollback complexity if change fails")

        # Change type specific risks
        if change_type == "infrastructure":
            risks.append("Database connection pool exhaustion")
            risks.append("Resource utilization spikes during migration")
        elif change_type == "security":
            risks.append("Authentication/authorization regressions")
            risks.append("Certificate or key management issues")
        elif change_type == "enhancement":
            risks.append("Performance regression in new code paths")
            risks.append("API contract incompatibility with consumers")

        # Critical service risks
        for svc in impacted_details:
            if svc.get("criticality") == "critical":
                risks.append(f"Critical service '{svc['name']}' downtime impact")

        # Learn from past incidents
        for inc in similar_incidents[:2]:
            if inc.get("root_cause"):
                risks.append(f"Similar to past issue: {inc.get('root_cause', '')}")

        return risks[:8]

    def _generate_recommended_tests(self, change_type: str,
                                     impacted_services: List[str],
                                     impacted_details: List[Dict]) -> List[str]:
        """Generate test recommendations."""
        tests = []

        tests.append("Unit tests for all changed code paths")
        tests.append("Integration tests for affected service APIs")

        if len(impacted_services) > 1:
            tests.append("End-to-end tests across service boundaries")

        if any(d.get("criticality") == "critical" for d in impacted_details):
            tests.append("Chaos engineering tests for critical services")
            tests.append("Load testing to validate performance under peak traffic")

        if change_type == "infrastructure":
            tests.append("Database migration rollback testing")
            tests.append("Connection pool stress testing")
        elif change_type == "security":
            tests.append("Penetration testing for security changes")
            tests.append("Authentication flow regression testing")

        tests.append("Smoke tests in staging environment")
        tests.append("Monitoring and alerting validation tests")

        return tests[:8]

    def _generate_mitigation_plan(self, risk_level: RiskLevel,
                                    change_type: str,
                                    impacted_services: List[str],
                                    potential_risks: List[str]) -> List[str]:
        """Generate mitigation plan steps."""
        plan = []

        plan.append("Create detailed change implementation plan with rollback steps")
        
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            plan.append("Schedule change during maintenance window")
            plan.append("Obtain approval from all impacted service owners")

        plan.append("Deploy to staging environment first for validation")
        plan.append("Run full test suite including smoke and regression tests")

        if len(impacted_services) > 1:
            plan.append("Coordinate deployment sequence across services")

        for risk in potential_risks[:3]:
            plan.append(f"Mitigation: Address '{risk}'")

        plan.append("Monitor closely for 24 hours post-deployment")
        plan.append("Document lessons learned post-implementation")

        return plan[:10]

    def _mock_agent_response(self, prompt: str) -> str:
        return """[Mock Risk Assessment]
        Risk Score: 0.65 (HIGH)
        Confidence: 0.82
        Key Risks: Database connection pool exhaustion, Service disruption during migration
        Recommended Tests: Load testing, DB migration rollback test, Integration tests
        Mitigation: Production deployment during maintenance window, 3-step rollout
        """

