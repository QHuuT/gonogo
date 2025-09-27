"""
Capability/Program Area Model for Strategic Epic Grouping

Provides strategic grouping of related Epics into Program Areas/Capabilities
for portfolio management, resource allocation, and cross-Epic dependency
tracking.

Related Issue: US-00062 - Program Areas/Capabilities - Epic Grouping and
Strategic Management
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

from datetime import datetime
from typing import Dict

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base


class Capability(Base):
    """
    Program Area/Capability model for strategic Epic grouping.

    Represents a business capability or program area that groups related Epics
    for strategic management, portfolio tracking, and resource allocation.
    """

    __tablename__ = "capabilities"

    id = Column(Integer, primary_key=True, index=True)
    capability_id = Column(
        String(20), unique=True, nullable=False, index=True
    )  # CAP-00001
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Strategic Information
    strategic_priority = Column(
        String(20), default="medium"
    )  # critical, high, medium, low
    business_value_theme = Column(
        String(100)
    )  # e.g., "User Experience", "Infrastructure", "Compliance"
    owner = Column(String(100))  # Person/Team responsible for this capability

    # Business Metrics
    estimated_business_impact_score = Column(Float, default=0.0)  # 0-100 scale
    roi_target_percentage = Column(Float, default=0.0)
    strategic_alignment_score = Column(
        Float, default=0.0
    )  # How well aligned with company strategy

    # Timeline
    planned_start_date = Column(DateTime)
    planned_completion_date = Column(DateTime)
    actual_start_date = Column(DateTime)
    actual_completion_date = Column(DateTime)

    # Status and Progress
    status = Column(
        String(50), default="planned"
    )  # planned, active, on-hold, completed, cancelled
    completion_percentage = Column(Float, default=0.0)

    # Resource Planning
    estimated_team_size = Column(Integer, default=1)
    budget_allocated = Column(Float, default=0.0)
    budget_consumed = Column(Float, default=0.0)

    # Risk Management
    risk_level = Column(
        String(20), default="medium"
    )  # critical, high, medium, low
    risk_notes = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    epics = relationship("Epic", back_populates="capability", lazy="dynamic")
    dependencies_as_parent = relationship(
    "CapabilityDependency",
    foreign_keys="[CapabilityDependency.parent_capability_id]",
    back_populates="parent_capability",
    lazy="dynamic",
    
)
    dependencies_as_dependent = relationship(
    "CapabilityDependency",
    foreign_keys="[CapabilityDependency.dependent_capability_id]",
    back_populates="dependent_capability",
    lazy="dynamic",
    
)

    def __repr__(self):
        return f"<Capability {self.capability_id}: {self.name}>"

    def calculate_completion_percentage(self) -> float:
        """Calculate completion based on Epic completion."""
        epics = list(self.epics)
        if not epics:
            return 0.0

        total_weight = len(epics)
        completed_weight = sum(
            1 for epic in epics if epic.completion_percentage >= 100.0
        )
        partial_weight = sum(
            epic.completion_percentage / 100.0
            for epic in epics
            if epic.completion_percentage < 100.0
        )

        return ((completed_weight + partial_weight) / total_weight) * 100.0

    def get_epic_count_by_status(self) -> Dict[str, int]:
        """Get count of Epics grouped by status."""
        epics = list(self.epics)
        status_counts = {}

        for epic in epics:
            status = epic.status
            status_counts[status] = status_counts.get(status, 0) + 1

        return status_counts

    def calculate_business_metrics(self) -> Dict[str, float]:
        """Calculate aggregated business metrics from child Epics."""
        epics = list(self.epics)
        if not epics:
            return {
    
                "total_story_points": 0.0,
                "average_roi": 0.0,
                "average_business_impact": 0.0,
                "total_estimated_days": 0.0,
            
}

        total_story_points = sum(epic.total_story_points for epic in epics)
        roi_scores = [
            epic.roi_percentage for epic in epics if epic.roi_percentage > 0
        ]
        impact_scores = [
            epic.business_impact_score
            for epic in epics
            if epic.business_impact_score > 0
        ]
        duration_days = [
            epic.estimated_duration_days
            for epic in epics
            if epic.estimated_duration_days
        ]

        return {
    
            "total_story_points": total_story_points,
            "average_roi": (
                sum(roi_scores) / len(roi_scores) if roi_scores else 0.0
            ),
            "average_business_impact": (
                (sum(impact_scores) / len(impact_scores))
                if impact_scores
                else 0.0
            ),
            "total_estimated_days": (
                sum(duration_days) if duration_days else 0.0
            ),
        
}

    def get_critical_path_analysis(self) -> Dict:
        """Analyze critical path through this capability's dependencies."""
        # This would integrate with Epic dependency system
        # For now, return basic structure
        return {
    
            "has_critical_dependencies": (
                len(list(self.dependencies_as_parent)) > 0
            ),
            "blocks_other_capabilities": (
                len(list(self.dependencies_as_parent)) > 0
            ),
            "blocked_by_capabilities": (
                len(list(self.dependencies_as_dependent)) > 0
            ),
            "risk_score": self._calculate_dependency_risk(),
        
}

    def _calculate_dependency_risk(self) -> float:
        """Calculate risk score based on dependencies and Epic status."""
        # Simple risk calculation - can be enhanced
        blocking_deps = len(
            list(self.dependencies_as_dependent.filter_by(is_active=True))
        )
        epic_risk_scores = [
            epic.dependency_risk_score
            for epic in self.epics
            if hasattr(epic, "dependency_risk_score")
        ]

        base_risk = blocking_deps * 10  # Each blocking dependency adds 10 risk
        epic_risk = (
            (sum(epic_risk_scores) / len(epic_risk_scores)
             if epic_risk_scores else 0)
        )

        return min(base_risk + epic_risk, 100.0)  # Cap at 100

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
    
            "id": self.id,
            "capability_id": self.capability_id,
            "name": self.name,
            "description": self.description,
            "strategic_priority": self.strategic_priority,
            "business_value_theme": self.business_value_theme,
            "owner": self.owner,
            "status": self.status,
            "completion_percentage": self.completion_percentage,
            "estimated_business_impact_score": (
                self.estimated_business_impact_score
            ),
            "roi_target_percentage": self.roi_target_percentage,
            "strategic_alignment_score": (
                self.strategic_alignment_score
            ),
            "risk_level": self.risk_level,
            "epic_count": self.epics.count(),
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else None
            ),
        
}


