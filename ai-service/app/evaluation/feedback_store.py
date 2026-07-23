"""
MODULE 8 — Feedback capture & persistence.

Backs the `POST /api/v1/feedback/capture` endpoint. Every developer vote
(thumbs up/down) or manual risk-score override is appended, durably, to a
local JSONL store. This is deliberately a simple, dependency-free format
(not a database) so it runs with zero extra infrastructure in the
hackathon/demo environment, while still being a real, persistent,
append-only audit log suitable for a later offline job to mine for:

  - fine-tuning / prompt-adjustment signal (which analyses were overridden,
    and by how much, feeds directly into recalibrating
    `score_risk_matrix`'s component weights over time)
  - vector-embedding / retrieval quality signal (thumbs-down entries can be
    used to down-weight or exclude specific historical incidents from being
    retrieved for similar future changes)

Production hardening note: swap `FeedbackStore`'s file-backed implementation
for a real table (e.g. Postgres) behind the same interface when moving
beyond a single-node deployment — no caller-facing code needs to change.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from app.evaluation.schemas import FeedbackEntry, StoredFeedback

logger = logging.getLogger(__name__)

FEEDBACK_STORE_PATH = Path(__file__).parent.parent.parent / "data" / "feedback_store.jsonl"


class FeedbackStore:
    """Thread-safe, append-only JSONL feedback store."""

    def __init__(self, path: Path = FEEDBACK_STORE_PATH):
        self.path = path
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def capture(self, entry: FeedbackEntry) -> StoredFeedback:
        stored = StoredFeedback(
            feedback_id=f"fb-{uuid.uuid4().hex[:12]}",
            analysis_id=entry.analysis_id,
            vote=entry.vote,
            overridden_risk_score=entry.overridden_risk_score,
            comment=entry.comment,
            submitted_by=entry.submitted_by,
            captured_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(stored.model_dump_json() + "\n")
        logger.info(
            "Captured feedback %s for analysis %s (vote=%s, override=%s)",
            stored.feedback_id, entry.analysis_id, entry.vote, entry.overridden_risk_score,
        )
        return stored

    def list_for_analysis(self, analysis_id: str) -> List[StoredFeedback]:
        return [f for f in self._read_all_raw() if f.analysis_id == analysis_id]

    def all(self) -> List[StoredFeedback]:
        return self._read_all_raw()

    def _read_all_raw(self) -> List[StoredFeedback]:
        if not self.path.exists():
            return []
        results: List[StoredFeedback] = []
        with self._lock:
            with open(self.path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        results.append(StoredFeedback(**json.loads(line)))
                    except (json.JSONDecodeError, TypeError, ValueError):
                        logger.warning("Skipping malformed feedback_store.jsonl line")
                        continue
        return results


default_feedback_store = FeedbackStore()
