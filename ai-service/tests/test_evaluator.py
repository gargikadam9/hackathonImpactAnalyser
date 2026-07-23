"""
Tests for MODULE 8 — Automated Evaluation Metric & Ground-Truth Scoring
Pipeline (`ImpactAnalyserEvaluator`).
"""

import pytest

from app.evaluation.evaluator import ImpactAnalyserEvaluator
from app.evaluation.schemas import EvaluationVerdict
from app.agents.schemas import (
    CodeAuditReport,
    HistoricalFindingsReport,
    ImpactedApplication,
    MalformedOutputFallback,
    MitigationStep,
    RiskAnalysisReport,
    SimilarOutageFinding,
    TouchedSymbol,
)


INCIDENT_CORPUS = [
    {
        "id": "inc-001",
        "title": "Payment Gateway Outage",
        "service": "payment-gateway",
        "severity": "critical",
        "description": "Payment gateway was unresponsive due to DB connection pool exhaustion",
        "rootCause": "Database connection leak under high load",
        "resolution": "Increased connection pool size",
        "impactedServices": ["payment-gateway", "order-service", "checkout-service"],
        "tags": ["database", "scaling", "high-load"],
    },
    {
        "id": "inc-002",
        "title": "User Login Failures",
        "service": "user-service",
        "severity": "high",
        "description": "Users unable to login due to Redis session cache corruption",
        "rootCause": "Memory corruption in Redis cluster after upgrade",
        "resolution": "Cleared Redis cache",
        "impactedServices": ["user-service", "api-gateway"],
        "tags": ["authentication", "cache", "upgrade"],
    },
]


def _code_audit(**overrides) -> CodeAuditReport:
    defaults = dict(
        inferred_change_type="DATABASE_MIGRATION",
        primary_component="payment-gateway",
        touched_symbols=[TouchedSymbol(symbol_name="chargeCard", file_path="src/PaymentService.java", change_kind="modified")],
        impacted_applications=[
            ImpactedApplication(service_id="payment-gateway", service_name="payment-gateway", criticality="critical", relationship="target"),
        ],
        blast_radius_score=40,
        reasoning=[],
    )
    defaults.update(overrides)
    return CodeAuditReport(**defaults)


def _historical(**overrides) -> HistoricalFindingsReport:
    defaults = dict(
        similar_outages=[
            SimilarOutageFinding(
                incident_id="inc-001",
                title="Payment Gateway Outage",
                similarity_score=0.9,
                root_cause="Database connection leak under high load",
                mitigation_used="Increased connection pool size",
            )
        ],
        historical_severity_signal="severe",
        recurring_pattern_summary="Matches inc-001",
        reasoning=[],
    )
    defaults.update(overrides)
    return HistoricalFindingsReport(**defaults)


def _risk_report(**overrides) -> RiskAnalysisReport:
    defaults = dict(
        risk_score=55,
        risk_level="HIGH",
        top_risks=["Critical dependency at risk: 'payment-gateway' (critical)."],
        applications_impacted=["payment-gateway"],
        teams_notified=["SRE"],
        step_by_step_mitigation=[MitigationStep(step_number=1, action="Deploy to staging first.", owner_team="SRE")],
        confidence=0.9,
        executive_summary="High risk change to payment-gateway.",
    )
    defaults.update(overrides)
    return RiskAnalysisReport(**defaults)


@pytest.fixture
def evaluator() -> ImpactAnalyserEvaluator:
    return ImpactAnalyserEvaluator()


class TestContextPrecisionRecall:
    def test_perfect_retrieval_yields_precision_and_recall_of_one(self, evaluator):
        code_audit = _code_audit()
        historical = _historical()  # retrieves inc-001, which shares payment-gateway
        result = evaluator.evaluate_context_precision_recall(code_audit, historical, INCIDENT_CORPUS)

        assert result.precision_at_k == 1.0
        assert result.recall_at_k == 1.0
        assert result.f1_score == 1.0
        assert "inc-001" in result.retrieved_incident_ids

    def test_irrelevant_retrieval_yields_low_precision(self, evaluator):
        code_audit = _code_audit()  # impacts payment-gateway
        # Historical detective (incorrectly) retrieved the user-service incident instead.
        historical = _historical(
            similar_outages=[
                SimilarOutageFinding(
                    incident_id="inc-002",
                    title="User Login Failures",
                    similarity_score=0.4,
                    root_cause="Memory corruption",
                    mitigation_used="Cleared cache",
                )
            ]
        )
        result = evaluator.evaluate_context_precision_recall(code_audit, historical, INCIDENT_CORPUS)

        assert result.precision_at_k == 0.0
        assert "inc-001" in result.relevant_incident_ids

    def test_no_relevant_incidents_in_corpus_gives_vacuous_perfect_recall(self, evaluator):
        code_audit = _code_audit(
            inferred_change_type="CONFIGURATION_CHANGE",
            impacted_applications=[
                ImpactedApplication(service_id="totally-unrelated-service", service_name="totally-unrelated-service", criticality="low", relationship="target")
            ],
        )
        historical = _historical(similar_outages=[])
        result = evaluator.evaluate_context_precision_recall(code_audit, historical, INCIDENT_CORPUS)

        assert result.relevant_incident_ids == []
        assert result.recall_at_k == 1.0


