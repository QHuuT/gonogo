#!/usr/bin/env python3
"""
Sync Component Data from GitHub Labels

This script synchronizes component data from GitHub issue labels to the database.
Populates the component field for User Stories, Defects, and Tests based on GitHub labels.

Related Issue: US-00009 - Implement Component Inheritance System
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import json
import sys
import logging
from typing import Dict, Optional

# Add src to path for imports
sys.path.append("src")

from be.database import SessionLocal
from be.models.traceability.defect import Defect
from be.models.traceability.epic import Epic
from be.models.traceability.user_story import UserStory

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_component_from_labels(github_labels: str) -> Optional[str]:
    """
    Parse component from GitHub labels string.

    Args:
        github_labels: JSON string of GitHub labels

    Returns:
        Component name or None
    """
    if not github_labels or github_labels == "None":
        return None

    try:
        # Handle both string representation of list and actual JSON
        if github_labels.startswith("[") and github_labels.endswith("]"):
            # String representation of list
            labels_str = github_labels.strip("[]").replace("'", '"')
            if labels_str:
                labels = json.loads(f"[{labels_str}]")
            else:
                labels = []
        else:
            # Assume it's JSON
            labels = json.loads(github_labels)

        # Find component/ labels
        for label in labels:
            if isinstance(label, dict) and "name" in label:
                label_name = label["name"]
            elif isinstance(label, str):
                label_name = label
            else:
                continue

            if label_name.startswith("component/"):
                component = label_name.replace("component/", "").lower()
                # Normalize component names
                component_mapping = {
                    "frontend": "frontend",
                    "backend": "backend",
                    "database": "database",
                    "security": "security",
                    "testing": "testing",
                    "ci-cd": "ci-cd",
                    "documentation": "documentation",
                }
                return component_mapping.get(component, component)

    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Error parsing labels '{github_labels}': {e}")

    return None


def sync_user_story_components(session) -> Dict[str, int]:
    """Sync User Story components from GitHub labels."""
    logger.info("Syncing User Story components from GitHub labels")

    stats = {
        "total_user_stories": 0,
        "updated_components": 0,
        "no_github_labels": 0,
        "no_component_labels": 0,
    }

    user_stories = session.query(UserStory).all()
    stats["total_user_stories"] = len(user_stories)

    for user_story in user_stories:
        if not user_story.github_labels:
            stats["no_github_labels"] += 1
            continue

        component = parse_component_from_labels(user_story.github_labels)
        if component:
            old_component = user_story.component
            user_story.component = component
            stats["updated_components"] += 1
            logger.info(
                f"Updated {user_story.user_story_id} component: {old_component} → {component}"
            )
        else:
            stats["no_component_labels"] += 1

    return stats


def sync_defect_components(session) -> Dict[str, int]:
    """Sync Defect components from GitHub labels."""
    logger.info("Syncing Defect components from GitHub labels")

    stats = {
        "total_defects": 0,
        "updated_components": 0,
        "no_github_labels": 0,
        "no_component_labels": 0,
    }

    defects = session.query(Defect).all()
    stats["total_defects"] = len(defects)

    for defect in defects:
        if not defect.github_labels:
            stats["no_github_labels"] += 1
            continue

        component = parse_component_from_labels(defect.github_labels)
        if component:
            old_component = defect.component
            defect.component = component
            stats["updated_components"] += 1
            logger.info(
                f"Updated {defect.defect_id} component: {old_component} → {component}"
            )
        else:
            stats["no_component_labels"] += 1

    return stats


def sync_epic_components(session) -> Dict[str, int]:
    """Sync Epic components from GitHub labels."""
    logger.info("Syncing Epic components from GitHub labels")

    stats = {
        "total_epics": 0,
        "updated_components": 0,
        "no_github_labels": 0,
        "no_component_labels": 0,
    }

    epics = session.query(Epic).all()
    stats["total_epics"] = len(epics)

    for epic in epics:
        if not hasattr(epic, "github_labels") or not epic.github_labels:
            stats["no_github_labels"] += 1
            continue

        component = parse_component_from_labels(epic.github_labels)
        if component:
            old_component = epic.component
            epic.component = component
            stats["updated_components"] += 1
            logger.info(
                f"Updated {epic.epic_id} component: {old_component} → {component}"
            )
        else:
            stats["no_component_labels"] += 1

    return stats


def sync_all_components(dry_run: bool = True) -> Dict[str, any]:
    """
    Sync all component data from GitHub labels.

    Args:
        dry_run: If True, don't commit changes to database

    Returns:
        Dict with sync statistics
    """
    logger.info(f"Starting component sync from GitHub labels (dry_run={dry_run})")

    session = SessionLocal()
    results = {
        "dry_run": dry_run,
        "user_story_stats": {},
        "defect_stats": {},
        "epic_stats": {},
        "total_updates": 0,
    }

    try:
        # Sync User Stories
        results["user_story_stats"] = sync_user_story_components(session)

        # Sync Defects
        results["defect_stats"] = sync_defect_components(session)

        # Sync Epics
        results["epic_stats"] = sync_epic_components(session)

        # Calculate total updates
        results["total_updates"] = (
            results["user_story_stats"]["updated_components"]
            + results["defect_stats"]["updated_components"]
            + results["epic_stats"]["updated_components"]
        )

        if not dry_run:
            session.commit()
            logger.info(f"Committed {results['total_updates']} component updates")
        else:
            session.rollback()
            logger.info(
                f"DRY RUN: Would commit {results['total_updates']} component updates"
            )

    except Exception as e:
        logger.error(f"Error during component sync: {e}")
        session.rollback()
        raise
    finally:
        session.close()

    return results


def main():
    """Main entry point for the sync script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Sync component data from GitHub labels"
    )
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
        help="Actually execute the sync (overrides --dry-run)",
    )

    args = parser.parse_args()

    # If --execute is specified, turn off dry run
    dry_run = args.dry_run and not args.execute

    logger.info("=== Component Sync from GitHub Labels ===")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")

    try:
        results = sync_all_components(dry_run=dry_run)

        print("\n=== Component Sync Results ===")
        for category, stats in results.items():
            if category == "dry_run" or category == "total_updates":
                continue
            print(f"\n{category.replace('_', ' ').title()}:")
            for key, value in stats.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")

        print(f"\nTotal Updates: {results['total_updates']}")

        if dry_run:
            print("\nThis was a DRY RUN. No changes were made.")
            print("Run with --execute to apply the changes.")
        else:
            print("\nChanges have been applied to the database.")

    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
