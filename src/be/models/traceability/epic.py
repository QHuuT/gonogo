"""
Epic Model

Database model for Epic entities in the hybrid RTM system.
Epics are stored in database for advanced relationship management and progress calculation.

Related Issue: US-00052 - Database schema design for traceability relationships
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Architecture Decision: ADR-003 - Hybrid GitHub + Database RTM Architecture
"""

from sqlalchemy import Boolean, Column, Float, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import TraceabilityBase


class Epic(TraceabilityBase):
    """Epic entity for high-level feature groupings."""

    __tablename__ = "epics"

    # Epic-specific fields
    epic_id = Column(String(20), unique=True, nullable=False, index=True)
    # Format: EP-00001, EP-00002, etc.

    business_value = Column(Text)
    success_criteria = Column(Text)

    # Progress tracking
    total_story_points = Column(Integer, default=0, nullable=False)
    completed_story_points = Column(Integer, default=0, nullable=False)
    completion_percentage = Column(Float, default=0.0, nullable=False)

    # Priority and planning
    priority = Column(String(20), default="medium", index=True, nullable=False)
    # Values: critical, high, medium, low

    # Risk assessment
    risk_level = Column(String(20), default="medium", nullable=False)
    # Values: low, medium, high, critical

    # GDPR implications
    gdpr_applicable = Column(Boolean, default=False, index=True, nullable=False)
    gdpr_considerations = Column(Text)

    # Relationships
    # User Stories - hybrid relationship (cached in DB, source of truth in GitHub)
    user_stories = relationship(
        "UserStory", back_populates="epic", cascade="all, delete-orphan"
    )

    # Tests - direct database relationship
    tests = relationship("Test", back_populates="epic", cascade="all, delete-orphan")

    # Defects - indirect relationship through user stories and tests
    defects = relationship("Defect", back_populates="epic")

    # Indexes for performance
    __table_args__ = (
        Index("idx_epic_status_priority", "status", "priority"),
        Index("idx_epic_completion", "completion_percentage"),
        Index("idx_epic_release", "target_release_version", "priority"),
    )

    def __init__(self, epic_id: str, title: str, **kwargs):
        """Initialize Epic with required fields."""
        super().__init__(title=title, **kwargs)
        self.epic_id = epic_id

        # Set defaults for fields that are NOT NULL
        if self.total_story_points is None:
            self.total_story_points = 0
        if self.completed_story_points is None:
            self.completed_story_points = 0
        if self.completion_percentage is None:
            self.completion_percentage = 0.0
        if self.priority is None:
            self.priority = "medium"
        if self.risk_level is None:
            self.risk_level = "medium"
        if self.gdpr_applicable is None:
            self.gdpr_applicable = False

    def calculate_completion_percentage(self):
        """Calculate completion percentage based on story points."""
        if self.total_story_points == 0:
            return 0.0
        return (self.completed_story_points / self.total_story_points) * 100.0

    def update_progress(self, completed_points: int, total_points: int):
        """Update progress metrics."""
        self.completed_story_points = completed_points
        self.total_story_points = total_points
        self.completion_percentage = self.calculate_completion_percentage()

    def to_dict(self):
        """Convert to dictionary with Epic-specific fields."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "epic_id": self.epic_id,
                "business_value": self.business_value,
                "success_criteria": self.success_criteria,
                "total_story_points": self.total_story_points,
                "completed_story_points": self.completed_story_points,
                "completion_percentage": self.completion_percentage,
                "priority": self.priority,
                "risk_level": self.risk_level,
                "gdpr_applicable": self.gdpr_applicable,
                "gdpr_considerations": self.gdpr_considerations,
                "test_count": len(self.tests) if self.tests else 0,
                "user_story_count": len(self.user_stories) if self.user_stories else 0,
                "defect_count": len(self.defects) if self.defects else 0,
            }
        )
        return base_dict

    def __repr__(self):
        return f"<Epic(epic_id='{self.epic_id}', title='{self.title}', status='{self.status}', completion={self.completion_percentage:.1f}%)>"
