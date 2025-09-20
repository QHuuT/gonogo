# Shared Infrastructure

**Last Updated**: 2025-09-20

## 🎯 Overview

This document outlines the shared infrastructure components that support all capabilities within the GoNoGo platform. These components provide common functionality, ensure consistency across the system, and maintain GDPR compliance standards.

## 🏗️ Infrastructure Components

### 1. Database Infrastructure

#### SQLAlchemy ORM Foundation
```python
# Base model with GDPR compliance built-in
class GDPRBaseModel(Base):
    __abstract__ = True

    id = Column(UUID, primary_key=True, default=uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # GDPR compliance fields
    consent_given = Column(Boolean, default=False)
    consent_timestamp = Column(DateTime, nullable=True)
    retention_until = Column(DateTime, nullable=True)
    anonymized = Column(Boolean, default=False)
```

#### Connection Management
- **Development**: SQLite with WAL mode for concurrency
- **Production**: PostgreSQL with connection pooling
- **Migrations**: Alembic with automated rollback capability
- **Backup**: Automated daily backups with 30-day retention

### 2. Authentication & Authorization

#### User Session Management
```python
# Session handling with privacy protection
class SessionManager:
    def create_session(self, user_data: dict) -> str:
        # Minimal data storage with automatic expiration
        session_data = {
            'user_id': anonymize_user_id(user_data['id']),
            'permissions': user_data.get('permissions', []),
            'expires_at': datetime.utcnow() + timedelta(hours=24)
        }
        return self.secure_token_generator.create(session_data)
```

#### Permission System
```
Roles: Anonymous → Commenter → Moderator → Admin
   ↓         ↓          ↓          ↓
Read      Comment    Moderate   Full Access
Only       Posts      Content     System
```

### 3. Configuration Management

#### Environment-Based Configuration
```python
# Settings hierarchy with GDPR defaults
class Settings(BaseSettings):
    # Database
    database_url: str
    database_pool_size: int = 10

    # GDPR Compliance
    data_retention_days: int = 365
    anonymization_delay_days: int = 30
    consent_cookie_duration: int = 365

    # Security
    secret_key: str
    cors_origins: List[str] = []
    rate_limit_per_minute: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = False
```

#### Feature Flags
```python
# Simple configuration-based feature toggles
FEATURE_FLAGS = {
    'enable_comments': True,
    'enable_user_registration': True,
    'enable_gdpr_banner': True,
    'enable_analytics': False,  # Privacy-first default
    'enable_email_notifications': True
}
```

### 4. Logging & Monitoring

#### Structured Logging
```python
# Privacy-aware logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'privacy_safe': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'filters': ['privacy_filter']  # Removes PII automatically
        }
    },
    'filters': {
        'privacy_filter': {
            '()': 'src.shared.utils.privacy_log_filter.PrivacyLogFilter'
        }
    }
}
```

#### Performance Monitoring
```python
# Built-in performance tracking
class PerformanceMiddleware:
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log performance metrics without PII
        logger.info(
            "request_processed",
            extra={
                'method': request.method,
                'path_template': get_path_template(request.url.path),
                'status_code': response.status_code,
                'duration_ms': round(process_time * 1000, 2)
            }
        )
        return response
```

### 5. Security Headers & Middleware

#### Security Middleware Stack
```python
# Applied to all requests automatically
SECURITY_MIDDLEWARE = [
    SecurityHeadersMiddleware,      # HSTS, CSP, X-Frame-Options
    GDPRComplianceMiddleware,       # Privacy headers and checks
    RateLimitingMiddleware,         # Prevent abuse
    ValidationMiddleware,           # Input sanitization
    AuditLoggingMiddleware         # Compliance logging
]
```

#### Content Security Policy
```python
CSP_POLICY = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "'unsafe-inline'"],  # Minimal inline scripts
    'style-src': ["'self'", "'unsafe-inline'"],   # Local stylesheets only
    'img-src': ["'self'", "data:", "https:"],     # Allow images from CDN
    'connect-src': ["'self'"],                     # API calls only to self
    'font-src': ["'self'"],                       # Local fonts only
    'frame-ancestors': ["'none'"],                # Prevent framing
    'base-uri': ["'self'"]                       # Prevent base tag attacks
}
```

## 🔧 Shared Utilities

### 1. Data Validation & Sanitization

#### Input Validation Framework
```python
# Pydantic models with GDPR considerations
class CommentCreateRequest(BaseModel):
    content: str = Field(..., max_length=1000, description="Comment content")
    author_name: str = Field(..., max_length=100, description="Author name")
    author_email: EmailStr = Field(..., description="Author email for notifications")
    gdpr_consent: bool = Field(..., description="GDPR consent confirmation")

    @validator('content')
    def validate_content(cls, v):
        # Sanitize HTML and check for malicious content
        return sanitize_html(v)

    @validator('gdpr_consent')
    def validate_gdpr_consent(cls, v):
        if not v:
            raise ValueError('GDPR consent is required')
        return v
```

