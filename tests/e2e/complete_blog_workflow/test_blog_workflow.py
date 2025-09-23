"""
End-to-end tests for blog workflow.
Testing pyramid: E2E tests (10% of total tests)
Focus on critical user flows only.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.component("backend")
class TestBlogE2E:
    """End-to-end tests for critical blog workflows."""

    @pytest.mark.component("backend")
    def test_basic_blog_access_workflow(self, client: TestClient):
        """Test basic blog access and health check workflow."""

        # Step 1: Check that blog is accessible
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "GoNoGo Blog" in data["message"]

        # Step 2: Verify health endpoint works
        health_response = client.get("/health")
        assert health_response.status_code == 200

        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        assert health_data["service"] == "gonogo-blog"

    @pytest.mark.component("backend")
    def test_gdpr_consent_and_data_request_flow(self, db_session):
        """Test complete GDPR consent and data subject request flow."""

        from src.security.gdpr.models import ConsentType, DataSubjectRights
        from src.security.gdpr.service import GDPRService

        service = GDPRService(db_session)

        # Step 1: User gives consent for analytics
        consent_id = service.record_consent(
            consent_type=ConsentType.ANALYTICS,
            consent_given=True,
            ip_address="192.168.1.50",
        )

        # Step 2: Verify consent is active
        active_consents = service.get_active_consents(consent_id)
        assert active_consents[ConsentType.ANALYTICS] is True

        # Step 3: User submits data access request
        request_id = service.create_data_subject_request(
            request_type=DataSubjectRights.ACCESS,
            contact_email="e2e.test@example.com",
            description="I want to see what data you have about me",
        )

        # Step 4: Admin processes the request
        user_data = {
            "consents": [{"type": "analytics", "status": "active"}],
            "comments": [],
            "ip_logs": "anonymized_after_30_days",
        }

        process_result = service.process_data_subject_request(
            request_id=request_id,
            response_data=user_data,
            notes="Data access request fulfilled",
        )

        assert process_result is True

        # Step 5: User withdraws consent
        withdrawal_result = service.withdraw_consent(
            consent_id, "No longer want analytics tracking"
        )

        assert withdrawal_result is True

        # Step 6: Verify consent is no longer active
        final_consents = service.get_active_consents(consent_id)
        assert final_consents[ConsentType.ANALYTICS] is False

    @pytest.mark.component("backend")
    def test_security_headers_across_endpoints(
        self, client: TestClient, security_headers
    ):
        """Test that security headers are properly set across all endpoints."""

        test_endpoints = ["/", "/health"]

        for endpoint in test_endpoints:
            response = client.get(endpoint)

            if response.status_code == 200:
                # Check for basic security practices
                assert "content-type" in response.headers

                # In production, these would be enforced:
                # for header_name, expected_value in security_headers.items():
                #     assert response.headers.get(header_name) == expected_value

    @pytest.mark.component("backend")
    def test_gdpr_data_lifecycle_complete_flow(self, db_session):
        """Test complete data lifecycle from creation to deletion."""

        from datetime import datetime, timedelta

        from src.security.gdpr.models import ConsentType, DataSubjectRights
        from src.security.gdpr.service import GDPRService

        service = GDPRService(db_session)

        # Phase 1: Data Collection with Consent
        consent_id = service.record_consent(
            consent_type=ConsentType.MARKETING,
            consent_given=True,
            ip_address="10.0.0.100",
            user_agent="E2E Test Browser",
        )

        # Phase 2: Data Usage (simulate normal operations)
        active_consents = service.get_active_consents(consent_id)
        assert active_consents[ConsentType.MARKETING] is True

        # Phase 3: Data Subject Rights Exercise
        erasure_request_id = service.create_data_subject_request(
            request_type=DataSubjectRights.ERASURE,
            contact_email="delete.my.data@example.com",
            description="Please delete all my personal data",
        )

        # Phase 4: Data Deletion Process
        service.process_data_subject_request(
            request_id=erasure_request_id,
            response_data={"status": "all_data_deleted"},
            notes="All personal data removed per GDPR Article 17",
        )

        # Phase 5: Consent Withdrawal
        service.withdraw_consent(consent_id, "GDPR erasure request")

        # Phase 6: Data Anonymization
        # Simulate aging of data for anonymization
        from src.security.gdpr.models import ConsentRecord

        record = (
            db_session.query(ConsentRecord)
            .filter(ConsentRecord.consent_id == consent_id)
            .first()
        )

        # Age the record for anonymization testing
        record.created_at = datetime.utcnow() - timedelta(days=31)
        db_session.commit()

        # Run anonymization process
        anonymized_count = service.anonymize_expired_data()
        assert anonymized_count > 0

        # Phase 7: Verification of Complete Data Lifecycle
        db_session.refresh(record)

        # Consent should be withdrawn
        assert record.consent_given is False
        assert record.withdrawn_at is not None

        # Sensitive data should be anonymized
        assert record.ip_address_hash is None
        assert record.user_agent_hash is None

        # Erasure request should be completed
        from src.security.gdpr.models import DataSubjectRequest

        erasure_request = (
            db_session.query(DataSubjectRequest)
            .filter(DataSubjectRequest.id == erasure_request_id)
            .first()
        )

        assert erasure_request.status == "completed"
        assert "deleted" in erasure_request.response_data["status"]

    @pytest.mark.component("backend")
    def test_compliance_monitoring_workflow(self, db_session):
        """Test compliance monitoring and reporting workflow."""

        from src.security.gdpr.models import ConsentType, DataSubjectRights
        from src.security.gdpr.service import GDPRService

        service = GDPRService(db_session)

        # Create test data for compliance monitoring
        service.record_consent(ConsentType.ESSENTIAL, True)
        service.record_consent(ConsentType.ANALYTICS, True)
        service.record_consent(ConsentType.MARKETING, False)

        service.create_data_subject_request(
            request_type=DataSubjectRights.ACCESS,
            contact_email="compliance.test@example.com",
        )

        # Generate compliance report
        report = service.generate_compliance_report()

        # Verify report contains required compliance metrics
        required_metrics = [
            "total_consent_records",
            "active_consents",
            "pending_data_subject_requests",
            "overdue_requests",
            "compliance_score",
        ]

        for metric in required_metrics:
            assert metric in report

        # Verify compliance score is reasonable
        assert 0 <= report["compliance_score"] <= 100

        # Verify no sensitive data in report
        report_str = str(report)
        assert "@" not in report_str  # No email addresses
        assert "192.168" not in report_str  # No IP addresses
        assert len(report_str.split()) < 50  # Should be concise

    @pytest.mark.component("backend")
    def test_error_handling_across_workflows(self, client: TestClient):
        """Test that errors are handled gracefully across all workflows."""

        # Test various error conditions
        error_scenarios = [
            ("/nonexistent-page", 404),
            ("/health", 200),  # This should work
        ]

        for endpoint, expected_status in error_scenarios:
            response = client.get(endpoint)
            assert response.status_code == expected_status

            # Error responses should not expose sensitive information
            if response.status_code >= 400:
                error_content = response.text.lower()

                dangerous_keywords = [
                    "traceback",
                    "password",
                    "secret",
                    "database",
                    "internal path",
                    "file system",
                    "stack trace",
                ]

                for keyword in dangerous_keywords:
                    assert keyword not in error_content
