"""
MODULE 4 — Deterministic guardrail schemas for the ReAct agent pipeline.

Every agent in `app/agents/react/` MUST produce output that validates
against one of these Pydantic models before it is allowed to be either
(a) passed to the next agent, or (b) returned to the API caller. This is the
enforcement mechanism referenced throughout the architecture blueprint as
"strict JSON guardrails" — conceptually equivalent to using the `instructor`
library's `response_model=` pattern, implemented here directly on top of
Pydantic + a bounded LLM-repair retry loop so the codebase has zero
additional runtime dependency risk.

Final output schema (per the hackathon spec) is `RiskAnalysisReport`, which
contains exactly:
  - risk_score            (1-100)
  - top_risks             (array)
  - applications_impacted (array)
  - teams_notified        (array)
  - step_by_step_mitigation (array)
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Agent 1 — Code Auditor output contract
# ---------------------------------------------------------------------------

class ChangeTypeEnum(str, Enum):
    INFRASTRUCTURE_UPGRADE = "INFRASTRUCTURE_UPGRADE"
    KAFKA_UPGRADE = "KAFKA_UPGRADE"
    DATABASE_MIGRATION = "DATABASE_MIGRATION"
    API_CONTRACT_CHANGE = "API_CONTRACT_CHANGE"
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"
    SECURITY_PATCH = "SECURITY_PATCH"
    FEATURE_ENHANCEMENT = "FEATURE_ENHANCEMENT"
    BUG_FIX = "BUG_FIX"
    ROLLBACK = "ROLLBACK"
    UNKNOWN = "UNKNOWN"


class TouchedSymbol(BaseModel):
    symbol_name: str
    file_path: str
    change_kind: str = Field(..., description="added | modified | removed")


class ImpactedApplication(BaseModel):
    service_id: str
    service_name: str
    criticality: str = Field(..., description="low | medium | high | critical")
    relationship: str = Field(..., description="target | direct_dependency | downstream_cascade")


class CodeAuditReport(BaseModel):
    """Strict output contract for the Code Auditor Agent."""

    model_config = {"extra": "forbid"}

    inferred_change_type: ChangeTypeEnum
    primary_component: str
    touched_symbols: List[TouchedSymbol] = Field(default_factory=list)
    impacted_applications: List[ImpactedApplication] = Field(default_factory=list)
    blast_radius_score: int = Field(..., ge=0, le=100, description="0 = isolated, 100 = whole platform")
    reasoning: List[str] = Field(default_factory=list, description="Bullet-point chain of reasoning")

    @field_validator("impacted_applications")
    @classmethod
    def _must_have_at_least_target(cls, value: List[ImpactedApplication]) -> List[ImpactedApplication]:
        if not value:
            raise ValueError("impacted_applications must contain at least the target component")
        return value


class CodeAuditReportFallback(CodeAuditReport):
    """Conservative, schema-valid substitute used when the Code Auditor's
    Final Answer fails guardrail validation even after the repair retry."""

    is_fallback: bool = True


# ---------------------------------------------------------------------------
# Agent 2 — Historical Detective output contract
# ---------------------------------------------------------------------------

class SimilarOutageFinding(BaseModel):
    incident_id: str
    title: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    root_cause: str
    mitigation_used: str


class HistoricalFindingsReport(BaseModel):
    """Strict output contract for the Historical Detective Agent."""

    model_config = {"extra": "forbid"}

    similar_outages: List[SimilarOutageFinding] = Field(default_factory=list, max_length=3)
    historical_severity_signal: str = Field(
        ..., description="none | low | moderate | severe — worst severity observed among similar_outages"
    )
    recurring_pattern_summary: str
    reasoning: List[str] = Field(default_factory=list)

    @field_validator("similar_outages")
    @classmethod
    def _cap_top_three(cls, value: List[SimilarOutageFinding]) -> List[SimilarOutageFinding]:
        if len(value) > 3:
            raise ValueError("similar_outages must contain at most the top 3 matches")
        return value


class HistoricalFindingsReportFallback(HistoricalFindingsReport):
    """Conservative, schema-valid substitute used when the Historical
    Detective's Final Answer fails guardrail validation even after retry."""

    is_fallback: bool = True


# ---------------------------------------------------------------------------
# Agent 3 — Risk Synthesizer output contract (the FINAL API response shape)
# ---------------------------------------------------------------------------

class RiskLevelEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MitigationStep(BaseModel):
    step_number: int = Field(..., ge=1)
    action: str
    owner_team: Optional[str] = None


