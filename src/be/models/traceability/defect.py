"""
Defect Model

Database model for Defect metadata in the hybrid RTM system.
Defects remain in GitHub Issues but metadata is cached in database for
relationships and reporting.

Related Issue: US-00052 - Database schema design for traceability relationships
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Architecture Decision: ADR-003 - Hybrid GitHub + Database RTM Architecture
"""

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import TraceabilityBase


class Defect(TraceabilityBase):
    """Defect metadata cached from GitHub Issues for hybrid RTM system."""

    __tablename__ = "defects"

    # Defect identification
    defect_id = Column(String(20), unique=True, nullable=False, index=True)
    # Format: DEF-00001, DEF-00002, etc.

    # GitHub Issue metadata (cached for performance)
    github_issue_number = Column(Integer, unique=True, nullable=False, index=True)
    github_issue_state = Column(String(20), index=True)  # open, closed
    github_labels = Column(Text)  # JSON string of labels
    github_assignees = Column(Text)  # JSON string of assignees

    # Traceability relationships
    # Note: Defects can relate to Epic, User Story, or Test
    epic_id = Column(Integer, ForeignKey("epics.id"), nullable=True, index=True)
    epic = relationship("Epic")

    github_user_story_number = Column(Integer, nullable=True, index=True)
    # References User Story GitHub issue number

    test_id = Column(Integer, ForeignKey("tests.id"), nullable=True, index=True)
    test = relationship("Test")

    # Defect classification
    defect_type = Column(String(50), default="bug", index=True)
    # Values: bug, regression, enhancement, security, performance, usability

    severity = Column(String(20), default="medium", index=True)
    # Values: critical, high, medium, low

    priority = Column(String(20), default="medium", index=True)
    # Values: critical, high, medium, low

    # Technical details
    environment = Column(String(100), index=True)
    # e.g., development, staging, production, windows, linux

    browser_version = Column(String(100))
    os_version = Column(String(100))

    # Reproduction and resolution
    steps_to_reproduce = Column(Text)
    expected_behavior = Column(Text)
    actual_behavior = Column(Text)

    resolution_details = Column(Text)
    root_cause = Column(Text)

    # Effort estimation
    estimated_hours = Column(Float)
    actual_hours = Column(Float)

    # Quality metrics
    found_in_phase = Column(String(50), index=True)
    # Values: development, testing, staging, production

    escaped_to_production = Column(Boolean, default=False, index=True)

    # Security and GDPR
    is_security_issue = Column(Boolean, default=False, index=True)
    affects_gdpr = Column(Boolean, default=False, index=True)
    gdpr_impact_details = Column(Text)

    # Regression tracking (enhanced with base version tracking)
    is_regression = Column(Boolean, default=False, index=True)

    # Customer impact
    affects_customers = Column(Boolean, default=False, index=True)
    customer_impact_details = Column(Text)

    # Component classification (inherited from User Story or manually set)
    component = Column(String(50), nullable=True, index=True)
    # Values: frontend, backend, database, security, testing, ci-cd,
    # documentation

    # Indexes for performance
    __table_args__ = (
        Index("idx_defect_epic_severity", "epic_id", "severity"),
        Index("idx_defect_type_priority", "defect_type", "priority"),
        Index("idx_defect_user_story", "github_user_story_number"),
        Index("idx_defect_test_relation", "test_id"),
        Index("idx_defect_production", "escaped_to_production", "severity"),
        Index("idx_defect_security_gdpr", "is_security_issue", "affects_gdpr"),
        Index("idx_defect_environment", "environment", "found_in_phase"),
    )

    def __init__(self, defect_id: str, github_issue_number: int, **kwargs):
        """Initialize Defect with required fields."""
        super().__init__(**kwargs)
        self.defect_id = defect_id
        self.github_issue_number = github_issue_number

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

    def calculate_impact_score(self) -> int:
        """Calculate defect impact score for prioritization."""
        score = 0

        # Severity scoring
        severity_scores = {"critical": 10, "high": 7, "medium": 4, "low": 1}
        score += severity_scores.get(self.severity, 0)

        # Customer impact
        if self.affects_customers:
            score += 5

        # Production escape
        if self.escaped_to_production:
            score += 5

        # Security issue
        if self.is_security_issue:
            score += 8

        # GDPR impact
        if self.affects_gdpr:
            score += 6

        return score

    def is_high_priority(self) -> bool:
        """Determine if defect should be high priority."""
        return (
            self.severity in ["critical", "high"]
            or self.is_security_issue
            or self.escaped_to_production
            or self.affects_gdpr
        )

    def inherit_component_from_user_story(self, session):
        """Inherit component from related User Story if not already set."""
        if self.component is not None:
            return  # Component already set, don't override

        if self.github_user_story_number:
            from .user_story import UserStory

            user_story = (
                session.query(UserStory)
                .filter(UserStory.github_issue_number == self.github_user_story_number)
                .first()
            )

            if user_story and user_story.component:
                self.component = user_story.component

    def to_dict(self):
        """Convert to dictionary with Defect specific fields."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "defect_id": self.defect_id,
                "github_issue_number": self.github_issue_number,
                "github_issue_state": self.github_issue_state,
                "epic_id": self.epic_id,
                "github_user_story_number": self.github_user_story_number,
                "test_id": self.test_id,
                "defect_type": self.defect_type,
                "severity": self.severity,
                "priority": self.priority,
                "environment": self.environment,
                "browser_version": self.browser_version,
                "os_version": self.os_version,
                "steps_to_reproduce": self.steps_to_reproduce,
                "expected_behavior": self.expected_behavior,
                "actual_behavior": self.actual_behavior,
                "resolution_details": self.resolution_details,
                "root_cause": self.root_cause,
                "estimated_hours": self.estimated_hours,
                "actual_hours": self.actual_hours,
                "found_in_phase": self.found_in_phase,
                "escaped_to_production": self.escaped_to_production,
                "is_security_issue": self.is_security_issue,
                "affects_gdpr": self.affects_gdpr,
                "gdpr_impact_details": self.gdpr_impact_details,
                "is_regression": self.is_regression,
                "affects_customers": self.affects_customers,
                "customer_impact_details": self.customer_impact_details,
                "component": self.component,
                "impact_score": self.calculate_impact_score(),
                "is_high_priority": self.is_high_priority(),
            }
        )
        return base_dict

    def __repr__(self):
        return (
            f"<Defect("
            f"defect_id='{self.defect_id}', "
            f"github_issue={self.github_issue_number}, "
            f"severity='{self.severity}', "
            f"status='{self.status}'"
            f")>"
        )
