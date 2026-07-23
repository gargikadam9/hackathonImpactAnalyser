"""
Tests for the full agent pipeline.
"""

import pytest
from app.pipeline import AgentPipeline
from app.models import ChangeImpactRequest


@pytest.fixture
def pipeline():
    return AgentPipeline()


class TestPipeline:
    def test_analyze_full(self, pipeline):
        """Test full pipeline execution."""
        request = ChangeImpactRequest(
            change_title="Payment Gateway Database Pool Upgrade",
            change_description="Increase database connection pool from 50 to 200",
            change_type="infrastructure",
            affected_services=["payment-gateway"],
            priority="high",
            proposed_by="team-payments",
            environment="production"
        )
        
        result = pipeline.analyze(request)
        
        # Verify all required fields
        assert result.analysisId is not None
        assert 0 <= result.riskScore <= 1.0
        assert result.riskLevel in ["low", "medium", "high", "critical"]
        assert 0 <= result.confidence <= 1.0
        assert len(result.impactedServices) > 0
        assert len(result.teamsToNotify) > 0
        assert len(result.potentialRisks) > 0
        assert len(result.recommendedTests) > 0
        assert len(result.mitigationPlan) > 0
        assert len(result.executiveSummary) > 0
        assert len(result.agentTraces) == 7  # 7 agents in pipeline
        assert result.mockMode is True  # Default mock mode

    def test_analyze_empty_services(self, pipeline):
        """Test with no affected services specified."""
        request = ChangeImpactRequest(
            change_title="Update config service",
            change_description="Configuration update for feature flags",
            change_type="enhancement",
            affected_services=[],
            priority="low"
        )
        
        result = pipeline.analyze(request)
        assert result.analysisId is not None

    def test_pipeline_agent_order(self, pipeline):
        """Test that pipeline executes agents in correct order."""
        request = ChangeImpactRequest(
            change_title="Test change",
            change_description="Test",
            change_type="bugfix",
            affected_services=["user-service"],
            priority="low"
        )
        
        result = pipeline.analyze(request)
        expected_order = ["intake", "dependency", "knowledge", "incident", "risk", "notification", "summary"]
        actual_order = [t["agent"] for t in result.agentTraces]
        assert actual_order == expected_order

    def test_classify_conversation(self, pipeline):
        result = pipeline.classify_and_respond("Hello there!")
        assert result["classification"] == "conversation"

    def test_classify_change_analysis(self, pipeline):
        result = pipeline.classify_and_respond("I need to deploy a change to the payment service")
        assert result["classification"] == "change-analysis"

    def test_get_change_types(self, pipeline):
        types = pipeline.get_change_types()
        assert len(types) == 8
        assert any(t["id"] == "infrastructure" for t in types)

    def test_get_components(self, pipeline):
        components = pipeline.get_components()
        assert len(components) > 0
        assert all("id" in c for c in components)

    def test_get_technical_details(self, pipeline):
        details = pipeline.get_technical_details()
        assert details["total_services"] > 0
        assert len(details["technologies"]) > 0

