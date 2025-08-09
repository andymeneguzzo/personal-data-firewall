"""
Pydantic schemas for service management endpoints.

This module contains all request/response models for service-related operations,
including user service management and policy information.
"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator
from enum import Enum

# Define service categories as literals for Pydantic
ServiceCategoryType = Literal[
    "Social Media",
    "Communication", 
    "Transportation",
    "E-commerce",
    "Entertainment",
    "Productivity",
    "Finance",
    "Health",
    "Education",
    "News",
    "Cloud Storage",
    "Analytics",
    "Other"
]

# Define policy types and risk levels as literals
PolicyTypeStr = Literal["privacy_policy", "terms_of_service", "cookie_policy", "dpa"]
RiskLevelStr = Literal["low", "medium", "high", "critical"]


# Base Service Schemas

class ServiceBase(BaseModel):
    """Base service schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Service name")
    domain: Optional[str] = Field(None, max_length=255, description="Service domain (e.g., instagram.com)")
    category: ServiceCategoryType = Field(..., description="Service category")
    description: Optional[str] = Field(None, max_length=500, description="Service description")
    website: Optional[HttpUrl] = Field(None, description="Service website URL")
    privacy_policy_url: Optional[HttpUrl] = Field(None, description="Privacy policy URL")
    terms_of_service_url: Optional[HttpUrl] = Field(None, description="Terms of service URL")


class ServiceCreate(ServiceBase):
    """Schema for creating a new service."""
    pass


class ServiceUpdate(BaseModel):
    """Schema for updating an existing service."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    domain: Optional[str] = Field(None, max_length=255)
    category: Optional[ServiceCategoryType] = None
    description: Optional[str] = Field(None, max_length=500)
    website: Optional[HttpUrl] = None
    privacy_policy_url: Optional[HttpUrl] = None
    terms_of_service_url: Optional[HttpUrl] = None
    is_active: Optional[bool] = None


class ServiceResponse(ServiceBase):
    """Schema for service response data."""
    id: int
    logo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Additional computed fields
    has_privacy_policy: bool = Field(False, description="Whether service has a privacy policy")
    policy_last_updated: Optional[datetime] = Field(None, description="When policy was last updated")
    privacy_rating: Optional[str] = Field(None, description="Overall privacy rating")

    class Config:
        from_attributes = True


# Policy-related Schemas

class PolicyFindingResponse(BaseModel):
    """Schema for policy finding data."""
    id: int
    clause_text: str
    finding_type: str
    risk_level: RiskLevelStr
    confidence_score: float
    data_categories: List[str]
    user_impact: Optional[str] = None

    class Config:
        from_attributes = True


class PolicyResponse(BaseModel):
    """Schema for policy response data."""
    id: int
    service_id: int
    policy_type: PolicyTypeStr
    version: Optional[str] = None
    effective_date: Optional[datetime] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    risk_score: Optional[float] = None
    data_collection_score: Optional[float] = None
    data_sharing_score: Optional[float] = None
    user_control_score: Optional[float] = None
    is_current: bool
    analysis_completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    findings: List[PolicyFindingResponse] = []

    class Config:
        from_attributes = True


class DataCategoryResponse(BaseModel):
    """Schema for data category information."""
    id: int
    service_id: int
    category_type: str
    is_collected: bool
    is_required: bool
    purpose: Optional[str] = None
    retention_period: Optional[str] = None
    can_be_deleted: bool
    is_shared_with_third_parties: bool
    opt_out_available: bool
    risk_score: Optional[float] = None

    class Config:
        from_attributes = True


class ServicePolicyResponse(BaseModel):
    """Schema for service policy information."""
    service: ServiceResponse
    policy: Optional[PolicyResponse] = None
    data_categories: List[DataCategoryResponse] = []
    last_updated: Optional[datetime] = None
    policy_summary: Optional[str] = None
    risk_assessment: Optional[Dict[str, Any]] = None


# User Service Management Schemas

class UserServiceBase(BaseModel):
    """Base schema for user service relationships."""
    service_id: int = Field(..., description="ID of the service")
    status: str = Field(
        default="active", 
        pattern="^(active|inactive|considering)$",  # FIXED: Changed from regex to pattern
        description="Status of the service for this user"
    )
    notes: Optional[str] = Field(None, max_length=500, description="User notes about this service")
    notification_enabled: bool = Field(
        default=True, 
        description="Whether to receive notifications about this service"
    )


class UserServiceCreate(UserServiceBase):
    """Schema for adding a service to user profile."""
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['active', 'inactive', 'considering']:
            raise ValueError('Status must be active, inactive, or considering')
        return v


class UserServiceUpdate(BaseModel):
    """Schema for updating user service settings."""
    status: Optional[str] = Field(None, pattern="^(active|inactive|considering)$")  # FIXED: Changed from regex to pattern
    notes: Optional[str] = Field(None, max_length=500)
    notification_enabled: Optional[bool] = None
    last_checked_at: Optional[datetime] = None

    @validator('status')
    def validate_status(cls, v):
        if v is not None and v not in ['active', 'inactive', 'considering']:
            raise ValueError('Status must be active, inactive, or considering')
        return v


class UserServiceResponse(UserServiceBase):
    """Schema for user service response."""
    id: int
    user_id: int
    added_at: datetime
    last_checked_at: Optional[datetime] = None
    
    # Related service data
    service: ServiceResponse
    
    # Computed fields
    privacy_impact: Optional[str] = Field(None, description="Privacy impact level")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    recommendations: List[str] = Field(default_factory=list, description="Privacy recommendations")

    class Config:
        from_attributes = True


# Search and Discovery Schemas

class ServiceSearchResponse(BaseModel):
    """Schema for service search results."""
    query: str = Field(..., description="Original search query")
    results: List[ServiceResponse] = Field(..., description="Matching services")
    total_found: int = Field(..., description="Total number of results found")
    categories_found: List[str] = Field(default_factory=list, description="Categories represented in results")
    suggestions: List[str] = Field(default_factory=list, description="Search suggestions")


class ServiceCategoryStats(BaseModel):
    """Schema for service category statistics."""
    category: ServiceCategoryType
    total_services: int
    active_services: int
    with_policies: int
    average_risk_score: Optional[float] = None


class ServiceDiscoveryResponse(BaseModel):
    """Schema for service discovery and recommendations."""
    popular_services: List[ServiceResponse] = []
    category_stats: List[ServiceCategoryStats] = []
    recently_added: List[ServiceResponse] = []
    recommended_for_user: List[ServiceResponse] = []


# Privacy Impact and Analysis Schemas

class ServicePrivacyImpact(BaseModel):
    """Schema for individual service privacy impact."""
    service_name: str
    service_id: int
    risk_level: str = Field(..., pattern="^(low|medium|high|critical)$")  # FIXED: Changed from regex to pattern
    data_collection_score: Optional[float] = None
    data_sharing_score: Optional[float] = None
    user_control_score: Optional[float] = None
    has_current_policy: bool
    policy_last_updated: Optional[datetime] = None
    risk_factors: List[str] = []
    mitigation_suggestions: List[str] = []


class UserPrivacyImpactResponse(BaseModel):
    """Schema for user's overall privacy impact analysis."""
    overall_privacy_score: Optional[float] = None
    total_services: int
    high_risk_services: int
    medium_risk_services: int = 0
    low_risk_services: int = 0
    services_without_policies: int
    service_breakdown: List[ServicePrivacyImpact] = []
    last_calculated: Optional[datetime] = None
    improvement_potential: Optional[float] = None
    top_recommendations: List[str] = []