class TestFaithfulness:
    def test_claims_naming_known_entities_are_fully_faithful(self, evaluator):
        code_audit = _code_audit()
        historical = _historical()
        risk_report = _risk_report(
            top_risks=["Critical dependency at risk: 'payment-gateway' (critical)."],
            step_by_step_mitigation=[MitigationStep(step_number=1, action="Deploy to staging first.", owner_team="SRE")],
        )
        result = evaluator.evaluate_faithfulness(risk_report, code_audit, historical)

        assert result.score == 1.0
        assert result.unsupported_claims == []

    def test_claim_naming_unknown_entity_is_flagged_as_unsupported(self, evaluator):
        code_audit = _code_audit()
        historical = _historical()
        risk_report = _risk_report(
            top_risks=["Critical dependency at risk: 'totally-fictitious-service-xyz' (critical)."],
        )
        result = evaluator.evaluate_faithfulness(risk_report, code_audit, historical)

        assert result.score < 1.0
        assert any("fictitious" in c for c in result.unsupported_claims)

    def test_generic_non_specific_claims_are_never_flagged(self, evaluator):
        code_audit = _code_audit()
        historical = _historical()
        risk_report = _risk_report(
            top_risks=["Standard deployment risk applies."],
            step_by_step_mitigation=[MitigationStep(step_number=1, action="Monitor error rates for 24 hours.", owner_team="SRE")],
        )
        result = evaluator.evaluate_faithfulness(risk_report, code_audit, historical)

        assert result.score == 1.0

    def test_fallback_output_is_also_supported_by_evaluator(self, evaluator):
        code_audit = _code_audit()
        historical = _historical()
        fallback = MalformedOutputFallback(applications_impacted=["payment-gateway"])
        result = evaluator.evaluate_faithfulness(fallback, code_audit, historical)
        assert 0.0 <= result.score <= 1.0


class TestGroundTruthDelta:
    def test_no_variance_warning_when_ai_score_close_to_baseline(self, evaluator):
        code_audit = _code_audit()
        historical = _historical()
        # First pass with an arbitrary valid placeholder score just to read
        # off the independently-computed deterministic baseline...
        base = evaluator.compute_ground_truth_delta(
            ai_risk_score=1,
            code_audit=code_audit,
            historical=historical,
            sanitized_diff_text="",
        )
        # ...then re-run using that exact baseline as the "AI score" to
        # assert zero deviation is reported when the two agree perfectly.
        close_score = base.deterministic_baseline_score
        result = evaluator.compute_ground_truth_delta(close_score, code_audit, historical, "")
        assert result.high_variance_warning is False
        assert result.percentage_deviation == 0.0

    def test_variance_warning_flagged_when_deviation_exceeds_threshold(self, evaluator):
        code_audit = _code_audit()
        historical = _historical()
        result = evaluator.compute_ground_truth_delta(1, code_audit, historical, "")
        assert result.percentage_deviation > 20.0
        assert result.high_variance_warning is True

    def test_db_and_api_literal_counts_increase_baseline_score(self, evaluator):
        code_audit = _code_audit()
        historical = _historical()
        no_diff = evaluator.compute_ground_truth_delta(50, code_audit, historical, "")
        with_diff = evaluator.compute_ground_truth_delta(
            50, code_audit, historical,
            "SELECT * FROM orders;\n@PostMapping(\"/orders\")\n@GetMapping(\"/orders\")\n",
        )
        assert with_diff.baseline_components["db_call_component"] > no_diff.baseline_components["db_call_component"]
        assert with_diff.baseline_components["api_alteration_component"] > no_diff.baseline_components["api_alteration_component"]


class TestEvaluateOrchestration:
    def test_trusted_verdict_for_well_grounded_low_variance_prediction(self, evaluator):
        code_audit = _code_audit()
        historical = _historical()
        baseline = evaluator.compute_ground_truth_delta(50, code_audit, historical, "")
        risk_report = _risk_report(
            risk_score=baseline.deterministic_baseline_score,
            top_risks=["Critical dependency at risk: 'payment-gateway' (critical)."],
        )

        report = evaluator.evaluate(
            code_audit=code_audit,
            historical=historical,
            final_output=risk_report,
            sanitized_diff_text="",
            all_incidents=INCIDENT_CORPUS,
        )

        assert report.overall_verdict == EvaluationVerdict.TRUSTED
        assert report.evaluated_at_ms > 0

    def test_low_confidence_flagged_when_faithfulness_very_low(self, evaluator):
        code_audit = _code_audit()
        historical = _historical()
        risk_report = _risk_report(
            top_risks=[
                "Critical dependency at risk: 'fictitious-service-1' (critical).",
                "Critical dependency at risk: 'fictitious-service-2' (critical).",
            ],
        )

        report = evaluator.evaluate(
            code_audit=code_audit,
            historical=historical,
            final_output=risk_report,
            sanitized_diff_text="",
            all_incidents=INCIDENT_CORPUS,
        )

        assert report.overall_verdict in (EvaluationVerdict.LOW_CONFIDENCE_FLAGGED, EvaluationVerdict.REVIEW_RECOMMENDED)

    def test_evaluate_never_raises_even_with_malformed_fallback_output(self, evaluator):
        code_audit = _code_audit()
        historical = _historical()
        fallback = MalformedOutputFallback(applications_impacted=["payment-gateway"])

        report = evaluator.evaluate(
            code_audit=code_audit,
            historical=historical,
            final_output=fallback,
            sanitized_diff_text="",
            all_incidents=INCIDENT_CORPUS,
        )
        assert report is not None
