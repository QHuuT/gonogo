"""
User Story Model

Database model for User Story metadata in the hybrid RTM system.
User Stories remain in GitHub Issues but metadata is cached in database for relationships and reporting.

Related Issue: US-00052 - Database schema design for traceability relationships
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Architecture Decision: ADR-003 - Hybrid GitHub + Database RTM Architecture
"""

from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import TraceabilityBase


class UserStory(TraceabilityBase):
    """User Story metadata cached from GitHub Issues for hybrid RTM system."""

    __tablename__ = "user_stories"

    # User Story identification
    user_story_id = Column(String(20), unique=True, nullable=False, index=True)
    # Format: US-00001, US-00002, etc.

    # Epic relationship (database foreign key)
    epic_id = Column(Integer, ForeignKey("epics.id"), nullable=False, index=True)
    epic = relationship("Epic")

    # GitHub Issue metadata (cached for performance)
    github_issue_number = Column(Integer, unique=True, nullable=False, index=True)
    github_issue_state = Column(String(20), index=True)  # open, closed
    github_labels = Column(Text)  # JSON string of labels
    github_assignees = Column(Text)  # JSON string of assignees

    # User Story specifics
    story_points = Column(Integer, default=0, index=True, nullable=False)
    acceptance_criteria = Column(Text)
    business_value = Column(Text)

    # Priority and planning
    priority = Column(String(20), default="medium", index=True, nullable=False)
    # Values: critical, high, medium, low

    sprint = Column(String(50), index=True)

    # Progress tracking
    implementation_status = Column(
        String(20), default="todo", index=True, nullable=False
    )
    # Values: todo, in_progress, in_review, done, blocked

    # BDD Integration
    has_bdd_scenarios = Column(Boolean, default=False, index=True, nullable=False)
    bdd_feature_files = Column(Text)  # JSON array of feature file paths

    # GDPR implications
    affects_gdpr = Column(Boolean, default=False, index=True, nullable=False)
    gdpr_considerations = Column(Text)

    # Dependencies tracking
    depends_on_issues = Column(Text)  # JSON array of issue numbers
    blocks_issues = Column(Text)  # JSON array of issue numbers

    # Relationships
    tests = relationship(
        "Test",
        primaryjoin="UserStory.github_issue_number == Test.github_user_story_number",
        foreign_keys="Test.github_user_story_number",
        viewonly=True,
    )

    defects = relationship(
        "Defect",
        primaryjoin="UserStory.github_issue_number == Defect.github_user_story_number",
        foreign_keys="Defect.github_user_story_number",
        viewonly=True,
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_us_epic_status", "epic_id", "implementation_status"),
        Index("idx_us_priority_points", "priority", "story_points"),
        Index("idx_us_release_sprint", "target_release_version", "sprint"),
        Index("idx_us_github_state", "github_issue_state", "github_issue_number"),
    )

    def __init__(
        self, user_story_id: str, epic_id: int, github_issue_number: int, **kwargs
    ):
        """Initialize User Story with required fields."""
        super().__init__(**kwargs)
        self.user_story_id = user_story_id
        self.epic_id = epic_id
        self.github_issue_number = github_issue_number

        # Set defaults for fields that are NOT NULL
        if self.story_points is None:
            self.story_points = 0
        if self.priority is None:
            self.priority = "medium"
        if self.implementation_status is None:
            self.implementation_status = "todo"
        if self.has_bdd_scenarios is None:
            self.has_bdd_scenarios = False
        if self.affects_gdpr is None:
            self.affects_gdpr = False

    def update_from_github(self, github_data: dict):
        """Update metadata from GitHub issue data."""
        self.github_issue_state = github_data.get("state", "open")
        self.github_labels = str(github_data.get("labels", []))
        self.github_assignees = str(github_data.get("assignees", []))

        # Update title and description from GitHub
        if github_data.get("title"):
            self.title = github_data["title"]
        if github_data.get("body"):
            self.description = github_data["body"]

    def calculate_test_coverage(self) -> dict:
        """Calculate test coverage metrics."""
        if not self.tests:
            return {"total_tests": 0, "passed_tests": 0, "coverage_percentage": 0.0}

        total_tests = len(self.tests)
        passed_tests = sum(
            1 for test in self.tests if test.last_execution_status == "passed"
        )
        coverage_percentage = (
            (passed_tests / total_tests * 100.0) if total_tests > 0 else 0.0
        )

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "coverage_percentage": coverage_percentage,
        }

    def to_dict(self):
        """Convert to dictionary with User Story specific fields."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "user_story_id": self.user_story_id,
                "epic_id": self.epic_id,
                "github_issue_number": self.github_issue_number,
                "github_issue_state": self.github_issue_state,
                "story_points": self.story_points,
                "acceptance_criteria": self.acceptance_criteria,
                "business_value": self.business_value,
                "priority": self.priority,
                "sprint": self.sprint,
                "implementation_status": self.implementation_status,
                "has_bdd_scenarios": self.has_bdd_scenarios,
                "affects_gdpr": self.affects_gdpr,
                "gdpr_considerations": self.gdpr_considerations,
                "test_coverage": self.calculate_test_coverage(),
                "defect_count": len(self.defects) if self.defects else 0,
            }
        )
        return base_dict

    def __repr__(self):
        return f"<UserStory(user_story_id='{self.user_story_id}', epic_id={self.epic_id}, github_issue={self.github_issue_number}, status='{self.implementation_status}')>"
