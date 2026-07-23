/**
 * MODULE 6 — Dashboard component contracts.
 *
 * These types are intentionally decoupled from the exact backend response
 * shape (`ChangeImpactResponse` in ../../types/index.ts, or the v2 ReAct
 * `FullAnalysisResponseV2` shape). Decoupling via small adapter functions
 * (see ../../services/dashboardAdapters.ts) means these presentational
 * components can be re-wired against new visual mockups without touching
 * any API-response-shaped code.
 */

export type CriticalityLevel = 'low' | 'medium' | 'high' | 'critical'
export type RiskLevelLabel = 'low' | 'medium' | 'high' | 'critical'

export type DependencyRelationship =
  | 'target'
  | 'direct_dependency'
  | 'downstream_cascade'

/** A single secondary metric tile rendered next to the primary risk gauge. */
export interface RiskMetric {
  key: string
  label: string
  /** 0-100 normalized value, used to drive any progress-bar styling. */
  value: number
  /** Pre-formatted display string, e.g. "82ms", "95%", "12 services". */
  displayValue: string
  /** Optional icon key resolved by the consuming component (e.g. lucide-react name). */
  icon?: string
  tone?: 'neutral' | 'positive' | 'warning' | 'critical'
}

export interface RiskGaugeMetricsProps {
  analysisId: string
  /** 0-100 */
  primaryScore: number
  riskLevel: RiskLevelLabel
  /** 0-1 */
  confidence: number
  secondaryMetrics: RiskMetric[]
  isMockMode?: boolean
}

/** One node in the dependency graph — a service/component impacted by the change. */
export interface DependencyNode {
  id: string
  name: string
  criticality: CriticalityLevel
  relationship: DependencyRelationship
  owner?: string
  processes?: string[]
}

export interface DependencyEdge {
  fromId: string
  toId: string
}

export interface DependencyMapProps {
  rootId: string
  nodes: DependencyNode[]
  edges?: DependencyEdge[]
  onNodeSelect?: (node: DependencyNode) => void
  selectedNodeId?: string | null
}

/** One historical incident match returned by the RAG vector search (Module 3). */
export interface IncidentMatch {
  id: string
  title: string
  severity: string
  service: string
  /** 0-1 cosine similarity */
  similarityScore: number
  rootCause?: string
  mitigationUsed?: string
  occurredAt?: string
}

export interface IncidentMatchCardsProps {
  incidents: IncidentMatch[]
  emptyStateMessage?: string
  onSelectIncident?: (incident: IncidentMatch) => void
}

/**
 * MODULE 7 — Explainable AI (XAI) & Attribution Pipeline.
 * Presentation-only view model for one line-item in the risk attribution
 * breakdown (decoupled from ai-service's RiskDriver Pydantic shape via
 * services/dashboardAdapters.ts::riskAttributionFromV2).
 */
export interface RiskDriverView {
  id: string
  codeSnippet: string
  filePath?: string | null
  /** 0-100 */
  severityWeight: number
  justification: string
  category: 'blast_radius' | 'criticality' | 'historical_precedent' | 'change_type_baseline' | string
}

export interface RiskAttributionBreakdownProps {
  riskScore: number
  drivers: RiskDriverView[]
  historicalCorrelationFactor: string
  totalAttributedWeight: number
}

/**
 * MODULE 8 — Automated Evaluation Metric & Ground-Truth Scoring Pipeline.
 */
export type EvaluationVerdictLabel = 'TRUSTED' | 'REVIEW_RECOMMENDED' | 'LOW_CONFIDENCE_FLAGGED'

export interface EvaluationScorecardProps {
  verdict: EvaluationVerdictLabel
  faithfulnessScore: number
  unsupportedClaims: string[]
  contextPrecision: number
  contextRecall: number
  contextF1: number
  aiPredictedScore: number
  deterministicBaselineScore: number
  percentageDeviation: number
  highVarianceWarning: boolean
  evaluatorVersion: string
}

/**
 * MODULE 8 — Feedback capture (thumbs up/down + manual override).
 */
export interface FeedbackWidgetProps {
  analysisId: string
  currentRiskScore: number
  onSubmit: (feedback: {
    vote?: 'up' | 'down'
    overriddenRiskScore?: number
    comment?: string
  }) => Promise<void> | void
}
