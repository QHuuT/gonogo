"""
Pytest Integration for Automatic Failure Tracking

This module integrates the FailureTracker with pytest to automatically
capture and analyze test failures during test execution.

Related to: US-00025 Test failure tracking and reporting
"""

import platform
import sys
from datetime import datetime
from pathlib import Path

import pytest

from .failure_tracker import (
    FailureTracker,
    TestFailure,
)


class FailureTrackingPlugin:
    """Pytest plugin for automatic failure tracking."""

    def __init__(self):
        """Initialize the failure tracking plugin."""
        self.failure_tracker = FailureTracker()
        self.session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.execution_mode = "standard"
        self.current_session_failures = []

    def pytest_configure(self, config):
        """Configure plugin with pytest session details."""
        # Get execution mode from test runner plugin if available
        if hasattr(config.option, "mode"):
            self.execution_mode = config.option.mode

    def pytest_runtest_logreport(self, report):
        """Capture test failure information from pytest reports."""
        if report.when == "call" and report.outcome == "failed":
            self._record_test_failure(report)

    def _record_test_failure(self, report):
        """Process and record a test failure."""
        # Extract test information
        test_id = report.nodeid
        test_name = report.nodeid.split("::")[-1]
        test_file = (
            (
                report.fspath.relto(Path.cwd())
                if hasattr(report, "fspath")
                else "unknown"
            )
        )

        # Extract failure information
        failure_message = (
            str(report.longrepr.reprcrash.message)
            if report.longrepr and hasattr(report.longrepr, "reprcrash")
            else "Unknown error"
        )
        stack_trace = str(report.longrepr) if report.longrepr else ""

        # Create failure record
        failure = TestFailure(
    test_id=test_id,
    test_name=test_name,
    test_file=str(test_file
),
            failure_message=failure_message,
            stack_trace=stack_trace,
            session_id=self.session_id,
            execution_mode=self.execution_mode,
            environment_info=self._get_environment_info(),
            metadata={
    
                "duration": getattr(report,
    "duration",
    0),
                "keywords": (
                    list(report.keywords.keys()) if hasattr(report,
    "keywords") else []
                ),
                "markers": [m.name for m in getattr(report,
    "markers",
    [])],
                "python_version": f"{sys.version_info.major
}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": platform.platform(),
            },
        )

        # Auto-categorize and determine severity
        failure.category = self.failure_tracker.categorize_failure(
            failure_message, stack_trace
        )
        failure.severity = self.failure_tracker.determine_severity(failure)

        # Record the failure
        try:
            failure_id = self.failure_tracker.record_failure(failure)
            self.current_session_failures.append(failure_id)
        except Exception as e:
            # Don't let failure tracking break the test run
            print(f"Warning: Failed to record test failure: {e}")

    def _get_environment_info(self) -> str:
        """Collect environment information for failure context."""
        env_info = {
    
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "pytest_version": pytest.__version__,
        
}
        return str(env_info)

    def pytest_sessionfinish(self, session, exitstatus):
        """Generate failure summary at end of test session."""
        if self.current_session_failures:
            print(f"\n📊 Failure Tracking Summary:")
            print(f"   Session ID: {self.session_id}")
            print(
                f"   New failures recorded: "
                f"{len(self.current_session_failures)}"
            )
            print(f"   Execution mode: {self.execution_mode}")

            # Get recent statistics
            try:
                stats = self.failure_tracker.get_failure_statistics(days=7)
                print(f"   7-day failure rate: {stats.failure_rate:.1f}%")
                print(
                    f"   Most common category: "
                    f"{stats.most_common_category.value}"
                )

                if stats.critical_failure_count > 0:
                    print(
                        f"   ⚠️  Critical failures: "
                        f"{stats.critical_failure_count}"
                    )

                if stats.flaky_test_count > 0:
                    print(
                        f"   🔄 Flaky tests detected: {stats.flaky_test_count}"
                    )

            except Exception as e:
                print(f"   Warning: Could not generate statistics: {e}")


def pytest_configure(config):
    """Register the failure tracking plugin with pytest."""
    config.pluginmanager.register(FailureTrackingPlugin(), "failure_tracking")


# Integration with existing test runner plugin
def get_failure_tracking_hooks():
    """Get failure tracking hooks for integration with test runner plugin."""
    return {
    
        "pytest_runtest_logreport": "failure_tracking",
        "pytest_sessionfinish": "failure_tracking",
    
}
