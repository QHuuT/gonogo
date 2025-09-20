# ADR-002: GDPR-First Architecture Approach

**Status**: Accepted
**Date**: 2025-09-20
**Deciders**: Development Team
**Supersedes**: None

## Context

The GoNoGo blog platform targets EU users and must comply with GDPR from day one. Rather than retrofitting privacy compliance, we need an architecture that treats privacy protection as a foundational requirement, not an afterthought.

## Decision

We will implement a **Privacy-by-Design** architecture with the following core principles:

### 1. Data Minimization at Architecture Level
- **User IDs**: Always use anonymized/hashed identifiers in logs and analytics
- **IP Addresses**: Store only anonymized IP ranges, never full addresses
- **Email Storage**: Store bcrypt hashes, not plaintext emails (except for essential communications)
- **Session Data**: Minimal session storage with automatic expiration

### 2. Consent-First Data Processing
- **No Data Collection**: Without explicit, informed consent
- **Granular Consent**: Separate consent for functional, analytics, and marketing
- **Consent Withdrawal**: One-click consent withdrawal with immediate effect
- **Audit Trail**: All consent changes logged with timestamps

### 3. Automatic Data Retention Policies
- **Comment Data**: 6 years retention, then automatic deletion
- **User Sessions**: 24 hours maximum, then auto-expire
- **Audit Logs**: 7 years (legal requirement), then deletion
- **Analytics**: 1 year retention, anonymized after 30 days

### 4. Right to Be Forgotten Implementation
- **Automatic Deletion**: Scheduled background tasks for data cleanup
- **Manual Deletion**: Admin interface for immediate data removal
- **Cascading Deletion**: Related data automatically removed
- **Verification**: Audit trail of all deletion operations

### 5. Data Subject Rights Automation
- **Data Export**: Automated generation of user data in portable format
- **Access Requests**: Self-service data access portal
- **Rectification**: User-controllable data correction interface
- **Processing Restriction**: Ability to pause data processing per user

## Technical Implementation

### Database Design
```sql
-- All user tables include GDPR compliance fields
CREATE TABLE users (
    id UUID PRIMARY KEY,
    anonymized_id VARCHAR(16) UNIQUE,  -- For logs/analytics
    email_hash VARCHAR(64),            -- bcrypt hash
    consent_timestamp TIMESTAMP,
    consent_types JSONB,               -- Granular consent tracking
    retention_until TIMESTAMP,        -- Automatic deletion date
    anonymized BOOLEAN DEFAULT FALSE
);
```

### Middleware Stack
```python
# Every request processed through privacy middleware
MIDDLEWARE = [
    'security.GDPRComplianceMiddleware',    # Check consent, log access
    'security.DataMinimizationMiddleware',  # Filter response data
    'security.AuditLoggingMiddleware',      # Privacy-safe audit logs
    'security.RetentionPolicyMiddleware'    # Apply retention rules
]
```

### Service Layer
```python
# All services implement privacy interfaces
class CommentService(GDPRCompliantService):
    def create_comment(self, data, user_consent):
        if not user_consent.functional:
            raise ConsentRequired("Functional consent required for comments")

        # Store with automatic retention policy
        comment = Comment(
            content=sanitize(data.content),
            author_hash=hash_email(data.email),
            retention_until=datetime.now() + timedelta(days=2190)  # 6 years
        )
```

## Consequences

### Positive
- **Legal Compliance**: Built-in GDPR compliance from day one
- **User Trust**: Transparent privacy practices build user confidence
- **Competitive Advantage**: Privacy-first approach differentiates from competitors
- **Future-Proof**: Architecture ready for additional privacy regulations

### Negative
- **Development Complexity**: Additional privacy logic in every feature
- **Performance Overhead**: Privacy checks and anonymization processing
- **Storage Overhead**: Additional fields and audit trails
- **Testing Complexity**: Privacy scenarios must be tested in every feature

### Risks and Mitigations
- **Risk**: Privacy middleware slows response times
  - **Mitigation**: Performance monitoring and optimization
- **Risk**: Complex consent management confuses users
  - **Mitigation**: Simple, clear consent interfaces with good UX
- **Risk**: Automatic deletion accidentally removes needed data
  - **Mitigation**: Comprehensive backup strategy and deletion verification

## Implementation Guidelines

### For All New Features
1. **Privacy Impact Assessment**: Every feature analyzed for GDPR implications
2. **Consent Requirements**: Determine what consent types are needed
3. **Data Minimization**: Collect only essential data, anonymize immediately
4. **Retention Policy**: Define and implement automatic cleanup
5. **User Rights**: Ensure data export/deletion works for new data types

### For Existing Features
1. **Audit Current Data**: Catalog all personal data currently stored
2. **Implement Retention**: Add retention_until to all personal data tables
3. **Add Consent Checks**: Retrofit consent validation into existing flows
4. **User Rights Support**: Ensure export/deletion covers legacy data

## Monitoring and Compliance

### Automated Monitoring
- **Consent Metrics**: Track consent rates and withdrawal patterns
- **Data Retention**: Monitor automatic deletion processes
- **Access Requests**: Track response times for data subject requests
- **Security Events**: Monitor for potential privacy breaches

### Regular Audits
- **Monthly**: Review data retention and deletion logs
- **Quarterly**: Privacy impact assessment of new features
- **Annually**: Full GDPR compliance audit with external review

## Related Decisions

- **ADR-001**: Technology stack supports GDPR implementation
- **Future ADR-003**: Specific data anonymization techniques
- **Future ADR-004**: International data transfer policies

---

**GitHub Issues**: All privacy-related issues should reference this ADR
**Compliance Documentation**: Links to docs/01-business/compliance/gdpr-requirements.md
**Last Updated**: 2025-09-20