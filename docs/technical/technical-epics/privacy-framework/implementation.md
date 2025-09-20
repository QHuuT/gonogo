# Privacy Framework Implementation

**Last Updated**: 2025-09-20

## 🏗️ Implementation Overview

This document details the technical implementation of the privacy and consent management framework, including GDPR compliance components, French CNIL requirements, and privacy-by-design patterns.

## 📁 Code Organization

### Directory Structure
```
src/be/
├── privacy/
│   ├── api/
│   │   ├── consent.py           # Consent management endpoints
│   │   ├── rights.py            # Data subject rights endpoints
│   │   └── retention.py         # Data retention endpoints
│   ├── services/
│   │   ├── consent_service.py   # Consent collection and validation
│   │   ├── rights_service.py    # GDPR rights implementation
│   │   ├── retention_service.py # Data lifecycle management
│   │   └── cnil_service.py      # French CNIL compliance
│   ├── models/
│   │   ├── consent_models.py    # Consent and preference models
│   │   ├── rights_models.py     # Data subject rights models
│   │   └── retention_models.py  # Retention policy models
│   ├── middleware/
│   │   ├── privacy_middleware.py # Privacy-by-design enforcement
│   │   ├── consent_middleware.py # Consent validation
│   │   └── audit_middleware.py   # Privacy audit logging
│   └── templates/
│       ├── consent/
│       │   ├── banner_fr.html   # French CNIL consent banner
│       │   ├── banner_en.html   # English consent banner
│       │   └── preferences.html # Consent management interface
│       └── rights/
│           ├── access_form.html # Data access request form
│           └── erasure_form.html # Data erasure request form
├── core/
│   ├── privacy_patterns.py      # Privacy-by-design base classes
│   └── gdpr_compliance.py       # GDPR validation utilities
└── tasks/
    ├── retention_cleanup.py     # Automated retention processing
    └── consent_renewal.py       # Consent renewal notifications
```

## 🔧 Core Components

### 1. Consent Management API (`src/be/privacy/api/consent.py`)

```python
from fastapi import APIRouter, Request, HTTPException, Depends
from ..services.consent_service import ConsentService
from ..models.consent_models import ConsentPreferences, ConsentRecord

router = APIRouter(prefix="/api/privacy/consent", tags=["consent"])

@router.post("/collect")
async def collect_consent(
    consent_data: ConsentPreferences,
    request: Request,
    consent_service: ConsentService = Depends()
):
    """
    Collect and validate GDPR-compliant consent
    """
    # Extract client information for audit
    client_info = ClientInfo(
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        language=request.headers.get("accept-language", "en")
    )

    # Validate consent meets GDPR requirements
    validation_result = await consent_service.validate_consent(
        consent_data, client_info
    )

    if not validation_result.is_valid:
        raise HTTPException(400, detail=validation_result.errors)

    # Store consent record
    consent_record = await consent_service.store_consent(
        consent_data, client_info
    )

    return {
        "consent_id": consent_record.id,
        "status": "collected",
        "expires_at": consent_record.expires_at.isoformat(),
        "renewal_notice": consent_record.renewal_notice_date.isoformat()
    }

@router.post("/withdraw")
async def withdraw_consent(
    withdrawal_request: ConsentWithdrawal,
    request: Request,
    consent_service: ConsentService = Depends()
):
    """
    Handle consent withdrawal per GDPR Article 7(3)
    """
    # Verify user identity for withdrawal
    identity_verified = await consent_service.verify_withdrawal_identity(
        withdrawal_request.user_identifier,
        withdrawal_request.verification_token
    )

    if not identity_verified:
        raise HTTPException(403, "Identity verification required")

    # Process withdrawal
    withdrawal_result = await consent_service.process_withdrawal(
        withdrawal_request
    )

    return {
        "withdrawal_id": withdrawal_result.id,
        "status": "processed",
        "effective_date": withdrawal_result.effective_date.isoformat(),
        "data_processing_deadline": withdrawal_result.processing_deadline.isoformat()
    }

@router.get("/status/{session_id}")
async def get_consent_status(
    session_id: str,
    consent_service: ConsentService = Depends()
):
    """
    Retrieve current consent status for session
    """
    consent_status = await consent_service.get_active_consent(session_id)

    return {
        "session_id": session_id,
        "has_essential_consent": consent_status.essential,
        "has_functional_consent": consent_status.functional,
        "has_analytics_consent": consent_status.analytics,
        "has_marketing_consent": consent_status.marketing,
        "last_updated": consent_status.last_updated.isoformat(),
        "renewal_required": consent_status.requires_renewal()
    }
```

