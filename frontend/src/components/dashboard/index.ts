/**
 * MODULE 6 — Barrel export for the modular dashboard component blueprint.
 * Also exports the MODULE 7 (Explainable AI) and MODULE 8 (Evaluation
 * Framework + Feedback) dashboard components.
 *
 * Import everything the dashboard needs from this single entry point:
 *   import { RiskGaugeMetrics, DependencyMap, IncidentMatchCards } from './components/dashboard'
 */

export { default as RiskGaugeMetrics } from './RiskGaugeMetrics'
export { default as DependencyMap } from './DependencyMap'
export { default as IncidentMatchCards } from './IncidentMatchCard'
export { default as RiskAttributionBreakdown } from './RiskAttributionBreakdown'
export { default as EvaluationScorecard } from './EvaluationScorecard'
export { default as FeedbackWidget } from './FeedbackWidget'

export type {
  RiskGaugeMetricsProps,
  RiskMetric,
  DependencyMapProps,
  DependencyNode,
  DependencyEdge,
  DependencyRelationship,
  CriticalityLevel,
  RiskLevelLabel,
  IncidentMatchCardsProps,
  IncidentMatch,
  RiskDriverView,
  RiskAttributionBreakdownProps,
  EvaluationVerdictLabel,
  EvaluationScorecardProps,
  FeedbackWidgetProps,
} from './types'
