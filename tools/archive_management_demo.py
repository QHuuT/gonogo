#!/usr/bin/env python3
"""
Archive Management Demo

Demonstrates the test report and log archiving system including
retention policies, compression, search capabilities, and automation.

Related to: US-00028 Test report archiving and retention management

Usage:
    python tools/archive_management_demo.py
"""

import sys
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shared.testing.archive_manager import TestArchiveManager, RetentionPolicy


def create_sample_files(base_path: Path) -> dict:
    """Create sample files with different ages for demonstration."""
    print("Creating sample test reports and logs for archive demo...")

    # Create directory structure
    reports_dir = base_path / "reports"
    logs_dir = base_path / "logs"
    reports_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    files_created = {
        "recent": [],
        "medium_age": [],
        "old": [],
        "very_old": []
    }

    # Recent files (< 7 days)
    recent_files = [
        (reports_dir / "test_report_latest.html", "HTML Test Report - Latest Run", 0.5),
        (reports_dir / "coverage_report.json", '{"coverage": 85.2, "timestamp": "2025-09-20"}', 0.1),
        (logs_dir / "test_execution.log", "INFO: Test execution started\nDEBUG: Loading test cases\nINFO: All tests passed", 0.2),
        (reports_dir / "failure_summary.json", '{"failures": 0, "total_tests": 150}', 0.05)
    ]

    for file_path, content, age_days in recent_files:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Set file modification time
        age_seconds = age_days * 24 * 3600
        timestamp = datetime.now().timestamp() - age_seconds
        import os
        os.utime(file_path, (timestamp, timestamp))

        files_created["recent"].append(str(file_path))

    # Medium age files (7-30 days) - should be compressed
    medium_files = [
        (reports_dir / "weekly_test_report.html", "<html><body>Weekly Test Summary - 2 weeks ago</body></html>" * 100, 14),
        (logs_dir / "integration_tests.log", "Integration test logs from 2 weeks ago\n" * 500, 15),
        (reports_dir / "performance_analysis.json", '{"performance_data": "large_dataset"}' * 50, 20),
        (logs_dir / "security_scan.log", "Security scan results - 3 weeks old\n" * 200, 21)
    ]

    for file_path, content, age_days in medium_files:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        age_seconds = age_days * 24 * 3600
        timestamp = datetime.now().timestamp() - age_seconds
        import os
        os.utime(file_path, (timestamp, timestamp))

        files_created["medium_age"].append(str(file_path))

    # Old files (30-90 days) - should be archived
    old_files = [
        (reports_dir / "monthly_report_july.html", "<html><body>July Monthly Report</body></html>" * 200, 45),
        (logs_dir / "debug_session.log", "Debug session from 2 months ago\n" * 1000, 60),
        (reports_dir / "compliance_check.json", '{"gdpr_compliant": true, "date": "2025-07-01"}', 75),
        (logs_dir / "performance_benchmark.log", "Performance benchmark - 2.5 months old\n" * 800, 80)
    ]

    for file_path, content, age_days in old_files:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        age_seconds = age_days * 24 * 3600
        timestamp = datetime.now().timestamp() - age_seconds
        import os
        os.utime(file_path, (timestamp, timestamp))

        files_created["old"].append(str(file_path))

    # Very old files (> 90 days) - should be deleted
    very_old_files = [
        (reports_dir / "legacy_report.html", "<html><body>Very old legacy report</body></html>", 120),
        (logs_dir / "ancient_debug.log", "Ancient debug logs from 4 months ago\n" * 100, 130),
        (reports_dir / "outdated_metrics.json", '{"old_data": true}', 150)
    ]

    for file_path, content, age_days in very_old_files:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        age_seconds = age_days * 24 * 3600
        timestamp = datetime.now().timestamp() - age_seconds
        import os
        os.utime(file_path, (timestamp, timestamp))

        files_created["very_old"].append(str(file_path))

    print(f"Created sample files:")
    print(f"  Recent files: {len(files_created['recent'])}")
    print(f"  Medium age files: {len(files_created['medium_age'])}")
    print(f"  Old files: {len(files_created['old'])}")
    print(f"  Very old files: {len(files_created['very_old'])}")

    return files_created


