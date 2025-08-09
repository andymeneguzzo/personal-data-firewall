"""
Privacy Scoring Engine for calculating user privacy health scores.

This module contains the core algorithms for analyzing user privacy based on
their service usage, preferences, and policy analysis.
"""

from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from app.models.user import User
from app.models.service import Service
from app.models.policy import Policy
from app.models.data_category import DataCategory, DataCategoryType
from app.models.user_models import UserPreference, UserService, PrivacyScore
from app.core.database import get_db

logger = logging.getLogger(__name__)


class PrivacyScoringEngine:
    """
    Core privacy scoring engine that calculates comprehensive privacy scores.
    
    This engine analyzes multiple factors to generate privacy scores:
    - Service risk levels
    - User privacy preferences vs actual data collection
    - Policy analysis results
    - Data sharing practices
    - User control options
    """
    
    def __init__(self):
        self.weights = {
            'data_collection': 0.35,  # How much data is collected
            'data_sharing': 0.25,     # How much data is shared
            'user_control': 0.25,     # How much control user has
            'preference_match': 0.15   # How well services match user preferences
        }
        
        # Risk multipliers for different data categories
        self.data_risk_multipliers = {
            # High-risk data types
            DataCategoryType.GOVERNMENT_ID: 3.0,
            DataCategoryType.SOCIAL_SECURITY: 3.0,
            DataCategoryType.FINANCIAL_HISTORY: 2.8,
            DataCategoryType.HEALTH_RECORDS: 2.8,
            DataCategoryType.PRECISE_LOCATION: 2.5,
            DataCategoryType.FINGERPRINTS: 2.5,
            DataCategoryType.FACE_ID: 2.5,
            
            # Medium-high risk
            DataCategoryType.CREDIT_CARD_INFO: 2.2,
            DataCategoryType.PHONE_NUMBER: 2.0,
            DataCategoryType.CONTACTS_LIST: 2.0,
            DataCategoryType.PHOTOS: 1.8,
            DataCategoryType.LOCATION_HISTORY: 1.8,
            
            # Medium risk
            DataCategoryType.EMAIL_ADDRESS: 1.5,
            DataCategoryType.BROWSING_HISTORY: 1.5,
            DataCategoryType.PURCHASE_HISTORY: 1.5,
            DataCategoryType.FULL_NAME: 1.3,
            
            # Lower risk
            DataCategoryType.APPROXIMATE_LOCATION: 1.2,
            DataCategoryType.DEVICE_SPECS: 1.0,
            DataCategoryType.APP_USAGE: 1.0,
        }

    async def calculate_user_privacy_score(
        self, 
        user_id: int, 
        db: AsyncSession
    ) -> Dict[str, float]:
        """
        Calculate comprehensive privacy score for a user.
        
        Args:
            user_id: ID of the user to analyze
            db: Database session
            
        Returns:
            Dict containing all score components and overall score
        """
        logger.info(f"🔍 Calculating privacy score for user {user_id}")
        
        try:
            # Get user's services and preferences
            user_services = await self._get_user_services(user_id, db)
            user_preferences = await self._get_user_preferences(user_id, db)
            
            if not user_services:
                logger.warning(f"No services found for user {user_id}")
                return self._get_default_score("No services tracked")
            
            # Calculate individual score components
            data_collection_score = await self._calculate_data_collection_score(
                user_services, db
            )
            
            data_sharing_score = await self._calculate_data_sharing_score(
                user_services, db
            )
            
            user_control_score = await self._calculate_user_control_score(
                user_services, db
            )
            
            preference_match_score = await self._calculate_preference_match_score(
                user_services, user_preferences, db
            )
            
            # Calculate weighted overall score
            overall_score = (
                data_collection_score * self.weights['data_collection'] +
                data_sharing_score * self.weights['data_sharing'] +
                user_control_score * self.weights['user_control'] +
                preference_match_score * self.weights['preference_match']
            )
            
            # Calculate improvement potential
            improvement_potential = await self._calculate_improvement_potential(
                user_services, user_preferences, db
            )
            
            # Determine trend (this would compare with previous scores)
            score_trend = await self._determine_score_trend(user_id, overall_score, db)
            
            score_data = {
                'overall_score': round(overall_score, 2),
                'data_collection_score': round(data_collection_score, 2),
                'data_sharing_score': round(data_sharing_score, 2),
                'user_control_score': round(user_control_score, 2),
                'preference_match_score': round(preference_match_score, 2),
                'improvement_potential': round(improvement_potential, 2),
                'score_trend': score_trend,
                'factors_analyzed': len(user_services),
                'services_count': len(user_services)
            }
            
            logger.info(f"✅ Privacy score calculated: {overall_score:.2f}/100")
            return score_data
            
        except Exception as e:
            logger.error(f"❌ Error calculating privacy score for user {user_id}: {e}")
            return self._get_default_score("Calculation error")

    async def _calculate_data_collection_score(
        self, 
        user_services: List[UserService], 
        db: AsyncSession
    ) -> float:
        """
        Calculate score based on how much data services collect.
        Higher collection = lower score.
        """
        if not user_services:
            return 100.0
        
        total_risk = 0.0
        service_count = len(user_services)
        
        for user_service in user_services:
            # Get data categories for this service
            result = await db.execute(
                select(DataCategory)
                .where(DataCategory.service_id == user_service.service_id)
                .where(DataCategory.is_collected == True)
            )
            data_categories = result.scalars().all()
            
            service_risk = 0.0
            for category in data_categories:
                # Apply risk multiplier based on data type
                multiplier = self.data_risk_multipliers.get(category.category_type, 1.0)
                category_risk = multiplier
                
                # Additional risk if data is required
                if category.is_required:
                    category_risk *= 1.5
                
                # Additional risk if shared with third parties
                if category.is_shared_with_third_parties:
                    category_risk *= 1.3
                
                service_risk += category_risk
            
            # Normalize service risk (assuming max 20 data types per service)
            normalized_service_risk = min(service_risk / 20.0, 1.0)
            total_risk += normalized_service_risk
        
        # Calculate average risk and convert to score (lower risk = higher score)
        average_risk = total_risk / service_count
        score = max(0, 100 - (average_risk * 100))
        
        return score

    async def _calculate_data_sharing_score(
        self, 
        user_services: List[UserService], 
        db: AsyncSession
    ) -> float:
        """
        Calculate score based on data sharing practices.
        More sharing = lower score.
        """
        if not user_services:
            return 100.0
        
        total_sharing_risk = 0.0
        service_count = len(user_services)
        
        for user_service in user_services:
            # Get service policy
            result = await db.execute(
                select(Policy)
                .where(Policy.service_id == user_service.service_id)
                .where(Policy.is_current == True)
                .where(Policy.policy_type == "privacy_policy")
            )
            policy = result.scalar_one_or_none()
            
            if policy and policy.data_sharing_score is not None:
                # Use policy analysis score (0-100, where 100 is worst)
                sharing_risk = policy.data_sharing_score / 100.0
            else:
                # Check data categories for sharing indicators
                result = await db.execute(
                    select(DataCategory)
                    .where(DataCategory.service_id == user_service.service_id)
                    .where(DataCategory.is_shared_with_third_parties == True)
                )
                shared_categories = result.scalars().all()
                
                # Estimate sharing risk based on shared categories
                sharing_risk = min(len(shared_categories) / 10.0, 1.0)
            
            total_sharing_risk += sharing_risk
        
        average_sharing_risk = total_sharing_risk / service_count
        score = max(0, 100 - (average_sharing_risk * 100))
        
        return score

    async def _calculate_user_control_score(
        self, 
        user_services: List[UserService], 
        db: AsyncSession
    ) -> float:
        """
        Calculate score based on user control options.
        More control = higher score.
        """
        if not user_services:
            return 100.0
        
        total_control = 0.0
        service_count = len(user_services)
        
        for user_service in user_services:
            # Get service policy
            result = await db.execute(
                select(Policy)
                .where(Policy.service_id == user_service.service_id)
                .where(Policy.is_current == True)
                .where(Policy.policy_type == "privacy_policy")
            )
            policy = result.scalar_one_or_none()
            
            if policy and policy.user_control_score is not None:
                # Use policy analysis score (0-100, where 100 is best)
                control_score = policy.user_control_score / 100.0
            else:
                # Check data categories for control options
                result = await db.execute(
                    select(DataCategory)
                    .where(DataCategory.service_id == user_service.service_id)
                )
                categories = result.scalars().all()
                
                control_factors = 0
                total_categories = len(categories)
                
                for category in categories:
                    if category.can_be_deleted:
                        control_factors += 1
                    if category.opt_out_available:
                        control_factors += 1
                
                # Calculate control score
                if total_categories > 0:
                    control_score = control_factors / (total_categories * 2)  # Max 2 factors per category
                else:
                    control_score = 0.5  # Default
            
            total_control += control_score
        
        average_control = total_control / service_count
        score = average_control * 100
        
        return score

    async def _calculate_preference_match_score(
        self, 
        user_services: List[UserService],
        user_preferences: List[UserPreference], 
        db: AsyncSession
    ) -> float:
        """
        Calculate how well services match user preferences.
        Better match = higher score.
        """
        if not user_preferences:
            return 75.0  # Neutral score if no preferences set
        
        # Create preference lookup
        avoid_categories = {
            pref.data_category: pref.importance_level 
            for pref in user_preferences 
            if pref.avoid_sharing
        }
        
        if not avoid_categories:
            return 75.0
        
        total_violations = 0.0
        max_possible_violations = 0.0
        
        for user_service in user_services:
            # Get data categories this service collects
            result = await db.execute(
                select(DataCategory)
                .where(DataCategory.service_id == user_service.service_id)
                .where(DataCategory.is_collected == True)
            )
            categories = result.scalars().all()
            
            for category in categories:
                if category.category_type in avoid_categories:
                    # User wants to avoid this but service collects it
                    importance = avoid_categories[category.category_type]
                    violation_weight = importance / 5.0  # Normalize to 0-1
                    
                    # Increase violation if required or shared
                    if category.is_required:
                        violation_weight *= 1.5
                    if category.is_shared_with_third_parties:
                        violation_weight *= 1.3
                    
                    total_violations += violation_weight
                
                # Count max possible violations
                if category.category_type in avoid_categories:
                    max_possible_violations += 1.0
        
        if max_possible_violations == 0:
            return 100.0
        
        violation_ratio = total_violations / max_possible_violations
        score = max(0, 100 - (violation_ratio * 100))
        
        return score

    async def _calculate_improvement_potential(
        self, 
        user_services: List[UserService],
        user_preferences: List[UserPreference],
        db: AsyncSession
    ) -> float:
        """
        Calculate how much the user's privacy score could improve.
        """
        # This is a simplified calculation
        # In reality, you'd analyze specific improvement opportunities
        
        improvement_factors = 0
        total_factors = 0
        
        for user_service in user_services:
            # Check if service has alternatives with better privacy
            # Check if user can adjust privacy settings
            # Check if user can opt out of data collection
            
            result = await db.execute(
                select(DataCategory)
                .where(DataCategory.service_id == user_service.service_id)
            )
            categories = result.scalars().all()
            
            for category in categories:
                total_factors += 1
                if category.opt_out_available or category.can_be_deleted:
                    improvement_factors += 1
        
        if total_factors == 0:
            return 0.0
        
        potential = (improvement_factors / total_factors) * 100
        return min(potential, 50.0)  # Cap at 50% improvement potential

    async def _determine_score_trend(
        self, 
        user_id: int, 
        current_score: float, 
        db: AsyncSession
    ) -> str:
        """
        Determine if privacy score is improving, declining, or stable.
        """
        # Get previous score from last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        result = await db.execute(
            select(PrivacyScore)
            .where(PrivacyScore.user_id == user_id)
            .where(PrivacyScore.calculated_at >= thirty_days_ago)
            .order_by(PrivacyScore.calculated_at.desc())
            .limit(2)
        )
        previous_scores = result.scalars().all()
        
        if len(previous_scores) < 2:
            return "stable"
        
        previous_score = previous_scores[1].overall_score
        score_change = current_score - previous_score
        
        if score_change > 5:
            return "improving"
        elif score_change < -5:
            return "declining"
        else:
            return "stable"

    async def _get_user_services(self, user_id: int, db: AsyncSession) -> List[UserService]:
        """Get all active services for a user."""
        result = await db.execute(
            select(UserService)
            .where(UserService.user_id == user_id)
            .where(UserService.status == "active")
        )
        return result.scalars().all()

    async def _get_user_preferences(self, user_id: int, db: AsyncSession) -> List[UserPreference]:
        """Get all preferences for a user."""
        result = await db.execute(
            select(UserPreference)
            .where(UserPreference.user_id == user_id)
        )
        return result.scalars().all()

    def _get_default_score(self, reason: str) -> Dict[str, float]:
        """Return default scores when calculation isn't possible."""
        return {
            'overall_score': 50.0,
            'data_collection_score': 50.0,
            'data_sharing_score': 50.0,
            'user_control_score': 50.0,
            'preference_match_score': 50.0,
            'improvement_potential': 25.0,
            'score_trend': 'stable',
            'factors_analyzed': 0,
            'services_count': 0,
            'calculation_note': reason
        }

    async def save_privacy_score(
        self, 
        user_id: int, 
        score_data: Dict[str, float], 
        db: AsyncSession
    ) -> PrivacyScore:
        """
        Save calculated privacy score to database.
        
        Args:
            user_id: ID of the user
            score_data: Calculated score data
            db: Database session
            
        Returns:
            Created PrivacyScore instance
        """
        privacy_score = PrivacyScore(
            user_id=user_id,
            overall_score=score_data['overall_score'],
            data_collection_score=score_data['data_collection_score'],
            data_sharing_score=score_data['data_sharing_score'],
            user_control_score=score_data['user_control_score'],
            improvement_potential=score_data['improvement_potential'],
            score_trend=score_data['score_trend'],
            factors_analyzed=score_data['factors_analyzed'],
            recommendations_count=0  # Will be updated when recommendations are generated
        )
        
        db.add(privacy_score)
        await db.commit()
        await db.refresh(privacy_score)
        
        logger.info(f"💾 Privacy score saved for user {user_id}: {score_data['overall_score']:.2f}")
        return privacy_score


# Global instance
privacy_scoring_engine = PrivacyScoringEngine()
