"""
Epic Metric History Model

Stores historical metric snapshots for an Epic so dashboards can display
trends without recalculating data each time.

Related Issue: US-00071 - Extend Epic model for metrics
Parent Epic: EP-00010 - Multi-persona traceability dashboard
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from .base import Base


class EpicMetricHistory(Base):
    """Historical snapshot of Epic metrics."""

    __tablename__ = "epic_metric_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    epic_id = Column(
        Integer,
        ForeignKey("epics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    captured_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    metrics = Column(Text, nullable=False)

    epic = relationship("Epic", back_populates="metric_history")

    def __init__(
        self,
        epic_id: int,
        metrics: str,
        captured_at: Optional[datetime] = None,
        **kwargs,
    ):
        self.epic_id = epic_id
        self.metrics = metrics
        self.captured_at = captured_at or datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "epic_id": self.epic_id,
            "captured_at": (self.captured_at.isoformat() if self.captured_at else None),
            "metrics": self.metrics,
        }
