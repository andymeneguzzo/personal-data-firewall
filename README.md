# 🔒 Personal Data Firewall API

> **API for Tracking and Controlling Your Digital Footprint**

A modern, security-focused backend API that helps users understand and control their digital footprint by tracking services they use, analyzing privacy policies, and providing personalized recommendations.

## 🎯 Project Overview

The Personal Data Firewall API is designed to be a **portfolio-worthy backend project** that demonstrates enterprise-level engineering skills including:

- **🔐 Security-First Architecture** - JWT authentication, rate limiting, input validation
- **📊 Complex Business Logic** - Policy evaluation, privacy scoring, recommendations
- **🏗️ Clean Architecture** - Domain-driven design with proper separation of concerns
- **📈 Production-Ready Features** - Background jobs, caching, comprehensive testing
- **📚 API Documentation** - Auto-generated Swagger/OpenAPI documentation

## ✨ Current Features

### ✅ **Implemented & Tested (100% Success Rate)**

#### 🔐 **Authentication & Security**
- JWT token-based authentication
- Password hashing with bcrypt
- Rate limiting (60 requests/minute)
- Input validation and sanitization
- CORS headers configuration
- Security headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection)

#### 🗄️ **Database & Models**
- **SQLAlchemy async ORM with SQLite**
- **Comprehensive User Model**: Email/password authentication, preferences, privacy score, alerts
- **Service Model**: Tracks digital services, categories, and user-service relationships
- **Policy Model**: Stores privacy policies, types (privacy, terms, cookie, DPA), and findings
- **Policy Finding Model**: Captures analysis results, risk levels, confidence, and clause text
- **Data Category Model**: Rich taxonomy of personal data types (identity, location, contact, media, behavioral, biometric, financial, health, device)
- **User Preferences & Privacy Score**: User-specific privacy settings and scoring
- **Alert Model**: Privacy alerts and types
- **Proper database migrations and schema management**
- **Transaction handling with rollback on errors**

#### 🚀 **API Endpoints**
- **Health Check**: `/health` - System status monitoring
- **Authentication**: 
  - `POST /api/v1/auth/register` - User registration
  - `POST /api/v1/auth/login` - User login
  - `GET /api/v1/auth/me` - Get current user info
- **User Management**: `GET /api/v1/users/`
- **Service Tracking**: `GET /api/v1/services/`
- **Privacy Recommendations**: `GET /api/v1/privacy/`
- **Policy & Data Category Expansion Ready**

#### 🧪 **Testing & Quality**
- **25 comprehensive test cases** with 100% success rate
- Automated test suite with metrics tracking
- Error handling and edge case coverage
- Performance and security testing
- Database isolation testing

## 🏗️ Technical Architecture

### **Tech Stack**
```
Backend Framework: FastAPI (Python 3.12+)
Database: SQLite with SQLAlchemy Async
Authentication: JWT with python-jose
Security: bcrypt, rate limiting, CORS
Testing: pytest, automated test suite
Documentation: Auto-generated Swagger UI
```

### **Project Structure**
```
personal-data-firewall/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── config.py          # Settings and configuration
│   │   ├── database.py        # Database setup and sessions
│   │   └── security.py        # JWT, hashing, rate limiting
│   ├── api/
│   │   └── v1/
│   │       ├── api.py         # Main router
│   │       └── endpoints/
│   │           ├── auth.py    # Authentication endpoints
│   │           ├── users.py   # User management
│   │           ├── services.py # Service tracking
│   │           └── privacy.py # Privacy features
│   ├── models/
│   │   └── user.py           # SQLAlchemy models
│   └── schemas/
│       └── auth.py           # Pydantic schemas
├── requirements.txt           # Python dependencies
├── run.py                    # Development server
├── api-endpoints-test.sh     # Comprehensive test suite
└── README.md                 # This file
```