**Responsibilities**:
- Collect and validate GDPR-compliant consent
- Handle consent withdrawal requests
- Provide consent status information
- Implement French CNIL specific requirements

### 2. Data Subject Rights API (`src/be/privacy/api/rights.py`)

```python
from fastapi import APIRouter, BackgroundTasks, HTTPException
from ..services.rights_service import RightsService
from ..models.rights_models import AccessRequest, ErasureRequest

router = APIRouter(prefix="/api/privacy/rights", tags=["data-rights"])

@router.post("/access")
async def request_data_access(
    access_request: AccessRequest,
    background_tasks: BackgroundTasks,
    rights_service: RightsService = Depends()
):
    """
    Handle GDPR Article 15 - Right of Access
    """
    # Validate request and user identity
    validation_result = await rights_service.validate_access_request(
        access_request
    )

    if not validation_result.is_valid:
        raise HTTPException(400, detail=validation_result.error_message)

    # Queue data collection job
    job_id = await rights_service.queue_data_access_job(access_request)

    # Process in background (complex data collection)
    background_tasks.add_task(
        rights_service.process_access_request,
        job_id
    )

    return {
        "request_id": job_id,
        "status": "processing",
        "estimated_completion": "72 hours",
        "legal_deadline": "30 days",
        "contact_info": "privacy@example.com"
    }

@router.post("/erasure")
async def request_data_erasure(
    erasure_request: ErasureRequest,
    background_tasks: BackgroundTasks,
    rights_service: RightsService = Depends()
):
    """
    Handle GDPR Article 17 - Right to Erasure
    """
    # Evaluate erasure request eligibility
    eligibility = await rights_service.evaluate_erasure_eligibility(
        erasure_request
    )

    if not eligibility.is_eligible:
        return {
            "request_id": None,
            "status": "rejected",
            "reason": eligibility.rejection_reason,
            "legal_basis": eligibility.legal_justification,
            "appeal_process": "Contact privacy@example.com for appeal"
        }

    # Queue erasure job
    job_id = await rights_service.queue_erasure_job(erasure_request)

    # Process in background (cross-system erasure)
    background_tasks.add_task(
        rights_service.process_erasure_request,
        job_id
    )

    return {
        "request_id": job_id,
        "status": "processing",
        "scope": erasure_request.scope,
        "estimated_completion": "30 days",
        "verification_required": True
    }

@router.get("/request/{request_id}/status")
async def get_request_status(
    request_id: str,
    rights_service: RightsService = Depends()
):
    """
    Check status of rights request
    """
    status = await rights_service.get_request_status(request_id)

    return {
        "request_id": request_id,
        "status": status.current_status,
        "progress_percentage": status.progress,
        "last_updated": status.last_updated.isoformat(),
        "estimated_completion": status.estimated_completion,
        "messages": status.status_messages
    }
```

**Responsibilities**:
- Implement GDPR Articles 15-22 data subject rights
- Handle complex data collection and erasure workflows
- Provide status tracking for rights requests
- Manage cross-system data operations

### 3. Consent Service (`src/be/privacy/services/consent_service.py`)

