#!/usr/bin/env python3
"""
Debug script to identify server startup issues.
"""

import sys
import os
import traceback

print("🔍 Debugging Personal Data Firewall API Server Startup")
print("=" * 60)

try:
    print("1. Checking Python path...")
    print(f"   Current directory: {os.getcwd()}")
    print(f"   Python executable: {sys.executable}")
    print(f"   Python version: {sys.version}")
    
    print("\n2. Testing basic imports...")
    
    # Test core imports
    try:
        import fastapi
        print(f"   ✅ FastAPI: {fastapi.__version__}")
    except ImportError as e:
        print(f"   ❌ FastAPI import failed: {e}")
    
    try:
        import sqlalchemy
        print(f"   ✅ SQLAlchemy: {sqlalchemy.__version__}")
    except ImportError as e:
        print(f"   ❌ SQLAlchemy import failed: {e}")
    
    try:
        import aiosqlite
        print(f"   ✅ aiosqlite imported successfully")
    except ImportError as e:
        print(f"   ❌ aiosqlite import failed: {e}")
    
    print("\n3. Testing app imports...")
    
    # Test app imports step by step
    try:
        from app.core.database import engine
        print("   ✅ Database engine imported")
    except Exception as e:
        print(f"   ❌ Database import failed: {e}")
        traceback.print_exc()
    
    try:
        from app.models import User
        print("   ✅ User model imported")
    except Exception as e:
        print(f"   ❌ User model import failed: {e}")
        traceback.print_exc()
    
    try:
        from app.schemas.service import ServiceResponse
        print("   ✅ Service schemas imported")
    except Exception as e:
        print(f"   ❌ Service schema import failed: {e}")
        traceback.print_exc()
    
    try:
        from app.api.v1.endpoints.services import router
        print("   ✅ Service endpoints imported")
    except Exception as e:
        print(f"   ❌ Service endpoints import failed: {e}")
        traceback.print_exc()
    
    print("\n4. Testing main app import...")
    try:
        from app.main import app
        print("   ✅ Main app imported successfully")
    except Exception as e:
        print(f"   ❌ Main app import failed: {e}")
        traceback.print_exc()
    
    print("\n5. Testing run.py...")
    try:
        with open("run.py", "r") as f:
            content = f.read()
            print("   ✅ run.py file exists")
            if "uvicorn" in content:
                print("   ✅ run.py contains uvicorn")
            else:
                print("   ⚠️ run.py may not contain uvicorn")
    except FileNotFoundError:
        print("   ❌ run.py file not found")
    except Exception as e:
        print(f"   ❌ Error reading run.py: {e}")

except Exception as e:
    print(f"\n❌ Critical error during debugging: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("🎯 Debugging complete. Check for any ❌ issues above.")
