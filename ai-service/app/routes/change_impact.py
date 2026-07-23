"""
Change Impact Analysis API routes.
"""

import time
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.models import ChangeImpactRequest, ChangeImpactResponse
from app.pipeline import AgentPipeline

router = APIRouter()
pipeline = AgentPipeline()


@router.post("/change-impact/analyze", response_model=ChangeImpactResponse)
async def analyze_change_impact(request: ChangeImpactRequest):
    """
    Analyze the impact of a proposed change.
    Runs the full multi-agent pipeline.
    """
    try:
        result = pipeline.analyze(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/change-impact/analyze-prompt")
async def analyze_change_impact_from_prompt(prompt: Dict[str, Any]):
    """
    Analyze change impact from a natural language prompt.
    Parses the prompt and runs the full analysis pipeline.
    """
    try:
        # Parse prompt into a structured request
        change_request = ChangeImpactRequest(
            change_title=prompt.get("title", prompt.get("change_title", "Unspecified Change")),
            change_description=prompt.get("description", prompt.get("message", "")),
            change_type=prompt.get("change_type", prompt.get("type", "enhancement")),
            affected_services=prompt.get("affected_services", prompt.get("services", [])),
            priority=prompt.get("priority", "medium"),
            proposed_by=prompt.get("proposed_by", ""),
            environment=prompt.get("environment", "production")
        )
        
        result = pipeline.analyze(change_request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

