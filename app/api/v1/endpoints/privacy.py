"""
Privacy and recommendations endpoints.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_privacy():
    return {"message": "Privacy endpoint - coming soon"}