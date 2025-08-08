"""
User management endpoints.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_users():
    """
    Get all users (placeholder endpoint).
    In a real application, this would require admin privileges.
    """
    return {
        "message": "Users endpoint - coming soon",
        "status": "placeholder",
        "description": "This endpoint will list all users when implemented"
    }