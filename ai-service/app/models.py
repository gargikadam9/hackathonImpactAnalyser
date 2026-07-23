from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentType(str, Enum):
    INTAKE = "intake"
    DEPENDENCY = "dependency"
    KNOWLEDGE = "knowledge"
    INCIDENT = "incident"
    RISK = "risk"
    NOTIFICATION = "notification"
    SUMMARY = "summary"


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    context: Optional[Dict[str, Any]] = {}


class ChatResponse(BaseModel):
    reply: str
    conversation_id: Optional[str] = None
    intent: Optional[str] = None
    processingTimeMs: Optional[int] = None


class ChangeImpactRequest(BaseModel):
    change_title: str = Field(..., description="Title of the change")
    change_description: str = Field(..., description="Detailed description of the change")
    change_type: str = Field(default="enhancement", description="Type of change: infrastructure, enhancement, bugfix, security, etc.")
    affected_services: Optional[List[str]] = Field(default=[], description="List of affected service IDs or names")
    priority: Optional[str] = Field(default="medium", description="Priority: low, medium, high, critical")
    proposed_by: Optional[str] = Field(default="", description="Team or person proposing the change")
    environment: Optional[str] = Field(default="production", description="Target environment")


class ChangeImpactResponse(BaseModel):
    analysisId: str
    riskScore: float
    riskLevel: RiskLevel
    confidence: float
    impactedServices: List[str]
    teamsToNotify: List[str]
    potentialRisks: List[str]
    recommendedTests: List[str]
    similarIncidents: List[Dict[str, Any]]
    mitigationPlan: List[str]
    executiveSummary: str
    agentTraces: List[Dict[str, Any]]
    interpretedIntent: str
    retrievedEvidence: List[Dict[str, Any]]
    dataSourcesUsed: List[str]
    processingTimeMs: int
    mockMode: bool


class AgentTrace(BaseModel):
    agent: AgentType
    status: str  # "running", "completed", "failed"
    input: Optional[str] = None
    output: Optional[str] = None
    processingTimeMs: int
    error: Optional[str] = None
    evidence: Optional[List[Dict[str, Any]]] = []


class HealthResponse(BaseModel):
    status: str
    version: str
    provider: str
    mock_mode: bool
    uptime: float
    data_loaded: Dict[str, int]


class ChangeType(BaseModel):
    id: str
    name: str
    description: str
    risk_default: str


class Component(BaseModel):
    id: str
    name: str
    type: str
    criticality: str
    owner: str
    dependencies: List[str]


class AssistantRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []


class AssistantResponse(BaseModel):
    classification: str  # "conversation" or "change-analysis"
    reply: str
    extracted_intent: Optional[Dict[str, Any]] = None
    suggested_actions: Optional[List[str]] = []

