"""
MODULE 7 — Explainable AI (XAI) & Attribution Pipeline.

The dashboard must not just show a raw "Risk Score: 85/100" — it must
explain *exactly why* that score was assigned so developers trust it. This
module deterministically converts the SAME inputs `score_risk_matrix()`
(app/agents/react/tools.py) used to compute the numeric `risk_score` into a
strict, structured "Attribution Matrix": a small, auditable list of the
concrete signals (touched code lines, blast-radius percentage, historical
precedent, change-type baseline) that produced that score — each carrying an
explicit percentage weight so the sum is mathematically traceable back to
the actual computation.

This is deliberately NOT another free-form LLM narrative. Every field here
is derived directly from already-validated `CodeAuditReport` /
`HistoricalFindingsReport` Pydantic models plus the exact `components` dict
returned by `score_risk_matrix()`, so the explanation can never diverge from
what was actually computed (no risk of an LLM "explaining" a number it
didn't really use).
"""

from __future__ import annotations

import re
import time
from typing import Dict, List, Optional

from app.agents.schemas import (
    CodeAuditReport,
    ExplainabilityReport,
    HistoricalFindingsReport,
    RiskDriver,
)

_MAX_SNIPPET_CHARS = 240
_DIFF_FILE_HEADER_RE = re.compile(r"^diff --git a/(\S+) b/(\S+)")


def _extract_snippet_for_symbol(diff_text: str, symbol_name: str, file_path: str) -> str:
    """
    Best-effort extraction of the diff line(s) that introduced/modified
    `symbol_name`, so the UI can literally highlight "the exact lines
    causing risk" rather than paraphrasing them.

    Falls back to a clearly-labeled structural descriptor when no diff text
    is available (e.g. a form-only submission with no raw_diff_text) — the
    UI must never fabricate a code snippet that was not actually supplied.
    """
    if not diff_text or not diff_text.strip():
        return f"(no diff supplied — structural signal only: symbol '{symbol_name}' in {file_path})"

    matched_lines: List[str] = []
    current_file = "unknown"

    for line in diff_text.splitlines():
        header_match = _DIFF_FILE_HEADER_RE.match(line)
        if header_match:
            current_file = header_match.group(2)
            continue
        if file_path != "unknown" and current_file != file_path:
            continue
        if line.startswith("+") and not line.startswith("+++") and symbol_name in line:
            matched_lines.append(line[1:].strip())

    if not matched_lines:
        return f"(symbol '{symbol_name}' flagged by AST diff parse; no single-line textual match in {file_path})"

    snippet = "\n".join(matched_lines[:5])
    return snippet[:_MAX_SNIPPET_CHARS]


