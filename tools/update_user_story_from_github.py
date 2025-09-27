#!/usr/bin/env python3
"""
Update specific user story from GitHub

Updates a user story with current GitHub labels and epic information.
"""

import requests
import os
import sys

sys.path.append("src")

from be.database import SessionLocal
from be.models.traceability.epic import Epic
from be.models.traceability.user_story import UserStory


def fetch_github_issue(issue_number: int):
    """Fetch a specific GitHub issue."""
    github_token = os.getenv("GITHUB_TOKEN")
    headers = {}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    url = f"https://api.github.com/repos/QHuuT/gonogo/issues/{issue_number}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch issue #{issue_number}: {response.status_code}")
        return None

    return response.json()


def update_user_story_epic(user_story_id: str, dry_run: bool = True):
    """Update user story epic from GitHub labels."""
    session = SessionLocal()

    try:
        # Find user story
        user_story = (
            session.query(UserStory)
            .filter(UserStory.user_story_id == user_story_id)
            .first()
        )

        if not user_story:
            print(f"User story {user_story_id} not found in database")
            return

        print(f"Current: {user_story_id} -> Epic ID: {user_story.epic_id}")

        # Fetch GitHub issue
        issue = fetch_github_issue(user_story.github_issue_number)
        if not issue:
            return

        # Get epic mapping
        epics = session.query(Epic).all()
        epic_mapping = {epic.epic_id: epic.id for epic in epics}

        # Extract epic from labels
        labels = [label["name"] for label in issue.get("labels", [])]
        print(f"GitHub labels: {labels}")

        epic_label_mapping = {
            "epic/blog-content": "EP-00001",
            "epic/comment-system": "EP-00002",
            "epic/privacy-consent": "EP-00003",
            "epic/github-workflow": "EP-00004",
            "epic/rtm": "EP-00005",
            "epic/github-project": "EP-00006",
            "epic/test-reporting": "EP-00007",
        }

        new_epic_id = None
        for label in labels:
            if label in epic_label_mapping:
                new_epic_id = epic_mapping.get(epic_label_mapping[label])
                print(
                    f"Found epic label: {label} -> {epic_label_mapping[label]} -> "
                    f"Epic ID: {new_epic_id}"
                )
                break

        if new_epic_id and new_epic_id != user_story.epic_id:
            print(f"Updating epic: {user_story.epic_id} -> {new_epic_id}")

            if not dry_run:
                user_story.epic_id = new_epic_id
                session.commit()
                print(f"✅ Updated {user_story_id} epic successfully")
            else:
                print("🔍 DRY RUN - Would update epic")
        elif new_epic_id == user_story.epic_id:
            print(f"✅ Epic already correct: {new_epic_id}")
        else:
            print("⚠️ No epic label found in GitHub")

    except Exception as e:
        print(f"Error: {e}")
        if not dry_run:
            session.rollback()
    finally:
        session.close()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Update user story from GitHub")
    parser.add_argument(
        "--user-story", required=True, help="User story ID (e.g., US-00013)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Only show what would be updated (default: True)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually execute the update (overrides --dry-run)",
    )

    args = parser.parse_args()

    # If --execute is specified, turn off dry run
    dry_run = args.dry_run and not args.execute

    print("=== Update User Story from GitHub ===")
    print(f"User Story: {args.user_story}")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")

    update_user_story_epic(args.user_story, dry_run)


if __name__ == "__main__":
    main()
