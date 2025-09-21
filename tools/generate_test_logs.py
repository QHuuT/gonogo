#!/usr/bin/env python3
"""
Generate Sample Test Logs

Creates realistic test execution logs using the proper structured logging system
to demonstrate report generation capabilities.

Related to: DEF-00008 - Report generator missing test_status data
"""

import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.shared.logging import (
    EnvironmentMode,
    LoggingConfig,
    LogLevel,
    get_logger,
    setup_logging,
)


def generate_sample_test_logs():
    """Generate sample test execution logs with proper test lifecycle events."""

    # Setup logging to write to test execution log
    log_file = Path("quality/logs/test_execution.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Clear existing log
    if log_file.exists():
        log_file.unlink()

    # Setup structured logging with proper config
    config = LoggingConfig(
        environment=EnvironmentMode.TESTING,
        log_level=LogLevel.INFO,
        log_directory=log_file.parent,
        log_filename=log_file.name,
        max_file_size_mb=10,
        max_files=5,
        include_metadata=True,
        include_stack_traces=True,
        sanitize_personal_data=True,
        buffer_size=100,
        flush_interval_seconds=1.0,
        data_retention_days=30,
        anonymize_ips=True,
        exclude_user_data=True,
    )

    logger = setup_logging(config)

    print(f"Generating sample test logs to {log_file}")

    # Sample test scenarios
    test_scenarios = [
        # Unit tests
        ("tests/unit/test_auth.py::TestAuth::test_valid_login", "unit", True, 45.2),
        (
            "tests/unit/test_auth.py::TestAuth::test_invalid_password",
            "unit",
            True,
            23.8,
        ),
        (
            "tests/unit/test_auth.py::TestAuth::test_missing_username",
            "unit",
            True,
            18.5,
        ),
        ("tests/unit/test_blog.py::TestBlog::test_create_post", "unit", True, 67.3),
        (
            "tests/unit/test_blog.py::TestBlog::test_edit_post",
            "unit",
            False,
            89.1,
        ),  # Failure
        (
            "tests/unit/test_comments.py::TestComments::test_add_comment",
            "unit",
            True,
            34.7,
        ),
        (
            "tests/unit/test_comments.py::TestComments::test_moderate_comment",
            "unit",
            True,
            28.9,
        ),
        # Integration tests
        (
            "tests/integration/test_database.py::TestDB::test_connection",
            "integration",
            True,
            156.4,
        ),
        (
            "tests/integration/test_api.py::TestAPI::test_create_user",
            "integration",
            True,
            234.1,
        ),
        (
            "tests/integration/test_api.py::TestAPI::test_user_flow",
            "integration",
            False,
            445.7,
        ),  # Failure
        # Security tests
        (
            "tests/security/test_gdpr.py::TestGDPR::test_consent_banner",
            "security",
            True,
            78.3,
        ),
        (
            "tests/security/test_gdpr.py::TestGDPR::test_data_retention",
            "security",
            True,
            92.6,
        ),
        (
            "tests/security/test_injection.py::TestSecurity::test_sql_injection",
            "security",
            True,
            145.8,
        ),
        # E2E tests
        (
            "tests/e2e/test_user_journey.py::TestE2E::test_comment_workflow",
            "e2e",
            True,
            2456.3,
        ),
        (
            "tests/e2e/test_user_journey.py::TestE2E::test_admin_workflow",
            "e2e",
            None,
            0,
        ),  # Skipped
    ]

    base_time = datetime.now()

    for i, (test_id, test_type, success, duration_ms) in enumerate(test_scenarios):
        # Extract test name from test_id
        test_name = test_id.split("::")[-1]

        # Calculate timestamp with small delays
        timestamp_offset = timedelta(seconds=i * 2.5)
        current_time = base_time + timestamp_offset

        print(f"  Logging: {test_name}")

        # Log test start
        logger.test_started(
            test_id=test_id,
            test_name=test_name,
            metadata={
                "test_file": test_id.split("::")[0],
                "test_class": test_id.split("::")[1] if "::" in test_id else None,
                "runner": "pytest",
                "session_id": f"test_session_{random.randint(1000, 9999)}",
                "test_type": test_type,
            },
        )

        # Simulate test execution time
        time.sleep(0.1)

        # Log test completion
        if success is True:
            logger.test_passed(
                test_id=test_id,
                test_name=test_name,
                duration_ms=duration_ms,
                metadata={
                    "assertions": random.randint(1, 8),
                    "coverage_lines": random.randint(10, 150),
                    "test_type": test_type,
                },
            )
        elif success is False:
            error_messages = [
                "AssertionError: Expected 200, got 404",
                "ConnectionError: Database connection failed",
                "ValidationError: Invalid email format",
                "TimeoutError: Request timed out after 30s",
                "PermissionError: Access denied to resource",
            ]
            error_msg = random.choice(error_messages)

            logger.test_failed(
                test_id=test_id,
                test_name=test_name,
                duration_ms=duration_ms,
                error_message=error_msg,
                stack_trace=f"Traceback (most recent call last):\n  File \"{test_id.split('::')[0]}\", line {random.randint(20, 100)}, in {test_name}\n    assert response.status_code == 200\n{error_msg}",
                metadata={"test_type": test_type},
            )
        else:  # Skipped
            skip_reasons = [
                "Test requires external service",
                "Feature not implemented yet",
                "Conditional skip - environment not ready",
                "Database migration in progress",
            ]
            skip_reason = random.choice(skip_reasons)

            logger.test_skipped(
                test_id=test_id,
                test_name=test_name,
                reason=skip_reason,
                metadata={"test_type": test_type},
            )

    print(f"\nGenerated {len(test_scenarios)} test log entries")
    print(
        f"Test results: {sum(1 for _, _, success, _ in test_scenarios if success is True)} passed, "
        f"{sum(1 for _, _, success, _ in test_scenarios if success is False)} failed, "
        f"{sum(1 for _, _, success, _ in test_scenarios if success is None)} skipped"
    )
    print(f"Log file: {log_file}")


if __name__ == "__main__":
    generate_sample_test_logs()
