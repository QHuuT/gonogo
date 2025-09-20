# Privacy Framework API Design

**Last Updated**: 2025-09-20

## 🎯 API Overview

The Privacy Framework API provides comprehensive GDPR compliance endpoints for consent management, data subject rights, and privacy controls. The design prioritizes legal compliance, user control, and audit transparency.

## 🌐 Core API Endpoints

### Consent Management

#### `POST /api/privacy/consent/collect`
**Purpose**: Collect GDPR-compliant user consent
**Authentication**: None (session-based)

```python
@app.post("/api/privacy/consent/collect")
async def collect_consent(
    consent_data: ConsentPreferences,
    request: Request
):
    """
    Collect user consent with full GDPR compliance
    """
    client_info = extract_client_info(request)

    # Validate GDPR requirements
    validation_result = await consent_service.validate_gdpr_consent(
        consent_data, client_info
    )

    if not validation_result.is_valid:
        raise HTTPException(400, detail=validation_result.errors)

    # Store consent with audit trail
    consent_record = await consent_service.store_consent(
        consent_data, client_info
    )

    return ConsentCollectionResponse(
        consent_id=consent_record.id,
        status="collected",
        expires_at=consent_record.expires_at,
        legal_basis=consent_record.legal_basis
    )
```

#### `GET /api/privacy/consent/status/{session_id}`
**Purpose**: Retrieve current consent status
**Response**: Current consent preferences and status

```python
@app.get("/api/privacy/consent/status/{session_id}")
async def get_consent_status(session_id: str):
    """
    Get current consent status for session
    """
    consent_status = await consent_service.get_active_consent(session_id)

    return ConsentStatusResponse(
        session_id=session_id,
        preferences=consent_status.preferences,
        collected_at=consent_status.timestamp,
        expires_at=consent_status.expires_at,
        requires_renewal=consent_status.requires_renewal()
    )
```

### Data Subject Rights

#### `POST /api/privacy/rights/access`
**Purpose**: Handle GDPR Article 15 (Right of Access)
**Authentication**: Email verification required

```python
@app.post("/api/privacy/rights/access")
async def request_data_access(
    access_request: DataAccessRequest,
    background_tasks: BackgroundTasks
):
    """
    Process GDPR Article 15 data access request
    """
    # Verify user identity
    verification = await identity_service.verify_user(
        access_request.email,
        access_request.verification_method
    )

    if not verification.verified:
        raise HTTPException(403, "Identity verification required")

    # Queue data collection job
    job_id = await rights_service.queue_access_request(access_request)

    background_tasks.add_task(
        rights_service.process_access_request, job_id
    )

    return RightsRequestResponse(
        request_id=job_id,
        status="processing",
        legal_deadline="30 days",
        estimated_completion="72 hours"
    )
```

#### `POST /api/privacy/rights/erasure`
**Purpose**: Handle GDPR Article 17 (Right to Erasure)
**Authentication**: Strong verification required

```python
@app.post("/api/privacy/rights/erasure")
async def request_data_erasure(
    erasure_request: DataErasureRequest,
    background_tasks: BackgroundTasks
):
    """
    Process GDPR Article 17 erasure request
    """
    # Evaluate erasure eligibility
    eligibility = await rights_service.evaluate_erasure_eligibility(
        erasure_request
    )

    if not eligibility.is_eligible:
        return ErasureRejectionResponse(
            status="rejected",
            reason=eligibility.rejection_reason,
            legal_basis=eligibility.legal_justification
        )

    # Queue erasure processing
    job_id = await rights_service.queue_erasure_request(erasure_request)

    background_tasks.add_task(
        rights_service.process_erasure_request, job_id
    )

    return RightsRequestResponse(
        request_id=job_id,
        status="processing",
        scope=erasure_request.scope,
        legal_deadline="30 days"
    )
```

### French CNIL Endpoints

#### `GET /api/privacy/cnil/banner`
**Purpose**: Retrieve CNIL-compliant consent banner
**Response**: Localized consent banner content

```python
@app.get("/api/privacy/cnil/banner")
async def get_cnil_banner(
    language: str = "fr",
    request: Request = None
):
    """
    Get CNIL-compliant consent banner
    """
    banner = await cnil_service.generate_consent_banner(language)

    # Add CNIL-specific requirements
    banner.cnil_compliance = CNILCompliance(
        authority_contact="CNIL - Commission Nationale de l'Informatique et des Libertés",
        complaint_url="https://www.cnil.fr/fr/plaintes",
        data_protection_officer_contact="dpo@example.com"
    )

    return banner
```

