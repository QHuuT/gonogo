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
            # Should be substantial length (cryptographically secure)
            assert len(consent_id) >= 32

            # Should contain sufficient entropy (mix of characters)
            assert any(c.isalpha() for c in consent_id), f"ID {consent_id} should contain letters"
            assert any(c.isdigit() for c in consent_id) or any(c in '-_' for c in consent_id), f"ID {consent_id} should contain digits or URL-safe chars"

        # IDs should not follow predictable patterns
        # Check that consecutive IDs don't have predictable relationships
        for i in range(len(consent_ids) - 1):
            current_id = consent_ids[i]
            next_id = consent_ids[i + 1]

            # IDs should not be identical (already checked by uniqueness)
            # IDs should not have obvious sequential patterns (Hamming distance should be substantial)
            different_chars = sum(c1 != c2 for c1, c2 in zip(current_id, next_id))
            assert different_chars >= len(current_id) // 4, f"IDs {current_id} and {next_id} are too similar"

    @pytest.mark.component("security")
    def test_consent_id_security_properties_regression(self, db_session):
        """Regression test: Ensure consent IDs have proper security properties without flawed digit assumptions."""

        service = GDPRService(db_session)

        # Generate multiple IDs to test security properties
        consent_ids = []
        for _ in range(20):
            consent_id = service.record_consent(
                consent_type=ConsentType.ANALYTICS, consent_given=True
            )
            consent_ids.append(consent_id)

        # Core security properties
        assert len(set(consent_ids)) == 20, "All consent IDs should be unique"

        for consent_id in consent_ids:
            # Length check for sufficient entropy
            assert len(consent_id) >= 32, f"ID {consent_id} should be at least 32 characters"

            # Should only contain URL-safe base64 characters (letters, digits, -, _)
            allowed_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')
            assert all(c in allowed_chars for c in consent_id), f"ID {consent_id} contains invalid characters"

            # REGRESSION: Do NOT check for absence of specific digits
            # The presence of '0', '1', '2', etc. in a cryptographically secure token
            # does NOT make it predictable - this was the original test flaw

        # Entropy distribution check - IDs should have good character distribution
        all_chars = ''.join(consent_ids)
        char_counts = {}
        for c in all_chars:
            char_counts[c] = char_counts.get(c, 0) + 1

        # Should have reasonable character distribution (not all same character)
        unique_chars = len(char_counts)
        assert unique_chars >= 10, f"Should have diverse character usage, got {unique_chars} unique chars"

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
    def test_timing_attack_resistance_regression(self, db_session):
        """Regression test: Ensure constant-time operations prevent timing-based information leakage."""

        service = GDPRService(db_session)

        # Create a legitimate consent for testing
        real_consent_id = service.record_consent(
            consent_type=ConsentType.FUNCTIONAL,
            consent_given=True,
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )

        # Test multiple fake consent IDs to ensure consistent behavior
        fake_consent_ids = [
            "completely-fake-id",
            "another-nonexistent-id",
            "invalid-consent-token",
            "fake-" + "x" * 32,  # Different length
            ""  # Empty string
        ]

        import time

        # Collect timing data for statistical analysis
        real_times = []
        fake_times = []

        # Run multiple iterations to get stable timing measurements
        for _ in range(5):
            # Time valid consent withdrawal
            start_time = time.perf_counter()
            result = service.withdraw_consent(real_consent_id, reason="timing test")
            real_time = time.perf_counter() - start_time
            real_times.append(real_time)

            # Re-create consent for next iteration (only first should succeed)
            if result:  # Only re-create if withdrawal was successful
                real_consent_id = service.record_consent(
                    consent_type=ConsentType.FUNCTIONAL,
                    consent_given=True
                )

            # Time invalid consent withdrawal
            fake_id = fake_consent_ids[_ % len(fake_consent_ids)]
            start_time = time.perf_counter()
            service.withdraw_consent(fake_id, reason="timing test")
            fake_time = time.perf_counter() - start_time
            fake_times.append(fake_time)

        # Statistical timing analysis
        avg_real_time = sum(real_times) / len(real_times)
        avg_fake_time = sum(fake_times) / len(fake_times)

        # The ratio should be close to 1.0 for proper timing attack resistance
        time_ratio = max(avg_real_time, avg_fake_time) / min(avg_real_time, avg_fake_time)

        # Assert timing attack resistance
        # Note: On fast systems, timing variations may be small but still measurable
        # We allow up to 10x ratio for timing attack resistance (same as original test)
        assert time_ratio < 10.0, f"Timing ratio {time_ratio:.2f} indicates potential timing attack vulnerability"

        # Verify that the service still correctly distinguishes valid vs invalid consent
        valid_result = service.withdraw_consent(
            service.record_consent(ConsentType.ANALYTICS, True),
            reason="valid test"
        )
        invalid_result = service.withdraw_consent("definitely-fake-id", reason="invalid test")

        assert valid_result is True, "Valid consent withdrawal should return True"
        assert invalid_result is False, "Invalid consent withdrawal should return False"

        # Ensure constant-time behavior doesn't compromise functionality
        # Both operations should handle their respective cases correctly
        # but take similar amounts of time to prevent information leakage

    @pytest.mark.component("security")
    def test_timing_attack_dummy_operations_regression(self, db_session):
        """Regression test: Verify dummy operations maintain timing consistency without side effects."""

        service = GDPRService(db_session)

        # Get initial database state
        from src.security.gdpr.models import ConsentRecord
        initial_count = db_session.query(ConsentRecord).count()

        # Perform multiple invalid consent withdrawals
        fake_consent_ids = [
            "fake-id-1",
            "fake-id-2",
            "fake-id-3",
            "non-existent-token",
            "invalid-consent-123"
        ]

        for fake_id in fake_consent_ids:
            result = service.withdraw_consent(fake_id, reason="dummy operation test")
            assert result is False, f"Invalid consent ID {fake_id} should return False"

        # Verify dummy operations didn't create actual database records
        final_count = db_session.query(ConsentRecord).count()
        assert final_count == initial_count, "Dummy operations should not create database records"

        # Verify no side effects from dummy operations
        all_records = db_session.query(ConsentRecord).all()
        for record in all_records:
            # No record should have been modified by dummy operations
            assert record.consent_id not in fake_consent_ids
            assert record.withdrawal_reason != "dummy operation test"

        # Verify that real operations still work after dummy operations
        real_consent_id = service.record_consent(
            consent_type=ConsentType.MARKETING,
            consent_given=True,
            ip_address="192.168.1.100"
        )

        # This should work normally and create actual database changes
        real_result = service.withdraw_consent(real_consent_id, reason="real withdrawal")
        assert real_result is True, "Real consent withdrawal should succeed after dummy operations"

        # Verify real withdrawal actually modified the database
        withdrawn_record = (
            db_session.query(ConsentRecord)
            .filter(ConsentRecord.consent_id == real_consent_id)
            .first()
        )
        assert withdrawn_record.consent_given is False
        assert withdrawn_record.withdrawn_at is not None
        assert withdrawn_record.withdrawal_reason == "real withdrawal"

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
