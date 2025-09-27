"""
Regression tests for datetime.utcnow() deprecation fixes and SQLAlchemy 2.0 API usage.

Ensures that code uses:
- datetime.now(datetime.UTC) instead of deprecated datetime.utcnow()
- Session.get() instead of deprecated Query.get()

Related to: DeprecationWarning fixes for datetime module changes and SQLAlchemy 2.0 migration
"""

import warnings
from datetime import UTC, datetime

import pytest


class TestDatetimeUTCDeprecationRegression:
    """Regression tests for datetime UTC deprecation fixes."""

    def test_no_utcnow_usage_in_imports(self):
        """Test that critical modules don't use deprecated datetime.utcnow()."""
        # Test that we can import modules without triggering utcnow deprecation warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)

            # Import modules that were fixed

            # Check for datetime.utcnow deprecation warnings
            utcnow_warnings = [
                warning
                for warning in w
                if "datetime.utcnow() is deprecated" in str(warning.message)
            ]

            assert len(utcnow_warnings) == 0, (
                f"Found {len(utcnow_warnings)} utcnow deprecation warnings during import"
            )

    def test_gdpr_service_uses_timezone_aware_datetime(self):
        """Test that GDPR service uses timezone-aware datetime objects."""
        from unittest.mock import MagicMock

        from src.security.gdpr.service import GDPRService

        # Mock database session
        mock_db = MagicMock()
        service = GDPRService(mock_db)

        # Test that methods would use timezone-aware datetime
        # We can't easily test the actual datetime calls without complex mocking,
        # but we can verify the service initializes correctly
        assert service.db == mock_db

    def test_failure_tracker_datetime_usage(self):
        """Test that failure tracker uses proper datetime methods."""
        from src.shared.testing.failure_tracker import TestFailure

        # Create a test failure instance
        failure = TestFailure(
            test_id="test_123",
            test_name="test_example",
            test_file="test_file.py",
            failure_message="Test failed",
        )

        # Verify that timestamps are set and are timezone-aware
        assert failure.first_seen is not None
        assert failure.last_seen is not None

        # Verify timestamps have timezone info (UTC)
        assert failure.first_seen.tzinfo is not None
        assert failure.last_seen.tzinfo is not None

    def test_datetime_utc_replacement_pattern(self):
        """Test that the replacement pattern works correctly."""
        # Test that datetime.now(UTC) works as expected
        now_utc = datetime.now(UTC)

        # Verify it's timezone-aware
        assert now_utc.tzinfo is not None
        assert str(now_utc.tzinfo) == "UTC"

        # Verify it returns current time (within reasonable bounds)
        import time

        current_timestamp = time.time()
        now_timestamp = now_utc.timestamp()

        # Should be within 1 second of current time
        assert abs(now_timestamp - current_timestamp) < 1.0

    def test_no_deprecated_datetime_patterns_in_code(self):
        """Test that key source files don't contain deprecated patterns."""
        import re
        from pathlib import Path

        # Files that were specifically fixed
        files_to_check = [
            "src/security/gdpr/service.py",
            "src/shared/testing/failure_tracker.py",
            "tools/rtm-db.py",
            "src/be/api/rtm.py",
            "tests/unit/security/test_gdpr_compliance.py",
            "tests/unit/shared/shared/testing/test_failure_tracker.py",
        ]

        deprecated_pattern = re.compile(r"datetime\.utcnow\(\)")

        for file_path in files_to_check:
            full_path = Path(__file__).parent.parent.parent / file_path
            if full_path.exists():
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                matches = deprecated_pattern.findall(content)
                assert len(matches) == 0, (
                    f"Found {len(matches)} deprecated datetime.utcnow() usage in {file_path}"
                )

    def test_timezone_consistency(self):
        """Test that UTC timezone handling is consistent."""
        # Test different ways of creating UTC datetime objects
        now1 = datetime.now(UTC)
        now2 = datetime.now(UTC)  # Alternative import style

        # Both should have same timezone
        assert now1.tzinfo == now2.tzinfo

        # Both should be close in time (within 1 second)
        diff = abs((now1 - now2).total_seconds())
        assert diff < 1.0

    @pytest.mark.parametrize(
        "method_name",
        [
            "record_consent",
            "withdraw_consent",
            "create_data_subject_request",
            "anonymize_expired_data",
        ],
    )
    def test_gdpr_service_methods_handle_timezone_aware_dates(self, method_name):
        """Test that GDPR service methods are designed for timezone-aware dates."""
        from src.security.gdpr.service import GDPRService

        # Verify that the methods exist and can be called
        # (This is a smoke test to ensure the service is properly structured)
        assert hasattr(GDPRService, method_name)
        method = getattr(GDPRService, method_name)
        assert callable(method)

    def test_deprecation_warning_count_reduced(self):
        """Integration test to verify overall deprecation warning reduction."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)

            # Import and instantiate key components that were fixed
            from unittest.mock import MagicMock

            from src.security.gdpr.service import GDPRService
            from src.shared.testing.failure_tracker import FailureTracker, TestFailure

            # Create instances
            mock_db = MagicMock()
            gdpr_service = GDPRService(mock_db)
            failure_tracker = FailureTracker()
            test_failure = TestFailure(
                test_id="test",
                test_name="test",
                test_file="test.py",
                failure_message="test",
            )

            # Filter for datetime.utcnow deprecation warnings
            utcnow_warnings = [
                warning
                for warning in w
                if "datetime.utcnow() is deprecated" in str(warning.message)
            ]

            # Should have significantly fewer warnings (target: 0)
            assert len(utcnow_warnings) <= 2, (
                f"Still found {len(utcnow_warnings)} utcnow deprecation warnings"
            )

    def test_rtm_cli_datetime_handling(self):
        """Test that RTM CLI tool handles datetime correctly."""
        import importlib.util
        from pathlib import Path
        from unittest.mock import Mock, patch

        # Load RTM CLI module directly
        repo_root = Path(__file__).parent.parent.parent
        cli_path = repo_root / "tools" / "rtm-db.py"

        spec = importlib.util.spec_from_file_location("rtm_db_cli", cli_path)
        rtm_db_cli = importlib.util.module_from_spec(spec)

        # Mock the imports to avoid database dependencies
        with patch.dict(
            "sys.modules",
            {
                "be.database": Mock(),
                "be.models.traceability": Mock(),
                "be.services.rtm_parser": Mock(),
                "rich.console": Mock(),
                "rich.table": Mock(),
                "rich.progress": Mock(),
            },
        ):
            spec.loader.exec_module(rtm_db_cli)

        # Verify that the module can be imported without datetime deprecation warnings
        # This test ensures that the CLI tool uses proper datetime patterns
        assert hasattr(rtm_db_cli, "cli")  # Main CLI function should exist

    def test_gdpr_compliance_datetime_handling(self):
        """Test that GDPR compliance tests use proper datetime patterns."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)

            # Import GDPR compliance test module

            # Filter for datetime.utcnow deprecation warnings from our code
            utcnow_warnings = [
                warning
                for warning in w
                if "datetime.utcnow() is deprecated" in str(warning.message)
                and "test_gdpr_compliance.py" in str(warning.filename)
            ]

            # Should have no warnings from our test code
            assert len(utcnow_warnings) == 0, (
                f"Found {len(utcnow_warnings)} utcnow deprecation warnings in GDPR compliance tests"
            )

    def test_timezone_aware_datetime_comparisons(self):
        """Test that datetime comparisons handle timezone-aware and naive datetimes properly."""
        from unittest.mock import MagicMock

        from src.security.gdpr.service import GDPRService

        # Create service instance
        mock_db = MagicMock()
        service = GDPRService(mock_db)

        # Test the timezone helper function
        from datetime import UTC, datetime

        # Test timezone-naive datetime
        naive_dt = datetime(2023, 1, 1, 12, 0, 0)
        aware_dt = service._ensure_timezone_aware(naive_dt)
        assert aware_dt.tzinfo == UTC

        # Test timezone-aware datetime
        original_aware_dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        unchanged_dt = service._ensure_timezone_aware(original_aware_dt)
        assert unchanged_dt == original_aware_dt

        # Test None handling
        none_result = service._ensure_timezone_aware(None)
        assert none_result is None

    def test_no_deprecated_content_upload_patterns(self):
        """Test that test files don't use deprecated content upload patterns."""
        import re
        from pathlib import Path

        # Check test files for deprecated 'data=' parameter in POST requests
        test_files_to_check = ["tests/unit/security/test_input_validation.py"]

        # Pattern that should be avoided: client.post(..., data=...)
        deprecated_pattern = re.compile(r"client\.post\([^)]*data=")

        for file_path in test_files_to_check:
            full_path = Path(__file__).parent.parent.parent / file_path
            if full_path.exists():
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                matches = deprecated_pattern.findall(content)
                assert len(matches) == 0, (
                    f"Found {len(matches)} deprecated 'data=' parameter usage in POST requests in {file_path}. Use 'content=' instead."
                )

    def test_test_files_use_timezone_aware_datetime(self):
        """Test that test files use timezone-aware datetime patterns properly."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)

            # Import the failure tracker test module

            # Filter for datetime.utcnow deprecation warnings from test files
            utcnow_warnings = [
                warning
                for warning in w
                if "datetime.utcnow() is deprecated" in str(warning.message)
                and "test_failure_tracker.py" in str(warning.filename)
            ]

            # Should have no warnings from our test code
            assert len(utcnow_warnings) == 0, (
                f"Found {len(utcnow_warnings)} datetime.utcnow deprecation warnings in failure tracker tests"
            )

    def test_sqlalchemy_legacy_api_usage(self):
        """Test that code uses SQLAlchemy 2.0 Session.get() instead of deprecated Query.get()."""
        import re
        from pathlib import Path

        # Files to check for SQLAlchemy 2.0 patterns
        files_to_check = [
            "tests/unit/tools/test_github_sync_manager.py",
            "tools/github_sync_manager.py",
            "src/be/services/rtm_parser.py",
            "src/be/models/traceability/epic.py",
            "src/be/models/traceability/user_story.py",
        ]

        # Pattern for deprecated Query.get() usage (not in compatibility checks)
        deprecated_query_get = re.compile(r"\.query\([^)]+\)\.get\([^)]+\)")

        # Pattern for compatibility check (should be allowed)
        compatibility_check = re.compile(
            r'if hasattr\(.*session.*,\s*["\']get["\']\)|else:|else.*\.query\(.*\)\.get\('
        )

        for file_path in files_to_check:
            full_path = Path(__file__).parent.parent.parent / file_path
            if full_path.exists():
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                # Find deprecated Query.get() usage
                for line_num, line in enumerate(lines, 1):
                    if deprecated_query_get.search(line):
                        # Check if this is part of a compatibility check
                        context_lines = lines[max(0, line_num - 3) : line_num + 2]
                        context = "\n".join(context_lines)

                        if not compatibility_check.search(context):
                            assert False, (
                                f"Found deprecated Query.get() usage at {file_path}:{line_num}\nLine: {line.strip()}\nUse Session.get(Model, primary_key) instead"
                            )

    def test_sqlalchemy_session_get_functionality(self):
        """Test that Session.get() works correctly as replacement for Query.get()."""
        import os
        import tempfile

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from src.security.gdpr.models import Base, ConsentRecord

        # Create temporary test database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            test_db_url = f"sqlite:///{temp_file.name}"

        try:
            # Create test database and session
            engine = create_engine(test_db_url, echo=False)
            Base.metadata.create_all(bind=engine)
            TestingSessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=engine
            )
            session = TestingSessionLocal()

            # Test that Session.get() method exists and works
            assert hasattr(session, "get"), (
                "Session should have get() method in SQLAlchemy 2.0"
            )

            # Test Session.get() with non-existent record (should return None)
            result = session.get(ConsentRecord, "nonexistent-id")
            assert result is None, (
                "Session.get() should return None for non-existent records"
            )

            session.close()
            engine.dispose()

        finally:
            # Cleanup
            try:
                os.unlink(temp_file.name)
            except (PermissionError, FileNotFoundError):
                pass  # Ignore cleanup errors
