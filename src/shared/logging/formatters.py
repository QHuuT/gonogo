"""
Log Formatters for GoNoGo Test System

Provides different formatting options for log output including JSON and
human-readable formats for different use cases.
"""

import json
from datetime import datetime
from typing import List, Optional

from .logger import LogEntry


class JSONFormatter:
    """Formats log entries as JSON."""

    def __init__(self, compact: bool = True, include_metadata: bool = True):
        """Initialize JSON formatter."""
        self.compact = compact
        self.include_metadata = include_metadata

    def format(self, entry: LogEntry) -> str:
        """Format a log entry as JSON."""
        entry_dict = {
            "timestamp": entry.timestamp,
            "level": entry.level,
            "message": entry.message,
        }

        # Add test-specific fields if present
        if entry.test_id:
            entry_dict["test_id"] = entry.test_id
        if entry.test_name:
            entry_dict["test_name"] = entry.test_name
        if entry.test_status:
            entry_dict["test_status"] = entry.test_status
        if entry.duration_ms is not None:
            entry_dict["duration_ms"] = entry.duration_ms

        # Add environment context
        if entry.environment:
            entry_dict["environment"] = entry.environment
        if entry.session_id:
            entry_dict["session_id"] = entry.session_id

        # Add optional fields
        if self.include_metadata and entry.metadata:
            entry_dict["metadata"] = entry.metadata
        if entry.stack_trace:
            entry_dict["stack_trace"] = entry.stack_trace
        if entry.tags:
            entry_dict["tags"] = entry.tags

        # Format JSON
        if self.compact:
            return json.dumps(entry_dict, separators=(",", ":"))
        else:
            return json.dumps(entry_dict, indent=2)

    def format_multiple(self, entries: List[LogEntry]) -> str:
        """Format multiple log entries as JSON array."""
        formatted_entries = [self.format(entry) for entry in entries]
        if self.compact:
            return "[" + ",".join(formatted_entries) + "]"
        else:
            return "[\n" + ",\n".join(formatted_entries) + "\n]"


class TestFormatter:
    """Human-readable formatter optimized for test output."""

    __test__ = False  # Tell pytest this is not a test class

    def __init__(
        self,
        show_timestamp: bool = True,
        show_session: bool = False,
        colorize: bool = False,
    ):
        """Initialize test formatter."""
        self.show_timestamp = show_timestamp
        self.show_session = show_session
        self.colorize = colorize

        # Color codes for terminal output
        self.colors = (
            {
                "DEBUG": "\033[36m",  # Cyan
                "INFO": "\033[32m",  # Green
                "WARNING": "\033[33m",  # Yellow
                "ERROR": "\033[31m",  # Red
                "CRITICAL": "\033[35m",  # Magenta
                "RESET": "\033[0m",  # Reset
            }
            if colorize
            else {}
        )

    def format(self, entry: LogEntry) -> str:
        """Format a log entry for human reading."""
        parts = []

        # Timestamp
        if self.show_timestamp:
            timestamp = self._format_timestamp(entry.timestamp)
            parts.append(f"[{timestamp}]")

        # Level with optional color
        level = entry.level.upper()
        if self.colorize and level in self.colors:
            level = f"{self.colors[level]}{level}{self.colors['RESET']}"
        parts.append(f"[{level}]")

        # Test information
        if entry.test_name:
            test_info = entry.test_name
            if entry.test_status:
                status_marker = self._get_status_marker(entry.test_status)
                test_info += f" {status_marker}"
            if entry.duration_ms is not None:
                test_info += f" ({entry.duration_ms:.1f}ms)"
            parts.append(f"[{test_info}]")

        # Session ID
        if self.show_session and entry.session_id:
            parts.append(f"[{entry.session_id}]")

        # Message
        parts.append(entry.message)

        # Additional information
        additional_info = []
        if entry.metadata:
            additional_info.append(f"metadata={entry.metadata}")
        if entry.tags:
            additional_info.append(f"tags={entry.tags}")

        if additional_info:
            parts.append(f"({', '.join(additional_info)})")

        line = " ".join(parts)

        # Add stack trace if present
        if entry.stack_trace:
            line += f"\nStack trace:\n{entry.stack_trace}"

        return line

    def _format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for display."""
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%H:%M:%S.%f")[:-3]  # HH:MM:SS.mmm
        except ValueError:
            return timestamp

    def _get_status_marker(self, status: str) -> str:
        """Get visual marker for test status."""
        markers = {
            "started": "🏃" if self.colorize else "→",
            "passed": "✅" if self.colorize else "✓",
            "failed": "❌" if self.colorize else "✗",
            "skipped": "⏭️" if self.colorize else "⊘",
        }
        return markers.get(status, "•")


class TableFormatter:
    """Formats log entries as a table."""

    def __init__(self, columns: Optional[List[str]] = None):
        """Initialize table formatter."""
        self.columns = columns or [
            "timestamp",
            "level",
            "test_name",
            "test_status",
            "duration_ms",
            "message",
        ]

    def format_header(self) -> str:
        """Format table header."""
        headers = []
        for col in self.columns:
            header = col.replace("_", " ").title()
            headers.append(header)

        # Create separator line
        separator = " | ".join("-" * len(h) for h in headers)
        header_line = " | ".join(headers)

        return f"{header_line}\n{separator}"

    def format_row(self, entry: LogEntry) -> str:
        """Format a single log entry as table row."""
        row_data = []

        for col in self.columns:
            value = getattr(entry, col, None)

            if col == "timestamp":
                value = self._format_timestamp(value) if value else ""
            elif col == "duration_ms":
                value = f"{value:.1f}ms" if value is not None else ""
            elif col == "test_status":
                value = value or ""
            elif col == "message":
                # Truncate long messages
                value = (value[:47] + "...") if value and len(value) > 50 else (value or "")
            else:
                value = str(value) if value is not None else ""

            row_data.append(value)

        return " | ".join(row_data)

    def format_multiple(self, entries: List[LogEntry]) -> str:
        """Format multiple entries as a complete table."""
        if not entries:
            return "No log entries to display."

        lines = [self.format_header()]
        for entry in entries:
            lines.append(self.format_row(entry))

        return "\n".join(lines)

    def _format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for table display."""
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%H:%M:%S")
        except ValueError:
            return timestamp[:8] if timestamp else ""


class SummaryFormatter:
    """Creates summary reports from log entries."""

    def format_test_summary(self, entries: List[LogEntry]) -> str:
        """Create a test execution summary."""
        if not entries:
            return "No test data available."

        # Group by test status
        status_counts = {}
        total_duration = 0
        test_count = 0

        for entry in entries:
            if entry.test_status and entry.test_status != "started":
                status_counts[entry.test_status] = status_counts.get(entry.test_status, 0) + 1
                test_count += 1

                if entry.duration_ms:
                    total_duration += entry.duration_ms

        # Create summary
        lines = ["Test Execution Summary", "=" * 25]

        if test_count > 0:
            lines.append(f"Total Tests: {test_count}")
            lines.append(f"Total Duration: {total_duration:.1f}ms")
            lines.append("")

            for status, count in sorted(status_counts.items()):
                percentage = (count / test_count) * 100
                lines.append(f"{status.title()}: {count} ({percentage:.1f}%)")

            # Success rate
            passed = status_counts.get("passed", 0)
            if test_count > 0:
                success_rate = (passed / test_count) * 100
                lines.append(f"\nSuccess Rate: {success_rate:.1f}%")
        else:
            lines.append("No completed tests found.")

        return "\n".join(lines)
