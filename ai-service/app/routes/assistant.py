"""
Unified assistant route - classifies and responds to user input.
"""

import time
from fastapi import APIRouter, HTTPException

from app.models import AssistantRequest, AssistantResponse
from app.pipeline import AgentPipeline

router = APIRouter()
pipeline = AgentPipeline()


@router.post("/assistant/respond", response_model=AssistantResponse)
async def assistant_respond(request: AssistantRequest):
    """
    Unified assistant endpoint.
    Classifies whether the input is a conversation or change-analysis request
    and responds appropriately.
    """
    try:
        result = pipeline.classify_and_respond(
            request.message,
            [m.dict() for m in request.conversation_history] if request.conversation_history else []
        )
        
        return AssistantResponse(
            classification=result["classification"],
            reply=result["reply"],
            extracted_intent=result.get("extracted_intent"),
            suggested_actions=result.get("suggested_actions", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

