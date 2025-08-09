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
    UserServiceUpdate,
    ServiceSearchResponse,
    ServicePolicyResponse,
    ServiceCategoryType
)
# TODO: Uncomment when these services are implemented
# from app.services.policy_scraper import policy_scraper
# from app.services.privacy_service import privacy_service

# FIXED: Remove prefix here since it's added in api.py
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
    query = select(Service).where(Service.is_active == True)
    
    # Apply filters - convert category string to enum
    if category:
        # Convert string category to enum
        try:
            category_enum = ServiceCategory(category)
            query = query.where(Service.category == category_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {category}"
            )
    
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
    
    # FIXED: Use model_validate instead of from_orm for Pydantic v2
    return [ServiceResponse.model_validate(service) for service in services]


@router.get("/categories", response_model=List[str])
async def get_service_categories():
    """Get all available service categories."""
    return [category.value for category in ServiceCategory]


@router.get("/search", response_model=ServiceSearchResponse)
async def search_services(
    q: str = Query(..., min_length=2),
    category: Optional[ServiceCategoryType] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Search for services by name, domain, or description.
    
    - **q**: Search query (minimum 2 characters)
    - **category**: Optional category filter
    - **limit**: Maximum number of results
    """
    search_term = f"%{q}%"
    query = select(Service).where(
        and_(
            Service.is_active == True,
            or_(
                Service.name.ilike(search_term),
                Service.domain.ilike(search_term),
                Service.description.ilike(search_term)
            )
        )
    )
    
    if category:
        try:
            category_enum = ServiceCategory(category)
            query = query.where(Service.category == category_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {category}"
            )
    
    query = query.limit(limit)
    result = await db.execute(query)
    services = result.scalars().all()
    
    return ServiceSearchResponse(
        query=q,
        results=[ServiceResponse.from_orm(service) for service in services],
        total_found=len(services)
    )


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific service."""
    query = select(Service).where(
        and_(Service.id == service_id, Service.is_active == True)
    )
    result = await db.execute(query)
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    return ServiceResponse.from_orm(service)


@router.get("/{service_id}/policy", response_model=ServicePolicyResponse)
async def get_service_policy(
    service_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get privacy policy information for a service."""
    # Get service
    service_query = await db.execute(
        select(Service).where(
            and_(Service.id == service_id, Service.is_active == True)
        )
    )
    service = service_query.scalar_one_or_none()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Get current privacy policy
    policy_query = await db.execute(
        select(Policy).where(
            and_(
                Policy.service_id == service_id,
                Policy.policy_type == PolicyType.PRIVACY_POLICY,
                Policy.is_current == True
            )
        )
    )
    policy = policy_query.scalar_one_or_none()
    
    # Get data categories
    categories_query = await db.execute(
        select(DataCategory).where(DataCategory.service_id == service_id)
    )
    data_categories = categories_query.scalars().all()
    
    return ServicePolicyResponse(
        service=ServiceResponse.from_orm(service),
        policy=policy,
        data_categories=data_categories,
        last_updated=policy.updated_at if policy else None
    )


# User Service Management Endpoints

@router.get("/user/my-services", response_model=List[UserServiceResponse])
async def get_user_services(
    status_filter: Optional[str] = Query(None, pattern="^(active|inactive|considering)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all services associated with the current user."""
    query = select(UserService).options(
        selectinload(UserService.service)
    ).where(UserService.user_id == current_user.id)
    
    if status_filter:
        query = query.where(UserService.status == status_filter)
    
    result = await db.execute(query)
    user_services = result.scalars().all()
    
    return [UserServiceResponse.from_orm(us) for us in user_services]


@router.post("/user/add-service", response_model=UserServiceResponse)
async def add_service_to_user(
    service_data: UserServiceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a service to the user's profile."""
    
    # Check if service exists and is active
    service_query = await db.execute(
        select(Service).where(
            and_(Service.id == service_data.service_id, Service.is_active == True)
        )
    )
    service = service_query.scalar_one_or_none()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or inactive"
        )
    
    # Check if user already has this service
    existing_query = await db.execute(
        select(UserService).where(
            and_(
                UserService.user_id == current_user.id,
                UserService.service_id == service_data.service_id
            )
        )
    )
    existing_service = existing_query.scalar_one_or_none()
    
    if existing_service:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service already added to user profile"
        )
    
    # Create new user service
    user_service = UserService(
        user_id=current_user.id,
        service_id=service_data.service_id,
        status=service_data.status,
        notes=service_data.notes,
        notification_enabled=service_data.notification_enabled
    )
    
    db.add(user_service)
    await db.commit()
    await db.refresh(user_service)
    
    # Load the service relationship
    await db.refresh(user_service, ['service'])
    
    return UserServiceResponse.from_orm(user_service)


@router.put("/user/services/{user_service_id}", response_model=UserServiceResponse)
async def update_user_service(
    user_service_id: int,
    service_update: UserServiceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a user's service settings."""
    
    # Get user service
    query = select(UserService).options(
        selectinload(UserService.service)
    ).where(
        and_(
            UserService.id == user_service_id,
            UserService.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    user_service = result.scalar_one_or_none()
    
    if not user_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User service not found"
        )
    
    # Update fields
    update_data = service_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user_service, field, value)
    
    await db.commit()
    await db.refresh(user_service)
    
    # Trigger privacy score recalculation if status changed
    if 'status' in update_data:
        try:
            # TODO: Uncomment when privacy_service is implemented
            # await privacy_service.calculate_and_save_privacy_score(current_user.id, db)
            pass
        except Exception:
            pass
    
    return UserServiceResponse.from_orm(user_service)


@router.delete("/user/services/{user_service_id}")
async def remove_user_service(
    user_service_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a service from the user's profile."""
    
    # Get user service
    query = select(UserService).where(
        and_(
            UserService.id == user_service_id,
            UserService.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    user_service = result.scalar_one_or_none()
    
    if not user_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User service not found"
        )
    
    await db.delete(user_service)
    await db.commit()
    
    # Trigger privacy score recalculation
    try:
        # TODO: Uncomment when privacy_service is implemented
        # await privacy_service.calculate_and_save_privacy_score(current_user.id, db)
        pass
    except Exception:
        pass
    
    return {"message": "Service removed successfully"}


@router.post("/refresh-policy/{service_id}")
async def refresh_service_policy(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger a policy refresh for a specific service."""
    
    # Check if service exists
    service_query = await db.execute(
        select(Service).where(Service.id == service_id)
    )
    service = service_query.scalar_one_or_none()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Scrape latest policy
    # TODO: Uncomment when policy_scraper is implemented
    # async with policy_scraper:
    #     scrape_result = await policy_scraper.scrape_service_policy(service)
    
    # if scrape_result["success"]:
    #     return {
    #         "message": "Policy refreshed successfully",
    #         "policy_url": scrape_result["policy_url"],
    #         "content_length": len(scrape_result["policy_content"] or ""),
    #         "scraped_at": scrape_result["scraped_at"]
    #     }
    # else:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=f"Failed to refresh policy: {scrape_result.get('error', 'Unknown error')}"
    #     )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Policy scraping functionality is not yet implemented."
    )


@router.get("/user/privacy-impact")
async def get_user_privacy_impact(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get privacy impact analysis for user's services."""
    
    # Get user services with policies
    user_services_query = await db.execute(
        select(UserService).options(
            selectinload(UserService.service)
        ).where(
            and_(
                UserService.user_id == current_user.id,
                UserService.status == "active"
            )
        )
    )
    user_services = user_services_query.scalars().all()
    
    # Get latest privacy score
    score_query = await db.execute(
        select(PrivacyScore).where(
            PrivacyScore.user_id == current_user.id
        ).order_by(PrivacyScore.calculated_at.desc()).limit(1)
    )
    latest_score = score_query.scalar_one_or_none()
    
    # Analyze impact per service
    service_impacts = []
    for user_service in user_services:
        # Get policy for this service
        policy_query = await db.execute(
            select(Policy).where(
                and_(
                    Policy.service_id == user_service.service_id,
                    Policy.policy_type == PolicyType.PRIVACY_POLICY,
                    Policy.is_current == True
                )
            )
        )
        policy = policy_query.scalar_one_or_none()
        
        service_impacts.append({
            "service_name": user_service.service.name,
            "service_id": user_service.service_id,
            "risk_level": "high" if (policy and policy.risk_score and policy.risk_score < 50) else "medium",
            "data_collection_score": policy.data_collection_score if policy else None,
            "data_sharing_score": policy.data_sharing_score if policy else None,
            "user_control_score": policy.user_control_score if policy else None,
            "has_current_policy": policy is not None,
            "policy_last_updated": policy.updated_at if policy else None
        })
    
    return {
        "overall_privacy_score": latest_score.overall_score if latest_score else None,
        "total_services": len(service_impacts),
        "high_risk_services": len([s for s in service_impacts if s["risk_level"] == "high"]),
        "services_without_policies": len([s for s in service_impacts if not s["has_current_policy"]]),
        "service_breakdown": service_impacts,
        "last_calculated": latest_score.calculated_at if latest_score else None
    }
