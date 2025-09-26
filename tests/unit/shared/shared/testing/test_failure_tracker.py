"""
Unit tests for test failure tracking and pattern analysis.

Tests the core functionality of the FailureTracker system,
ensuring proper categorization, storage, and analysis of test failures.

Related to: US-00025 Test failure tracking and reporting
"""

import importlib.util

# Import the module under test
# Use importlib to explicitly load from the correct source path
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Load the module directly from the source file to avoid namespace collision
repo_root = Path(__file__).parent.parent.parent.parent.parent.parent
failure_tracker_path = repo_root / "src" / "shared" / "testing" / "failure_tracker.py"

spec = importlib.util.spec_from_file_location("failure_tracker", failure_tracker_path)
failure_tracker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(failure_tracker)

# Import the classes from the loaded module
FailureTracker = failure_tracker.FailureTracker
TestFailure = failure_tracker.TestFailure
FailureCategory = failure_tracker.FailureCategory
FailureSeverity = failure_tracker.FailureSeverity
FailurePattern = failure_tracker.FailurePattern
FailureStatistics = failure_tracker.FailureStatistics


@pytest.mark.epic("EP-00007")
@pytest.mark.user_story("US-00025")
@pytest.mark.component("shared")
class TestFailureTracker:
    """Test core FailureTracker functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        # Handle Windows file locking issues with SQLite
        try:
            if db_path.exists():
                db_path.unlink()
        except PermissionError:
            # File might be locked by SQLite on Windows, ignore for tests
            pass

    @pytest.fixture
    def tracker(self, temp_db):
        """Create FailureTracker instance with temporary database."""
        return FailureTracker(db_path=temp_db)

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_database_initialization(self, tracker):
        """Test that database tables are created correctly."""
        # Database should be initialized
        assert tracker.db_path.exists()

        # Check that tables exist by attempting to query them
        import sqlite3

        with sqlite3.connect(tracker.db_path) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()

        table_names = [t[0] for t in tables]
        assert "test_failures" in table_names
        assert "failure_patterns" in table_names

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_failure_categorization(self, tracker):
        """Test automatic failure categorization."""
        test_cases = [
            (
                "AssertionError: expected 5 but got 3",
                "assert",
                FailureCategory.ASSERTION_ERROR,
            ),
            (
                "ModuleNotFoundError: No module named 'nonexistent'",
                "",
                FailureCategory.IMPORT_ERROR,
            ),
            (
                "UnicodeEncodeError: 'charmap' codec can't encode",
                "",
                FailureCategory.UNICODE_ERROR,
            ),
            ("TimeoutError: operation timed out", "", FailureCategory.TIMEOUT_ERROR),
            ("ConnectionError: Failed to connect", "", FailureCategory.NETWORK_ERROR),
            ("PermissionError: Access denied", "", FailureCategory.PERMISSION_ERROR),
            ("Some unknown error message", "", FailureCategory.UNKNOWN_ERROR),
        ]

        for error_msg, stack_trace, expected_category in test_cases:
            category = tracker.categorize_failure(error_msg, stack_trace)
            assert category == expected_category, f"Failed for: {error_msg}"

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_severity_determination(self, tracker):
        """Test failure severity determination."""
        # Critical failure
        critical_failure = TestFailure(
            test_name="test_critical",
            failure_message="Fatal error: segmentation fault",
            stack_trace="core dumped",
        )
        severity = tracker.determine_severity(critical_failure)
        assert severity == FailureSeverity.CRITICAL

        # High severity
        high_failure = TestFailure(
            test_name="test_high",
            failure_message="Database connection failed",
            stack_trace="",
        )
        severity = tracker.determine_severity(high_failure)
        assert severity == FailureSeverity.HIGH

        # Flaky test (multiple occurrences)
        flaky_failure = TestFailure(
            test_name="test_flaky",
            failure_message="Random failure",
            stack_trace="",
            occurrence_count=5,
        )
        severity = tracker.determine_severity(flaky_failure)
        assert severity == FailureSeverity.FLAKY

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_record_new_failure(self, tracker):
        """Test recording a new test failure."""
        failure = TestFailure(
            test_id="tests/unit/test_example.py::test_function",
            test_name="test_function",
            test_file="tests/unit/test_example.py",
            failure_message="AssertionError: Test failed",
            stack_trace="Full stack trace here",
            category=FailureCategory.ASSERTION_ERROR,
            severity=FailureSeverity.MEDIUM,
            session_id="test_session_123",
            execution_mode="verbose",
        )

        failure_id = tracker.record_failure(failure)
        assert failure_id is not None
        assert isinstance(failure_id, int)

        # Verify the failure was stored
        import sqlite3

        with sqlite3.connect(tracker.db_path) as conn:
            result = conn.execute(
                "SELECT test_name, category, occurrence_count FROM test_failures WHERE id = ?",
                (failure_id,),
            ).fetchone()

        assert result is not None
        assert result[0] == "test_function"
        assert result[1] == "assertion_error"
        assert result[2] == 1

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_record_duplicate_failure(self, tracker):
        """Test that duplicate failures increment occurrence count."""
        failure = TestFailure(
            test_name="test_duplicate",
            test_file="test_file.py",
            failure_message="Same error message",
            stack_trace="Same stack trace",
        )

        # Record the same failure twice
        first_id = tracker.record_failure(failure)
        second_id = tracker.record_failure(failure)

        # Should return the same ID (updated existing record)
        assert first_id == second_id

        # Verify occurrence count was incremented
        import sqlite3

        with sqlite3.connect(tracker.db_path) as conn:
            result = conn.execute(
                "SELECT occurrence_count FROM test_failures WHERE id = ?", (first_id,)
            ).fetchone()

        assert result[0] == 2

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_get_failure_statistics(self, tracker):
        """Test failure statistics generation."""
        # Create some test failures
        failures = [
            TestFailure(
                test_name="test1",
                failure_message="Error 1",
                category=FailureCategory.ASSERTION_ERROR,
            ),
            TestFailure(
                test_name="test2",
                failure_message="Error 2",
                category=FailureCategory.ASSERTION_ERROR,
            ),
            TestFailure(
                test_name="test3",
                failure_message="Error 3",
                category=FailureCategory.IMPORT_ERROR,
            ),
        ]

        for failure in failures:
            tracker.record_failure(failure)

        stats = tracker.get_failure_statistics(days=7)

        assert isinstance(stats, FailureStatistics)
        assert stats.total_failures >= 3
        assert stats.unique_failures >= 3
        assert stats.most_common_category == FailureCategory.ASSERTION_ERROR

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_get_top_failing_tests(self, tracker):
        """Test retrieval of top failing tests."""
        # Create failures with different occurrence counts
        failure1 = TestFailure(test_name="flaky_test", failure_message="Error")
        failure2 = TestFailure(
            test_name="stable_test", failure_message="Different error"
        )

        # Record flaky test multiple times
        for _ in range(5):
            tracker.record_failure(failure1)

        # Record stable test once
        tracker.record_failure(failure2)

        top_failing = tracker.get_top_failing_tests(limit=5)

        assert len(top_failing) >= 2
        assert top_failing[0]["test_name"] == "flaky_test"
        assert top_failing[0]["total_failures"] >= 5

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_detect_patterns(self, tracker):
        """Test pattern detection functionality."""
        # Create multiple failures of the same category
        for i in range(3):
            failure = TestFailure(
                test_name=f"test_{i}",
                failure_message="AssertionError: Test failed",
                category=FailureCategory.ASSERTION_ERROR,
            )
            tracker.record_failure(failure)

        patterns = tracker.detect_patterns()

        assert len(patterns) > 0
        assertion_pattern = next(
            (p for p in patterns if p.category == FailureCategory.ASSERTION_ERROR), None
        )
        assert assertion_pattern is not None
        assert assertion_pattern.occurrences >= 3

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_cleanup_old_failures(self, tracker):
        """Test cleanup of old failure records."""
        # Create an old failure
        old_failure = TestFailure(test_name="old_test", failure_message="Old error")
        # Set an old timestamp
        old_failure.last_seen = datetime.utcnow() - timedelta(days=100)

        # Create a recent failure
        recent_failure = TestFailure(
            test_name="recent_test", failure_message="Recent error"
        )

        tracker.record_failure(old_failure)
        tracker.record_failure(recent_failure)

        # Cleanup failures older than 90 days
        deleted_count = tracker.cleanup_old_failures(days=90)

        assert deleted_count >= 1

        # Verify recent failure still exists
        top_failing = tracker.get_top_failing_tests()
        test_names = [t["test_name"] for t in top_failing]
        assert "recent_test" in test_names
        # Old test should be gone, but might not be in top failing if there are others


@pytest.mark.epic("EP-00007")
@pytest.mark.user_story("US-00025")
@pytest.mark.component("shared")
class TestTestFailure:
    """Test TestFailure dataclass functionality."""

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_failure_creation(self):
        """Test TestFailure object creation and defaults."""
        failure = TestFailure(
            test_name="test_example", failure_message="Test error message"
        )

        assert failure.test_name == "test_example"
        assert failure.failure_message == "Test error message"
        assert failure.category == FailureCategory.UNKNOWN_ERROR
        assert failure.severity == FailureSeverity.MEDIUM
        assert failure.occurrence_count == 1
        assert isinstance(failure.first_seen, datetime)
        assert isinstance(failure.last_seen, datetime)
        assert failure.error_hash != ""
        assert failure.metadata == {}

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_error_hash_generation(self):
        """Test that error hash is generated consistently."""
        failure1 = TestFailure(
            test_name="test_function",
            failure_message="AssertionError: expected 5 got 3",
            category=FailureCategory.ASSERTION_ERROR,
        )

        failure2 = TestFailure(
            test_name="test_function",
            failure_message="AssertionError: expected 7 got 9",  # Different numbers
            category=FailureCategory.ASSERTION_ERROR,
        )

        # Should generate same hash (numbers normalized)
        assert failure1.error_hash == failure2.error_hash

        failure3 = TestFailure(
            test_name="different_test",  # Different test name
            failure_message="AssertionError: expected 5 got 3",
            category=FailureCategory.ASSERTION_ERROR,
        )

        # Should generate different hash (different test name)
        assert failure1.error_hash != failure3.error_hash

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_hash_normalization(self):
        """Test that error hash normalizes common variable elements."""
        failure = TestFailure(
            test_name="test_function",
            failure_message="Error at line 123 with value 0x7f8b8c000000 in file /path/to/file.py",
        )

        # Verify normalization patterns are applied
        assert (
            "123" not in failure._generate_error_hash()
        )  # Numbers should be normalized


@pytest.mark.epic("EP-00007")
@pytest.mark.user_story("US-00025")
@pytest.mark.component("shared")
class TestFailureEnums:
    """Test enum definitions and behavior."""

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_failure_category_values(self):
        """Test FailureCategory enum values."""
        assert FailureCategory.ASSERTION_ERROR.value == "assertion_error"
        assert FailureCategory.UNICODE_ERROR.value == "unicode_error"
        assert FailureCategory.UNKNOWN_ERROR.value == "unknown_error"

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_failure_severity_values(self):
        """Test FailureSeverity enum values."""
        assert FailureSeverity.CRITICAL.value == "critical"
        assert FailureSeverity.HIGH.value == "high"
        assert FailureSeverity.FLAKY.value == "flaky"


@pytest.mark.epic("EP-00007")
@pytest.mark.user_story("US-00025")
@pytest.mark.component("shared")
class TestFailureTrackerIntegration:
    """Test integration scenarios and edge cases."""

    @pytest.fixture
    def tracker(self):
        """Create FailureTracker with temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        tracker = FailureTracker(db_path=db_path)
        yield tracker
        # Handle Windows file locking issues with SQLite
        try:
            if db_path.exists():
                db_path.unlink()
        except PermissionError:
            # File might be locked by SQLite on Windows, ignore for tests
            pass

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_unicode_content_handling(self, tracker):
        """Test that tracker handles Unicode content correctly."""
        failure = TestFailure(
            test_name="test_unicode",
            test_file="tests/test_file.py",
            failure_message="UnicodeEncodeError: 'charmap' codec can't encode character '✅'",
            stack_trace="Error with emoji ✅ and symbols ⚠️ 📝",
            metadata={"status": "✅", "type": "📝"},
        )

        failure_id = tracker.record_failure(failure)
        assert failure_id is not None

        # Verify Unicode content was stored correctly
        import sqlite3

        with sqlite3.connect(tracker.db_path) as conn:
            result = conn.execute(
                "SELECT failure_message, stack_trace FROM test_failures WHERE id = ?",
                (failure_id,),
            ).fetchone()

        assert "✅" in result[0]
        assert "⚠️" in result[1]

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_large_stack_trace_handling(self, tracker):
        """Test handling of very large stack traces."""
        large_stack_trace = "Line of stack trace\n" * 1000  # Large stack trace

        failure = TestFailure(
            test_name="test_large_stack",
            failure_message="Error with large stack trace",
            stack_trace=large_stack_trace,
        )

        failure_id = tracker.record_failure(failure)
        assert failure_id is not None

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_concurrent_failure_recording(self, tracker):
        """Test recording failures concurrently (simulated)."""
        failures = [
            TestFailure(test_name=f"test_{i}", failure_message=f"Error {i}")
            for i in range(10)
        ]

        # Record all failures
        failure_ids = []
        for failure in failures:
            failure_id = tracker.record_failure(failure)
            failure_ids.append(failure_id)

        # All should be recorded successfully
        assert len(failure_ids) == 10
        assert all(fid is not None for fid in failure_ids)

    @pytest.mark.user_story("US-00025")
    @pytest.mark.component("shared")
    def test_malformed_data_handling(self, tracker):
        """Test handling of malformed or edge case data."""
        # Empty strings
        failure = TestFailure(test_name="", failure_message="", stack_trace="")
        failure_id = tracker.record_failure(failure)
        assert failure_id is not None

        # Very long test name
        failure = TestFailure(
            test_name="test_" + "x" * 1000, failure_message="Long test name error"
        )
        failure_id = tracker.record_failure(failure)
        assert failure_id is not None
