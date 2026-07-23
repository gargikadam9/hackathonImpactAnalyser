"""
Chat-related API routes.
"""

import time
import uuid
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.models import ChatRequest, ChatResponse
from app.pipeline import AgentPipeline

router = APIRouter()
pipeline = AgentPipeline()


@router.post("/chat/general", response_model=ChatResponse)
async def general_chat(request: ChatRequest):
    """
    General chat endpoint for conversational interactions.
    """
    start = time.time()
    
    try:
        result = pipeline.classify_and_respond(
            request.message,
            [m.dict() for m in request.conversation_history] if request.conversation_history else []
        )
        
        processing_time = int((time.time() - start) * 1000)
        
        return ChatResponse(
            reply=result["reply"],
            conversation_id=f"conv-{uuid.uuid4().hex[:8]}",
            intent=result.get("classification", "general"),
            processingTimeMs=processing_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

