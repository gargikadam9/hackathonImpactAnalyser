"""
System info API routes.
"""

from fastapi import APIRouter

from app.models import ChangeType, Component
from app.pipeline import AgentPipeline

router = APIRouter()
pipeline = AgentPipeline()


@router.get("/change-types")
async def get_change_types():
    """Get available change types for analysis."""
    return pipeline.get_change_types()


@router.get("/components")
async def get_components():
    """Get all tracked system components."""
    return pipeline.get_components()


@router.get("/system/technical-details")
async def get_technical_details():
    """Get system technical details and architecture overview."""
    return pipeline.get_technical_details()

