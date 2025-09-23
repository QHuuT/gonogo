#!/usr/bin/env python3
"""
Epic Label Inheritance System

This script implements comprehensive epic label inheritance for all entity types:
- User Stories inherit from parent epic
- Defects inherit from parent user story or direct epic reference
- All test types inherit from associated user story or direct epic reference

Related Issue: US-00006 - Implement Automated Epic Label Management and Inheritance System
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import json
import logging
import re
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

# Add src to path for imports
sys.path.append('src')

from be.database import SessionLocal
from be.models.traceability.defect import Defect
from be.models.traceability.epic import Epic
from be.models.traceability.test import Test
from be.models.traceability.user_story import UserStory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_github_issue_labels(issue_number: int) -> List[str]:
    """
    Get current labels from a GitHub issue.

    Args:
        issue_number: GitHub issue number

    Returns:
        List of label names
    """
    try:
        result = subprocess.run(
            ['gh', 'issue', 'view', str(issue_number), '--json', 'labels'],
            capture_output=True,
            text=True,
            check=True
        )

        issue_data = json.loads(result.stdout)
        labels = [label['name'] for label in issue_data.get('labels', [])]
        return labels

    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to get labels for issue #{issue_number}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error getting labels for issue #{issue_number}: {e}")
        return []


def add_github_issue_labels(issue_number: int, labels_to_add: List[str]) -> bool:
    """
    Add labels to a GitHub issue.

    Args:
        issue_number: GitHub issue number
        labels_to_add: List of labels to add

    Returns:
        True if successful, False otherwise
    """
    if not labels_to_add:
        return True

    try:
        # Convert labels to --add-label arguments
        label_args = []
        for label in labels_to_add:
            label_args.extend(['--add-label', label])

        result = subprocess.run(
            ['gh', 'issue', 'edit', str(issue_number)] + label_args,
            capture_output=True,
            text=True,
            check=True
        )

        logger.info(f"✅ Added labels to issue #{issue_number}: {labels_to_add}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to add labels to issue #{issue_number}: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"❌ Error adding labels to issue #{issue_number}: {e}")
        return False


def inherit_epic_labels_for_user_stories(session, dry_run: bool = True) -> Dict[str, int]:
    """
    Apply epic label inheritance for user stories.

    Args:
        session: Database session
        dry_run: If True, don't apply changes

    Returns:
        Dict with inheritance statistics
    """
    logger.info("Processing epic label inheritance for user stories")

    stats = {
        'total_user_stories': 0,
        'user_stories_processed': 0,
        'labels_added': 0,
        'github_updates': 0,
        'errors': 0
    }

    user_stories = session.query(UserStory).join(Epic).all()
    stats['total_user_stories'] = len(user_stories)

    for user_story in user_stories:
        try:
            # Get epic information
            epic = user_story.epic
            if not epic:
                continue

            # Generate expected epic labels
            epic_label = epic.get_github_epic_label()  # e.g., "epic/rtm"
            component_label = epic.get_component_label()  # e.g., "component/backend"

            expected_labels = [epic_label, component_label]

            # Get current GitHub labels
            if user_story.github_issue_number:
                current_labels = get_github_issue_labels(user_story.github_issue_number)

                # Find missing labels
                missing_labels = [label for label in expected_labels if label not in current_labels]

                if missing_labels:
                    stats['user_stories_processed'] += 1
                    stats['labels_added'] += len(missing_labels)

                    logger.info(f"US {user_story.user_story_id} (#{user_story.github_issue_number}): "
                               f"Adding labels {missing_labels}")

                    if not dry_run:
                        if add_github_issue_labels(user_story.github_issue_number, missing_labels):
                            stats['github_updates'] += 1
                        else:
                            stats['errors'] += 1

        except Exception as e:
            logger.error(f"Error processing user story {user_story.user_story_id}: {e}")
            stats['errors'] += 1

    return stats


def inherit_epic_labels_for_defects(session, dry_run: bool = True) -> Dict[str, int]:
    """
    Apply epic label inheritance for defects.

    Args:
        session: Database session
        dry_run: If True, don't apply changes

    Returns:
        Dict with inheritance statistics
    """
    logger.info("Processing epic label inheritance for defects")

    stats = {
        'total_defects': 0,
        'defects_processed': 0,
        'labels_added': 0,
        'github_updates': 0,
        'errors': 0
    }

    defects = session.query(Defect).all()
    stats['total_defects'] = len(defects)

    for defect in defects:
        try:
            epic = None
            inheritance_source = None

            # Try to find epic through user story relationship
            if defect.github_user_story_number:
                parent_us = session.query(UserStory).filter(
                    UserStory.github_issue_number == defect.github_user_story_number
                ).first()
                if parent_us and parent_us.epic:
                    epic = parent_us.epic
                    inheritance_source = f"via US-{parent_us.user_story_id}"

            # Try direct epic relationship
            if not epic and defect.epic:
                epic = defect.epic
                inheritance_source = "direct epic reference"

            if not epic:
                continue

            # Generate expected epic labels
            epic_label = epic.get_github_epic_label()
            component_label = epic.get_component_label()
            expected_labels = [epic_label, component_label]

            # Get current GitHub labels
            if defect.github_issue_number:
                current_labels = get_github_issue_labels(defect.github_issue_number)

                # Find missing labels
                missing_labels = [label for label in expected_labels if label not in current_labels]

                if missing_labels:
                    stats['defects_processed'] += 1
                    stats['labels_added'] += len(missing_labels)

                    logger.info(f"DEF {defect.defect_id} (#{defect.github_issue_number}): "
                               f"Adding labels {missing_labels} ({inheritance_source})")

                    if not dry_run:
                        if add_github_issue_labels(defect.github_issue_number, missing_labels):
                            stats['github_updates'] += 1
                        else:
                            stats['errors'] += 1

        except Exception as e:
            logger.error(f"Error processing defect {defect.defect_id}: {e}")
            stats['errors'] += 1

    return stats


def find_test_epic_relationship(test: Test, session) -> Tuple[Optional[Epic], Optional[str]]:
    """
    Find epic relationship for a test through various inheritance paths.

    Args:
        test: Test entity
        session: Database session

    Returns:
        Tuple of (Epic, inheritance_source) or (None, None)
    """
    # Direct epic relationship
    if test.epic:
        return test.epic, "direct epic reference"

    # Through user story relationship
    if test.github_user_story_number:
        parent_us = session.query(UserStory).filter(
            UserStory.github_issue_number == test.github_user_story_number
        ).first()
        if parent_us and parent_us.epic:
            return parent_us.epic, f"via US-{parent_us.user_story_id}"

    # Through defect relationship (if test is for a defect)
    if hasattr(test, 'github_defect_number') and test.github_defect_number:
        parent_defect = session.query(Defect).filter(
            Defect.github_issue_number == test.github_defect_number
        ).first()
        if parent_defect:
            # Try defect -> user story -> epic
            if parent_defect.github_user_story_number:
                grandparent_us = session.query(UserStory).filter(
                    UserStory.github_issue_number == parent_defect.github_user_story_number
                ).first()
                if grandparent_us and grandparent_us.epic:
                    return grandparent_us.epic, f"via DEF-{parent_defect.defect_id} -> US-{grandparent_us.user_story_id}"

            # Direct defect -> epic
            if parent_defect.epic:
                return parent_defect.epic, f"via DEF-{parent_defect.defect_id}"

    # File-based epic inference (parse test file path/name for epic markers)
    if test.test_file:
        epic_patterns = [
            (r'ep[-_]?00*1\b', 'EP-00001'),
            (r'ep[-_]?00*2\b', 'EP-00002'),
            (r'ep[-_]?00*3\b', 'EP-00003'),
            (r'ep[-_]?00*4\b', 'EP-00004'),
            (r'ep[-_]?00*5\b', 'EP-00005'),
            (r'ep[-_]?00*6\b', 'EP-00006'),
            (r'ep[-_]?00*7\b', 'EP-00007'),
            (r'blog|content', 'EP-00001'),
            (r'comment|gdpr', 'EP-00002'),
            (r'privacy|consent', 'EP-00003'),
            (r'github.*workflow', 'EP-00004'),
            (r'rtm|traceability', 'EP-00005'),
            (r'github.*project', 'EP-00006'),
            (r'test.*report|logging', 'EP-00007'),
        ]

        test_path_lower = test.test_file.lower()
        for pattern, epic_id in epic_patterns:
            if re.search(pattern, test_path_lower):
                epic = session.query(Epic).filter(Epic.epic_id == epic_id).first()
                if epic:
                    return epic, f"inferred from file path: {pattern}"

    return None, None


def inherit_epic_labels_for_tests(session, dry_run: bool = True) -> Dict[str, int]:
    """
    Apply epic label inheritance for all test types.

    Args:
        session: Database session
        dry_run: If True, don't apply changes

    Returns:
        Dict with inheritance statistics
    """
    logger.info("Processing epic label inheritance for all test types")

    stats = {
        'total_tests': 0,
        'tests_processed': 0,
        'tests_with_epics': 0,
        'tests_without_epics': 0,
        'inheritance_sources': {},
        'epic_distribution': {},
        'errors': 0
    }

    tests = session.query(Test).all()
    stats['total_tests'] = len(tests)

    for test in tests:
        try:
            epic, inheritance_source = find_test_epic_relationship(test, session)

            if epic:
                stats['tests_with_epics'] += 1

                # Track inheritance sources
                if inheritance_source not in stats['inheritance_sources']:
                    stats['inheritance_sources'][inheritance_source] = 0
                stats['inheritance_sources'][inheritance_source] += 1

                # Track epic distribution
                if epic.epic_id not in stats['epic_distribution']:
                    stats['epic_distribution'][epic.epic_id] = 0
                stats['epic_distribution'][epic.epic_id] += 1

                # Update test epic relationship in database
                if test.epic_id != epic.id:
                    logger.info(f"Test {test.test_file}: Linking to {epic.epic_id} ({inheritance_source})")
                    if not dry_run:
                        test.epic_id = epic.id
                        stats['tests_processed'] += 1

            else:
                stats['tests_without_epics'] += 1
                logger.debug(f"Test {test.test_file}: No epic relationship found")

        except Exception as e:
            logger.error(f"Error processing test {test.test_file}: {e}")
            stats['errors'] += 1

    return stats


def run_comprehensive_epic_inheritance(dry_run: bool = True) -> Dict[str, any]:
    """
    Run comprehensive epic label inheritance for all entity types.

    Args:
        dry_run: If True, don't apply changes

    Returns:
        Dict with comprehensive results
    """
    logger.info(f"Starting comprehensive epic label inheritance (dry_run={dry_run})")

    results = {
        'dry_run': dry_run,
        'user_story_stats': {},
        'defect_stats': {},
        'test_stats': {},
        'summary': {},
        'success': False
    }

    session = SessionLocal()
    try:
        # Process user stories
        results['user_story_stats'] = inherit_epic_labels_for_user_stories(session, dry_run)

        # Process defects
        results['defect_stats'] = inherit_epic_labels_for_defects(session, dry_run)

        # Process all test types
        results['test_stats'] = inherit_epic_labels_for_tests(session, dry_run)

        # Generate summary
        results['summary'] = {
            'total_entities_processed': (
                results['user_story_stats']['user_stories_processed'] +
                results['defect_stats']['defects_processed'] +
                results['test_stats']['tests_processed']
            ),
            'total_labels_added': (
                results['user_story_stats']['labels_added'] +
                results['defect_stats']['labels_added']
            ),
            'total_github_updates': (
                results['user_story_stats']['github_updates'] +
                results['defect_stats']['github_updates']
            ),
            'total_errors': (
                results['user_story_stats']['errors'] +
                results['defect_stats']['errors'] +
                results['test_stats']['errors']
            )
        }

        if not dry_run:
            session.commit()
            logger.info("✅ Epic label inheritance completed successfully")
        else:
            session.rollback()
            logger.info("🔍 DRY RUN - No changes committed")

        results['success'] = True

    except Exception as e:
        logger.error(f"❌ Error during epic label inheritance: {e}")
        session.rollback()
        results['error'] = str(e)
    finally:
        session.close()

    return results


def main():
    """Main entry point for the epic label inheritance script."""
    import argparse

    parser = argparse.ArgumentParser(description='Apply epic label inheritance to all entity types')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Only analyze and log what would be changed (default: True)')
    parser.add_argument('--execute', action='store_true', default=False,
                       help='Actually apply the inheritance (overrides --dry-run)')
    parser.add_argument('--entity-type', choices=['user-stories', 'defects', 'tests', 'all'], default='all',
                       help='Which entity types to process (default: all)')

    args = parser.parse_args()

    # If --execute is specified, turn off dry run
    dry_run = args.dry_run and not args.execute

    logger.info("=== Epic Label Inheritance System ===")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")
    logger.info(f"Entity Types: {args.entity_type}")

    try:
        if args.entity_type == 'all':
            results = run_comprehensive_epic_inheritance(dry_run=dry_run)
        else:
            # Run specific entity type
            session = SessionLocal()
            try:
                if args.entity_type == 'user-stories':
                    results = {'user_story_stats': inherit_epic_labels_for_user_stories(session, dry_run)}
                elif args.entity_type == 'defects':
                    results = {'defect_stats': inherit_epic_labels_for_defects(session, dry_run)}
                elif args.entity_type == 'tests':
                    results = {'test_stats': inherit_epic_labels_for_tests(session, dry_run)}

                if not dry_run:
                    session.commit()
                else:
                    session.rollback()

                results['success'] = True
            except Exception as e:
                session.rollback()
                results = {'error': str(e), 'success': False}
            finally:
                session.close()

        print("\n=== Epic Label Inheritance Results ===")

        # User Story Results
        if 'user_story_stats' in results:
            us_stats = results['user_story_stats']
            print(f"\nUser Stories:")
            print(f"  Total: {us_stats.get('total_user_stories', 0)}")
            print(f"  Processed: {us_stats.get('user_stories_processed', 0)}")
            print(f"  Labels Added: {us_stats.get('labels_added', 0)}")
            print(f"  GitHub Updates: {us_stats.get('github_updates', 0)}")

        # Defect Results
        if 'defect_stats' in results:
            defect_stats = results['defect_stats']
            print(f"\nDefects:")
            print(f"  Total: {defect_stats.get('total_defects', 0)}")
            print(f"  Processed: {defect_stats.get('defects_processed', 0)}")
            print(f"  Labels Added: {defect_stats.get('labels_added', 0)}")
            print(f"  GitHub Updates: {defect_stats.get('github_updates', 0)}")

        # Test Results
        if 'test_stats' in results:
            test_stats = results['test_stats']
            print(f"\nTests:")
            print(f"  Total: {test_stats.get('total_tests', 0)}")
            print(f"  With Epic Links: {test_stats.get('tests_with_epics', 0)}")
            print(f"  Without Epic Links: {test_stats.get('tests_without_epics', 0)}")
            print(f"  Database Updates: {test_stats.get('tests_processed', 0)}")

            if test_stats.get('inheritance_sources'):
                print(f"  Inheritance Sources:")
                for source, count in test_stats['inheritance_sources'].items():
                    print(f"    {source}: {count}")

        # Summary
        if 'summary' in results:
            summary = results['summary']
            print(f"\nSummary:")
            print(f"  Total Entities Processed: {summary.get('total_entities_processed', 0)}")
            print(f"  Total Labels Added: {summary.get('total_labels_added', 0)}")
            print(f"  Total GitHub Updates: {summary.get('total_github_updates', 0)}")
            print(f"  Total Errors: {summary.get('total_errors', 0)}")

        print(f"\nOverall Success: {'✅ YES' if results.get('success') else '❌ NO'}")

        if dry_run:
            print("\nThis was a DRY RUN. No changes were made.")
            print("Run with --execute to apply the changes.")
        else:
            print("\nChanges have been applied.")

    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()