## 📊 Data Models

### Consent Models

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum

class ConsentCategory(str, Enum):
    ESSENTIAL = "essential"
    FUNCTIONAL = "functional"
    ANALYTICS = "analytics"
    MARKETING = "marketing"

class ConsentPreferences(BaseModel):
    """User consent preferences for different categories"""
    essential: bool = Field(True, description="Required for service operation")
    functional: bool = Field(False, description="Enhanced functionality")
    analytics: bool = Field(False, description="Usage analytics")
    marketing: bool = Field(False, description="Marketing communications")
    language: str = Field("en", description="User interface language")

    @validator('essential')
    def essential_must_be_true(cls, v):
        if not v:
            raise ValueError('Essential consent is required for service operation')
        return v

class ConsentRecord(BaseModel):
    """Complete consent record with audit information"""
    id: str
    session_id: str
    timestamp: datetime
    preferences: ConsentPreferences
    ip_address_hash: str = Field(..., description="Hashed IP for audit")
    user_agent_hash: str = Field(..., description="Hashed user agent")
    language: str
    consent_version: str = Field("2.0")
    expires_at: datetime
    legal_basis: Dict[str, str] = Field(..., description="Legal basis for each category")
    renewal_notice_sent: bool = Field(False)

class ConsentCollectionResponse(BaseModel):
    """Response after consent collection"""
    consent_id: str
    status: str = "collected"
    expires_at: datetime
    legal_basis: Dict[str, str]
    renewal_date: datetime = Field(..., description="When renewal notice will be sent")

class ConsentStatusResponse(BaseModel):
    """Current consent status response"""
    session_id: str
    preferences: ConsentPreferences
    collected_at: datetime
    expires_at: datetime
    requires_renewal: bool
    last_updated: datetime
```

### Data Subject Rights Models

```python
class RightsRequestType(str, Enum):
    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    RESTRICTION = "restriction"
    PORTABILITY = "portability"
    OBJECTION = "objection"

class DataAccessRequest(BaseModel):
    """GDPR Article 15 - Right of Access request"""
    email: str = Field(..., description="User's email address")
    verification_method: str = Field("email", description="Identity verification method")
    requested_data_types: List[str] = Field(
        default=["all"],
        description="Specific data types to include"
    )
    delivery_format: str = Field("json", description="Export format preference")

    @validator('email')
    def validate_email_format(cls, v):
        # Basic email validation
        if "@" not in v or "." not in v:
            raise ValueError('Valid email address required')
        return v.lower()

class DataErasureRequest(BaseModel):
    """GDPR Article 17 - Right to Erasure request"""
    email: str = Field(..., description="User's email address")
    verification_code: str = Field(..., description="Email verification code")
    erasure_reason: str = Field(..., description="Reason for erasure request")
    scope: ErasureScope = Field(..., description="Scope of data to erase")

class ErasureScope(BaseModel):
    """Scope definition for erasure requests"""
    include_comments: bool = Field(True, description="Include user comments")
    include_personal_data: bool = Field(True, description="Include personal data")
    include_analytics: bool = Field(True, description="Include analytics data")
    preserve_anonymized: bool = Field(True, description="Keep anonymized data")

class RightsRequestResponse(BaseModel):
    """Standard response for rights requests"""
    request_id: str
    status: str
    legal_deadline: str = "30 days"
    estimated_completion: str
    contact_email: str = "privacy@example.com"
    tracking_url: Optional[str] = None

class DataExportPackage(BaseModel):
    """Complete data export for access requests"""
    user_identifier: str
    export_date: datetime
    request_id: str
    data_categories: Dict[str, List[dict]]
    metadata: ExportMetadata
    legal_information: LegalInformation

class ExportMetadata(BaseModel):
    """Metadata about the data export"""
    total_records: int
    data_sources: List[str]
    export_format: str
    file_size_bytes: int
    checksum: str

class LegalInformation(BaseModel):
    """Legal information included with exports"""
    legal_basis: Dict[str, str]
    retention_periods: Dict[str, str]
    data_sharing: List[str]
    user_rights: Dict[str, str]
```

### CNIL Compliance Models

```python
class CNILBanner(BaseModel):
    """CNIL-compliant consent banner content"""
    language: str = "fr"
    title: str
    description: str
    cookie_categories: List[CNILCookieCategory]
    action_buttons: CNILActionButtons
    legal_links: CNILLegalLinks
    cnil_info: CNILContactInfo

