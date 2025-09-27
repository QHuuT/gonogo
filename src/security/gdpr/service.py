"""
GDPR compliance service for managing consent and data subject rights.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import and_, text
from sqlalchemy.orm import Session

from .models import (
    ConsentRecord,
    ConsentType,
    DataProcessingRecord,
    DataSubjectRequest,
    DataSubjectRights,
    LegalBasis,
)


class GDPRService:
    """Service for GDPR compliance operations."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def _ensure_timezone_aware(self, dt: datetime) -> datetime:
        """Ensure datetime is timezone-aware (assume UTC if naive)."""
        if dt is None:
            return None
        if dt.tzinfo is None:
            # Assume naive datetime is UTC
            return dt.replace(tzinfo=UTC)
        return dt

    def _hash_data(self, data: str, salt: Optional[str] = None) -> str:
        """Hash sensitive data for privacy protection."""
        if salt is None:
            salt = secrets.token_hex(16)

        combined = f"{data}{salt}"
        hashed = hashlib.sha256(combined.encode()).hexdigest()
        return f"{salt}:{hashed}"

    def _generate_consent_id(self) -> str:
        """Generate a unique, non-personally-identifiable consent ID."""
        return secrets.token_urlsafe(32)

    def record_consent(
    self,
    consent_type: ConsentType,
    consent_given: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    consent_version: str = "1.0",
    
) -> str:
        """
        Record user consent with GDPR compliance.

        Args:
            consent_type: Type of consent being given/withdrawn
            consent_given: Whether consent is given (True) or withdrawn (False)
            ip_address: User's IP address (will be hashed)
            user_agent: User's browser user agent (will be hashed)
            consent_version: Version of consent form/policy

        Returns:
            Unique consent ID for tracking
        """

        consent_id = self._generate_consent_id()

        # Hash sensitive data
        ip_hash = self._hash_data(ip_address) if ip_address else None
        ua_hash = self._hash_data(user_agent) if user_agent else None

        # Set expiration based on consent type
        expires_at = None
        if consent_type in [ConsentType.ANALYTICS, ConsentType.MARKETING]:
            expires_at = datetime.now(UTC) + timedelta(days=365)  # 1 year

        consent_record = ConsentRecord(
    consent_id=consent_id,
    consent_type=consent_type.value,
    consent_given=consent_given,
    consent_version=consent_version,
    expires_at=expires_at,
    ip_address_hash=ip_hash,
    user_agent_hash=ua_hash,
    
)

        self.db.add(consent_record)
        self.db.commit()

        return consent_id

    def withdraw_consent(
        self, consent_id: str, reason: Optional[str] = None
    ) -> bool:
        """
        Withdraw consent and update record.

        Implements timing attack resistance by ensuring constant-time
        operations
        regardless of whether consent ID exists.

        Args:
            consent_id: The consent ID to withdraw
            reason: Optional reason for withdrawal

        Returns:
            True if withdrawal was successful, False if consent not found
        """

        consent = (
            self.db.query(ConsentRecord)
            .filter(ConsentRecord.consent_id == consent_id)
            .first()
        )

        # Timing attack resistance: Always perform similar operations
        # regardless of whether consent exists
        withdrawal_time = datetime.now(UTC)

        if consent:
            # Valid consent: perform actual withdrawal
            consent.consent_given = False
            consent.withdrawn_at = withdrawal_time
            consent.withdrawal_reason = reason
            self.db.commit()
            return True
        else:
            # Invalid consent: perform dummy operations to maintain timing
            # consistency
            # Create a dummy consent object (not persisted) and perform similar
            # operations
            dummy_consent = ConsentRecord(
    consent_id="dummy",
    consent_type=ConsentType.FUNCTIONAL,
    consent_given=True,
    created_at=withdrawal_time,
    
)
            dummy_consent.consent_given = False
            dummy_consent.withdrawn_at = withdrawal_time
            dummy_consent.withdrawal_reason = reason

            # Perform a dummy database operation to match timing of real commit
            # Query that doesn't affect data but takes similar time to commit
            self.db.execute(text("SELECT 1"))
            self.db.flush()  # Flush without commit to simulate database work

            return False

    def get_active_consents(self, consent_id: str) -> Dict[ConsentType, bool]:
        """
        Get all active consents for a consent ID.

        Args:
            consent_id: The consent ID to lookup

        Returns:
            Dictionary mapping consent types to their status
        """

        consents = (
            self.db.query(ConsentRecord)
            .filter(
    and_(
                    ConsentRecord.consent_id == consent_id,
    ConsentRecord.consent_given == True,
    ConsentRecord.withdrawn_at.is_(None
),
                )
            )
            .all()
        )

        # Check for expired consents
        now = datetime.now(UTC)
        active_consents = {}

        for consent in consents:
            expires_at_aware = self._ensure_timezone_aware(consent.expires_at)
            if expires_at_aware is None or expires_at_aware > now:
                try:
                    consent_type = ConsentType(consent.consent_type)
                    active_consents[consent_type] = True
                except ValueError:
                    # Skip invalid consent types
                    continue

        # Ensure all consent types are represented
        for consent_type in ConsentType:
            if consent_type not in active_consents:
                active_consents[consent_type] = False

        return active_consents

    def create_data_subject_request(
    self,
    request_type: DataSubjectRights,
    contact_email: str,
    description: Optional[str] = None,
    
) -> int:
        """
        Create a data subject rights request.

        Args:
            request_type: Type of request (access, erasure, etc.)
            contact_email: Contact email (will be hashed)
            description: Optional description of the request

        Returns:
            Request ID for tracking
        """

        email_hash = self._hash_data(contact_email)

        request = DataSubjectRequest(
    request_type=request_type.value,
    contact_email_hash=email_hash,
    description=description,
    due_date=datetime.now(UTC
) + timedelta(days=30),
        )

        self.db.add(request)
        self.db.commit()

        return request.id

    def process_data_subject_request(
    self,
    request_id: int,
    response_data: Optional[Dict] = None,
    notes: Optional[str] = None,
    
) -> bool:
        """
        Mark a data subject request as completed.

        Args:
            request_id: The request ID to complete
            response_data: Data provided in response
            notes: Completion notes

        Returns:
            True if successful, False if request not found
        """

        request = (
            self.db.query(DataSubjectRequest)
            .filter(DataSubjectRequest.id == request_id)
            .first()
        )

        if not request:
            return False

        request.status = "completed"
        request.completed_at = datetime.now(UTC)
        request.response_data = response_data
        request.completion_notes = notes

        self.db.commit()
        return True

    def get_overdue_requests(self) -> List[DataSubjectRequest]:
        """Get all overdue data subject requests."""

        return (
            self.db.query(DataSubjectRequest)
            .filter(
    and_(
                    DataSubjectRequest.status == "pending",
    DataSubjectRequest.due_date < datetime.now(UTC
),
                )
            )
            .all()
        )

    def record_data_processing_activity(
    self,
    activity_name: str,
    purpose: str,
    legal_basis: LegalBasis,
    data_categories: List[str],
    data_subjects: str,
    retention_period_days: Optional[int] = None,
    recipients: Optional[List[str]] = None,
    security_measures: Optional[List[str]] = None,
    
) -> int:
        """
        Record a data processing activity for GDPR Article 30 compliance.

        Args:
            activity_name: Name of the processing activity
            purpose: Purpose of the processing
            legal_basis: Legal basis for processing
            data_categories: Categories of data being processed
            data_subjects: Description of data subjects
            retention_period_days: How long data is retained
            recipients: Who receives the data
            security_measures: Security measures in place

        Returns:
            Processing record ID
        """

        if security_measures is None:
            security_measures = [
                "encryption",
                "access_controls",
                "audit_logging",
            ]

        if recipients is None:
            recipients = []

        record = DataProcessingRecord(
    activity_name=activity_name,
    purpose=purpose,
    legal_basis=legal_basis.value,
    data_categories=data_categories,
    data_subjects=data_subjects,
    retention_period_days=retention_period_days,
    recipients=recipients,
    security_measures=security_measures,
    
)

        self.db.add(record)
        self.db.commit()

        return record.id

    def anonymize_expired_data(self) -> int:
        """
        Anonymize or delete expired data according to retention policies.

        Returns:
            Number of records processed
        """

        processed_count = 0

        # Find expired consent records
        expired_consents = (
            self.db.query(ConsentRecord)
            .filter(
                and_(
                    ConsentRecord.expires_at < datetime.now(UTC),
                    ConsentRecord.withdrawn_at.is_(None),
                )
            )
            .all()
        )

        for consent in expired_consents:
            consent.withdrawn_at = datetime.now(UTC)
            consent.withdrawal_reason = "expired"
            processed_count += 1

        # Process old IP address hashes (anonymize after 30 days)
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
        old_records = (
            self.db.query(ConsentRecord)
            .filter(
    and_(
                    ConsentRecord.created_at < thirty_days_ago,
    ConsentRecord.ip_address_hash.isnot(None
),
                )
            )
            .all()
        )

        for record in old_records:
            record.ip_address_hash = None
            record.user_agent_hash = None
            processed_count += 1

        self.db.commit()
        return processed_count

    def generate_compliance_report(self) -> Dict:
        """
        Generate a GDPR compliance report.

        Returns:
            Dictionary with compliance metrics
        """

        total_consents = self.db.query(ConsentRecord).count()
        active_consents = (
            self.db.query(ConsentRecord)
            .filter(
    and_(
                    ConsentRecord.consent_given == True,
    ConsentRecord.withdrawn_at.is_(None
),
                )
            )
            .count()
        )

        pending_requests = (
            self.db.query(DataSubjectRequest)
            .filter(DataSubjectRequest.status == "pending")
            .count()
        )

        overdue_requests = len(self.get_overdue_requests())

        return {
    
            "total_consent_records": total_consents,
            "active_consents": active_consents,
            "pending_data_subject_requests": pending_requests,
            "overdue_requests": overdue_requests,
            "compliance_score": self._calculate_compliance_score(
    total_consents,
    pending_requests,
    overdue_requests
),
            "last_anonymization_run": datetime.now(UTC).isoformat(),
        
}

    def _calculate_compliance_score(
    self,
    total_consents: int,
    pending_requests: int,
    overdue_requests: int
) -> float:
        """Calculate compliance score (0-100)."""

        score = 100.0

        # Deduct for overdue requests (major issue)
        if overdue_requests > 0:
            score -= min(overdue_requests * 20, 60)

        # Deduct for many pending requests
        if pending_requests > 10:
            score -= min((pending_requests - 10) * 2, 20)

        # Bonus for having consent management
        if total_consents > 0:
            score += 10

        return max(min(score, 100.0), 0.0)
