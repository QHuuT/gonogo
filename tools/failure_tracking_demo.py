#!/usr/bin/env python3
"""
Failure Tracking System Demo

Demonstrates the test failure tracking and analysis capabilities.
Creates sample failures and generates comprehensive reports.

Related to: US-00025 Test failure tracking and reporting

Usage:
    python tools/failure_tracking_demo.py
"""

import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shared.testing.failure_tracker import (
    FailureTracker, TestFailure, FailureCategory, FailureSeverity
)
from shared.testing.failure_reporter import FailureReporter


def create_sample_failures(tracker: FailureTracker, num_failures: int = 20):
    """Create sample test failures for demonstration."""
    print(f"Creating {num_failures} sample test failures...")

    # Sample test data
    test_files = [
        "tests/unit/test_authentication.py",
        "tests/unit/test_blog_posts.py",
        "tests/unit/test_comments.py",
        "tests/unit/test_gdpr_service.py",
        "tests/integration/test_api_endpoints.py",
        "tests/integration/test_database.py",
        "tests/security/test_input_validation.py",
        "tests/e2e/test_user_workflow.py"
    ]

    sample_errors = [
        ("AssertionError: expected 5 but got 3", "assert response.status_code == 200", FailureCategory.ASSERTION_ERROR),
        ("UnicodeEncodeError: 'charmap' codec can't encode character 'DONE:'", "tempfile writing", FailureCategory.UNICODE_ERROR),
        ("ModuleNotFoundError: No module named 'nonexistent_module'", "import statement", FailureCategory.IMPORT_ERROR),
        ("TimeoutError: operation timed out after 30 seconds", "database connection", FailureCategory.TIMEOUT_ERROR),
        ("ConnectionError: Failed to connect to database", "postgresql connection", FailureCategory.DATABASE_ERROR),
        ("PermissionError: Access denied to file", "file operations", FailureCategory.PERMISSION_ERROR),
        ("ValueError: invalid literal for int()", "data conversion", FailureCategory.UNKNOWN_ERROR),
    ]

    session_ids = [f"session_{i}" for i in range(1, 6)]
    execution_modes = ["standard", "verbose", "detailed", "silent"]

    failure_ids = []
    for i in range(num_failures):
        # Pick random test and error
        test_file = random.choice(test_files)
        test_name = f"test_{random.choice(['function', 'method', 'scenario'])}_{i % 10}"
        error_msg, stack_trace, category = random.choice(sample_errors)

        # Create some variation in timing
        base_time = datetime.utcnow()
        if i < 5:  # Recent failures
            failure_time = base_time - timedelta(hours=random.randint(1, 24))
        elif i < 15:  # This week
            failure_time = base_time - timedelta(days=random.randint(1, 7))
        else:  # Older failures
            failure_time = base_time - timedelta(days=random.randint(8, 30))

        failure = TestFailure(
            test_id=f"{test_file}::{test_name}",
            test_name=test_name,
            test_file=test_file,
            failure_message=f"{error_msg} (sample #{i})",
            stack_trace=f"Full stack trace for {stack_trace}\n  at line {random.randint(10, 100)}",
            category=category,
            session_id=random.choice(session_ids),
            execution_mode=random.choice(execution_modes),
            environment_info=f"Python 3.13, Windows, Session {random.choice(session_ids)}",
            metadata={
                "duration": random.uniform(0.1, 5.0),
                "retry_count": random.randint(0, 3),
                "test_type": random.choice(["unit", "integration", "security", "e2e"])
            }
        )

        # Set custom timing
        failure.first_seen = failure_time
        failure.last_seen = failure_time

        # Determine severity
        failure.severity = tracker.determine_severity(failure)

        # Record the failure
        failure_id = tracker.record_failure(failure)
        failure_ids.append(failure_id)

        # Create some duplicate failures (flaky tests)
        if i % 7 == 0:  # Every 7th test becomes flaky
            for _ in range(random.randint(2, 5)):
                duplicate_time = failure_time + timedelta(hours=random.randint(1, 48))
                duplicate_failure = TestFailure(
                    test_id=failure.test_id,
                    test_name=failure.test_name,
                    test_file=failure.test_file,
                    failure_message=failure.failure_message,
                    stack_trace=failure.stack_trace,
                    category=failure.category,
                    session_id=random.choice(session_ids),
                    execution_mode=random.choice(execution_modes)
                )
                duplicate_failure.first_seen = duplicate_time
                duplicate_failure.last_seen = duplicate_time
                tracker.record_failure(duplicate_failure)

    print(f"Created {len(failure_ids)} unique failures with additional duplicates")
    return failure_ids


def demonstrate_analysis(tracker: FailureTracker):
    """Demonstrate failure analysis capabilities."""
    print("\n*** Analyzing failure data...")

    # Get statistics
    stats = tracker.get_failure_statistics(days=30)
    print(f"\n*** Failure Statistics (Last 30 Days):")
    print(f"   Total failures: {stats.total_failures}")
    print(f"   Unique failures: {stats.unique_failures}")
    print(f"   Failure rate: {stats.failure_rate:.1f}%")
    print(f"   Most common category: {stats.most_common_category.value}")
    print(f"   Critical failures: {stats.critical_failure_count}")
    print(f"   Flaky tests: {stats.flaky_test_count}")

    # Get top failing tests
    print(f"\n*** Top Failing Tests:")
    top_failing = tracker.get_top_failing_tests(limit=5)
    for i, test in enumerate(top_failing, 1):
        print(f"   {i}. {test['test_name']} ({test['total_failures']} failures)")
        print(f"      File: {test['test_file']}")
        print(f"      Category: {test['category']} | Severity: {test['severity']}")

    # Detect patterns
    print(f"\n*** Detected Patterns:")
    patterns = tracker.detect_patterns()
    for pattern in patterns:
        print(f"   • {pattern.description}")
        print(f"     Occurrences: {pattern.occurrences} | Impact: {pattern.impact_score:.1f}")
        print(f"     Affected tests: {len(pattern.affected_tests)}")

    return stats, top_failing, patterns


def generate_reports(tracker: FailureTracker):
    """Generate failure analysis reports."""
    print("\n*** Generating failure reports...")

    reporter = FailureReporter(tracker)

    # Generate daily summary
    output_dir = Path("quality/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_report = reporter.generate_daily_summary()
    print(f"DONE: Daily summary report generated: quality/reports/failure_summary_daily.json")

    # Generate HTML report
    html_report_path = reporter.generate_html_failure_report()
    print(f"DONE: HTML failure analysis report generated: {html_report_path}")

    return summary_report, html_report_path


def main():
    """Main demo function."""
    print("Test Failure Tracking System Demo")
    print("=" * 50)

    # Initialize tracker
    db_path = Path("quality/logs/demo_test_failures.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Clean up existing demo database
    if db_path.exists():
        db_path.unlink()

    tracker = FailureTracker(db_path=db_path)
    print(f"Initialized failure tracker with database: {db_path}")

    try:
        # Create sample data
        failure_ids = create_sample_failures(tracker, num_failures=25)

        # Demonstrate analysis
        stats, top_failing, patterns = demonstrate_analysis(tracker)

        # Generate reports
        summary_report, html_report_path = generate_reports(tracker)

        # Display recommendations
        print(f"\nRecommendations:")
        for rec in summary_report.get("recommendations", []):
            print(f"   - {rec}")

        print(f"\nDemo completed successfully!")
        print(f"Database: {db_path}")
        print(f"HTML Report: {html_report_path}")
        print(f"JSON Summary: quality/reports/failure_summary_daily.json")

    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())