"""
Unit tests for Test model.

Tests Test entity functionality for RTM system.

Related Issue: US-00052 - Database schema design for traceability relationships
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.be.models.traceability.base import Base
from src.be.models.traceability.epic import Epic
from src.be.models.traceability.test import Test


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def epic(db_session):
    """Create a test Epic for Test relationships."""
    epic = Epic(epic_id="EP-00001", title="Parent Epic")
    db_session.add(epic)
    db_session.commit()
    return epic


@pytest.fixture
def test_entity(epic):
    """Create a test Test instance."""
    return Test(
        test_type="unit",
        test_file_path="tests/unit/test_auth.py",
        title="Test Authentication",
        test_function_name="test_login_success",
        epic_id=epic.id,
    )


@pytest.mark.epic("EP-00001", "EP-00005")
@pytest.mark.user_story("US-00052")
class TestTestModel:
    """Test cases for Test model."""

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_test_creation(self, test_entity, epic):
        """Test basic Test creation."""
        assert test_entity.test_type == "unit"
        assert test_entity.test_file_path == "tests/unit/test_auth.py"
        assert test_entity.title == "Test Authentication"
        assert test_entity.test_function_name == "test_login_success"
        assert test_entity.epic_id == epic.id

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_test_persistence(self, db_session, test_entity):
        """Test Test can be saved and retrieved."""
        db_session.add(test_entity)
        db_session.commit()

        retrieved = (
            db_session.query(Test)
            .filter_by(test_function_name="test_login_success")
            .first()
        )
        assert retrieved is not None
        assert retrieved.test_type == "unit"
        assert retrieved.test_file_path == "tests/unit/test_auth.py"

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_epic_relationship(self, db_session, test_entity, epic):
        """Test relationship with Epic."""
        db_session.add(test_entity)
        db_session.commit()

        # Test access to parent epic
        assert test_entity.epic.epic_id == "EP-00001"

        # Test reverse relationship
        assert test_entity in epic.tests

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_test_types(self, test_entity):
        """Test valid test types."""
        valid_types = ["unit", "integration", "bdd", "security", "e2e"]

        for test_type in valid_types:
            test_entity.test_type = test_type
            assert test_entity.test_type == test_type

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_bdd_fields(self, test_entity):
        """Test BDD-specific fields."""
        test_entity.test_type = "bdd"
        test_entity.bdd_feature_file = "features/authentication.feature"
        test_entity.bdd_scenario_name = "User logs in successfully"

        assert test_entity.bdd_feature_file == "features/authentication.feature"
        assert test_entity.bdd_scenario_name == "User logs in successfully"

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_github_references(self, test_entity):
        """Test GitHub issue references."""
        test_entity.github_user_story_number = 123
        test_entity.github_defect_number = 456

        assert test_entity.github_user_story_number == 123
        assert test_entity.github_defect_number == 456

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_update_execution_result_success(self, test_entity):
        """Test updating execution result for successful test."""
        test_entity.update_execution_result("passed", duration_ms=150.5)

        assert test_entity.last_execution_status == "passed"
        assert test_entity.execution_duration_ms == 150.5
        assert test_entity.execution_count == 1
        assert test_entity.failure_count == 0
        assert test_entity.last_error_message is None

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_update_execution_result_failure(self, test_entity):
        """Test updating execution result for failed test."""
        error_msg = "AssertionError: Expected 200, got 401"
        test_entity.update_execution_result(
            "failed", duration_ms=75.0, error_message=error_msg
        )

        assert test_entity.last_execution_status == "failed"
        assert test_entity.execution_duration_ms == 75.0
        assert test_entity.execution_count == 1
        assert test_entity.failure_count == 1
        assert test_entity.last_error_message == error_msg

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_update_execution_result_multiple_runs(self, test_entity):
        """Test multiple execution result updates."""
        # First run - pass
        test_entity.update_execution_result("passed")
        assert test_entity.execution_count == 1
        assert test_entity.failure_count == 0

        # Second run - fail
        test_entity.update_execution_result("failed", error_message="Test error")
        assert test_entity.execution_count == 2
        assert test_entity.failure_count == 1

        # Third run - pass (should clear error)
        test_entity.update_execution_result("passed")
        assert test_entity.execution_count == 3
        assert test_entity.failure_count == 1  # Total failures remains
        assert test_entity.last_error_message is None

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_get_success_rate_no_executions(self, test_entity):
        """Test success rate calculation with no executions."""
        assert test_entity.get_success_rate() == 0.0

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_get_success_rate_all_passed(self, test_entity):
        """Test success rate calculation with all tests passing."""
        for _ in range(5):
            test_entity.update_execution_result("passed")

        assert test_entity.get_success_rate() == 100.0

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_get_success_rate_mixed_results(self, test_entity):
        """Test success rate calculation with mixed results."""
        # 3 passes, 2 failures
        for _ in range(3):
            test_entity.update_execution_result("passed")
        for _ in range(2):
            test_entity.update_execution_result("failed")

        assert test_entity.get_success_rate() == 60.0  # 3/5 * 100

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_test_priority_values(self, test_entity):
        """Test valid test priority values."""
        valid_priorities = ["critical", "high", "medium", "low"]

        for priority in valid_priorities:
            test_entity.test_priority = priority
            assert test_entity.test_priority == priority

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_automation_flags(self, test_entity):
        """Test automation-related flags."""
        test_entity.is_automated = False
        test_entity.requires_manual_verification = True

        assert test_entity.is_automated is False
        assert test_entity.requires_manual_verification is True

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_coverage_information(self, test_entity):
        """Test code coverage fields."""
        test_entity.code_coverage_percentage = 85.5
        covered_files = ["src/auth.py", "src/user.py"]
        test_entity.covered_files = json.dumps(covered_files)

        assert test_entity.code_coverage_percentage == 85.5
        assert json.loads(test_entity.covered_files) == covered_files

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_gdpr_and_security_flags(self, test_entity):
        """Test GDPR and security testing flags."""
        test_entity.tests_gdpr_compliance = True
        test_entity.tests_security_aspects = True

        assert test_entity.tests_gdpr_compliance is True
        assert test_entity.tests_security_aspects is True

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_error_tracking(self, test_entity):
        """Test error message and traceback tracking."""
        error_msg = "ValueError: Invalid input"
        traceback = "Traceback (most recent call last):\n  File 'test.py', line 42"

        test_entity.last_error_message = error_msg
        test_entity.last_error_traceback = traceback

        assert test_entity.last_error_message == error_msg
        assert test_entity.last_error_traceback == traceback

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_to_dict_basic(self, test_entity):
        """Test dictionary conversion with basic Test data."""
        result = test_entity.to_dict()

        assert result["test_type"] == "unit"
        assert result["test_file_path"] == "tests/unit/test_auth.py"
        assert result["test_function_name"] == "test_login_success"
        assert result["epic_id"] == test_entity.epic_id
        assert result["last_execution_status"] == "not_run"
        assert result["execution_count"] == 0
        assert result["failure_count"] == 0
        assert result["success_rate"] == 0.0

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_to_dict_with_execution_data(self, test_entity):
        """Test dictionary conversion includes execution data."""
        test_entity.update_execution_result("passed", duration_ms=123.45)

        result = test_entity.to_dict()

        assert result["last_execution_status"] == "passed"
        assert result["execution_duration_ms"] == 123.45
        assert result["execution_count"] == 1
        assert result["success_rate"] == 100.0

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_repr(self, test_entity):
        """Test string representation."""
        repr_str = repr(test_entity)

        assert "Test" in repr_str
        assert "unit" in repr_str
        assert "tests/unit/test_auth.py" in repr_str
        assert "not_run" in repr_str
        assert str(test_entity.epic_id) in repr_str

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_default_values(self, epic):
        """Test default values on Test creation."""
        test = Test(
            test_type="integration",
            test_file_path="tests/integration/test_api.py",
            title="API Test",
        )

        assert test.status == "planned"
        assert test.last_execution_status == "not_run"
        assert test.execution_count == 0
        assert test.failure_count == 0
        assert test.test_priority == "medium"
        assert test.is_automated is True
        assert test.requires_manual_verification is False
        assert test.tests_gdpr_compliance is False
        assert test.tests_security_aspects is False

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_execution_status_values(self, test_entity):
        """Test valid execution status values."""
        valid_statuses = ["not_run", "passed", "failed", "skipped", "error"]

        for status in valid_statuses:
            test_entity.last_execution_status = status
            assert test_entity.last_execution_status == status

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_version_tracking_inheritance(self, test_entity):
        """Test that Test inherits version tracking from base."""
        test_entity.set_git_context("abc123def", "feature/test-implementation")
        test_entity.target_release_version = "v1.1.0"

        assert test_entity.introduced_in_commit == "abc123def"
        assert test_entity.introduced_in_branch == "feature/test-implementation"
        assert test_entity.target_release_version == "v1.1.0"

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_test_file_path_indexing(self, db_session, epic):
        """Test that test_file_path is properly indexed for queries."""
        test1 = Test(
            test_type="unit",
            test_file_path="tests/unit/auth/test_login.py",
            title="Login Test",
            epic_id=epic.id,
        )
        test2 = Test(
            test_type="unit",
            test_file_path="tests/unit/auth/test_logout.py",
            title="Logout Test",
            epic_id=epic.id,
        )

        db_session.add_all([test1, test2])
        db_session.commit()

        # Query by file path pattern should work efficiently due to index
        results = (
            db_session.query(Test)
            .filter(Test.test_file_path.like("tests/unit/auth/%"))
            .all()
        )

        assert len(results) == 2
