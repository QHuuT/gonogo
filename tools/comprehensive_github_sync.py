#!/usr/bin/env python3
"""
Comprehensive GitHub Sync Tool

Unified tool that syncs all GitHub data including:
- User stories with epics and components
- Defects with epics and components
- Epic labels and metadata
- All GitHub labels (priority, status, release, etc.)

This replaces the need for multiple separate sync tools.
"""

import requests
import re
import os
import sys

sys.path.append("src")

from be.database import SessionLocal
from be.models.traceability.epic import Epic
from be.models.traceability.user_story import UserStory
from be.models.traceability.defect import Defect


def fetch_github_issues():
    """Fetch GitHub issues using API."""
    github_token = os.getenv("GITHUB_TOKEN")
    headers = {}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    print("Fetching GitHub issues...")
    url = "https://api.github.com/repos/QHuuT/gonogo/issues"
    params = {"state": "all", "per_page": 100}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Failed to fetch issues: {response.status_code}")
        return []

    issues = response.json()
    print(f"Found {len(issues)} GitHub issues")
    return issues


def extract_id_from_title(title: str, pattern: str):
    """Extract ID from title using pattern."""
    match = re.search(pattern, title)
    if match:
        return match.group(0)
    return None


def parse_github_labels(labels_list):
    """Parse GitHub labels into categorized information."""
    labels = [label["name"] for label in labels_list]

    parsed = {
        "epic": None,
        "component": None,
        "priority": None,
        "status": None,
        "release": None,
        "raw_labels": labels,
    }

    # Epic label mapping
    epic_label_mapping = {
        "epic/blog-content": "EP-00001",
        "epic/comment-system": "EP-00002",
        "epic/privacy-consent": "EP-00003",
        "epic/github-workflow": "EP-00004",
        "epic/rtm": "EP-00005",
        "epic/github-project": "EP-00006",
        "epic/test-reporting": "EP-00007",
    }

    for label in labels:
        if label in epic_label_mapping:
            parsed["epic"] = epic_label_mapping[label]
        elif label.startswith("component/"):
            parsed["component"] = label.replace("component/", "")
        elif label.startswith("priority/"):
            parsed["priority"] = label.replace("priority/", "")
        elif label.startswith("status/"):
            parsed["status"] = label.replace("status/", "")
        elif label.startswith("release/"):
            parsed["release"] = label.replace("release/", "")

    return parsed


def infer_epic_from_content(title: str, epic_mapping: dict):
    """Infer epic from title content if no epic label exists."""
    title_lower = title.lower()

    if "blog" in title_lower or "content" in title_lower:
        return epic_mapping.get("EP-00001")  # Blog Content
    elif "comment" in title_lower or "gdpr" in title_lower:
        return epic_mapping.get("EP-00002")  # Comments/GDPR
    elif "privacy" in title_lower:
        return epic_mapping.get("EP-00003")  # Privacy
    elif "workflow" in title_lower or "action" in title_lower:
        return epic_mapping.get("EP-00004")  # Workflow
    elif (
        "rtm" in title_lower or "matrix" in title_lower or "traceability" in title_lower
    ):
        return epic_mapping.get("EP-00005")  # RTM
    elif "project" in title_lower or "management" in title_lower:
        return epic_mapping.get("EP-00006")  # Project Management
    elif "test" in title_lower or "report" in title_lower:
        return epic_mapping.get("EP-00007")  # Testing
    else:
        # Default to EP-00005 (RTM) for unmapped items
        return epic_mapping.get("EP-00005")


def sync_user_stories_comprehensive(session, issues, epic_mapping, dry_run=True):
    """Comprehensive user story sync with all metadata."""
    print("\n=== Comprehensive User Story Sync ===")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")

    user_story_pattern = r"US-\d{5}"
    processed_ids = set()
    created_count = 0
    updated_count = 0
    skipped_count = 0

    for issue in issues:
        title = issue.get("title", "")
        us_id = extract_id_from_title(title, user_story_pattern)

        if not us_id:
            continue

        # Skip duplicates within this session
        if us_id in processed_ids:
            skipped_count += 1
            print(f"  {us_id}: Skipping duplicate")
            continue

        processed_ids.add(us_id)

        # Parse GitHub labels
        parsed_labels = parse_github_labels(issue.get("labels", []))

        # Determine epic
        epic_id = None
        if parsed_labels["epic"]:
            epic_id = epic_mapping.get(parsed_labels["epic"])
        if not epic_id:
            epic_id = infer_epic_from_content(title, epic_mapping)

        # Check if user story exists
        existing = (
            session.query(UserStory).filter(UserStory.user_story_id == us_id).first()
        )

        epic_name = next(
            (k for k, v in epic_mapping.items() if v == epic_id), "Unknown"
        )
        component_info = (
            f", component: {parsed_labels['component']}"
            if parsed_labels["component"]
            else ""
        )

        if existing:
            # Update existing user story
            needs_update = False
            updates = []

            if existing.epic_id != epic_id:
                updates.append(f"epic: {existing.epic_id} -> {epic_id}")
                needs_update = True
                if not dry_run:
                    existing.epic_id = epic_id

            if (
                parsed_labels["component"]
                and existing.component != parsed_labels["component"]
            ):
                updates.append(
                    f"component: {existing.component} -> {parsed_labels['component']}"
                )
                needs_update = True
                if not dry_run:
                    existing.component = parsed_labels["component"]

            if (
                parsed_labels["priority"]
                and existing.priority != parsed_labels["priority"]
            ):
                updates.append(
                    f"priority: {existing.priority} -> {parsed_labels['priority']}"
                )
                needs_update = True
                if not dry_run:
                    existing.priority = parsed_labels["priority"]

            if needs_update:
                print(
                    f"  {us_id}: UPDATE"
                    f"-> {epic_name}{component_info} ({', '.join(updates)})"
                )
                updated_count += 1
            else:
                print(f"  {us_id}: No changes needed -> {epic_name}{component_info}")
        else:
            # Create new user story
            print(f"  {us_id}: CREATE -> {epic_name}{component_info}")

            if not dry_run:
                user_story = UserStory(
                    user_story_id=us_id,
                    title=title,
                    description=issue.get("body", ""),
                    github_issue_number=issue["number"],
                    epic_id=epic_id,
                    component=parsed_labels["component"],
                    priority=parsed_labels["priority"] or "medium",
                    status="planned",
                )
                session.add(user_story)
            created_count += 1

    print("\nUser Stories Summary:")
    print(f"  Processed unique IDs: {len(processed_ids)}")
    print(f"  Created: {created_count}")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped duplicates: {skipped_count}")

    return created_count + updated_count


