#!/usr/bin/env python3
"""
Log-Failure Correlation System Demo

Demonstrates the log-failure correlation capabilities including
context preservation, debugging assistance, and reproduction guides.

Related to: US-00026 Log-failure association and context preservation

Usage:
    python tools/log_correlation_demo.py
"""

import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shared.logging.logger import LogEntry
from shared.testing.failure_tracker import FailureCategory, FailureTracker, TestFailure
from shared.testing.log_failure_correlator import LogFailureCorrelator


class MockStructuredLogger:
    """Mock structured logger for demo purposes."""

    def __init__(self):
        self.logs = []

    def add_log(self, log_entry: LogEntry):
        """Add a log entry to the mock logger."""
        self.logs.append(log_entry)

    def get_recent_logs(self, limit: int = 1000) -> list[LogEntry]:
        """Get recent logs (mock implementation)."""
        return self.logs[-limit:] if self.logs else []

    def flush(self):
        """Flush logs (mock implementation)."""
        pass


def create_sample_logs_and_failures(correlator: LogFailureCorrelator) -> list[int]:
    """Create sample logs and failures with realistic correlation scenarios."""
    print("Creating sample logs and failures for correlation demo...")

    # Create mock logger
    mock_logger = MockStructuredLogger()
    correlator.logger = mock_logger

    failure_ids = []
    base_time = datetime.now()

    # Scenario 1: Assertion Error with detailed context
    print("  Scenario 1: Assertion error with test setup logs")
    test_id_1 = "test-scenario-1-uuid"

    # Setup phase logs
    mock_logger.add_log(
        LogEntry(
            timestamp=(base_time - timedelta(minutes=5)).isoformat(),
            level="INFO",
            message="Test session started",
            tags=["session_lifecycle", "start"],
            metadata={"pytest_version": "7.4.0", "session_id": "session-123"},
        )
    )

    mock_logger.add_log(
        LogEntry(
            timestamp=(base_time - timedelta(minutes=3)).isoformat(),
            level="INFO",
            message="Test setup: initializing database fixtures",
            test_id=test_id_1,
            test_name="test_user_authentication",
            tags=["setup", "test_lifecycle"],
            metadata={
                "environment": "test",
                "python_version": "3.13.0",
                "platform": "Windows",
                "working_directory": "C:/repo/gonogo",
                "test_data": {"username": "testuser", "password": "secure123"},
            },
        )
    )

    # Execution phase logs
    mock_logger.add_log(
        LogEntry(
            timestamp=(base_time - timedelta(minutes=2)).isoformat(),
            level="INFO",
            message="Executing authentication test with test user",
            test_id=test_id_1,
            test_name="test_user_authentication",
            tags=["execution"],
            metadata={
                "test_input": {"username": "testuser", "expected_role": "user"},
                "database_state": "clean",
                "fixture_data": "loaded",
            },
        )
    )

    mock_logger.add_log(
        LogEntry(
            timestamp=(base_time - timedelta(minutes=1)).isoformat(),
            level="ERROR",
            message="Authentication test failed: role mismatch",
            test_id=test_id_1,
            test_name="test_user_authentication",
            test_status="failed",
            duration_ms=1250.75,
            tags=["failure", "assertion"],
            metadata={
                "actual_value": "admin",
                "expected_value": "user",
                "comparison_type": "role_comparison",
            },
        )
    )

    # Teardown phase logs
    mock_logger.add_log(
        LogEntry(
            timestamp=base_time.isoformat(),
            level="INFO",
            message="Test teardown: cleaning database fixtures",
            test_id=test_id_1,
            test_name="test_user_authentication",
            tags=["teardown", "test_lifecycle"],
            metadata={"cleanup_status": "completed", "fixtures_removed": True},
        )
    )

    # Create corresponding failure
    failure_1 = TestFailure(
        test_id=test_id_1,
        test_name="test_user_authentication",
        test_file="tests/unit/test_authentication.py",
        failure_message="AssertionError: expected role 'user' but got 'admin'",
        stack_trace="""tests/unit/test_authentication.py:45 in test_user_authentication
    assert user.role == 'user'
AssertionError: expected role 'user' but got 'admin'""",
        category=FailureCategory.ASSERTION_ERROR,
        metadata={"test_type": "unit", "duration": 1250.75, "retry_count": 0},
    )
    failure_1.last_seen = base_time

    failure_id_1 = correlator.failure_tracker.record_failure(failure_1)
    failure_ids.append(failure_id_1)

    # Scenario 2: Import Error with environment context
    print("  Scenario 2: Import error with environment debugging")
    test_id_2 = "test-scenario-2-uuid"

    mock_logger.add_log(
        LogEntry(
            timestamp=(base_time + timedelta(minutes=1)).isoformat(),
            level="INFO",
            message="Test setup: checking module imports",
            test_id=test_id_2,
            test_name="test_gdpr_service_initialization",
            tags=["setup", "imports"],
            metadata={
                "python_path": ["C:/repo/gonogo/src", "C:/repo/gonogo"],
                "virtual_env": "active",
                "installed_packages": ["fastapi", "sqlalchemy", "pytest"],
            },
        )
    )

    mock_logger.add_log(
        LogEntry(
            timestamp=(base_time + timedelta(minutes=2)).isoformat(),
            level="ERROR",
            message="Module import failed: gdpr_compliance module not found",
            test_id=test_id_2,
            test_name="test_gdpr_service_initialization",
            test_status="failed",
            duration_ms=50.0,
            tags=["failure", "import"],
            metadata={
                "missing_module": "gdpr_compliance",
                "import_path": "src.security.gdpr.gdpr_compliance",
                "sys_path": ["C:/repo/gonogo/src", "C:/repo/gonogo"],
            },
        )
    )

    failure_2 = TestFailure(
        test_id=test_id_2,
        test_name="test_gdpr_service_initialization",
        test_file="tests/unit/test_gdpr_service.py",
        failure_message="ModuleNotFoundError: No module named 'gdpr_compliance'",
        stack_trace="""tests/unit/test_gdpr_service.py:12 in <module>
    from src.security.gdpr.gdpr_compliance import GDPRService
ModuleNotFoundError: No module named 'gdpr_compliance'""",
        category=FailureCategory.IMPORT_ERROR,
    )
    failure_2.last_seen = base_time + timedelta(minutes=2)

    failure_id_2 = correlator.failure_tracker.record_failure(failure_2)
    failure_ids.append(failure_id_2)

    # Scenario 3: Timeout Error with performance context
    print("  Scenario 3: Timeout error with performance analysis")
    test_id_3 = "test-scenario-3-uuid"

    mock_logger.add_log(
        LogEntry(
            timestamp=(base_time + timedelta(minutes=5)).isoformat(),
            level="INFO",
            message="Database integration test started",
            test_id=test_id_3,
            test_name="test_database_heavy_query",
            tags=["integration", "database"],
            metadata={
                "database_url": "sqlite:///test.db",
                "connection_pool_size": 5,
                "timeout_setting": 30,
            },
        )
    )

    mock_logger.add_log(
        LogEntry(
            timestamp=(base_time + timedelta(minutes=6)).isoformat(),
            level="WARNING",
            message="Database query taking longer than expected",
            test_id=test_id_3,
            test_name="test_database_heavy_query",
            tags=["performance", "database"],
            metadata={
                "query_duration_ms": 25000,
                "expected_max_ms": 5000,
                "query_type": "complex_join",
            },
        )
    )

    mock_logger.add_log(
        LogEntry(
            timestamp=(base_time + timedelta(minutes=7)).isoformat(),
            level="ERROR",
            message="Database operation timed out after 30 seconds",
            test_id=test_id_3,
            test_name="test_database_heavy_query",
            test_status="failed",
            duration_ms=30000,
            tags=["failure", "timeout"],
            metadata={
                "timeout_limit_ms": 30000,
                "operation": "SELECT with complex JOIN",
                "rows_processed": 0,
            },
        )
    )

    failure_3 = TestFailure(
        test_id=test_id_3,
        test_name="test_database_heavy_query",
        test_file="tests/integration/test_database.py",
        failure_message="TimeoutError: Database operation timed out after 30 seconds",
        stack_trace="""tests/integration/test_database.py:78 in test_database_heavy_query
    result = db.execute(complex_query).fetchall()
TimeoutError: Database operation timed out after 30 seconds""",
        category=FailureCategory.TIMEOUT_ERROR,
    )
    failure_3.last_seen = base_time + timedelta(minutes=7)

    failure_id_3 = correlator.failure_tracker.record_failure(failure_3)
    failure_ids.append(failure_id_3)

    print(f"Created {len(failure_ids)} failures with correlated logs")
    return failure_ids


