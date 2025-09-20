# Comment System Architecture

**Last Updated**: 2025-09-20

## 🏗️ Architecture Decisions

### ADR-001: Privacy-by-Design Comment Architecture

**Status**: Approved
**Date**: 2025-09-20

#### Context
Need to implement comment system that satisfies GDPR requirements while maintaining user experience.

#### Decision
Use privacy-by-design architecture with minimal data collection and explicit consent management.

#### Rationale
- **GDPR Compliance**: Built-in privacy protection from system design
- **Data Minimization**: Collect only essential data for functionality
- **User Control**: Explicit consent for optional features
- **Legal Safety**: Reduces compliance risk through design

#### Consequences
- Enhanced privacy protection
- Reduced legal risk
- Increased development complexity
- Better user trust

### ADR-002: Database Design for GDPR Compliance

**Status**: Approved
**Date**: 2025-09-20

#### Context
Need database schema that supports GDPR rights (access, rectification, erasure) efficiently.

#### Decision
Use separate tables for core comment data and optional personal data with soft deletion.

#### Rationale
- **Right to Erasure**: Soft deletion preserves comment threads
- **Data Minimization**: Separate optional data from required data
- **Right to Access**: Efficient data export capabilities
- **Audit Requirements**: Maintain compliance trails

#### Consequences
- GDPR rights easily implementable
- Complex database queries for soft-deleted content
- Enhanced auditability
- Increased storage requirements for audit logs

### ADR-003: Consent Management Strategy

**Status**: Approved
**Date**: 2025-09-20

#### Context
Need explicit consent collection for optional data while maintaining comment functionality.

#### Decision
Use granular consent system with separate permissions for different data types.

#### Rationale
- **GDPR Article 7**: Requires specific, informed, freely given consent
- **User Control**: Granular permissions enhance user agency
- **Compliance**: Clear consent records for audit purposes
- **Flexibility**: Users can change consent preferences

#### Consequences
- Complex consent interface design
- Multiple consent tracking requirements
- Enhanced user control
- Simplified compliance verification

## 🏛️ System Architecture

### Component Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Comment API   │    │  Consent Engine  │    │ Moderation API  │
│                 │    │                  │    │                 │
│ - Submit        │    │ - Collect        │    │ - Review        │
│ - Display       │    │ - Validate       │    │ - Approve       │
│ - Thread        │    │ - Track          │    │ - Reject        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────────────────────────────┐
         │           Database Layer                │
         │                                         │
         │ ┌─────────────┐ ┌─────────────────────┐ │
         │ │  Comments   │ │    Personal Data    │ │
         │ │   Table     │ │      Table          │ │
         │ └─────────────┘ └─────────────────────┘ │
         │ ┌─────────────┐ ┌─────────────────────┐ │
         │ │   Consent   │ │    Audit Logs       │ │
         │ │   Records   │ │      Table          │ │
         │ └─────────────┘ └─────────────────────┘ │
         └─────────────────────────────────────────┘
```

### Data Flow Architecture
```
User Comment Submission:
1. User → Comment Form (with consent checkboxes)
2. Frontend → Consent Validation
3. Frontend → Comment API (with consent flags)
4. Comment API → Data Validation
5. Comment API → Database (separate tables)
6. Comment API → Moderation Queue
7. Moderator → Approval/Rejection
8. System → Comment Display
```

## 🔐 Security Architecture

### Data Protection Strategy

#### Encryption at Rest
```python
# Core comment data encryption
class EncryptedCommentField:
    def encrypt_content(self, content: str) -> str:
        # AES-256 encryption for comment content
        pass

    def decrypt_content(self, encrypted: str) -> str:
        # Decryption with access logging
        pass
```

#### Data Access Controls
```python
class CommentAccessControl:
    def can_access_comment(self, user_id: str, comment_id: str) -> bool:
        # Role-based access control for comment data
        pass

    def log_data_access(self, user_id: str, action: str, data_type: str):
        # Audit logging for GDPR compliance
        pass
```

### Privacy Architecture

#### Data Minimization
- **Core Data**: Only comment content, timestamp, post reference
- **Optional Data**: Email (with explicit consent), name display preference
- **Prohibited Data**: IP addresses, tracking cookies, behavioral analytics

#### Consent Architecture
```python
class ConsentManager:
    consent_types = {
        "comment_storage": True,      # Required for functionality
        "email_notifications": False, # Optional with consent
        "name_display": False,        # Optional with consent
    }

    def validate_consent(self, consent_data: dict) -> bool:
        # Validate consent meets GDPR requirements
        pass
```

## 🧠 Moderation Architecture

### Workflow Design
```
Comment Submission → Auto-Moderation → Human Review → Publication
     │                    │                │              │
     ├─ Spam Detection    ├─ Content Rules ├─ Approve     ├─ Display
     ├─ Language Filter   ├─ Link Analysis ├─ Reject      ├─ Index
     └─ GDPR Validation   └─ Risk Scoring  └─ Request     └─ Archive
                                              Changes
```

### Moderation Rules Engine
```python
class ModerationEngine:
    def auto_moderate(self, comment: Comment) -> ModerationResult:
        # Automated content screening
        pass

    def queue_for_human_review(self, comment: Comment, reason: str):
        # Human moderation workflow
        pass

    def apply_moderation_decision(self, comment_id: str, decision: str):
        # Execute moderation decision with audit trail
        pass
```

## 📊 Performance Architecture

### Caching Strategy
- **Comment Threads**: Cache rendered comment trees for 5 minutes
- **Moderation Queue**: Real-time updates without caching
- **Consent Records**: Cache active consent for session duration
- **User Preferences**: Cache display preferences for 1 hour

### Database Optimization
- **Indexing**: Optimized indexes for comment threading and time-based queries
- **Partitioning**: Partition audit logs by date for performance
- **Archiving**: Archive old comments with preserved references

---

**Related Documentation**:
- [Implementation Details](implementation.md)
- [Performance Optimization](performance.md)
- [API Design](api-design.md)