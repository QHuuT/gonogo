#!/usr/bin/env python3
"""
Repair Defect-User Story Relationship Links

This script finds and repairs broken defect-user story relationships by:
1. Parsing defect descriptions for US-XXXXX and #issue-number references
2. Validating references against existing user stories
3. Updating defect.github_user_story_number field with valid links
4. Logging all changes made for audit purposes

Related Issue: US-00011 - Fix Defect-User Story Relationship Links
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import re
import sys
import logging
from datetime import datetime
from typing import List, Dict, Optional

# Add src to path for imports
sys.path.append('src')

from be.database import SessionLocal
from be.models.traceability.defect import Defect
from be.models.traceability.user_story import UserStory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'quality/logs/defect_relationship_repair_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def parse_user_story_references(text: str) -> Dict[str, List[str]]:
    """
    Parse text for user story references in various formats.

    Returns:
        Dict with 'us_ids' and 'issue_numbers' lists
    """
    if not text:
        return {'us_ids': [], 'issue_numbers': []}

    # Find US-XXXXX format references
    us_matches = re.findall(r'US-(\d{5})', text, re.IGNORECASE)

    # Find #issue-number format references (but exclude obvious non-issue references)
    # Look for # followed by 1-5 digits, but not in contexts like version numbers
    issue_matches = re.findall(r'(?<!v)(?<!V)#(\d{1,5})(?!\.\d)', text)

    return {
        'us_ids': [f'US-{match}' for match in us_matches],
        'issue_numbers': [int(match) for match in issue_matches if 1 <= int(match) <= 99999]
    }


def find_matching_user_story(session, us_ids: List[str], issue_numbers: List[int]) -> Optional[UserStory]:
    """
    Find a matching user story for the given references.

    Prioritizes US-XXXXX format over issue numbers.
    """
    # Try US-XXXXX format first (more reliable)
    for us_id in us_ids:
        user_story = session.query(UserStory).filter(
            UserStory.user_story_id == us_id
        ).first()
        if user_story:
            logger.debug(f"Found user story via US ID: {us_id} -> {user_story.user_story_id}")
            return user_story

    # Try issue numbers if no US-XXXXX match found
    for issue_num in issue_numbers:
        user_story = session.query(UserStory).filter(
            UserStory.github_issue_number == issue_num
        ).first()
        if user_story:
            logger.debug(f"Found user story via issue number: #{issue_num} -> {user_story.user_story_id}")
            return user_story

    return None


def repair_defect_relationships(dry_run: bool = True) -> Dict[str, int]:
    """
    Main repair function for defect-user story relationships.

    Args:
        dry_run: If True, only log what would be changed without making changes

    Returns:
        Dict with repair statistics
    """
    logger.info(f"Starting defect relationship repair (dry_run={dry_run})")

    session = SessionLocal()
    stats = {
        'total_defects': 0,
        'orphaned_defects': 0,
        'defects_with_references': 0,
        'successful_repairs': 0,
        'failed_repairs': 0,
        'broken_links_fixed': 0
    }

    try:
        # Get all defects without user story links
        orphaned_defects = session.query(Defect).filter(
            Defect.github_user_story_number.is_(None)
        ).all()

        stats['total_defects'] = session.query(Defect).count()
        stats['orphaned_defects'] = len(orphaned_defects)

        logger.info(f"Found {len(orphaned_defects)} orphaned defects to analyze")

        for defect in orphaned_defects:
            # Combine title and description for analysis
            title = defect.title or ''
            description = defect.description or ''
            combined_text = f'{title} {description}'

            # Parse for user story references
            references = parse_user_story_references(combined_text)

            if references['us_ids'] or references['issue_numbers']:
                stats['defects_with_references'] += 1
                logger.info(f"Analyzing {defect.defect_id}: \"{title[:50]}...\"")
                logger.info(f"  US references: {references['us_ids']}")
                logger.info(f"  Issue references: {references['issue_numbers']}")

                # Find matching user story
                user_story = find_matching_user_story(
                    session,
                    references['us_ids'],
                    references['issue_numbers']
                )

                if user_story:
                    logger.info(f"  ✓ Found matching user story: {user_story.user_story_id} (GitHub #{user_story.github_issue_number})")

                    if not dry_run:
                        defect.github_user_story_number = user_story.github_issue_number
                        logger.info(f"  ✓ Updated {defect.defect_id}.github_user_story_number = {user_story.github_issue_number}")
                    else:
                        logger.info(f"  ✓ DRY RUN: Would update {defect.defect_id}.github_user_story_number = {user_story.github_issue_number}")

                    stats['successful_repairs'] += 1
                else:
                    logger.warning(f"  ✗ No matching user story found for references: {references}")
                    stats['failed_repairs'] += 1

        # Check for and fix broken links (defects pointing to non-existent user stories)
        linked_defects = session.query(Defect).filter(
            Defect.github_user_story_number.isnot(None)
        ).all()

        for defect in linked_defects:
            user_story = session.query(UserStory).filter(
                UserStory.github_issue_number == defect.github_user_story_number
            ).first()

            if not user_story:
                logger.warning(f"BROKEN LINK: {defect.defect_id} -> US #{defect.github_user_story_number} (NOT FOUND)")
                if not dry_run:
                    defect.github_user_story_number = None
                    logger.info(f"  ✓ Cleared broken link for {defect.defect_id}")
                else:
                    logger.info(f"  ✓ DRY RUN: Would clear broken link for {defect.defect_id}")

                stats['broken_links_fixed'] += 1

        if not dry_run:
            session.commit()
            logger.info("All changes committed to database")
        else:
            logger.info("DRY RUN: No changes committed to database")

    except Exception as e:
        logger.error(f"Error during repair: {e}")
        session.rollback()
        raise
    finally:
        session.close()

    return stats


def validate_relationships() -> Dict[str, int]:
    """
    Validate all defect-user story relationships for consistency.

    Returns:
        Dict with validation statistics
    """
    logger.info("Starting relationship validation")

    session = SessionLocal()
    validation_stats = {
        'total_defects': 0,
        'linked_defects': 0,
        'valid_links': 0,
        'broken_links': 0,
        'orphaned_defects': 0
    }

    try:
        validation_stats['total_defects'] = session.query(Defect).count()

        # Check linked defects
        linked_defects = session.query(Defect).filter(
            Defect.github_user_story_number.isnot(None)
        ).all()
        validation_stats['linked_defects'] = len(linked_defects)

        for defect in linked_defects:
            user_story = session.query(UserStory).filter(
                UserStory.github_issue_number == defect.github_user_story_number
            ).first()

            if user_story:
                validation_stats['valid_links'] += 1
                logger.debug(f"VALID: {defect.defect_id} -> {user_story.user_story_id}")
            else:
                validation_stats['broken_links'] += 1
                logger.error(f"BROKEN: {defect.defect_id} -> US #{defect.github_user_story_number} (NOT FOUND)")

        # Check orphaned defects
        validation_stats['orphaned_defects'] = session.query(Defect).filter(
            Defect.github_user_story_number.is_(None)
        ).count()

        logger.info(f"Validation complete: {validation_stats['valid_links']} valid, {validation_stats['broken_links']} broken, {validation_stats['orphaned_defects']} orphaned")

    except Exception as e:
        logger.error(f"Error during validation: {e}")
        raise
    finally:
        session.close()

    return validation_stats


def main():
    """Main entry point for the repair script."""
    import argparse

    parser = \
        argparse.ArgumentParser(description='Repair defect-user story relationship links')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Only analyze and log what would be changed (default: True)')
    parser.add_argument('--execute', action='store_true', default=False,
                       help='Actually execute the repairs (overrides --dry-run)')
    parser.add_argument('--validate-only', action='store_true', default=False,
                       help='Only validate existing relationships without repair')

    args = parser.parse_args()

    # If --execute is specified, turn off dry run
    dry_run = args.dry_run and not args.execute

    logger.info("=== Defect-User Story Relationship Repair Tool ===")
    logger.info(f"Mode: {'VALIDATION ONLY' if args.validate_only else ('DRY RUN' if dry_run else 'EXECUTION')}")

    try:
        if args.validate_only:
            validation_stats = validate_relationships()
            print("\n=== Validation Results ===")
            for key, value in validation_stats.items():
                print(f"{key.replace('_', ' ').title()}: {value}")
        else:
            repair_stats = repair_defect_relationships(dry_run=dry_run)

            print("\n=== Repair Results ===")
            for key, value in repair_stats.items():
                print(f"{key.replace('_', ' ').title()}: {value}")

            if dry_run:
                print("\nThis was a DRY RUN. No changes were made.")
                print("Run with --execute to apply the changes.")
            else:
                print("\nChanges have been applied to the database.")

                # Run validation after repair
                print("\nRunning post-repair validation...")
                validation_stats = validate_relationships()
                print("\n=== Post-Repair Validation ===")
                for key, value in validation_stats.items():
                    print(f"{key.replace('_', ' ').title()}: {value}")

    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()