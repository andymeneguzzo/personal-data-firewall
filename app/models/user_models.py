"""
User-related models for preferences, services, and privacy tracking.

This module contains models that link users to their privacy preferences,
tracked services, and privacy scores.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserPreference(Base):
    """
    User privacy preferences model.
    
    This model stores user preferences about what types of data they want
    to avoid sharing and their privacy comfort levels.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        data_category: Type of data (from DataCategoryType)
        avoid_sharing: Whether user wants to avoid sharing this data type
        importance_level: How important this preference is (1-5)
        notes: User notes about this preference
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """
    
    __tablename__ = "user_preferences"
    
    # Primary key and relationships
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Preference details
    data_category = Column(String(50), nullable=False, index=True)
    avoid_sharing = Column(Boolean, default=True, nullable=False)
    importance_level = Column(Integer, default=3, nullable=False)  # 1-5 scale
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")


class UserService(Base):
    """
    User-Service relationship model.
    
    This model tracks which services each user uses and when they started using them.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        service_id: Foreign key to Service
        status: Current status (active, inactive, considering)
        added_at: When user added this service
        last_checked_at: When we last checked this service's policies
        notes: User notes about this service
        notification_enabled: Whether to notify user about policy changes
    """
    
    __tablename__ = "user_services"
    
    # Primary key and relationships
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False, index=True)
    
    # Service usage details
    status = Column(String(20), default="active", nullable=False, index=True)  # active, inactive, considering
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    notification_enabled = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="user_services")
    service = relationship("Service", back_populates="user_services")
    
    # Unique constraint
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class PrivacyScore(Base):
    """
    Privacy score model for tracking user's overall privacy health.
    
    This model stores calculated privacy scores for users based on their
    service usage and privacy preferences.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        overall_score: Overall privacy score (0-100)
        data_collection_score: Score for data collection exposure (0-100)
        data_sharing_score: Score for data sharing exposure (0-100)
        user_control_score: Score for user control over data (0-100)
        improvement_potential: How much score could improve (0-100)
        score_trend: Recent trend (improving, declining, stable)
        calculated_at: When this score was calculated
        factors_analyzed: Number of factors included in calculation
        recommendations_count: Number of recommendations generated
    """
    
    __tablename__ = "privacy_scores"
    
    # Primary key and relationships
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Score components (0-100 scale)
    overall_score = Column(Float, nullable=False, index=True)
    data_collection_score = Column(Float, nullable=False)
    data_sharing_score = Column(Float, nullable=False)
    user_control_score = Column(Float, nullable=False)
    improvement_potential = Column(Float, nullable=False)
    
    # Metadata
    score_trend = Column(String(20), nullable=True, index=True)  # improving, declining, stable
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    factors_analyzed = Column(Integer, default=0, nullable=False)
    recommendations_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="privacy_scores")


class PrivacyAlert(Base):
    """
    Privacy alert model for notifying users about privacy concerns.
    
    This model stores alerts about privacy issues, policy changes,
    or recommendations for users.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        service_id: Foreign key to Service (optional)
        alert_type: Type of alert (policy_change, risk_increase, recommendation)
        severity: Alert severity (low, medium, high, critical)
        title: Brief alert title
        message: Detailed alert message
        action_required: Whether user action is required
        action_url: URL for user to take action
        is_read: Whether user has read this alert
        is_dismissed: Whether user has dismissed this alert
        expires_at: When this alert expires (optional)
        created_at: Record creation timestamp
    """
    
    __tablename__ = "privacy_alerts"
    
    # Primary key and relationships
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True, index=True)
    
    # Alert details
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    action_required = Column(Boolean, default=False, nullable=False)
    action_url = Column(String(500), nullable=True)
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False)
    is_dismissed = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="privacy_alerts")
    service = relationship("Service")


class AlertType:
    """
    Enum-like class for alert types.
    """
    
    POLICY_CHANGE = "policy_change"
    RISK_INCREASE = "risk_increase"
    NEW_RECOMMENDATION = "new_recommendation"
    DATA_BREACH = "data_breach"
    PRIVACY_SETTING = "privacy_setting"
    
    @classmethod
    def get_all_types(cls):
        """Get list of all alert types."""
        return [cls.POLICY_CHANGE, cls.RISK_INCREASE, cls.NEW_RECOMMENDATION, cls.DATA_BREACH, cls.PRIVACY_SETTING]