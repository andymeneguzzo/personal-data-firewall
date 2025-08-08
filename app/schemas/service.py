"""
Pydantic schemas for service-related operations.
"""

from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime


class ServiceBase(BaseModel):
    """Base schema for Service model."""
    name: str
    domain: str
    category: str
    description: Optional[str] = None
    logo_url: Optional[HttpUrl] = None
    is_active: bool = True
    privacy_policy_url: Optional[HttpUrl] = None
    terms_of_service_url: Optional[HttpUrl] = None


class ServiceCreate(ServiceBase):
    """Schema for creating a new service."""
    pass


class ServiceUpdate(BaseModel):
    """Schema for updating a service."""
    name: Optional[str] = None
    domain: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[HttpUrl] = None
    is_active: Optional[bool] = None
    privacy_policy_url: Optional[HttpUrl] = None
    terms_of_service_url: Optional[HttpUrl] = None


class ServiceResponse(ServiceBase):
    """Schema for service responses."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ServiceListResponse(BaseModel):
    """Schema for service list responses."""
    services: List[ServiceResponse]
    total: int
    page: int
    per_page: int

