"""
Service model for tracking websites and applications.

This module contains the Service model that represents various online services
like Instagram, Uber, TikTok, etc. that users interact with.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Service(Base):
    """
    Service model representing online platforms and applications.
    
    This model stores information about various services that users might use,
    including social media platforms, ride-sharing apps, e-commerce sites, etc.
    
    Attributes:
        id: Primary key
        name: Service name (e.g., "Instagram", "Uber")
        domain: Primary domain (e.g., "instagram.com", "uber.com")
        category: Service category (e.g., "Social Media", "Transportation")
        description: Brief description of the service
        logo_url: URL to service logo/icon
        is_active: Whether the service is actively tracked
        privacy_policy_url: URL to the service's privacy policy
        terms_of_service_url: URL to the service's terms of service
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """
    
    __tablename__ = "services"
    
    # Primary key and basic info
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Visual and status
    logo_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Policy URLs
    privacy_policy_url = Column(String(500), nullable=True)
    terms_of_service_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    policies = relationship("Policy", back_populates="service", cascade="all, delete-orphan")
    data_categories = relationship("DataCategory", back_populates="service", cascade="all, delete-orphan")
    user_services = relationship("UserService", back_populates="service", cascade="all, delete-orphan")


class ServiceCategory:
    """
    Enum-like class for service categories.
    
    This provides standardized categories for different types of services
    to enable better organization and filtering.
    """
    
    SOCIAL_MEDIA = "Social Media"
    E_COMMERCE = "E-Commerce"
    TRANSPORTATION = "Transportation"
    FOOD_DELIVERY = "Food Delivery"
    STREAMING = "Streaming"
    CLOUD_STORAGE = "Cloud Storage"
    MESSAGING = "Messaging"
    EMAIL = "Email"
    SEARCH = "Search"
    NEWS = "News"
    FINANCE = "Finance"
    HEALTH = "Health"
    EDUCATION = "Education"
    PRODUCTIVITY = "Productivity"
    GAMING = "Gaming"
    OTHER = "Other"
    
    @classmethod
    def get_all_categories(cls):
        """Get list of all available categories."""
        return [
            cls.SOCIAL_MEDIA, cls.E_COMMERCE, cls.TRANSPORTATION, cls.FOOD_DELIVERY,
            cls.STREAMING, cls.CLOUD_STORAGE, cls.MESSAGING, cls.EMAIL, cls.SEARCH,
            cls.NEWS, cls.FINANCE, cls.HEALTH, cls.EDUCATION, cls.PRODUCTIVITY,
            cls.GAMING, cls.OTHER
        ]

