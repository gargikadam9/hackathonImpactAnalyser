/**
 * MODULE 6 — Adapter functions.
 *
 * Bridge the two backend response shapes this project ships today —
 * the legacy v1 mock 7-agent `ChangeImpactResponse` and the hardened v2
 * ReAct `FullAnalysisResponseV2` — into the small, presentation-only prop
 * shapes consumed by components/dashboard/*.
 *
 * Keeping this mapping logic in one place means that when new UI mockups
 * are supplied, only these adapters (or the dashboard prop types) need to
 * change — the API response types and the presentational components stay
 * untouched.
 */

import type { ChangeImpactResponse } from '../types'
import type { FullAnalysisResponseV2 } from '../types/reactAnalysis'
import type {
  CriticalityLevel,
  DependencyNode,
  EvaluationScorecardProps,
  IncidentMatch,
  RiskAttributionBreakdownProps,
  RiskDriverView,
  RiskGaugeMetricsProps,
  RiskLevelLabel,
  RiskMetric,
} from '../components/dashboard/types'

function normalizeCriticality(value: string | undefined): CriticalityLevel {
  const v = (value ?? '').toLowerCase()
  if (v === 'low' || v === 'medium' || v === 'high' || v === 'critical') return v
  return 'medium'
}

function normalizeRiskLevel(value: string | undefined): RiskLevelLabel {
  const v = (value ?? '').toLowerCase()
  if (v === 'low' || v === 'medium' || v === 'high' || v === 'critical') return v
  return 'medium'
}

// ---------------------------------------------------------------------------
// v1 (legacy mock 7-agent pipeline) adapters
// ---------------------------------------------------------------------------

export function riskGaugeMetricsFromV1(report: ChangeImpactResponse): RiskGaugeMetricsProps {
  const secondaryMetrics: RiskMetric[] = [
    {
      key: 'confidence',
      label: 'Confidence',
      value: report.confidence * 100,
      displayValue: `${Math.round(report.confidence * 100)}%`,
      tone: report.confidence >= 0.8 ? 'positive' : 'neutral',
    },
    {
      key: 'services-impacted',
      label: 'Services Impacted',
      value: Math.min(report.impactedServices.length * 10, 100),
      displayValue: `${report.impactedServices.length}`,
      tone: report.impactedServices.length > 5 ? 'warning' : 'neutral',
    },
    {
      key: 'similar-incidents',
      label: 'Similar Incidents',
      value: Math.min(report.similarIncidents.length * 20, 100),
      displayValue: `${report.similarIncidents.length}`,
      tone: report.similarIncidents.length > 0 ? 'warning' : 'positive',
    },
    {
      key: 'processing-time',
      label: 'Processing Time',
      value: Math.min((report.processingTimeMs / 5000) * 100, 100),
      displayValue: `${(report.processingTimeMs / 1000).toFixed(1)}s`,
      tone: 'neutral',
    },
  ]

  return {
    analysisId: report.analysisId,
    primaryScore: Math.round(report.riskScore * 100),
    riskLevel: normalizeRiskLevel(report.riskLevel),
    confidence: report.confidence,
    secondaryMetrics,
    isMockMode: report.mockMode,
  }
}

export function dependencyNodesFromV1(report: ChangeImpactResponse): {
  rootId: string
  nodes: DependencyNode[]
} {
  const nodes: DependencyNode[] = report.impactedServices.map((serviceName, index) => ({
    id: serviceName,
    name: serviceName,
    criticality: 'medium',
    relationship: index === 0 ? 'target' : 'direct_dependency',
  }))
  return { rootId: report.impactedServices[0] ?? 'unknown', nodes }
}

export function incidentMatchesFromV1(report: ChangeImpactResponse): IncidentMatch[] {
  return report.similarIncidents.map((incident) => ({
    id: incident.id,
    title: incident.title,
    severity: incident.severity,
    service: incident.service,
    similarityScore: incident.similarity_score ?? 0,
    rootCause: incident.root_cause,
    mitigationUsed: incident.resolution,
  }))
}

// ---------------------------------------------------------------------------
// v2 (hardened ReAct pipeline) adapters — richer, structured source data
// ---------------------------------------------------------------------------

