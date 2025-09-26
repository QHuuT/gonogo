"""
Unit tests for GitHubSyncManager status synchronization.

Ensures GitHub state/label data persist to the RTM database exactly as
expected so dashboard consumers always see accurate implementation status.

Related Issue: US-00059 - Comprehensive GitHub-database sync manager
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tools.github_sync_manager import GitHubSyncManager
from src.be.models.traceability.base import Base
from src.be.models.traceability.epic import Epic
from src.be.models.traceability.user_story import UserStory
from src.be.models.traceability.capability import Capability


@pytest.fixture
def db_session():
    """Set up an in-memory SQLite session for isolated tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sync_manager(db_session):
    """Instantiate a GitHubSyncManager backed by the test session."""
    manager = GitHubSyncManager(dry_run=False, verbose=False)
    manager.db_session = db_session
    return manager


@pytest.fixture
def epic(db_session):
    """Provide a persisted epic for linking user stories."""
    epic = Epic(epic_id="EP-00005", title="Requirements Traceability Matrix Automation", github_issue_number=5000)
    db_session.add(epic)
    db_session.commit()
    return epic


def _make_user_story(db_session, epic, story_id, issue_number, implementation_status="planned"):
    """Create and persist a basic UserStory record for sync tests."""
    story = UserStory(
        user_story_id=story_id,
        epic_id=epic.id,
        github_issue_number=issue_number,
        title=f"Story {story_id}",
        story_points=3,
        priority="medium",
    )
    story.github_issue_state = "open"
    story.github_labels = "[]"
    story.implementation_status = implementation_status
    db_session.add(story)
    db_session.commit()
    return story


@pytest.mark.epic("EP-00005")
@pytest.mark.user_story("US-00059", "US-00060")
@pytest.mark.component("backend")
class TestGitHubSyncManagerStatus:
    """Status-alignment behaviours for GitHub sync."""

    def test_sync_updates_status_from_github_labels(self, sync_manager, db_session, epic):
        """status/in-progress labels must persist as in_progress implementation status."""
        story = _make_user_story(db_session, epic, "US-00059", 59)
        sync_manager.github_issues = [
            {
                "number": story.github_issue_number,
                "state": "open",
                "title": story.title,
                "body": "",
                "labels": [{"name": "status/in-progress"}],
                "assignees": [],
            }
        ]

        results = sync_manager.sync_user_stories()

        assert any(r.entity_id == story.user_story_id and r.updated for r in results)

        refreshed = (
            db_session.query(UserStory)
            .filter(UserStory.user_story_id == story.user_story_id)
            .one()
        )
        assert refreshed.implementation_status == "in_progress"
        assert refreshed.github_issue_state == "open"
        assert "status/in-progress" in refreshed.github_labels

    def test_sync_marks_completed_when_issue_closed(self, sync_manager, db_session, epic):
        """Closed GitHub issues should flip implementation status to completed."""
        story = _make_user_story(
            db_session, epic, "US-00060", 60, implementation_status="in_progress"
        )
        sync_manager.github_issues = [
            {
                "number": story.github_issue_number,
                "state": "closed",
                "title": story.title,
                "body": "",
                "labels": [],
                "assignees": [],
            }
        ]

        results = sync_manager.sync_user_stories()

        assert any(r.entity_id == story.user_story_id and r.updated for r in results)

        refreshed = (
            db_session.query(UserStory)
            .filter(UserStory.user_story_id == story.user_story_id)
            .one()
        )
        assert refreshed.implementation_status == "completed"
        assert refreshed.github_issue_state == "closed"

    def test_sync_epics_assigns_default_capability(self, sync_manager, db_session, epic):
        """Epics without capability labels should fall back to the canonical mapping."""
        sync_manager.github_issues = [
            {
                "number": epic.github_issue_number,
                "state": "open",
                "title": epic.title,
                "body": "",
                "labels": [],
                "assignees": [],
            }
        ]

        results = sync_manager.sync_epics()
        assert any(r.entity_id == epic.epic_id and r.updated for r in results)

        refreshed_epic = (
            db_session.query(Epic)
            .filter(Epic.epic_id == epic.epic_id)
            .one()
        )
        capability = db_session.get(Capability, refreshed_epic.capability_id)
        assert capability is not None
        assert capability.capability_id == "CAP-00002"

        matching_suggestions = [
            suggestion
            for suggestion in sync_manager.capability_label_suggestions
            if suggestion["epic_id"] == epic.epic_id
        ]
        assert matching_suggestions
        assert matching_suggestions[0]["label"] == "capability/CAP-00002"