class CNILCookieCategory(BaseModel):
    """CNIL cookie category information"""
    category: ConsentCategory
    name_fr: str
    name_en: str
    description_fr: str
    description_en: str
    required: bool
    examples: List[str]

class CNILActionButtons(BaseModel):
    """CNIL banner action buttons"""
    accept_all_fr: str = "Accepter tout"
    accept_all_en: str = "Accept all"
    accept_selected_fr: str = "Accepter la sélection"
    accept_selected_en: str = "Accept selection"
    reject_optional_fr: str = "Refuser les cookies optionnels"
    reject_optional_en: str = "Reject optional cookies"

class CNILContactInfo(BaseModel):
    """CNIL authority contact information"""
    authority_name: str = "Commission Nationale de l'Informatique et des Libertés (CNIL)"
    website: str = "https://www.cnil.fr"
    complaint_url: str = "https://www.cnil.fr/fr/plaintes"
    dpo_contact: str
```

## 🔧 Service Layer Design

### Privacy Service Interface

```python
class PrivacyFrameworkService:
    """Core privacy framework service interface"""

    async def collect_gdpr_consent(
        self,
        preferences: ConsentPreferences,
        client_info: ClientInfo
    ) -> ConsentRecord:
        """Collect GDPR-compliant consent"""

    async def process_consent_withdrawal(
        self,
        user_identifier: str,
        categories: List[ConsentCategory]
    ) -> ConsentWithdrawalResult:
        """Process consent withdrawal"""

    async def execute_data_subject_right(
        self,
        user_identifier: str,
        right_type: RightsRequestType,
        request_details: dict
    ) -> RightsExecutionResult:
        """Execute any GDPR data subject right"""

    async def apply_retention_policies(
        self,
        data_type: str,
        retention_rules: RetentionRules
    ) -> RetentionResult:
        """Apply automated data retention policies"""

    async def generate_compliance_report(
        self,
        report_type: str,
        date_range: DateRange
    ) -> ComplianceReport:
        """Generate compliance audit reports"""
```

## 🚀 Performance Considerations

### API Response Optimization

```python
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class PrivacyAPIOptimizationMiddleware(BaseHTTPMiddleware):
    """Optimize privacy API responses"""

    async def dispatch(self, request: Request, call_next):
        # Start timing
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Add performance headers
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        # Optimize privacy-specific responses
        if request.url.path.startswith("/api/privacy"):
            response = await self._optimize_privacy_response(response, request)

        return response

    async def _optimize_privacy_response(
        self,
        response: Response,
        request: Request
    ) -> Response:
        """Apply privacy-specific optimizations"""

        # Set appropriate cache headers for privacy data
        if "consent/status" in request.url.path:
            response.headers["Cache-Control"] = "private, max-age=300"
        elif "rights/" in request.url.path:
            response.headers["Cache-Control"] = "no-cache, no-store"

        # Add privacy headers
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        return response
```

### Batch Processing APIs

```python
@app.post("/api/privacy/admin/batch/consent-renewal")
async def batch_consent_renewal(
    renewal_batch: ConsentRenewalBatch,
    admin_user: AdminUser = Depends(get_admin_user)
):
    """Process batch consent renewals efficiently"""

    results = await consent_service.process_renewal_batch(
        renewal_batch.consent_ids,
        batch_size=100
    )

    return BatchProcessingResponse(
        total_processed=len(renewal_batch.consent_ids),
        successful=results.success_count,
        failed=results.failure_count,
        processing_time=results.processing_time
    )

@app.post("/api/privacy/admin/batch/retention-cleanup")
async def batch_retention_cleanup(
    cleanup_request: RetentionCleanupRequest,
    admin_user: AdminUser = Depends(get_admin_user)
):
    """Execute batch retention cleanup"""

    cleanup_result = await retention_service.execute_batch_cleanup(
        data_types=cleanup_request.data_types,
        cutoff_date=cleanup_request.cutoff_date
    )

    return RetentionCleanupResponse(
        data_types_processed=cleanup_result.data_types,
        records_anonymized=cleanup_result.anonymized_count,
        records_deleted=cleanup_result.deleted_count,
        completion_time=cleanup_result.completion_time
    )
```

---

**Related Documentation**:
- [Architecture Decisions](architecture.md)
- [Implementation Details](implementation.md)
- [Performance Optimization](performance.md)