#!/usr/bin/env python3
"""
Import GitHub User Stories using Title-Based ID Extraction

Extracts user story IDs from GitHub issue titles only (not body text)
to avoid duplicate ID issues from cross-references.
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


def import_user_stories_from_titles(dry_run: bool = True):
    """Import user stories using title-based ID extraction."""
    session = SessionLocal()

    try:
        issues = fetch_github_issues()
        if not issues:
            return

        # Get epic mapping
        epics = session.query(Epic).all()
        epic_mapping = {epic.epic_id: epic.id for epic in epics}

        print("\n=== User Story Import (Title-Based) ===")
        print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")

        user_stories_created = []
        user_stories_skipped = []
        user_story_pattern = r"US-\d{5}"
        processed_ids = set()  # Track IDs we've already processed

        for issue in issues:
            title = issue.get("title", "")

            # Extract user story ID from title only
            us_id = extract_id_from_title(title, user_story_pattern)

            if us_id:
                # Skip if we've already processed this ID in this session
                if us_id in processed_ids:
                    user_stories_skipped.append(us_id)
                    print(f"  {us_id}: Skipping duplicate")
                    continue

                # Check if this user story already exists in database
                existing = (
                    session.query(UserStory)
                    .filter(UserStory.user_story_id == us_id)
                    .first()
                )

                if existing:
                    print(f"  {us_id}:Already exists (#{existing.github_issue_number})")
                    processed_ids.add(us_id)
                    continue

                # Mark this ID as processed
                processed_ids.add(us_id)

                # Try to determine epic from labels
                epic_id = None
                labels = [label["name"] for label in issue.get("labels", [])]

                # Simple epic label mapping
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
                        epic_id = epic_mapping.get(epic_label_mapping[label])
                        break

                # If no epic found from labels, try to infer from issue content/title
                if not epic_id:
                    # Default mapping based on keywords
                    title_lower = title.lower()
                    if "blog" in title_lower or "content" in title_lower:
                        epic_id = epic_mapping.get("EP-00001")  # Blog Content
                    elif "comment" in title_lower or "gdpr" in title_lower:
                        epic_id = epic_mapping.get("EP-00002")  # Comments/GDPR
                    elif "privacy" in title_lower:
                        epic_id = epic_mapping.get("EP-00003")  # Privacy
                    elif "workflow" in title_lower or "action" in title_lower:
                        epic_id = epic_mapping.get("EP-00004")  # Workflow
                    elif (
                        "rtm" in title_lower
                        or "matrix" in title_lower
                        or "traceability" in title_lower
                    ):
                        epic_id = epic_mapping.get("EP-00005")  # RTM
                    elif "project" in title_lower or "management" in title_lower:
                        epic_id = epic_mapping.get("EP-00006")  # Project Management
                    elif "test" in title_lower or "report" in title_lower:
                        epic_id = epic_mapping.get("EP-00007")  # Testing
                    else:
                        # Default to EP-00005 (RTM) for unmapped user stories
                        epic_id = epic_mapping.get("EP-00005")

                epic_info = ""
                if epic_id:
                    epic = session.query(Epic).filter(Epic.id == epic_id).first()
                    epic_info = f" -> {epic.epic_id}" if epic else " -> Unknown Epic"

                print(f"  {us_id}: {title[:50]}...{epic_info}")

                if not dry_run:
                    # Create user story
                    user_story = UserStory(
                        user_story_id=us_id,
                        title=title,
                        description=issue.get("body", ""),
                        github_issue_number=issue["number"],
                        epic_id=epic_id,
                        status="planned",  # Default status
                    )
                    session.add(user_story)
                    user_stories_created.append(us_id)

        print(f"\nProcessed {len(processed_ids)} unique user story IDs")
        print(f"Skipped {len(user_stories_skipped)} duplicates")

        if not dry_run:
            session.commit()
            print(f"Created {len(user_stories_created)} user stories")
        else:
            print("Would create user stories (dry run)")

    except Exception as e:
        print(f"Error: {e}")
        if not dry_run:
            session.rollback()
    finally:
        session.close()


def import_defects_from_titles(dry_run: bool = True):
    """Import defects using title-based ID extraction."""
    session = SessionLocal()

    try:
        issues = fetch_github_issues()
        if not issues:
            return

        print("\n=== Defect Import (Title-Based) ===")
        print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")

        defects_created = []
        defect_pattern = r"DEF-\d{5}"

        for issue in issues:
            title = issue.get("title", "")

            # Extract defect ID from title only
            def_id = extract_id_from_title(title, defect_pattern)

            if def_id:
                # Check if this defect already exists
                existing = (
                    session.query(Defect).filter(Defect.defect_id == def_id).first()
                )

                if existing:
                    print(
                        f"  {def_id}:Already exists (#{existing.github_issue_number})"
                    )
                    continue

                print(f"  {def_id}: {title[:50]}...")

                if not dry_run:
                    # Create defect
                    defect = Defect(
                        defect_id=def_id,
                        title=title,
                        description=issue.get("body", ""),
                        github_issue_number=issue["number"],
                        status="open" if issue["state"] == "open" else "closed",
                        priority="medium",  # Default priority
                    )
                    session.add(defect)
                    defects_created.append(def_id)

        if not dry_run:
            session.commit()
            print(f"\nCreated {len(defects_created)} defects")
        else:
            print("\nWould create defects (dry run)")

    except Exception as e:
        print(f"Error: {e}")
        if not dry_run:
            session.rollback()
    finally:
        session.close()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Import GitHub entities using title-based ID extraction"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Only analyze what would be imported (default: True)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually execute the import (overrides --dry-run)",
    )
    parser.add_argument(
        "--entity-type",
        choices=["user-stories", "defects", "all"],
        default="all",
        help="Which entity types to import (default: all)",
    )

    args = parser.parse_args()

    # If --execute is specified, turn off dry run
    dry_run = args.dry_run and not args.execute

    print("=== GitHub Title-Based Import ===")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")
    print(f"Entity Types: {args.entity_type}")

    if args.entity_type in ["user-stories", "all"]:
        import_user_stories_from_titles(dry_run)

    if args.entity_type in ["defects", "all"]:
        import_defects_from_titles(dry_run)

    print("\n=== Import Complete ===")


if __name__ == "__main__":
    main()
