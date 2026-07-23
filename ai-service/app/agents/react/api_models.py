"""
Request/response contracts for the v2 ReAct analysis API surface
(POST /api/v2/change-impact/analyze-react). Kept separate from the legacy
`app/models.py` so the two pipelines (mock 7-agent DAG vs. ReAct 3-agent)
can evolve independently.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.agents.schemas import ExplainabilityReport
from app.evaluation.schemas import EvaluationReport
from app.security.sanitizer import RedactionReport


class ChangeAnalysisRequestV2(BaseModel):
    change_title: str = Field(..., description="Short title of the proposed change")
    change_description: str = Field(..., description="Detailed description of the proposed change")
    target_component: str = Field(..., description="CMDB component id/name this change primarily targets")
    change_type: Optional[str] = Field(default=None, description="Optional hint; the Code Auditor will infer this if omitted")
    raw_diff_text: Optional[str] = Field(
        default=None,
        description="Raw git diff or config snippet. MAY contain secrets — this is sanitized "
        "locally before anything is sent to a cloud LLM.",
    )
    environment: Optional[str] = Field(default="production")
    requested_by: Optional[str] = Field(default="")


class ReactStepTrace(BaseModel):
    iteration: int
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[Dict[str, Any]] = None
    is_final_step: bool = False


class AgentExecutionTrace(BaseModel):
    agent_name: str
    steps: List[ReactStepTrace]
    hit_iteration_cap: bool
    used_fallback: bool
    elapsed_ms: int


class FullAnalysisResponseV2(BaseModel):
    analysis_id: str
    risk_score: int
    risk_level: str
    top_risks: List[str]
    applications_impacted: List[str]
    teams_notified: List[str]
    step_by_step_mitigation: List[Dict[str, Any]]
    confidence: float
    executive_summary: str
    is_fallback: bool = False

    code_audit: Dict[str, Any]
    historical_findings: Dict[str, Any]
    redaction_report: RedactionReport
    agent_traces: List[AgentExecutionTrace]

    # MODULE 7 — Explainable AI: strict attribution matrix explaining EXACTLY
    # why risk_score is what it is (see app/agents/react/explainability.py).
    explainability_report: ExplainabilityReport

    # MODULE 8 — Automated Evaluation: independent post-hoc audit of this
    # same prediction (see app/evaluation/evaluator.py).
    evaluation_report: EvaluationReport

    processing_time_ms: int
    mock_mode: bool
