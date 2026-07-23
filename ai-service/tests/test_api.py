"""
Tests for FastAPI routes.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthAPI:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "provider" in data
        assert "data_loaded" in data

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data


class TestSystemAPI:
    def test_change_types(self, client):
        response = client.get("/api/v1/change-types")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert any(ct["id"] == "infrastructure" for ct in data)

    def test_components(self, client):
        response = client.get("/api/v1/components")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert any(c["name"] == "payment-gateway" for c in data)

    def test_technical_details(self, client):
        response = client.get("/api/v1/system/technical-details")
        assert response.status_code == 200
        data = response.json()
        assert data["total_services"] > 0


class TestAssistantAPI:
    def test_assistant_conversation(self, client):
        response = client.post("/api/v1/assistant/respond", json={
            "message": "Hello, how are you?"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["classification"] == "conversation"
        assert len(data["reply"]) > 0

    def test_assistant_change_analysis(self, client):
        response = client.post("/api/v1/assistant/respond", json={
            "message": "I need to analyze the impact of upgrading the payment gateway database"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["classification"] == "change-analysis"
        assert len(data["suggested_actions"]) > 0


class TestChatAPI:
    def test_general_chat(self, client):
        response = client.post("/api/v1/chat/general", json={
            "message": "Tell me about the architecture"
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["reply"]) > 0
        assert "conversation_id" in data

    def test_general_chat_with_history(self, client):
        response = client.post("/api/v1/chat/general", json={
            "message": "Thank you",
            "conversation_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        })
        assert response.status_code == 200


class TestChangeImpactAPI:
    def test_analyze(self, client):
        response = client.post("/api/v1/change-impact/analyze", json={
            "change_title": "Payment Gateway Database Pool Upgrade",
            "change_description": "Increase database connection pool from 50 to 200 to handle peak load",
            "change_type": "infrastructure",
            "affected_services": ["payment-gateway"],
            "priority": "high"
        })
        assert response.status_code == 200
        data = response.json()
        assert "analysisId" in data
        assert "riskScore" in data
        assert "riskLevel" in data
        assert "confidence" in data
        assert "impactedServices" in data
        assert "teamsToNotify" in data
        assert "potentialRisks" in data
        assert "recommendedTests" in data
        assert "similarIncidents" in data
        assert "mitigationPlan" in data
        assert "executiveSummary" in data
        assert "agentTraces" in data
        assert "mockMode" in data

    def test_analyze_prompt(self, client):
        response = client.post("/api/v1/change-impact/analyze-prompt", json={
            "title": "Upgrade payment gateway database",
            "description": "Need to upgrade the payment database connection pool",
            "type": "infrastructure",
            "services": ["payment-gateway"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "analysisId" in data
        assert "riskScore" in data

    def test_analyze_prompt_minimal(self, client):
        response = client.post("/api/v1/change-impact/analyze-prompt", json={
            "message": "Need to change the database config"
        })
        assert response.status_code == 200
        data = response.json()
        assert "analysisId" in data

