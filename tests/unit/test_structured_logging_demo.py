"""
Demonstration tests for the structured logging system.
Shows how the logging integrates with test execution.

Related to: US-00022 Structured logging system for test execution
"""

import time
import pytest
from pathlib import Path

# Import the structured logging system
from src.shared.logging import (
    StructuredLogger, LoggingConfig, EnvironmentMode, LogLevel,
    JSONFormatter, TestFormatter, SummaryFormatter
)


class TestStructuredLoggingDemo:
    """Demonstration of structured logging capabilities."""

    def setup_method(self):
        """Set up logging for each test."""
        # Create a test-specific logging configuration
        self.config = LoggingConfig(
            environment=EnvironmentMode.TESTING,
            log_level=LogLevel.DEBUG,
            log_directory=Path("quality/logs"),
            log_filename="test_demo.log",
            max_file_size_mb=5,
            max_files=3,
            include_metadata=True,
            include_stack_traces=True,
            sanitize_personal_data=True,
            buffer_size=100,
            flush_interval_seconds=1.0,
            data_retention_days=7,
            anonymize_ips=True,
            exclude_user_data=False
        )

        self.logger = StructuredLogger(self.config)

    def test_basic_logging_functionality(self):
        """Test basic logging operations."""
        # Test different log levels
        self.logger.debug("Debug message for development", metadata={"test_data": "debug_value"})
        self.logger.info("Information about test execution", tags=["demo", "info"])
        self.logger.warning("Warning about potential issue", metadata={"warning_code": "W001"})
        self.logger.error("Error occurred during test", metadata={"error_code": "E001"})

        # Verify logs were captured
        recent_logs = self.logger.get_recent_logs(10)
        assert len(recent_logs) >= 4

        # Check that different log levels were recorded
        log_levels = {log.level for log in recent_logs}
        assert "debug" in log_levels
        assert "info" in log_levels
        assert "warning" in log_levels
        assert "error" in log_levels

    def test_test_lifecycle_logging(self):
        """Test logging for test lifecycle events."""
        test_id = "test_123"
        test_name = "sample_test_case"

        # Simulate test lifecycle
        self.logger.test_started(test_id, test_name, metadata={"setup_time": 50})

        # Simulate some test work
        time.sleep(0.01)  # 10ms

        self.logger.test_passed(test_id, test_name, 10.5, metadata={"assertions": 5})

        # Verify test logs
        test_logs = self.logger.get_logs_for_test(test_id)
        assert len(test_logs) == 2
        assert test_logs[0].test_status == "started"
        assert test_logs[1].test_status == "passed"
        assert test_logs[1].duration_ms == 10.5

    def test_test_failure_logging(self):
        """Test logging for test failures."""
        test_id = "test_456"
        test_name = "failing_test_case"

        self.logger.test_started(test_id, test_name)

        # Simulate test failure
        error_msg = "Assertion failed: expected 5, got 3"
        stack_trace = "  File 'test.py', line 42, in test_function\n    assert result == 5\nAssertionError: expected 5, got 3"

        self.logger.test_failed(
            test_id, test_name, 25.3, error_msg,
            stack_trace=stack_trace,
            metadata={"assertion_type": "equality", "expected": 5, "actual": 3}
        )

        # Verify failure logs
        test_logs = self.logger.get_logs_for_test(test_id)
        failure_log = test_logs[-1]
        assert failure_log.test_status == "failed"
        assert "Assertion failed" in failure_log.message
        assert failure_log.stack_trace is not None

    def test_gdpr_sanitization(self):
        """Test GDPR-compliant data sanitization."""
        # Log some data that should be sanitized
        sensitive_data = {
            "user_email": "user@example.com",
            "ip_address": "192.168.1.100",
            "safe_data": "this should remain",
            "file_path": "/home/john/documents/test.txt"
        }

        self.logger.info(
            "Processing user data: user@example.com from IP 192.168.1.100",
            metadata=sensitive_data
        )

        # Get the log and verify sanitization
        recent_logs = self.logger.get_recent_logs(1)
        log_entry = recent_logs[0]

        # Check that sensitive data was sanitized in the message
        assert "[EMAIL_REDACTED]" in log_entry.message
        assert "[IP_REDACTED]" in log_entry.message
        assert "user@example.com" not in log_entry.message
        assert "192.168.1.100" not in log_entry.message

    def test_json_formatting(self):
        """Test JSON log formatting."""
        formatter = JSONFormatter(compact=True, include_metadata=True)

        # Create a sample log entry
        self.logger.info(
            "Test JSON formatting",
            test_id="json_test",
            test_name="test_json_format",
            metadata={"format": "json", "compact": True},
            tags=["formatting", "json"]
        )

        recent_logs = self.logger.get_recent_logs(1)
        json_output = formatter.format(recent_logs[0])

        # Verify it's valid JSON and contains expected fields
        import json
        parsed = json.loads(json_output)

        assert parsed["level"] == "info"
        assert parsed["message"] == "Test JSON formatting"
        assert parsed["test_id"] == "json_test"
        assert "metadata" in parsed
        assert "tags" in parsed

    def test_human_readable_formatting(self):
        """Test human-readable log formatting."""
        formatter = TestFormatter(show_timestamp=True, colorize=False)

        # Create test log entries
        self.logger.test_started("hr_test", "human_readable_test")
        self.logger.test_passed("hr_test", "human_readable_test", 15.7)

        test_logs = self.logger.get_logs_for_test("hr_test")

        for log in test_logs:
            formatted = formatter.format(log)
            assert "[INFO]" in formatted or "[DEBUG]" in formatted
            assert "human_readable_test" in formatted

    def test_summary_generation(self):
        """Test summary report generation."""
        # Create multiple test results
        tests = [
            ("test_1", "passed", 10.0),
            ("test_2", "passed", 15.0),
            ("test_3", "failed", 8.0),
            ("test_4", "skipped", None),
            ("test_5", "passed", 12.0)
        ]

        for test_id, status, duration in tests:
            self.logger.test_started(test_id, f"test_case_{test_id}")
            if status == "passed":
                self.logger.test_passed(test_id, f"test_case_{test_id}", duration)
            elif status == "failed":
                self.logger.test_failed(test_id, f"test_case_{test_id}", duration, "Test failed")
            elif status == "skipped":
                self.logger.test_skipped(test_id, f"test_case_{test_id}", "Test skipped")

        # Generate summary
        formatter = SummaryFormatter()
        all_logs = self.logger.get_recent_logs(100)
        summary = formatter.format_test_summary(all_logs)

        assert "Test Execution Summary" in summary
        assert "Total Tests:" in summary
        assert "Success Rate:" in summary

    def test_configuration_info(self):
        """Test that configuration information is accessible."""
        config_info = self.logger.get_config_info()

        assert "config" in config_info
        assert "sanitizer" in config_info
        assert "session_id" in config_info
        assert "log_file" in config_info

        # Verify config values
        config = config_info["config"]
        assert config["environment"] == "test"
        assert config["sanitize_personal_data"] is True

    def teardown_method(self):
        """Clean up after each test."""
        self.logger.close()