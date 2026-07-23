"""
MODULE 8 — Automated Evaluation Metric & Ground-Truth Scoring Pipeline.

`ImpactAnalyserEvaluator` is a fully independent "Auditor Agent" that runs
AFTER the primary 3-agent ReAct pipeline (Module 1) has produced its
`RiskAnalysisReport`. It never participates in generating the prediction —
it only grades it, the way a human QA reviewer or a bank's model-risk team
would, using three structural/algorithmic metrics:

  1. Context Precision & Recall — did the Historical Detective agent
     retrieve the historical incidents that actually share services/tags
     with this change (not just "similar-sounding" ones)?
  2. Faithfulness Score (0.0-1.0) — does every claim in the final risk
     report trace back to something present in the retrieved evidence
     (CodeAuditReport + HistoricalFindingsReport), or did the LLM invent a
     service/incident that was never actually retrieved (hallucination)?
  3. Deterministic Ground-Truth Delta — cross-checks the AI's risk_score
     against an INDEPENDENT rule-engine baseline (counts of DB calls / API
     surface alterations literally present in the diff) and flags a
     `high_variance_warning` if the AI's score deviates from that baseline
     by more than 20%.

This module deliberately uses NO calls to the same LLM/pipeline being
evaluated by default — an evaluator that shares a blind spot with the thing
it evaluates provides no independent signal. All three metrics are
structural/algorithmic, so this runs safely with zero API keys, consistent
with the rest of this project's mock-mode-by-default design. An optional
Ragas-backed LLM-as-judge strategy can be injected as a *supplementary*
opinion (see `RagasFaithfulnessStrategy`) for environments that have `ragas`
installed and a live LLM provider configured.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional, Protocol, Union

from app.agents.react.tools import score_risk_matrix
from app.agents.schemas import (
    CodeAuditReport,
    HistoricalFindingsReport,
    MalformedOutputFallback,
    RiskAnalysisReport,
)
from app.evaluation.schemas import (
    ContextPrecisionRecall,
    EvaluationReport,
    EvaluationVerdict,
    FaithfulnessScore,
    GroundTruthDelta,
)

logger = logging.getLogger(__name__)

_HIGH_VARIANCE_THRESHOLD_PCT = 20.0

# A "final output" from the Risk Synthesizer agent is either the strict
# schema or its guardrail-triggered conservative fallback — both expose the
# same fields the evaluator needs (risk_score, top_risks, step_by_step_mitigation).
RiskVerdict = Union[RiskAnalysisReport, MalformedOutputFallback]


# ---------------------------------------------------------------------------
# Deterministic ground-truth rule-engine (Module 8, metric 3)
# ---------------------------------------------------------------------------
#
# These patterns intentionally overlap in spirit with, but are computed
# INDEPENDENTLY of, `parse_ast_diff` (app/agents/react/tools.py) — the goal
# is a second, cheap, purely-syntactic signal ("how many DB/API-shaped lines
# literally appear in this diff?") that the primary agents never see as a
# single pre-aggregated number, so it functions as a genuine cross-check
# rather than a re-run of the same computation.

_DB_CALL_PATTERNS = [
    re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|MERGE)\b", re.IGNORECASE),
    re.compile(r"\.(save|persist|query|execute|findBy\w+|createQuery)\s*\(", re.IGNORECASE),
    re.compile(r"@(Query|Transactional|Repository)\b"),
    re.compile(r"\b(cursor\.execute|session\.query|objects\.filter)\b"),
]

_API_ALTERATION_PATTERNS = [
    re.compile(r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\b"),
    re.compile(r"\b(app\.(get|post|put|delete|patch)|router\.(get|post|put|delete|patch))\s*\(", re.IGNORECASE),
    re.compile(r"@router\.(get|post|put|delete|patch)\s*\(", re.IGNORECASE),
    re.compile(r"\b(openapi|swagger)\b", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Optional pluggable strategy: Ragas-backed faithfulness (LLM-as-judge)
# ---------------------------------------------------------------------------

class FaithfulnessStrategy(Protocol):
    """Pluggable interface for a supplementary, heavier-weight faithfulness
    scorer. `ImpactAnalyserEvaluator` never REQUIRES an implementation of
    this — the deterministic `evaluate_faithfulness` method always runs and
    is always the authoritative `FaithfulnessScore.score`."""

    def score(self, question: str, answer: str, contexts: List[str]) -> float: ...


class RagasFaithfulnessStrategy:
    """
    Optional, heavier-weight faithfulness scorer using the `ragas` library's
    LLM-as-judge Faithfulness metric. NOT installed by default (see
    requirements.txt) and NOT used unless explicitly injected — the
    deterministic strategy above requires zero extra dependencies and zero
    API keys, consistent with this project's mock-mode-by-default design.

    Usage (optional, requires `pip install ragas datasets` and a configured
    live LLM provider):

        evaluator = ImpactAnalyserEvaluator(
            faithfulness_strategy=RagasFaithfulnessStrategy()
        )
    """

    def score(self, question: str, answer: str, contexts: List[str]) -> float:
        try:
            from datasets import Dataset
            from ragas import evaluate as ragas_evaluate
            from ragas.metrics import faithfulness as ragas_faithfulness
        except ImportError as exc:
            raise RuntimeError(
                "ragas is not installed. Run `pip install ragas datasets` to use "
                "RagasFaithfulnessStrategy, or omit `faithfulness_strategy` to use the "
                "default deterministic ImpactAnalyserEvaluator.evaluate_faithfulness instead."
            ) from exc

        dataset = Dataset.from_dict({"question": [question], "answer": [answer], "contexts": [contexts]})
        result = ragas_evaluate(dataset, metrics=[ragas_faithfulness])
        return float(result["faithfulness"][0])


# ---------------------------------------------------------------------------
# The evaluator
# ---------------------------------------------------------------------------

class ImpactAnalyserEvaluator:
    """Independent post-hoc auditor for the v2 ReAct pipeline's output."""

    def __init__(
        self,
        high_variance_threshold_pct: float = _HIGH_VARIANCE_THRESHOLD_PCT,
        faithfulness_strategy: Optional[FaithfulnessStrategy] = None,
    ):
        self.high_variance_threshold_pct = high_variance_threshold_pct
        # Optional supplementary LLM-judge strategy (e.g. Ragas). Never
        # required; failures here are always caught and logged, never raised
        # (this evaluator must never crash the primary analysis request).
        self.faithfulness_strategy = faithfulness_strategy

    # -- Metric 1: Context Precision & Recall --------------------------------

    def evaluate_context_precision_recall(
        self,
        code_audit: CodeAuditReport,
        historical: HistoricalFindingsReport,
        all_incidents: List[Dict[str, Any]],
        top_k: int = 3,
    ) -> ContextPrecisionRecall:
        """
        Ground truth for "was this incident actually relevant?" is defined
        structurally (never by asking an LLM to grade itself): an incident
        in the FULL corpus is considered relevant to this change if it
        shares at least one impacted service with the CodeAuditReport's
        impacted_applications, OR its tags overlap the inferred change type.
        This mirrors how an SRE would manually validate "did the RAG system
        pull the right incidents" during a model-risk review.
        """
        impacted_service_names = {app.service_name.lower() for app in code_audit.impacted_applications}
        impacted_service_names |= {app.service_id.lower() for app in code_audit.impacted_applications}

        change_type_tokens = set(code_audit.inferred_change_type.lower().split("_"))

        relevant_ids: List[str] = []
        for incident in all_incidents:
            incident_services = {str(s).lower() for s in incident.get("impactedServices", [])}
            incident_services.add(str(incident.get("service", "")).lower())
            incident_tags = {str(t).lower() for t in incident.get("tags", [])}

            service_overlap = bool(impacted_service_names & incident_services)
            tag_overlap = bool(change_type_tokens & incident_tags)

            if service_overlap or tag_overlap:
                relevant_ids.append(str(incident.get("id", "")))

        retrieved_ids = [outage.incident_id for outage in historical.similar_outages[:top_k]]
        true_positives = len([rid for rid in retrieved_ids if rid in relevant_ids])

        precision = (true_positives / len(retrieved_ids)) if retrieved_ids else 0.0
        # No ground-truth-relevant incidents exist in the corpus at all —
        # recall is vacuously perfect (nothing to miss) rather than
        # dividing by zero / penalizing the retriever for a fact about the
        # underlying dataset composition.
        recall = (true_positives / len(relevant_ids)) if relevant_ids else 1.0
        recall = min(recall, 1.0)

        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        return ContextPrecisionRecall(
            precision_at_k=round(precision, 4),
            recall_at_k=round(recall, 4),
            f1_score=round(f1, 4),
            k=top_k,
            retrieved_incident_ids=retrieved_ids,
            relevant_incident_ids=relevant_ids[:20],
        )

    # -- Metric 2: Faithfulness (hallucination check) ------------------------

    def evaluate_faithfulness(
        self,
        final_output: RiskVerdict,
        code_audit: CodeAuditReport,
        historical: HistoricalFindingsReport,
    ) -> FaithfulnessScore:
        """
        Claim-level entailment check: every named entity mentioned in
        `top_risks` and `step_by_step_mitigation` (service names, incident
        titles) MUST be traceable to something that was actually present in
        the retrieved evidence set (CodeAuditReport.impacted_applications or
        HistoricalFindingsReport.similar_outages). Any claim naming an
        entity NOT present in the evidence is flagged as an unsupported
        (potentially hallucinated) claim.

        This is a conservative, fully local approximation of the Ragas
        "Faithfulness" metric (which normally uses an LLM-as-judge to
        decompose a generation into atomic claims and check each one against
        the retrieved context). If `self.faithfulness_strategy` is
        configured (e.g. `RagasFaithfulnessStrategy`), its score is attached
        as a *supplementary* `llm_judge_score` — it never overrides the
        deterministic `score`, which is always computed here.
        """
        known_entities = {app.service_name.lower() for app in code_audit.impacted_applications}
        known_entities |= {app.service_id.lower() for app in code_audit.impacted_applications}
        known_entities |= {outage.title.lower() for outage in historical.similar_outages}
        known_entities |= {outage.incident_id.lower() for outage in historical.similar_outages}
        known_entities.add(code_audit.primary_component.lower())

        step_actions = [
            step.action if hasattr(step, "action") else str(step.get("action", ""))
            for step in final_output.step_by_step_mitigation
        ]
        claims = list(final_output.top_risks) + step_actions

        supported: List[str] = []
        unsupported: List[str] = []

        for claim in claims:
            claim_lower = claim.lower()
            mentioned_known_entity = any(
                entity in claim_lower for entity in known_entities if len(entity) > 3
            )
            looks_specific = bool(re.search(r"'[^']{3,}'|\"[^\"]{3,}\"", claim)) or mentioned_known_entity

            if not looks_specific:
                # Generic, non-attributable recommendation (e.g. "Deploy to
                # a canary environment first") — nothing named to hallucinate.
                supported.append(claim)
            elif mentioned_known_entity:
                supported.append(claim)
            else:
                unsupported.append(claim)

        total = len(claims) or 1
        deterministic_score = round(len(supported) / total, 4)

        llm_judge_score: Optional[float] = None
        if self.faithfulness_strategy is not None:
            try:
                contexts = [code_audit.model_dump_json(), historical.model_dump_json()]
                answer = " ".join(claims)
                llm_judge_score = round(
                    self.faithfulness_strategy.score(
                        question=f"Is this risk analysis faithful to the evidence for {code_audit.primary_component}?",
                        answer=answer,
                        contexts=contexts,
                    ),
                    4,
                )
            except Exception as exc:  # never let an optional strategy crash the evaluator
                logger.warning("Optional faithfulness strategy failed (%s); using deterministic score only", exc)

        return FaithfulnessScore(
            score=deterministic_score,
            unsupported_claims=unsupported,
            supported_claims=supported,
            total_claims_checked=len(claims),
            llm_judge_score=llm_judge_score,
        )

    # -- Metric 3: Deterministic Ground-Truth Delta ---------------------------

    def compute_ground_truth_delta(
        self,
        ai_risk_score: int,
        code_audit: CodeAuditReport,
        historical: HistoricalFindingsReport,
        sanitized_diff_text: Optional[str],
    ) -> GroundTruthDelta:
        """
        Independent rule-engine baseline: literally counts DB-call-shaped
        and API-alteration-shaped lines in the raw (sanitized) diff and
        folds that count into the SAME deterministic weighted-sum formula
        used by `score_risk_matrix` (app/agents/react/tools.py) — but with
        `db_call_component`/`api_alteration_component` added as an
        additional, code-literal signal the primary agents never see as a
        single pre-aggregated number. If the AI's self-reported risk_score
        deviates from this independently-derived baseline by more than
        `high_variance_threshold_pct`, `high_variance_warning=True` is set
        so a human reviewer is pulled in before anyone trusts the number.
        """
        diff_text = sanitized_diff_text or ""
        db_call_count = sum(len(pattern.findall(diff_text)) for pattern in _DB_CALL_PATTERNS)
        api_alteration_count = sum(len(pattern.findall(diff_text)) for pattern in _API_ALTERATION_PATTERNS)

        base_score_result = score_risk_matrix(
            code_audit=code_audit.model_dump(), historical=historical.model_dump()
        )
        baseline_components: Dict[str, int] = dict(base_score_result["components"])

        db_component = min(db_call_count * 3, 20)
        api_component = min(api_alteration_count * 4, 20)
        baseline_components["db_call_component"] = db_component
        baseline_components["api_alteration_component"] = api_component

        deterministic_baseline_score = max(1, min(100, sum(baseline_components.values())))

        absolute_delta = abs(ai_risk_score - deterministic_baseline_score)
        percentage_deviation = round((absolute_delta / max(deterministic_baseline_score, 1)) * 100, 2)
        high_variance_warning = percentage_deviation > self.high_variance_threshold_pct

        return GroundTruthDelta(
            ai_predicted_score=ai_risk_score,
            deterministic_baseline_score=deterministic_baseline_score,
            absolute_delta=absolute_delta,
            percentage_deviation=percentage_deviation,
            high_variance_warning=high_variance_warning,
            baseline_components=baseline_components,
        )

    # -- Orchestration ----------------------------------------------------------

    def evaluate(
        self,
        code_audit: CodeAuditReport,
        historical: HistoricalFindingsReport,
        final_output: RiskVerdict,
        sanitized_diff_text: Optional[str],
        all_incidents: List[Dict[str, Any]],
    ) -> EvaluationReport:
        """Run all three metrics and produce the aggregate, guardrail-validated
        `EvaluationReport`. Never raises — any per-metric failure is caught,
        logged, and substituted with a conservative worst-case value so a
        bug in the evaluator can never take down the primary analysis
        endpoint it is auditing."""
        start = time.time()

        try:
            context_metrics = self.evaluate_context_precision_recall(code_audit, historical, all_incidents)
        except Exception:
            logger.exception("Context precision/recall evaluation failed; using zeroed-out result")
            context_metrics = ContextPrecisionRecall(
                precision_at_k=0.0, recall_at_k=0.0, f1_score=0.0, k=3,
                retrieved_incident_ids=[], relevant_incident_ids=[],
            )

        try:
            faithfulness = self.evaluate_faithfulness(final_output, code_audit, historical)
        except Exception:
            logger.exception("Faithfulness evaluation failed; defaulting to score=0.0 (fail closed)")
            faithfulness = FaithfulnessScore(score=0.0, unsupported_claims=[], supported_claims=[], total_claims_checked=0)

        try:
            ground_truth_delta = self.compute_ground_truth_delta(
                final_output.risk_score, code_audit, historical, sanitized_diff_text
            )
        except Exception:
            logger.exception("Ground-truth delta computation failed; flagging high variance (fail closed)")
            ground_truth_delta = GroundTruthDelta(
                ai_predicted_score=final_output.risk_score,
                deterministic_baseline_score=final_output.risk_score,
                absolute_delta=0,
                percentage_deviation=0.0,
                high_variance_warning=True,
                baseline_components={},
            )

        verdict = self._determine_verdict(context_metrics, faithfulness, ground_truth_delta)

        logger.info(
            "ImpactAnalyserEvaluator verdict=%s faithfulness=%.2f precision=%.2f recall=%.2f "
            "variance_warning=%s (%.1fms)",
            verdict.value,
            faithfulness.score,
            context_metrics.precision_at_k,
            context_metrics.recall_at_k,
            ground_truth_delta.high_variance_warning,
            (time.time() - start) * 1000,
        )

        return EvaluationReport(
            context_precision_recall=context_metrics,
            faithfulness=faithfulness,
            ground_truth_delta=ground_truth_delta,
            overall_verdict=verdict,
            evaluated_at_ms=int(time.time() * 1000),
        )

    @staticmethod
    def _determine_verdict(
        context_metrics: ContextPrecisionRecall,
        faithfulness: FaithfulnessScore,
        ground_truth_delta: GroundTruthDelta,
    ) -> EvaluationVerdict:
        """
        Verdict thresholds (documented, versioned, and intentionally
        conservative — a false "TRUSTED" is far more costly than an
        unnecessary "REVIEW_RECOMMENDED" for a change-risk tool):

          LOW_CONFIDENCE_FLAGGED  — faithfulness < 0.5 OR variance > 50%
          REVIEW_RECOMMENDED      — faithfulness < 0.8 OR high_variance_warning
                                     OR retrieval F1 < 0.5
          TRUSTED                 — otherwise
        """
        if faithfulness.score < 0.5 or ground_truth_delta.percentage_deviation > 50:
            return EvaluationVerdict.LOW_CONFIDENCE_FLAGGED
        if (
            faithfulness.score < 0.8
            or ground_truth_delta.high_variance_warning
            or context_metrics.f1_score < 0.5
        ):
            return EvaluationVerdict.REVIEW_RECOMMENDED
        return EvaluationVerdict.TRUSTED


default_evaluator = ImpactAnalyserEvaluator()
