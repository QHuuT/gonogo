"""
Integration tests for GDPR compliance.
Testing pyramid: Integration tests (20% of total tests)
"""

import pytest
from datetime import datetime, timedelta

from src.security.gdpr.models import ConsentType, DataSubjectRights
from src.security.gdpr.service import GDPRService


class TestGDPRIntegration:
    """Integration tests for GDPR service with database."""

    def test_full_consent_lifecycle(self, db_session):
        """Test complete consent lifecycle: record -> query -> withdraw."""

        service = GDPRService(db_session)

        # Step 1: Record consent
        consent_id = service.record_consent(
            consent_type=ConsentType.ANALYTICS,
            consent_given=True,
            ip_address="192.168.1.100"
        )

        # Step 2: Verify consent is active
        active_consents = service.get_active_consents(consent_id)
        assert active_consents[ConsentType.ANALYTICS] is True
        assert active_consents[ConsentType.MARKETING] is False  # Not given

        # Step 3: Withdraw consent
        withdrawal_result = service.withdraw_consent(
            consent_id,
            "User requested data deletion"
        )
        assert withdrawal_result is True

        # Step 4: Verify consent is no longer active
        active_consents_after = service.get_active_consents(consent_id)
        assert active_consents_after[ConsentType.ANALYTICS] is False

    def test_multiple_consent_types_single_user(self, db_session):
        """Test that a user can have multiple consent types."""

        service = GDPRService(db_session)

        # Record multiple consents
        analytics_id = service.record_consent(
            consent_type=ConsentType.ANALYTICS,
            consent_given=True
        )

        marketing_id = service.record_consent(
            consent_type=ConsentType.MARKETING,
            consent_given=True
        )

        functional_id = service.record_consent(
            consent_type=ConsentType.FUNCTIONAL,
            consent_given=False  # Explicitly denied
        )

        # Verify each consent independently
        analytics_consents = service.get_active_consents(analytics_id)
        assert analytics_consents[ConsentType.ANALYTICS] is True

        marketing_consents = service.get_active_consents(marketing_id)
        assert marketing_consents[ConsentType.MARKETING] is True

        functional_consents = service.get_active_consents(functional_id)
        assert functional_consents[ConsentType.FUNCTIONAL] is False

    def test_data_subject_request_full_workflow(self, db_session):
        """Test complete data subject request workflow."""

        service = GDPRService(db_session)

        # Step 1: Create request
        request_id = service.create_data_subject_request(
            request_type=DataSubjectRights.ACCESS,
            contact_email="integration.test@example.com",
            description="I need access to all my personal data for review"
        )

        # Step 2: Verify request was created properly
        from src.security.gdpr.models import DataSubjectRequest
        request = db_session.query(DataSubjectRequest).filter(
            DataSubjectRequest.id == request_id
        ).first()

        assert request is not None
        assert request.status == "pending"
        assert request.request_type == DataSubjectRights.ACCESS.value
        assert request.due_date > datetime.utcnow()

        # Step 3: Process the request
        response_data = {
            "personal_data": {
                "comments": [],
                "consents": ["analytics"],
                "ip_access_logs": "anonymized"
            },
            "data_sources": ["comments_table", "consent_records"],
            "export_date": datetime.utcnow().isoformat()
        }

        process_result = service.process_data_subject_request(
            request_id=request_id,
            response_data=response_data,
            notes="Data exported successfully to secure download link"
        )

        assert process_result is True

        # Step 4: Verify completion
        db_session.refresh(request)
        assert request.status == "completed"
        assert request.completed_at is not None
        assert request.response_data == response_data

    def test_anonymization_workflow(self, db_session):
        """Test data anonymization workflow for expired data."""

        service = GDPRService(db_session)

        # Create consent with IP address
        consent_id = service.record_consent(
            consent_type=ConsentType.FUNCTIONAL,
            consent_given=True,
            ip_address="10.0.0.1",
            user_agent="Test Browser 1.0"
        )

        # Manually age the record for testing
        from src.security.gdpr.models import ConsentRecord
        record = db_session.query(ConsentRecord).filter(
            ConsentRecord.consent_id == consent_id
        ).first()

        original_ip_hash = record.ip_address_hash
        original_ua_hash = record.user_agent_hash

        # Set creation date to 31 days ago
        record.created_at = datetime.utcnow() - timedelta(days=31)
        db_session.commit()

        # Run anonymization
        processed_count = service.anonymize_expired_data()

        assert processed_count > 0

        # Verify IP and UA were anonymized
        db_session.refresh(record)
        assert record.ip_address_hash is None
        assert record.user_agent_hash is None

    def test_overdue_requests_detection(self, db_session):
        """Test detection of overdue data subject requests."""

        service = GDPRService(db_session)

        # Create a request
        request_id = service.create_data_subject_request(
            request_type=DataSubjectRights.ERASURE,
            contact_email="overdue.test@example.com"
        )

        # Make it overdue
        from src.security.gdpr.models import DataSubjectRequest
        request = db_session.query(DataSubjectRequest).filter(
            DataSubjectRequest.id == request_id
        ).first()

        request.due_date = datetime.utcnow() - timedelta(days=5)  # 5 days overdue
        db_session.commit()

        # Check overdue detection
        overdue_requests = service.get_overdue_requests()

        assert len(overdue_requests) >= 1
        overdue_ids = [req.id for req in overdue_requests]
        assert request_id in overdue_ids

    def test_compliance_report_generation(self, db_session):
        """Test generation of comprehensive compliance report."""

        service = GDPRService(db_session)

        # Create test data
        service.record_consent(ConsentType.ANALYTICS, True)
        service.record_consent(ConsentType.MARKETING, True)
        service.record_consent(ConsentType.FUNCTIONAL, False)

        request_id = service.create_data_subject_request(
            request_type=DataSubjectRights.ACCESS,
            contact_email="report.test@example.com"
        )

        # Generate report
        report = service.generate_compliance_report()

        # Verify report structure
        assert "total_consent_records" in report
        assert "active_consents" in report
        assert "pending_data_subject_requests" in report
        assert "overdue_requests" in report
        assert "compliance_score" in report

        # Verify report data
        assert report["total_consent_records"] >= 3
        assert report["active_consents"] >= 2  # analytics and marketing
        assert report["pending_data_subject_requests"] >= 1
        assert 0 <= report["compliance_score"] <= 100

    def test_gdpr_data_processing_record_creation(self, db_session):
        """Test creation of data processing records for Article 30 compliance."""

        service = GDPRService(db_session)

        from src.security.gdpr.models import LegalBasis

        # Record a data processing activity
        activity_id = service.record_data_processing_activity(
            activity_name="Blog Comment Processing",
            purpose="Enable user comments on blog posts",
            legal_basis=LegalBasis.CONSENT,
            data_categories=["name", "email", "comment_content", "timestamp"],
            data_subjects="Blog visitors who choose to comment",
            retention_period_days=1095,  # 3 years
            recipients=["Blog administrators", "Comment moderation service"],
            security_measures=["encryption", "access_controls", "audit_logging", "data_minimization"]
        )

        assert activity_id is not None

        # Verify the record was created
        from src.security.gdpr.models import DataProcessingRecord
        record = db_session.query(DataProcessingRecord).filter(
            DataProcessingRecord.id == activity_id
        ).first()

        assert record is not None
        assert record.activity_name == "Blog Comment Processing"
        assert record.legal_basis == LegalBasis.CONSENT.value
        assert "email" in record.data_categories
        assert record.retention_period_days == 1095

    def test_consent_expiration_handling(self, db_session):
        """Test that expired consents are properly handled."""

        service = GDPRService(db_session)

        # Create consent that expires
        consent_id = service.record_consent(
            consent_type=ConsentType.MARKETING,
            consent_given=True
        )

        # Manually expire the consent for testing
        from src.security.gdpr.models import ConsentRecord
        record = db_session.query(ConsentRecord).filter(
            ConsentRecord.consent_id == consent_id
        ).first()

        # Set expiration to yesterday
        record.expires_at = datetime.utcnow() - timedelta(days=1)
        db_session.commit()

        # Check that expired consent is not active
        active_consents = service.get_active_consents(consent_id)
        assert active_consents[ConsentType.MARKETING] is False

        # Run anonymization to clean up expired consents
        processed_count = service.anonymize_expired_data()
        assert processed_count > 0

        # Verify the consent was marked as withdrawn
        db_session.refresh(record)
        assert record.withdrawn_at is not None
        assert record.withdrawal_reason == "expired"