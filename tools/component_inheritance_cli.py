#!/usr/bin/env python3
"""
Component Inheritance CLI Tool

Command-line interface for managing component inheritance in the RTM system.
Supports inheritance, override, and validation operations.

Related Issue: US-00009 - Implement Component Inheritance System
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import sys
import logging

# Add src to path for imports
sys.path.append("src")

from be.services.component_inheritance_service import ComponentInheritanceService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def inherit_all_components(force: bool = False, dry_run: bool = True):
    """Process all component inheritance."""
    logger.info(
        f"Processing all component inheritance (force={force}, dry_run={dry_run})"
    )

    with ComponentInheritanceService() as service:
        results = service.process_full_inheritance_chain(dry_run=dry_run)

        print("\n=== Component Inheritance Results ===")
        print(f"Dry Run: {results['dry_run']}")
        print(f"Total Changes: {results['total_changes']}")

        print("\nDefect Statistics:")
        for key, value in results["defect_stats"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")

        print("\nTest Statistics:")
        for key, value in results["test_stats"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")

        print("\nEpic Statistics:")
        for key, value in results["epic_stats"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")

        return results


def validate_consistency():
    """Validate component consistency across relationships."""
    logger.info("Validating component consistency")

    with ComponentInheritanceService() as service:
        results = service.validate_component_consistency()

        print("\n=== Component Consistency Validation ===")
        print(f"Total Inconsistencies: {results['total_inconsistencies']}")

        if results["defect_inconsistencies"]:
            print(
                f"\nDefect Inconsistencies({len(results['defect_inconsistencies'])}):"
            )
            for inconsistency in results["defect_inconsistencies"]:
                print(
                    f"  {inconsistency['defect_id']}: {inconsistency['defect_component']} != {inconsistency['user_story_id']}: {inconsistency['user_story_component']}"
                )

        if results["test_inconsistencies"]:
            print(f"\nTest Inconsistencies({len(results['test_inconsistencies'])}):")
            for inconsistency in results["test_inconsistencies"]:
                print(
                    f"  Test {inconsistency['test_id']}: {inconsistency['test_component']} != {inconsistency['user_story_id']}: {inconsistency['user_story_component']}"
                )

        if results["total_inconsistencies"] == 0:
            print("\nAll components are consistent!")

        return results


def inherit_defects_only(force: bool = False, dry_run: bool = True):
    """Process defect component inheritance only."""
    logger.info(
        f"Processing defect component inheritance (force={force}, dry_run={dry_run})"
    )

    with ComponentInheritanceService() as service:
        stats = service.process_all_defect_inheritance(force=force)

        if not dry_run:
            service.session.commit()
            logger.info("Changes committed to database")

        print("\n=== Defect Component Inheritance Results ===")
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

        return stats


def inherit_tests_only(force: bool = False, dry_run: bool = True):
    """Process test component inheritance only."""
    logger.info(
        f"Processing test component inheritance (force={force}, dry_run={dry_run})"
    )

    with ComponentInheritanceService() as service:
        stats = service.process_all_test_inheritance(force=force)

        if not dry_run:
            service.session.commit()
            logger.info("Changes committed to database")

        print("\n=== Test Component Inheritance Results ===")
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

        return stats


def inherit_epics_only(dry_run: bool = True):
    """Process epic component inheritance only."""
    logger.info(f"Processing epic component inheritance (dry_run={dry_run})")

    with ComponentInheritanceService() as service:
        stats = service.process_all_epic_inheritance()

        if not dry_run:
            service.session.commit()
            logger.info("Changes committed to database")

        print("\n=== Epic Component Inheritance Results ===")
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

        return stats


def main():
    """Main entry point for the CLI tool."""
    import argparse

    parser = argparse.ArgumentParser(description="Component inheritance management CLI")

    # Common arguments
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Only analyze and log what would be changed (default: True)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually execute changes (overrides --dry-run)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Force override existing components",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # All inheritance
    subparsers.add_parser("inherit-all", help="Process all component inheritance")

    # Specific inheritance
    subparsers.add_parser(
        "inherit-defects", help="Process defect component inheritance only"
    )
    subparsers.add_parser(
        "inherit-tests", help="Process test component inheritance only"
    )
    subparsers.add_parser(
        "inherit-epics", help="Process epic component inheritance only"
    )

    # Validation
    subparsers.add_parser("validate", help="Validate component consistency")

    args = parser.parse_args()

    # If --execute is specified, turn off dry run
    dry_run = args.dry_run and not args.execute

    logger.info("=== Component Inheritance CLI ===")
    logger.info(f"Command: {args.command}")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")
    logger.info(f"Force: {args.force}")

    try:
        if args.command == "inherit-all":
            result = inherit_all_components(force=args.force, dry_run=dry_run)

        elif args.command == "inherit-defects":
            result = inherit_defects_only(force=args.force, dry_run=dry_run)

        elif args.command == "inherit-tests":
            result = inherit_tests_only(force=args.force, dry_run=dry_run)

        elif args.command == "inherit-epics":
            result = inherit_epics_only(dry_run=dry_run)

        elif args.command == "validate":
            result = validate_consistency()

        else:
            parser.print_help()
            sys.exit(1)

        if dry_run and args.command != "validate":
            print("\nThis was a DRY RUN. No changes were made.")
            print("Run with --execute to apply the changes.")
        elif args.command != "validate":
            print("\nChanges have been applied to the database.")

    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
