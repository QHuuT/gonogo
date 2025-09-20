# Security Architecture

**Last Updated**: 2025-09-20

## 🎯 Overview

The GoNoGo security architecture implements a comprehensive defense-in-depth strategy with GDPR compliance as a foundational requirement. Every component is designed with privacy-by-design principles and follows European data protection standards.

## 🛡️ Security Framework

### Defense-in-Depth Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 7: User Education & Awareness                       │
├─────────────────────────────────────────────────────────────┤
│  Layer 6: Application Security (FastAPI + Custom)          │
├─────────────────────────────────────────────────────────────┤
│  Layer 5: Data Security (Encryption + Anonymization)       │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Network Security (HTTPS + Security Headers)      │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Host Security (Container + OS Hardening)         │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Infrastructure Security (DigitalOcean + EU)      │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Physical Security (EU Data Centers)              │
└─────────────────────────────────────────────────────────────┘
```

### Security Principles

1. **Privacy by Design**: Data protection built into every component
2. **Zero Trust**: Verify every request, trust nothing by default
3. **Minimal Privilege**: Users and systems get only necessary permissions
4. **Data Minimization**: Collect only essential data, delete when not needed
5. **Transparency**: Clear privacy policies and data handling practices

## 🔐 Authentication & Authorization

### Authentication Strategy

#### Multi-Factor Authentication Support
```python
class AuthenticationService:
    def authenticate_user(self, credentials: UserCredentials) -> AuthResult:
        """
        Secure authentication with rate limiting and audit logging
        """
        # Rate limiting by IP (anonymized for logging)
        if self.rate_limiter.is_blocked(self.anonymize_ip(request.client.host)):
            raise RateLimitExceeded()

        # Verify credentials with secure password hashing
        user = self.verify_credentials(credentials)
        if not user:
            self.audit_logger.log_failed_login(
                ip_hash=self.anonymize_ip(request.client.host),
                attempt_time=datetime.utcnow()
            )
            raise AuthenticationFailed()

        # Generate secure session token
        session_token = self.create_session(user)
        self.audit_logger.log_successful_login(user.anonymized_id)

        return AuthResult(token=session_token, user=user)
```

#### Session Management
```python
class SecureSessionManager:
    def __init__(self):
        self.session_timeout = timedelta(hours=24)
        self.token_refresh_threshold = timedelta(hours=1)

    def create_session(self, user: User) -> str:
        """Create cryptographically secure session token"""
        session_data = {
            'user_id': user.anonymized_id,  # Never use real user ID
            'permissions': user.permissions,
            'issued_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + self.session_timeout,
            'ip_hash': self.hash_ip(request.client.host)  # Bind to anonymized IP
        }
        return jwt.encode(session_data, self.secret_key, algorithm='HS256')

    def validate_session(self, token: str) -> Optional[dict]:
        """Validate session with automatic refresh"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])

            # Check expiration
            if datetime.utcnow() > payload['expires_at']:
                raise SessionExpired()

            # Check IP binding (anonymized)
            if payload['ip_hash'] != self.hash_ip(request.client.host):
                raise SessionInvalid()

            return payload
        except jwt.InvalidTokenError:
            raise SessionInvalid()
```

### Authorization Framework

#### Role-Based Access Control (RBAC)
```python
class Permission(str, Enum):
    READ_POSTS = "posts:read"
    CREATE_COMMENTS = "comments:create"
    MODERATE_COMMENTS = "comments:moderate"
    MANAGE_USERS = "users:manage"
    ADMIN_SYSTEM = "system:admin"

class Role(str, Enum):
    ANONYMOUS = "anonymous"
    COMMENTER = "commenter"
    MODERATOR = "moderator"
    ADMIN = "admin"

ROLE_PERMISSIONS = {
    Role.ANONYMOUS: [Permission.READ_POSTS],
    Role.COMMENTER: [Permission.READ_POSTS, Permission.CREATE_COMMENTS],
    Role.MODERATOR: [Permission.READ_POSTS, Permission.CREATE_COMMENTS, Permission.MODERATE_COMMENTS],
    Role.ADMIN: [Permission.READ_POSTS, Permission.CREATE_COMMENTS, Permission.MODERATE_COMMENTS,
                 Permission.MANAGE_USERS, Permission.ADMIN_SYSTEM]
}
```

#### Authorization Decorators
```python
def require_permission(permission: Permission):
    """Decorator to enforce permission-based access control"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from current session
            current_user = get_current_user()
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")

            # Check permission
            if not has_permission(current_user.role, permission):
                self.audit_logger.log_unauthorized_access(
                    user_id=current_user.anonymized_id,
                    attempted_permission=permission,
                    endpoint=request.url.path
                )
                raise HTTPException(status_code=403, detail="Insufficient permissions")

            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

