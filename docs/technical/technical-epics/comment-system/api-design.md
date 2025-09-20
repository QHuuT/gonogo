# Comment System API Design

**Last Updated**: 2025-09-20

## 🎯 API Overview

The comment system API provides GDPR-compliant endpoints for comment submission, display, moderation, and data subject rights. The design prioritizes privacy protection, performance, and audit compliance.

## 🌐 API Endpoints

### Comment Management

#### `POST /api/comments`
**Purpose**: Submit new comment with GDPR consent
**Authentication**: None (anonymous commenting supported)

```python
@app.post("/api/comments", response_model=CommentSubmissionResponse)
async def submit_comment(
    comment_data: CommentSubmission,
    request: Request
):
    """
    Submit comment with privacy consent validation
    """
    # Validate GDPR consent
    consent_result = await consent_service.validate_consent(
        comment_data.consent_preferences
    )

    if not consent_result.is_valid:
        raise HTTPException(400, detail=consent_result.error_message)

    # Create comment with privacy controls
    comment = await comment_service.create_comment(
        content=comment_data.content,
        post_slug=comment_data.post_slug,
        consent_preferences=consent_result.preferences,
        client_ip=request.client.host
    )

    return CommentSubmissionResponse(
        comment_id=comment.id,
        status="pending_moderation",
        estimated_review_time="24 hours"
    )
```

#### `GET /api/comments/{post_slug}`
**Purpose**: Retrieve approved comments for a blog post
**Response**: JSON with comment thread data

```python
@app.get("/api/comments/{post_slug}", response_model=CommentThreadResponse)
async def get_comments(
    post_slug: str,
    include_metadata: bool = False,
    sort_order: CommentSortOrder = CommentSortOrder.CHRONOLOGICAL
):
    """
    Retrieve public comment thread for blog post
    """
    comments = await comment_service.get_approved_comments(
        post_slug=post_slug,
        sort_order=sort_order
    )

    response_data = CommentThreadResponse(
        post_slug=post_slug,
        comments=[c.to_public_display() for c in comments],
        total_count=len(comments),
        last_updated=max(c.created_at for c in comments) if comments else None
    )

    if include_metadata:
        response_data.metadata = await self._generate_thread_metadata(comments)

    return response_data
```

### Moderation Management

#### `GET /api/admin/moderation/queue`
**Purpose**: Retrieve pending comments for moderation
**Authentication**: Admin required

```python
@app.get("/api/admin/moderation/queue", response_model=ModerationQueueResponse)
async def get_moderation_queue(
    current_admin: Admin = Depends(get_current_admin),
    page: int = 1,
    per_page: int = 20,
    filter_by: Optional[ModerationFilter] = None
):
    """
    Retrieve moderation queue with filtering and pagination
    """
    queue_items = await moderation_service.get_queue_items(
        page=page,
        per_page=per_page,
        filter_criteria=filter_by
    )

    return ModerationQueueResponse(
        items=[item.to_review_format() for item in queue_items],
        pagination=PaginationInfo(
            current_page=page,
            total_pages=await moderation_service.get_total_pages(per_page),
            total_items=await moderation_service.get_queue_size()
        )
    )
```

#### `POST /api/admin/moderation/{comment_id}/approve`
**Purpose**: Approve comment for public display
**Authentication**: Admin required

```python
@app.post("/api/admin/moderation/{comment_id}/approve")
async def approve_comment(
    comment_id: str,
    moderation_data: ModerationDecision,
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Approve comment with optional modifications
    """
    result = await moderation_service.approve_comment(
        comment_id=comment_id,
        moderator_id=current_admin.id,
        decision_notes=moderation_data.notes,
        content_modifications=moderation_data.modifications
    )

    # Send notification if user consented
    await notification_service.send_approval_notification(comment_id)

    return {"status": "approved", "comment_id": comment_id}
```

### GDPR Compliance Endpoints

#### `POST /api/gdpr/data-access`
**Purpose**: Handle GDPR Article 15 (Right to Access) requests
**Authentication**: Email verification required

```python
@app.post("/api/gdpr/data-access", response_model=DataAccessResponse)
async def request_data_access(
    request_data: DataAccessRequest,
    background_tasks: BackgroundTasks
):
    """
    Process GDPR data access request
    """
    # Validate user identity
    verification_result = await identity_service.verify_user_identity(
        request_data.email,
        request_data.verification_method
    )

    if not verification_result.is_verified:
        raise HTTPException(403, "Identity verification required")

    # Queue data export job
    job_id = await gdpr_service.queue_data_export(
        user_identifier=request_data.email,
        requester_ip=request.client.host
    )

    # Process export in background
    background_tasks.add_task(
        gdpr_service.process_data_export,
        job_id
    )

    return DataAccessResponse(
        request_id=job_id,
        status="processing",
        estimated_completion="72 hours",
        contact_email="privacy@example.com"
    )
```

#### `POST /api/gdpr/data-erasure`
**Purpose**: Handle GDPR Article 17 (Right to Erasure) requests
**Authentication**: Email verification required