class RiskAnalysisReport(BaseModel):
    """
    THE strict, final JSON output schema required by the hackathon spec.

    The LLM is instructed (see app/agents/prompts.py) to emit ONLY raw JSON
    matching this shape — no markdown fences, no prose preamble. This model
    is the guardrail: any response that does not validate against it is
    rejected and routed through the fallback repair path
    (see app/agents/guardrails.py).
    """

    model_config = {"extra": "forbid"}

    risk_score: int = Field(..., ge=1, le=100, description="1 (negligible) - 100 (catastrophic)")
    risk_level: RiskLevelEnum
    top_risks: List[str] = Field(..., min_length=1, max_length=10)
    applications_impacted: List[str] = Field(..., min_length=1)
    teams_notified: List[str] = Field(..., min_length=1)
    step_by_step_mitigation: List[MitigationStep] = Field(..., min_length=1)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    executive_summary: str = Field(default="")

    @model_validator(mode="after")
    def _risk_level_must_match_score(self) -> "RiskAnalysisReport":
        expected = self._level_for_score(self.risk_score)
        if self.risk_level != expected:
            # Do not raise — deterministically correct instead. This keeps
            # the numeric score authoritative (see Module 5.3: determinism
            # for compliance sign-off) even if the LLM's categorical label
            # drifted from the numeric score it also produced.
            self.risk_level = expected
        return self

    @staticmethod
    def _level_for_score(score: int) -> RiskLevelEnum:
        if score >= 80:
            return RiskLevelEnum.CRITICAL
        if score >= 60:
            return RiskLevelEnum.HIGH
        if score >= 35:
            return RiskLevelEnum.MEDIUM
        return RiskLevelEnum.LOW


# ---------------------------------------------------------------------------
# MODULE 7 — Explainable AI (XAI): Attribution Matrix output contract
# ---------------------------------------------------------------------------
#
# The dashboard must never show a bare "Risk Score: 85/100" with no
# justification. Every RiskDriver below is derived DETERMINISTICALLY from the
# exact same `components` dict produced by `score_risk_matrix()`
# (app/agents/react/tools.py) — see app/agents/react/explainability.py for
# the builder. This guarantees the explanation can never drift from the
# actual computation (no separate LLM narrative that could contradict the
# number it's supposedly explaining).

class RiskDriver(BaseModel):
    """One line-item in the Risk Synthesizer's attribution matrix — a single,
    named reason the risk score is what it is, traceable back to a concrete
    code location or structural signal (never a vague, unfalsifiable claim)."""

    model_config = {"extra": "forbid"}

    driver_id: str = Field(..., description="Stable id within this report, e.g. 'driver-1'")
    code_snippet: str = Field(
        ..., description="The exact line(s) of the diff causing this risk signal, or a "
        "structural descriptor when no line-level diff was supplied"
    )
    file_path: Optional[str] = Field(default=None, description="File the snippet was extracted from, if applicable")
    severity_weight: float = Field(
        ..., ge=0.0, le=100.0,
        description="This driver's percentage contribution to the total risk_score; "
        "all drivers in one report sum to ~100.0 by construction"
    )
    justification_text: str = Field(..., min_length=1, description="Human-readable explanation of why this driver contributes risk")
    category: str = Field(
        ..., description="blast_radius | criticality | historical_precedent | change_type_baseline"
    )


class ExplainabilityReport(BaseModel):
    """MODULE 7 output — attached to every `FullAnalysisResponseV2` so a
    developer can see EXACTLY why `risk_score` is what it is, not just the
    number. Rendered by the frontend's `RiskAttributionBreakdown` dashboard
    component (frontend/src/components/dashboard/RiskAttributionBreakdown.tsx)."""

    model_config = {"extra": "forbid"}

    primary_risk_drivers: List[RiskDriver] = Field(..., min_length=1, max_length=10)
    historical_correlation_factor: str = Field(
        ..., min_length=1,
        description="Text explanation linking the current code-change pattern directly "
        "to past incident root-cause analyses (or explicitly stating none was found)",
    )
    total_attributed_weight: float = Field(
        ..., ge=0.0, le=100.0, description="Sum of all primary_risk_drivers[].severity_weight"
    )
    generated_at_ms: int = Field(..., description="Unix epoch milliseconds this report was generated")


class MalformedOutputFallback(BaseModel):
    """
    Emitted instead of RiskAnalysisReport when the LLM output could not be
    coerced into a valid schema even after the repair retry (see
    app/agents/guardrails.py). Callers must check `is_fallback` before
    trusting risk_score at face value.
    """

    model_config = {"extra": "forbid"}

    is_fallback: bool = True
    risk_score: int = Field(default=50, ge=1, le=100)
    risk_level: RiskLevelEnum = RiskLevelEnum.MEDIUM
    top_risks: List[str] = Field(default_factory=lambda: ["Unable to fully parse AI output; manual review required"])
    applications_impacted: List[str] = Field(default_factory=list)
    teams_notified: List[str] = Field(default_factory=lambda: ["Change Advisory Board (CAB)"])
    step_by_step_mitigation: List[MitigationStep] = Field(
        default_factory=lambda: [
            MitigationStep(step_number=1, action="Escalate to on-call engineer for manual risk review", owner_team="SRE")
        ]
    )
    confidence: float = 0.0
    executive_summary: str = "AI risk synthesis failed structured validation twice; defaulted to a conservative manual-review verdict."
    raw_model_output: str = ""
    validation_errors: List[str] = Field(default_factory=list)
