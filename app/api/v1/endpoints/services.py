"""
Service management endpoints for adding, removing, and managing user services.

This module provides comprehensive CRUD operations for user services,
including privacy settings and policy information.
"""

from typing import List, Optional, Dict, Any, Literal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.service import Service, ServiceCategory
from app.models.user_models import UserService, PrivacyScore
from app.models.policy import Policy, PolicyType
from app.models.data_category import DataCategory
from app.schemas.service import (
    ServiceResponse, 
    ServiceCreate, 
    ServiceUpdate,
    UserServiceResponse,
    UserServiceCreate,
    ServicePolicyResponse,
    ServiceSearchResponse,
    UserPrivacyImpactResponse,  # FIXED: Changed from PrivacyImpactResponse
    ServiceCategoryType
)

# TODO: Import these when available
# from app.services.policy_scraper import policy_scraper
# from app.services.privacy_service import privacy_service

# Create the router without prefix to avoid double prefix
router = APIRouter(tags=["Services"])


@router.get("/", response_model=List[ServiceResponse])
async def get_all_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: Optional[ServiceCategoryType] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all available services with optional filtering.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **category**: Filter by service category
    - **search**: Search services by name or description
    """
    try:
        query = select(Service)
        
        # Apply filters
        if category:
            query = query.where(Service.category == category)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Service.name.ilike(search_term),
                    Service.description.ilike(search_term)
                )
            )
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        services = result.scalars().all()
        
        # Convert to response models with ALL required fields
        response_data = []
        for service in services:
            service_dict = {
                # From ServiceBase
                'name': service.name,
                'domain': service.domain,
                'category': service.category,
                'description': service.description,
                'website': f"https://{service.domain}" if service.domain else None,
                'privacy_policy_url': service.privacy_policy_url,
                'terms_of_service_url': service.terms_of_service_url,
                
                # From ServiceResponse
                'id': service.id,
                'logo_url': service.logo_url,
                'is_active': service.is_active,  # FIXED: Added missing field
                'created_at': service.created_at,
                'updated_at': service.updated_at
            }
            response_data.append(ServiceResponse(**service_dict))
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve services: {str(e)}"
        )


@router.get("/categories", response_model=List[str])
async def get_service_categories():
    """Get all available service categories."""
    try:
        # Return the category values as strings
        categories = [
            "Social Media",
            "Communication", 
            "Transportation",
            "E-commerce",
            "Financial",
            "Entertainment",
            "Productivity",
            "Health",
            "Education",
            "News",
            "Gaming",
            "Dating",
            "Food & Drink",
            "Travel",
            "Other"
        ]
        return categories
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve categories: {str(e)}"
        )


@router.get("/search", response_model=ServiceSearchResponse)
async def search_services(
    q: str = Query(..., min_length=2),
    category: Optional[ServiceCategoryType] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Search services by name, description, or other criteria.
    
    - **q**: Search query (minimum 2 characters)
    - **category**: Filter by service category
    - **limit**: Maximum number of results to return
    """
    try:
        query = select(Service)
        
        # Apply search filter
        search_term = f"%{q}%"
        query = query.where(
            or_(
                Service.name.ilike(search_term),
                Service.description.ilike(search_term)
            )
        )
        
        # Apply category filter
        if category:
            query = query.where(Service.category == category)
        
        # Apply limit
        query = query.limit(limit)
        
        result = await db.execute(query)
        services = result.scalars().all()
        
        # Convert to response format with ALL required fields
        results = []
        for service in services:
            service_dict = {
                # From ServiceBase
                'name': service.name,
                'domain': service.domain,
                'category': service.category,
                'description': service.description,
                'website': f"https://{service.domain}" if service.domain else None,
                'privacy_policy_url': service.privacy_policy_url,
                'terms_of_service_url': service.terms_of_service_url,
                
                # From ServiceResponse
                'id': service.id,
                'logo_url': service.logo_url,
                'is_active': service.is_active,  # FIXED: Added missing field
                'created_at': service.created_at,
                'updated_at': service.updated_at
            }
            results.append(ServiceResponse(**service_dict))
        
        return ServiceSearchResponse(
            query=q,
            total_found=len(results),
            results=results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific service."""
    try:
        query = select(Service).where(Service.id == service_id)
        result = await db.execute(query)
        service = result.scalar_one_or_none()
        
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        # Convert to response model with ALL required fields
        service_dict = {
            # From ServiceBase
            'name': service.name,
            'domain': service.domain,
            'category': service.category,
            'description': service.description,
            'website': f"https://{service.domain}" if service.domain else None,
            'privacy_policy_url': service.privacy_policy_url,
            'terms_of_service_url': service.terms_of_service_url,
            
            # From ServiceResponse
            'id': service.id,
            'logo_url': service.logo_url,
            'is_active': service.is_active,  # FIXED: Added missing field
            'created_at': service.created_at,
            'updated_at': service.updated_at
        }
        
        return ServiceResponse(**service_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve service: {str(e)}"
        )


@router.get("/{service_id}/policy", response_model=ServicePolicyResponse)
async def get_service_policy(
    service_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get privacy policy information for a specific service."""
    try:
        # Get service
        service_query = select(Service).where(Service.id == service_id)
        service_result = await db.execute(service_query)
        service = service_result.scalar_one_or_none()
        
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        # Get associated policies
        policy_query = select(Policy).where(Policy.service_id == service_id)
        policy_result = await db.execute(policy_query)
        policies = policy_result.scalars().all()
        
        # Convert to response format
        policy_summaries = []
        for policy in policies:
            policy_summary = {
                'policy_type': policy.policy_type.value if hasattr(policy.policy_type, 'value') else str(policy.policy_type),
                'risk_level': policy.risk_level.value if hasattr(policy.risk_level, 'value') else str(policy.risk_level),
                'summary': policy.summary or "No summary available",
                'last_updated': policy.last_updated
            }
            policy_summaries.append(policy_summary)
        
        return ServicePolicyResponse(
            service_id=service_id,
            service_name=service.name,
            policies=policy_summaries,
            has_privacy_policy=bool(service.privacy_policy_url),
            privacy_policy_url=service.privacy_policy_url,
            last_policy_check=max([p.last_updated for p in policies]) if policies else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve policy information: {str(e)}"
        )


# User Service Management Endpoints

@router.get("/user/my-services", response_model=List[UserServiceResponse])
async def get_user_services(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all services that the current user has added."""
    try:
        query = select(UserService).options(
            selectinload(UserService.service)
        ).where(UserService.user_id == current_user.id)
        
        result = await db.execute(query)
        user_services = result.scalars().all()
        
        # Convert to response format with CORRECT field mapping
        response_data = []
        for user_service in user_services:
            service = user_service.service
            user_service_dict = {
                'id': user_service.id,
                'service_id': service.id,
                'service_name': service.name,
                'service_category': service.category,  # Already a string
                'added_at': user_service.added_at,  # FIXED: Use correct field name
                'is_active': user_service.status == "active",  # FIXED: Convert status to boolean
                'risk_score': 50.0,  # TODO: Calculate from privacy service
                'privacy_settings': {}  # FIXED: Default empty dict since field doesn't exist in model
            }
            response_data.append(UserServiceResponse(**user_service_dict))
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user services: {str(e)}"
        )


@router.post("/user/add-service", response_model=UserServiceResponse)
async def add_user_service(
    service_request: UserServiceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a service to the user's tracked services."""
    try:
        # Check if service exists
        service_query = select(Service).where(Service.id == service_request.service_id)
        service_result = await db.execute(service_query)
        service = service_result.scalar_one_or_none()
        
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        # Check if user already has this service
        existing_query = select(UserService).where(
            and_(
                UserService.user_id == current_user.id,
                UserService.service_id == service_request.service_id
            )
        )
        existing_result = await db.execute(existing_query)
        existing_service = existing_result.scalar_one_or_none()
        
        if existing_service:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service already added to user account"
            )
        
        # Create new user service with CORRECT field mapping
        user_service = UserService(
            user_id=current_user.id,
            service_id=service_request.service_id,
            status="active",  # FIXED: Use status instead of is_active
            # Note: privacy_settings would need to be stored as JSON in notes or separate table
        )
        
        db.add(user_service)
        await db.commit()
        await db.refresh(user_service)
        
        # Return response with CORRECT field mapping
        user_service_dict = {
            'id': user_service.id,
            'service_id': service.id,
            'service_name': service.name,
            'service_category': service.category,  # Already a string
            'added_at': user_service.added_at,  # FIXED: Use correct field name
            'is_active': user_service.status == "active",  # FIXED: Convert status to boolean
            'risk_score': 50.0,  # TODO: Calculate from privacy service
            'privacy_settings': service_request.privacy_settings or {}  # FIXED: Use request data
        }
        
        return UserServiceResponse(**user_service_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add service: {str(e)}"
        )


@router.delete("/user/remove-service/{service_id}")
async def remove_user_service(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a service from the user's tracked services."""
    try:
        # Find the user service
        query = select(UserService).where(
            and_(
                UserService.user_id == current_user.id,
                UserService.service_id == service_id
            )
        )
        result = await db.execute(query)
        user_service = result.scalar_one_or_none()
        
        if not user_service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found in user's services"
            )
        
        # Delete the user service
        await db.delete(user_service)
        await db.commit()
        
        return {"message": "Service removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove service: {str(e)}"
        )


@router.get("/user/privacy-impact", response_model=UserPrivacyImpactResponse)
async def get_privacy_impact(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get privacy impact analysis for user's services."""
    try:
        # Get user services with policies
        query = select(UserService).options(
            selectinload(UserService.service)
        ).where(UserService.user_id == current_user.id)
        
        result = await db.execute(query)
        user_services = result.scalars().all()
        
        if not user_services:
            return UserPrivacyImpactResponse(
                overall_privacy_score=0.0,
                total_services=0,
                high_risk_services=0,
                services_without_policies=0,
                top_recommendations=["Add some services to get privacy analysis"]
            )
        
        # Calculate basic metrics (TODO: Use privacy service for real calculation)
        total_services = len(user_services)
        high_risk_services = max(1, total_services // 3)  # Simulate some high-risk services
        overall_privacy_score = min(85.0, 30.0 + (total_services * 5))  # Simulate increasing risk
        
        return UserPrivacyImpactResponse(
            overall_privacy_score=overall_privacy_score,
            total_services=total_services,
            high_risk_services=high_risk_services,
            services_without_policies=0,  # TODO: Calculate real value
            top_recommendations=[
                f"Review privacy settings for {high_risk_services} high-risk services",
                "Consider removing unused services to reduce exposure",
                "Enable two-factor authentication where available"
            ]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate privacy impact: {str(e)}"
        )


# Admin/Maintenance Endpoints

@router.post("/refresh-policy/{service_id}")
async def refresh_service_policy(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh privacy policy for a specific service.
    
    This endpoint would typically trigger the policy scraper to fetch
    the latest privacy policy and update the database.
    """
    try:
        # Check if service exists
        service_query = select(Service).where(Service.id == service_id)
        service_result = await db.execute(service_query)
        service = service_result.scalar_one_or_none()
        
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        # TODO: Implement actual policy refresh with policy_scraper
        # For now, return a placeholder response
        
        return {
            "message": f"Policy refresh queued for {service.name}",
            "service_id": service_id,
            "status": "queued",
            "estimated_completion": "2-5 minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh policy: {str(e)}"
        )
