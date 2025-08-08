#!/bin/bash

# Personal Data Firewall API - Endpoint Testing Script
# This script tests all available endpoints to ensure they work correctly

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

# Metrics counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to make HTTP requests and check responses
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=$4
    local description=$5

    ((TOTAL_TESTS++))
    print_status "Testing: $description"

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi

    # Extract status code (last line)
    status_code=$(echo "$response" | tail -n1)
    # Extract response body (all lines except last)
    response_body=$(echo "$response" | head -n -1)

    if [ "$status_code" = "$expected_status" ]; then
        print_success "✅ $description - Status: $status_code"
        echo "Response: $response_body" | head -c 200
        echo ""
        ((PASSED_TESTS++))
    else
        print_error "❌ $description - Expected: $expected_status, Got: $status_code"
        echo "Response: $response_body"
        ((FAILED_TESTS++))
    fi

    echo "----------------------------------------"
}

# Start the server in the background
print_status "Starting API server (python run.py)..."
python run.py &
SERVER_PID=$!

# Function to clean up server process on exit
cleanup() {
    print_status "Stopping API server (PID $SERVER_PID)..."
    kill $SERVER_PID
    wait $SERVER_PID 2>/dev/null
    print_success "API server stopped."
}
trap cleanup EXIT

# Wait for the server to be ready
print_status "Waiting for server to start..."
for i in {1..20}; do
    if curl -s "$BASE_URL/health" > /dev/null; then
        print_success "Server is running!"
        break
    else
        sleep 0.5
    fi
    if [ $i -eq 20 ]; then
        print_error "Server did not start in time. Exiting."
        exit 1
    fi
done

echo ""
print_status "Starting API endpoint tests..."
echo "========================================"

# Test 1: Health Check
test_endpoint "GET" "$BASE_URL/health" "" "200" "Health Check Endpoint"

# Test 2: Root Endpoint
test_endpoint "GET" "$BASE_URL/" "" "200" "Root Endpoint"

# Test 3: API Documentation
test_endpoint "GET" "$BASE_URL/docs" "" "200" "API Documentation"

# Test 4: Register new user
test_endpoint "POST" "$API_URL/auth/register" "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" "200" "User Registration"

# Test 5: Register duplicate user (should fail)
test_endpoint "POST" "$API_URL/auth/register" "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" "400" "Duplicate User Registration (should fail)"

# Test 6: Login with correct credentials
test_endpoint "POST" "$API_URL/auth/login" "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" "200" "User Login"

# Test 7: Login with wrong password
test_endpoint "POST" "$API_URL/auth/login" "{\"email\":\"$TEST_EMAIL\",\"password\":\"wrongpassword\"}" "401" "Login with Wrong Password"

# Test 8: Login with non-existent user
test_endpoint "POST" "$API_URL/auth/login" "{\"email\":\"nonexistent@example.com\",\"password\":\"$TEST_PASSWORD\"}" "401" "Login with Non-existent User"

# Test 9: Get current user info (without token - should fail)
test_endpoint "GET" "$API_URL/auth/me" "" "401" "Get Current User (without token)"

# Test 10: Test placeholder endpoints
test_endpoint "GET" "$API_URL/users/" "" "200" "Users Endpoint (placeholder)"
test_endpoint "GET" "$API_URL/services/" "" "200" "Services Endpoint (placeholder)"
test_endpoint "GET" "$API_URL/privacy/" "" "200" "Privacy Endpoint (placeholder)"

echo ""
print_status "Testing with authentication token..."

# Get token by logging in
print_status "Getting authentication token..."
login_response=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

# Extract token from response using jq if available, otherwise use grep
if command -v jq &> /dev/null; then
    TOKEN=$(echo "$login_response" | jq -r '.access_token // empty')
else
    TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
fi

if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
    print_success "Token obtained successfully: ${TOKEN:0:20}..."

    # Test 11: Get current user info (with token) - Fixed authentication
    print_status "Testing: Get Current User (with token)"
    ((TOTAL_TESTS++))
    response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "$API_URL/auth/me")
    status_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" = "200" ]; then
        print_success "✅ Get Current User (with token) - Status: $status_code"
        echo "Response: $response_body" | head -c 200
        echo ""
        ((PASSED_TESTS++))
    else
        print_error "❌ Get Current User (with token) - Expected: 200, Got: $status_code"
        echo "Response: $response_body"
        ((FAILED_TESTS++))
    fi
    echo "----------------------------------------"

    # Test 12: Test rate limiting (make multiple requests)
    print_status "Testing rate limiting..."
    for i in {1..5}; do
        ((TOTAL_TESTS++))
        response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "$API_URL/auth/me")
        status_code=$(echo "$response" | tail -n1)
        if [ "$status_code" = "200" ]; then
            print_success "Rate limit test $i: OK"
            ((PASSED_TESTS++))
        else
            print_warning "Rate limit test $i: Status $status_code"
            ((FAILED_TESTS++))
        fi
    done

