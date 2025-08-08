"""
Configuration settings for the Personal Data Firewall API.

This module contains all configuration settings using Pydantic Settings
for environment variable management and type safety.
"""

from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    Attributes:
        PROJECT_NAME: Personal Data Firewall
        VERSION: API version
        API_V1_STR: API version prefix
        SECRET_KEY: JWT secret key for token generation
        ALGORITHM: JWT algorithm for token signing
        ACCESS_TOKEN_EXPIRE_MINUTES: Token expiration time
        DATABASE_URL: SQLite database connection string
        ALLOWED_HOSTS: List of allowed hosts for security
        ALLOWED_ORIGINS: CORS allowed origins
        RATE_LIMIT_PER_MINUTE: Rate limiting configuration
    """
    
    # Basic app configuration
    PROJECT_NAME: str = "Personal Data Firewall API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security configuration
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./personal_data_firewall.db"
    
    # Security middleware configuration
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Rate limiting configuration
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # External API configuration
    TOSDR_API_URL: str = "https://tosdr.org/api"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()