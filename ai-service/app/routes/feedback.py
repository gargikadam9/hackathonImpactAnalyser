"""
MODULE 8 — Feedback capture API surface.

`POST /api/v1/feedback/capture` lets a developer submit a thumbs up/down
verdict on a specific analysis, or manually override its risk score. This is
the human-in-the-loop signal that closes the loop between "the model
predicted X" and "a human confirmed/rejected X" — the raw material later
used to fine-tune prompts, the deterministic scoring formula's weights, and
which historical incidents the vector index should surface for similar
future changes (see app/evaluation/feedback_store.py for the persistence
layer and its production-hardening notes).
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from app.evaluation.feedback_store import default_feedback_store
from app.evaluation.schemas import FeedbackCaptureResponse, FeedbackEntry, StoredFeedback

router = APIRouter()


@router.post("/feedback/capture", response_model=FeedbackCaptureResponse, tags=["Feedback"])
async def capture_feedback(entry: FeedbackEntry) -> FeedbackCaptureResponse:
    """
    Persist a thumbs up/down vote and/or a manual risk-score override for a
    given `analysis_id`. Returns immediately; storage is a fast local
    append-only write (see `app/evaluation/feedback_store.py`).
    """
    if entry.vote is not None and entry.vote not in ("up", "down"):
        raise HTTPException(status_code=422, detail="vote must be 'up' or 'down' if provided")
    if entry.vote is None and entry.overridden_risk_score is None:
        raise HTTPException(
            status_code=422,
            detail="At least one of 'vote' or 'overridden_risk_score' must be provided",
        )

    stored = default_feedback_store.capture(entry)
    return FeedbackCaptureResponse(
        status="captured",
        feedback_id=stored.feedback_id,
        stored_at=stored.captured_at,
    )


@router.get("/feedback/{analysis_id}", response_model=List[StoredFeedback], tags=["Feedback"])
async def get_feedback_for_analysis(analysis_id: str) -> List[StoredFeedback]:
    """Retrieve all feedback captured so far for a specific analysis."""
    return default_feedback_store.list_for_analysis(analysis_id)
