"""
Database models for the Personal Data Firewall API.

This module imports all database models to ensure they are registered
with SQLAlchemy when the application starts.
"""

from app.models.user import User
from app.models.service import Service, ServiceCategory
from app.models.policy import Policy, PolicyFinding, PolicyType, RiskLevel
from app.models.data_category import DataCategory, DataCategoryType
from app.models.user_models import (
    UserPreference, 
    UserService, 
    PrivacyScore, 
    PrivacyAlert, 
    AlertType
)

# Export all models
__all__ = [
    # Core models
    "User",
    "Service", 
    "Policy",
    "DataCategory",
    
    # Relationship models
    "UserPreference",
    "UserService", 
    "PrivacyScore",
    "PrivacyAlert",
    
    # Finding models
    "PolicyFinding",
    
    # Enum classes
    "ServiceCategory",
    "PolicyType", 
    "RiskLevel",
    "DataCategoryType",
    "AlertType",
]
