"""
Data category models for tracking what types of data services collect.

This module contains models for categorizing and tracking different types
of personal data that services might collect from users.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DataCategory(Base):
    """
    Data category model for tracking what data types a service collects.
    
    This model links services to the types of personal data they collect,
    with risk assessments for each data type.
    
    Attributes:
        id: Primary key
        service_id: Foreign key to Service
        category_type: Type of data (location, contacts, photos, etc.)
        is_collected: Whether this service collects this data type
        is_required: Whether providing this data is required
        purpose: Why the service collects this data
        retention_period: How long the service keeps this data
        can_be_deleted: Whether users can delete this data
        is_shared_with_third_parties: Whether data is shared externally
        opt_out_available: Whether users can opt out of collection
        risk_score: Risk score for this specific data collection (0-100)
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """
    
    __tablename__ = "data_categories"
    
    # Primary key and relationships
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False, index=True)
    
    # Data category details
    category_type = Column(String(50), nullable=False, index=True)
    is_collected = Column(Boolean, default=False, nullable=False)
    is_required = Column(Boolean, default=False, nullable=False)
    
    # Collection details
    purpose = Column(Text, nullable=True)  # Why they collect this data
    retention_period = Column(String(100), nullable=True)  # How long they keep it
    can_be_deleted = Column(Boolean, default=False, nullable=False)
    is_shared_with_third_parties = Column(Boolean, default=False, nullable=False)
    opt_out_available = Column(Boolean, default=False, nullable=False)
    
    # Risk assessment
    risk_score = Column(Float, nullable=True)  # 0-100 risk score for this data type
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    service = relationship("Service", back_populates="data_categories")


class DataCategoryType:
    """
    Enum-like class for different types of personal data.
    
    This provides standardized categories for different types of personal data
    that services might collect from users.
    """
    
    # Identity Data
    FULL_NAME = "full_name"
    EMAIL_ADDRESS = "email_address"
    PHONE_NUMBER = "phone_number"
    DATE_OF_BIRTH = "date_of_birth"
    GOVERNMENT_ID = "government_id"
    SOCIAL_SECURITY = "social_security"
    
    # Location Data
    PRECISE_LOCATION = "precise_location"
    APPROXIMATE_LOCATION = "approximate_location"
    LOCATION_HISTORY = "location_history"
    IP_ADDRESS = "ip_address"
    
    # Contact Data
    CONTACTS_LIST = "contacts_list"
    CALL_HISTORY = "call_history"
    SMS_MESSAGES = "sms_messages"
    
    # Media Data
    PHOTOS = "photos"
    VIDEOS = "videos"
    AUDIO_RECORDINGS = "audio_recordings"
    CAMERA_ACCESS = "camera_access"
    MICROPHONE_ACCESS = "microphone_access"
    
    # Behavioral Data
    BROWSING_HISTORY = "browsing_history"
    SEARCH_HISTORY = "search_history"
    APP_USAGE = "app_usage"
    PURCHASE_HISTORY = "purchase_history"
    
    # Biometric Data
    FINGERPRINTS = "fingerprints"
    FACE_ID = "face_id"
    VOICE_PRINT = "voice_print"
    
    # Financial Data
    CREDIT_CARD_INFO = "credit_card_info"
    BANK_ACCOUNT = "bank_account"
    FINANCIAL_HISTORY = "financial_history"
    
    # Health Data
    HEALTH_RECORDS = "health_records"
    FITNESS_DATA = "fitness_data"
    MEDICAL_CONDITIONS = "medical_conditions"
    
    # Device Data
    DEVICE_ID = "device_id"
    DEVICE_SPECS = "device_specs"
    INSTALLED_APPS = "installed_apps"
    
    @classmethod
    def get_all_categories(cls):
        """Get list of all data category types."""
        return [
            # Identity
            cls.FULL_NAME, cls.EMAIL_ADDRESS, cls.PHONE_NUMBER, cls.DATE_OF_BIRTH,
            cls.GOVERNMENT_ID, cls.SOCIAL_SECURITY,
            # Location
            cls.PRECISE_LOCATION, cls.APPROXIMATE_LOCATION, cls.LOCATION_HISTORY, cls.IP_ADDRESS,
            # Contact
            cls.CONTACTS_LIST, cls.CALL_HISTORY, cls.SMS_MESSAGES,
            # Media
            cls.PHOTOS, cls.VIDEOS, cls.AUDIO_RECORDINGS, cls.CAMERA_ACCESS, cls.MICROPHONE_ACCESS,
            # Behavioral
            cls.BROWSING_HISTORY, cls.SEARCH_HISTORY, cls.APP_USAGE, cls.PURCHASE_HISTORY,
            # Biometric
            cls.FINGERPRINTS, cls.FACE_ID, cls.VOICE_PRINT,
            # Financial
            cls.CREDIT_CARD_INFO, cls.BANK_ACCOUNT, cls.FINANCIAL_HISTORY,
            # Health
            cls.HEALTH_RECORDS, cls.FITNESS_DATA, cls.MEDICAL_CONDITIONS,
            # Device
            cls.DEVICE_ID, cls.DEVICE_SPECS, cls.INSTALLED_APPS
        ]
    
    @classmethod
    def get_high_risk_categories(cls):
        """Get list of high-risk data categories."""
        return [
            cls.GOVERNMENT_ID, cls.SOCIAL_SECURITY, cls.PRECISE_LOCATION,
            cls.FINGERPRINTS, cls.FACE_ID, cls.VOICE_PRINT,
            cls.CREDIT_CARD_INFO, cls.BANK_ACCOUNT, cls.FINANCIAL_HISTORY,
            cls.HEALTH_RECORDS, cls.MEDICAL_CONDITIONS
        ]