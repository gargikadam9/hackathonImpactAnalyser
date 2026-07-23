export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface AgentTrace {
  agent: string
  status: string
  input?: string
  output?: string
  processingTimeMs: number
  error?: string
  evidence?: Array<Record<string, unknown>>
}

export interface SimilarIncident {
  id: string
  title: string
  severity: string
  service: string
  resolution: string
  root_cause?: string
  similarity_score?: number
}

export interface ChangeImpactResponse {
  analysisId: string
  riskScore: number
  riskLevel: string
  confidence: number
  impactedServices: string[]
  teamsToNotify: string[]
  potentialRisks: string[]
  recommendedTests: string[]
  similarIncidents: SimilarIncident[]
  mitigationPlan: string[]
  executiveSummary: string
  agentTraces: AgentTrace[]
  interpretedIntent: string
  retrievedEvidence: Array<Record<string, unknown>>
  dataSourcesUsed: string[]
  processingTimeMs: number
  mockMode: boolean
}

export interface ChangeType {
  id: string
  name: string
  description: string
  risk_default: string
}

export interface Component {
  id: string
  name: string
  type: string
  criticality: string
  owner: string
  dependencies: string[]
}

export interface AssistantResponse {
  classification: string
  reply: string
  extracted_intent?: Record<string, unknown>
  suggested_actions?: string[]
}

export interface ChatResponse {
  reply: string
  conversation_id?: string
  intent?: string
  processingTimeMs?: number
}

export type AnalysisMode = 'chat' | 'form'
export type TabView = 'overview' | 'understanding' | 'evidence' | 'incidents' | 'mitigation' | 'trace'

