# System Architecture

**Last Updated**: 2025-09-20

## 🎯 Overview

The GoNoGo system architecture follows a modular, privacy-first design built on FastAPI with GDPR compliance as a foundational requirement. The architecture emphasizes simplicity, security, and maintainability while providing a scalable foundation for a European-hosted blog platform.

## 🏗️ System Components

### Core Application Layer
```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│  API Routes  │  Templates  │  Static Assets  │  Middleware  │
├─────────────────────────────────────────────────────────────┤
│              Business Logic Services                        │
├─────────────────────────────────────────────────────────────┤
│                 SQLAlchemy ORM                              │
└─────────────────────────────────────────────────────────────┘
```

### Data Layer
```
┌─────────────────────────────────────────────────────────────┐
│  Development: SQLite  │  Production: PostgreSQL (EU)        │
├─────────────────────────────────────────────────────────────┤
│              File Storage: DigitalOcean Spaces              │
├─────────────────────────────────────────────────────────────┤
│            Content: Markdown Files (Git-tracked)            │
└─────────────────────────────────────────────────────────────┘
```

### Infrastructure Layer
```
┌─────────────────────────────────────────────────────────────┐
│            DigitalOcean App Platform (EU Region)            │
├─────────────────────────────────────────────────────────────┤
│    Load Balancer  │  Auto-scaling  │  SSL Termination       │
├─────────────────────────────────────────────────────────────┤
│              GitHub Actions CI/CD Pipeline                  │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Request Flow Architecture

### 1. HTTP Request Processing
```
Internet → DigitalOcean Load Balancer → FastAPI App → Response
    ↓
Security Headers Applied
    ↓
GDPR Compliance Checks
    ↓
Authentication/Authorization
    ↓
Business Logic Processing
    ↓
Database Operations (if needed)
    ↓
Template Rendering
    ↓
Response with Privacy Headers
```

### 2. Content Management Flow
```
Developer → GitHub Repository → GitHub Actions → DigitalOcean Deployment
    ↓
Markdown Content Updated
    ↓
Static Content Regeneration
    ↓
Database Migration (if schema changes)
    ↓
Application Restart
    ↓
Content Available to Users
```

## 🗄️ Data Architecture

### Database Schema Design
```sql
-- Core entities with GDPR compliance built-in
Users (anonymized_id, consent_timestamp, retention_until)
    ↓
Posts (markdown_path, metadata, gdpr_reviewed)
    ↓
Comments (content_hash, user_consent, moderation_status)
    ↓
Audit_Logs (action, timestamp, anonymized_user, retention_policy)
```

### Content Storage Strategy
- **Blog Posts**: Markdown files in Git repository
- **User Data**: PostgreSQL with encryption at rest
- **Static Assets**: DigitalOcean Spaces CDN
- **Logs**: Structured logging with privacy filters

## 🛡️ Security Architecture Integration

### Defense in Depth
1. **Infrastructure Level**: DigitalOcean security + EU data residency
2. **Network Level**: HTTPS only, security headers, rate limiting
3. **Application Level**: Input validation, SQL injection prevention
4. **Data Level**: Encryption at rest, anonymization, retention policies

### GDPR Compliance Architecture
```
Data Collection → Consent Management → Processing → Retention → Erasure
       ↓               ↓                ↓           ↓          ↓
   Minimal Data    Explicit Consent   Lawful Basis  Auto-Delete  Right to Forget
```

## 📊 Performance Architecture

### Optimization Strategies
- **Database**: Connection pooling, query optimization, indexes
- **Caching**: Browser caching headers, CDN for static assets
- **Templates**: Jinja2 template compilation and caching
- **Assets**: Minification, compression, lazy loading

### Monitoring Architecture
```
Application Metrics → DigitalOcean Monitoring → Alerts
       ↓
Performance Logs → Structured Analysis → Optimization
       ↓
User Experience → Analytics (Privacy-Compliant) → Insights
```

## 🔌 Integration Points

### External Services
- **GitHub**: Source control, issue tracking, CI/CD
- **DigitalOcean**: Hosting, database, object storage
- **Email Service**: Transactional emails (GDPR-compliant provider)

### Internal Service Communication
- **Synchronous**: Direct function calls within FastAPI
- **Asynchronous**: Background tasks for heavy operations
- **Data Flow**: SQLAlchemy ORM for database operations

## 🚀 Deployment Architecture

### Environment Strategy
```
Development (Local)
    ↓
Feature Branch → PR → Code Review
    ↓
Staging Environment (DigitalOcean)
    ↓
Production Deployment (Manual Approval)
    ↓
Production Environment (EU Region)
```

### Container Strategy
- **Development**: Direct Python execution with hot reload
- **Production**: Docker container with optimized layers
- **Database**: Managed PostgreSQL service
- **Scaling**: Horizontal scaling via DigitalOcean App Platform

## 📈 Scalability Considerations

### Current Architecture Supports
- **Traffic**: Up to 30 concurrent users
- **Content**: Unlimited blog posts via Git storage
- **Comments**: Database-limited, optimized for performance
- **Geographic**: EU-focused with CDN distribution

### Future Scaling Options
- **Database**: Read replicas, connection pooling optimization
- **Application**: Multi-instance deployment
- **Content**: Advanced CDN strategies
- **Search**: Elasticsearch integration for large content volumes

## 🔧 Development Architecture

### Local Development
```
Python Virtual Environment
    ↓
FastAPI with Auto-reload
    ↓
SQLite Database
    ↓
Local File Storage
    ↓
Browser Testing
```

### Testing Architecture
```
Unit Tests (70%) → Integration Tests (20%) → E2E Tests (10%)
       ↓                    ↓                      ↓
   Fast Feedback      Service Integration    User Journey
```

## 📝 Configuration Management

### Environment Configuration
- **Development**: `.env` files (not committed)
- **Production**: DigitalOcean App Platform environment variables
- **Secrets**: Secure environment variable injection
- **Feature Flags**: Simple configuration-based toggles

### Database Migrations
- **Tool**: Alembic for SQLAlchemy
- **Strategy**: Forward-only migrations
- **Rollback**: Database backup before major changes
- **Testing**: Migration testing in staging environment

---

**Architecture Decisions Log**: See `docs/02-technical/technical-epics/` for detailed technical decisions and rationale.

**Review Schedule**: Quarterly architecture review with team leads.