def sync_defects_comprehensive(session, issues, epic_mapping, dry_run=True):
    """Comprehensive defect sync with all metadata."""
    print("\n=== Comprehensive Defect Sync ===")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")

    defect_pattern = r"DEF-\d{5}"
    processed_ids = set()
    created_count = 0
    updated_count = 0
    skipped_count = 0

    for issue in issues:
        title = issue.get("title", "")
        def_id = extract_id_from_title(title, defect_pattern)

        if not def_id:
            continue

        # Skip duplicates
        if def_id in processed_ids:
            skipped_count += 1
            print(f"  {def_id}: Skipping duplicate")
            continue

        processed_ids.add(def_id)

        # Parse GitHub labels
        parsed_labels = parse_github_labels(issue.get("labels", []))

        # Determine epic
        epic_id = None
        if parsed_labels["epic"]:
            epic_id = epic_mapping.get(parsed_labels["epic"])
        if not epic_id:
            epic_id = infer_epic_from_content(title, epic_mapping)

        # Check if defect exists
        existing = session.query(Defect).filter(Defect.defect_id == def_id).first()

        epic_name = next(
            (k for k, v in epic_mapping.items() if v == epic_id), "Unknown"
        )
        component_info = (
            f", component: {parsed_labels['component']}"
            if parsed_labels["component"]
            else ""
        )

        if existing:
            # Update existing defect
            needs_update = False
            updates = []

            if existing.epic_id != epic_id:
                updates.append(f"epic: {existing.epic_id} -> {epic_id}")
                needs_update = True
                if not dry_run:
                    existing.epic_id = epic_id

            if (
                parsed_labels["component"]
                and existing.component != parsed_labels["component"]
            ):
                updates.append(
                    f"component: {existing.component} -> {parsed_labels['component']}"
                )
                needs_update = True
                if not dry_run:
                    existing.component = parsed_labels["component"]

            if needs_update:
                print(
                    f"  {def_id}: UPDATE"
                    f"-> {epic_name}{component_info} ({', '.join(updates)})"
                )
                updated_count += 1
            else:
                print(f"  {def_id}:No changes needed -> {epic_name}{component_info}")
        else:
            # Create new defect
            print(f"  {def_id}: CREATE -> {epic_name}{component_info}")

            if not dry_run:
                defect = Defect(
                    defect_id=def_id,
                    title=title,
                    description=issue.get("body", ""),
                    github_issue_number=issue["number"],
                    epic_id=epic_id,
                    component=parsed_labels["component"],
                    status="open" if issue["state"] == "open" else "closed",
                    priority=parsed_labels["priority"] or "medium",
                )
                session.add(defect)
            created_count += 1

    print("\nDefects Summary:")
    print(f"  Processed unique IDs: {len(processed_ids)}")
    print(f"  Created: {created_count}")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped duplicates: {skipped_count}")

    return created_count + updated_count


def comprehensive_github_sync(dry_run=True, entity_types=["all"]):
    """Main comprehensive sync function."""
    session = SessionLocal()

    try:
        issues = fetch_github_issues()
        if not issues:
            return

        # Get epic mapping
        epics = session.query(Epic).all()
        epic_mapping = {epic.epic_id: epic.id for epic in epics}

        print("\n=== Comprehensive GitHub Sync ===")
        print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")
        print(f"Entity Types: {', '.join(entity_types)}")

        total_changes = 0

        # Sync user stories
        if "all" in entity_types or "user-stories" in entity_types:
            changes = sync_user_stories_comprehensive(
                session, issues, epic_mapping, dry_run
            )
            total_changes += changes

        # Sync defects
        if "all" in entity_types or "defects" in entity_types:
            changes = sync_defects_comprehensive(session, issues, epic_mapping, dry_run)
            total_changes += changes

        # Commit changes
        if not dry_run and total_changes > 0:
            session.commit()
            print(f"\nCommitted {total_changes} changes to database")
        elif dry_run:
            print(f"\nDRY RUN - Would make {total_changes} changes")
        else:
            print("\nNo changes needed")

    except Exception as e:
        print(f"Error during sync: {e}")
        if not dry_run:
            session.rollback()
    finally:
        session.close()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Comprehensive GitHub sync tool")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Only show what would be synced (default: True)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually execute the sync (overrides --dry-run)",
    )
    parser.add_argument(
        "--entity-type",
        action="append",
        choices=["user-stories", "defects", "all"],
        default=["all"],
        help="Which entity types to sync (default: all)",
    )

    args = parser.parse_args()

    # If --execute is specified, turn off dry run
    dry_run = args.dry_run and not args.execute

    comprehensive_github_sync(dry_run, args.entity_type)


if __name__ == "__main__":
    main()