def demonstrate_correlation_analysis(
    correlator: LogFailureCorrelator, failure_ids: list[int]
):
    """Demonstrate correlation analysis capabilities."""
    print("\n*** Analyzing log-failure correlations...")

    for i, failure_id in enumerate(failure_ids, 1):
        print(f"\n*** Failure {i} Analysis:")

        # Get failure context
        context = correlator.correlate_failure_with_logs(
            failure_id, time_window_minutes=15
        )

        if context:
            print(f"   Test: {context.test_name}")
            print(f"   Error: {context.failure_message}")
            print(f"   Setup logs: {len(context.setup_logs)}")
            print(f"   Execution logs: {len(context.execution_logs)}")
            print(f"   Teardown logs: {len(context.teardown_logs)}")

            print("\n   Environment Context:")
            for key, value in context.environment_info.items():
                print(f"     {key}: {value}")

            print("\n   Debugging Hints:")
            for hint in context.debugging_hints[:3]:  # Show first 3 hints
                print(f"     - {hint}")

            print(f"\n   Related Failures: {len(context.related_failures)}")

        else:
            print(f"   No correlation found for failure {failure_id}")


def demonstrate_reproduction_guides(
    correlator: LogFailureCorrelator, failure_ids: list[int]
):
    """Demonstrate reproduction guide generation."""
    print("\n*** Generating failure reproduction guides...")

    output_dir = Path("quality/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, failure_id in enumerate(failure_ids, 1):
        print(f"\n*** Reproduction Guide {i}:")

        script = correlator.generate_failure_reproduction_script(failure_id)
        if script:
            script_path = output_dir / f"reproduction_script_{failure_id}.py"
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script)

            print(f"   Generated: {script_path}")

            # Show preview of script
            lines = script.split("\n")
            print("   Preview:")
            for line in lines[:10]:  # Show first 10 lines
                print(f"     {line}")
            if len(lines) > 10:
                print(f"     ... (+ {len(lines) - 10} more lines)")

        else:
            print(f"   Failed to generate script for failure {failure_id}")


