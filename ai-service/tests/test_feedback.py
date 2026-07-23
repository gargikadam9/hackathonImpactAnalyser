"""
Tests for MODULE 8 — Feedback capture API surface
(POST /api/v1/feedback/capture, GET /api/v1/feedback/{analysis_id}).
"""

import pytest
from fastapi.testclient import TestClient

from app.evaluation.feedback_store import FeedbackStore
from app.main import app


@pytest.fixture
def isolated_feedback_store(tmp_path, monkeypatch):
    """Redirect the feedback store to a throwaway file for this test only,
    so tests never pollute (or depend on) the real ai-service/data directory."""
    store = FeedbackStore(path=tmp_path / "feedback_store.jsonl")
    monkeypatch.setattr("app.routes.feedback.default_feedback_store", store)
    return store


@pytest.fixture
def client():
    return TestClient(app)


class TestFeedbackCapture:
    def test_capture_thumbs_up_vote(self, client, isolated_feedback_store):
        response = client.post(
            "/api/v1/feedback/capture",
            json={"analysis_id": "CIA-REACT-ABC123", "vote": "up"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "captured"
        assert data["feedback_id"].startswith("fb-")

    def test_capture_risk_score_override(self, client, isolated_feedback_store):
        response = client.post(
            "/api/v1/feedback/capture",
            json={
                "analysis_id": "CIA-REACT-ABC123",
                "overridden_risk_score": 30,
                "comment": "AI overestimated blast radius; only one service actually affected.",
                "submitted_by": "engineer-42",
            },
        )
        assert response.status_code == 200

    def test_rejects_empty_feedback(self, client, isolated_feedback_store):
        response = client.post("/api/v1/feedback/capture", json={"analysis_id": "CIA-REACT-XYZ"})
        assert response.status_code == 422

    def test_rejects_invalid_vote_value(self, client, isolated_feedback_store):
        response = client.post(
            "/api/v1/feedback/capture",
            json={"analysis_id": "CIA-REACT-XYZ", "vote": "sideways"},
        )
        assert response.status_code == 422

    def test_captured_feedback_is_retrievable_by_analysis_id(self, client, isolated_feedback_store):
        client.post("/api/v1/feedback/capture", json={"analysis_id": "CIA-REACT-RETR1", "vote": "down"})
        client.post("/api/v1/feedback/capture", json={"analysis_id": "CIA-REACT-RETR1", "overridden_risk_score": 20})
        client.post("/api/v1/feedback/capture", json={"analysis_id": "CIA-REACT-OTHER", "vote": "up"})

        response = client.get("/api/v1/feedback/CIA-REACT-RETR1")
        assert response.status_code == 200
        entries = response.json()
        assert len(entries) == 2
        assert all(e["analysis_id"] == "CIA-REACT-RETR1" for e in entries)

    def test_unknown_analysis_id_returns_empty_list(self, client, isolated_feedback_store):
        response = client.get("/api/v1/feedback/does-not-exist")
        assert response.status_code == 200
        assert response.json() == []


class TestFeedbackStorePersistence:
    def test_capture_appends_durably_to_jsonl_file(self, tmp_path):
        store = FeedbackStore(path=tmp_path / "fb.jsonl")
        from app.evaluation.schemas import FeedbackEntry

        store.capture(FeedbackEntry(analysis_id="a1", vote="up"))
        store.capture(FeedbackEntry(analysis_id="a1", overridden_risk_score=40))
        store.capture(FeedbackEntry(analysis_id="a2", vote="down"))

        assert len(store.all()) == 3
        assert len(store.list_for_analysis("a1")) == 2
        assert len(store.list_for_analysis("a2")) == 1

        # A fresh FeedbackStore instance pointed at the same file must see
        # the same durable data (this is what makes it a real persistence
        # layer, not just an in-memory cache).
        reloaded = FeedbackStore(path=tmp_path / "fb.jsonl")
        assert len(reloaded.all()) == 3

    def test_malformed_lines_are_skipped_gracefully(self, tmp_path):
        path = tmp_path / "fb.jsonl"
        path.write_text("not-valid-json\n{\"incomplete\": true", encoding="utf-8")
        store = FeedbackStore(path=path)
        assert store.all() == []