#### Data Sanitization
```python
# HTML sanitization with allowlist approach
ALLOWED_HTML_TAGS = ['p', 'br', 'strong', 'em', 'a', 'ul', 'ol', 'li']
ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}

def sanitize_html(content: str) -> str:
    return bleach.clean(
        content,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
```

### 2. GDPR Compliance Utilities

#### Data Anonymization
```python
class DataAnonymizer:
    def anonymize_user_data(self, user_id: UUID) -> dict:
        """Replace identifiable data with anonymized versions"""
        return {
            'anonymized_id': self.generate_anonymous_id(user_id),
            'anonymized_at': datetime.utcnow(),
            'original_data_hash': self.hash_original_data(user_id)
        }

    def schedule_data_deletion(self, user_id: UUID, days: int = 30):
        """Schedule automatic data deletion after specified days"""
        deletion_date = datetime.utcnow() + timedelta(days=days)
        # Schedule background task for data deletion
```

#### Consent Management
```python
class ConsentManager:
    def record_consent(self, user_id: UUID, consent_types: List[str]):
        """Record user consent with timestamp and IP anonymization"""
        consent_record = ConsentRecord(
            user_id=user_id,
            consent_types=consent_types,
            timestamp=datetime.utcnow(),
            ip_hash=self.hash_ip(request.client.host),  # Anonymized IP
            user_agent_hash=self.hash_user_agent(request.headers.get('user-agent'))
        )
        self.db.add(consent_record)
        self.db.commit()
```

### 3. Error Handling & Resilience

#### Global Exception Handler
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all exceptions with privacy-safe logging"""

    # Log error without exposing sensitive data
    logger.error(
        "unhandled_exception",
        extra={
            'exception_type': type(exc).__name__,
            'path': request.url.path,
            'method': request.method,
            'user_agent_hash': hash_user_agent(request.headers.get('user-agent', ''))
        }
    )

    # Return user-friendly error without technical details
    return JSONResponse(
        status_code=500,
        content={
            'error': 'An unexpected error occurred',
            'support_id': generate_support_id()  # For user support reference
        }
    )
```

#### Circuit Breaker Pattern
```python
class CircuitBreaker:
    """Prevent cascade failures for external service calls"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
```

## 🗄️ Shared Data Models

### 1. Base Models

#### Audit Trail Model
```python
class AuditLog(GDPRBaseModel):
    __tablename__ = 'audit_logs'

    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(UUID, nullable=True)
    user_id_hash = Column(String(64), nullable=True)  # Anonymized user ID
    ip_address_hash = Column(String(64), nullable=True)  # Anonymized IP
    user_agent_hash = Column(String(64), nullable=True)  # Anonymized user agent
    details = Column(JSON, nullable=True)  # Non-PII details only

    # Automatic retention policy
    retention_until = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=365))
```

#### Configuration Model
```python
class SystemConfiguration(Base):
    __tablename__ = 'system_config'

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    is_sensitive = Column(Boolean, default=False)  # Encrypted storage flag
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), nullable=False)
```

### 2. Shared Enums and Constants

#### System-wide Enumerations
```python
class UserRole(str, Enum):
    ANONYMOUS = "anonymous"
    COMMENTER = "commenter"
    MODERATOR = "moderator"
    ADMIN = "admin"

class ConsentType(str, Enum):
    ESSENTIAL = "essential"      # Required for basic functionality
    FUNCTIONAL = "functional"    # Enhanced user experience
    ANALYTICS = "analytics"      # Usage analytics (privacy-compliant)
    MARKETING = "marketing"      # Newsletter and updates

class DataRetentionPeriod(int, Enum):
    LOGS = 365          # 1 year
    USER_DATA = 1095    # 3 years
    COMMENTS = 2190     # 6 years
    AUDIT_TRAIL = 2555  # 7 years (legal requirement)
```

## 🚀 Deployment Infrastructure

### 1. Container Configuration

#### Production Dockerfile Optimizations
```dockerfile
# Multi-stage build for minimal production image
FROM python:3.11-slim as builder
# ... build dependencies and wheel creation

FROM python:3.11-slim as production
# Security: non-root user
RUN groupadd -r gonogo && useradd -r -g gonogo gonogo
# ... minimal runtime with security hardening
USER gonogo
```

#### Docker Compose for Local Development
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./gonogo.db
      - GDPR_MODE=development
    volumes:
      - ./src:/app/src:ro  # Read-only code mounting
      - ./content:/app/content:ro  # Read-only content
```

### 2. Environment Management

#### Staging Environment
- **Purpose**: Pre-production testing with production-like data
- **Data**: Anonymized production data for realistic testing
- **Access**: Restricted to development team
- **Monitoring**: Full observability stack enabled

#### Production Environment
- **Region**: EU (Amsterdam/Frankfurt) for GDPR compliance
- **Scaling**: Auto-scaling based on CPU and memory thresholds
- **Monitoring**: Real-time alerts for performance and security
- **Backup**: Automated backups with point-in-time recovery

---

**Infrastructure Dependencies**: See `system-architecture.md` for overall system design context.

**Security Integration**: See `security-architecture.md` for detailed security infrastructure.