def demonstrate_retention_policies(manager: TestArchiveManager):
    """Demonstrate retention policy application."""
    print("\n*** Demonstrating Retention Policies...")
    print("Current policies:")

    for i, policy in enumerate(manager.policies, 1):
        print(f"  {i}. {policy.file_pattern}: keep {policy.retention_days} days, compress after {policy.compress_after_days} days")

    # Show dry run first
    print(f"\n*** DRY RUN - What would happen:")
    dry_results = manager.apply_retention_policies(dry_run=True)

    print(f"  Actions planned: {len(dry_results['actions'])}")
    print(f"  Files to compress: {dry_results['compressed_files']}")
    print(f"  Files to archive: {dry_results['archived_files']}")
    print(f"  Files to delete: {dry_results['deleted_files']}")
    print(f"  Estimated space savings: {dry_results['space_saved_mb']:.1f} MB")

    if dry_results['actions']:
        print(f"\n  Sample actions:")
        for action in dry_results['actions'][:5]:  # Show first 5
            print(f"    [{action['type'].upper()}] {Path(action['file']).name} - {action['reason']}")

    return dry_results


def demonstrate_storage_metrics(manager: TestArchiveManager):
    """Demonstrate storage metrics analysis."""
    print("\n*** Storage Metrics Analysis...")

    metrics = manager.generate_storage_metrics()

    print(f"Current storage usage:")
    print(f"  Total files: {metrics.total_files}")
    print(f"  Total size: {metrics.total_size_mb:.1f} MB")
    print(f"  Compressed files: {metrics.compressed_files}")
    print(f"  Compression savings: {metrics.compression_savings_mb:.1f} MB")
    print(f"  Old files (>30 days): {metrics.old_files_count} ({metrics.old_files_size_mb:.1f} MB)")

    if metrics.recommendations:
        print(f"\n  Optimization recommendations:")
        for rec in metrics.recommendations:
            print(f"    - {rec}")
    else:
        print(f"\n  No optimization recommendations at this time.")

    return metrics


def demonstrate_compression_and_archiving(manager: TestArchiveManager):
    """Demonstrate actual compression and archiving."""
    print("\n*** Applying Retention Policies (LIVE)...")

    # Apply policies for real
    live_results = manager.apply_retention_policies(dry_run=False)

    print(f"Actions completed:")
    print(f"  Files processed: {live_results['processed_files']}")
    print(f"  Files compressed: {live_results['compressed_files']}")
    print(f"  Files archived: {live_results['archived_files']}")
    print(f"  Files deleted: {live_results['deleted_files']}")
    print(f"  Space saved: {live_results['space_saved_mb']:.1f} MB")

    if live_results['errors']:
        print(f"\n  Errors encountered:")
        for error in live_results['errors']:
            print(f"    - {error}")

    return live_results


