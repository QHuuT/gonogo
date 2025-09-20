"""
Shared Testing Infrastructure

This module provides testing utilities, failure tracking, and analysis tools
for the GoNoGo project testing ecosystem.

Components:
- FailureTracker: Test failure tracking and pattern analysis
- FailureCategory: Categorization of different failure types
- FailureSeverity: Severity classification for failures
"""

from .failure_tracker import (
    FailureTracker,
    FailureCategory,
    FailureSeverity,
    TestFailure,
    FailurePattern,
    FailureStatistics
)

__all__ = [
    "FailureTracker",
    "FailureCategory",
    "FailureSeverity",
    "TestFailure",
    "FailurePattern",
    "FailureStatistics"
]