```python
class ConsentService:
    """Core consent management business logic"""

    def __init__(self, consent_repo: ConsentRepository, audit_service: AuditService):
        self.consent_repo = consent_repo
        self.audit_service = audit_service

    async def validate_consent(
        self,
        consent_data: ConsentPreferences,
        client_info: ClientInfo
    ) -> ConsentValidationResult:
        """Validate consent meets GDPR Article 7 requirements"""

        validation_errors = []

        # Check required consent fields
        if not consent_data.essential:
            validation_errors.append("Essential consent required for service operation")

        # Validate optional consent logic
        if consent_data.analytics and not consent_data.functional:
            validation_errors.append("Analytics consent requires functional consent")

        # Check consent specificity (GDPR Article 7)
        if not self._is_consent_specific(consent_data):
            validation_errors.append("Consent must be specific for each purpose")

        # Validate French CNIL requirements
        if client_info.language.startswith("fr"):
            cnil_validation = await self._validate_cnil_requirements(
                consent_data, client_info
            )
            validation_errors.extend(cnil_validation.errors)

        return ConsentValidationResult(
            is_valid=len(validation_errors) == 0,
            errors=validation_errors,
            warnings=self._generate_consent_warnings(consent_data)
        )

    async def store_consent(
        self,
        consent_data: ConsentPreferences,
        client_info: ClientInfo
    ) -> ConsentRecord:
        """Store GDPR-compliant consent record"""

        # Create comprehensive consent record
        consent_record = ConsentRecord(
            timestamp=datetime.utcnow(),
            ip_address_hash=self._hash_ip_address(client_info.ip_address),
            user_agent_hash=self._hash_user_agent(client_info.user_agent),
            language=client_info.language,
            consent_version="2.0",
            preferences=consent_data,
            legal_basis=self._determine_legal_basis(consent_data),
            expires_at=self._calculate_expiry_date(),
            renewal_notice_date=self._calculate_renewal_date()
        )

        # Store with appropriate retention
        stored_record = await self.consent_repo.store(consent_record)

        # Log for audit trail
        await self.audit_service.log_consent_collection(
            stored_record.id,
            consent_data,
            client_info
        )

        return stored_record

    async def process_withdrawal(
        self,
        withdrawal_request: ConsentWithdrawal
    ) -> ConsentWithdrawalResult:
        """Process consent withdrawal per GDPR Article 7(3)"""

        # Find existing consent records
        existing_consents = await self.consent_repo.find_by_user(
            withdrawal_request.user_identifier
        )

        if not existing_consents:
            raise ConsentNotFoundError("No consent records found for user")

        # Create withdrawal record
        withdrawal_record = ConsentWithdrawalRecord(
            user_identifier=withdrawal_request.user_identifier,
            withdrawn_categories=withdrawal_request.categories,
            withdrawal_timestamp=datetime.utcnow(),
            processing_deadline=datetime.utcnow() + timedelta(days=30),
            reason=withdrawal_request.reason
        )

        # Update consent status
        for consent in existing_consents:
            await self._update_consent_for_withdrawal(consent, withdrawal_record)

        # Trigger data processing changes
        await self._trigger_withdrawal_processing(withdrawal_record)

        # Log withdrawal for audit
        await self.audit_service.log_consent_withdrawal(withdrawal_record)

        return ConsentWithdrawalResult(
            id=withdrawal_record.id,
            effective_date=withdrawal_record.withdrawal_timestamp,
            processing_deadline=withdrawal_record.processing_deadline,
            affected_systems=await self._identify_affected_systems(withdrawal_record)
        )

    def _hash_ip_address(self, ip_address: str) -> str:
        """Hash IP address for privacy protection"""
        # Use cryptographic hash with salt for anonymization
        salt = self._get_daily_salt()
        return hashlib.sha256(f"{ip_address}{salt}".encode()).hexdigest()

    def _determine_legal_basis(self, consent_data: ConsentPreferences) -> dict:
        """Determine legal basis for each type of processing"""
        return {
            "essential": "legitimate_interest",  # Service operation
            "functional": "consent" if consent_data.functional else None,
            "analytics": "consent" if consent_data.analytics else None,
            "marketing": "consent" if consent_data.marketing else None
        }
```

**Responsibilities**:
- Validate GDPR-compliant consent collection
- Store consent records with proper retention
- Handle consent withdrawal processing
- Implement privacy protection for consent data

### 4. French CNIL Service (`src/be/privacy/services/cnil_service.py`)

