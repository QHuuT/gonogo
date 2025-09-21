"""
pytest Integration for Structured Logging

Integrates the structured logging system with pytest to automatically
capture test execution information and generate structured logs.
"""

import time
import uuid
from typing import Any, Dict, Optional

import pytest

from .config import LoggingConfig
from .logger import StructuredLogger, get_logger


class PytestLoggingPlugin:
    """pytest plugin for structured logging integration."""

    def __init__(self, logger: Optional[StructuredLogger] = None):
        """Initialize the pytest logging plugin."""
        self.logger = logger or get_logger()
        self._test_start_times: Dict[str, float] = {}
        self._test_sessions: Dict[str, str] = {}

    def pytest_runtest_setup(self, item):
        """Called before each test is run."""
        test_id = str(uuid.uuid4())
        test_name = f"{item.module.__name__}::{item.function.__name__}"

        # Store test information
        self._test_sessions[item.nodeid] = test_id
        self._test_start_times[item.nodeid] = time.time()

        # Log test start
        self.logger.test_started(
            test_id=test_id,
            test_name=test_name,
            metadata={
                "file": str(item.fspath),
                "function": item.function.__name__,
                "module": item.module.__name__,
                "markers": [marker.name for marker in item.iter_markers()],
                "nodeid": item.nodeid,
            },
        )

        # Store test_id in item for access during test
        item.test_id = test_id

    def pytest_runtest_call(self, item):
        """Called during test execution."""
        # Add test context to any logs generated during test
        if hasattr(item, "test_id"):
            # This would require modifying the global logger context
            # For now, we'll just ensure the test_id is available
            pass

    def pytest_runtest_teardown(self, item, nextitem):
        """Called after each test completes."""
        test_id = self._test_sessions.get(item.nodeid)
        if not test_id:
            return

        test_name = f"{item.module.__name__}::{item.function.__name__}"
        start_time = self._test_start_times.get(item.nodeid, time.time())
        duration_ms = (time.time() - start_time) * 1000

        # Log test completion (this will be updated by pytest_runtest_logreport)
        self.logger.info(
            f"Test teardown: {test_name}",
            test_id=test_id,
            test_name=test_name,
            duration_ms=duration_ms,
            tags=["test_lifecycle", "teardown"],
        )

    def pytest_runtest_logreport(self, report):
        """Called for each test phase report."""
        if report.when != "call":  # Only process the main test call phase
            return

        test_id = self._test_sessions.get(report.nodeid)
        if not test_id:
            return

        test_name = f"{report.fspath}::{report.location[2]}"
        start_time = self._test_start_times.get(report.nodeid, time.time())
        duration_ms = report.duration * 1000 if hasattr(report, "duration") else 0

        # Determine test outcome and log accordingly
        if report.passed:
            self.logger.test_passed(
                test_id=test_id,
                test_name=test_name,
                duration_ms=duration_ms,
                metadata={"outcome": "passed"},
            )
        elif report.failed:
            error_message = str(report.longrepr) if report.longrepr else "Test failed"
            stack_trace = self._extract_stack_trace(report)

            self.logger.test_failed(
                test_id=test_id,
                test_name=test_name,
                duration_ms=duration_ms,
                error_message=error_message,
                stack_trace=stack_trace,
                metadata={
                    "outcome": "failed",
                    "failure_type": self._classify_failure(report),
                },
            )
        elif report.skipped:
            skip_reason = str(report.longrepr) if report.longrepr else "Test skipped"
            self.logger.test_skipped(
                test_id=test_id,
                test_name=test_name,
                reason=skip_reason,
                metadata={"outcome": "skipped"},
            )

        # Clean up
        self._test_start_times.pop(report.nodeid, None)
        self._test_sessions.pop(report.nodeid, None)

    def pytest_sessionstart(self, session):
        """Called at the start of the test session."""
        self.logger.info(
            "Test session started",
            tags=["session_lifecycle", "start"],
            metadata={
                "pytest_version": pytest.__version__,
                "session_id": str(uuid.uuid4()),
            },
        )

    def pytest_sessionfinish(self, session, exitstatus):
        """Called at the end of the test session."""
        # Get session summary
        test_summary = self._generate_session_summary()

        self.logger.info(
            "Test session finished",
            tags=["session_lifecycle", "finish"],
            metadata={"exit_status": exitstatus, "summary": test_summary},
        )

        # Flush all logs
        self.logger.flush()

    def _extract_stack_trace(self, report) -> Optional[str]:
        """Extract stack trace from test report."""
        if hasattr(report, "longrepr") and report.longrepr:
            if hasattr(report.longrepr, "reprtraceback"):
                return str(report.longrepr.reprtraceback)
            else:
                return str(report.longrepr)
        return None

    def _classify_failure(self, report) -> str:
        """Classify the type of test failure."""
        if not hasattr(report, "longrepr") or not report.longrepr:
            return "unknown"

        error_text = str(report.longrepr).lower()

        if "assertionerror" in error_text:
            return "assertion"
        elif "timeout" in error_text:
            return "timeout"
        elif "connection" in error_text or "network" in error_text:
            return "network"
        elif "import" in error_text or "module" in error_text:
            return "import"
        elif "permission" in error_text or "access" in error_text:
            return "permission"
        else:
            return "runtime"

    def _generate_session_summary(self) -> Dict[str, Any]:
        """Generate a summary of the test session."""
        recent_logs = self.logger.get_recent_logs(1000)
        test_logs = [
            log
            for log in recent_logs
            if log.test_status and log.test_status != "started"
        ]

        if not test_logs:
            return {"total_tests": 0}

        # Count by status
        status_counts = {}
        total_duration = 0

        for log in test_logs:
            status = log.test_status
            status_counts[status] = status_counts.get(status, 0) + 1
            if log.duration_ms:
                total_duration += log.duration_ms

        return {
            "total_tests": len(test_logs),
            "status_counts": status_counts,
            "total_duration_ms": total_duration,
            "average_duration_ms": total_duration / len(test_logs) if test_logs else 0,
        }


def setup_pytest_logging(config: Optional[LoggingConfig] = None) -> PytestLoggingPlugin:
    """Set up pytest logging integration."""
    logger = get_logger(config)
    return PytestLoggingPlugin(logger)


# pytest plugin registration function
def pytest_configure(config):
    """Configure pytest with structured logging."""
    if not hasattr(config, "_structured_logging_plugin"):
        config._structured_logging_plugin = setup_pytest_logging()
        config.pluginmanager.register(config._structured_logging_plugin)
