"""
Traceability Models Package

Database models for Requirements Traceability Matrix (RTM) system.
Implements the hybrid GitHub + Database architecture per ADR-003.

Related Issue: US-00052 - Database schema design for traceability relationships
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Architecture Decision: ADR-003 - Hybrid GitHub + Database RTM Architecture
"""

from .base import Base, TraceabilityBase
from .capability import Capability, CapabilityDependency
from .defect import Defect
from .epic import Epic
from .epic_dependency import EpicDependency
from .github_sync import GitHubSync
from .test import Test
from .user_story import UserStory

# Export all models for database migrations and imports
__all__ = [
    "TraceabilityBase",
    "Base",
    "Epic",
    "EpicDependency",
    "UserStory",
    "Defect",
    "Test",
    "GitHubSync",
    "Capability",
    "CapabilityDependency",
]
