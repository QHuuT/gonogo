#!/usr/bin/env python3
"""
Archive Cleanup Tool

Command-line interface for test report and log archive management
with configurable retention policies and automation capabilities.

Related to: US-00028 Test report archiving and retention management

Usage:
    python tools/archive_cleanup.py --dry-run
    python tools/archive_cleanup.py --apply
    python tools/archive_cleanup.py --metrics
    python tools/archive_cleanup.py --search "test_report"
"""

import sys
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shared.testing.archive_manager import TestArchiveManager, StorageMetrics


def apply_retention_policies(manager: TestArchiveManager, dry_run: bool = True):
    """Apply retention policies with detailed reporting."""
    print(f"{'DRY RUN: ' if dry_run else ''}Applying retention policies...")
    print("=" * 60)

    results = manager.apply_retention_policies(dry_run=dry_run)

    print(f"Summary:")
    print(f"  Files processed: {results['processed_files']}")
    print(f"  Files compressed: {results['compressed_files']}")
    print(f"  Files archived: {results['archived_files']}")
    print(f"  Files deleted: {results['deleted_files']}")
    print(f"  Space saved: {results['space_saved_mb']:.1f} MB")

    if results['errors']:
        print(f"\nErrors encountered:")
        for error in results['errors']:
            print(f"  - {error}")

    if results['actions']:
        print(f"\nActions {'that would be ' if dry_run else ''}taken:")
        for action in results['actions'][:20]:  # Show first 20 actions
            print(f"  [{action['type'].upper()}] {action['file']}")
            print(f"    Reason: {action['reason']}")
            if 'space_saved_mb' in action:
                print(f"    Space saved: {action['space_saved_mb']:.1f} MB")
            if 'archive_path' in action:
                print(f"    Archived to: {action['archive_path']}")

        if len(results['actions']) > 20:
            print(f"  ... and {len(results['actions']) - 20} more actions")

    return results


def show_storage_metrics(manager: TestArchiveManager):
    """Display comprehensive storage metrics."""
    print("Storage Metrics Analysis")
    print("=" * 60)

    metrics = manager.generate_storage_metrics()

    print(f"Current Storage:")
    print(f"  Total files: {metrics.total_files}")
    print(f"  Total size: {metrics.total_size_mb:.1f} MB")
    print(f"  Compressed files: {metrics.compressed_files}")
    print(f"  Compression savings: {metrics.compression_savings_mb:.1f} MB")

    print(f"\nFiles Older Than 30 Days:")
    print(f"  Count: {metrics.old_files_count}")
    print(f"  Size: {metrics.old_files_size_mb:.1f} MB")

    if metrics.recommendations:
        print(f"\nRecommendations:")
        for rec in metrics.recommendations:
            print(f"  - {rec}")
    else:
        print(f"\nNo optimization recommendations at this time.")

    return metrics


def search_archives(manager: TestArchiveManager, query: str, file_type: str = None):
    """Search archived items."""
    print(f"Searching archives for: {query}")
    if file_type:
        print(f"File type filter: {file_type}")
    print("=" * 60)

    results = manager.search_archives(
        query=query,
        file_type=file_type,
        limit=50
    )

    if not results:
        print("No archived items found matching the criteria.")
        return

    print(f"Found {len(results)} archived items:")
    for i, item in enumerate(results, 1):
        print(f"\n{i}. {Path(item.original_path).name}")
        print(f"   Original: {item.original_path}")
        print(f"   Archive: {item.archive_path}")
        print(f"   Type: {item.file_type}")
        print(f"   Size: {item.original_size / 1024:.1f} KB -> {item.compressed_size / 1024:.1f} KB")
        print(f"   Compression: {(1 - item.compression_ratio) * 100:.1f}%")
        print(f"   Created: {item.created_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Archived: {item.archived_date.strftime('%Y-%m-%d %H:%M')}")

    return results


def create_bundle(manager: TestArchiveManager, patterns: list, bundle_name: str):
    """Create an archive bundle."""
    print(f"Creating archive bundle: {bundle_name}")
    print(f"Patterns: {', '.join(patterns)}")
    print("=" * 60)

    try:
        bundle_path = manager.create_archive_bundle(patterns, bundle_name)
        bundle_size = bundle_path.stat().st_size / (1024 * 1024)

        print(f"Bundle created successfully:")
        print(f"  Path: {bundle_path}")
        print(f"  Size: {bundle_size:.1f} MB")

        return bundle_path

    except ValueError as e:
        print(f"Error creating bundle: {e}")
        return None


