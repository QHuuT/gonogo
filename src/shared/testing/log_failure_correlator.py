#!/usr/bin/env python3
"""
Log-Failure Correlation Service

Correlates structured logs with test failures to provide comprehensive
debugging context and failure reproduction guides.

Related to: US-00026 Log-failure association and context preservation
Parent Epic: EP-00006 Test Logging and Reporting
"""

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..logging.logger import LogEntry, StructuredLogger, get_logger
from .failure_tracker import FailureTracker, TestFailure


@dataclass
class FailureContext:
    """Complete context information for a test failure."""

    failure_id: int
    test_id: str
    test_name: str
    failure_message: str
    stack_trace: Optional[str]

    # Correlated logs
    setup_logs: List[LogEntry]
    execution_logs: List[LogEntry]
    teardown_logs: List[LogEntry]

    # Environment context
    environment_info: Dict[str, Any]
    test_data: Dict[str, Any]
    execution_state: Dict[str, Any]

    # Debugging assistance
    reproduction_guide: str
    debugging_hints: List[str]
    related_failures: List[Dict[str, Any]]


@dataclass
class LogCorrelationSummary:
    """Summary of log-failure correlation analysis."""

    total_failures_processed: int
    failures_with_logs: int
    correlation_success_rate: float
    common_failure_patterns: List[Dict[str, Any]]
    debugging_insights: List[str]


