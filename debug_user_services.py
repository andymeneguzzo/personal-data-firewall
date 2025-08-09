#!/usr/bin/env python3
"""
Debug script to test user service endpoints and identify the exact error.
"""

import asyncio
import aiohttp
import sys
import os
import traceback

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_user_services_debug():
    """Debug the user services endpoint."""
    
    BASE_URL = "http://localhost:8000"
    API_URL = f"{BASE_URL}/api/v1"
    
    print("🔍 Debugging User Services Endpoint")
    print("=" * 50)
    
    # First, check if server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status != 200:
                    print("❌ Server not running")
                    return False
                print("✅ Server is running")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False
    
    # Test authentication first
    print("\n🔐 Testing Authentication...")
    try:
        async with aiohttp.ClientSession() as session:
            # Register a test user
            register_data = {
                "email": f"debug_{int(asyncio.get_event_loop().time())}@example.com",
                "password": "testpassword123"
            }
            
            async with session.post(f"{API_URL}/auth/register", json=register_data) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get("access_token")
                    print(f"✅ User registered successfully")
                    print(f"🎫 Token: {token[:20]}...")
                else:
                    error_text = await response.text()
                    print(f"❌ Registration failed: {response.status}")
                    print(f"Response: {error_text}")
                    return False
            
            # Test authenticated request
            headers = {'Authorization': f'Bearer {token}'}
            print(f"\n🧪 Testing user services endpoint...")
            
            async with session.get(f"{API_URL}/services/user/my-services", headers=headers) as response:
                print(f"Status: {response.status}")
                response_text = await response.text()
                print(f"Response: {response_text}")
                
                if response.status == 500:
                    print("❌ 500 Internal Server Error detected")
                    print("This suggests a server-side issue with the endpoint")
                elif response.status == 200:
                    print("✅ Endpoint working correctly")
                    data = await response.json()
                    print(f"Data: {data}")
                else:
                    print(f"⚠️ Unexpected status: {response.status}")
                
            # Test privacy impact endpoint too
            print(f"\n🧪 Testing privacy impact endpoint...")
            
            async with session.get(f"{API_URL}/services/user/privacy-impact", headers=headers) as response:
                print(f"Status: {response.status}")
                response_text = await response.text()
                print(f"Response: {response_text}")
                
                if response.status == 500:
                    print("❌ 500 Internal Server Error detected")
                elif response.status == 200:
                    print("✅ Endpoint working correctly")
                    data = await response.json()
                    print(f"Data: {data}")
                else:
                    print(f"⚠️ Unexpected status: {response.status}")
                    
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_user_services_debug())
