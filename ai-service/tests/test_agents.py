"""
Tests for multi-agent pipeline.
"""

import pytest
import json

from app.rag.data_loader import DataLoader
from app.rag.embeddings import EmbeddingService
from app.agents.intake_agent import IntakeAgent
from app.agents.dependency_agent import DependencyAgent
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.incident_agent import IncidentAgent
from app.agents.risk_agent import RiskAgent
from app.agents.notification_agent import NotificationAgent
from app.agents.summary_agent import SummaryAgent
from app.models import ChangeImpactRequest


@pytest.fixture
def data_loader():
    return DataLoader()


@pytest.fixture
def embeddings():
    return EmbeddingService(provider="mock")


@pytest.fixture
def sample_input():
    return {
        "change_title": "Payment Gateway Database Pool Upgrade",
        "change_description": "Increase database connection pool from 50 to 200 to handle peak load during flash sales",
        "change_type": "infrastructure",
        "affected_services": ["payment-gateway"],
        "priority": "high",
        "proposed_by": "team-payments",
        "environment": "production"
    }


class TestIntakeAgent:
    def test_process(self, data_loader, embeddings, sample_input):
        agent = IntakeAgent(data_loader, embeddings)
        trace = agent.execute(sample_input, {})
        assert trace.status == "completed"
        assert trace.agent.value == "intake"

    def test_determine_scope(self, data_loader, embeddings):
        agent = IntakeAgent(data_loader, embeddings)
        assert agent._determine_scope("infrastructure", ["svc-001"]) == "single-service"
        assert agent._determine_scope("enhancement", ["svc-001", "svc-002"]) == "multi-service"
        assert agent._determine_scope("bugfix", ["svc-001", "svc-002", "svc-003", "svc-004"]) == "enterprise-wide"


class TestDependencyAgent:
    def test_process(self, data_loader, embeddings, sample_input):
        agent = DependencyAgent(data_loader, embeddings)
        context = {
            "intake": {"primary_services": ["payment-gateway"]}
        }
        trace = agent.execute(sample_input, context)
        assert trace.status == "completed"
        assert trace.agent.value == "dependency"


class TestKnowledgeAgent:
    def test_process(self, data_loader, embeddings, sample_input):
        agent = KnowledgeAgent(data_loader, embeddings)
        context = {
            "dependency": {"all_impacted_services": ["payment-gateway", "order-service"]}
        }
        trace = agent.execute(sample_input, context)
        assert trace.status == "completed"
        assert trace.agent.value == "knowledge"


class TestIncidentAgent:
    def test_process(self, data_loader, embeddings, sample_input):
        agent = IncidentAgent(data_loader, embeddings)
        context = {
            "dependency": {"all_impacted_services": ["payment-gateway"]}
        }
        trace = agent.execute(sample_input, context)
        assert trace.status == "completed"
        assert trace.agent.value == "incident"


class TestRiskAgent:
    def test_process(self, data_loader, embeddings, sample_input):
        agent = RiskAgent(data_loader, embeddings)
        context = {
            "intake": {"change_type": "infrastructure", "priority": "high"},
            "dependency": {"all_impacted_services": ["payment-gateway"], "impacted_details": [
                {"name": "payment-gateway", "criticality": "critical", "owner": "team-payments", "type": "microservice"}
            ]},
            "knowledge": {"retrieved_evidence": []},
            "incident": {"similar_incidents": [], "high_severity_count": 0}
        }
        trace = agent.execute(sample_input, context)
        assert trace.status == "completed"
        assert trace.agent.value == "risk"


class TestNotificationAgent:
    def test_process(self, data_loader, embeddings, sample_input):
        agent = NotificationAgent(data_loader, embeddings)
        context = {
            "dependency": {"impacted_details": [
                {"name": "payment-gateway", "owner": "team-payments", "criticality": "critical"}
            ]},
            "risk": {"risk_level": "high"}
        }
        trace = agent.execute(sample_input, context)
        assert trace.status == "completed"
        assert trace.agent.value == "notification"


class TestSummaryAgent:
    def test_process(self, data_loader, embeddings, sample_input):
        agent = SummaryAgent(data_loader, embeddings)
        context = {
            "intake": sample_input,
            "dependency": {"all_impacted_services": ["payment-gateway", "order-service"]},
            "knowledge": {"retrieved_evidence": [], "data_sources_used": ["cmdb.json"]},
            "incident": {"similar_incidents": []},
            "risk": {"risk_score": 0.65, "risk_level": "high", "confidence": 0.82,
                     "potential_risks": ["Risk 1"], "recommended_tests": ["Test 1"],
                     "mitigation_plan": ["Step 1"]},
            "notification": {"teams_to_notify": ["Payments", "Platform"]},
            "agent_traces": [],
            "start_time": 0.0
        }
        trace = agent.execute(sample_input, context)
        assert trace.status == "completed"
        assert trace.agent.value == "summary"