## 🔒 Data Protection & GDPR Compliance

### Data Classification

#### Data Categories with Protection Levels
```python
class DataClassification(str, Enum):
    PUBLIC = "public"              # Blog posts, public comments
    INTERNAL = "internal"          # System logs, analytics
    CONFIDENTIAL = "confidential"  # User emails, IP addresses
    RESTRICTED = "restricted"      # Admin credentials, system keys

class ProtectionLevel:
    PUBLIC = {
        'encryption_required': False,
        'access_logging': False,
        'retention_period': None  # Permanent
    }
    INTERNAL = {
        'encryption_required': True,
        'access_logging': True,
        'retention_period': timedelta(days=365)
    }
    CONFIDENTIAL = {
        'encryption_required': True,
        'access_logging': True,
        'anonymization_required': True,
        'retention_period': timedelta(days=1095)  # 3 years
    }
    RESTRICTED = {
        'encryption_required': True,
        'access_logging': True,
        'rotation_required': True,
        'retention_period': timedelta(days=90)
    }
```

### GDPR Implementation

#### Privacy Rights Automation
```python
class GDPRComplianceService:
    def handle_data_subject_request(self, request_type: str, user_id: UUID):
        """Handle GDPR data subject rights requests"""
        match request_type:
            case "access":
                return self.generate_data_export(user_id)
            case "rectification":
                return self.create_rectification_form(user_id)
            case "erasure":
                return self.schedule_data_deletion(user_id)
            case "portability":
                return self.export_portable_data(user_id)
            case "restriction":
                return self.restrict_data_processing(user_id)
            case "objection":
                return self.process_objection(user_id)

    def generate_data_export(self, user_id: UUID) -> dict:
        """Generate complete data export for user"""
        user_data = {
            'personal_data': self.get_personal_data(user_id),
            'comments': self.get_user_comments(user_id),
            'consent_records': self.get_consent_history(user_id),
            'access_logs': self.get_access_logs(user_id, days=30),  # Limited period
            'export_timestamp': datetime.utcnow().isoformat(),
            'export_format': 'JSON',
            'data_controller': 'GoNoGo Blog Platform'
        }
        return user_data
```

#### Consent Management System
```python
class ConsentManager:
    def __init__(self):
        self.consent_types = {
            'essential': {
                'required': True,
                'description': 'Essential for basic website functionality',
                'legal_basis': 'legitimate_interest'
            },
            'functional': {
                'required': False,
                'description': 'Enhanced user experience features',
                'legal_basis': 'consent'
            },
            'analytics': {
                'required': False,
                'description': 'Anonymous usage analytics',
                'legal_basis': 'consent'
            }
        }

    def record_consent(self, user_id: UUID, consents: dict):
        """Record user consent with full audit trail"""
        consent_record = ConsentRecord(
            user_id=user_id,
            consents=consents,
            timestamp=datetime.utcnow(),
            ip_hash=self.anonymize_ip(request.client.host),
            user_agent_hash=self.anonymize_user_agent(request.headers.get('user-agent')),
            privacy_policy_version='1.0',
            withdrawal_instructions='Available in user account settings'
        )
        self.db.add(consent_record)
        self.audit_consent_change(user_id, consents)
```

### Data Anonymization & Pseudonymization

#### Automatic Anonymization Pipeline
```python
class DataAnonymizer:
    def __init__(self):
        self.anonymization_key = self.load_anonymization_key()
        self.hash_algorithm = 'SHA-256'

    def anonymize_user_id(self, user_id: UUID) -> str:
        """Convert user ID to consistent anonymous identifier"""
        return hashlib.sha256(
            f"{user_id}{self.anonymization_key}".encode()
        ).hexdigest()[:16]  # 16-character anonymous ID

    def anonymize_ip_address(self, ip: str) -> str:
        """Anonymize IP address for logging purposes"""
        # IPv4: Zero out last octet, IPv6: Zero out last 64 bits
        if ':' in ip:  # IPv6
            parts = ip.split(':')
            return ':'.join(parts[:4] + ['0000'] * 4)
        else:  # IPv4
            parts = ip.split('.')
            return '.'.join(parts[:3] + ['0'])

    def schedule_anonymization(self, table: str, record_id: UUID, days: int = 30):
        """Schedule automatic anonymization of sensitive data"""
        anonymization_task = AnonymizationTask(
            table_name=table,
            record_id=record_id,
            scheduled_for=datetime.utcnow() + timedelta(days=days),
            anonymization_type='full'
        )
        self.db.add(anonymization_task)
```

