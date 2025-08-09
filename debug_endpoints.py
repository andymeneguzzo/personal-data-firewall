#!/usr/bin/env python3
"""
Comprehensive debug script to test service endpoints.
This script starts the server, tests endpoints, and stops the server.
"""

import asyncio
import aiohttp
import json
import subprocess
import time
import sys
import signal
import os

class EndpointDebugger:
    def __init__(self):
        self.server_process = None
        self.base_url = "http://localhost:8000"
        
    def start_server(self):
        """Start the FastAPI server."""
        print("🚀 Starting Personal Data Firewall API server...")
        
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, "run.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # Wait for server to start
            for i in range(30):
                try:
                    import requests
                    response = requests.get(f"{self.base_url}/health", timeout=2)
                    if response.status_code == 200:
                        print("✅ Server started successfully")
                        return True
                except:
                    time.sleep(1)
            
            print("❌ Server failed to start within 30 seconds")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start server: {str(e)}")
            return False
    
    def stop_server(self):
        """Stop the FastAPI server."""
        if self.server_process:
            print("🛑 Stopping server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=10)
                print("✅ Server stopped successfully")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                print("⚠️ Server force-killed")
    
    async def test_endpoints(self):
        """Test service endpoints comprehensively."""
        print("\n🔍 Testing Service Endpoints")
        print("=" * 50)
        
        async with aiohttp.ClientSession() as session:
            tests_passed = 0
            total_tests = 0
            
            # Test 1: Health check
            total_tests += 1
            try:
                async with session.get(f"{self.base_url}/health") as response:
                    print(f"✅ Health Check: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"   Status: {data.get('status', 'unknown')}")
                        tests_passed += 1
                    else:
                        print(f"   ❌ Expected 200, got {response.status}")
            except Exception as e:
                print(f"❌ Health Check: {e}")
            
            # Test 2: OpenAPI Schema
            total_tests += 1
            try:
                async with session.get(f"{self.base_url}/openapi.json") as response:
                    print(f"✅ OpenAPI Schema: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        paths = data.get("paths", {})
                        service_paths = [p for p in paths.keys() if "/services" in p]
                        print(f"   Total API paths: {len(paths)}")
                        print(f"   Service endpoints: {len(service_paths)}")
                        tests_passed += 1
                        
                        # Show service endpoints
                        if service_paths:
                            print("   Service endpoints found:")
                            for path in sorted(service_paths)[:5]:  # Show first 5
                                print(f"     • {path}")
                    else:
                        print(f"   ❌ Expected 200, got {response.status}")
            except Exception as e:
                print(f"❌ OpenAPI Schema: {e}")
            
            # Test 3: Service Categories
            total_tests += 1
            try:
                async with session.get(f"{self.base_url}/api/v1/services/categories") as response:
                    print(f"✅ Service Categories: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"   Found {len(data)} categories: {data}")
                        tests_passed += 1
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Expected 200, got {response.status}")
                        print(f"   Response: {error_text[:200]}")
            except Exception as e:
                print(f"❌ Service Categories: {e}")
            
            # Test 4: Get All Services
            total_tests += 1
            try:
                async with session.get(f"{self.base_url}/api/v1/services/") as response:
                    print(f"✅ Get All Services: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"   Found {len(data)} services")
                        tests_passed += 1
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Expected 200, got {response.status}")
                        print(f"   Response: {error_text[:200]}")
            except Exception as e:
                print(f"❌ Get All Services: {e}")
            
            # Test 5: Search Services
            total_tests += 1
            try:
                async with session.get(f"{self.base_url}/api/v1/services/search?q=test") as response:
                    print(f"✅ Search Services: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"   Search results: {data.get('total_found', 0)} found")
                        tests_passed += 1
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Expected 200, got {response.status}")
                        print(f"   Response: {error_text[:200]}")
            except Exception as e:
                print(f"❌ Search Services: {e}")
            
            # Test 6: API Documentation
            total_tests += 1
            try:
                async with session.get(f"{self.base_url}/docs") as response:
                    print(f"✅ API Documentation: {response.status}")
                    if response.status == 200:
                        print("   Swagger UI accessible")
                        tests_passed += 1
                    else:
                        print(f"   ❌ Expected 200, got {response.status}")
            except Exception as e:
                print(f"❌ API Documentation: {e}")
            
            # Test 7: Authentication Required Endpoint (should get 401)
            total_tests += 1
            try:
                async with session.get(f"{self.base_url}/api/v1/services/user/my-services") as response:
                    print(f"✅ Auth Required Endpoint: {response.status}")
                    if response.status == 401:
                        print("   ✅ Correctly returns 401 without authentication")
                        tests_passed += 1
                    else:
                        print(f"   ⚠️ Expected 401, got {response.status}")
            except Exception as e:
                print(f"❌ Auth Required Endpoint: {e}")
            
            # Test Summary
            print("\n" + "=" * 50)
            print(f"📊 Endpoint Test Results:")
            print(f"   Tests Passed: {tests_passed}/{total_tests}")
            print(f"   Success Rate: {(tests_passed/total_tests)*100:.1f}%")
            
            if tests_passed >= total_tests * 0.8:
                print("✅ Endpoints are working well!")
                return True
            else:
                print("❌ Some endpoints need attention")
                return False
    
    async def debug_import_issues(self):
        """Debug potential import issues."""
        print("\n🔍 Debugging Import Issues")
        print("=" * 30)
        
        try:
            print("Testing imports...")
            from app.main import app
            print("✅ Main app imported successfully")
            
            from app.api.v1.api import api_router
            print("✅ API router imported successfully")
            
            from app.api.v1.endpoints.services import router
            print("✅ Service router imported successfully")
            
            # Check router routes
            routes = []
            for route in router.routes:
                if hasattr(route, 'path'):
                    routes.append(route.path)
            
            print(f"✅ Service router has {len(routes)} routes:")
            for route in routes[:5]:  # Show first 5
                print(f"   • {route}")
            
            return True
            
        except Exception as e:
            print(f"❌ Import error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_comprehensive_debug(self):
        """Run comprehensive debugging."""
        print("🔬 Personal Data Firewall - Endpoint Debug Suite")
        print("=" * 60)
        
        # First check imports
        if not asyncio.run(self.debug_import_issues()):
            print("❌ Import issues detected. Fix imports before testing endpoints.")
            return False
        
        # Start server
        if not self.start_server():
            print("❌ Cannot start server. Exiting.")
            return False
        
        try:
            # Wait for server initialization
            time.sleep(3)
            
            # Test endpoints
            success = asyncio.run(self.test_endpoints())
            
            return success
            
        finally:
            self.stop_server()


def main():
    """Main function."""
    debugger = EndpointDebugger()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n🛑 Debug interrupted by user")
        debugger.stop_server()
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run comprehensive debug
    success = debugger.run_comprehensive_debug()
    
    if success:
        print("\n🎉 Debug completed successfully!")
        print("✅ Service endpoints are ready for testing!")
    else:
        print("\n❌ Debug found issues that need to be addressed.")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
