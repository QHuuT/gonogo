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


@pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
@pytest.mark.user_story("US-00052")
class TestEpic:
    """Test cases for Epic model."""

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_epic_creation(self, epic):
        """Test basic Epic creation."""
        assert epic.epic_id == "EP-00001"
        assert epic.title == "Test Epic"
        assert epic.business_value == "Improve user experience"
        assert epic.priority == "high"
        assert epic.total_story_points == 0
        assert epic.completion_percentage == 0.0

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_epic_persistence(self, db_session, epic):
        """Test Epic can be saved and retrieved."""
        db_session.add(epic)
        db_session.commit()

        retrieved = db_session.query(Epic).filter_by(epic_id="EP-00001").first()
        assert retrieved is not None
        assert retrieved.epic_id == "EP-00001"
        assert retrieved.title == "Test Epic"

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_calculate_completion_percentage_zero_points(self, epic):
        """Test completion calculation with zero story points."""
        result = epic.calculate_completion_percentage()
        assert result == 0.0

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_calculate_completion_percentage_normal(self, epic):
        """Test completion calculation with normal values."""
        epic.total_story_points = 10
        epic.completed_story_points = 3

        result = epic.calculate_completion_percentage()
        assert result == 30.0

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_calculate_completion_percentage_complete(self, epic):
        """Test completion calculation when fully complete."""
        epic.total_story_points = 10
        epic.completed_story_points = 10

        result = epic.calculate_completion_percentage()
        assert result == 100.0

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_update_progress(self, epic):
        """Test progress update functionality."""
        epic.update_progress(completed_points=5, total_points=15)

        assert epic.completed_story_points == 5
        assert epic.total_story_points == 15
        assert (
            abs(epic.completion_percentage - 33.333333333333336) < 0.0001
        )  # 5/15 * 100 with tolerance

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_update_progress_zero_total(self, epic):
        """Test progress update with zero total points."""
        epic.update_progress(completed_points=0, total_points=0)

        assert epic.completed_story_points == 0
        assert epic.total_story_points == 0
        assert epic.completion_percentage == 0.0

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_gdpr_fields(self, epic):
        """Test GDPR-related fields."""
        epic.gdpr_applicable = True
        epic.gdpr_considerations = "Personal data processing required"

        assert epic.gdpr_applicable is True
        assert "Personal data" in epic.gdpr_considerations

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_risk_assessment(self, epic):
        """Test risk assessment fields."""
        epic.risk_level = "high"

        assert epic.risk_level == "high"

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_success_criteria(self, epic):
        """Test success criteria field."""
        criteria = "User satisfaction > 90%, Performance < 200ms"
        epic.success_criteria = criteria

        assert epic.success_criteria == criteria

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
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

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
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

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_repr(self, epic):
        """Test string representation."""
        repr_str = repr(epic)

        assert "Epic" in repr_str
        assert "EP-00001" in repr_str
        assert "Test Epic" in repr_str
        assert "planned" in repr_str  # Default status
        assert "0.0%" in repr_str  # Completion percentage

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_epic_id_uniqueness_constraint(self, db_session):
        """Test that epic_id must be unique."""
        epic1 = Epic(epic_id="EP-00001", title="First Epic")
        epic2 = Epic(epic_id="EP-00001", title="Second Epic")

        db_session.add(epic1)
        db_session.commit()

        db_session.add(epic2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_priority_values(self, epic):
        """Test valid priority values."""
        valid_priorities = ["critical", "high", "medium", "low"]

        for priority in valid_priorities:
            epic.priority = priority
            assert epic.priority == priority

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_risk_level_values(self, epic):
        """Test valid risk level values."""
        valid_risk_levels = ["low", "medium", "high", "critical"]

        for risk_level in valid_risk_levels:
            epic.risk_level = risk_level
            assert epic.risk_level == risk_level

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
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

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_github_integration(self, epic):
        """Test GitHub issue integration fields."""
        epic.github_issue_number = 42
        epic.github_issue_url = "https://github.com/owner/repo/issues/42"

        assert epic.github_issue_number == 42
        assert epic.github_issue_url.endswith("/issues/42")

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_version_tracking_inheritance(self, epic):
        """Test that Epic inherits version tracking from base."""
        epic.set_git_context("abc123def", "feature/epic-implementation")
        epic.target_release_version = "v1.2.0"

        assert epic.introduced_in_commit == "abc123def"
        assert epic.introduced_in_branch == "feature/epic-implementation"
        assert epic.target_release_version == "v1.2.0"

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
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

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_metrics_cache_and_history(self, db_session, epic):
        """Metrics should cache and append history entries when refreshed."""
        db_session.add(epic)
        db_session.commit()

        metrics = epic.update_metrics(
            force_recalculate=True, session=db_session, record_history=True
        )
        db_session.commit()
        db_session.refresh(epic)

        assert epic.metrics_cache is not None
        assert epic.metrics_cache_updated_at is not None
        assert len(epic.metric_history) == 1

        cached_metrics = epic.get_cached_metrics(session=db_session)
        assert cached_metrics == metrics

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_persona_metrics_include_statuses(self, db_session, epic):
        """Persona metrics should expose status annotations from thresholds."""
        from src.shared.metrics.thresholds import get_threshold_service

        epic.total_story_points = 10
        epic.completed_story_points = 5
        epic.velocity_points_per_sprint = 5
        epic.team_size = 2
        epic.test_coverage_percentage = 85
        epic.code_review_score = 8
        epic.technical_debt_hours = 30

        db_session.add(epic)
        db_session.commit()

        epic.update_metrics(
            force_recalculate=True, session=db_session, record_history=True
        )
        db_session.commit()

        thresholds = get_threshold_service()

        pm_metrics = epic.get_persona_specific_metrics(
            "PM", session=db_session, thresholds=thresholds
        )
        assert "timeline" in pm_metrics
        assert "velocity" in pm_metrics

        qa_metrics = epic.get_persona_specific_metrics(
            "QA", session=db_session, thresholds=thresholds
        )
        assert "quality" in qa_metrics
        assert "testing" in qa_metrics

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_cache_stale_detection(self, db_session, epic):
        """Test cache staleness detection."""
        from datetime import datetime, timedelta

        db_session.add(epic)
        db_session.commit()

        # Cache should be stale initially
        assert epic.is_metrics_cache_stale()

        # After caching, should not be stale
        epic.cache_metrics({"test": "data"}, session=db_session)
        assert not epic.is_metrics_cache_stale()

        # Should be stale after some time
        epic.metrics_cache_updated_at = datetime.now() - timedelta(minutes=20)
        assert epic.is_metrics_cache_stale(max_age_minutes=15)

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_metrics_history_trend(self, db_session, epic):
        """Test metric history tracking for trend analysis."""
        db_session.add(epic)
        db_session.commit()

        # Generate multiple metric snapshots
        epic.velocity_points_per_sprint = 5
        epic.force_refresh_metrics(session=db_session, record_history=True)
        db_session.commit()

        epic.velocity_points_per_sprint = 7
        epic.force_refresh_metrics(session=db_session, record_history=True)
        db_session.commit()

        epic.velocity_points_per_sprint = 6
        epic.force_refresh_metrics(session=db_session, record_history=True)
        db_session.commit()

        # Check history
        history = epic.get_metric_history(session=db_session, limit=5)
        assert len(history) == 3

        # Verify trend data
        velocities = [
            h["metrics"]["velocity_metrics"]["velocity_points_per_sprint"]
            for h in history
        ]
        assert 6 in velocities  # Most recent
        assert 7 in velocities
        assert 5 in velocities

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
    @pytest.mark.user_story("US-00052")
    def test_cache_only_access(self, db_session, epic):
        """Test accessing only cached metrics without recalculation."""
        db_session.add(epic)
        db_session.commit()

        # Should return None when no cache
        cached = epic.get_cached_metrics_only()
        assert cached is None

        # Cache some metrics
        test_metrics = {"velocity": 5, "completion": 25}
        epic.cache_metrics(test_metrics, session=db_session)
        db_session.commit()

        # Should return cached data
        cached = epic.get_cached_metrics_only()
        assert cached == test_metrics

        # Clear cache
        epic.clear_metrics_cache()
        assert epic.get_cached_metrics_only() is None