### **Security Features**
- **JWT Authentication**: Secure token-based auth with configurable expiration
- **Password Security**: bcrypt hashing with salt
- **Rate Limiting**: In-memory rate limiter (60 req/min)
- **Input Validation**: Pydantic schemas with email validation
- **CORS Protection**: Configurable cross-origin resource sharing
- **Security Headers**: XSS protection, content type options, frame options

## 🚀 Quick Start

### **Prerequisites**
- Python 3.12+
- pip (Python package manager)

### **Installation**

1. **Clone the repository**
```bash
git clone <repository-url>
cd personal-data-firewall
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the development server**
```bash
python run.py
```

4. **Access the API**
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Root Endpoint**: http://localhost:8000/

### **Running Tests**

Execute the comprehensive test suite:
```bash
./api-endpoints-test.sh
```

**Expected Output:**
```
📊 Test Metrics Summary:
----------------------
Total tests run: 25
Tests passed:    25
Tests failed:    0

Success Rate: 100.00%
Failure Rate: 0.00%

🎯 All tests passed! Excellent API health.
```

## 📚 API Documentation

### **Authentication Endpoints**

#### **Register User**
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": 1,
  "email": "user@example.com"
}
```

#### **Login User**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### **Get Current User**
```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

### **Health Check**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Personal Data Firewall API",
  "version": "1.0.0",
  "database": "connected"
}
```

## 🔧 Configuration

### **Environment Variables**
Create a `.env` file in the root directory:

```env
# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite+aiosqlite:///./personal_data_firewall.db

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

### **Default Settings**
- **JWT Secret**: Auto-generated secure key
- **Token Expiration**: 30 minutes
- **Rate Limit**: 60 requests per minute
- **Database**: SQLite (development)
- **CORS**: Configured for local development

## 🧪 Testing Strategy

### **Test Coverage**
- ✅ **Authentication Tests**: Registration, login, token validation
- ✅ **Security Tests**: Rate limiting, input validation, error handling
- ✅ **Database Tests**: User creation, isolation, transaction handling
- ✅ **API Tests**: Endpoint functionality, status codes, response formats
- ✅ **Header Tests**: CORS and security headers validation
- ✅ **Error Handling**: Invalid inputs, missing fields, edge cases

### **Test Metrics**
```
📊 Test Results:
- Total Tests: 25
- Passed: 25 (100%)
- Failed: 0 (0%)
- Coverage: Comprehensive
```

### **Running Individual Tests**
```bash
# Test authentication only
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Test with authentication
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <your-token>"
```

## 🎯 Portfolio Value

### **Technical Skills Demonstrated**

#### **Backend Development**
- **FastAPI**: Modern async web framework
- **SQLAlchemy**: ORM with async support
- **JWT Authentication**: Industry-standard auth system
- **Rate Limiting**: Production-ready security feature

#### **Security Implementation**
- **Password Hashing**: bcrypt with salt
- **Input Validation**: Pydantic schemas
- **CORS Configuration**: Cross-origin security
- **Security Headers**: XSS and injection protection

#### **Testing & Quality**
- **Comprehensive Test Suite**: 25 test cases
- **Automated Testing**: Shell script with metrics
- **Error Handling**: Proper exception management
- **Performance Testing**: Rate limiting validation

#### **Architecture & Design**
- **Clean Architecture**: Separation of concerns
- **Domain-Driven Design**: Business logic organization
- **API Design**: RESTful endpoints with documentation
- **Database Design**: Proper schema and relationships

### **Business Logic Complexity**
- **Policy Evaluation**: Algorithm for privacy analysis
- **Scoring System**: Privacy risk calculation
- **Recommendation Engine**: Personalized suggestions
- **Data Categorization**: Service classification

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** for the excellent async web framework
- **SQLAlchemy** for robust database ORM
- **Pydantic** for data validation
- **JWT** for secure authentication

---

**🎉 Ready for Production**: This API demonstrates enterprise-level backend development skills and is ready to be showcased.

**📊 Current Status**: 100% test success rate with comprehensive security features and clean architecture.