def configure_policies(manager: TestArchiveManager, config_file: str = None):
    """Configure retention policies."""
    if config_file:
        config_path = Path(config_file)
        if config_path.exists():
            manager.import_configuration(config_path)
            print(f"Configuration imported from: {config_path}")
        else:
            print(f"Configuration file not found: {config_path}")
            return

    print("Current Retention Policies:")
    print("=" * 60)

    for i, policy in enumerate(manager.policies, 1):
        print(f"{i}. Pattern: {policy.file_pattern}")
        print(f"   Retention: {policy.retention_days} days")
        print(f"   Compress after: {policy.compress_after_days} days")
        print(f"   Archive location: {policy.archive_location}")
        print(f"   Max size: {policy.max_size_mb} MB" if policy.max_size_mb else "   Max size: unlimited")
        print(f"   Enabled: {policy.enabled}")
        print()

    # Export current configuration
    export_path = manager.export_configuration()
    print(f"Current configuration exported to: {export_path}")


def generate_cleanup_script(manager: TestArchiveManager, schedule: str = "0 2 * * *"):
    """Generate automated cleanup script configuration."""
    print("Automated Cleanup Configuration")
    print("=" * 60)

    cron_job = manager.schedule_cleanup(schedule)
    script_content = f"""#!/bin/bash
# Automated archive cleanup script
# Generated: {datetime.now().isoformat()}

# Add this line to your crontab (crontab -e):
# {cron_job}

# Or run manually:
cd {manager.base_path.parent}
python tools/archive_cleanup.py --apply --quiet

# For metrics only:
# python tools/archive_cleanup.py --metrics --quiet
"""

    script_path = manager.base_path / "archive_cleanup.sh"
    with open(script_path, 'w') as f:
        f.write(script_content)

    print(f"Cleanup script generated: {script_path}")
    print(f"Cron job configuration: {cron_job}")
    print(f"\nTo enable automated cleanup:")
    print(f"1. Make script executable: chmod +x {script_path}")
    print(f"2. Add to crontab: crontab -e")
    print(f"3. Add line: {cron_job}")

    return script_path


def restore_file(manager: TestArchiveManager, archive_path: str, destination: str = None):
    """Restore a file from archive."""
    print(f"Restoring file from archive: {archive_path}")
    if destination:
        print(f"Destination: {destination}")
    print("=" * 60)

    try:
        dest_path = Path(destination) if destination else None
        restored_path = manager.retrieve_from_archive(archive_path, dest_path)

        restored_size = restored_path.stat().st_size / 1024

        print(f"File restored successfully:")
        print(f"  Restored to: {restored_path}")
        print(f"  Size: {restored_size:.1f} KB")

        return restored_path

    except Exception as e:
        print(f"Error restoring file: {e}")
        return None


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Test Archive Management Tool")

    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--apply', action='store_true',
                       help='Apply retention policies and make actual changes')
    parser.add_argument('--metrics', action='store_true',
                       help='Show storage metrics and recommendations')
    parser.add_argument('--search', type=str,
                       help='Search archived items')
    parser.add_argument('--file-type', type=str,
                       help='Filter search by file type (e.g., .html, .log)')
    parser.add_argument('--bundle', type=str,
                       help='Create archive bundle with given name')
    parser.add_argument('--patterns', nargs='+',
                       help='File patterns for bundle creation')
    parser.add_argument('--configure', action='store_true',
                       help='Show and configure retention policies')
    parser.add_argument('--config-file', type=str,
                       help='Import configuration from JSON file')
    parser.add_argument('--schedule', type=str, default="0 2 * * *",
                       help='Generate cleanup script with cron schedule')
    parser.add_argument('--restore', type=str,
                       help='Restore file from archive path')
    parser.add_argument('--destination', type=str,
                       help='Destination for restored file')
    parser.add_argument('--base-path', type=str,
                       help='Base path for archive operations')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce output verbosity')

    args = parser.parse_args()

    if not any([args.dry_run, args.apply, args.metrics, args.search, args.bundle,
               args.configure, args.restore]):
        parser.print_help()
        return 1

    # Initialize archive manager
    base_path = Path(args.base_path) if args.base_path else None
    manager = TestArchiveManager(base_path=base_path)

    if not args.quiet:
        print("Test Archive Management Tool")
        print(f"Base path: {manager.base_path}")
        print(f"Archive path: {manager.archive_base}")
        print()

    try:
        # Execute requested operations
        if args.configure:
            configure_policies(manager, args.config_file)

        if args.metrics:
            metrics = show_storage_metrics(manager)

        if args.search:
            results = search_archives(manager, args.search, args.file_type)

        if args.bundle and args.patterns:
            bundle_path = create_bundle(manager, args.patterns, args.bundle)

        if args.restore:
            restored_path = restore_file(manager, args.restore, args.destination)

        if args.dry_run or args.apply:
            results = apply_retention_policies(manager, dry_run=args.dry_run)

            if args.apply and not args.quiet:
                print(f"\nGenerated automated cleanup script...")
                script_path = generate_cleanup_script(manager, args.schedule)

        if not args.quiet:
            print(f"\nArchive management completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())