# Policy Scraping and Management Schemas

class PolicyScrapeRequest(BaseModel):
    """Schema for requesting policy scraping."""
    force_refresh: bool = Field(default=False, description="Force refresh even if recently updated")
    analyze_immediately: bool = Field(default=True, description="Run analysis after scraping")


class PolicyScrapeResult(BaseModel):
    """Schema for policy scraping results."""
    success: bool
    service_name: str
    policy_url: Optional[str] = None
    content_length: Optional[int] = None
    content_hash: Optional[str] = None
    scraped_at: datetime
    error_message: Optional[str] = None
    policy_changed: bool = False
    analysis_queued: bool = False


class BulkPolicyUpdateResponse(BaseModel):
    """Schema for bulk policy update results."""
    total_services: int
    successful_updates: int
    failed_updates: int
    policy_changes_detected: int
    new_policies_added: int
    errors: List[str] = []
    started_at: datetime
    completed_at: datetime
    duration_seconds: float


# Error Response Schemas

class ErrorDetail(BaseModel):
    """Schema for detailed error information."""
    code: str
    message: str
    field: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    details: List[ErrorDetail] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


# Export all schemas for easy importing
__all__ = [
    # Base schemas
    "ServiceBase",
    "ServiceCreate", 
    "ServiceUpdate",
    "ServiceResponse",
    
    # Policy schemas
    "PolicyResponse",
    "PolicyFindingResponse",
    "DataCategoryResponse", 
    "ServicePolicyResponse",
    
    # User service schemas
    "UserServiceBase",
    "UserServiceCreate",
    "UserServiceUpdate", 
    "UserServiceResponse",
    
    # Search and discovery
    "ServiceSearchResponse",
    "ServiceDiscoveryResponse",
    "ServiceCategoryStats",
    
    # Privacy analysis
    "ServicePrivacyImpact",
    "UserPrivacyImpactResponse",
    
    # Policy management
    "PolicyScrapeRequest",
    "PolicyScrapeResult", 
    "BulkPolicyUpdateResponse",
    
    # Utilities
    "ErrorResponse",
    "ErrorDetail"
]

