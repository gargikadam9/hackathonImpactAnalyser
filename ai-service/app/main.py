"""
AI Change Impact Analyzer - FastAPI Application
Main entry point for the AI service.
"""

import os
import time

# Load .env BEFORE any app module reads environment variables. This is what
# makes "paste an API key into ai-service/.env and restart" actually work —
# without it, AI_PROVIDER / GROQ_API_KEY / OPENAI_API_KEY set in .env were
# silently ignored and the service always ran in mock mode.
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import HealthResponse
from app.pipeline import AgentPipeline
from app.routes import chat, assistant, change_impact, system, sanitize, react_pipeline, feedback

# Application metadata
APP_VERSION = "1.0.0"
APP_START_TIME = time.time()

# Initialize FastAPI
app = FastAPI(
    title="AI Change Impact Analyzer",
    description="Multi-agent AI service for analyzing the impact of system changes",
    version=APP_VERSION
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline (lazy)
pipeline = None


def get_pipeline() -> AgentPipeline:
    """Get or initialize the agent pipeline."""
    global pipeline
    if pipeline is None:
        pipeline = AgentPipeline()
    return pipeline


# Include routers
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(assistant.router, prefix="/api/v1", tags=["Assistant"])
app.include_router(change_impact.router, prefix="/api/v1", tags=["Change Impact"])
app.include_router(system.router, prefix="/api/v1", tags=["System"])
app.include_router(sanitize.router, prefix="/api/v1", tags=["Security"])
# MODULE 8: human-in-the-loop feedback capture (thumbs up/down + score override)
app.include_router(feedback.router, prefix="/api/v1", tags=["Feedback"])

# v2: hardened 3-agent ReAct pipeline (Code Auditor -> Historical Detective -> Risk Synthesizer)
# Also carries MODULE 7 (explainability_report) and MODULE 8 (evaluation_report)
# as additional fields on FullAnalysisResponseV2 — see app/agents/react/react_executor.py
app.include_router(react_pipeline.router, prefix="/api/v2", tags=["Change Impact V2 (ReAct)"])


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    p = get_pipeline()
    provider = os.getenv("AI_PROVIDER", "mock")
    data_counts = p.data_loader.get_counts()
    
    return HealthResponse(
        status="healthy",
        version=APP_VERSION,
        provider=provider,
        mock_mode=provider == "mock",
        uptime=time.time() - APP_START_TIME,
        data_loaded=data_counts
    )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info."""
    return {
        "service": "AI Change Impact Analyzer",
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }

