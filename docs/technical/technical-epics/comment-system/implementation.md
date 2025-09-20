# Comment System Implementation

**Last Updated**: 2025-09-20

## 🏗️ Implementation Overview

This document details the technical implementation of the GDPR-compliant comment system, including code organization, key components, and GDPR compliance patterns.

## 📁 Code Organization

### Directory Structure
```
src/be/
├── api/
│   ├── comments.py          # Comment submission and display endpoints
│   ├── moderation.py        # Comment moderation endpoints
│   └── consent.py           # Consent management endpoints
├── services/
│   ├── comment_service.py   # Core comment business logic
│   ├── consent_service.py   # Consent collection and validation
│   ├── moderation_service.py # Comment moderation logic
│   └── gdpr_service.py      # GDPR rights implementation
├── models/
│   ├── comment_models.py    # Comment data models
│   ├── consent_models.py    # Consent and privacy models
│   └── moderation_models.py # Moderation workflow models
├── templates/
│   ├── comments/
│   │   ├── comment_form.html    # Comment submission form
│   │   ├── comment_thread.html  # Comment display
│   │   └── consent_notice.html  # GDPR consent interface
│   └── moderation/
│       ├── queue.html           # Moderation dashboard
│       └── review.html          # Individual comment review
└── middleware/
    ├── gdpr_middleware.py   # GDPR compliance middleware
    └── audit_middleware.py  # Audit logging middleware
```

## 🔧 Core Components

### 1. Comment API (`src/be/api/comments.py`)

```python
@app.post("/api/comments")
async def submit_comment(
    comment_data: CommentSubmission,
    consent_data: ConsentData,
    request: Request
):
    """
    Submit new comment with GDPR consent validation
    """
    # Validate consent before processing
    consent_result = await consent_service.validate_submission_consent(
        consent_data
    )

    if not consent_result.is_valid:
        raise HTTPException(400, "Invalid or missing consent")

    # Process comment submission
    comment = await comment_service.create_comment(
        content=comment_data.content,
        post_slug=comment_data.post_slug,
        consent_preferences=consent_result.preferences
    )

    # Queue for moderation
    await moderation_service.queue_for_review(comment.id)

    return {"comment_id": comment.id, "status": "pending_moderation"}

@app.get("/api/comments/{post_slug}")
async def get_comments(post_slug: str, include_pending: bool = False):
    """
    Retrieve approved comments for a post
    """
    comments = await comment_service.get_approved_comments(
        post_slug=post_slug,
        include_pending=include_pending
    )

    return {"comments": comments, "count": len(comments)}
```

**Responsibilities**:
- Handle comment submission with consent validation
- Serve approved comments for display
- Coordinate with moderation workflow
- Implement GDPR compliance checks

### 2. Comment Service (`src/be/services/comment_service.py`)

```python
class CommentService:
    """
    Core business logic for comment management
    """

    async def create_comment(
        self,
        content: str,
        post_slug: str,
        consent_preferences: ConsentPreferences
    ) -> Comment:
        """Create new comment with privacy controls"""

        # Create core comment record
        comment = Comment(
            content=self.sanitize_content(content),
            post_slug=post_slug,
            created_at=datetime.utcnow(),
            status=CommentStatus.PENDING_MODERATION
        )

        # Handle optional personal data based on consent
        if consent_preferences.allow_email_storage:
            personal_data = PersonalData(
                comment_id=comment.id,
                email=consent_preferences.email,
                retention_until=self.calculate_retention_date()
            )
            await self.store_personal_data(personal_data)

        # Log creation for audit trail
        await self.audit_service.log_comment_creation(comment)

        return await self.repository.save(comment)

    async def get_approved_comments(
        self,
        post_slug: str,
        include_pending: bool = False
    ) -> List[CommentDisplay]:
        """Retrieve comments for public display"""

        status_filter = [CommentStatus.APPROVED]
        if include_pending:
            status_filter.append(CommentStatus.PENDING_MODERATION)

        comments = await self.repository.get_by_post_and_status(
            post_slug, status_filter
        )

        # Transform to display format (privacy-safe)
        return [self.to_display_format(c) for c in comments]

    def sanitize_content(self, content: str) -> str:
        """Sanitize comment content for security"""
        # Remove potential XSS vectors
        # Limit content length
        # Basic profanity filtering
        pass
```

**Responsibilities**:
- Implement comment creation with privacy controls
- Handle content sanitization and validation
- Manage comment lifecycle and status
- Coordinate with consent and audit services

### 3. Consent Service (`src/be/services/consent_service.py`)

```python
class ConsentService:
    """
    GDPR consent collection and management
    """

    async def validate_submission_consent(
        self,
        consent_data: ConsentData
    ) -> ConsentValidationResult:
        """Validate consent meets GDPR requirements"""

        # Check required consents
        if not consent_data.agree_to_comment_storage:
            return ConsentValidationResult(
                is_valid=False,
                error="Comment storage consent required"
            )

        # Validate optional consents
        preferences = ConsentPreferences(
            allow_email_storage=consent_data.allow_email_notifications,
            allow_name_display=consent_data.allow_name_display,
            email=consent_data.email if consent_data.allow_email_notifications else None
        )

        # Store consent record for audit
        consent_record = ConsentRecord(
            timestamp=datetime.utcnow(),
            ip_hash=self.hash_ip(consent_data.user_ip),  # Hashed for privacy
            consent_version="1.0",
            preferences=preferences
        )

        await self.store_consent_record(consent_record)

        return ConsentValidationResult(
            is_valid=True,
            preferences=preferences,
            consent_id=consent_record.id
        )

    async def handle_consent_withdrawal(
        self,
        comment_id: str,
        consent_type: str
    ):
        """Handle user consent withdrawal"""

        if consent_type == "email_notifications":
            await self.remove_email_data(comment_id)
        elif consent_type == "name_display":
            await self.anonymize_display_name(comment_id)

        # Log withdrawal for compliance
        await self.audit_service.log_consent_withdrawal(
            comment_id, consent_type
        )
```

**Responsibilities**:
- Validate GDPR consent requirements
- Store consent records for audit compliance
- Handle consent withdrawal requests
- Manage consent preferences and updates

### 4. GDPR Service (`src/be/services/gdpr_service.py`)

```python
class GDPRService:
    """
    Implementation of GDPR data subject rights
    """

    async def handle_data_access_request(
        self,
        user_identifier: str
    ) -> DataExportPackage:
        """Right to Access - Export user's personal data"""

        # Find all comments by user
        comments = await self.find_user_comments(user_identifier)

        # Gather personal data
        personal_data = await self.gather_personal_data(user_identifier)

        # Create export package
        export_data = DataExportPackage(
            user_identifier=user_identifier,
            export_date=datetime.utcnow(),
            comments=[c.to_export_format() for c in comments],
            personal_data=personal_data.to_export_format(),
            consent_history=await self.get_consent_history(user_identifier)
        )

        # Log access request for audit
        await self.audit_service.log_data_access_request(
            user_identifier, export_data.file_size
        )

        return export_data

    async def handle_erasure_request(
        self,
        user_identifier: str,
        erasure_scope: ErasureScope
    ) -> ErasureResult:
        """Right to Erasure - Delete or anonymize user data"""

        if erasure_scope.include_comments:
            # Soft delete comments to preserve thread structure
            await self.soft_delete_user_comments(user_identifier)

        if erasure_scope.include_personal_data:
            # Hard delete personal data
            await self.delete_personal_data(user_identifier)

        # Remove consent records (keep audit trail)
        await self.anonymize_consent_records(user_identifier)

        # Create comprehensive audit log
        erasure_log = ErasureAuditLog(
            user_identifier=user_identifier,
            erasure_date=datetime.utcnow(),
            scope=erasure_scope,
            items_processed=await self.count_erasure_items(user_identifier)
        )

        await self.audit_service.log_erasure_request(erasure_log)

        return ErasureResult(
            success=True,
            items_erased=erasure_log.items_processed,
            completion_date=erasure_log.erasure_date
        )
```

**Responsibilities**:
- Implement GDPR data subject rights
- Handle data access and export requests
- Manage data erasure with audit compliance
- Coordinate with audit and consent services

### 5. Moderation Service (`src/be/services/moderation_service.py`)

```python
class ModerationService:
    """
    Comment moderation and approval workflow
    """

    async def queue_for_review(self, comment_id: str):
        """Add comment to moderation queue"""

        comment = await self.comment_service.get_by_id(comment_id)

        # Auto-moderation checks
        auto_result = await self.auto_moderate(comment)

        if auto_result.should_auto_approve:
            await self.approve_comment(comment_id, "auto-approved")
        elif auto_result.should_auto_reject:
            await self.reject_comment(comment_id, auto_result.rejection_reason)
        else:
            # Queue for human review
            moderation_item = ModerationQueueItem(
                comment_id=comment_id,
                priority=auto_result.priority,
                flags=auto_result.flags,
                queued_at=datetime.utcnow()
            )
            await self.queue_repository.add(moderation_item)

    async def approve_comment(
        self,
        comment_id: str,
        moderator_id: str
    ):
        """Approve comment for public display"""

        # Update comment status
        await self.comment_service.update_status(
            comment_id,
            CommentStatus.APPROVED
        )

        # Log moderation decision
        decision = ModerationDecision(
            comment_id=comment_id,
            moderator_id=moderator_id,
            decision=ModerationAction.APPROVE,
            timestamp=datetime.utcnow()
        )

        await self.log_moderation_decision(decision)

        # Send notification if consent given
        await self.notification_service.send_approval_notification(comment_id)
```

**Responsibilities**:
- Implement automated content moderation
- Manage human moderation workflow
- Track moderation decisions for audit
- Handle comment status lifecycle

## 🎨 Template Implementation

### Comment Form Template (`src/be/templates/comments/comment_form.html`)

```html
{% extends "base.html" %}

{% block content %}
<form id="comment-form" class="comment-submission">
    <div class="comment-content">
        <label for="comment-text">Your Comment</label>
        <textarea
            id="comment-text"
            name="content"
            required
            maxlength="2000"
            placeholder="Share your thoughts...">
        </textarea>
    </div>

    <!-- GDPR Consent Section -->
    <div class="consent-section">
        <h4>Privacy Preferences</h4>

        <!-- Required Consent -->
        <label class="consent-required">
            <input type="checkbox" name="agree_to_comment_storage" required>
            <span>I agree to store my comment for display on this blog post</span>
            <small class="required-notice">Required</small>
        </label>

        <!-- Optional Consents -->
        <label class="consent-optional">
            <input type="checkbox" name="allow_email_notifications">
            <span>Send me email notifications about replies to my comment</span>
            <small class="optional-notice">Optional</small>
        </label>

        <div class="email-input" style="display: none;">
            <input type="email" name="email" placeholder="your@email.com">
        </div>

        <label class="consent-optional">
            <input type="checkbox" name="allow_name_display">
            <span>Display my name with this comment</span>
            <input type="text" name="display_name" placeholder="Your name" style="display: none;">
        </label>
    </div>

    <!-- Privacy Notice -->
    <div class="privacy-notice">
        <p><strong>Your Privacy:</strong> We minimize data collection and respect your choices.
        You can withdraw consent at any time. <a href="/privacy">Learn more</a></p>
    </div>

    <button type="submit">Submit Comment</button>
</form>

<script>
// Dynamic consent form behavior
document.addEventListener('DOMContentLoaded', function() {
    const emailCheckbox = document.querySelector('input[name="allow_email_notifications"]');
    const emailInput = document.querySelector('.email-input');

    emailCheckbox.addEventListener('change', function() {
        emailInput.style.display = this.checked ? 'block' : 'none';
        emailInput.querySelector('input').required = this.checked;
    });

    // Similar logic for name display
    const nameCheckbox = document.querySelector('input[name="allow_name_display"]');
    const nameInput = nameCheckbox.parentElement.querySelector('input[type="text"]');

    nameCheckbox.addEventListener('change', function() {
        nameInput.style.display = this.checked ? 'inline' : 'none';
        nameInput.required = this.checked;
    });
});
</script>
{% endblock %}
```

## 🔄 Data Processing Pipeline

### Comment Submission Flow

1. **Frontend Validation**: JavaScript validates consent requirements
2. **API Submission**: POST to `/api/comments` with consent data
3. **Consent Validation**: Verify GDPR consent requirements
4. **Content Sanitization**: Clean and validate comment content
5. **Database Storage**: Store in separate tables based on consent
6. **Moderation Queue**: Auto-moderation and human review queue
7. **Approval Process**: Moderator review and decision
8. **Publication**: Approved comments displayed to users

### GDPR Rights Processing

1. **Request Validation**: Verify user identity for rights requests
2. **Data Discovery**: Find all user data across system
3. **Rights Execution**: Implement specific right (access, erasure, etc.)
4. **Audit Logging**: Record all rights activities
5. **Response Generation**: Provide confirmation to user

## 🧪 Testing Strategy

### Unit Tests
- Comment service functionality
- GDPR rights implementation
- Consent validation logic
- Moderation workflow

### Integration Tests
- End-to-end comment submission
- GDPR compliance workflows
- Template rendering with real data
- API security and validation

### Compliance Tests
- GDPR rights request handling
- Consent withdrawal processing
- Data minimization verification
- Audit trail completeness

---

**Related Documentation**:
- [Architecture Decisions](architecture.md)
- [Performance Optimization](performance.md)
- [API Design](api-design.md)