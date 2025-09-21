"""
Unit tests for Epic model.

Tests Epic-specific functionality for database RTM system.

Related Issue: US-00052 - Database schema design for traceability relationships
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.be.models.traceability.base import Base
from src.be.models.traceability.epic import Epic


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
def epic():
    """Create a test Epic instance."""
    return Epic(
        epic_id="EP-00001",
        title="Test Epic",
        description="Test epic description",
        business_value="Improve user experience",
        priority="high",
    )


class TestEpic:
    """Test cases for Epic model."""

    def test_epic_creation(self, epic):
        """Test basic Epic creation."""
        assert epic.epic_id == "EP-00001"
        assert epic.title == "Test Epic"
        assert epic.business_value == "Improve user experience"
        assert epic.priority == "high"
        assert epic.total_story_points == 0
        assert epic.completion_percentage == 0.0

    def test_epic_persistence(self, db_session, epic):
        """Test Epic can be saved and retrieved."""
        db_session.add(epic)
        db_session.commit()

        retrieved = db_session.query(Epic).filter_by(epic_id="EP-00001").first()
        assert retrieved is not None
        assert retrieved.epic_id == "EP-00001"
        assert retrieved.title == "Test Epic"

    def test_calculate_completion_percentage_zero_points(self, epic):
        """Test completion calculation with zero story points."""
        result = epic.calculate_completion_percentage()
        assert result == 0.0

    def test_calculate_completion_percentage_normal(self, epic):
        """Test completion calculation with normal values."""
        epic.total_story_points = 10
        epic.completed_story_points = 3

        result = epic.calculate_completion_percentage()
        assert result == 30.0

    def test_calculate_completion_percentage_complete(self, epic):
        """Test completion calculation when fully complete."""
        epic.total_story_points = 10
        epic.completed_story_points = 10

        result = epic.calculate_completion_percentage()
        assert result == 100.0

    def test_update_progress(self, epic):
        """Test progress update functionality."""
        epic.update_progress(completed_points=5, total_points=15)

        assert epic.completed_story_points == 5
        assert epic.total_story_points == 15
        assert (
            abs(epic.completion_percentage - 33.333333333333336) < 0.0001
        )  # 5/15 * 100 with tolerance

    def test_update_progress_zero_total(self, epic):
        """Test progress update with zero total points."""
        epic.update_progress(completed_points=0, total_points=0)

        assert epic.completed_story_points == 0
        assert epic.total_story_points == 0
        assert epic.completion_percentage == 0.0

    def test_gdpr_fields(self, epic):
        """Test GDPR-related fields."""
        epic.gdpr_applicable = True
        epic.gdpr_considerations = "Personal data processing required"

        assert epic.gdpr_applicable is True
        assert "Personal data" in epic.gdpr_considerations

    def test_risk_assessment(self, epic):
        """Test risk assessment fields."""
        epic.risk_level = "high"

        assert epic.risk_level == "high"

    def test_success_criteria(self, epic):
        """Test success criteria field."""
        criteria = "User satisfaction > 90%, Performance < 200ms"
        epic.success_criteria = criteria

        assert epic.success_criteria == criteria

    def test_to_dict_basic(self, epic):
        """Test dictionary conversion with basic Epic data."""
        result = epic.to_dict()

        assert result["epic_id"] == "EP-00001"
        assert result["title"] == "Test Epic"
        assert result["business_value"] == "Improve user experience"
        assert result["priority"] == "high"
        assert result["total_story_points"] == 0
        assert result["completion_percentage"] == 0.0
        assert result["test_count"] == 0
        assert result["user_story_count"] == 0
        assert result["defect_count"] == 0

    def test_to_dict_with_relationships(self, db_session, epic):
        """Test dictionary conversion includes relationship counts."""
        # Save epic to get ID for relationships
        db_session.add(epic)
        db_session.commit()

        result = epic.to_dict()

        # Should have relationship count fields even if empty
        assert "test_count" in result
        assert "user_story_count" in result
        assert "defect_count" in result

    def test_repr(self, epic):
        """Test string representation."""
        repr_str = repr(epic)

        assert "Epic" in repr_str
        assert "EP-00001" in repr_str
        assert "Test Epic" in repr_str
        assert "planned" in repr_str  # Default status
        assert "0.0%" in repr_str  # Completion percentage

    def test_epic_id_uniqueness_constraint(self, db_session):
        """Test that epic_id must be unique."""
        epic1 = Epic(epic_id="EP-00001", title="First Epic")
        epic2 = Epic(epic_id="EP-00001", title="Second Epic")

        db_session.add(epic1)
        db_session.commit()

        db_session.add(epic2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

    def test_priority_values(self, epic):
        """Test valid priority values."""
        valid_priorities = ["critical", "high", "medium", "low"]

        for priority in valid_priorities:
            epic.priority = priority
            assert epic.priority == priority

    def test_risk_level_values(self, epic):
        """Test valid risk level values."""
        valid_risk_levels = ["low", "medium", "high", "critical"]

        for risk_level in valid_risk_levels:
            epic.risk_level = risk_level
            assert epic.risk_level == risk_level

    def test_default_values(self):
        """Test default values on Epic creation."""
        epic = Epic(epic_id="EP-00002", title="Default Test")

        assert epic.status == "planned"
        assert epic.priority == "medium"
        assert epic.risk_level == "medium"
        assert epic.total_story_points == 0
        assert epic.completed_story_points == 0
        assert epic.completion_percentage == 0.0
        assert epic.gdpr_applicable is False

    def test_github_integration(self, epic):
        """Test GitHub issue integration fields."""
        epic.github_issue_number = 42
        epic.github_issue_url = "https://github.com/owner/repo/issues/42"

        assert epic.github_issue_number == 42
        assert epic.github_issue_url.endswith("/issues/42")

    def test_version_tracking_inheritance(self, epic):
        """Test that Epic inherits version tracking from base."""
        epic.set_git_context("abc123def", "feature/epic-implementation")
        epic.target_release_version = "v1.2.0"

        assert epic.introduced_in_commit == "abc123def"
        assert epic.introduced_in_branch == "feature/epic-implementation"
        assert epic.target_release_version == "v1.2.0"

    def test_completion_percentage_property(self, epic):
        """Test that completion_percentage is correctly calculated and stored."""
        epic.total_story_points = 20
        epic.completed_story_points = 8

        # Update progress which should recalculate percentage
        epic.update_progress(8, 20)

        assert epic.completion_percentage == 40.0

        # Test direct calculation
        calculated = epic.calculate_completion_percentage()
        assert calculated == 40.0
