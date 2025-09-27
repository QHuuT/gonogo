"""
Unit tests for UserStory model.

Tests UserStory hybrid GitHub + Database functionality.

Related Issue: US-00052 - Database schema design for traceability relationships
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.be.models.traceability.base import Base
from src.be.models.traceability.epic import Epic
from src.be.models.traceability.user_story import UserStory


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
    """Create a test Epic for UserStory relationships."""
    epic = Epic(epic_id="EP-00001", title="Parent Epic")
    db_session.add(epic)
    db_session.commit()
    return epic


@pytest.fixture
def user_story(epic):
    """Create a test UserStory instance."""
    return UserStory(
        user_story_id="US-00001",
        epic_id=epic.id,
        github_issue_number=123,
        title="Test User Story",
        story_points=5,
        priority="high",
    )


@pytest.mark.epic("EP-00001", "EP-00005")
@pytest.mark.user_story("US-00001", "US-00002", "US-00052")
class TestUserStory:
    """Test cases for UserStory model."""

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_user_story_creation(self, user_story, epic):
        """Test basic UserStory creation."""
        assert user_story.user_story_id == "US-00001"
        assert user_story.epic_id == epic.id
        assert user_story.github_issue_number == 123
        assert user_story.title == "Test User Story"
        assert user_story.story_points == 5
        assert user_story.priority == "high"

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_user_story_persistence(self, db_session, user_story):
        """Test UserStory can be saved and retrieved."""
        db_session.add(user_story)
        db_session.commit()

        retrieved = (
            db_session.query(UserStory).filter_by(user_story_id="US-00001").first()
        )
        assert retrieved is not None
        assert retrieved.user_story_id == "US-00001"
        assert retrieved.github_issue_number == 123

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_epic_relationship(self, db_session, user_story, epic):
        """Test relationship with Epic."""
        db_session.add(user_story)
        db_session.commit()

        # Test access to parent epic
        assert user_story.epic.epic_id == "EP-00001"

        # Test reverse relationship
        assert user_story in epic.user_stories

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_update_from_github_basic(self, user_story):
        """Test updating from GitHub issue data."""
        github_data = {
            "state": "open",
            "title": "Updated Title",
            "body": "Updated description",
            "labels": ["bug", "priority-high"],
            "assignees": ["developer1", "developer2"],
        }

        user_story.update_from_github(github_data)

        assert user_story.github_issue_state == "open"
        assert user_story.title == "Updated Title"
        assert user_story.description == "Updated description"
        assert "bug" in user_story.github_labels
        assert "developer1" in user_story.github_assignees

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_update_from_github_partial(self, user_story):
        """Test updating from partial GitHub data."""
        original_title = user_story.title
        github_data = {"state": "closed"}

        user_story.update_from_github(github_data)

        assert user_story.github_issue_state == "closed"
        assert user_story.title == original_title  # Should remain unchanged

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_update_from_github_recalculates_in_progress_status(self, user_story):
        """GitHub label updates should refresh implementation status."""
        user_story.github_issue_state = "open"
        user_story.github_labels = "[]"
        user_story.implementation_status = "planned"

        github_data = {
            "state": "open",
            "labels": [{"name": "status/in-progress"}],
            "assignees": [],
        }

        user_story.update_from_github(github_data)

        assert user_story.implementation_status == "in_progress"

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_update_from_github_closed_issue_sets_completed(self, user_story):
        """Closed GitHub issues should mark the story as completed."""
        user_story.github_issue_state = "open"
        user_story.implementation_status = "in_progress"

        github_data = {
            "state": "closed",
            "labels": [],
            "assignees": [],
        }

        user_story.update_from_github(github_data)

        assert user_story.implementation_status == "completed"

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_update_from_github_data_format_compatibility_regression(self, user_story):
        """Regression test: Ensure update_from_github handles both string and object label formats."""

        # Test 1: Simple string format (test data format)
        github_data_strings = {
            "state": "open",
            "title": "String Labels Test",
            "body": "Testing simple string label format",
            "labels": ["bug", "priority-high", "component/frontend"],
            "assignees": ["developer1"],
        }

        user_story.update_from_github(github_data_strings)

        assert user_story.github_issue_state == "open"
        assert user_story.title == "String Labels Test"
        assert user_story.description == "Testing simple string label format"
        assert "bug" in user_story.github_labels
        assert "component/frontend" in user_story.github_labels
        assert (
            user_story.component == "frontend"
        )  # Should extract component from string label

        # Test 2: GitHub API object format
        github_data_objects = {
            "state": "open",
            "title": "Object Labels Test",
            "body": "Testing GitHub API object label format",
            "labels": [
                {"name": "enhancement"},
                {"name": "priority-medium"},
                {"name": "component/backend"},
                {"name": "status/in-progress"},
            ],
            "assignees": [{"login": "developer2"}],
        }

        user_story.update_from_github(github_data_objects)

        assert user_story.github_issue_state == "open"
        assert user_story.title == "Object Labels Test"
        assert user_story.description == "Testing GitHub API object label format"
        assert "enhancement" in user_story.github_labels
        assert "component/backend" in user_story.github_labels
        assert (
            user_story.component == "backend"
        )  # Should extract component from object label
        assert (
            user_story.implementation_status == "in_progress"
        )  # Should derive status from labels

        # Test 3: Mixed format edge case (shouldn't happen in practice but should be handled)
        github_data_mixed = {
            "state": "open",
            "labels": [
                "simple-string",
                {"name": "object-label"},
                {"name": "component/api"},
                "another-string",
            ],
        }

        user_story.update_from_github(github_data_mixed)

        assert "simple-string" in user_story.github_labels
        assert "object-label" in user_story.github_labels
        assert "component/api" in user_story.github_labels
        assert "another-string" in user_story.github_labels
        assert (
            user_story.component == "api"
        )  # Should handle mixed format and extract component

        # Test 4: Empty and None labels (edge cases)
        github_data_empty = {
            "state": "open",
            "labels": [],
        }

        user_story.update_from_github(github_data_empty)
        # Should not crash and should handle empty labels gracefully

        github_data_none = {
            "state": "open",
            # labels key omitted entirely
        }

        user_story.update_from_github(github_data_none)
        # Should not crash when labels key is missing

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_calculate_test_coverage_no_tests(self, user_story):
        """Test test coverage calculation with no tests."""
        result = user_story.calculate_test_coverage()

        assert result["total_tests"] == 0
        assert result["passed_tests"] == 0
        assert result["coverage_percentage"] == 0.0

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_bdd_integration_fields(self, user_story):
        """Test BDD integration fields."""
        user_story.has_bdd_scenarios = True
        user_story.bdd_feature_files = json.dumps(
            ["features/auth.feature", "features/user.feature"]
        )

        assert user_story.has_bdd_scenarios is True
        feature_files = json.loads(user_story.bdd_feature_files)
        assert "features/auth.feature" in feature_files

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_gdpr_fields(self, user_story):
        """Test GDPR-related fields."""
        user_story.affects_gdpr = True
        user_story.gdpr_considerations = "Processes personal user data"

        assert user_story.affects_gdpr is True
        assert "personal user data" in user_story.gdpr_considerations

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_dependencies_tracking(self, user_story):
        """Test dependency tracking fields."""
        depends_on = [124, 125]
        blocks = [126, 127]

        user_story.depends_on_issues = json.dumps(depends_on)
        user_story.blocks_issues = json.dumps(blocks)

        assert json.loads(user_story.depends_on_issues) == depends_on
        assert json.loads(user_story.blocks_issues) == blocks

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_implementation_status_values(self, user_story):
        """Test valid implementation status values."""
        valid_statuses = ["todo", "in_progress", "in_review", "done", "blocked"]

        for status in valid_statuses:
            user_story.implementation_status = status
            assert user_story.implementation_status == status

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_sprint_assignment(self, user_story):
        """Test sprint assignment."""
        user_story.sprint = "Sprint 2024-01"
        assert user_story.sprint == "Sprint 2024-01"

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_story_points_validation(self, user_story):
        """Test story points assignment."""
        valid_points = [0, 1, 2, 3, 5, 8, 13, 21]

        for points in valid_points:
            user_story.story_points = points
            assert user_story.story_points == points

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_acceptance_criteria(self, user_story):
        """Test acceptance criteria field."""
        criteria = (
            "Given user is logged in, When they click profile, Then profile page loads"
        )
        user_story.acceptance_criteria = criteria

        assert user_story.acceptance_criteria == criteria

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_business_value(self, user_story):
        """Test business value field."""
        value = "Improves user experience and reduces support tickets"
        user_story.business_value = value

        assert user_story.business_value == value

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_to_dict_basic(self, user_story):
        """Test dictionary conversion with basic UserStory data."""
        result = user_story.to_dict()

        assert result["user_story_id"] == "US-00001"
        assert result["epic_id"] == user_story.epic_id
        assert result["github_issue_number"] == 123
        assert result["story_points"] == 5
        assert result["priority"] == "high"
        assert "test_coverage" in result
        assert "defect_count" in result

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_to_dict_includes_test_coverage(self, user_story):
        """Test that to_dict includes test coverage calculation."""
        result = user_story.to_dict()

        coverage = result["test_coverage"]
        assert coverage["total_tests"] == 0
        assert coverage["passed_tests"] == 0
        assert coverage["coverage_percentage"] == 0.0

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_repr(self, user_story):
        """Test string representation."""
        repr_str = repr(user_story)

        assert "UserStory" in repr_str
        assert "US-00001" in repr_str
        assert str(user_story.epic_id) in repr_str
        assert "123" in repr_str  # GitHub issue number

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_github_issue_uniqueness(self, db_session, epic):
        """Test that GitHub issue numbers must be unique."""
        us1 = UserStory(
            user_story_id="US-00001",
            epic_id=epic.id,
            github_issue_number=123,
            title="First Story",
        )
        us2 = UserStory(
            user_story_id="US-00002",
            epic_id=epic.id,
            github_issue_number=123,  # Same GitHub issue number
            title="Second Story",
        )

        db_session.add(us1)
        db_session.commit()

        db_session.add(us2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_user_story_id_uniqueness(self, db_session, epic):
        """Test that user_story_id must be unique."""
        us1 = UserStory(
            user_story_id="US-00001",
            epic_id=epic.id,
            github_issue_number=123,
            title="First Story",
        )
        us2 = UserStory(
            user_story_id="US-00001",  # Same user story ID
            epic_id=epic.id,
            github_issue_number=124,
            title="Second Story",
        )

        db_session.add(us1)
        db_session.commit()

        db_session.add(us2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_default_values(self, epic):
        """Test default values on UserStory creation."""
        us = UserStory(
            user_story_id="US-00002",
            epic_id=epic.id,
            github_issue_number=124,
            title="Default Test",
        )

        assert us.status == "planned"
        assert us.priority == "medium"
        assert us.story_points == 0
        assert us.implementation_status == "todo"
        assert us.has_bdd_scenarios is False
        assert us.affects_gdpr is False

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00052")
    def test_version_tracking_inheritance(self, user_story):
        """Test that UserStory inherits version tracking from base."""
        user_story.set_git_context("def456abc", "feature/user-story")
        user_story.target_release_version = "v1.3.0"

        assert user_story.introduced_in_commit == "def456abc"
        assert user_story.introduced_in_branch == "feature/user-story"
        assert user_story.target_release_version == "v1.3.0"
