"""
Test script for the Privacy Scoring Engine.

This script demonstrates the privacy scoring functionality with sample data.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.services.privacy_service import privacy_service
from app.models.user import User
from app.models.service import Service
from app.models.user_models import UserService, UserPreference
from app.models.data_category import DataCategory, DataCategoryType
from sqlalchemy import select


async def create_test_data():
    """Create sample data for testing the privacy scoring engine."""
    
    async with AsyncSessionLocal() as db:
        print("🔄 Creating test data for privacy scoring...")
        
        # Use timestamp for unique test user
        timestamp = str(int(datetime.now().timestamp()))
        test_email = f"privacy_test_{timestamp}@example.com"
        
        # Create a test user with unique email
        test_user = User(
            email=test_email,
            hashed_password="test_hash"
        )
        db.add(test_user)
        await db.commit()
        await db.refresh(test_user)
        print(f"✅ Created test user: {test_user.id} ({test_email})")
        
        # Check if test services already exist
        instagram_query = await db.execute(
            select(Service).where(Service.name == "Instagram")
        )
        existing_instagram = instagram_query.scalar_one_or_none()
        
        uber_query = await db.execute(
            select(Service).where(Service.name == "Uber")
        )
        existing_uber = uber_query.scalar_one_or_none()
        
        if existing_instagram and existing_uber:
            print(f"✅ Using existing services: Instagram ({existing_instagram.id}), Uber ({existing_uber.id})")
            instagram = existing_instagram
            uber = existing_uber
        else:
            # Create test services if they don't exist
            instagram = Service(
                name="Instagram",
                domain="instagram.com",
                category="Social Media",
                description="Photo and video sharing social network",
                privacy_policy_url="https://help.instagram.com/privacy-policy"
            )
            
            uber = Service(
                name="Uber",
                domain="uber.com", 
                category="Transportation",
                description="Ride-sharing and delivery service",
                privacy_policy_url="https://www.uber.com/privacy"
            )
            
            db.add_all([instagram, uber])
            await db.commit()
            await db.refresh(instagram)
            await db.refresh(uber)
            print(f"✅ Created test services: Instagram ({instagram.id}), Uber ({uber.id})")
        
        # Add user services
        user_instagram = UserService(
            user_id=test_user.id,
            service_id=instagram.id,
            status="active"
        )
        
        user_uber = UserService(
            user_id=test_user.id,
            service_id=uber.id,
            status="active"
        )
        
        db.add_all([user_instagram, user_uber])
        await db.commit()
        print("✅ Added services to user")
        
        # Add user preferences (user wants to avoid sharing location and photos)
        location_pref = UserPreference(
            user_id=test_user.id,
            data_category=DataCategoryType.PRECISE_LOCATION,
            avoid_sharing=True,
            importance_level=5  # Very important
        )
        
        photo_pref = UserPreference(
            user_id=test_user.id,
            data_category=DataCategoryType.PHOTOS,
            avoid_sharing=True,
            importance_level=4  # Important
        )
        
        db.add_all([location_pref, photo_pref])
        await db.commit()
        print("✅ Added user preferences")
        
        # Check if data categories already exist for these services
        existing_categories_query = await db.execute(
            select(DataCategory).where(
                DataCategory.service_id.in_([instagram.id, uber.id])
            )
        )
        existing_categories = existing_categories_query.scalars().all()
        
        if len(existing_categories) >= 4:
            print("✅ Using existing data categories for services")
        else:
            # Add data categories for Instagram (collects photos - conflicts with user preference)
            instagram_photos = DataCategory(
                service_id=instagram.id,
                category_type=DataCategoryType.PHOTOS,
                is_collected=True,
                is_required=True,  # Required for core functionality
                purpose="Photo sharing and storage",
                is_shared_with_third_parties=False,
                opt_out_available=False,
                can_be_deleted=True
            )
            
            instagram_contacts = DataCategory(
                service_id=instagram.id,
                category_type=DataCategoryType.CONTACTS_LIST,
                is_collected=True,
                is_required=False,
                purpose="Find friends and suggest connections",
                is_shared_with_third_parties=False,
                opt_out_available=True,
                can_be_deleted=True
            )
            
            # Add data categories for Uber (collects location - conflicts with user preference)
            uber_location = DataCategory(
                service_id=uber.id,
                category_type=DataCategoryType.PRECISE_LOCATION,
                is_collected=True,
                is_required=True,  # Required for ride matching
                purpose="Ride matching and navigation",
                is_shared_with_third_parties=True,  # Shared with drivers
                opt_out_available=False,
                can_be_deleted=False
            )
            
            uber_payment = DataCategory(
                service_id=uber.id,
                category_type=DataCategoryType.CREDIT_CARD_INFO,
                is_collected=True,
                is_required=True,
                purpose="Payment processing",
                is_shared_with_third_parties=True,  # Shared with payment processors
                opt_out_available=False,
                can_be_deleted=False
            )
            
            db.add_all([instagram_photos, instagram_contacts, uber_location, uber_payment])
            await db.commit()
            print("✅ Added data categories for services")
        
        return test_user.id


async def test_privacy_scoring():
    """Test the privacy scoring engine with sample data."""
    
    print("\n🧠 Testing Privacy Scoring Engine")
    print("=" * 50)
    
    try:
        # Create test data
        user_id = await create_test_data()
        
        # Test privacy score calculation
        async with AsyncSessionLocal() as db:
            print(f"\n🔍 Calculating privacy score for user {user_id}...")
            
            # Calculate and save privacy score
            result = await privacy_service.calculate_and_save_privacy_score(user_id, db)
            
            if result["status"] == "success":
                print("✅ Privacy score calculation successful!")
                print(f"📊 Results:")
                print(f"   Score ID: {result['score_id']}")
                print(f"   Calculated at: {result['calculated_at']}")
                
                scores = result["scores"]
                print(f"\n📈 Score Breakdown:")
                print(f"   Overall Score: {scores['overall_score']:.1f}/100")
                print(f"   Data Collection: {scores['data_collection_score']:.1f}/100")
                print(f"   Data Sharing: {scores['data_sharing_score']:.1f}/100")
                print(f"   User Control: {scores['user_control_score']:.1f}/100")
                print(f"   Preference Match: {scores['preference_match_score']:.1f}/100")
                print(f"   Improvement Potential: {scores['improvement_potential']:.1f}%")
                print(f"   Trend: {scores['score_trend']}")
                
                insights = result["insights"]
                print(f"\n💡 Insights:")
                print(f"   Privacy Level: {insights['privacy_level']}")
                print(f"   Description: {insights['level_description']}")
                print(f"   Services Analyzed: {insights['services_analyzed']}")
                
                if insights["concerns"]:
                    print(f"\n⚠️  Main Concerns:")
                    for concern in insights["concerns"]:
                        print(f"   • {concern['area']}: {concern['message']} (Score: {concern['score']:.1f})")
                
                if insights["strengths"]:
                    print(f"\n✅ Strengths:")
                    for strength in insights["strengths"]:
                        print(f"   • {strength['area']}: {strength['message']} (Score: {strength['score']:.1f})")
                
                if insights["quick_tips"]:
                    print(f"\n💡 Quick Tips:")
                    for tip in insights["quick_tips"]:
                        print(f"   {tip}")
                
                # Test getting latest score
                print(f"\n🔄 Testing score retrieval...")
                latest_score = await privacy_service.get_latest_privacy_score(user_id, db)
                
                if latest_score:
                    print(f"✅ Retrieved latest score: {latest_score['scores']['overall_score']:.1f}/100")
                    return True
                else:
                    print("❌ No score found")
                    return False
            
            else:
                print(f"❌ Privacy score calculation failed: {result['message']}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Privacy Scoring Engine Test")
    print("=" * 50)
    
    # Run the test
    success = asyncio.run(test_privacy_scoring())
    
    if success:
        print("\n✅ Test completed successfully!")
        exit(0)
    else:
        print("\n❌ Test failed!")
        exit(1)
