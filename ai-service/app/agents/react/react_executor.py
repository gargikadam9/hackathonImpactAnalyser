"""
MODULE 1 — ReAct pipeline orchestrator.

Wires together, in order:
  1. Local sanitization (Module 2) of the raw diff/description.
  2. CodeAuditorAgent.run()
  3. HistoricalDetectiveAgent.run() (fed the Code Auditor's validated output)
  4. RiskSynthesizerAgent.run() (fed both prior validated outputs)
  5. Assembly of the final strict-JSON API response, including the full,
     auditable Thought/Action/Observation transcript of every agent.

This is the single entry point the FastAPI route (app/routes/react_pipeline.py)
calls.
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, Optional

from app.agents.react.code_auditor_agent import CodeAuditorAgent
from app.agents.react.explainability import build_attribution_matrix
from app.agents.react.historical_detective_agent import HistoricalDetectiveAgent
from app.agents.react.risk_synthesizer_agent import RiskSynthesizerAgent
from app.agents.react.tools import score_risk_matrix
from app.agents.react.api_models import (
    AgentExecutionTrace,
    ChangeAnalysisRequestV2,
    FullAnalysisResponseV2,
    ReactStepTrace,
)
from app.agents.schemas import MalformedOutputFallback
from app.evaluation.evaluator import default_evaluator
from app.rag.data_loader import DataLoader
from app.security.sanitizer import RedactionReport, SanitizationError, default_sanitizer


class ReactPipelineExecutor:
    """Orchestrator — safe to reuse a single instance across requests. Holds
    a `DataLoader` so MODULE 8's evaluator can access the full incident
    corpus for its context-precision/recall ground-truth computation without
    re-reading `incidents.json` from disk on every request."""

    def __init__(self, data_loader: Optional[DataLoader] = None):
        self.data_loader = data_loader or DataLoader()

    def analyze(self, request: ChangeAnalysisRequestV2) -> FullAnalysisResponseV2:
        start = time.time()
        analysis_id = f"CIA-REACT-{uuid.uuid4().hex[:8].upper()}"

        # --- Module 2: local sanitization happens BEFORE any agent/LLM sees the text ---
        # Description and diff are sanitized independently so a raw newline inside
        # either field can never desynchronize the two (fail-closed, never guess).
        try:
            sanitized_description, description_report = default_sanitizer.sanitize(
                request.change_description or "", strict=True
            )
            sanitized_diff, diff_report = default_sanitizer.sanitize(
                request.raw_diff_text or "", strict=True
            )
        except SanitizationError:
            # Fail closed: never let ambiguous high-risk content flow into the
            # agent pipeline. Re-raise so the API layer returns HTTP 422.
            raise

        redaction_report = self._merge_redaction_reports(description_report, diff_report)

        base_context: Dict[str, Any] = {
            "change_title": request.change_title,
            "change_description": sanitized_description,
            "target_component": request.target_component,
            "sanitized_diff_text": sanitized_diff,
        }

        # --- Agent 1: Code Auditor ---
        code_auditor = CodeAuditorAgent(base_context)
        code_audit_run = code_auditor.run(code_auditor.build_initial_message())

        # --- Agent 2: Historical Detective ---
        historical_detective = HistoricalDetectiveAgent(base_context, code_audit_run.output)
        historical_run = historical_detective.run(historical_detective.build_initial_message())

        # --- Agent 3: Risk Synthesizer ---
        risk_synthesizer = RiskSynthesizerAgent(base_context, code_audit_run.output, historical_run.output)
        risk_run = risk_synthesizer.run(risk_synthesizer.build_initial_message())

        final_output = risk_run.output
        is_fallback = isinstance(final_output, MalformedOutputFallback)

        agent_traces = [
            self._to_agent_trace(code_audit_run),
            self._to_agent_trace(historical_run),
            self._to_agent_trace(risk_run),
        ]

        # --- MODULE 7: Explainable AI — build the strict attribution matrix ---
        # Re-derive the SAME deterministic score components risk_synthesizer
        # used (score_risk_matrix is a pure function of code_audit/historical,
        # so this is not a second, divergent computation — it is the single
        # source of truth both the score AND its explanation are built from).
        score_result = score_risk_matrix(
            code_audit=code_audit_run.output.model_dump(),
            historical=historical_run.output.model_dump(),
        )
        explainability_report = build_attribution_matrix(
            code_audit=code_audit_run.output,
            historical=historical_run.output,
            sanitized_diff_text=sanitized_diff,
            risk_score=final_output.risk_score,
            score_components=score_result["components"],
        )

        # --- MODULE 8: independent post-hoc evaluation of this prediction ---
        # Runs AFTER the primary prediction is finalized and never feeds back
        # into it — a true independent "Auditor Agent" pass (see
        # app/evaluation/evaluator.py). Never allowed to fail the request:
        # ImpactAnalyserEvaluator.evaluate() internally catches and
        # fail-closes on any per-metric error.
        evaluation_report = default_evaluator.evaluate(
            code_audit=code_audit_run.output,
            historical=historical_run.output,
            final_output=final_output,
            sanitized_diff_text=sanitized_diff,
            all_incidents=self.data_loader.get_incidents(),
        )

        response = FullAnalysisResponseV2(
            analysis_id=analysis_id,
            risk_score=final_output.risk_score,
            risk_level=final_output.risk_level if isinstance(final_output.risk_level, str) else final_output.risk_level.value,
            top_risks=final_output.top_risks,
            applications_impacted=final_output.applications_impacted,
            teams_notified=final_output.teams_notified,
            step_by_step_mitigation=[
                step.model_dump() if hasattr(step, "model_dump") else step
                for step in final_output.step_by_step_mitigation
            ],
            confidence=final_output.confidence,
            executive_summary=final_output.executive_summary,
            is_fallback=is_fallback,
            code_audit=code_audit_run.output.model_dump(),
            historical_findings=historical_run.output.model_dump(),
            redaction_report=redaction_report,
            agent_traces=agent_traces,
            explainability_report=explainability_report,
            evaluation_report=evaluation_report,
            processing_time_ms=int((time.time() - start) * 1000),
            mock_mode=os.getenv("PIPELINE_AI_PROVIDER", "mock") == "mock",
        )
        return response

    @staticmethod
    def _merge_redaction_reports(*reports: RedactionReport) -> RedactionReport:
        total = sum(r.total_redactions for r in reports)
        merged_categories: Dict[str, int] = {}
        merged_events = []
        is_safe = True
        for report in reports:
            for category, count in report.redactions_by_category.items():
                merged_categories[category] = merged_categories.get(category, 0) + count
            merged_events.extend(report.events)
            is_safe = is_safe and report.is_safe_for_llm
        return RedactionReport(
            total_redactions=total,
            redactions_by_category=merged_categories,
            events=merged_events,
            is_safe_for_llm=is_safe,
        )

    @staticmethod
    def _to_agent_trace(run_result) -> AgentExecutionTrace:
        steps = []
        for i, step in enumerate(run_result.steps):
            is_final = step.final_answer_raw is not None
            steps.append(
                ReactStepTrace(
                    iteration=step.iteration,
                    thought=step.thought,
                    action=step.action,
                    action_input=step.action_input,
                    observation=step.observation,
                    is_final_step=is_final,
                )
            )
        return AgentExecutionTrace(
            agent_name=run_result.agent_name,
            steps=steps,
            hit_iteration_cap=run_result.hit_iteration_cap,
            used_fallback=run_result.used_fallback,
            elapsed_ms=run_result.elapsed_ms,
        )


default_executor = ReactPipelineExecutor()
