"""
Service management endpoints.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_services():
    return {"message": "Services endpoint - coming soon"}