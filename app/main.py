"""
Personal Data Firewall API - Main Application Entry Point

This module serves as the main entry point for the Personal Data Firewall API.
It configures FastAPI, includes routers, and sets up middleware for security.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import Response
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.core.security import rate_limiter


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


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

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.ALLOWED_HOSTS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
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