class LogFailureCorrelator:
    """Service for correlating structured logs with test failures."""

    def __init__(
        self,
        failure_tracker: Optional[FailureTracker] = None,
        logger: Optional[StructuredLogger] = None,
    ):
        """Initialize the log-failure correlator."""
        self.failure_tracker = failure_tracker or FailureTracker()
        self.logger = logger or get_logger()

    def correlate_failure_with_logs(
        self, failure_id: int, time_window_minutes: int = 10
    ) -> Optional[FailureContext]:
        """
        Correlate a specific failure with its related logs.

        Args:
            failure_id: ID of the failure in the failure tracking database
            time_window_minutes: Time window to search for related logs

        Returns:
            FailureContext with correlated logs and debugging information
        """
        # Get failure details
        failure = self._get_failure_by_id(failure_id)
        if not failure:
            return None

        # Get correlated logs
        logs = self._get_logs_for_failure(failure, time_window_minutes)

        # Organize logs by phase
        setup_logs, execution_logs, teardown_logs = self._organize_logs_by_phase(logs)

        # Extract context information
        environment_info = self._extract_environment_context(logs)
        test_data = self._extract_test_data_context(logs)
        execution_state = self._extract_execution_state(logs)

        # Generate debugging assistance
        reproduction_guide = self._generate_reproduction_guide(
            failure, logs, environment_info
        )
        debugging_hints = self._generate_debugging_hints(failure, logs)
        related_failures = self._find_related_failures(failure)

        return FailureContext(
            failure_id=failure_id,
            test_id=failure["test_id"],
            test_name=failure["test_name"],
            failure_message=failure["failure_message"],
            stack_trace=failure["stack_trace"],
            setup_logs=setup_logs,
            execution_logs=execution_logs,
            teardown_logs=teardown_logs,
            environment_info=environment_info,
            test_data=test_data,
            execution_state=execution_state,
            reproduction_guide=reproduction_guide,
            debugging_hints=debugging_hints,
            related_failures=related_failures,
        )

    def correlate_all_recent_failures(self, days: int = 7) -> LogCorrelationSummary:
        """
        Correlate all recent failures with their logs.

        Args:
            days: Number of days back to process failures

        Returns:
            Summary of correlation analysis
        """
        # Get recent failures
        recent_failures = self._get_recent_failures(days)

        total_failures = len(recent_failures)
        failures_with_logs = 0
        failure_patterns = {}
        debugging_insights = []

        for failure in recent_failures:
            context = self.correlate_failure_with_logs(failure["id"])
            if context and (
                context.setup_logs or context.execution_logs or context.teardown_logs
            ):
                failures_with_logs += 1

                # Analyze patterns
                pattern_key = f"{failure['category']}:{failure.get('test_file', '').split('/')[-1]}"
                if pattern_key not in failure_patterns:
                    failure_patterns[pattern_key] = {
                        "category": failure["category"],
                        "test_file": failure.get("test_file", ""),
                        "count": 0,
                        "common_hints": [],
                    }
                failure_patterns[pattern_key]["count"] += 1

                # Collect debugging insights
                if context.debugging_hints:
                    debugging_insights.extend(context.debugging_hints)

        # Calculate success rate
        correlation_success_rate = (
            (failures_with_logs / total_failures * 100) if total_failures > 0 else 0
        )

        # Convert patterns to list and sort by frequency
        common_patterns = list(failure_patterns.values())
        common_patterns.sort(key=lambda x: x["count"], reverse=True)

        # Deduplicate debugging insights
        unique_insights = list(set(debugging_insights))

        return LogCorrelationSummary(
            total_failures_processed=total_failures,
            failures_with_logs=failures_with_logs,
            correlation_success_rate=correlation_success_rate,
            common_failure_patterns=common_patterns[:10],  # Top 10
            debugging_insights=unique_insights[:20],  # Top 20
        )

    def generate_failure_reproduction_script(self, failure_id: int) -> Optional[str]:
        """
        Generate a script to reproduce a specific failure.

        Args:
            failure_id: ID of the failure to create reproduction script for

        Returns:
            Python script content for reproducing the failure
        """
        context = self.correlate_failure_with_logs(failure_id)
        if not context:
            return None

        script_lines = [
            "#!/usr/bin/env python3",
            '"""',
            f"Failure Reproduction Script",
            f"Generated for: {context.test_name}",
            f"Failure: {context.failure_message}",
            f"Generated: {datetime.now().isoformat()}",
            '"""',
            "",
            "import pytest",
            "import os",
            "import sys",
            "from pathlib import Path",
            "",
            "# Environment setup",
        ]

        # Add environment variables
        for key, value in context.environment_info.items():
            if isinstance(value, str) and key.upper() == key:  # Likely env var
                script_lines.append(f'os.environ["{key}"] = "{value}"')

        script_lines.extend(
            [
                "",
                "# Test data setup",
                "test_data = " + json.dumps(context.test_data, indent=2),
                "",
                "# Reproduction command",
                f'# Run: pytest {context.test_name.split("::")[0]} -v',
                f"# Expected failure: {context.failure_message}",
                "",
                "if __name__ == '__main__':",
                "    print(f'Reproducing failure: {context.test_name}')",
                "    print(f'Expected error: {context.failure_message}')",
                '    print(f\'Environment: {context.environment_info.get("python_version", "unknown")}\')',
            ]
        )

        return "\n".join(script_lines)

    def export_correlation_report(self, output_path: Optional[Path] = None) -> str:
        """
        Export comprehensive correlation report.

        Args:
            output_path: Where to save the report (defaults to quality/reports/)

        Returns:
            Path to the generated report
        """
        if output_path is None:
            output_path = Path("quality/reports/log_correlation_report.json")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate correlation summary
        summary = self.correlate_all_recent_failures()

        # Get recent failures with full context
        recent_failures = self._get_recent_failures(7)
        failure_contexts = []

        for failure in recent_failures[:10]:  # Limit to top 10 for report size
            context = self.correlate_failure_with_logs(failure["id"])
            if context:
                # Convert to serializable format
                context_dict = asdict(context)
                # Convert LogEntry objects to dicts
                context_dict["setup_logs"] = [asdict(log) for log in context.setup_logs]
                context_dict["execution_logs"] = [
                    asdict(log) for log in context.execution_logs
                ]
                context_dict["teardown_logs"] = [
                    asdict(log) for log in context.teardown_logs
                ]
                failure_contexts.append(context_dict)

        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": asdict(summary),
            "failure_contexts": failure_contexts,
            "correlation_metadata": {
                "log_sources": ["structured_logging", "pytest_integration"],
                "correlation_strategies": [
                    "test_id_matching",
                    "temporal_correlation",
                    "session_correlation",
                ],
                "context_preservation": ["environment", "test_data", "execution_state"],
            },
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return str(output_path)

    def _get_failure_by_id(self, failure_id: int) -> Optional[Dict[str, Any]]:
        """Get failure details by ID from the failure tracker database."""
        with sqlite3.connect(self.failure_tracker.db_path) as conn:
            conn.row_factory = sqlite3.Row
            result = conn.execute(
                "SELECT * FROM test_failures WHERE id = ?", (failure_id,)
            ).fetchone()

        return dict(result) if result else None

    def _get_logs_for_failure(
        self, failure: Dict[str, Any], time_window_minutes: int
    ) -> List[LogEntry]:
        """Get logs related to a specific failure."""
        # Get logs around the failure time
        failure_time = datetime.fromisoformat(failure["last_seen"])
        start_time = failure_time - timedelta(minutes=time_window_minutes)
        end_time = failure_time + timedelta(minutes=5)  # Small buffer after failure

        # Get logs from the structured logger
        all_logs = self.logger.get_recent_logs(
            10000
        )  # Large number to get enough context

        # Filter by time and test correlation
        related_logs = []
        for log in all_logs:
            log_time = datetime.fromisoformat(log.timestamp)
            if start_time <= log_time <= end_time:
                # Check if log is related to this test
                if (
                    (
                        hasattr(log, "test_id")
                        and log.test_id
                        and log.test_id == failure.get("test_id")
                    )
                    or (
                        hasattr(log, "test_name")
                        and log.test_name
                        and log.test_name == failure["test_name"]
                    )
                    or (failure["test_name"] in str(log.message))
                ):
                    related_logs.append(log)

        return related_logs

    def _organize_logs_by_phase(
        self, logs: List[LogEntry]
    ) -> Tuple[List[LogEntry], List[LogEntry], List[LogEntry]]:
        """Organize logs into setup, execution, and teardown phases."""
        setup_logs = []
        execution_logs = []
        teardown_logs = []

        for log in logs:
            if hasattr(log, "tags") and log.tags:
                if (
                    "setup" in log.tags
                    or "test_lifecycle" in log.tags
                    and "start" in log.message.lower()
                ):
                    setup_logs.append(log)
                elif (
                    "teardown" in log.tags
                    or "test_lifecycle" in log.tags
                    and "teardown" in log.message.lower()
                ):
                    teardown_logs.append(log)
                else:
                    execution_logs.append(log)
            else:
                execution_logs.append(log)  # Default to execution phase

        return setup_logs, execution_logs, teardown_logs

    def _extract_environment_context(self, logs: List[LogEntry]) -> Dict[str, Any]:
        """Extract environment information from logs."""
        environment = {}

        for log in logs:
            if hasattr(log, "metadata") and log.metadata:
                # Look for environment-related metadata
                for key, value in log.metadata.items():
                    if key in [
                        "python_version",
                        "platform",
                        "environment",
                        "working_directory",
                    ]:
                        environment[key] = value

        return environment

    def _extract_test_data_context(self, logs: List[LogEntry]) -> Dict[str, Any]:
        """Extract test data and parameters from logs."""
        test_data = {}

        for log in logs:
            if hasattr(log, "metadata") and log.metadata:
                # Look for test-specific data
                for key, value in log.metadata.items():
                    if key.startswith("test_") or key in [
                        "input_data",
                        "parameters",
                        "fixtures",
                    ]:
                        test_data[key] = value

        return test_data

    def _extract_execution_state(self, logs: List[LogEntry]) -> Dict[str, Any]:
        """Extract execution state information from logs."""
        execution_state = {}

        for log in logs:
            if hasattr(log, "duration_ms") and log.duration_ms:
                execution_state["duration_ms"] = log.duration_ms
            if hasattr(log, "test_status") and log.test_status:
                execution_state["final_status"] = log.test_status

        return execution_state

    def _generate_reproduction_guide(
        self, failure: Dict[str, Any], logs: List[LogEntry], environment: Dict[str, Any]
    ) -> str:
        """Generate a guide for reproducing the failure."""
        guide_lines = [
            f"## Reproduction Guide for {failure['test_name']}",
            "",
            "### Environment Setup:",
        ]

        for key, value in environment.items():
            guide_lines.append(f"- {key}: {value}")

        guide_lines.extend(
            [
                "",
                "### Steps to Reproduce:",
                f"1. Run test: `pytest {failure.get('test_file', 'unknown')} -v`",
                f"2. Expected failure: {failure['failure_message']}",
                "",
                "### Log Analysis:",
            ]
        )

        if logs:
            guide_lines.append(f"- {len(logs)} related log entries found")
            guide_lines.append(f"- Test execution timeline available")
        else:
            guide_lines.append("- No correlated logs found")

        return "\n".join(guide_lines)

    def _generate_debugging_hints(
        self, failure: Dict[str, Any], logs: List[LogEntry]
    ) -> List[str]:
        """Generate debugging hints based on failure and log analysis."""
        hints = []

        # Category-specific hints
        category = failure.get("category", "unknown")
        if category == "assertion_error":
            hints.append("Check test assertions and expected vs actual values")
            hints.append("Review test data setup and fixture initialization")
        elif category == "import_error":
            hints.append("Verify Python path and module dependencies")
            hints.append("Check virtual environment activation")
        elif category == "timeout_error":
            hints.append("Review test performance and resource usage")
            hints.append("Check for network dependencies or slow operations")
        elif category == "unicode_error":
            hints.append("Verify file encoding and locale settings")
            hints.append("Check Windows console encoding configuration")

        # Log-based hints
        if logs:
            error_logs = [log for log in logs if log.level == "ERROR"]
            if error_logs:
                hints.append(
                    f"Found {len(error_logs)} error log entries - review for additional context"
                )

        return hints

    def _find_related_failures(self, failure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find failures related to the current one."""
        with sqlite3.connect(self.failure_tracker.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Find failures with same error hash or in same test file
            results = conn.execute(
                """
                SELECT id, test_name, failure_message, category, last_seen, occurrence_count
                FROM test_failures
                WHERE (error_hash = ? OR test_file = ?)
                AND id != ?
                ORDER BY last_seen DESC
                LIMIT 5
            """,
                (
                    failure.get("error_hash", ""),
                    failure.get("test_file", ""),
                    failure["id"],
                ),
            ).fetchall()

        return [dict(row) for row in results]

    def _get_recent_failures(self, days: int) -> List[Dict[str, Any]]:
        """Get recent failures from the failure tracker."""
        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.failure_tracker.db_path) as conn:
            conn.row_factory = sqlite3.Row
            results = conn.execute(
                """
                SELECT * FROM test_failures
                WHERE last_seen >= ?
                ORDER BY last_seen DESC
            """,
                (cutoff_date.isoformat(),),
            ).fetchall()

        return [dict(row) for row in results]