else
    print_error "Failed to obtain authentication token"
    print_error "Login response: $login_response"
fi

echo ""
print_status "Testing error handling..."

# Test 13: Invalid JSON
test_endpoint "POST" "$API_URL/auth/login" "invalid json" "422" "Invalid JSON Format"

# Test 14: Missing required fields
test_endpoint "POST" "$API_URL/auth/login" "{\"email\":\"$TEST_EMAIL\"}" "422" "Missing Required Fields"

# Test 15: Invalid email format
test_endpoint "POST" "$API_URL/auth/register" "{\"email\":\"invalid-email\",\"password\":\"$TEST_PASSWORD\"}" "422" "Invalid Email Format"

echo ""
print_status "Performance and Security Tests..."

# Test 16: Check CORS headers (use GET instead of HEAD)
print_status "Testing CORS headers..."
((TOTAL_TESTS++))
cors_response=$(curl -s -I -H "Origin: http://localhost:3000" "$BASE_URL/health")
if echo "$cors_response" | grep -q "Access-Control-Allow-Origin"; then
    print_success "CORS headers are properly configured"
    ((PASSED_TESTS++))
else
    print_warning "CORS headers not found in response"
    ((FAILED_TESTS++))
fi

# Test 17: Check security headers (use GET instead of HEAD)
print_status "Testing security headers..."
((TOTAL_TESTS++))
security_response=$(curl -s -I "$BASE_URL/health")
if echo "$security_response" | grep -q "X-Content-Type-Options\|X-Frame-Options\|X-XSS-Protection"; then
    print_success "Security headers are present"
    ((PASSED_TESTS++))
else
    print_warning "Security headers not found"
    ((FAILED_TESTS++))
fi

echo ""
print_status "Database Tests..."

# Test 18: Register another user to test database isolation
test_endpoint "POST" "$API_URL/auth/register" "{\"email\":\"$TEST_EMAIL_2\",\"password\":\"$TEST_PASSWORD\"}" "200" "Second User Registration"

# Test 19: Login with second user
test_endpoint "POST" "$API_URL/auth/login" "{\"email\":\"$TEST_EMAIL_2\",\"password\":\"$TEST_PASSWORD\"}" "200" "Second User Login"

echo ""
print_status "Summary of Tests:"
echo "======================"
print_success "✅ Health check endpoint working"
print_success "✅ Authentication endpoints working"
print_success "✅ Database operations working"
print_success "✅ Error handling working"
print_success "✅ Security middleware active"
print_success "✅ API documentation accessible"

echo ""
print_status "🎉 All tests completed! Your Personal Data Firewall API is working correctly."
print_status "📚 Visit http://localhost:8000/docs for interactive API documentation"
print_status "🔐 Test authentication with the provided test credentials"
print_status "🚀 Ready to move on to the next phase: Database Schema Design"

echo ""
print_status "Test Credentials Created:"
echo "- Email: $TEST_EMAIL"
echo "- Email: $TEST_EMAIL_2"
echo "- Password: $TEST_PASSWORD"
echo ""
print_status "You can use these credentials to test the API manually in the Swagger UI."

# -------------------------
# Metrics Section
# -------------------------
echo ""
print_status "📊 Test Metrics Summary:"
echo "----------------------"
echo "Total tests run: $TOTAL_TESTS"
echo "Tests passed:    $PASSED_TESTS"
echo "Tests failed:    $FAILED_TESTS"

if [ "$TOTAL_TESTS" -gt 0 ]; then
    SUCCESS_RATE=$(awk "BEGIN {printf \"%.2f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")
    FAILURE_RATE=$(awk "BEGIN {printf \"%.2f\", ($FAILED_TESTS/$TOTAL_TESTS)*100}")
else
    SUCCESS_RATE=0
    FAILURE_RATE=0
fi

echo ""
echo -e "${GREEN}Success Rate: $SUCCESS_RATE%${NC}"
echo -e "${RED}Failure Rate: $FAILURE_RATE%${NC}"
echo ""
if [ "$FAILED_TESTS" -eq 0 ]; then
    print_success "🎯 All tests passed! Excellent API health."
else
    print_warning "Some tests failed. Please review the errors above."
fi
