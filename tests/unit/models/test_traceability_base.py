"""
Unit tests for TraceabilityBase model.

Tests common functionality shared across all RTM entities.

Related Issue: US-00052 - Database schema design for traceability relationships
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import json
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.be.models.traceability.base import Base, TraceabilityBase


@pytest.mark.epic("EP-00005")
@pytest.mark.user_story("US-00052")
class TestEntity(TraceabilityBase):
    """Test entity for testing base functionality."""

    __tablename__ = "test_entities"


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
@pytest.mark.epic("EP-00005")
@pytest.mark.user_story("US-00052")
def test_entity():
    """Create a test entity instance."""
    return TestEntity(
        title="Test Entity", description="Test description", status="planned"
    )


@pytest.mark.epic("EP-00005")
@pytest.mark.user_story("US-00052")
class TestTraceabilityBase:
    """Test cases for TraceabilityBase functionality."""

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_entity_creation(self, test_entity):
        """Test basic entity creation."""
        assert test_entity.title == "Test Entity"
        assert test_entity.description == "Test description"
        assert test_entity.status == "planned"
        assert test_entity.id is None  # Not saved yet

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_entity_persistence(self, db_session, test_entity):
        """Test entity can be saved and retrieved."""
        db_session.add(test_entity)
        db_session.commit()

        assert test_entity.id is not None
        assert test_entity.created_at is not None
        assert test_entity.updated_at is not None

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_set_git_context(self, test_entity):
        """Test git context setting."""
        commit_sha = "abc123def456"
        branch = "feature/rtm-implementation"

        test_entity.set_git_context(commit_sha, branch)

        assert test_entity.introduced_in_commit == commit_sha
        assert test_entity.introduced_in_branch == branch

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_mark_resolved(self, test_entity):
        """Test marking entity as resolved."""
        commit_sha = "def456abc123"
        release_version = "v1.2.0"

        test_entity.mark_resolved(commit_sha, release_version)

        assert test_entity.resolved_in_commit == commit_sha
        assert test_entity.released_in_version == release_version
        assert test_entity.status == "completed"

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_mark_resolved_status_preservation(self, test_entity):
        """Test that already completed status is preserved."""
        test_entity.status = "done"
        test_entity.mark_resolved("abc123")

        assert test_entity.status == "done"

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_add_affected_version_new_list(self, test_entity):
        """Test adding affected version to new entity."""
        version = "v1.1.0"
        test_entity.add_affected_version(version)

        versions = json.loads(test_entity.affects_versions)
        assert version in versions
        assert len(versions) == 1

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_add_affected_version_existing_list(self, test_entity):
        """Test adding version to existing list."""
        # Set up existing versions
        test_entity.affects_versions = json.dumps(["v1.0.0"])

        test_entity.add_affected_version("v1.1.0")

        versions = json.loads(test_entity.affects_versions)
        assert "v1.0.0" in versions
        assert "v1.1.0" in versions
        assert len(versions) == 2

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_add_affected_version_duplicate(self, test_entity):
        """Test that duplicate versions are not added."""
        version = "v1.1.0"
        test_entity.add_affected_version(version)
        test_entity.add_affected_version(version)  # Duplicate

        versions = json.loads(test_entity.affects_versions)
        assert len(versions) == 1
        assert version in versions

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_add_fixed_version(self, test_entity):
        """Test adding fixed version."""
        version = "v1.2.0"
        test_entity.add_fixed_version(version)

        versions = json.loads(test_entity.fixed_in_versions)
        assert version in versions

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_is_fixed_in_version_true(self, test_entity):
        """Test checking if fixed in specific version - positive case."""
        version = "v1.2.0"
        test_entity.add_fixed_version(version)

        assert test_entity.is_fixed_in_version(version) is True

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_is_fixed_in_version_false(self, test_entity):
        """Test checking if fixed in specific version - negative case."""
        test_entity.add_fixed_version("v1.2.0")

        assert test_entity.is_fixed_in_version("v1.3.0") is False

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_is_fixed_in_version_empty(self, test_entity):
        """Test checking fixed version on entity with no fixed versions."""
        assert test_entity.is_fixed_in_version("v1.0.0") is False

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_is_fixed_in_version_invalid_json(self, test_entity):
        """Test handling of invalid JSON in fixed_in_versions."""
        test_entity.fixed_in_versions = "invalid json"

        assert test_entity.is_fixed_in_version("v1.0.0") is False

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_to_dict_basic(self, test_entity):
        """Test dictionary conversion with basic data."""
        result = test_entity.to_dict()

        assert result["title"] == "Test Entity"
        assert result["description"] == "Test description"
        assert result["status"] == "planned"
        assert result["id"] is None
        assert "created_at" in result
        assert "updated_at" in result

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_to_dict_with_git_context(self, test_entity):
        """Test dictionary conversion with git context."""
        test_entity.set_git_context("abc123", "main")

        result = test_entity.to_dict()

        assert result["introduced_in_commit"] == "abc123"
        assert result["introduced_in_branch"] == "main"

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_repr(self, test_entity):
        """Test string representation."""
        repr_str = repr(test_entity)

        assert "TestEntity" in repr_str
        assert "Test Entity" in repr_str
        assert "planned" in repr_str

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_github_integration_fields(self, test_entity):
        """Test GitHub integration fields."""
        test_entity.github_issue_number = 123
        test_entity.github_issue_url = "https://github.com/owner/repo/issues/123"

        assert test_entity.github_issue_number == 123
        assert "github.com" in test_entity.github_issue_url

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_version_tracking_fields(self, test_entity):
        """Test version tracking fields."""
        test_entity.target_release_version = "v1.2.0"
        test_entity.released_in_version = "v1.1.5"

        assert test_entity.target_release_version == "v1.2.0"
        assert test_entity.released_in_version == "v1.1.5"

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_json_version_handling_corruption(self, test_entity):
        """Test handling of corrupted JSON in version fields."""
        # Test add_affected_version with corrupted JSON
        test_entity.affects_versions = "{invalid json"
        test_entity.add_affected_version("v1.0.0")

        versions = json.loads(test_entity.affects_versions)
        assert "v1.0.0" in versions

        # Test add_fixed_version with corrupted JSON
        test_entity.fixed_in_versions = "{invalid json"
        test_entity.add_fixed_version("v1.1.0")

        fixed_versions = json.loads(test_entity.fixed_in_versions)
        assert "v1.1.0" in fixed_versions

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_none_version_handling(self, test_entity):
        """Test handling of None values in version fields."""
        test_entity.affects_versions = None
        test_entity.add_affected_version("v1.0.0")

        versions = json.loads(test_entity.affects_versions)
        assert "v1.0.0" in versions
