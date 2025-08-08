"""
Service management endpoints.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_services():
    """
    Get all available services (placeholder endpoint).
    """
    return {
        "message": "Services endpoint - coming soon",
        "status": "placeholder",
        "description": "This endpoint will list all available services when implemented"
    }
