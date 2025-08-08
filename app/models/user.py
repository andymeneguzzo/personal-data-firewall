"""
User model for authentication and user management.
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """
    User model for storing user account information.
    
    Attributes:
        id: Primary key
        email: User's email address (unique)
        hashed_password: Bcrypt hashed password
        created_at: Account creation timestamp
    """
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    user_services = relationship("UserService", back_populates="user", cascade="all, delete-orphan")
    privacy_scores = relationship("PrivacyScore", back_populates="user", cascade="all, delete-orphan")
    privacy_alerts = relationship("PrivacyAlert", back_populates="user", cascade="all, delete-orphan")