```python
class CNILComplianceService:
    """French CNIL specific requirements implementation"""

    def __init__(self):
        self.cnil_requirements = {
            "cookie_banner_language": "fr",
            "ip_retention_days": 30,
            "data_retention_years": 3,
            "consent_renewal_months": 13
        }

    async def generate_cnil_consent_banner(
        self,
        language: str = "fr"
    ) -> CNILConsentBanner:
        """Generate CNIL-compliant consent banner"""

        if language == "fr":
            banner_content = CNILConsentBanner(
                title="Gestion des cookies et de la confidentialité",
                description="Nous utilisons des cookies pour améliorer votre expérience. "
                           "Vous pouvez choisir quels cookies accepter.",
                essential_text="Cookies essentiels : Nécessaires au fonctionnement du site",
                functional_text="Cookies fonctionnels : Améliorent l'expérience utilisateur",
                analytics_text="Cookies analytiques : Nous aident à comprendre l'utilisation",
                marketing_text="Cookies marketing : Personnalisent la publicité",
                accept_all_text="Accepter tout",
                accept_selected_text="Accepter la sélection",
                reject_optional_text="Refuser les cookies optionnels",
                manage_preferences_text="Gérer les préférences",
                more_info_text="Plus d'informations",
                cnil_info=CNILInfo(
                    authority_name="Commission Nationale de l'Informatique et des Libertés (CNIL)",
                    website="https://www.cnil.fr",
                    complaint_url="https://www.cnil.fr/fr/plaintes",
                    contact_text="Pour exercer vos droits ou déposer une plainte : CNIL"
                )
            )
        else:
            banner_content = self._generate_english_banner()

        # Validate banner meets CNIL readability requirements
        await self._validate_cnil_readability(banner_content)

        return banner_content

    async def implement_ip_anonymization(self):
        """CNIL requirement: IP anonymization after 30 days"""

        anonymization_policy = IPAnonymizationPolicy(
            retention_period=timedelta(days=30),
            anonymization_method="sha256_with_daily_salt",
            schedule="daily_at_2am",
            verification_required=True
        )

        # Register with retention engine
        await self.retention_engine.register_policy(
            "ip_addresses",
            anonymization_policy
        )

        # Set up monitoring
        await self.monitoring_service.setup_ip_anonymization_alerts()

    async def generate_french_privacy_policy(self) -> FrenchPrivacyPolicy:
        """Generate CNIL-compliant privacy policy in French"""

        policy_content = FrenchPrivacyPolicy(
            title="Politique de Confidentialité",
            last_updated=datetime.utcnow(),
            sections={
                "finalites": self._generate_processing_purposes_section(),
                "donnees_collectees": self._generate_data_collected_section(),
                "base_legale": self._generate_legal_basis_section(),
                "duree_conservation": self._generate_retention_section(),
                "droits_utilisateur": self._generate_user_rights_section(),
                "contact_dpo": self._generate_dpo_contact_section(),
                "reclamation_cnil": self._generate_cnil_complaint_section()
            },
            cnil_compliance_verified=True,
            legal_review_date=datetime.utcnow()
        )

        return policy_content

    def _generate_user_rights_section(self) -> dict:
        """Generate French user rights section"""
        return {
            "title": "Vos droits sur vos données personnelles",
            "content": {
                "droit_acces": "Droit d'accès (Article 15 RGPD)",
                "droit_rectification": "Droit de rectification (Article 16 RGPD)",
                "droit_effacement": "Droit à l'effacement (Article 17 RGPD)",
                "droit_limitation": "Droit à la limitation du traitement (Article 18 RGPD)",
                "droit_portabilite": "Droit à la portabilité (Article 20 RGPD)",
                "droit_opposition": "Droit d'opposition (Article 21 RGPD)",
                "contact": "Pour exercer vos droits : privacy@example.com",
                "delai_reponse": "Délai de réponse : 30 jours maximum",
                "recours_cnil": "En cas de litige : plainte auprès de la CNIL"
            }
        }
```

**Responsibilities**:
- Generate French CNIL-compliant consent interfaces
- Implement IP anonymization requirements
- Generate French privacy policy content
- Ensure CNIL-specific compliance measures

## 🎨 Privacy-by-Design Patterns

