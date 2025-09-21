"""
Base Model for Traceability Entities

Provides common fields and functionality for all RTM database entities.

Related Issue: US-00052 - Database schema design for traceability relationships
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Architecture Decision: ADR-003 - Hybrid GitHub + Database RTM Architecture
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class TraceabilityBase(Base):
    """Base class for all traceability entities with common audit fields."""

    __abstract__ = True

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core identification
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)

    # Status tracking
    status = Column(String(50), nullable=False, default="planned", index=True)
    # Possible values: planned, in_progress, completed, blocked, cancelled

    # GitHub integration
    github_issue_number = Column(Integer, nullable=True, index=True)
    github_issue_url = Column(String(255), nullable=True)

    # Version tracking (consistent across all entities)
    # Development versions (git-based, internal development)
    introduced_in_commit = Column(String(40), index=True)  # Git commit SHA
    introduced_in_branch = Column(String(100), index=True)  # Git branch name
    resolved_in_commit = Column(String(40), index=True)  # Resolution commit SHA

    # Release versions (customer-facing versions)
    target_release_version = Column(
        String(50), index=True
    )  # Planned release (e.g., v1.2.0)
    released_in_version = Column(
        String(50), index=True
    )  # Actual release (e.g., v1.1.5)

    # Version context
    affects_versions = Column(Text)  # JSON array of affected versions
    fixed_in_versions = Column(Text)  # JSON array of versions where fixed

    # Audit trail
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    def __init__(self, **kwargs):
        """Initialize TraceabilityBase with default values."""
        super().__init__(**kwargs)

        # Set default status if not provided
        if self.status is None:
            self.status = "planned"

    def set_git_context(self, commit_sha: str, branch: str):
        """Set git context for version tracking."""
        self.introduced_in_commit = commit_sha
        self.introduced_in_branch = branch

    def mark_resolved(self, commit_sha: str, release_version: str = None):
        """Mark as resolved with git and release context."""
        self.resolved_in_commit = commit_sha
        if release_version:
            self.released_in_version = release_version

        # Update status if not already completed
        if self.status not in ["completed", "done"]:
            self.status = "completed"

    def add_affected_version(self, version: str):
        """Add a version to the affected versions list."""
        import json

        try:
            versions = (
                json.loads(self.affects_versions) if self.affects_versions else []
            )
        except (json.JSONDecodeError, TypeError):
            versions = []

        if version not in versions:
            versions.append(version)
            self.affects_versions = json.dumps(versions)

    def add_fixed_version(self, version: str):
        """Add a version to the fixed versions list."""
        import json

        try:
            versions = (
                json.loads(self.fixed_in_versions) if self.fixed_in_versions else []
            )
        except (json.JSONDecodeError, TypeError):
            versions = []

        if version not in versions:
            versions.append(version)
            self.fixed_in_versions = json.dumps(versions)

    def is_fixed_in_version(self, version: str) -> bool:
        """Check if issue is fixed in a specific version."""
        import json

        try:
            versions = (
                json.loads(self.fixed_in_versions) if self.fixed_in_versions else []
            )
            return version in versions
        except (json.JSONDecodeError, TypeError):
            return False

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, title='{self.title}', status='{self.status}')>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "github_issue_number": self.github_issue_number,
            "github_issue_url": self.github_issue_url,
            # Version tracking
            "introduced_in_commit": self.introduced_in_commit,
            "introduced_in_branch": self.introduced_in_branch,
            "resolved_in_commit": self.resolved_in_commit,
            "target_release_version": self.target_release_version,
            "released_in_version": self.released_in_version,
            "affects_versions": self.affects_versions,
            "fixed_in_versions": self.fixed_in_versions,
            # Audit
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
