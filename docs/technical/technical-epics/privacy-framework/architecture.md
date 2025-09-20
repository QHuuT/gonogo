# Privacy Framework Architecture

**Last Updated**: 2025-09-20

## 🏗️ Architecture Decisions

### ADR-001: Privacy-by-Design Architecture

**Status**: Approved
**Date**: 2025-09-20

#### Context
Need foundational architecture that embeds privacy protection into every system component to achieve GDPR compliance.

#### Decision
Implement privacy-by-design principles as architectural constraints across all platform components.

#### Rationale
- **GDPR Article 25**: Data protection by design and by default required
- **Legal Safety**: Proactive privacy protection reduces compliance risk
- **User Trust**: Transparent privacy controls build user confidence
- **Scalability**: Embedded privacy patterns scale across features

#### Consequences
- Enhanced privacy protection across all features
- Increased development complexity for privacy compliance
- Stronger legal compliance posture
- Better user trust and transparency

### ADR-002: Granular Consent Management System

**Status**: Approved
**Date**: 2025-09-20

#### Context
Need consent system that meets GDPR Article 7 requirements for specific, informed, freely given consent.

#### Decision
Implement granular consent categories with independent opt-in/opt-out controls.

#### Rationale
- **GDPR Article 7**: Consent must be specific and granular
- **User Control**: Independent consent categories enhance user agency
- **Legal Compliance**: Clear consent records for regulatory audit
- **French CNIL**: Specific requirements for cookie consent

#### Consequences
- Complex consent interface design
- Multiple consent tracking systems required
- Enhanced user control and legal compliance
- Improved audit trail for regulatory review

### ADR-003: Data Subject Rights API Architecture

**Status**: Approved
**Date**: 2025-09-20

#### Context
Need systematic implementation of GDPR Articles 15-22 data subject rights.

#### Decision
Build centralized API for all data subject rights with cross-system integration.

#### Rationale
- **GDPR Articles 15-22**: Legal requirement for data subject rights
- **Centralization**: Consistent implementation across all features
- **Audit Trail**: Complete logging for compliance verification
- **Automation**: Reduce manual processing and response time

#### Consequences
- Complex cross-system integration requirements
- Enhanced compliance verification capabilities
- Improved response time for rights requests
- Comprehensive audit trail for regulatory review

## 🏛️ System Architecture

### Privacy Framework Components
```
┌─────────────────────────────────────────────────────────────┐
│                  Privacy Framework                          │
│                                                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ Consent Manager │ │ Rights Engine   │ │ Retention Engine│ │
│ │                 │ │                 │ │                 │ │
│ │ - Cookie Banner │ │ - Access        │ │ - Auto Cleanup  │ │
│ │ - Granular Opts │ │ - Rectification │ │ - Retention     │ │
│ │ - CNIL Compliance│ │ - Erasure       │ │ - Anonymization │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│           │                   │                   │         │
│           └───────────────────┼───────────────────┘         │
│                               │                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │              Privacy Data Store                         │ │
│ │                                                         │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │ │
│ │ │   Consent   │ │   Rights    │ │    Retention        │ │ │
│ │ │   Records   │ │   Logs      │ │    Policies         │ │ │
│ │ └─────────────┘ └─────────────┘ └─────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Cross-System Integration
```
Privacy Framework
       │
       ├── Blog Platform (Content + Comments)
       │   ├── Comment Consent Validation
       │   ├── Author Data Rights
       │   └── Content Retention Policies
       │
       ├── Comment System (User Generated Content)
       │   ├── Comment Submission Consent
       │   ├── Personal Data Separation
       │   └── User Rights Implementation
       │
       └── Analytics & Tracking (Optional Features)
           ├── Tracking Consent Management
           ├── Analytics Data Rights
           └── Cookie Consent Integration
```

## 🔐 Privacy-by-Design Architecture

### Data Minimization Patterns

#### Separation of Core and Personal Data
```python
# Architecture pattern for data separation
class PrivacyAwareDataModel:
    """Base pattern for privacy-compliant data models"""

    # Core functional data (required for operation)
    core_data: CoreDataModel

    # Personal data (requires consent, separate storage)
    personal_data: Optional[PersonalDataModel]

    # Consent tracking (links consent to data)
    consent_record: ConsentRecord

class CommentImplementation(PrivacyAwareDataModel):
    """Example: Comment system implementing privacy pattern"""

    # Core data: content, post reference, timestamp
    core_data = CommentCore(
        content="sanitized_comment_text",
        post_slug="blog-post-slug",
        created_at=datetime.utcnow(),
        status=CommentStatus.PENDING
    )

    # Personal data: email, name (only if consented)
    personal_data = PersonalCommentData(
        email="user@example.com",  # Only if email consent given
        display_name="User Name",  # Only if name consent given
        retention_until=calculate_retention_date()
    )

    # Consent record: tracks what user consented to
    consent_record = ConsentRecord(
        consent_id="consent_123",
        granted_permissions=["comment_storage", "email_notifications"],
        consent_timestamp=datetime.utcnow(),
        consent_version="1.0"
    )
```

#### Data Access Control Architecture
```python
class PrivacyAccessControl:
    """Privacy-aware access control for all data operations"""

    def authorize_data_access(
        self,
        user_id: str,
        data_type: str,
        operation: str,
        purpose: str
    ) -> AccessDecision:
        """
        Authorize data access based on privacy constraints
        """
        # Check consent for the specific purpose
        consent = self.consent_service.get_active_consent(user_id, data_type)

        if not consent.allows_purpose(purpose):
            return AccessDecision.DENIED("Insufficient consent")

        # Check retention policies
        if self.retention_service.is_data_expired(user_id, data_type):
            return AccessDecision.DENIED("Data retention period expired")

        # Check GDPR rights restrictions
        if self.rights_service.has_restriction(user_id, data_type):
            return AccessDecision.DENIED("User has restricted processing")

        # Log access for audit trail
        self.audit_service.log_data_access(
            user_id, data_type, operation, purpose
        )

        return AccessDecision.ALLOWED()
```

## 🌐 Consent Management Architecture

### Granular Consent System
```python
class ConsentCategories:
    """GDPR-compliant consent categories"""

    ESSENTIAL = "essential"          # Required for service operation
    FUNCTIONAL = "functional"        # Enhanced functionality
    ANALYTICS = "analytics"          # Usage analytics and optimization
    MARKETING = "marketing"          # Marketing communications

class ConsentManager:
    """Central consent management system"""

    def collect_consent(
        self,
        user_session: str,
        consent_preferences: ConsentPreferences
    ) -> ConsentRecord:
        """Collect and validate GDPR-compliant consent"""

        # Validate consent meets GDPR Article 7 requirements
        validation_result = self.validate_gdpr_consent(consent_preferences)

        if not validation_result.is_valid:
            raise ConsentValidationError(validation_result.errors)

        # Create consent record with full audit trail
        consent_record = ConsentRecord(
            session_id=user_session,
            timestamp=datetime.utcnow(),
            ip_address=self.anonymize_ip(request.client.host),
            user_agent_hash=self.hash_user_agent(request.headers.get("user-agent")),
            consent_version="2.0",
            language="fr",  # French CNIL requirement
            preferences=consent_preferences,
            legal_basis=self.determine_legal_basis(consent_preferences)
        )

        # Store with appropriate retention
        await self.consent_repository.store_consent(consent_record)

        # Update active consent cache
        await self.update_active_consent_cache(user_session, consent_record)

        return consent_record

    def withdraw_consent(
        self,
        user_identifier: str,
        consent_category: str
    ) -> ConsentWithdrawal:
        """Handle consent withdrawal per GDPR Article 7(3)"""

        # Create withdrawal record
        withdrawal = ConsentWithdrawal(
            user_identifier=user_identifier,
            category=consent_category,
            withdrawal_timestamp=datetime.utcnow(),
            processing_deadline=datetime.utcnow() + timedelta(days=30)
        )

        # Trigger data processing changes
        await self.process_consent_withdrawal(withdrawal)

        # Update consent cache immediately
        await self.invalidate_consent_cache(user_identifier)

        return withdrawal
```

### French CNIL Compliance Architecture
```python
class CNILComplianceService:
    """French CNIL specific requirements implementation"""

    async def generate_cnil_banner(self, language: str = "fr") -> CNILBanner:
        """Generate CNIL-compliant cookie consent banner"""

        banner_content = CNILBanner(
            language=language,
            title=self.get_localized_text("consent.banner.title", language),
            description=self.get_localized_text("consent.banner.description", language),
            essential_cookies=self.get_essential_cookie_info(),
            optional_cookies=self.get_optional_cookie_info(),
            cnil_info=CNILContactInfo(
                authority="Commission Nationale de l'Informatique et des Libertés (CNIL)",
                website="https://www.cnil.fr",
                complaint_process="https://www.cnil.fr/fr/plaintes"
            ),
            legal_links={
                "privacy_policy": "/politique-confidentialite",
                "cookie_policy": "/politique-cookies",
                "legal_notices": "/mentions-legales"
            }
        )

        # Ensure all text meets CNIL readability requirements
        await self.validate_cnil_compliance(banner_content)

        return banner_content

    async def implement_ip_anonymization(self):
        """CNIL requirement: IP anonymization after 30 days"""

        # Schedule automatic IP anonymization
        retention_policy = RetentionPolicy(
            data_type="ip_addresses",
            retention_period=timedelta(days=30),
            anonymization_method="hash_with_rotating_salt",
            schedule=CronSchedule("0 2 * * *")  # Daily at 2 AM
        )

        await self.retention_engine.register_policy(retention_policy)
