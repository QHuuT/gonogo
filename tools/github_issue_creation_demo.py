#!/usr/bin/env python3
"""
GitHub Issue Creation Demo

Demonstrates automated GitHub issue creation from test failures
with pre-filled context, logs, and reproduction guides.

Related to: US-00027 GitHub issue creation integration for test failures

Usage:
    python tools/github_issue_creation_demo.py --dry-run
    python tools/github_issue_creation_demo.py --create-issues
"""

import sys
import argparse
import tempfile
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shared.testing.failure_tracker import FailureTracker, TestFailure, FailureCategory
from shared.testing.log_failure_correlator import LogFailureCorrelator
from shared.testing.github_issue_creator import TestFailureIssueCreator


def create_sample_failures_for_demo(failure_tracker: FailureTracker) -> list[int]:
    """Create realistic sample failures for issue creation demo."""
    print("Creating sample failures for GitHub issue creation demo...")

    failure_ids = []

    # Failure 1: Critical authentication bug (high priority)
    failure_1 = TestFailure(
        test_id="auth-critical-001",
        test_name="test_user_login_security",
        test_file="tests/security/test_authentication.py",
        failure_message="AssertionError: Authentication bypass detected - critical security vulnerability",
        stack_trace="""tests/security/test_authentication.py:67 in test_user_login_security
    assert user.is_authenticated == True
AssertionError: Authentication bypass detected - critical security vulnerability
  Expected: True
  Actual: False
  Context: User with invalid credentials gained access""",
        category=FailureCategory.ASSERTION_ERROR,
        metadata={"severity_level": "critical", "security_impact": "high"}
    )
    failure_1.occurrence_count = 3  # Multiple failures
    failure_id_1 = failure_tracker.record_failure(failure_1)
    failure_ids.append(failure_id_1)

    # Failure 2: Flaky integration test (medium priority)
    failure_2 = TestFailure(
        test_id="integration-flaky-001",
        test_name="test_database_connection_pool",
        test_file="tests/integration/test_database.py",
        failure_message="TimeoutError: Connection pool exhausted after 30 seconds",
        stack_trace="""tests/integration/test_database.py:145 in test_database_connection_pool
    connection = pool.get_connection(timeout=30)
TimeoutError: Connection pool exhausted after 30 seconds
  Active connections: 10/10
  Waiting requests: 5""",
        category=FailureCategory.TIMEOUT_ERROR,
        metadata={"retry_count": 2, "infrastructure_related": True}
    )
    failure_2.occurrence_count = 7  # Very flaky
    failure_id_2 = failure_tracker.record_failure(failure_2)
    failure_ids.append(failure_id_2)

    # Failure 3: GDPR compliance issue (high priority)
    failure_3 = TestFailure(
        test_id="gdpr-compliance-001",
        test_name="test_data_retention_policy",
        test_file="tests/security/test_gdpr_compliance.py",
        failure_message="AssertionError: Personal data not deleted after retention period",
        stack_trace="""tests/security/test_gdpr_compliance.py:89 in test_data_retention_policy
    assert personal_data_count == 0
AssertionError: Personal data not deleted after retention period
  Expected: 0 records
  Actual: 156 records
  Context: Data older than 365 days still present in database""",
        category=FailureCategory.ASSERTION_ERROR,
        metadata={"compliance_impact": "high", "gdpr_violation": True}
    )
    failure_3.occurrence_count = 2
    failure_id_3 = failure_tracker.record_failure(failure_3)
    failure_ids.append(failure_id_3)

    # Failure 4: Import/dependency issue (low priority)
    failure_4 = TestFailure(
        test_id="dependency-missing-001",
        test_name="test_optional_feature_integration",
        test_file="tests/unit/test_optional_features.py",
        failure_message="ModuleNotFoundError: No module named 'optional_crypto_lib'",
        stack_trace="""tests/unit/test_optional_features.py:23 in test_optional_feature_integration
    from optional_crypto_lib import encrypt_data
ModuleNotFoundError: No module named 'optional_crypto_lib'
  Note: This is an optional dependency for enhanced encryption features""",
        category=FailureCategory.IMPORT_ERROR,
        metadata={"optional_dependency": True, "feature_impact": "low"}
    )
    failure_4.occurrence_count = 1
    failure_id_4 = failure_tracker.record_failure(failure_4)
    failure_ids.append(failure_id_4)

    print(f"Created {len(failure_ids)} sample failures for issue creation demo")
    return failure_ids


