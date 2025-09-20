# GDPR Requirements

**Last Updated**: 2025-09-20

## 🎯 Overview

This document outlines the specific GDPR requirements that GoNoGo must meet as a blog platform targeting EU users. These requirements drive technical implementation decisions and provide compliance validation criteria.

## 📋 Core GDPR Obligations

### 1. Lawful Basis for Processing
- **Essential Functions**: Legitimate interest for basic blog functionality
- **Comments**: Consent required for user-generated content
- **Analytics**: Consent required for usage tracking
- **Marketing**: Explicit opt-in consent for newsletters

### 2. Data Subject Rights
#### Right of Access (Article 15)
- Users can request all personal data we hold
- Response required within 1 month
- Data export in machine-readable format

#### Right to Rectification (Article 16)
- Users can correct inaccurate personal data
- Self-service correction interface preferred
- Updates propagated to all systems

#### Right to Erasure (Article 17)
- "Right to be forgotten" implementation
- Automatic deletion upon request
- Cascading deletion of related data
- Backup purging procedures

#### Right to Data Portability (Article 20)
- Export personal data in structured format
- JSON export with all user-related data
- Include comments, preferences, consent history

### 3. Data Protection Principles

#### Data Minimization (Article 5)
- Collect only necessary personal data
- No "nice to have" data collection
- Regular data audits and cleanup

#### Purpose Limitation
- Use data only for stated purposes
- Clear purpose for each data field
- No repurposing without new consent

#### Storage Limitation
- **Comments**: 6 years maximum retention
- **Session Data**: 24 hours maximum
- **Audit Logs**: 7 years (legal requirement)
- **Marketing Data**: Until consent withdrawn

#### Accuracy
- Users can update their information
- Regular data validation processes
- Automated correction where possible

## 🛡️ Privacy by Design Requirements

### 1. Default Privacy Settings
- Minimal data collection by default
- Opt-in for non-essential features
- Privacy-friendly configuration out of the box

### 2. Consent Management
#### Consent Collection
- Clear, specific, informed consent
- Granular consent options (functional, analytics, marketing)
- Easy consent withdrawal
- Age verification for users under 16

#### Consent Records
- Timestamp of consent
- Method of consent collection
- IP address (anonymized) for verification
- Consent withdrawal history

### 3. Data Security Measures
- Encryption at rest and in transit
- Access controls and authentication
- Regular security assessments
- Incident response procedures

## 📊 Technical Implementation Requirements

### 1. Database Design
```sql
-- All personal data tables must include:
consent_timestamp TIMESTAMP,
consent_types JSONB,
retention_until TIMESTAMP,
anonymized BOOLEAN DEFAULT FALSE
```

### 2. API Endpoints Required
- `GET /api/user/data-export` - Data portability
- `POST /api/user/data-correction` - Rectification
- `DELETE /api/user/data-deletion` - Erasure
- `POST /api/consent/withdraw` - Consent management

### 3. Automated Processes
- Daily retention policy enforcement
- Weekly consent status checks
- Monthly data accuracy validation
- Quarterly security assessments

## 🌍 EU Data Residency

### Hosting Requirements
- **Primary**: EU-based hosting (DigitalOcean Amsterdam/Frankfurt)
- **Backups**: EU-only backup storage
- **CDN**: EU edge nodes preferred
- **Third Parties**: GDPR-compliant processors only

### Data Transfer Restrictions
- No data transfers outside EU without adequacy decision
- Standard Contractual Clauses for necessary transfers
- User notification for any cross-border processing

## 📝 Documentation Requirements

### Privacy Policy
- Clear, understandable language
- Specific purposes for data processing
- Retention periods clearly stated
- Contact information for data protection queries

### Records of Processing Activities (Article 30)
- Purposes of processing
- Categories of data subjects
- Types of personal data
- Data retention periods
- Technical and organizational security measures

### Data Protection Impact Assessment (DPIA)
- Required for high-risk processing
- Regular review and updates
- Consultation with supervisory authority if needed

## 🚨 Compliance Monitoring

### Automated Checks
- Daily consent validation
- Weekly data retention compliance
- Monthly security log review
- Quarterly compliance assessment

### Manual Reviews
- **Monthly**: Privacy policy accuracy
- **Quarterly**: Data processing activities
- **Annually**: Full GDPR compliance audit

### Incident Response
- Data breach notification within 72 hours
- User notification if high risk to rights
- Incident documentation and analysis
- Process improvement implementation

## 📞 Contact and Governance

### Data Protection Officer (DPO)
- **Required**: If systematic monitoring of EU residents
- **Responsibilities**: GDPR compliance oversight
- **Contact**: Accessible to users and supervisory authorities

### Supervisory Authority
- **Primary**: Based on main establishment location
- **Cooperation**: With other EU supervisory authorities
- **Reporting**: Data breaches and DPIA consultations

---

**Related ADRs**: ADR-002 (GDPR-First Architecture)
**Technical Implementation**: See docs/02-technical/cross-cutting-architecture/security-architecture.md
**GitHub Integration**: GDPR compliance requirements referenced in relevant issues