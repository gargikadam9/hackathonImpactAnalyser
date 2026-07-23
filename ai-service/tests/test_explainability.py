"""
Tests for MODULE 7 — Explainable AI (XAI) & Attribution Pipeline.
"""

import pytest

from app.agents.react.explainability import build_attribution_matrix
from app.agents.react.tools import score_risk_matrix
from app.agents.schemas import (
    CodeAuditReport,
    HistoricalFindingsReport,
    ImpactedApplication,
    SimilarOutageFinding,
    TouchedSymbol,
)


def _code_audit(**overrides) -> CodeAuditReport:
    defaults = dict(
        inferred_change_type="DATABASE_MIGRATION",
        primary_component="payment-gateway",
        touched_symbols=[
            TouchedSymbol(symbol_name="chargeCard", file_path="src/PaymentService.java", change_kind="modified"),
            TouchedSymbol(symbol_name="refund", file_path="src/PaymentService.java", change_kind="added"),
        ],
        impacted_applications=[
            ImpactedApplication(service_id="payment-gateway", service_name="payment-gateway", criticality="critical", relationship="target"),
            ImpactedApplication(service_id="order-service", service_name="order-service", criticality="high", relationship="downstream_cascade"),
        ],
        blast_radius_score=72,
        reasoning=["Parsed diff.", "Traced dependency graph."],
    )
    defaults.update(overrides)
    return CodeAuditReport(**defaults)


def _historical(**overrides) -> HistoricalFindingsReport:
    defaults = dict(
        similar_outages=[
            SimilarOutageFinding(
                incident_id="inc-001",
                title="Payment Gateway Outage",
                similarity_score=0.87,
                root_cause="Database connection leak under high load",
                mitigation_used="Increased connection pool size from 50 to 200",
            )
        ],
        historical_severity_signal="severe",
        recurring_pattern_summary="Most similar past incident is 'Payment Gateway Outage'.",
        reasoning=["Vector search backend: InMemoryCosineIndex."],
    )
    defaults.update(overrides)
    return HistoricalFindingsReport(**defaults)


class TestBuildAttributionMatrix:
    def test_drivers_sum_to_approximately_full_weight(self):
        code_audit = _code_audit()
        historical = _historical()
        score_result = score_risk_matrix(code_audit=code_audit.model_dump(), historical=historical.model_dump())

        report = build_attribution_matrix(
            code_audit=code_audit,
            historical=historical,
            sanitized_diff_text="+public void chargeCard() {}\n+public void refund() {}\n",
            risk_score=score_result["risk_score"],
            score_components=score_result["components"],
        )

        assert 1 <= len(report.primary_risk_drivers) <= 10
        # Weights are percentages of the SAME components dict; they must sum
        # close to 100 (allowing for rounding across multiple drivers).
        assert 95.0 <= report.total_attributed_weight <= 100.0
        assert report.generated_at_ms > 0

    def test_every_driver_has_a_non_empty_justification_and_valid_category(self):
        code_audit = _code_audit()
        historical = _historical()
        score_result = score_risk_matrix(code_audit=code_audit.model_dump(), historical=historical.model_dump())

        report = build_attribution_matrix(
            code_audit=code_audit,
            historical=historical,
            sanitized_diff_text=None,
            risk_score=score_result["risk_score"],
            score_components=score_result["components"],
        )

        valid_categories = {"blast_radius", "criticality", "historical_precedent", "change_type_baseline"}
        for driver in report.primary_risk_drivers:
            assert driver.justification_text.strip() != ""
            assert driver.category in valid_categories
            assert 0.0 <= driver.severity_weight <= 100.0

    def test_code_snippet_extracted_from_diff_when_available(self):
        code_audit = _code_audit()
        historical = _historical(similar_outages=[])
        diff_text = (
            "diff --git a/src/PaymentService.java b/src/PaymentService.java\n"
            "+public void chargeCard() { doCharge(); }\n"
        )
        score_result = score_risk_matrix(code_audit=code_audit.model_dump(), historical=historical.model_dump())

        report = build_attribution_matrix(
            code_audit=code_audit,
            historical=historical,
            sanitized_diff_text=diff_text,
            risk_score=score_result["risk_score"],
            score_components=score_result["components"],
        )

        blast_drivers = [d for d in report.primary_risk_drivers if d.category == "blast_radius"]
        assert any("chargeCard" in d.code_snippet for d in blast_drivers)

    def test_no_diff_supplied_produces_labeled_structural_placeholder(self):
        code_audit = _code_audit(touched_symbols=[])
        historical = _historical(similar_outages=[])
        score_result = score_risk_matrix(code_audit=code_audit.model_dump(), historical=historical.model_dump())

        report = build_attribution_matrix(
            code_audit=code_audit,
            historical=historical,
            sanitized_diff_text=None,
            risk_score=score_result["risk_score"],
            score_components=score_result["components"],
        )

        # No touched symbols -> blast radius driver falls back to a
        # structural descriptor, never a fabricated code snippet.
        assert not any("chargeCard" in d.code_snippet for d in report.primary_risk_drivers)

    def test_historical_correlation_factor_references_incident_when_present(self):
        code_audit = _code_audit()
        historical = _historical()
        score_result = score_risk_matrix(code_audit=code_audit.model_dump(), historical=historical.model_dump())

        report = build_attribution_matrix(
            code_audit=code_audit,
            historical=historical,
            sanitized_diff_text=None,
            risk_score=score_result["risk_score"],
            score_components=score_result["components"],
        )

        assert "inc-001" in report.historical_correlation_factor or "Payment Gateway Outage" in report.historical_correlation_factor

    def test_historical_correlation_factor_explicit_when_no_outages_found(self):
        code_audit = _code_audit()
        historical = _historical(similar_outages=[], historical_severity_signal="none")
        score_result = score_risk_matrix(code_audit=code_audit.model_dump(), historical=historical.model_dump())

        report = build_attribution_matrix(
            code_audit=code_audit,
            historical=historical,
            sanitized_diff_text=None,
            risk_score=score_result["risk_score"],
            score_components=score_result["components"],
        )

        assert "No sufficiently similar historical incident" in report.historical_correlation_factor

    def test_never_returns_empty_driver_list_even_with_all_zero_components(self):
        code_audit = _code_audit(touched_symbols=[], impacted_applications=[
            ImpactedApplication(service_id="x", service_name="x", criticality="low", relationship="target")
        ], blast_radius_score=0)
        historical = _historical(similar_outages=[], historical_severity_signal="none")

        report = build_attribution_matrix(
            code_audit=code_audit,
            historical=historical,
            sanitized_diff_text=None,
            risk_score=15,
            score_components={
                "base_change_type_risk": 0,
                "blast_radius_component": 0,
                "criticality_component": 0,
                "historical_severity_component": 0,
            },
        )

        assert len(report.primary_risk_drivers) >= 1