def build_attribution_matrix(
    code_audit: CodeAuditReport,
    historical: HistoricalFindingsReport,
    sanitized_diff_text: Optional[str],
    risk_score: int,
    score_components: Dict[str, int],
) -> ExplainabilityReport:
    """
    Build the strict `ExplainabilityReport` attached to every
    `FullAnalysisResponseV2`.

    `score_components` MUST be the `components` dict returned by
    `score_risk_matrix()` (app/agents/react/tools.py) for THIS SAME
    code_audit/historical pair, so every driver's `severity_weight` is a
    real percentage of the actual formula inputs — never a separately
    re-derived or LLM-guessed number.
    """
    total = max(sum(score_components.values()), 1)
    drivers: List[RiskDriver] = []
    driver_counter = 1
    # `inferred_change_type` is a `str, Enum` mixin; `.value` gives the clean
    # "INFRASTRUCTURE_UPGRADE" form for display text (str(enum) can render as
    # "ChangeTypeEnum.INFRASTRUCTURE_UPGRADE" depending on Python version).
    change_type_display = getattr(code_audit.inferred_change_type, "value", code_audit.inferred_change_type)

    # --- Driver group 1: touched symbols / blast radius --------------------
    blast_weight_pct = round((score_components.get("blast_radius_component", 0) / total) * 100, 2)
    if code_audit.touched_symbols:
        # Distribute the blast-radius weight across the (bounded) set of
        # touched symbols so the biggest, most-directly-implicated code
        # change gets an explicit, individually-labeled slice of the risk.
        top_symbols = code_audit.touched_symbols[:5]
        per_symbol_weight = round(blast_weight_pct / max(len(top_symbols), 1), 2)
        for symbol in top_symbols:
            drivers.append(
                RiskDriver(
                    driver_id=f"driver-{driver_counter}",
                    code_snippet=_extract_snippet_for_symbol(
                        sanitized_diff_text or "", symbol.symbol_name, symbol.file_path
                    ),
                    file_path=symbol.file_path,
                    severity_weight=per_symbol_weight,
                    justification_text=(
                        f"Symbol '{symbol.symbol_name}' was {symbol.change_kind} in "
                        f"{symbol.file_path}, contributing to a blast radius of "
                        f"{code_audit.blast_radius_score}/100 across "
                        f"{len(code_audit.impacted_applications)} service(s)."
                    ),
                    category="blast_radius",
                )
            )
            driver_counter += 1
    elif blast_weight_pct > 0:
        drivers.append(
            RiskDriver(
                driver_id=f"driver-{driver_counter}",
                code_snippet=(
                    "(no line-level diff supplied; blast radius computed from "
                    "target_component dependency-graph traversal)"
                ),
                file_path=None,
                severity_weight=blast_weight_pct,
                justification_text=(
                    f"Dependency graph traversal from '{code_audit.primary_component}' reached "
                    f"{len(code_audit.impacted_applications)} service(s), yielding a blast-radius "
                    f"score of {code_audit.blast_radius_score}/100."
                ),
                category="blast_radius",
            )
        )
        driver_counter += 1

    # --- Driver group 2: criticality of impacted applications --------------
    criticality_weight_pct = round((score_components.get("criticality_component", 0) / total) * 100, 2)
    critical_apps = [a for a in code_audit.impacted_applications if a.criticality in ("high", "critical")]
    if critical_apps and criticality_weight_pct > 0:
        per_app_weight = round(criticality_weight_pct / len(critical_apps[:3]), 2)
        for app in critical_apps[:3]:
            drivers.append(
                RiskDriver(
                    driver_id=f"driver-{driver_counter}",
                    code_snippet=f"(structural signal) impacted_applications[] entry: {app.service_name}",
                    file_path=None,
                    severity_weight=per_app_weight,
                    justification_text=(
                        f"'{app.service_name}' is a {app.criticality}-criticality service in the "
                        f"{app.relationship.replace('_', ' ')} path of this change."
                    ),
                    category="criticality",
                )
            )
            driver_counter += 1

    # --- Driver group 3: change-type baseline -------------------------------
    base_weight_pct = round((score_components.get("base_change_type_risk", 0) / total) * 100, 2)
    if base_weight_pct > 0:
        drivers.append(
            RiskDriver(
                driver_id=f"driver-{driver_counter}",
                code_snippet=f"(structural signal) inferred_change_type = {change_type_display}",
                file_path=None,
                severity_weight=base_weight_pct,
                justification_text=(
                    f"Changes classified as '{change_type_display}' carry a fixed "
                    f"baseline risk weight under the versioned deterministic scoring formula "
                    f"(score_risk_matrix, formula_version=v1.0-deterministic-weighted-sum)."
                ),
                category="change_type_baseline",
            )
        )
        driver_counter += 1

    # --- Driver group 4: historical severity precedent ----------------------
    history_weight_pct = round((score_components.get("historical_severity_component", 0) / total) * 100, 2)
    historical_correlation_factor = (
        "No sufficiently similar historical incident was found in the vector index; this "
        "component of the risk score is driven purely by structural code-impact signals "
        "(blast radius, criticality, change type), not historical precedent."
    )
    if historical.similar_outages and history_weight_pct > 0:
        top_outage = historical.similar_outages[0]
        drivers.append(
            RiskDriver(
                driver_id=f"driver-{driver_counter}",
                code_snippet=f"(historical precedent) incident_id={top_outage.incident_id}",
                file_path=None,
                severity_weight=history_weight_pct,
                justification_text=(
                    f"Historically similar to incident '{top_outage.title}' "
                    f"(similarity {top_outage.similarity_score:.2f}), root cause: "
                    f"{top_outage.root_cause}."
                ),
                category="historical_precedent",
            )
        )
        driver_counter += 1
        historical_correlation_factor = (
            f"This change's code-impact signature (change type "
            f"'{change_type_display}', touching '{code_audit.primary_component}' and "
            f"cascading to {len(code_audit.impacted_applications)} service(s)) matches the pattern "
            f"that preceded incident '{top_outage.incident_id}: {top_outage.title}' "
            f"(similarity={top_outage.similarity_score:.2f}). Root cause on record: "
            f"'{top_outage.root_cause}'; resolved via: '{top_outage.mitigation_used}'. "
            f"Historical severity signal for this change class is "
            f"'{historical.historical_severity_signal}'."
        )

    if not drivers:
        # Never return an empty attribution matrix — a risk score with zero
        # explained drivers is worse than a clearly-labeled placeholder that
        # tells the reviewer to treat the number conservatively.
        drivers.append(
            RiskDriver(
                driver_id="driver-1",
                code_snippet="(no structural drivers computed)",
                file_path=None,
                severity_weight=100.0,
                justification_text=(
                    "Insufficient structural signal (no touched symbols, no elevated "
                    "criticality, no historical precedent) to attribute risk to specific "
                    "drivers; treat this score as a conservative baseline default."
                ),
                category="change_type_baseline",
            )
        )

    total_attributed_weight = round(sum(d.severity_weight for d in drivers), 2)
    total_attributed_weight = min(total_attributed_weight, 100.0)

    return ExplainabilityReport(
        primary_risk_drivers=drivers[:10],
        historical_correlation_factor=historical_correlation_factor,
        total_attributed_weight=total_attributed_weight,
        generated_at_ms=int(time.time() * 1000),
    )
