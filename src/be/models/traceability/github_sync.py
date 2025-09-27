"""
GitHub Sync Model

Database model for tracking GitHub ↔ Database synchronization status.
Ensures data consistency in the hybrid RTM architecture.

Related Issue: US-00052 - Database schema design for traceability relationships
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Architecture Decision: ADR-003 - Hybrid GitHub + Database RTM Architecture
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from .base import TraceabilityBase


class GitHubSync(TraceabilityBase):
    """Tracks synchronization between GitHub Issues and database entities."""

    __tablename__ = "github_sync"

    # GitHub issue information
    github_issue_number = Column(Integer, nullable=False, index=True)
    github_issue_type = Column(String(20), nullable=False, index=True)
    # Values: epic, user_story, defect

    github_issue_title = Column(String(255), nullable=False)
    github_issue_state = Column(String(20), index=True)
    # Values: open, closed

    github_labels = Column(JSON)  # Array of label names
    github_assignees = Column(JSON)  # Array of assignee usernames
    github_milestone = Column(String(100), index=True)

    # Epic relationship (for US/DEF issues)
    referenced_epic_id = Column(String(20), index=True)  # EP-00001 format
    referenced_epic_db_id = Column(Integer, index=True)  # Database Epic.id

    # Sync tracking
    last_sync_time = Column(DateTime, default=func.now(), nullable=False)
    sync_status = Column(String(20), default="pending", index=True)
    # Values: pending, in_progress, completed, failed, conflict

    github_updated_at = Column(DateTime, nullable=True)
    github_etag = Column(String(100))  # For GitHub API caching

    # Conflict resolution
    has_conflicts = Column(Boolean, default=False, index=True)
    conflict_details = Column(JSON)  # Details about data conflicts
    conflict_resolution = Column(String(50))  # manual, github_wins, db_wins

    # Error tracking
    last_sync_error = Column(Text)
    sync_retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Metadata
    sync_source = Column(String(50), default="webhook", index=True)
    # Values: webhook, manual, scheduled, api_poll

    # Indexes for performance
    __table_args__ = (
        Index(
            "idx_github_sync_issue", "github_issue_number", "github_issue_type"
        ),
        Index("idx_github_sync_status", "sync_status", "has_conflicts"),
        Index(
            "idx_github_sync_epic",
            "referenced_epic_id",
            "referenced_epic_db_id"
        ),
        Index("idx_github_sync_time", "last_sync_time"),
    )

    def __init__(
        self,
        github_issue_number: int,
        github_issue_type: str,
        github_issue_title: str,
        **kwargs,
    ):
        """Initialize GitHub sync record."""
        super().__init__(
            title=f"Sync-{github_issue_type}-{github_issue_number}", **kwargs
        )
        self.github_issue_number = github_issue_number
        self.github_issue_type = github_issue_type
        self.github_issue_title = github_issue_title

    def mark_sync_completed(self):
        """Mark synchronization as completed."""
        self.sync_status = "completed"
        self.last_sync_time = func.now()
        self.has_conflicts = False
        self.conflict_details = None
        self.last_sync_error = None
        self.sync_retry_count = 0

    def mark_sync_failed(self, error_message: str):
        """Mark synchronization as failed with error."""
        self.sync_status = "failed"
        self.last_sync_time = func.now()
        self.last_sync_error = error_message
        self.sync_retry_count += 1

    def mark_conflict(self, conflict_details: dict):
        """Mark synchronization conflict."""
        self.sync_status = "conflict"
        self.has_conflicts = True
        self.conflict_details = conflict_details
        self.last_sync_time = func.now()

    def can_retry(self) -> bool:
        """Check if sync can be retried."""
        return self.sync_retry_count < self.max_retries

    def to_dict(self):
        """Convert to dictionary with GitHub sync specific fields."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "github_issue_number": self.github_issue_number,
                "github_issue_type": self.github_issue_type,
                "github_issue_title": self.github_issue_title,
                "github_issue_state": self.github_issue_state,
                "github_labels": self.github_labels,
                "github_assignees": self.github_assignees,
                "github_milestone": self.github_milestone,
                "referenced_epic_id": self.referenced_epic_id,
                "referenced_epic_db_id": self.referenced_epic_db_id,
                "last_sync_time": (
                    (
                        self.last_sync_time.isoformat()
                        if self.last_sync_time
                        else None
                    )
                ),
                "sync_status": self.sync_status,
                "github_updated_at": (
                    self.github_updated_at.isoformat()
                    if self.github_updated_at
                    else None
                ),
                "github_etag": self.github_etag,
                "has_conflicts": self.has_conflicts,
                "conflict_details": self.conflict_details,
                "conflict_resolution": self.conflict_resolution,
                "last_sync_error": self.last_sync_error,
                "sync_retry_count": self.sync_retry_count,
                "max_retries": self.max_retries,
                "sync_source": self.sync_source,
                "can_retry": self.can_retry(),
            }
        )
        return base_dict

    def __repr__(self):
        return (
            f"<GitHubSync(issue_number={self.github_issue_number}, "
            f"type='{self.github_issue_type}', "
            f"status='{self.sync_status}')>"
        )
