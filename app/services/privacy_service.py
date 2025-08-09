"""
Privacy service for managing privacy scores and analysis.

This service provides high-level functions for privacy score calculation,
retrieval, and management.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import logging

from app.core.privacy_scoring import privacy_scoring_engine
from app.models.user_models import PrivacyScore
from app.models.user import User

logger = logging.getLogger(__name__)


class PrivacyService:
    """
    Service class for privacy-related operations.
    
    This service handles privacy score calculation, retrieval,
    and analysis for users.
    """
    
    async def calculate_and_save_privacy_score(
        self, 
        user_id: int, 
        db: AsyncSession
    ) -> Dict[str, any]:
        """
        Calculate privacy score for user and save to database.
        
        Args:
            user_id: ID of the user
            db: Database session
            
        Returns:
            Dict containing score data and metadata
        """
        try:
            logger.info(f"🔄 Starting privacy score calculation for user {user_id}")
            
            # Verify user exists
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Calculate scores
            score_data = await privacy_scoring_engine.calculate_user_privacy_score(
                user_id, db
            )
            
            # Save to database
            privacy_score = await privacy_scoring_engine.save_privacy_score(
                user_id, score_data, db
            )
            
            # Generate insights
            insights = await self._generate_score_insights(score_data)
            
            result = {
                "user_id": user_id,
                "score_id": privacy_score.id,
                "calculated_at": privacy_score.calculated_at,
                "scores": score_data,
                "insights": insights,
                "status": "success"
            }
            
            logger.info(f"✅ Privacy score calculation completed for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate privacy score for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "status": "error",
                "message": str(e)
            }

    async def get_latest_privacy_score(
        self, 
        user_id: int, 
        db: AsyncSession
    ) -> Optional[Dict[str, any]]:
        """
        Get the most recent privacy score for a user.
        
        Args:
            user_id: ID of the user
            db: Database session
            
        Returns:
            Latest privacy score data or None
        """
        result = await db.execute(
            select(PrivacyScore)
            .where(PrivacyScore.user_id == user_id)
            .order_by(desc(PrivacyScore.calculated_at))
            .limit(1)
        )
        
        latest_score = result.scalar_one_or_none()
        if not latest_score:
            return None
        
        # Generate insights for the score
        score_data = {
            'overall_score': latest_score.overall_score,
            'data_collection_score': latest_score.data_collection_score,
            'data_sharing_score': latest_score.data_sharing_score,
            'user_control_score': latest_score.user_control_score,
            'improvement_potential': latest_score.improvement_potential,
            'score_trend': latest_score.score_trend,
            'factors_analyzed': latest_score.factors_analyzed
        }
        
        insights = await self._generate_score_insights(score_data)
        
        return {
            "score_id": latest_score.id,
            "user_id": user_id,
            "calculated_at": latest_score.calculated_at,
            "scores": score_data,
            "insights": insights
        }

    async def get_privacy_score_history(
        self, 
        user_id: int, 
        days: int, 
        db: AsyncSession
    ) -> List[Dict[str, any]]:
        """
        Get privacy score history for a user.
        
        Args:
            user_id: ID of the user
            days: Number of days to look back
            db: Database session
            
        Returns:
            List of privacy scores with insights
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await db.execute(
            select(PrivacyScore)
            .where(PrivacyScore.user_id == user_id)
            .where(PrivacyScore.calculated_at >= cutoff_date)
            .order_by(desc(PrivacyScore.calculated_at))
        )
        
        scores = result.scalars().all()
        
        history = []
        for score in scores:
            score_data = {
                'overall_score': score.overall_score,
                'data_collection_score': score.data_collection_score,
                'data_sharing_score': score.data_sharing_score,
                'user_control_score': score.user_control_score,
                'improvement_potential': score.improvement_potential,
                'score_trend': score.score_trend,
                'factors_analyzed': score.factors_analyzed
            }
            
            history.append({
                "score_id": score.id,
                "calculated_at": score.calculated_at,
                "scores": score_data
            })
        
        return history

    async def _generate_score_insights(self, score_data: Dict[str, float]) -> Dict[str, any]:
        """
        Generate human-readable insights from score data.
        
        Args:
            score_data: Calculated score data
            
        Returns:
            Dict containing insights and recommendations
        """
        overall_score = score_data['overall_score']
        
        # Determine overall privacy level
        if overall_score >= 80:
            privacy_level = "Excellent"
            level_color = "green"
            level_description = "Your privacy practices are excellent!"
        elif overall_score >= 65:
            privacy_level = "Good"
            level_color = "light_green"
            level_description = "Good privacy practices with room for improvement."
        elif overall_score >= 50:
            privacy_level = "Fair"
            level_color = "yellow"
            level_description = "Your privacy could use some attention."
        elif overall_score >= 35:
            privacy_level = "Poor"
            level_color = "orange"
            level_description = "Several privacy concerns need attention."
        else:
            privacy_level = "Critical"
            level_color = "red"
            level_description = "Immediate privacy improvements needed."
        
        # Identify biggest concerns
        concerns = []
        strengths = []
        
        if score_data['data_collection_score'] < 50:
            concerns.append({
                "area": "Data Collection",
                "score": score_data['data_collection_score'],
                "message": "Services are collecting significant amounts of your data"
            })
        else:
            strengths.append({
                "area": "Data Collection",
                "score": score_data['data_collection_score'],
                "message": "Good control over data collection"
            })
        
        if score_data['data_sharing_score'] < 50:
            concerns.append({
                "area": "Data Sharing",
                "score": score_data['data_sharing_score'],
                "message": "Your data may be shared extensively with third parties"
            })
        else:
            strengths.append({
                "area": "Data Sharing",
                "score": score_data['data_sharing_score'],
                "message": "Limited data sharing with third parties"
            })
        
        if score_data['user_control_score'] < 50:
            concerns.append({
                "area": "User Control",
                "score": score_data['user_control_score'],
                "message": "Limited control over your personal data"
            })
        else:
            strengths.append({
                "area": "User Control",
                "score": score_data['user_control_score'],
                "message": "Good control options available"
            })
        
        # Generate quick tips
        tips = []
        if score_data['improvement_potential'] > 20:
            tips.append("📱 Review privacy settings in your most-used apps")
            tips.append("🔒 Consider alternatives to high-risk services")
            tips.append("⚙️ Update your privacy preferences to be more specific")
        
        return {
            "privacy_level": privacy_level,
            "level_color": level_color,
            "level_description": level_description,
            "concerns": concerns,
            "strengths": strengths,
            "improvement_potential": score_data['improvement_potential'],
            "quick_tips": tips,
            "trend": score_data['score_trend'],
            "services_analyzed": score_data.get('services_count', 0)
        }


# Global service instance
privacy_service = PrivacyService()
