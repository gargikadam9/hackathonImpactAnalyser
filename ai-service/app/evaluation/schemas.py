"""
MODULE 8 — Automated Evaluation & Ground-Truth Scoring: Pydantic contracts.

These models are the strict output/input schemas for `ImpactAnalyserEvaluator`
(app/evaluation/evaluator.py) and the feedback-capture API surface
(app/routes/feedback.py). Kept in their own package (separate from
`app/agents/schemas.py`) because the evaluator is architecturally independent
from the agents it evaluates — it must be importable/testable without pulling
in the ReAct agent machinery.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Metric 1 — Context Precision & Recall (RAG retrieval quality)
# ---------------------------------------------------------------------------

class ContextPrecisionRecall(BaseModel):
    """
    Did the Historical Detective agent retrieve the CORRECT historical
    incidents based on the code-change semantics, or just superficially
    "similar-sounding" ones? Ground truth is computed structurally (service
    overlap + change-type/tag overlap against the full incident corpus) —
    never by asking an LLM to grade its own retrieval.
    """

    model_config = {"extra": "forbid"}

    precision_at_k: float = Field(..., ge=0.0, le=1.0, description="Of the incidents retrieved, fraction that were actually relevant")
    recall_at_k: float = Field(..., ge=0.0, le=1.0, description="Of all relevant incidents in the corpus, fraction that were retrieved")
    f1_score: float = Field(..., ge=0.0, le=1.0)
    k: int = Field(..., ge=1)
    retrieved_incident_ids: List[str] = Field(default_factory=list)
    relevant_incident_ids: List[str] = Field(default_factory=list, description="Ground-truth relevant set (capped for payload size)")
    methodology: str = Field(
        default=(
            "Structural ground truth: an incident is 'relevant' if it shares an impacted "
            "service with CodeAuditReport.impacted_applications, or its tags overlap the "
            "inferred change type. See ImpactAnalyserEvaluator.evaluate_context_precision_recall."
        )
    )


# ---------------------------------------------------------------------------
# Metric 2 — Faithfulness (hallucination check)
# ---------------------------------------------------------------------------

class FaithfulnessScore(BaseModel):
    """
    Is the generated risk report factual based ONLY on the retrieved
    codebase-audit and historical-incident evidence, or did the AI
    hallucinate an entity (service, incident) that was never actually
    retrieved? 1.0 = fully grounded, 0.0 = fully hallucinated.
    """

    model_config = {"extra": "forbid"}

    score: float = Field(..., ge=0.0, le=1.0)
    unsupported_claims: List[str] = Field(default_factory=list, description="Claims naming an entity absent from retrieved evidence")
    supported_claims: List[str] = Field(default_factory=list)
    total_claims_checked: int = Field(..., ge=0)
    llm_judge_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Optional secondary opinion from an LLM-as-judge strategy (e.g. Ragas), "
        "if one was configured and available at evaluation time. Never required for the "
        "primary `score` field, which is always computed deterministically.",
    )
    methodology: str = Field(
        default=(
            "Claim-level entity-entailment check: every named entity mentioned in top_risks "
            "and step_by_step_mitigation must be present in the retrieved evidence set "
            "(CodeAuditReport.impacted_applications or HistoricalFindingsReport.similar_outages)."
        )
    )


# ---------------------------------------------------------------------------
# Metric 3 — Deterministic Ground-Truth Delta
# ---------------------------------------------------------------------------

class GroundTruthDelta(BaseModel):
    """
    Cross-checks the AI's self-reported risk_score against an INDEPENDENT
    deterministic rule-engine baseline (literal counts of DB calls / API
    surface alterations in the diff, folded into the same weighted-sum
    formula used by score_risk_matrix). Flags `high_variance_warning` when
    the AI's score deviates from that baseline by more than the configured
    threshold (default 20%).
    """

    model_config = {"extra": "forbid"}

    ai_predicted_score: int = Field(..., ge=1, le=100)
    deterministic_baseline_score: int = Field(..., ge=1, le=100)
    absolute_delta: int = Field(..., ge=0)
    percentage_deviation: float = Field(..., ge=0.0)
    high_variance_warning: bool
    baseline_components: Dict[str, int] = Field(default_factory=dict)
    baseline_formula_version: str = Field(default="ground-truth-v1.0-rule-engine")


# ---------------------------------------------------------------------------
# Aggregate evaluation report
# ---------------------------------------------------------------------------

class EvaluationVerdict(str, Enum):
    TRUSTED = "TRUSTED"
    REVIEW_RECOMMENDED = "REVIEW_RECOMMENDED"
    LOW_CONFIDENCE_FLAGGED = "LOW_CONFIDENCE_FLAGGED"


class EvaluationReport(BaseModel):
    """
    MODULE 8 output — attached to every `FullAnalysisResponseV2` as an
    independent, post-hoc audit of the primary prediction. Rendered by the
    frontend's `EvaluationScorecard` dashboard component.
    """

    model_config = {"extra": "forbid"}

    context_precision_recall: ContextPrecisionRecall
    faithfulness: FaithfulnessScore
    ground_truth_delta: GroundTruthDelta
    overall_verdict: EvaluationVerdict
    evaluator_version: str = Field(default="impact-analyser-evaluator-v1.0")
    evaluated_at_ms: int


# ---------------------------------------------------------------------------
# Feedback capture (human-in-the-loop)
# ---------------------------------------------------------------------------

class FeedbackEntry(BaseModel):
    """Request body for POST /api/v1/feedback/capture."""

    model_config = {"extra": "forbid"}

    analysis_id: str = Field(..., min_length=1)
    vote: Optional[str] = Field(default=None, description="'up' or 'down'")
    overridden_risk_score: Optional[int] = Field(default=None, ge=1, le=100)
    comment: Optional[str] = Field(default=None, max_length=2000)
    submitted_by: Optional[str] = Field(default=None, max_length=200)


class StoredFeedback(BaseModel):
    """Persisted record, one line per entry in the feedback JSONL store."""

    model_config = {"extra": "forbid"}

    feedback_id: str
    analysis_id: str
    vote: Optional[str] = None
    overridden_risk_score: Optional[int] = None
    comment: Optional[str] = None
    submitted_by: Optional[str] = None
    captured_at: str


class FeedbackCaptureResponse(BaseModel):
    status: str
    feedback_id: str
    stored_at: str