export function riskGaugeMetricsFromV2(report: FullAnalysisResponseV2): RiskGaugeMetricsProps {
  const secondaryMetrics: RiskMetric[] = [
    {
      key: 'confidence',
      label: 'Confidence',
      value: report.confidence * 100,
      displayValue: `${Math.round(report.confidence * 100)}%`,
      tone: report.confidence >= 0.8 ? 'positive' : 'neutral',
    },
    {
      key: 'blast-radius',
      label: 'Blast Radius',
      value: report.code_audit.blast_radius_score,
      displayValue: `${report.code_audit.blast_radius_score}/100`,
      tone: report.code_audit.blast_radius_score >= 60 ? 'critical' : report.code_audit.blast_radius_score >= 30 ? 'warning' : 'positive',
    },
    {
      key: 'historical-signal',
      label: 'Historical Signal',
      value:
        report.historical_findings.historical_severity_signal === 'severe'
          ? 100
          : report.historical_findings.historical_severity_signal === 'moderate'
          ? 60
          : report.historical_findings.historical_severity_signal === 'low'
          ? 30
          : 0,
      displayValue: report.historical_findings.historical_severity_signal.toUpperCase(),
      tone:
        report.historical_findings.historical_severity_signal === 'severe'
          ? 'critical'
          : report.historical_findings.historical_severity_signal === 'moderate'
          ? 'warning'
          : 'positive',
    },
    {
      key: 'processing-time',
      label: 'Processing Time',
      value: Math.min((report.processing_time_ms / 5000) * 100, 100),
      displayValue: `${(report.processing_time_ms / 1000).toFixed(1)}s`,
      tone: 'neutral',
    },
  ]

  return {
    analysisId: report.analysis_id,
    primaryScore: report.risk_score,
    riskLevel: normalizeRiskLevel(report.risk_level),
    confidence: report.confidence,
    secondaryMetrics,
    isMockMode: report.mock_mode,
  }
}

export function dependencyNodesFromV2(report: FullAnalysisResponseV2): {
  rootId: string
  nodes: DependencyNode[]
} {
  const nodes: DependencyNode[] = report.code_audit.impacted_applications.map((app) => ({
    id: app.service_id,
    name: app.service_name,
    criticality: normalizeCriticality(app.criticality),
    relationship:
      app.relationship === 'target' || app.relationship === 'downstream_cascade'
        ? app.relationship
        : 'direct_dependency',
  }))
  return { rootId: report.code_audit.primary_component, nodes }
}

export function incidentMatchesFromV2(report: FullAnalysisResponseV2): IncidentMatch[] {
  return report.historical_findings.similar_outages.map((outage) => ({
    id: outage.incident_id,
    title: outage.title,
    severity: report.historical_findings.historical_severity_signal,
    service: report.code_audit.primary_component,
    similarityScore: outage.similarity_score,
    rootCause: outage.root_cause,
    mitigationUsed: outage.mitigation_used,
  }))
}

// ---------------------------------------------------------------------------
// MODULE 7 — Explainable AI (XAI) & Attribution Pipeline adapter
// ---------------------------------------------------------------------------

export function riskAttributionFromV2(report: FullAnalysisResponseV2): RiskAttributionBreakdownProps {
  const drivers: RiskDriverView[] = report.explainability_report.primary_risk_drivers.map((driver) => ({
    id: driver.driver_id,
    codeSnippet: driver.code_snippet,
    filePath: driver.file_path,
    severityWeight: driver.severity_weight,
    justification: driver.justification_text,
    category: driver.category,
  }))

  return {
    riskScore: report.risk_score,
    drivers,
    historicalCorrelationFactor: report.explainability_report.historical_correlation_factor,
    totalAttributedWeight: report.explainability_report.total_attributed_weight,
  }
}

// ---------------------------------------------------------------------------
// MODULE 8 — Automated Evaluation Metric & Ground-Truth Scoring adapter
// ---------------------------------------------------------------------------

export function evaluationScorecardFromV2(report: FullAnalysisResponseV2): EvaluationScorecardProps {
  const evaluation = report.evaluation_report
  return {
    verdict: evaluation.overall_verdict,
    faithfulnessScore: evaluation.faithfulness.score,
    unsupportedClaims: evaluation.faithfulness.unsupported_claims,
    contextPrecision: evaluation.context_precision_recall.precision_at_k,
    contextRecall: evaluation.context_precision_recall.recall_at_k,
    contextF1: evaluation.context_precision_recall.f1_score,
    aiPredictedScore: evaluation.ground_truth_delta.ai_predicted_score,
    deterministicBaselineScore: evaluation.ground_truth_delta.deterministic_baseline_score,
    percentageDeviation: evaluation.ground_truth_delta.percentage_deviation,
    highVarianceWarning: evaluation.ground_truth_delta.high_variance_warning,
    evaluatorVersion: evaluation.evaluator_version,
  }
}