```python
@app.post("/api/gdpr/data-erasure", response_model=DataErasureResponse)
async def request_data_erasure(
    erasure_request: DataErasureRequest,
    background_tasks: BackgroundTasks
):
    """
    Process GDPR right to erasure request
    """
    # Validate identity and consent withdrawal
    verification_result = await identity_service.verify_erasure_request(
        erasure_request.email,
        erasure_request.verification_code
    )

    if not verification_result.is_authorized:
        raise HTTPException(403, "Unauthorized erasure request")

    # Queue erasure job
    job_id = await gdpr_service.queue_data_erasure(
        user_identifier=erasure_request.email,
        erasure_scope=erasure_request.scope
    )

    background_tasks.add_task(
        gdpr_service.process_data_erasure,
        job_id
    )

    return DataErasureResponse(
        request_id=job_id,
        status="processing",
        items_to_process=await gdpr_service.count_user_data(erasure_request.email),
        completion_deadline="30 days"
    )
```

## 📊 Data Models

### Comment Submission Models

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional
from enum import Enum

class ConsentPreferences(BaseModel):
    """GDPR consent preferences for comment submission"""
    agree_to_comment_storage: bool = Field(..., description="Required consent for comment storage")
    allow_email_notifications: bool = Field(False, description="Optional: Email notifications about replies")
    allow_name_display: bool = Field(False, description="Optional: Display name with comment")
    email: Optional[str] = Field(None, description="Email for notifications (if consented)")
    display_name: Optional[str] = Field(None, description="Name to display (if consented)")

    @validator('email')
    def validate_email_with_consent(cls, v, values):
        if values.get('allow_email_notifications') and not v:
            raise ValueError('Email required when notifications are enabled')
        return v

    @validator('display_name')
    def validate_name_with_consent(cls, v, values):
        if values.get('allow_name_display') and not v:
            raise ValueError('Display name required when name display is enabled')
        return v

class CommentSubmission(BaseModel):
    """Comment submission data with privacy controls"""
    content: str = Field(..., min_length=1, max_length=2000, description="Comment content")
    post_slug: str = Field(..., description="Blog post identifier")
    parent_comment_id: Optional[str] = Field(None, description="Parent comment for threading")
    consent_preferences: ConsentPreferences = Field(..., description="GDPR consent data")

    @validator('content')
    def validate_content(cls, v):
        # Basic content validation
        if not v.strip():
            raise ValueError('Comment content cannot be empty')
        return v.strip()

class CommentSubmissionResponse(BaseModel):
    """Response after comment submission"""
    comment_id: str
    status: str = Field(..., description="Current comment status")
    estimated_review_time: str = Field(..., description="Expected moderation time")
    message: str = Field(default="Thank you for your comment. It will be reviewed before publication.")
```

### Comment Display Models

```python
class CommentDisplay(BaseModel):
    """Public comment display format"""
    id: str
    content: str
    created_at: datetime
    post_slug: str
    display_name: Optional[str] = Field(None, description="Display name if consented")
    reply_count: int = Field(0, description="Number of replies")
    replies: List['CommentDisplay'] = Field(default_factory=list)

    class Config:
        # Allow self-referencing for nested replies
        schema_extra = {
            "example": {
                "id": "comment_123",
                "content": "This is a great article!",
                "created_at": "2025-01-01T10:00:00Z",
                "post_slug": "example-blog-post",
                "display_name": "Anonymous",
                "reply_count": 2,
                "replies": []
            }
        }

class CommentThreadResponse(BaseModel):
    """Complete comment thread for a blog post"""
    post_slug: str
    comments: List[CommentDisplay]
    total_count: int
    last_updated: Optional[datetime]
    metadata: Optional[dict] = Field(None, description="Additional thread metadata")

class CommentSortOrder(str, Enum):
    CHRONOLOGICAL = "chronological"
    REVERSE_CHRONOLOGICAL = "reverse_chronological"
    MOST_REPLIES = "most_replies"
```

### Moderation Models

```python
class ModerationQueueItem(BaseModel):
    """Comment awaiting moderation"""
    comment_id: str
    content: str
    post_slug: str
    submitted_at: datetime
    priority: int = Field(..., description="Moderation priority (1-10)")
    flags: List[str] = Field(default_factory=list, description="Auto-moderation flags")
    risk_score: float = Field(..., description="Automated risk assessment")
    estimated_review_time: int = Field(..., description="Estimated review time in minutes")

class ModerationDecision(BaseModel):
    """Moderator's decision on comment"""
    action: str = Field(..., description="approve, reject, or request_changes")
    notes: Optional[str] = Field(None, description="Moderator notes")
    content_modifications: Optional[str] = Field(None, description="Suggested content changes")
    tags: List[str] = Field(default_factory=list, description="Classification tags")

class ModerationQueueResponse(BaseModel):
    """Moderation queue with pagination"""
    items: List[ModerationQueueItem]
    pagination: dict
    queue_stats: dict = Field(..., description="Queue size and processing statistics")
