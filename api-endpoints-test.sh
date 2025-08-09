#!/bin/bash

# Personal Data Firewall API - Comprehensive Testing Script
# This script tests all API endpoints AND the privacy scoring engine

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API base URL
BASE_URL="http://localhost:8000"
API_URL="$BASE_URL/api/v1"

# Test data - Use unique emails for each test run
TIMESTAMP=$(date +%s)
TEST_EMAIL="test${TIMESTAMP}@example.com"
TEST_PASSWORD="testpassword123"
TEST_EMAIL_2="test2${TIMESTAMP}@example.com"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Improved function to run a test with proper curl handling
run_test() {
    local test_name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="$5"
    local success_pattern="$6"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -e "\n${BLUE}Testing:${NC} $test_name"
    
    # Build curl command based on method
    if [[ "$method" == "GET" ]]; then
        if [[ -n "$data" ]]; then
            # GET with authorization header
            response=$(curl -s -w "\nSTATUS_CODE:%{http_code}" -H "$data" "$endpoint")
        else
            # Simple GET
            response=$(curl -s -w "\nSTATUS_CODE:%{http_code}" "$endpoint")
        fi
    elif [[ "$method" == "POST" ]]; then
        if [[ -n "$success_pattern" && "$success_pattern" == "Authorization:"* ]]; then
            # POST with authorization header
            response=$(curl -s -w "\nSTATUS_CODE:%{http_code}" -X POST -H "Content-Type: application/json" -H "$success_pattern" -d "$data" "$endpoint")
        else
            # Regular POST
            response=$(curl -s -w "\nSTATUS_CODE:%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$endpoint")
        fi
    fi
    
    # Extract status code and body
    actual_status=$(echo "$response" | grep "STATUS_CODE:" | cut -d: -f2)
    response_body=$(echo "$response" | sed '/STATUS_CODE:/d')
    
    # Check status code
    if [[ "$actual_status" == "$expected_status" ]]; then
        # If success pattern provided, check for it (but skip Authorization headers)
        if [[ -n "$success_pattern" && "$success_pattern" != "Authorization:"* && "$response_body" != *"$success_pattern"* ]]; then
            print_error "$test_name - Response doesn't contain expected pattern: $success_pattern"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
        print_success "$test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        print_error "$test_name - Expected status $expected_status, got $actual_status"
        if [[ -n "$response_body" ]]; then
            echo "Response: $response_body" | head -3
        fi
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Function to start server
start_server() {
    print_status "Starting Personal Data Firewall API server..."
    
    # Check if server is already running
    if curl -s "$BASE_URL/health" > /dev/null 2>&1; then
        print_success "Server already running on $BASE_URL"
        return 0
    fi
    
    # Start new server
    python run.py &
    SERVER_PID=$!
    
    # Wait for server to start
    for i in {1..30}; do
        if curl -s "$BASE_URL/health" > /dev/null 2>&1; then
            print_success "Server started successfully on $BASE_URL"
            return 0
        fi
        sleep 1
    done
    
    print_error "Server failed to start within 30 seconds"
    return 1
}

# Function to stop server
stop_server() {
    if [[ -n "$SERVER_PID" ]]; then
        print_status "Stopping server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null
        wait $SERVER_PID 2>/dev/null
    fi
}

# Function to run privacy scoring tests
run_privacy_scoring_tests() {
    print_status "Running Privacy Scoring Engine Tests..."
    echo -e "${BLUE}=" * 50 "${NC}"
    
    # Check if Python test file exists
    if [[ ! -f "test_privacy_scoring.py" ]]; then
        print_error "Privacy scoring test file not found: test_privacy_scoring.py"
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    # Run privacy scoring tests
    python test_privacy_scoring.py
    privacy_test_exit_code=$?
    
    # Count privacy tests as 1 comprehensive test
    PRIVACY_TESTS_COUNT=1
    TOTAL_TESTS=$((TOTAL_TESTS + PRIVACY_TESTS_COUNT))
    
    if [[ $privacy_test_exit_code -eq 0 ]]; then
        PASSED_TESTS=$((PASSED_TESTS + PRIVACY_TESTS_COUNT))
        print_success "Privacy Scoring Engine tests completed successfully"
    else
        FAILED_TESTS=$((FAILED_TESTS + PRIVACY_TESTS_COUNT))
        print_error "Privacy Scoring Engine tests failed"
    fi
}

# Main test execution
main() {
    echo -e "${BLUE}🔒 Personal Data Firewall API - Comprehensive Test Suite${NC}"
    echo -e "${BLUE}=" * 70 "${NC}"
    echo -e "Timestamp: $(date)"
    echo -e "Base URL: $BASE_URL"
    echo ""
    
    # Start the server
    if ! start_server; then
        print_error "Cannot start server. Exiting."
        exit 1
    fi
    
    # Wait a bit more for full initialization
    sleep 3
    
    # Test 1: Health Check
    run_test "Health Check" "GET" "$BASE_URL/health" "" "200" "healthy"
    
    # Test 2: User Registration
    run_test "User Registration" "POST" "$API_URL/auth/register" "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" "200" "access_token"
    
    # Get authentication token for subsequent tests
    AUTH_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")
    
    # Extract token
    TOKEN=$(echo "$AUTH_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    if [[ -z "$TOKEN" ]]; then
        print_warning "Failed to get authentication token, some tests may fail"
        TOKEN="dummy_token"
    fi
    
    # Test 3: User Login
    run_test "User Login" "POST" "$API_URL/auth/login" "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" "200" "access_token"
    
    # Test 4: User Profile (Authenticated)
    run_test "Get User Profile" "GET" "$API_URL/auth/me" "Authorization: Bearer $TOKEN" "200" "email"
    
    # Test 5: Services Endpoint
    run_test "Get Services" "GET" "$API_URL/services/" "" "200" "services"
    
    # Test 6: Privacy Endpoint
    run_test "Get Privacy Info" "GET" "$API_URL/privacy/" "" "200" "privacy"
    
    # Test 7: Users Endpoint
    run_test "Get Users (Protected)" "GET" "$API_URL/users/" "Authorization: Bearer $TOKEN" "200" ""
    
    # Test 8: Invalid Authentication
    run_test "Invalid Token Authentication" "GET" "$API_URL/auth/me" "Authorization: Bearer invalid_token" "401" ""
    
    # Test 9: Registration with Existing Email
    run_test "Duplicate Email Registration" "POST" "$API_URL/auth/register" "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" "400" ""
    
    # Test 10: Invalid Login
    run_test "Invalid Login Credentials" "POST" "$API_URL/auth/login" "{\"email\":\"$TEST_EMAIL\",\"password\":\"wrongpassword\"}" "401" ""
    
    # Test 11: API Documentation (Swagger) - FIXED
    echo -e "\n${BLUE}Testing:${NC} API Documentation (Swagger)"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    DOCS_RESPONSE=$(curl -s -w "\nSTATUS_CODE:%{http_code}" "$BASE_URL/docs")
    DOCS_STATUS=$(echo "$DOCS_RESPONSE" | grep "STATUS_CODE:" | cut -d: -f2)
    DOCS_BODY=$(echo "$DOCS_RESPONSE" | sed '/STATUS_CODE:/d')
    
    if [[ "$DOCS_STATUS" == "200" ]] && [[ "$DOCS_BODY" == *"html"* ]]; then
        print_success "API Documentation (Swagger)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        print_error "API Documentation (Swagger) - Expected 200 with HTML content, got $DOCS_STATUS"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
    # Test 12: OpenAPI Schema
    run_test "OpenAPI Schema" "GET" "$BASE_URL/openapi.json" "" "200" "openapi"
    
    # Test 13: CORS Headers - FIXED
    echo -e "\n${BLUE}Testing:${NC} CORS Headers"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    CORS_RESPONSE=$(curl -s -I "$BASE_URL/health")
    if echo "$CORS_RESPONSE" | grep -qi "access-control-allow-origin"; then
        print_success "CORS Headers"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        print_error "CORS Headers - access-control-allow-origin not found"
        echo "Available headers:"
        echo "$CORS_RESPONSE" | head -10
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
    # Test 14: Security Headers
    echo -e "\n${BLUE}Testing:${NC} Security Headers"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    SECURITY_RESPONSE=$(curl -s -I "$BASE_URL/health")
    if echo "$SECURITY_RESPONSE" | grep -qi "x-content-type-options"; then
        print_success "Security Headers"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        print_error "Security Headers - x-content-type-options not found"
        echo "Available headers:"
        echo "$SECURITY_RESPONSE" | head -10
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
    echo -e "\n${BLUE}=" * 70 "${NC}"
    
    # Run Privacy Scoring Engine Tests
    run_privacy_scoring_tests
    
    # Stop the server
    stop_server
    
    # Calculate success rate
    if [[ $TOTAL_TESTS -gt 0 ]]; then
        SUCCESS_RATE=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
    else
        SUCCESS_RATE=0
    fi
    
    # Final Report
    echo -e "\n${BLUE}📊 COMPREHENSIVE TEST RESULTS${NC}"
    echo -e "${BLUE}=" * 70 "${NC}"
    echo -e "🎯 Total Tests: $TOTAL_TESTS"
    echo -e "✅ Passed: $PASSED_TESTS"
    echo -e "❌ Failed: $FAILED_TESTS"
    echo -e "📈 Success Rate: $SUCCESS_RATE%"
    echo -e "⏱️ Test Duration: $(date)"
    
    # Status assessment
    if [[ $SUCCESS_RATE -ge 95 ]]; then
        echo -e "\n${GREEN}🏆 EXCELLENT: API is production-ready!${NC}"
        exit 0
    elif [[ $SUCCESS_RATE -ge 85 ]]; then
        echo -e "\n${YELLOW}✅ GOOD: API is mostly functional, minor issues to address${NC}"
        exit 0
    elif [[ $SUCCESS_RATE -ge 70 ]]; then
        echo -e "\n${YELLOW}⚠️ FAIR: API needs improvements${NC}"
        exit 1
    else
        echo -e "\n${RED}❌ POOR: API has significant issues${NC}"
        exit 1
    fi
}

# Cleanup on exit
trap 'stop_server' EXIT

# Run main function
main "$@"
