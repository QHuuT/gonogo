"""
Epic Model

Database model for Epic entities in the hybrid RTM system.
Epics are stored in database for advanced relationship management and progress calculation.

Related Issue: US-00052 - Database schema design for traceability relationships
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Architecture Decision: ADR-003 - Hybrid GitHub + Database RTM Architecture
"""

from sqlalchemy import Boolean, Column, DateTime, Float, Index, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from typing import Optional, Dict, List

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

    # Component classification
    component = Column(String(50), nullable=False, index=True, default='backend')

    # Advanced Metrics (US-00071) - Multi-persona dashboard metrics
    # Planning and timeline metrics
    estimated_duration_days = Column(Integer, nullable=True)  # Estimated duration in days
    actual_duration_days = Column(Integer, nullable=True)  # Actual duration (when completed)
    planned_start_date = Column(DateTime, nullable=True)  # Planned start date
    actual_start_date = Column(DateTime, nullable=True)  # When work actually started
    planned_end_date = Column(DateTime, nullable=True)  # Planned completion date
    actual_end_date = Column(DateTime, nullable=True)  # When actually completed

    # Velocity and productivity metrics
    initial_scope_estimate = Column(Integer, default=0, nullable=False)  # Original story points estimate
    scope_creep_percentage = Column(Float, default=0.0, nullable=False)  # % of scope increase
    velocity_points_per_sprint = Column(Float, default=0.0, nullable=False)  # Average velocity
    team_size = Column(Integer, default=1, nullable=False)  # Team members working on epic

    # Quality metrics
    defect_density = Column(Float, default=0.0, nullable=False)  # Defects per story point
    test_coverage_percentage = Column(Float, default=0.0, nullable=False)  # Test coverage %
    code_review_score = Column(Float, default=0.0, nullable=False)  # Code quality score
    technical_debt_hours = Column(Integer, default=0, nullable=False)  # Estimated tech debt

    # Stakeholder and business metrics
    stakeholder_satisfaction_score = Column(Float, default=0.0, nullable=False)  # 0-10 score
    business_impact_score = Column(Float, default=0.0, nullable=False)  # Estimated business impact
    roi_percentage = Column(Float, default=0.0, nullable=False)  # Return on investment
    user_adoption_rate = Column(Float, default=0.0, nullable=False)  # % user adoption (post-release)

    # Tracking and history
    last_metrics_update = Column(DateTime, nullable=True)  # When metrics were last calculated
    metrics_calculation_frequency = Column(String(20), default="daily", nullable=False)  # daily, weekly, etc.

    # Epic Label Management (US-00006)
    epic_label_name = Column(String(50), nullable=True, index=True)
    # Format: "rtm-automation", "github-project", etc. (used in epic/x GitHub labels)

    github_epic_label = Column(String(100), nullable=True, index=True)
    # Format: "epic/rtm-automation" (full GitHub label name)

    last_github_sync = Column(String(50), nullable=True)
    # Timestamp of last sync with GitHub labels

    # Program Areas/Capabilities (US-00062) - Strategic Epic Grouping
    capability_id = Column(Integer, ForeignKey("capabilities.id"), nullable=True, index=True)
    # Links Epic to a Program Area/Capability for strategic grouping

    # Relationships
    # User Stories - hybrid relationship (cached in DB, source of truth in GitHub)
    user_stories = relationship(
        "UserStory", back_populates="epic", cascade="all, delete-orphan"
    )

    # Tests - direct database relationship
    tests = relationship("Test", back_populates="epic", cascade="all, delete-orphan")

    # Defects - indirect relationship through user stories and tests
    defects = relationship("Defect", back_populates="epic")

    # Dependencies - Epic dependency relationships (US-00070)
    dependencies_as_parent = relationship(
        "EpicDependency",
        foreign_keys="[EpicDependency.parent_epic_id]",
        back_populates="parent_epic",
        cascade="all, delete-orphan"
    )

    dependencies_as_dependent = relationship(
        "EpicDependency",
        foreign_keys="[EpicDependency.dependent_epic_id]",
        back_populates="dependent_epic",
        cascade="all, delete-orphan"
    )

    # Program Areas/Capabilities (US-00062) - Strategic grouping relationship
    capability = relationship("Capability", back_populates="epics")

    # Indexes for performance
    __table_args__ = (
        Index("idx_epic_status_priority", "status", "priority"),
        Index("idx_epic_completion", "completion_percentage"),
        Index("idx_epic_release", "target_release_version", "priority"),
        Index("idx_epic_component", "component"),
        Index("idx_epic_label", "epic_label_name", "github_epic_label"),
        Index("idx_epic_capability", "capability_id"),  # Program Areas/Capabilities index

        # Advanced metrics indexes (US-00071)
        Index("idx_epic_timeline", "planned_start_date", "planned_end_date"),
        Index("idx_epic_velocity", "velocity_points_per_sprint", "completion_percentage"),
        Index("idx_epic_quality", "defect_density", "test_coverage_percentage"),
        Index("idx_epic_business_impact", "business_impact_score", "roi_percentage"),
        Index("idx_epic_metrics_update", "last_metrics_update"),
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
        if self.component is None:
            self.component = "backend"

        # Set defaults for advanced metrics (US-00071)
        if self.initial_scope_estimate is None:
            self.initial_scope_estimate = self.total_story_points
        if self.scope_creep_percentage is None:
            self.scope_creep_percentage = 0.0
        if self.velocity_points_per_sprint is None:
            self.velocity_points_per_sprint = 0.0
        if self.team_size is None:
            self.team_size = 1
        if self.defect_density is None:
            self.defect_density = 0.0
        if self.test_coverage_percentage is None:
            self.test_coverage_percentage = 0.0
        if self.code_review_score is None:
            self.code_review_score = 0.0
        if self.technical_debt_hours is None:
            self.technical_debt_hours = 0
        if self.stakeholder_satisfaction_score is None:
            self.stakeholder_satisfaction_score = 0.0
        if self.business_impact_score is None:
            self.business_impact_score = 0.0
        if self.roi_percentage is None:
            self.roi_percentage = 0.0
        if self.user_adoption_rate is None:
            self.user_adoption_rate = 0.0
        if self.metrics_calculation_frequency is None:
            self.metrics_calculation_frequency = "daily"

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

    def get_component_label(self) -> str:
        """Convert component to GitHub label format."""
        mapping = {
            'frontend/ui': 'component/frontend',
            'frontend': 'component/frontend',
            'backend/api': 'component/backend',
            'backend': 'component/backend',
            'database': 'component/database',
            'security/gdpr': 'component/security',
            'security': 'component/security',
            'testing': 'component/testing',
            'ci/cd': 'component/ci-cd',
            'ci-cd': 'component/ci-cd',
            'documentation': 'component/documentation'
        }
        component_key = self.component.lower().replace(' ', '/').replace('-', '/')
        return mapping.get(component_key, mapping.get(self.component.lower(), f'component/{self.component.lower().replace("/", "-").replace(" ", "-")}'))

    def validate_component(self) -> bool:
        """Validate component value against allowed options."""
        allowed = [
            'frontend/ui', 'frontend', 'backend/api', 'backend', 'database',
            'security/gdpr', 'security', 'testing', 'ci/cd', 'ci-cd', 'documentation'
        ]
        component_normalized = self.component.lower().replace(' ', '/').replace('-', '/')
        return component_normalized in allowed or self.component.lower() in allowed

    def get_inherited_components(self) -> list:
        """Get unique components from child User Stories."""
        if not self.user_stories:
            return []

        components = set()
        for user_story in self.user_stories:
            if user_story.component:
                components.add(user_story.component)

        return sorted(list(components))

    def update_component_from_user_stories(self):
        """Update Epic component based on child User Stories."""
        inherited_components = self.get_inherited_components()
        if inherited_components:
            # If Epic has multiple components, join them with comma
            self.component = ','.join(inherited_components)
        elif not self.component:
            # Default if no components found
            self.component = 'backend'

    def get_epic_label_name(self) -> str:
        """Get or generate epic label name for GitHub labels."""
        if self.epic_label_name:
            return self.epic_label_name

        # Generate from title if not set
        from tools.sync_epic_labels import generate_epic_label_name
        return generate_epic_label_name(self.title, self.epic_id)

    def get_github_epic_label(self) -> str:
        """Get full GitHub epic label (epic/name format)."""
        if self.github_epic_label:
            return self.github_epic_label

        # Generate from label name
        label_name = self.get_epic_label_name()
        return f"epic/{label_name}"

    def update_epic_label_info(self, label_name: str, sync_timestamp: str = None):
        """Update epic label information after GitHub sync."""
        self.epic_label_name = label_name
        self.github_epic_label = f"epic/{label_name}"
        if sync_timestamp:
            self.last_github_sync = sync_timestamp
        else:
            from datetime import datetime
            self.last_github_sync = datetime.now().isoformat()

    # Dependency management methods (US-00070)
    def get_blocking_dependencies(self):
        """Retourne les dépendances qui bloquent cet Epic."""
        return [
            dep for dep in self.dependencies_as_dependent
            if dep.is_active and dep.is_blocking() and not dep.is_resolved
        ]

    def get_blocked_epics(self):
        """Retourne les Epics bloqués par cet Epic."""
        return [
            dep.dependent_epic for dep in self.dependencies_as_parent
            if dep.is_active and dep.is_blocking() and not dep.is_resolved
        ]

    def is_blocked(self) -> bool:
        """Retourne True si cet Epic est bloqué par des dépendances."""
        return len(self.get_blocking_dependencies()) > 0

    def can_start(self) -> bool:
        """Retourne True si cet Epic peut commencer (pas de dépendances bloquantes non résolues)."""
        return not self.is_blocked()

    def get_dependency_risk_score(self) -> int:
        """Calcule un score de risque basé sur les dépendances."""
        score = 0

        # Pénalité pour être bloqué
        blocking_deps = self.get_blocking_dependencies()
        score += len(blocking_deps) * 5

        # Pénalité supplémentaire pour dépendances critiques
        for dep in blocking_deps:
            if dep.priority == 'critical':
                score += 10
            elif dep.priority == 'high':
                score += 5

        # Pénalité pour impact estimé élevé
        for dep in self.dependencies_as_dependent:
            if dep.estimated_impact_days and dep.estimated_impact_days > 5:
                score += dep.estimated_impact_days

        return score

    # Advanced Metrics Methods (US-00071) - Multi-persona dashboard calculations

    def calculate_all_metrics(self) -> Dict:
        """Calculate all advanced metrics for dashboard views."""
        return {
            "timeline_metrics": self.calculate_timeline_metrics(),
            "velocity_metrics": self.calculate_velocity_metrics(),
            "quality_metrics": self.calculate_quality_metrics(),
            "business_metrics": self.calculate_business_metrics(),
            "predictive_metrics": self.calculate_predictive_metrics()
        }

    def calculate_timeline_metrics(self) -> Dict:
        """Calculate timeline and planning metrics."""
        metrics = {}

        # Timeline deviation
        if self.planned_end_date and self.actual_end_date:
            planned_duration = (self.planned_end_date - self.planned_start_date).days if self.planned_start_date else 0
            actual_duration = (self.actual_end_date - self.actual_start_date).days if self.actual_start_date else 0
            metrics["schedule_variance_days"] = actual_duration - planned_duration
            metrics["schedule_variance_percentage"] = (metrics["schedule_variance_days"] / planned_duration * 100) if planned_duration > 0 else 0

        # Current timeline status
        if self.status != "completed" and self.planned_end_date:
            days_until_deadline = (self.planned_end_date - datetime.now()).days
            metrics["days_until_deadline"] = days_until_deadline
            metrics["is_at_risk"] = days_until_deadline < 7 and self.completion_percentage < 80

        # Duration estimates
        metrics["estimated_duration_days"] = self.estimated_duration_days
        metrics["actual_duration_days"] = self.actual_duration_days
        metrics["is_overdue"] = self.planned_end_date and datetime.now() > self.planned_end_date if self.planned_end_date else False

        return metrics

    def calculate_velocity_metrics(self) -> Dict:
        """Calculate velocity and productivity metrics."""
        metrics = {}

        # Scope metrics
        if self.initial_scope_estimate > 0:
            current_scope = self.total_story_points
            metrics["scope_creep_points"] = current_scope - self.initial_scope_estimate
            metrics["scope_creep_percentage"] = ((current_scope - self.initial_scope_estimate) / self.initial_scope_estimate) * 100

        # Velocity calculations
        metrics["velocity_points_per_sprint"] = self.velocity_points_per_sprint
        if self.team_size > 0:
            metrics["velocity_per_team_member"] = self.velocity_points_per_sprint / self.team_size

        # Completion rate
        if self.actual_start_date:
            days_in_progress = (datetime.now() - self.actual_start_date).days
            if days_in_progress > 0:
                metrics["points_completed_per_day"] = self.completed_story_points / days_in_progress
                metrics["estimated_completion_date"] = self.calculate_estimated_completion_date()

        return metrics

    def calculate_quality_metrics(self) -> Dict:
        """Calculate quality and technical metrics."""
        metrics = {}

        # Quality scores
        metrics["defect_density"] = self.defect_density
        metrics["test_coverage_percentage"] = self.test_coverage_percentage
        metrics["code_review_score"] = self.code_review_score
        metrics["technical_debt_hours"] = self.technical_debt_hours

        # Quality assessment
        defect_count = len(self.defects) if self.defects else 0
        if self.completed_story_points > 0:
            metrics["actual_defect_density"] = defect_count / self.completed_story_points

        # Quality trend
        metrics["quality_score"] = self.calculate_overall_quality_score()
        metrics["quality_grade"] = self.get_quality_grade(metrics["quality_score"])

        return metrics

    def calculate_business_metrics(self) -> Dict:
        """Calculate business value and impact metrics."""
        metrics = {}

        # Business scores
        metrics["business_impact_score"] = self.business_impact_score
        metrics["roi_percentage"] = self.roi_percentage
        metrics["stakeholder_satisfaction_score"] = self.stakeholder_satisfaction_score
        metrics["user_adoption_rate"] = self.user_adoption_rate

        # Business value calculations
        if self.completed_story_points > 0 and self.total_story_points > 0:
            completion_ratio = self.completed_story_points / self.total_story_points
            metrics["realized_business_value"] = self.business_impact_score * completion_ratio

        # Stakeholder metrics
        metrics["stakeholder_satisfaction_grade"] = self.get_satisfaction_grade(self.stakeholder_satisfaction_score)

        return metrics

    def calculate_predictive_metrics(self) -> Dict:
        """Calculate predictive analytics and forecasting."""
        metrics = {}

        # Completion prediction
        if self.velocity_points_per_sprint > 0:
            remaining_points = self.total_story_points - self.completed_story_points
            sprints_remaining = remaining_points / self.velocity_points_per_sprint
            metrics["estimated_sprints_remaining"] = sprints_remaining
            metrics["estimated_completion_date"] = self.calculate_estimated_completion_date()

        # Risk predictions
        risk_factors = []
        if self.is_blocked():
            risk_factors.append("blocked_by_dependencies")
        if self.scope_creep_percentage > 20:
            risk_factors.append("scope_creep")
        if self.defect_density > 0.5:
            risk_factors.append("quality_issues")

        metrics["risk_factors"] = risk_factors
        metrics["overall_risk_score"] = len(risk_factors) * 10 + self.get_dependency_risk_score()
        metrics["success_probability"] = max(0, min(100, 100 - metrics["overall_risk_score"]))

        return metrics

    def calculate_estimated_completion_date(self) -> Optional[datetime]:
        """Calculate estimated completion date based on current velocity."""
        if not self.velocity_points_per_sprint or self.velocity_points_per_sprint <= 0:
            return None

        remaining_points = self.total_story_points - self.completed_story_points
        if remaining_points <= 0:
            return datetime.now()  # Already completed

        # Assume 2-week sprints
        sprints_remaining = remaining_points / self.velocity_points_per_sprint
        days_remaining = sprints_remaining * 14  # 14 days per sprint

        return datetime.now() + timedelta(days=days_remaining)

    def calculate_overall_quality_score(self) -> float:
        """Calculate overall quality score (0-10)."""
        # Weight different quality factors
        coverage_score = min(10, self.test_coverage_percentage / 10)  # Max 10 for 100% coverage
        review_score = self.code_review_score  # Assuming 0-10 scale
        defect_penalty = min(5, self.defect_density * 2)  # Penalty for defects

        overall_score = (coverage_score + review_score - defect_penalty) / 2
        return max(0, min(10, overall_score))

    def get_quality_grade(self, score: float) -> str:
        """Convert quality score to letter grade."""
        if score >= 9: return "A+"
        elif score >= 8: return "A"
        elif score >= 7: return "B+"
        elif score >= 6: return "B"
        elif score >= 5: return "C+"
        elif score >= 4: return "C"
        elif score >= 3: return "D"
        else: return "F"

    def get_satisfaction_grade(self, score: float) -> str:
        """Convert stakeholder satisfaction to grade."""
        if score >= 9: return "Excellent"
        elif score >= 7: return "Good"
        elif score >= 5: return "Average"
        elif score >= 3: return "Below Average"
        else: return "Poor"

    def update_metrics(self, force_recalculate: bool = False) -> Dict:
        """Update all metrics and return calculated values."""
        now = datetime.now()

        # Check if update is needed
        if not force_recalculate and self.last_metrics_update:
            if self.metrics_calculation_frequency == "daily" and (now - self.last_metrics_update).days < 1:
                return self.calculate_all_metrics()
            elif self.metrics_calculation_frequency == "weekly" and (now - self.last_metrics_update).days < 7:
                return self.calculate_all_metrics()

        # Update calculated fields
        self.scope_creep_percentage = ((self.total_story_points - self.initial_scope_estimate) / self.initial_scope_estimate * 100) if self.initial_scope_estimate > 0 else 0

        # Calculate defect density
        defect_count = len(self.defects) if self.defects else 0
        self.defect_density = defect_count / self.completed_story_points if self.completed_story_points > 0 else 0

        # Update last calculation time
        self.last_metrics_update = now

        return self.calculate_all_metrics()

    def get_persona_specific_metrics(self, persona: str) -> Dict:
        """Get metrics tailored for specific dashboard personas."""
        all_metrics = self.calculate_all_metrics()

        timeline_metrics = all_metrics.get("timeline_metrics", {})
        velocity_metrics = all_metrics.get("velocity_metrics", {})
        business_metrics = all_metrics.get("business_metrics", {})
        predictive_metrics = all_metrics.get("predictive_metrics", {})
        quality_metrics = all_metrics.get("quality_metrics", {})

        persona_key = persona.lower()

        if persona_key == "pm":  # Project Manager
            return {
                "timeline": timeline_metrics,
                "velocity": velocity_metrics,
                "risk": {
                    "overall_risk_score": predictive_metrics.get("overall_risk_score", 0),
                    "success_probability": predictive_metrics.get("success_probability", 0),
                    "risk_factors": predictive_metrics.get("risk_factors", []),
                },
                "team_productivity": {
                    "velocity_per_team_member": velocity_metrics.get("velocity_per_team_member", 0),
                    "team_size": self.team_size,
                },
            }
        elif persona_key == "po":  # Product Owner
            return {
                "business_value": business_metrics,
                "scope": {
                    "scope_creep_percentage": velocity_metrics.get("scope_creep_percentage", 0),
                    "scope_creep_points": velocity_metrics.get("scope_creep_points", 0),
                },
                "stakeholder": {
                    "satisfaction_score": self.stakeholder_satisfaction_score or 0,
                    "satisfaction_grade": business_metrics.get("stakeholder_satisfaction_grade", "Unknown"),
                },
                "adoption": {
                    "user_adoption_rate": self.user_adoption_rate or 0,
                },
            }
        elif persona_key == "qa":  # Quality Assurance
            return {
                "quality": quality_metrics,
                "defects": {
                    "defect_count": len(self.defects) if self.defects else 0,
                    "defect_density": self.defect_density or 0,
                },
                "testing": {
                    "test_coverage": self.test_coverage_percentage or 0,
                    "test_count": len(self.tests) if self.tests else 0,
                },
                "technical_debt": {
                    "debt_hours": self.technical_debt_hours or 0,
                    "code_review_score": self.code_review_score or 0,
                },
            }
        else:
            # Return all metrics for unknown personas
            return all_metrics


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
                "component": self.component,
                "component_label": self.get_component_label(),
                "inherited_components": self.get_inherited_components(),
                "epic_label_name": self.epic_label_name,
                "github_epic_label": self.github_epic_label,
                "last_github_sync": self.last_github_sync,
                "test_count": len(self.tests) if self.tests else 0,
                "user_story_count": len(self.user_stories) if self.user_stories else 0,
                "defect_count": len(self.defects) if self.defects else 0,

                # Dependency information (US-00070)
                "is_blocked": self.is_blocked(),
                "can_start": self.can_start(),
                "dependency_risk_score": self.get_dependency_risk_score(),
                "blocking_dependencies_count": len(self.get_blocking_dependencies()),
                "blocked_epics_count": len(self.get_blocked_epics()),

                # Advanced metrics (US-00071) - Timeline metrics
                "estimated_duration_days": self.estimated_duration_days,
                "actual_duration_days": self.actual_duration_days,
                "planned_start_date": self.planned_start_date.isoformat() if self.planned_start_date else None,
                "actual_start_date": self.actual_start_date.isoformat() if self.actual_start_date else None,
                "planned_end_date": self.planned_end_date.isoformat() if self.planned_end_date else None,
                "actual_end_date": self.actual_end_date.isoformat() if self.actual_end_date else None,

                # Velocity and productivity metrics
                "initial_scope_estimate": self.initial_scope_estimate,
                "scope_creep_percentage": self.scope_creep_percentage,
                "velocity_points_per_sprint": self.velocity_points_per_sprint,
                "team_size": self.team_size,

                # Quality metrics
                "defect_density": self.defect_density,
                "test_coverage_percentage": self.test_coverage_percentage,
                "code_review_score": self.code_review_score,
                "technical_debt_hours": self.technical_debt_hours,

                # Business metrics
                "stakeholder_satisfaction_score": self.stakeholder_satisfaction_score,
                "business_impact_score": self.business_impact_score,
                "roi_percentage": self.roi_percentage,
                "user_adoption_rate": self.user_adoption_rate,

                # Metrics tracking
                "last_metrics_update": self.last_metrics_update.isoformat() if self.last_metrics_update else None,
                "metrics_calculation_frequency": self.metrics_calculation_frequency,

                # Program Areas/Capabilities (US-00062)
                "capability_id": self.capability_id,
                "capability_name": self.capability.name if self.capability else None,
                "capability_capability_id": self.capability.capability_id if self.capability else None,
                "capability_strategic_priority": self.capability.strategic_priority if self.capability else None,
            }
        )
        return base_dict

    def __repr__(self):
        return f"<Epic(epic_id='{self.epic_id}', title='{self.title}', status='{self.status}', completion={self.completion_percentage:.1f}%)>"
