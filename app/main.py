"""
Personal Data Firewall API - Main Application Entry Point

This module serves as the main entry point for the Personal Data Firewall API.
It configures FastAPI, includes routers, and sets up middleware for security.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.core.security import rate_limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    Handles database initialization and cleanup.
    """
    # Startup
    print("🚀 Starting Personal Data Firewall API...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database tables created successfully")
    print("🔐 Security middleware initialized")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Personal Data Firewall API...")


# Initialize FastAPI application
app = FastAPI(
    title="Personal Data Firewall API",
    description="API for tracking and controlling your digital footprint",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.ALLOWED_HOSTS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify API is running.
    Returns basic system status information.
    """
    return {
        "status": "healthy",
        "service": "Personal Data Firewall API",
        "version": "1.0.0",
        "database": "connected"
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information and links to documentation.
    """
    return {
        "message": "Welcome to Personal Data Firewall API",
        "description": "API for tracking and controlling your digital footprint",
        "documentation": "/docs",
        "health_check": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )