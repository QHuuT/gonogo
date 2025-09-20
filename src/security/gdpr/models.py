"""
GDPR compliance models for data tracking and consent management.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ConsentType(str, Enum):
    """Types of consent that can be given."""
    ESSENTIAL = "essential"
    FUNCTIONAL = "functional"
    ANALYTICS = "analytics"
    MARKETING = "marketing"


class LegalBasis(str, Enum):
    """Legal basis for data processing under GDPR."""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class DataSubjectRights(str, Enum):
    """GDPR Data Subject Rights."""
    ACCESS = "access"              # Article 15
    RECTIFICATION = "rectification"  # Article 16
    ERASURE = "erasure"           # Article 17
    RESTRICT = "restrict"         # Article 18
    PORTABILITY = "portability"   # Article 20
    OBJECT = "object"             # Article 21


class ConsentRecord(Base):
    """Store user consent preferences with GDPR compliance."""

    __tablename__ = "consent_records"

    id = Column(Integer, primary_key=True)

    # Anonymized identifier (not personally identifiable)
    consent_id = Column(String(64), unique=True, nullable=False, index=True)

    # Consent details
    consent_type = Column(String(20), nullable=False)
    consent_given = Column(Boolean, nullable=False)
    consent_version = Column(String(10), nullable=False, default="1.0")

    # Timestamps for GDPR compliance
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Withdrawal tracking
    withdrawn_at = Column(DateTime, nullable=True)
    withdrawal_reason = Column(String(100), nullable=True)

    # Audit trail
    ip_address_hash = Column(String(64), nullable=True)  # Hashed IP for security
    user_agent_hash = Column(String(64), nullable=True)   # Hashed for fingerprinting prevention


class DataProcessingRecord(Base):
    """Track data processing activities for GDPR Article 30."""

    __tablename__ = "data_processing_records"

    id = Column(Integer, primary_key=True)

    # Processing details
    activity_name = Column(String(100), nullable=False)
    purpose = Column(Text, nullable=False)
    legal_basis = Column(String(30), nullable=False)

    # Data categories
    data_categories = Column(JSON, nullable=False)  # List of data types processed
    data_subjects = Column(String(100), nullable=False)  # Who the data is about

    # Recipients and transfers
    recipients = Column(JSON, nullable=True)  # Who receives the data
    third_country_transfers = Column(JSON, nullable=True)  # International transfers

    # Retention and security
    retention_period_days = Column(Integer, nullable=True)
    security_measures = Column(JSON, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DataSubjectRequest(Base):
    """Track GDPR data subject rights requests."""

    __tablename__ = "data_subject_requests"

    id = Column(Integer, primary_key=True)

    # Request details
    request_type = Column(String(20), nullable=False)  # DataSubjectRights enum
    status = Column(String(20), nullable=False, default="pending")

    # Contact information (encrypted)
    contact_email_hash = Column(String(64), nullable=False)  # Hashed for privacy

    # Request specifics
    description = Column(Text, nullable=True)
    requested_data = Column(JSON, nullable=True)  # What data is requested

    # Processing
    response_data = Column(JSON, nullable=True)  # Response provided
    completion_notes = Column(Text, nullable=True)

    # Timestamps (GDPR requires 30-day response time)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.due_date:
            self.due_date = self.created_at + timedelta(days=30)


# Pydantic models for API

class ConsentRequest(BaseModel):
    """Request model for consent submission."""
    consent_type: ConsentType
    consent_given: bool
    consent_version: str = "1.0"


class ConsentResponse(BaseModel):
    """Response model for consent operations."""
    consent_id: str
    consent_type: ConsentType
    consent_given: bool
    created_at: datetime
    expires_at: Optional[datetime] = None


class DataSubjectRequestCreate(BaseModel):
    """Request model for data subject rights requests."""
    request_type: DataSubjectRights
    contact_email: str
    description: Optional[str] = None

    class Config:
        use_enum_values = True


class DataSubjectRequestResponse(BaseModel):
    """Response model for data subject rights requests."""
    request_id: int
    request_type: DataSubjectRights
    status: str
    created_at: datetime
    due_date: datetime

    class Config:
        use_enum_values = True
        from_attributes = True


class GDPRCompliance(BaseModel):
    """Model for GDPR compliance status."""

    consent_records_count: int
    active_consents: Dict[ConsentType, int]
    pending_requests: int
    overdue_requests: int
    retention_policy_compliant: bool
    last_audit_date: Optional[datetime] = None

    @classmethod
    def calculate_compliance_score(cls,
                                 consent_records: int,
                                 pending_requests: int,
                                 overdue_requests: int) -> float:
        """Calculate a GDPR compliance score (0-100)."""

        score = 100.0

        # Deduct points for overdue requests
        if overdue_requests > 0:
            score -= min(overdue_requests * 10, 50)  # Max 50 point deduction

        # Deduct points for too many pending requests
        if pending_requests > 5:
            score -= min((pending_requests - 5) * 5, 25)  # Max 25 point deduction

        return max(score, 0.0)