def demonstrate_issue_template_generation(creator: TestFailureIssueCreator, failure_ids: list[int]):
    """Demonstrate issue template generation."""
    print("\n*** Demonstrating Issue Template Generation...")

    for i, failure_id in enumerate(failure_ids, 1):
        print(f"\n*** Template {i} (Failure ID: {failure_id}):")

        # Generate template in dry-run mode
        result = creator.create_issue_from_failure(failure_id, dry_run=True)

        if result.success:
            print(f"   Template generated: {result.issue_url}")
            print(f"   Labels: {', '.join(result.labels_applied)}")

            # Show preview of template
            try:
                with open(result.issue_url, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                print(f"   Preview (first 15 lines):")
                for line in lines[:15]:
                    print(f"     {line}")

                if len(lines) > 15:
                    print(f"     ... (+ {len(lines) - 15} more lines)")

            except Exception as e:
                print(f"   Error reading template: {e}")

        else:
            print(f"   Failed to generate template: {result.error_message}")


def demonstrate_candidate_identification(creator: TestFailureIssueCreator):
    """Demonstrate identification of failure candidates for issue creation."""
    print("\n*** Identifying Issue Creation Candidates...")

    candidates = creator.get_recent_failure_candidates(days=30, min_occurrences=1)

    print(f"   Found {len(candidates)} candidates for issue creation:")

    for i, candidate in enumerate(candidates, 1):
        print(f"\n   {i}. **{candidate['test_name']}**")
        print(f"      - Category: {candidate['category']}")
        print(f"      - Severity: {candidate['severity']}")
        print(f"      - Occurrences: {candidate['occurrence_count']}")
        print(f"      - Last seen: {candidate['last_seen']}")
        print(f"      - Recommended labels: {', '.join(candidate['recommended_labels'])}")

    return candidates


def demonstrate_batch_processing(creator: TestFailureIssueCreator, failure_ids: list[int], dry_run: bool = True):
    """Demonstrate batch issue creation."""
    print(f"\n*** Demonstrating Batch Issue Creation (dry_run={dry_run})...")

    # Process batch
    results = creator.create_batch_issues_from_failures(failure_ids, dry_run=dry_run)

    # Generate report
    report = creator.generate_batch_creation_report(results)

    # Save report
    output_dir = Path("quality/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / f"github_issue_creation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"   Batch processing completed")
    print(f"   Report generated: {report_path}")

    # Display summary
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    print(f"   Summary:")
    print(f"     - Total processed: {len(results)}")
    print(f"     - Successful: {len(successful)}")
    print(f"     - Failed: {len(failed)}")
    print(f"     - Success rate: {len(successful)/len(results)*100:.1f}%" if results else "0%")

    if failed:
        print(f"   Errors:")
        for result in failed:
            print(f"     - {result.error_message}")

    return results


def demonstrate_label_intelligence(creator: TestFailureIssueCreator, failure_ids: list[int]):
    """Demonstrate intelligent label assignment."""
    print("\n*** Demonstrating Intelligent Label Assignment...")

    for i, failure_id in enumerate(failure_ids, 1):
        print(f"\n   Failure {i} (ID: {failure_id}):")

        # Get failure context
        context = creator.correlator.correlate_failure_with_logs(failure_id)
        if context:
            print(f"     Test: {context.test_name}")
            print(f"     Error: {context.failure_message[:80]}...")

            # Generate template to see labels
            template = creator._generate_issue_template(context)
            print(f"     Auto-assigned labels: {', '.join(template.labels)}")
            print(f"     Template type: {template.template_type}")

            # Show label reasoning
            if 'priority/high' in template.labels:
                print(f"     [HIGH] High priority detected (critical/security issue)")
            elif 'flaky-test' in template.template_type:
                print(f"     [FLAKY] Flaky test detected (multiple occurrences)")
            elif 'infrastructure' in template.template_type:
                print(f"     [INFRA] Infrastructure issue detected")

        else:
            print(f"     No context available for failure {failure_id}")


def main():
    """Main demo function."""
    parser = argparse.ArgumentParser(description="GitHub Issue Creation Demo")
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Generate templates without creating actual issues (default)')
    parser.add_argument('--create-issues', action='store_true',
                       help='Actually create GitHub issues (requires GitHub CLI auth)')
    parser.add_argument('--skip-samples', action='store_true',
                       help='Skip creating sample failures (use existing)')

    args = parser.parse_args()

    # Determine mode
    dry_run = not args.create_issues
    if args.create_issues:
        print("⚠️  WARNING: This will create real GitHub issues!")
        confirm = input("Are you sure you want to proceed? (y/N): ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return 1

    print("GitHub Issue Creation Demo")
    print("=" * 50)
    print(f"Mode: {'DRY RUN (templates only)' if dry_run else 'LIVE (creating real issues)'}")
    print()

    # Initialize components with temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    try:
        failure_tracker = FailureTracker(db_path=db_path)
        correlator = LogFailureCorrelator(failure_tracker=failure_tracker)
        creator = TestFailureIssueCreator(correlator=correlator)

        print(f"Initialized GitHub issue creator with database: {db_path}")

        # Create sample failures (unless skipping)
        if not args.skip_samples:
            failure_ids = create_sample_failures_for_demo(failure_tracker)
        else:
            # Get existing failures
            recent_failures = failure_tracker._get_recent_failures(30)
            failure_ids = [f['id'] for f in recent_failures[:4]]  # Use first 4
            print(f"Using existing failures: {failure_ids}")

        if not failure_ids:
            print("No failures available for demo")
            return 1

        # Demonstrate features
        demonstrate_issue_template_generation(creator, failure_ids)
        demonstrate_candidate_identification(creator)
        demonstrate_label_intelligence(creator, failure_ids)
        demonstrate_batch_processing(creator, failure_ids, dry_run=dry_run)

        print(f"\nDemo completed successfully!")
        print(f"Database: {db_path}")
        print(f"Templates: quality/reports/issue_template_*.md")
        print(f"Report: quality/reports/github_issue_creation_report_*.md")

        # Display key achievements
        print(f"\n*** Key Achievements:")
        print(f"[DONE] Automated issue template generation with failure context")
        print(f"[DONE] Intelligent label assignment based on failure characteristics")
        print(f"[DONE] Pre-filled environment info and reproduction guides")
        print(f"[DONE] Batch processing for multiple failures")
        print(f"[DONE] Integration with failure correlation and log analysis")
        print(f"[DONE] Dry-run mode for safe template validation")

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