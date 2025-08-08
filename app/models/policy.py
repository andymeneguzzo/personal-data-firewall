"""
Policy model for storing privacy policies and terms of service.

This module contains models for tracking and analyzing privacy policies
and terms of service for different services.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Policy(Base):
    """
    Policy model for storing privacy policies and terms of service.
    
    This model stores analyzed privacy policies and terms of service,
    including risk assessments and key findings.
    
    Attributes:
        id: Primary key
        service_id: Foreign key to Service
        policy_type: Type of policy (privacy_policy, terms_of_service)
        version: Policy version identifier
        effective_date: When this policy became effective
        content: Full text content of the policy
        summary: AI-generated summary of key points
        risk_score: Calculated privacy risk score (0-100)
        data_collection_score: Score for data collection practices (0-100)
        data_sharing_score: Score for data sharing practices (0-100)
        user_control_score: Score for user control options (0-100)
        is_current: Whether this is the current active policy
        analysis_completed: Whether AI analysis is complete
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """
    
    __tablename__ = "policies"
    
    # Primary key and relationships
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False, index=True)
    
    # Policy metadata
    policy_type = Column(String(50), nullable=False, index=True)  # 'privacy_policy', 'terms_of_service'
    version = Column(String(50), nullable=True)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    
    # Policy content
    content = Column(Text, nullable=True)  # Full policy text
    summary = Column(Text, nullable=True)  # AI-generated summary
    
    # Risk scores (0-100 scale)
    risk_score = Column(Float, nullable=True, index=True)  # Overall risk score
    data_collection_score = Column(Float, nullable=True)  # How much data they collect
    data_sharing_score = Column(Float, nullable=True)     # How much they share
    user_control_score = Column(Float, nullable=True)     # User control options
    
    # Status flags
    is_current = Column(Boolean, default=True, nullable=False)
    analysis_completed = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    service = relationship("Service", back_populates="policies")
    policy_findings = relationship("PolicyFinding", back_populates="policy", cascade="all, delete-orphan")


class PolicyFinding(Base):
    """
    Specific findings from policy analysis.
    
    This model stores specific concerning clauses or positive aspects
    found during policy analysis.
    
    Attributes:
        id: Primary key
        policy_id: Foreign key to Policy
        finding_type: Type of finding (concern, positive, neutral)
        category: Category of the finding (data_collection, sharing, etc.)
        title: Brief title of the finding
        description: Detailed description
        risk_level: Risk level (low, medium, high, critical)
        confidence_score: AI confidence in this finding (0-100)
        clause_text: Original text from policy that triggered this finding
        created_at: Record creation timestamp
    """
    
    __tablename__ = "policy_findings"
    
    # Primary key and relationships
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False, index=True)
    
    # Finding details
    finding_type = Column(String(20), nullable=False, index=True)  # 'concern', 'positive', 'neutral'
    category = Column(String(50), nullable=False, index=True)      # 'data_collection', 'sharing', etc.
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    risk_level = Column(String(20), nullable=False, index=True)    # 'low', 'medium', 'high', 'critical'
    confidence_score = Column(Float, nullable=False)              # 0-100
    clause_text = Column(Text, nullable=True)                     # Original policy text
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    policy = relationship("Policy", back_populates="policy_findings")


class PolicyType:
    """
    Enum-like class for policy types.
    """
    
    PRIVACY_POLICY = "privacy_policy"
    TERMS_OF_SERVICE = "terms_of_service"
    COOKIE_POLICY = "cookie_policy"
    DATA_PROCESSING_AGREEMENT = "data_processing_agreement"
    
    @classmethod
    def get_all_types(cls):
        """Get list of all policy types."""
        return [cls.PRIVACY_POLICY, cls.TERMS_OF_SERVICE, cls.COOKIE_POLICY, cls.DATA_PROCESSING_AGREEMENT]


class RiskLevel:
    """
    Enum-like class for risk levels.
    """
    
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"
    
    @classmethod
    def get_all_levels(cls):
        """Get list of all risk levels."""
        return [cls.LOW, cls.MEDIUM, cls.HIGH, cls.CRITICAL]