def demonstrate_search_capabilities(manager: TestArchiveManager):
    """Demonstrate archive search functionality."""
    print("\n*** Archive Search Capabilities...")

    # Search for HTML reports
    print(f"\nSearching for HTML reports...")
    html_results = manager.search_archives(query="html", limit=10)

    if html_results:
        print(f"  Found {len(html_results)} HTML reports in archive:")
        for result in html_results[:3]:  # Show first 3
            print(f"    - {Path(result.original_path).name}")
            print(f"      Archived: {result.archived_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"      Compression: {(1-result.compression_ratio)*100:.1f}%")
    else:
        print(f"  No HTML reports found in archive yet.")

    # Search for log files
    print(f"\nSearching for log files...")
    log_results = manager.search_archives(file_type=".log", limit=10)

    if log_results:
        print(f"  Found {len(log_results)} log files in archive:")
        for result in log_results[:3]:  # Show first 3
            print(f"    - {Path(result.original_path).name}")
            print(f"      Original size: {result.original_size/1024:.1f} KB")
            print(f"      Compressed size: {result.compressed_size/1024:.1f} KB")
    else:
        print(f"  No log files found in archive yet.")

    return html_results, log_results


def demonstrate_bundle_creation(manager: TestArchiveManager):
    """Demonstrate archive bundle creation."""
    print("\n*** Archive Bundle Creation...")

    try:
        # Create a bundle of all JSON reports
        bundle_path = manager.create_archive_bundle(
            file_patterns=["reports/*.json"],
            bundle_name="json_reports_backup"
        )

        bundle_size = bundle_path.stat().st_size / 1024

        print(f"  Bundle created successfully:")
        print(f"    Path: {bundle_path}")
        print(f"    Size: {bundle_size:.1f} KB")

        return bundle_path

    except ValueError as e:
        print(f"  Bundle creation failed: {e}")
        return None


def demonstrate_file_restoration(manager: TestArchiveManager):
    """Demonstrate file restoration from archive."""
    print("\n*** File Restoration...")

    # Search for archived files
    archived_files = manager.search_archives(limit=5)

    if archived_files:
        # Try to restore the first archived file
        first_file = archived_files[0]
        print(f"  Attempting to restore: {Path(first_file.original_path).name}")

        try:
            restored_path = manager.retrieve_from_archive(first_file.archive_path)
            restored_size = restored_path.stat().st_size / 1024

            print(f"  File restored successfully:")
            print(f"    Restored to: {restored_path}")
            print(f"    Size: {restored_size:.1f} KB")

            return restored_path

        except Exception as e:
            print(f"  Restoration failed: {e}")
            return None
    else:
        print(f"  No archived files available for restoration demo.")
        return None


def demonstrate_automation_config(manager: TestArchiveManager):
    """Demonstrate automation configuration."""
    print("\n*** Automation Configuration...")

    # Export current configuration
    config_path = manager.export_configuration()
    print(f"  Configuration exported to: {config_path}")

    # Generate cron job configuration
    cron_job = manager.schedule_cleanup("0 3 * * *")  # Daily at 3 AM
    print(f"  Suggested cron job: {cron_job}")

    print(f"  To enable automated cleanup:")
    print(f"    1. Add to crontab: crontab -e")
    print(f"    2. Add line: {cron_job}")
    print(f"    3. Save and exit")

    return config_path


def main():
    """Main demo function."""
    print("Test Archive Management Demo")
    print("=" * 50)

    # Create temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        demo_path = Path(temp_dir) / "quality"
        demo_path.mkdir(parents=True, exist_ok=True)

        print(f"Demo running in temporary directory: {demo_path}")

        # Initialize archive manager
        manager = TestArchiveManager(base_path=demo_path)

        try:
            # Create sample files
            sample_files = create_sample_files(demo_path)

            # Demonstrate features
            demonstrate_storage_metrics(manager)
            demonstrate_retention_policies(manager)
            demonstrate_compression_and_archiving(manager)
            demonstrate_search_capabilities(manager)
            demonstrate_bundle_creation(manager)
            demonstrate_file_restoration(manager)
            demonstrate_automation_config(manager)

            # Final metrics
            print("\n*** Final Storage Analysis...")
            final_metrics = manager.generate_storage_metrics()
            print(f"  Final total size: {final_metrics.total_size_mb:.1f} MB")
            print(f"  Compressed files: {final_metrics.compressed_files}")
            print(f"  Space saved through compression: {final_metrics.compression_savings_mb:.1f} MB")

            print(f"\nDemo completed successfully!")
            print(f"Archive location: {manager.archive_base}")

            # Display key achievements
            print(f"\n*** Key Achievements:")
            print(f"[DONE] Configurable retention policies with automatic application")
            print(f"[DONE] File compression with space optimization")
            print(f"[DONE] Archive search and retrieval capabilities")
            print(f"[DONE] Automated cleanup with scheduling support")
            print(f"[DONE] Storage metrics and optimization recommendations")
            print(f"[DONE] Bundle creation for batch archiving")

        except Exception as e:
            print(f"Demo failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())