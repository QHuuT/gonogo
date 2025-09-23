#!/usr/bin/env python3
"""
Fix Missing Component Inheritance

Handles component inheritance for entities that are missing components:
1. Defects inherit from Epic (when no user story parent)
2. Tests inherit from Epic (direct epic relationship)

Note: User Stories need manual component assignment, they don't inherit from epics.
The inheritance flow is User Stories -> Epics (not the reverse).
"""

import sys
import logging
sys.path.append('src')

from be.database import SessionLocal
from be.models.traceability.epic import Epic
from be.models.traceability.user_story import UserStory
from be.models.traceability.defect import Defect
from be.models.traceability.test import Test

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def inherit_defect_components_from_epics(session, dry_run: bool = True) -> dict:
    """
    Inherit components for defects that are directly linked to epics.

    Args:
        session: Database session
        dry_run: If True, don't apply changes

    Returns:
        Dict with inheritance statistics
    """
    logger.info("Processing defect component inheritance from epics")

    stats = {
        'total_defects': 0,
        'defects_processed': 0,
        'defects_updated': 0,
        'errors': 0
    }

    # Get defects with no component but with epic
    defects_missing_components = session.query(Defect).filter(
        Defect.component.is_(None),
        Defect.epic_id.isnot(None)
    ).all()

    stats['total_defects'] = len(defects_missing_components)

    for defect in defects_missing_components:
        try:
            stats['defects_processed'] += 1

            # Get first component from epic's comma-separated components
            epic_components = [c.strip() for c in defect.epic.component.split(',') if c.strip()]
            if epic_components:
                component_to_inherit = epic_components[0]  # Take first component

                logger.info(f"DEF {defect.defect_id}: Inheriting component '{component_to_inherit}' from epic {defect.epic.epic_id}")

                if not dry_run:
                    defect.component = component_to_inherit
                    stats['defects_updated'] += 1

        except Exception as e:
            logger.error(f"Error processing defect {defect.defect_id}: {e}")
            stats['errors'] += 1

    return stats

def inherit_test_components_from_epics(session, dry_run: bool = True) -> dict:
    """
    Inherit components for tests that are directly linked to epics.

    Args:
        session: Database session
        dry_run: If True, don't apply changes

    Returns:
        Dict with inheritance statistics
    """
    logger.info("Processing test component inheritance from epics")

    stats = {
        'total_tests': 0,
        'tests_processed': 0,
        'tests_updated': 0,
        'errors': 0
    }

    # Get tests with no component but with epic
    tests_missing_components = session.query(Test).filter(
        Test.component.is_(None),
        Test.epic_id.isnot(None)
    ).all()

    stats['total_tests'] = len(tests_missing_components)

    for test in tests_missing_components:
        try:
            stats['tests_processed'] += 1

            # Get first component from epic's comma-separated components
            epic_components = [c.strip() for c in test.epic.component.split(',') if c.strip()]
            if epic_components:
                component_to_inherit = epic_components[0]  # Take first component

                logger.info(f"Test {test.test_file_path}: Inheriting component '{component_to_inherit}' from epic {test.epic.epic_id}")

                if not dry_run:
                    test.component = component_to_inherit
                    stats['tests_updated'] += 1

        except Exception as e:
            logger.error(f"Error processing test {test.test_file_path}: {e}")
            stats['errors'] += 1

    return stats

def fix_all_missing_components(dry_run: bool = True) -> dict:
    """
    Fix all missing component inheritance issues.

    Args:
        dry_run: If True, don't apply changes

    Returns:
        Dict with complete results
    """
    logger.info(f"=== Fix Missing Components (dry_run={dry_run}) ===")

    results = {
        'dry_run': dry_run,
        'defect_stats': {},
        'test_stats': {},
        'success': False
    }

    session = SessionLocal()
    try:
        # Fix defects
        results['defect_stats'] = inherit_defect_components_from_epics(session, dry_run)

        # Fix tests
        results['test_stats'] = inherit_test_components_from_epics(session, dry_run)

        if not dry_run:
            session.commit()
            logger.info("✅ Component inheritance changes committed")
        else:
            logger.info("🔍 DRY RUN - No changes made")

        results['success'] = True

    except Exception as e:
        logger.error(f"❌ Error fixing missing components: {e}")
        if not dry_run:
            session.rollback()
        results['error'] = str(e)
    finally:
        session.close()

    return results

def main():
    """Main entry point for the missing component fix script."""
    import argparse

    parser = argparse.ArgumentParser(description='Fix missing component inheritance')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Only analyze and log what would be changed (default: True)')
    parser.add_argument('--execute', action='store_true', default=False,
                       help='Actually execute the fixes (overrides --dry-run)')
    parser.add_argument('--entity-type', choices=['defects', 'tests', 'all'], default='all',
                       help='Which entity types to fix (default: all)')

    args = parser.parse_args()

    # If --execute is specified, turn off dry run
    dry_run = args.dry_run and not args.execute

    logger.info("=== Missing Component Inheritance Fix ===")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")
    logger.info(f"Entity Types: {args.entity_type}")

    try:
        session = SessionLocal()

        if args.entity_type in ['defects', 'all']:
            defect_stats = inherit_defect_components_from_epics(session, dry_run)
            print(f"\n=== Defect Component Inheritance ===")
            print(f"Total Missing Components: {defect_stats['total_defects']}")
            print(f"Processed: {defect_stats['defects_processed']}")
            if not dry_run:
                print(f"Updated: {defect_stats['defects_updated']}")
            print(f"Errors: {defect_stats['errors']}")

        if args.entity_type in ['tests', 'all']:
            test_stats = inherit_test_components_from_epics(session, dry_run)
            print(f"\n=== Test Component Inheritance ===")
            print(f"Total Missing Components: {test_stats['total_tests']}")
            print(f"Processed: {test_stats['tests_processed']}")
            if not dry_run:
                print(f"Updated: {test_stats['tests_updated']}")
            print(f"Errors: {test_stats['errors']}")

        if not dry_run:
            session.commit()
            print(f"\n✅ Changes committed to database")
        else:
            print(f"\n🔍 This was a DRY RUN. No changes were made.")
            print("Run with --execute to apply the changes.")

        session.close()

    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()