def demonstrate_correlation_summary(correlator: LogFailureCorrelator):
    """Demonstrate overall correlation summary."""
    print("\n*** Overall Correlation Summary:")

    summary = correlator.correlate_all_recent_failures(days=1)

    print(f"   Total failures processed: {summary.total_failures_processed}")
    print(f"   Failures with correlated logs: {summary.failures_with_logs}")
    print(f"   Correlation success rate: {summary.correlation_success_rate:.1f}%")

    print("\n   Common Failure Patterns:")
    for pattern in summary.common_failure_patterns[:5]:  # Top 5 patterns
        print(f"     - {pattern['category']}: {pattern['count']} occurrences")

    print("\n   Key Debugging Insights:")
    for insight in summary.debugging_insights[:5]:  # Top 5 insights
        print(f"     - {insight}")


def generate_reports(correlator: LogFailureCorrelator):
    """Generate comprehensive correlation reports."""
    print("\n*** Generating correlation reports...")

    output_dir = Path("quality/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate JSON correlation report
    report_path = correlator.export_correlation_report()
    print(f"   JSON report generated: {report_path}")

    # Validate report content
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    print(
        f"   Report contains {len(report['failure_contexts'])} detailed failure contexts"
    )
    print(
        f"   Correlation metadata includes {len(report['correlation_metadata']['correlation_strategies'])} strategies"
    )

    return report_path


def main():
    """Main demo function."""
    print("Log-Failure Correlation System Demo")
    print("=" * 50)

    # Initialize correlator with temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        failure_tracker = FailureTracker(db_path=db_path)
        correlator = LogFailureCorrelator(failure_tracker=failure_tracker)

        print(f"Initialized log-failure correlator with database: {db_path}")

        # Create sample data
        failure_ids = create_sample_logs_and_failures(correlator)

        # Demonstrate analysis capabilities
        demonstrate_correlation_analysis(correlator, failure_ids)

        # Demonstrate reproduction guides
        demonstrate_reproduction_guides(correlator, failure_ids)

        # Demonstrate summary analysis
        demonstrate_correlation_summary(correlator)

        # Generate reports
        report_path = generate_reports(correlator)

        print("\nDemo completed successfully!")
        print(f"Database: {db_path}")
        print(f"Correlation Report: {report_path}")
        print("Reproduction Scripts: quality/reports/reproduction_script_*.py")

        # Display key achievements
        print("\n*** Key Achievements:")
        print(f"[DONE] Log-failure correlation with {len(failure_ids)} scenarios")
        print("[DONE] Contextpreservation (environment, test data, execution state)")
        print("[DONE] Debugging assistance with categorized hints")
        print("[DONE] Reproduction guide generation")
        print("[DONE] Pattern analysis and insights")
        print("[DONE] GDPR-compliant data handling")

    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        # Cleanup
        try:
            if db_path.exists():
                db_path.unlink()
        except PermissionError:
            print(f"Note: Database file {db_path} may remain (Windows file locking)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
