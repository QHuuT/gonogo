"""
Test Model

Database model for Test entities in the hybrid RTM system.
Tests are stored in database with execution results and traceability chains.

Related Issue: US-00052 - Database schema design for traceability relationships
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Architecture Decision: ADR-003 - Hybrid GitHub + Database RTM Architecture
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import TraceabilityBase


class Test(TraceabilityBase):
    """Test entity for BDD scenarios, unit tests, and integration tests."""

    __tablename__ = "tests"

    # Test identification
    test_type = Column(String(50), nullable=False, index=True)
    # Values: unit, integration, bdd, security, e2e

    test_file_path = Column(String(500), nullable=False, index=True)
    test_function_name = Column(String(255), index=True)

    # BDD-specific fields
    bdd_feature_file = Column(String(500), index=True)
    bdd_scenario_name = Column(String(255), index=True)

    # Relationships (Hybrid Architecture)
    epic_id = Column(Integer, ForeignKey("epics.id"), nullable=True, index=True)
    epic = relationship("Epic", back_populates="tests")

    # GitHub issue references (US/DEF remain in GitHub)
    github_user_story_number = Column(Integer, nullable=True, index=True)
    github_defect_number = Column(Integer, nullable=True, index=True)

    # Test execution tracking
    last_execution_time = Column(DateTime, nullable=True)
    last_execution_status = Column(String(20), default="not_run", index=True)
    # Values: not_run, passed, failed, skipped, error

    execution_duration_ms = Column(Float, nullable=True)
    execution_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)

    # Test metadata
    test_priority = Column(String(20), default="medium", index=True, nullable=False)
    # Values: critical, high, medium, low

    is_automated = Column(Boolean, default=True, index=True, nullable=False)
    requires_manual_verification = Column(Boolean, default=False, nullable=False)

    # Coverage information
    code_coverage_percentage = Column(Float, nullable=True)
    covered_files = Column(Text)  # JSON array of covered file paths

    # GDPR and security
    tests_gdpr_compliance = Column(Boolean, default=False, index=True, nullable=False)
    tests_security_aspects = Column(Boolean, default=False, index=True, nullable=False)

    # Error tracking
    last_error_message = Column(Text)
    last_error_traceback = Column(Text)

    # Component classification (inherited from User Story or manually set)
    component = Column(String(50), nullable=True, index=True)
    # Values: frontend, backend, database, security, testing, ci-cd, documentation

    # Test category (smoke, edge, regression, performance, error-handling, compliance-gdpr, compliance-rgaa, compliance-doc, compliance-project-management)
    test_category = Column(String(50), nullable=True, index=True)
    # Values: smoke, edge, regression, performance, error-handling, compliance-gdpr, compliance-rgaa, compliance-doc, compliance-project-management

    # Indexes for performance
    __table_args__ = (
        Index("idx_test_epic_type", "epic_id", "test_type"),
        Index(
            "idx_test_execution_status", "last_execution_status", "last_execution_time"
        ),
        Index(
            "idx_test_github_references",
            "github_user_story_number",
            "github_defect_number",
        ),
        Index("idx_test_bdd_scenario", "bdd_feature_file", "bdd_scenario_name"),
        Index("idx_test_file_path", "test_file_path"),
    )

    def __init__(self, test_type: str, test_file_path: str, **kwargs):
        """Initialize Test with required fields."""
        super().__init__(**kwargs)
        self.test_type = test_type
        self.test_file_path = test_file_path

        # Set defaults for fields that are NOT NULL
        if self.execution_count is None:
            self.execution_count = 0
        if self.failure_count is None:
            self.failure_count = 0
        if self.test_priority is None:
            self.test_priority = "medium"
        if self.is_automated is None:
            self.is_automated = True
        if self.requires_manual_verification is None:
            self.requires_manual_verification = False
        if self.tests_gdpr_compliance is None:
            self.tests_gdpr_compliance = False
        if self.tests_security_aspects is None:
            self.tests_security_aspects = False
        if self.last_execution_status is None:
            self.last_execution_status = "not_run"

    def update_execution_result(
        self, status: str, duration_ms: float = None, error_message: str = None
    ):
        """Update test execution results."""
        from datetime import datetime

        self.last_execution_time = datetime.now()
        self.last_execution_status = status
        self.execution_count += 1

        if duration_ms is not None:
            self.execution_duration_ms = duration_ms

        if status == "failed":
            self.failure_count += 1
            if error_message:
                self.last_error_message = error_message
        else:
            # Clear error on successful run
            self.last_error_message = None
            self.last_error_traceback = None

    def get_success_rate(self) -> float:
        """Calculate test success rate."""
        if self.execution_count == 0:
            return 0.0
        return (
            (self.execution_count - self.failure_count) / self.execution_count
        ) * 100.0

    def inherit_component_from_user_story(self, session):
        """Inherit component from related User Story if not already set."""
        if self.component is not None:
            return  # Component already set, don't override

        if self.github_user_story_number:
            from .user_story import UserStory
            user_story = session.query(UserStory).filter(
                UserStory.github_issue_number == self.github_user_story_number
            ).first()

            if user_story and user_story.component:
                self.component = user_story.component

    def to_dict(self):
        """Convert to dictionary with Test-specific fields."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "test_type": self.test_type,
                "test_file_path": self.test_file_path,
                "test_function_name": self.test_function_name,
                "bdd_feature_file": self.bdd_feature_file,
                "bdd_scenario_name": self.bdd_scenario_name,
                "epic_id": self.epic_id,
                "github_user_story_number": self.github_user_story_number,
                "github_defect_number": self.github_defect_number,
                "last_execution_time": (
                    self.last_execution_time.isoformat()
                    if self.last_execution_time
                    else None
                ),
                "last_execution_status": self.last_execution_status,
                "execution_duration_ms": self.execution_duration_ms,
                "execution_count": self.execution_count,
                "failure_count": self.failure_count,
                "success_rate": self.get_success_rate(),
                "test_priority": self.test_priority,
                "is_automated": self.is_automated,
                "requires_manual_verification": self.requires_manual_verification,
                "code_coverage_percentage": self.code_coverage_percentage,
                "tests_gdpr_compliance": self.tests_gdpr_compliance,
                "tests_security_aspects": self.tests_security_aspects,
                "component": self.component,
                "test_category": self.test_category,
                "last_error_message": self.last_error_message,
            }
        )
        return base_dict

    def __repr__(self):
        return f"<Test(type='{self.test_type}', file='{self.test_file_path}', status='{self.last_execution_status}', epic_id={self.epic_id})>"
