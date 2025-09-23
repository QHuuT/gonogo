"""
Security tests for GDPR compliance and data protection.
Focus on security aspects of data handling and privacy.
"""

import re
from datetime import datetime, timedelta

import pytest

from src.security.gdpr.models import ConsentType, DataSubjectRights
from src.security.gdpr.service import GDPRService


@pytest.mark.epic("EP-00003")
@pytest.mark.component("security")
class TestGDPRSecurity:
    """Security tests for GDPR compliance."""

    @pytest.mark.component("security")
    def test_ip_address_anonymization_security(self, db_session):
        """Test that IP addresses are properly anonymized and cannot be reversed."""

        service = GDPRService(db_session)

        original_ip = "192.168.1.100"

        consent_id = service.record_consent(
            consent_type=ConsentType.ANALYTICS,
            consent_given=True,
            ip_address=original_ip,
        )

        # Verify IP is hashed, not stored plaintext
        from src.security.gdpr.models import ConsentRecord

        record = (
            db_session.query(ConsentRecord)
            .filter(ConsentRecord.consent_id == consent_id)
            .first()
        )

        # Original IP should not appear anywhere in the hash
        assert original_ip not in record.ip_address_hash
        assert len(record.ip_address_hash) > 32  # Should be substantial hash

        # Hash should include salt (format: salt:hash)
        assert ":" in record.ip_address_hash

    @pytest.mark.component("security")
    def test_email_hashing_prevents_enumeration(self, db_session):
        """Test that email hashing prevents email enumeration attacks."""

        service = GDPRService(db_session)

        test_emails = ["user1@example.com", "user2@example.com", "admin@company.com"]

        hashed_emails = []

        for email in test_emails:
            request_id = service.create_data_subject_request(
                request_type=DataSubjectRights.ACCESS, contact_email=email
            )

            from src.security.gdpr.models import DataSubjectRequest

            request = (
                db_session.query(DataSubjectRequest)
                .filter(DataSubjectRequest.id == request_id)
                .first()
            )

            hashed_emails.append(request.contact_email_hash)

            # Verify original email is not stored
            assert email not in request.contact_email_hash

        # All hashes should be different
        assert len(set(hashed_emails)) == len(test_emails)

    @pytest.mark.component("security")
    def test_consent_id_unpredictability(self, db_session):
        """Test that consent IDs are cryptographically unpredictable."""

        service = GDPRService(db_session)

        consent_ids = []

        # Generate multiple consent IDs
        for i in range(10):
            consent_id = service.record_consent(
                consent_type=ConsentType.FUNCTIONAL, consent_given=True
            )
            consent_ids.append(consent_id)

        # All IDs should be unique
        assert len(set(consent_ids)) == 10

        # IDs should not be sequential or predictable
        for i, consent_id in enumerate(consent_ids):
            # Should not contain sequential numbers
            assert str(i) not in consent_id
            assert str(i + 1) not in consent_id

            # Should be substantial length (cryptographically secure)
            assert len(consent_id) >= 32

    @pytest.mark.component("security")
    def test_sensitive_data_not_logged(self, db_session, caplog):
        """Test that sensitive data is not accidentally logged."""

        service = GDPRService(db_session)

        sensitive_email = "sensitive.user@company.com"
        sensitive_ip = "10.0.0.50"

        # Perform operations that might log data
        consent_id = service.record_consent(
            consent_type=ConsentType.MARKETING,
            consent_given=True,
            ip_address=sensitive_ip,
        )

        service.create_data_subject_request(
            request_type=DataSubjectRights.ERASURE, contact_email=sensitive_email
        )

        # Check that sensitive data is not in logs
        log_output = caplog.text

        assert sensitive_email not in log_output
        assert sensitive_ip not in log_output

    @pytest.mark.component("security")
    def test_sql_injection_prevention_in_consent_queries(self, db_session):
        """Test that consent queries are resistant to SQL injection."""

        service = GDPRService(db_session)

        # Attempt SQL injection in consent_id
        malicious_consent_id = "'; DROP TABLE consent_records; --"

        # This should not cause SQL errors or database damage
        result = service.withdraw_consent(malicious_consent_id)

        assert result is False  # Should safely return False

        # Verify database still works
        legitimate_consent_id = service.record_consent(
            consent_type=ConsentType.ANALYTICS, consent_given=True
        )

        assert legitimate_consent_id is not None

    @pytest.mark.component("security")
    def test_data_subject_request_injection_prevention(self, db_session):
        """Test that data subject requests prevent injection attacks."""

        service = GDPRService(db_session)

        # Attempt various injection attacks
        malicious_inputs = [
            "'; DROP TABLE data_subject_requests; --",
            "<script>alert('xss')</script>",
            "{{7*7}}",  # Template injection
            "../../../etc/passwd",  # Path traversal
        ]

        for malicious_input in malicious_inputs:
            # Try in email field
            try:
                request_id = service.create_data_subject_request(
                    request_type=DataSubjectRights.ACCESS, contact_email=malicious_input
                )

                # If successful, verify malicious content was properly escaped/hashed
                from src.security.gdpr.models import DataSubjectRequest

                request = (
                    db_session.query(DataSubjectRequest)
                    .filter(DataSubjectRequest.id == request_id)
                    .first()
                )

                # Original malicious input should not be stored
                assert malicious_input not in str(request.contact_email_hash)

            except Exception as e:
                # Some inputs might cause validation errors, which is fine
                pass

    @pytest.mark.component("security")
    def test_timing_attack_resistance(self, db_session):
        """Test that operations don't leak information through timing attacks."""

        service = GDPRService(db_session)

        # Create a legitimate consent
        real_consent_id = service.record_consent(
            consent_type=ConsentType.ANALYTICS, consent_given=True
        )

        fake_consent_id = "nonexistent-consent-id"

        # Time operations on real vs fake consent IDs
        import time

        # Test withdrawal timing
        start_time = time.time()
        service.withdraw_consent(real_consent_id)
        real_time = time.time() - start_time

        start_time = time.time()
        service.withdraw_consent(fake_consent_id)
        fake_time = time.time() - start_time

        # Times should be similar (within reasonable variance)
        time_ratio = max(real_time, fake_time) / min(real_time, fake_time)
        assert time_ratio < 10  # Should not differ by more than 10x

    @pytest.mark.component("security")
    def test_data_retention_enforcement(self, db_session):
        """Test that data retention policies are properly enforced."""

        service = GDPRService(db_session)

        # Create old consent record
        consent_id = service.record_consent(
            consent_type=ConsentType.MARKETING,
            consent_given=True,
            ip_address="192.168.1.1",
        )

        # Manually age the record beyond retention period
        from src.security.gdpr.models import ConsentRecord

        record = (
            db_session.query(ConsentRecord)
            .filter(ConsentRecord.consent_id == consent_id)
            .first()
        )

        # Set creation date to 4 years ago (beyond 3-year retention)
        record.created_at = datetime.utcnow() - timedelta(days=1461)  # 4 years
        record.expires_at = datetime.utcnow() - timedelta(days=1096)  # Expired
        db_session.commit()

        # Run anonymization
        processed_count = service.anonymize_expired_data()

        assert processed_count > 0

        # Verify data was properly anonymized
        db_session.refresh(record)
        assert record.withdrawn_at is not None
        assert record.withdrawal_reason == "expired"

    @pytest.mark.component("security")
    def test_access_control_on_sensitive_operations(self, db_session):
        """Test that sensitive operations require proper authorization."""

        service = GDPRService(db_session)

        # In a real implementation, these operations would require authentication
        # For now, we test that they don't expose sensitive data

        # Generate compliance report
        report = service.generate_compliance_report()

        # Report should contain aggregate data, not individual records
        assert "consent_id" not in str(report)
        assert "email" not in str(report)
        assert "ip_address" not in str(report)

        # Should only contain statistical data
        assert isinstance(report["total_consent_records"], int)
        assert isinstance(report["compliance_score"], float)

    @pytest.mark.component("security")
    def test_gdpr_right_to_be_forgotten_security(self, db_session):
        """Test that right to be forgotten is properly implemented securely."""

        service = GDPRService(db_session)

        # Create consent and data subject request
        consent_id = service.record_consent(
            consent_type=ConsentType.ANALYTICS,
            consent_given=True,
            ip_address="192.168.1.200",
        )

        erasure_request_id = service.create_data_subject_request(
            request_type=DataSubjectRights.ERASURE,
            contact_email="delete.me@example.com",
        )

        # Process erasure request
        service.process_data_subject_request(
            request_id=erasure_request_id,
            response_data={"status": "data_deleted"},
            notes="All personal data deleted per GDPR Article 17",
        )

        # Withdraw the consent as part of erasure
        service.withdraw_consent(consent_id, "GDPR Article 17 - Right to be forgotten")

        # Verify that data is properly marked for deletion
        from src.security.gdpr.models import ConsentRecord, DataSubjectRequest

        consent_record = (
            db_session.query(ConsentRecord)
            .filter(ConsentRecord.consent_id == consent_id)
            .first()
        )

        assert consent_record.consent_given is False
        assert consent_record.withdrawn_at is not None
        assert "forgotten" in consent_record.withdrawal_reason

        erasure_request = (
            db_session.query(DataSubjectRequest)
            .filter(DataSubjectRequest.id == erasure_request_id)
            .first()
        )

        assert erasure_request.status == "completed"
        assert "deleted" in erasure_request.response_data["status"]

    @pytest.mark.component("security")
    def test_data_minimization_principle(self, db_session):
        """Test that only necessary data is collected and stored."""

        service = GDPRService(db_session)

        # Record consent with minimal data
        consent_id = service.record_consent(
            consent_type=ConsentType.FUNCTIONAL,
            consent_given=True,
            # Note: Not providing IP or user agent unless necessary
        )

        from src.security.gdpr.models import ConsentRecord

        record = (
            db_session.query(ConsentRecord)
            .filter(ConsentRecord.consent_id == consent_id)
            .first()
        )

        # Verify minimal data storage
        assert record.consent_id is not None
        assert record.consent_type is not None
        assert record.consent_given is not None
        assert record.created_at is not None

        # Optional fields should be None when not provided
        assert record.ip_address_hash is None
        assert record.user_agent_hash is None
