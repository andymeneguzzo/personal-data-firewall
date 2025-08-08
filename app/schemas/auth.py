"""
Pydantic schemas for authentication.
"""

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """
    Schema for user registration.
    """
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """
    Schema for user login.
    """
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    Schema for JWT token response.
    """
    access_token: str
    token_type: str
    user_id: int
    email: str