## 🌐 Network Security

### HTTPS & TLS Configuration

#### Security Headers Implementation
```python
class SecurityHeadersMiddleware:
    def __init__(self):
        self.security_headers = {
            # HTTPS enforcement
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',

            # XSS protection
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',

            # Content Security Policy
            'Content-Security-Policy': self.build_csp_header(),

            # Privacy headers
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',

            # GDPR compliance
            'X-Privacy-Policy': '/privacy-policy',
            'X-Data-Controller': 'GoNoGo Blog Platform'
        }

    def build_csp_header(self) -> str:
        """Build Content Security Policy header"""
        policy_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",  # Minimal inline scripts
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "connect-src 'self'",
            "font-src 'self'",
            "object-src 'none'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        return '; '.join(policy_directives)
```

### Rate Limiting & DDoS Protection

#### Adaptive Rate Limiting
```python
class AdaptiveRateLimiter:
    def __init__(self):
        self.rate_limits = {
            'anonymous': {'requests': 100, 'window': 3600},      # 100/hour
            'authenticated': {'requests': 500, 'window': 3600},   # 500/hour
            'api_calls': {'requests': 1000, 'window': 3600},     # 1000/hour
            'login_attempts': {'requests': 5, 'window': 900}     # 5/15min
        }

    async def check_rate_limit(self, identifier: str, limit_type: str) -> bool:
        """Check if request is within rate limits"""
        limit_config = self.rate_limits[limit_type]
        key = f"rate_limit:{limit_type}:{self.hash_identifier(identifier)}"

        current_count = await self.redis.get(key) or 0
        if int(current_count) >= limit_config['requests']:
            # Log rate limiting event (anonymized)
            self.security_logger.warning(
                "rate_limit_exceeded",
                extra={
                    'limit_type': limit_type,
                    'identifier_hash': self.hash_identifier(identifier),
                    'current_count': current_count,
                    'limit': limit_config['requests']
                }
            )
            return False

        # Increment counter with expiration
        await self.redis.incr(key)
        await self.redis.expire(key, limit_config['window'])
        return True
```

## 🔍 Security Monitoring & Incident Response

### Security Event Detection

#### Automated Threat Detection
```python
class SecurityMonitor:
    def __init__(self):
        self.suspicious_patterns = [
            r'<script.*?>.*?</script>',     # XSS attempts
            r'union.*select.*from',         # SQL injection
            r'\.\.\/.*\.\.\/.*\.\./',      # Path traversal
            r'eval\s*\(',                  # Code injection
            r'document\.cookie',            # Cookie theft attempts
        ]

    def analyze_request(self, request: Request) -> SecurityThreat:
        """Analyze incoming request for security threats"""
        threats = []

        # Check for suspicious patterns in all inputs
        request_data = self.extract_request_data(request)
        for field, value in request_data.items():
            for pattern in self.suspicious_patterns:
                if re.search(pattern, str(value), re.IGNORECASE):
                    threats.append({
                        'type': 'suspicious_pattern',
                        'field': field,
                        'pattern': pattern,
                        'severity': 'high'
                    })

        # Check request frequency for potential DDoS
        if self.check_request_frequency(request.client.host):
            threats.append({
                'type': 'high_frequency_requests',
                'severity': 'medium'
            })

        return SecurityThreat(
            request_id=generate_request_id(),
            threats=threats,
            ip_hash=self.anonymize_ip(request.client.host),
            timestamp=datetime.utcnow()
        )
```