### Base Privacy Model Pattern

```python
from abc import ABC, abstractmethod
from typing import Optional, List, Dict

class PrivacyAwareModel(ABC):
    """Base class enforcing privacy-by-design patterns"""

    def __init__(self):
        self.core_data: Optional[dict] = None
        self.personal_data: Optional[dict] = None
        self.consent_record: Optional[ConsentRecord] = None
        self.retention_policy: Optional[RetentionPolicy] = None

    @abstractmethod
    def get_core_data(self) -> dict:
        """Return data required for core functionality"""
        pass

    @abstractmethod
    def get_personal_data(self) -> Optional[dict]:
        """Return personal data (requires consent)"""
        pass

    @abstractmethod
    def apply_privacy_constraints(self, user_consent: ConsentRecord) -> 'PrivacyAwareModel':
        """Apply privacy constraints based on user consent"""
        pass

    def to_public_display(self) -> dict:
        """Return privacy-safe data for public display"""
        public_data = self.get_core_data().copy()

        # Only include personal data if consent allows
        if self.consent_record and self.consent_record.allows_personal_display():
            personal_data = self.get_personal_data()
            if personal_data:
                public_data.update(personal_data)

        return public_data

    def to_audit_format(self) -> dict:
        """Return complete data for audit purposes"""
        return {
            "core_data": self.get_core_data(),
            "personal_data": self.get_personal_data(),
            "consent_id": self.consent_record.id if self.consent_record else None,
            "retention_until": self.retention_policy.expires_at if self.retention_policy else None
        }

class PrivacyAwareComment(PrivacyAwareModel):
    """Example implementation for comment system"""

    def __init__(self, content: str, post_slug: str):
        super().__init__()
        self.core_data = {
            "content": content,
            "post_slug": post_slug,
            "created_at": datetime.utcnow(),
            "status": "pending"
        }

    def get_core_data(self) -> dict:
        return self.core_data

    def get_personal_data(self) -> Optional[dict]:
        return self.personal_data

    def apply_privacy_constraints(self, user_consent: ConsentRecord) -> 'PrivacyAwareComment':
        """Apply privacy constraints based on consent"""

        if user_consent.allows_email_storage():
            self.personal_data = self.personal_data or {}
            # Email data can be stored
        else:
            # Remove email data if consent withdrawn
            if self.personal_data:
                self.personal_data.pop("email", None)

        if not user_consent.allows_name_display():
            # Remove display name
            if self.personal_data:
                self.personal_data.pop("display_name", None)

        return self
```

### Privacy Middleware Implementation

```python
class PrivacyMiddleware:
    """Middleware enforcing privacy-by-design across all requests"""

    async def __call__(self, request: Request, call_next):
        # Add privacy context to request
        privacy_context = await self._build_privacy_context(request)
        request.state.privacy_context = privacy_context

        # Process request
        response = await call_next(request)

        # Apply privacy headers
        self._add_privacy_headers(response)

        # Log privacy-relevant events
        await self._log_privacy_events(request, response, privacy_context)

        return response

    async def _build_privacy_context(self, request: Request) -> PrivacyContext:
        """Build privacy context for request"""

        # Extract user session/identifier
        session_id = self._extract_session_id(request)

        # Get active consent
        active_consent = await self.consent_service.get_active_consent(session_id)

        # Determine data collection permissions
        permissions = DataCollectionPermissions(
            can_collect_analytics=active_consent.analytics,
            can_collect_functional=active_consent.functional,
            can_store_personal_data=active_consent.personal_data_storage,
            requires_anonymization=self._requires_anonymization(request)
        )

        return PrivacyContext(
            session_id=session_id,
            consent_record=active_consent,
            permissions=permissions,
            client_info=self._extract_client_info(request)
        )

    def _add_privacy_headers(self, response: Response):
        """Add privacy-related HTTP headers"""
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "accelerometer=(), gyroscope=(), magnetometer=()"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Content-Type-Options"] = "nosniff"
```

---

**Related Documentation**:
- [Architecture Decisions](architecture.md)
- [Performance Optimization](performance.md)
- [API Design](api-design.md)