```

### GDPR Models

```python
class DataAccessRequest(BaseModel):
    """GDPR Article 15 data access request"""
    email: str = Field(..., description="User's email address")
    verification_method: str = Field("email", description="Identity verification method")
    requested_data_types: List[str] = Field(
        default_factory=lambda: ["comments", "personal_data", "consent_history"],
        description="Types of data to include in export"
    )
    delivery_method: str = Field("email", description="How to deliver the export")

class DataErasureRequest(BaseModel):
    """GDPR Article 17 right to erasure request"""
    email: str = Field(..., description="User's email address")
    verification_code: str = Field(..., description="Email verification code")
    erasure_scope: dict = Field(..., description="Scope of data to erase")
    reason: Optional[str] = Field(None, description="Reason for erasure request")

class DataExportPackage(BaseModel):
    """Complete user data export"""
    user_identifier: str
    export_date: datetime
    data_types: List[str]
    comments: List[dict]
    personal_data: dict
    consent_history: List[dict]
    audit_logs: List[dict]
    file_format: str = Field("json", description="Export file format")
    file_size_bytes: int = Field(..., description="Total export size")
```

## 🔧 Service Layer Design

### Comment Service Interface

```python
class CommentService:
    """Core comment management service"""

    async def create_comment(
        self,
        content: str,
        post_slug: str,
        consent_preferences: ConsentPreferences,
        client_ip: str
    ) -> Comment:
        """Create new comment with privacy controls"""

    async def get_approved_comments(
        self,
        post_slug: str,
        sort_order: CommentSortOrder = CommentSortOrder.CHRONOLOGICAL
    ) -> List[CommentDisplay]:
        """Retrieve approved comments for public display"""

    async def update_comment_status(
        self,
        comment_id: str,
        new_status: CommentStatus,
        moderator_id: Optional[str] = None
    ) -> bool:
        """Update comment status with audit trail"""

    async def soft_delete_comment(
        self,
        comment_id: str,
        reason: str
    ) -> bool:
        """Soft delete comment while preserving thread structure"""
```

### GDPR Service Interface

```python
class GDPRService:
    """GDPR compliance and data subject rights service"""

    async def handle_data_access_request(
        self,
        user_identifier: str
    ) -> DataExportPackage:
        """Process Article 15 data access request"""

    async def handle_erasure_request(
        self,
        user_identifier: str,
        erasure_scope: dict
    ) -> ErasureResult:
        """Process Article 17 erasure request"""

    async def export_user_consent_history(
        self,
        user_identifier: str
    ) -> List[ConsentRecord]:
        """Export complete consent history for user"""

    async def anonymize_user_data(
        self,
        user_identifier: str,
        preserve_comments: bool = True
    ) -> AnonymizationResult:
        """Anonymize user data while preserving comment threads"""
```

## 🚀 Performance Considerations

### Response Optimization

```python
from fastapi.responses import JSONResponse
from starlette.responses import Response

async def optimized_comment_response(
    comments: List[CommentDisplay],
    request: Request
) -> JSONResponse:
    """Optimized JSON response with caching headers"""

    # Generate ETag for caching
    content_hash = generate_content_hash(comments)
    etag = f'"{content_hash}"'

    # Check client cache
    if_none_match = request.headers.get("if-none-match")
    if if_none_match == etag:
        return Response(status_code=304)

    # Prepare optimized response
    response_data = {
        "comments": [c.dict(exclude_none=True) for c in comments],
        "meta": {
            "total": len(comments),
            "generated_at": datetime.utcnow().isoformat()
        }
    }

    return JSONResponse(
        content=response_data,
        headers={
            "ETag": etag,
            "Cache-Control": "public, max-age=300",  # 5 minutes
            "Vary": "Accept-Encoding"
        }
    )
```

### Batch Operations

```python
class BatchCommentService:
    """Optimized batch operations for comment management"""

    async def batch_approve_comments(
        self,
        comment_ids: List[str],
        moderator_id: str
    ) -> BatchOperationResult:
        """Approve multiple comments in single transaction"""

        async with self.database.transaction():
            results = []
            for comment_id in comment_ids:
                try:
                    await self.approve_single_comment(comment_id, moderator_id)
                    results.append({"comment_id": comment_id, "status": "approved"})
                except Exception as e:
                    results.append({"comment_id": comment_id, "status": "error", "error": str(e)})

            # Batch cache invalidation
            affected_posts = await self.get_affected_posts(comment_ids)
            await self.cache_service.batch_invalidate(affected_posts)

        return BatchOperationResult(
            total_processed=len(comment_ids),
            successful=len([r for r in results if r["status"] == "approved"]),
            failed=len([r for r in results if r["status"] == "error"]),
            details=results
        )
```

---

**Related Documentation**:
- [Architecture Decisions](architecture.md)
- [Implementation Details](implementation.md)
- [Performance Optimization](performance.md)