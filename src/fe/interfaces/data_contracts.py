"""
Data Contracts for Backend/Frontend Communication

Defines the expected data structures that backend services
should provide to frontend views.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EpicData:
    """Contract for epic data from backend to frontend."""

    epic_id: str
    title: str
    description: Optional[str]
    status: str
    components: List[str]
    created_at: datetime
    updated_at: datetime

    # Calculated fields
    progress: float
    user_stories_count: int
    tests_count: int
    defects_count: int


@dataclass
class UserStoryData:
    """Contract for user story data."""

    user_story_id: str
    title: str
    description: Optional[str]
    status: str
    story_points: int
    epic_id: str
    created_at: datetime
    updated_at: datetime


@dataclass
class TestData:
    """Contract for test data."""

    test_id: str
    test_name: str
    test_type: str
    status: str
    file_path: str
    last_execution: Optional[datetime]
    epic_id: Optional[str]
    user_story_id: Optional[str]


@dataclass
class DefectData:
    """Contract for defect data."""

    defect_id: str
    title: str
    description: Optional[str]
    priority: str
    severity: str
    status: str
    epic_id: Optional[str]
    user_story_id: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class RTMMatrixData:
    """Contract for complete RTM matrix data."""

    epics: List[EpicData]
    metadata: Dict[str, Any]
    filters_applied: Dict[str, Any]
    generated_at: datetime


@dataclass
class FailureReportData:
    """Contract for failure report data."""

    stats: Dict[str, Any]
    top_failing_tests: List[Dict[str, Any]]
    patterns: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: datetime


# Type aliases for common data structures
MetricsData = Dict[str, Union[int, float, str]]
FilterData = Dict[str, Union[str, int, bool, List[str]]]
ComponentData = Dict[str, Any]