#### Incident Response Automation
```python
class IncidentResponseSystem:
    def handle_security_incident(self, incident: SecurityIncident):
        """Automated incident response workflow"""
        match incident.severity:
            case 'critical':
                self.immediate_response(incident)
            case 'high':
                self.escalated_response(incident)
            case 'medium':
                self.standard_response(incident)
            case 'low':
                self.log_and_monitor(incident)

    def immediate_response(self, incident: SecurityIncident):
        """Critical incident response - immediate action required"""
        # Block suspicious IP (anonymized for logging)
        self.firewall.block_ip(incident.source_ip)

        # Alert security team
        self.alert_system.send_critical_alert(
            title=f"Critical Security Incident: {incident.type}",
            details=incident.details,
            source_ip_hash=self.anonymize_ip(incident.source_ip)
        )

        # Create incident record
        self.create_incident_record(incident)

        # Initiate backup procedures if data integrity threatened
        if incident.threatens_data_integrity:
            self.backup_service.create_emergency_backup()
```

### Audit Logging

#### Comprehensive Audit Trail
```python
class SecurityAuditLogger:
    def __init__(self):
        self.audit_events = [
            'user_login', 'user_logout', 'password_change',
            'permission_change', 'data_access', 'data_modification',
            'admin_action', 'configuration_change', 'security_incident',
            'gdpr_request', 'consent_change', 'data_export'
        ]

    def log_security_event(self, event_type: str, **kwargs):
        """Log security event with full context (privacy-safe)"""
        audit_record = SecurityAuditLog(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            user_id_hash=kwargs.get('user_id_hash'),
            ip_hash=self.anonymize_ip(kwargs.get('ip_address', '')),
            user_agent_hash=self.anonymize_user_agent(kwargs.get('user_agent', '')),
            resource_type=kwargs.get('resource_type'),
            resource_id=kwargs.get('resource_id'),
            action=kwargs.get('action'),
            result=kwargs.get('result', 'success'),
            details=self.sanitize_details(kwargs.get('details', {})),
            severity=kwargs.get('severity', 'info'),
            retention_until=datetime.utcnow() + timedelta(days=2555)  # 7 years
        )

        self.db.add(audit_record)
        self.forward_to_siem(audit_record)  # Security Information and Event Management
```

## 🔧 Security Testing & Validation

### Automated Security Testing

#### Security Test Suite
```python
class SecurityTestSuite:
    def test_authentication_security(self):
        """Test authentication mechanisms for common vulnerabilities"""
        test_cases = [
            self.test_password_strength_requirements,
            self.test_session_timeout,
            self.test_concurrent_session_limits,
            self.test_brute_force_protection,
            self.test_credential_enumeration
        ]
        return self.run_test_suite(test_cases)

    def test_input_validation(self):
        """Test all input validation and sanitization"""
        malicious_inputs = [
            "<script>alert('xss')</script>",           # XSS
            "'; DROP TABLE users; --",                 # SQL injection
            "../../../etc/passwd",                     # Path traversal
            "eval('malicious_code')",                   # Code injection
            "\x00\x01\x02\x03"                        # Binary injection
        ]

        for malicious_input in malicious_inputs:
            response = self.client.post("/api/comments", json={
                "content": malicious_input,
                "author_name": "Test User",
                "author_email": "test@example.com",
                "gdpr_consent": True
            })
            assert response.status_code in [400, 422], f"Failed to block: {malicious_input}"

    def test_gdpr_compliance(self):
        """Test GDPR compliance mechanisms"""
        test_cases = [
            self.test_consent_recording,
            self.test_data_export,
            self.test_data_deletion,
            self.test_data_anonymization,
            self.test_retention_policies
        ]
        return self.run_test_suite(test_cases)
```

### Penetration Testing Integration

#### Automated Vulnerability Scanning
```python
class VulnerabilityScanner:
    def __init__(self):
        self.scan_modules = [
            'owasp_top_10',
            'gdpr_compliance',
            'input_validation',
            'authentication',
            'authorization',
            'session_management',
            'cryptography',
            'error_handling'
        ]

    def run_security_scan(self) -> SecurityScanReport:
        """Run comprehensive security scan"""
        results = {}
        for module in self.scan_modules:
            scanner = self.get_scanner(module)
            results[module] = scanner.scan()

        return SecurityScanReport(
            scan_id=generate_scan_id(),
            timestamp=datetime.utcnow(),
            results=results,
            overall_score=self.calculate_security_score(results),
            recommendations=self.generate_recommendations(results)
        )
```

---

**Security Integration**: This security architecture integrates with all other system components through the shared infrastructure layer.

**Compliance Verification**: Regular security audits and GDPR compliance checks ensure ongoing protection standards.