class CapabilityDependency(Base):
    """
    Dependencies between Capabilities for strategic planning.

    Tracks high-level dependencies between Program Areas/Capabilities
    for portfolio planning and resource scheduling.
    """

    __tablename__ = "capability_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    parent_capability_id = Column(
        Integer, ForeignKey("capabilities.id"), nullable=False
    )
    dependent_capability_id = Column(
        Integer, ForeignKey("capabilities.id"), nullable=False
    )

    # Dependency Information
    dependency_type = Column(
        String(50), default="strategic"
    )  # strategic, technical, informational, resource
    priority = Column(
        String(20), default="medium"
    )  # critical, high, medium, low
    rationale = Column(Text)  # Why this dependency exists

    # Impact Assessment
    estimated_impact_weeks = Column(
        Integer
    )  # Impact in weeks if dependency is delayed
    risk_mitigation_notes = Column(Text)

    # Status
    is_active = Column(Boolean, default=True)
    is_resolved = Column(Boolean, default=False)
    resolution_date = Column(DateTime)
    resolution_notes = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by = Column(String(100))  # Who identified this dependency

    # Relationships
    parent_capability = relationship(
    "Capability",
    foreign_keys=[parent_capability_id],
    back_populates="dependencies_as_parent",
    
)
    dependent_capability = relationship(
    "Capability",
    foreign_keys=[dependent_capability_id],
    back_populates="dependencies_as_dependent",
    
)

    def __repr__(self):
        return (
    f"<CapabilityDependency {self.parent_capability_id} "
    f"-> {self.dependent_capability_id}>"
)

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
    
            "id": self.id,
            "parent_capability_id": self.parent_capability_id,
            "dependent_capability_id": self.dependent_capability_id,
            "dependency_type": self.dependency_type,
            "priority": self.priority,
            "rationale": self.rationale,
            "estimated_impact_weeks": (
                self.estimated_impact_weeks
            ),
            "is_active": self.is_active,
            "is_resolved": self.is_resolved,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        
}
