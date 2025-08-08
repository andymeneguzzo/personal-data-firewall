"""
Main API router that includes all endpoint routers.

This module combines all API endpoints into a single router
for the main application.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, services, privacy

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(services.router, prefix="/services", tags=["Services"])
api_router.include_router(privacy.router, prefix="/privacy", tags=["Privacy"])