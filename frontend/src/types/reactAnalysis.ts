/**
 * TypeScript mirror of ai-service/app/agents/react/api_models.py
 * (the v2 ReAct pipeline's FullAnalysisResponseV2 contract).
 */

export interface MitigationStep {
  step_number: number
  action: string
  owner_team?: string | null
}

export interface RedactionEvent {
  category: string
  tag_used: string
  span_start: number
  span_end: number
  matched_length: number
  detector: string
}

export interface RedactionReport {
  total_redactions: number
  redactions_by_category: Record<string, number>
  events: RedactionEvent[]
  is_safe_for_llm: boolean
}

export interface ReactStepTrace {
  iteration: number
  thought: string
  action?: string | null
  action_input?: Record<string, unknown> | null
  observation?: Record<string, unknown> | null
  is_final_step: boolean
}

export interface AgentExecutionTrace {
  agent_name: string
  steps: ReactStepTrace[]
  hit_iteration_cap: boolean
  used_fallback: boolean
  elapsed_ms: number
}

export interface TouchedSymbol {
  symbol_name: string
  file_path: string
  change_kind: string
}

export interface ImpactedApplication {
  service_id: string
  service_name: string
  criticality: string
  relationship: string
}

export interface CodeAuditReport {
  inferred_change_type: string
  primary_component: string
  touched_symbols: TouchedSymbol[]
  impacted_applications: ImpactedApplication[]
  blast_radius_score: number
  reasoning: string[]
}

export interface SimilarOutageFinding {
  incident_id: string
  title: string
  similarity_score: number
  root_cause: string
  mitigation_used: string
}

export interface HistoricalFindingsReport {
  similar_outages: SimilarOutageFinding[]
  historical_severity_signal: string
  recurring_pattern_summary: string
  reasoning: string[]
}

/**
 * MODULE 7 — Explainable AI (XAI) & Attribution Pipeline.
 * Mirrors ai-service/app/agents/schemas.py::RiskDriver / ExplainabilityReport.
 */
export interface RiskDriver {
  driver_id: string
  code_snippet: string
  file_path?: string | null
  /** Percentage (0-100) contribution to the total risk_score. */
  severity_weight: number
  justification_text: string
  category: 'blast_radius' | 'criticality' | 'historical_precedent' | 'change_type_baseline' | string
}

export interface ExplainabilityReport {
  primary_risk_drivers: RiskDriver[]
  historical_correlation_factor: string
  total_attributed_weight: number
  generated_at_ms: number
}

/**
 * MODULE 8 — Automated Evaluation Metric & Ground-Truth Scoring Pipeline.
 * Mirrors ai-service/app/evaluation/schemas.py.
 */
export interface ContextPrecisionRecall {
  precision_at_k: number
  recall_at_k: number
  f1_score: number
  k: number
  retrieved_incident_ids: string[]
  relevant_incident_ids: string[]
  methodology: string
}

export interface FaithfulnessScore {
  score: number
  unsupported_claims: string[]
  supported_claims: string[]
  total_claims_checked: number
  llm_judge_score?: number | null
  methodology: string
}

export interface GroundTruthDelta {
  ai_predicted_score: number
  deterministic_baseline_score: number
  absolute_delta: number
  percentage_deviation: number
  high_variance_warning: boolean
  baseline_components: Record<string, number>
  baseline_formula_version: string
}

export type EvaluationVerdict = 'TRUSTED' | 'REVIEW_RECOMMENDED' | 'LOW_CONFIDENCE_FLAGGED'

export interface EvaluationReport {
  context_precision_recall: ContextPrecisionRecall
  faithfulness: FaithfulnessScore
  ground_truth_delta: GroundTruthDelta
  overall_verdict: EvaluationVerdict
  evaluator_version: string
  evaluated_at_ms: number
}

export interface FeedbackEntry {
  analysis_id: string
  vote?: 'up' | 'down' | null
  overridden_risk_score?: number | null
  comment?: string | null
  submitted_by?: string | null
}

export interface FeedbackCaptureResponse {
  status: string
  feedback_id: string
  stored_at: string
}

export interface FullAnalysisResponseV2 {
  analysis_id: string
  risk_score: number
  risk_level: string
  top_risks: string[]
  applications_impacted: string[]
  teams_notified: string[]
  step_by_step_mitigation: MitigationStep[]
  confidence: number
  executive_summary: string
  is_fallback: boolean

  code_audit: CodeAuditReport
  historical_findings: HistoricalFindingsReport
  redaction_report: RedactionReport
  agent_traces: AgentExecutionTrace[]

  /** MODULE 7 — why risk_score is what it is, line-item by line-item. */
  explainability_report: ExplainabilityReport
  /** MODULE 8 — independent post-hoc audit of this same prediction. */
  evaluation_report: EvaluationReport

  processing_time_ms: number
  mock_mode: boolean
}

export interface ChangeAnalysisRequestV2 {
  change_title: string
  change_description: string
  target_component: string
  change_type?: string
  raw_diff_text?: string
  environment?: string
  requested_by?: string
}
