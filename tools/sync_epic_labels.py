#!/usr/bin/env python3
"""
Epic Label Synchronization Tool

This script synchronizes epic labels between the RTM database and GitHub repository.
Creates missing GitHub epic labels and ensures bidirectional consistency.

Related Issue: US-00006 - Implement Automated Epic Label Management and Inheritance System
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import json
import logging
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Set

# Add src to path for imports
sys.path.append('src')

from be.database import SessionLocal
from be.models.traceability.epic import Epic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_epic_label_name(epic_title: str, epic_id: str) -> str:
    """
    Generate a GitHub label name from epic title.

    Args:
        epic_title: Epic title (e.g., "Requirements Traceability Matrix Automation")
        epic_id: Epic ID (e.g., "EP-00005")

    Returns:
        Label name (e.g., "rtm-automation")
    """
    # Extract meaningful words from title
    title_lower = epic_title.lower()

    # Handle common patterns
    patterns = {
        'requirements traceability matrix': 'rtm',
        'github workflow integration': 'github-workflow',
        'github project management': 'github-project',
        'test logging and reporting': 'test-reporting',
        'gdpr-compliant comment system': 'comment-system',
        'privacy and consent management': 'privacy-consent',
        'blog content management': 'blog-content'
    }

    # Check for exact pattern matches first
    for pattern, label in patterns.items():
        if pattern in title_lower:
            return label

    # Extract key words and create label
    # Remove common stop words
    stop_words = {'and', 'the', 'of', 'for', 'with', 'in', 'on', 'at', 'to', 'a', 'an'}
    words = re.findall(r'\b[a-zA-Z]+\b', title_lower)

    # Filter meaningful words
    meaningful_words = [w for w in words if len(w) > 2 and w not in stop_words]

    # Take first 2-3 words and join with hyphens
    if len(meaningful_words) >= 2:
        label_words = meaningful_words[:2]
    else:
        # Fallback to epic number
        epic_num = epic_id.split('-')[-1]
        return f"epic-{epic_num.lstrip('0')}"

    return '-'.join(label_words)


def get_existing_github_epic_labels() -> Dict[str, Dict[str, str]]:
    """
    Get existing epic labels from GitHub.

    Returns:
        Dict mapping label names to label properties
    """
    import subprocess

    try:
        # Get all epic/ labels from GitHub
        result = subprocess.run(
            ['gh', 'label', 'list', '--search', 'epic/'],
            capture_output=True,
            text=True,
            check=True
        )

        epic_labels = {}
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                # Parse gh label list output: name<tab>description<tab>color
                parts = line.split('\t')
                if len(parts) >= 3:
                    name = parts[0]
                    description = parts[1]
                    color = parts[2]

                    epic_labels[name] = {
                        'description': description,
                        'color': color
                    }

        logger.info(f"Found {len(epic_labels)} existing epic labels in GitHub")
        return epic_labels

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get GitHub labels: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error getting GitHub labels: {e}")
        return {}


def create_github_epic_label(epic_id: str, epic_title: str, label_name: str) -> bool:
    """
    Create a new epic label in GitHub.

    Args:
        epic_id: Epic ID (e.g., "EP-00005")
        epic_title: Epic title
        label_name: Label name (e.g., "rtm-automation")

    Returns:
        True if successful, False otherwise
    """
    import subprocess

    try:
        full_label_name = f"epic/{label_name}"
        description = f"{epic_id}: {epic_title}"
        color = "c5def5"  # Light blue color matching existing epic labels

        result = subprocess.run(
            ['gh', 'label', 'create', full_label_name, '--description', description, '--color', color],
            capture_output=True,
            text=True,
            check=True
        )

        logger.info(f"✅ Created GitHub label: {full_label_name}")
        return True

    except subprocess.CalledProcessError as e:
        if "already exists" in e.stderr:
            logger.info(f"⚠️ Label {full_label_name} already exists")
            return True
        else:
            logger.error(f"❌ Failed to create label {full_label_name}: {e.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Error creating label {full_label_name}: {e}")
        return False


def sync_epic_labels_to_github(session) -> Dict[str, any]:
    """
    Sync epic labels from database to GitHub.

    Args:
        session: Database session

    Returns:
        Dict with sync statistics
    """
    logger.info("Syncing epic labels from database to GitHub")

    stats = {
        'total_epics': 0,
        'existing_labels': 0,
        'created_labels': 0,
        'failed_labels': 0,
        'updated_database': 0
    }

    # Get existing GitHub labels
    existing_labels = get_existing_github_epic_labels()

    # Get all epics from database
    epics = session.query(Epic).all()
    stats['total_epics'] = len(epics)

    for epic in epics:
        # Generate label name
        label_name = generate_epic_label_name(epic.title, epic.epic_id)
        full_label_name = f"epic/{label_name}"

        # Check if label already exists
        if full_label_name in existing_labels:
            logger.info(f"✅ Label {full_label_name} already exists for {epic.epic_id}")
            stats['existing_labels'] += 1
        else:
            # Create new label
            if create_github_epic_label(epic.epic_id, epic.title, label_name):
                stats['created_labels'] += 1
            else:
                stats['failed_labels'] += 1
                continue

        # Update epic in database with label name
        if epic.epic_label_name != label_name:
            epic.update_epic_label_info(label_name)
            stats['updated_database'] += 1
            logger.info(f"Updated {epic.epic_id} label info: {label_name} -> epic/{label_name}")

    return stats


def validate_epic_label_consistency() -> Dict[str, any]:
    """
    Validate consistency between database epics and GitHub epic labels.

    Returns:
        Dict with validation results
    """
    logger.info("Validating epic label consistency")

    results = {
        'database_epics': [],
        'github_labels': [],
        'missing_in_github': [],
        'orphaned_in_github': [],
        'consistent': True
    }

    session = SessionLocal()
    try:
        # Get database epics
        epics = session.query(Epic).all()
        for epic in epics:
            label_name = generate_epic_label_name(epic.title, epic.epic_id)
            results['database_epics'].append({
                'epic_id': epic.epic_id,
                'title': epic.title,
                'expected_label': f"epic/{label_name}"
            })

        # Get GitHub epic labels
        github_labels = get_existing_github_epic_labels()
        results['github_labels'] = list(github_labels.keys())

        # Find missing labels
        expected_labels = {item['expected_label'] for item in results['database_epics']}
        existing_labels = set(github_labels.keys())

        results['missing_in_github'] = list(expected_labels - existing_labels)
        results['orphaned_in_github'] = list(existing_labels - expected_labels)

        # Check consistency
        if results['missing_in_github'] or results['orphaned_in_github']:
            results['consistent'] = False

        logger.info(f"Validation complete - Consistent: {results['consistent']}")

    except Exception as e:
        logger.error(f"Error during validation: {e}")
        results['error'] = str(e)
    finally:
        session.close()

    return results


def sync_all_epic_labels(dry_run: bool = True) -> Dict[str, any]:
    """
    Sync all epic labels between database and GitHub.

    Args:
        dry_run: If True, don't create labels, just analyze

    Returns:
        Dict with sync results
    """
    logger.info(f"Starting epic label sync (dry_run={dry_run})")

    results = {
        'dry_run': dry_run,
        'validation': {},
        'sync_stats': {},
        'success': False
    }

    try:
        # First validate current state
        results['validation'] = validate_epic_label_consistency()

        if not dry_run:
            # Perform actual sync
            session = SessionLocal()
            try:
                results['sync_stats'] = sync_epic_labels_to_github(session)
                session.commit()
                logger.info("✅ Epic label sync completed successfully")
                results['success'] = True
            except Exception as e:
                logger.error(f"❌ Error during sync: {e}")
                session.rollback()
                results['error'] = str(e)
            finally:
                session.close()
        else:
            logger.info("🔍 DRY RUN - No changes made")
            results['success'] = True

    except Exception as e:
        logger.error(f"❌ Epic label sync failed: {e}")
        results['error'] = str(e)

    return results


def main():
    """Main entry point for the epic label sync script."""
    import argparse

    parser = argparse.ArgumentParser(description='Sync epic labels between database and GitHub')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Only analyze and log what would be changed (default: True)')
    parser.add_argument('--execute', action='store_true', default=False,
                       help='Actually execute the sync (overrides --dry-run)')
    parser.add_argument('--validate-only', action='store_true', default=False,
                       help='Only validate consistency, don\'t sync')

    args = parser.parse_args()

    # If --execute is specified, turn off dry run
    dry_run = args.dry_run and not args.execute

    logger.info("=== Epic Label Synchronization ===")
    logger.info(f"Mode: {'VALIDATION ONLY' if args.validate_only else ('DRY RUN' if dry_run else 'EXECUTION')}")

    try:
        if args.validate_only:
            # Only run validation
            results = validate_epic_label_consistency()

            print("\n=== Epic Label Validation Results ===")
            print(f"Database Epics: {len(results['database_epics'])}")
            print(f"GitHub Epic Labels: {len(results['github_labels'])}")
            print(f"Missing in GitHub: {len(results['missing_in_github'])}")
            print(f"Orphaned in GitHub: {len(results['orphaned_in_github'])}")
            print(f"Consistent: {'✅ YES' if results['consistent'] else '❌ NO'}")

            if results['missing_in_github']:
                print(f"\nMissing labels: {results['missing_in_github']}")
            if results['orphaned_in_github']:
                print(f"Orphaned labels: {results['orphaned_in_github']}")

        else:
            # Run full sync
            results = sync_all_epic_labels(dry_run=dry_run)

            print("\n=== Epic Label Sync Results ===")

            # Validation results
            validation = results.get('validation', {})
            print(f"Database Epics: {len(validation.get('database_epics', []))}")
            print(f"GitHub Epic Labels: {len(validation.get('github_labels', []))}")
            print(f"Missing in GitHub: {len(validation.get('missing_in_github', []))}")

            # Sync results (if not dry run)
            sync_stats = results.get('sync_stats', {})
            if sync_stats:
                print(f"\nSync Statistics:")
                for key, value in sync_stats.items():
                    print(f"  {key.replace('_', ' ').title()}: {value}")

            print(f"\nOverall Success: {'✅ YES' if results['success'] else '❌ NO'}")

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