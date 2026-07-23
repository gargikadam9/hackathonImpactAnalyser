import type { ChangeImpactResponse, AssistantResponse, ChatResponse, ChangeType, Component } from '../types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081'
const AI_SERVICE_URL = import.meta.env.VITE_AI_SERVICE_URL || 'http://localhost:8000'
const DIRECT_AI_MODE = import.meta.env.VITE_DIRECT_AI_MODE === 'true'

function getBaseUrl(path: string): string {
  if (DIRECT_AI_MODE) {
    return `${AI_SERVICE_URL}${path}`
  }
  return `${API_BASE}${path}`
}

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const url = getBaseUrl(path)
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`API Error (${response.status}): ${error}`)
  }

  return response.json()
}

// Health check
export async function checkHealth(): Promise<Record<string, unknown>> {
  const url = DIRECT_AI_MODE
    ? `${AI_SERVICE_URL}/health`
    : `${API_BASE}/actuator/health`
  const response = await fetch(url)
  return response.json()
}

// Assistant - Unified route
export async function assistantRespond(
  message: string,
  conversationHistory?: Array<{ role: string; content: string }>
): Promise<AssistantResponse> {
  return fetchApi<AssistantResponse>('/api/v1/assistant/respond', {
    method: 'POST',
    body: JSON.stringify({
      message,
      conversation_history: conversationHistory || [],
    }),
  })
}

// Chat - General conversation
export async function generalChat(
  message: string,
  conversationHistory?: Array<{ role: string; content: string }>
): Promise<ChatResponse> {
  return fetchApi<ChatResponse>('/api/v1/chat/general', {
    method: 'POST',
    body: JSON.stringify({
      message,
      conversation_history: conversationHistory || [],
    }),
  })
}

// Change Impact Analysis
export async function analyzeChangeImpact(data: {
  change_title: string
  change_description: string
  change_type: string
  affected_services?: string[]
  priority?: string
}): Promise<ChangeImpactResponse> {
  return fetchApi<ChangeImpactResponse>('/api/v1/change-impact/analyze', {
    method: 'POST',
    body: JSON.stringify({
      ...data,
      change_type: data.change_type || 'enhancement',
      priority: data.priority || 'medium',
    }),
  })
}

// Analyze from prompt
export async function analyzeChangeImpactFromPrompt(promptData: Record<string, unknown>): Promise<ChangeImpactResponse> {
  return fetchApi<ChangeImpactResponse>('/api/v1/change-impact/analyze-prompt', {
    method: 'POST',
    body: JSON.stringify(promptData),
  })
}

// Get change types
export async function getChangeTypes(): Promise<ChangeType[]> {
  return fetchApi<ChangeType[]>('/api/v1/change-types')
}

// Get components
export async function getComponents(): Promise<Component[]> {
  return fetchApi<Component[]>('/api/v1/components')
}

// Get system technical details
export async function getTechnicalDetails(): Promise<Record<string, unknown>> {
  return fetchApi<Record<string, unknown>>('/api/v1/system/technical-details')
}

// Get analysis history
export async function getAnalysisHistory(): Promise<ChangeImpactResponse[]> {
  return fetchApi<ChangeImpactResponse[]>('/api/v1/analyses/history')
}

// Get analysis by ID
export async function getAnalysisById(analysisId: string): Promise<ChangeImpactResponse> {
  return fetchApi<ChangeImpactResponse>(`/api/v1/analyses/${analysisId}`)
}