```

## 🔍 Data Subject Rights Architecture

### Rights Engine Design
```python
class DataSubjectRightsEngine:
    """Centralized implementation of GDPR Articles 15-22"""

    async def handle_access_request(
        self,
        user_identifier: str,
        requested_data_types: List[str]
    ) -> AccessRequestResult:
        """Article 15: Right of Access implementation"""

        # Validate identity
        identity_verification = await self.verify_user_identity(user_identifier)

        if not identity_verification.is_verified:
            raise IdentityVerificationError("Unable to verify user identity")

        # Collect data from all systems
        data_collection_tasks = [
            self.collect_blog_data(user_identifier),
            self.collect_comment_data(user_identifier),
            self.collect_consent_data(user_identifier),
            self.collect_analytics_data(user_identifier)
        ]

        collected_data = await asyncio.gather(*data_collection_tasks)

        # Generate comprehensive export
        export_package = DataExportPackage(
            user_identifier=user_identifier,
            request_timestamp=datetime.utcnow(),
            data_categories=self.categorize_collected_data(collected_data),
            legal_basis=self.identify_legal_basis_for_data(collected_data),
            retention_periods=self.get_retention_info(collected_data),
            sharing_information=self.get_data_sharing_info(),
            rights_information=self.get_user_rights_info()
        )

        # Log request for audit
        await self.audit_service.log_access_request(
            user_identifier, export_package.size_bytes
        )

        return AccessRequestResult(
            export_package=export_package,
            delivery_method="secure_email",
            completion_date=datetime.utcnow()
        )

    async def handle_erasure_request(
        self,
        user_identifier: str,
        erasure_scope: ErasureScope
    ) -> ErasureResult:
        """Article 17: Right to Erasure implementation"""

        # Evaluate erasure applicability
        erasure_evaluation = await self.evaluate_erasure_request(
            user_identifier, erasure_scope
        )

        if not erasure_evaluation.is_applicable:
            return ErasureResult(
                status="rejected",
                reason=erasure_evaluation.rejection_reason,
                legal_basis=erasure_evaluation.legal_justification
            )

        # Execute cross-system erasure
        erasure_tasks = [
            self.erase_blog_data(user_identifier, erasure_scope),
            self.erase_comment_data(user_identifier, erasure_scope),
            self.erase_personal_data(user_identifier, erasure_scope),
            self.anonymize_analytics_data(user_identifier)
        ]

        erasure_results = await asyncio.gather(*erasure_tasks)

        # Generate comprehensive erasure report
        erasure_report = ErasureReport(
            user_identifier=user_identifier,
            completion_date=datetime.utcnow(),
            items_processed=sum(r.items_count for r in erasure_results),
            systems_affected=[r.system_name for r in erasure_results],
            verification_hash=self.generate_erasure_verification(erasure_results)
        )

        # Log erasure for audit compliance
        await self.audit_service.log_erasure_completion(erasure_report)

        return ErasureResult(
            status="completed",
            report=erasure_report,
            completion_confirmation=True
        )
```

## 📊 Retention and Lifecycle Architecture

### Automated Data Lifecycle Management
```python
class DataRetentionEngine:
    """Automated data retention and lifecycle management"""

    def __init__(self):
        self.retention_policies = {
            "comment_data": RetentionPolicy(
                duration=timedelta(days=1095),  # 3 years (CNIL requirement)
                action=RetentionAction.ANONYMIZE
            ),
            "personal_data": RetentionPolicy(
                duration=timedelta(days=1095),  # 3 years
                action=RetentionAction.DELETE
            ),
            "consent_records": RetentionPolicy(
                duration=timedelta(days=2555),  # 7 years (legal requirement)
                action=RetentionAction.ARCHIVE
            ),
            "ip_addresses": RetentionPolicy(
                duration=timedelta(days=30),    # CNIL requirement
                action=RetentionAction.ANONYMIZE
            ),
            "audit_logs": RetentionPolicy(
                duration=timedelta(days=2555),  # 7 years
                action=RetentionAction.ARCHIVE
            )
        }

    async def process_retention_policies(self):
        """Daily execution of retention policies"""

        for data_type, policy in self.retention_policies.items():
            expired_data = await self.find_expired_data(data_type, policy)

            if expired_data:
                await self.execute_retention_action(
                    data_type, expired_data, policy.action
                )

                # Log retention processing
                await self.audit_service.log_retention_processing(
                    data_type, len(expired_data), policy.action
                )

    async def execute_retention_action(
        self,
        data_type: str,
        data_items: List[str],
        action: RetentionAction
    ):
        """Execute specific retention action on data"""

        if action == RetentionAction.DELETE:
            await self.hard_delete_data(data_type, data_items)
        elif action == RetentionAction.ANONYMIZE:
            await self.anonymize_data(data_type, data_items)
        elif action == RetentionAction.ARCHIVE:
            await self.archive_data(data_type, data_items)
```

---

**Related Documentation**:
- [Implementation Details](implementation.md)
- [Performance Optimization](performance.md)
- [API Design](api-design.md)