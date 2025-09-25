#!/usr/bin/env python3
"""
Restore Component Assignments from GitHub Labels

This script reads GitHub issue labels and updates user story component assignments.
"""

import sys
from pathlib import Path
import subprocess
import json

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from be.database import get_db_session
from be.models.traceability import UserStory


def get_github_issue_data(issue_number):
    """Get GitHub issue data using gh CLI."""
    try:
        result = subprocess.run(
            ['gh', 'issue', 'view', str(issue_number), '--json', 'labels,title,body,state'],
            capture_output=True, text=True, encoding='utf-8'
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"Failed to get data for issue {issue_number}: {result.stderr}")
            return None
    except Exception as e:
        print(f"Error getting issue {issue_number}: {e}")
        return None


def extract_component_from_labels(labels):
    """Extract component from GitHub labels."""
    for label in labels:
        label_name = label.get("name", "")
        if label_name.startswith("component/"):
            return label_name.replace("component/", "")
    return None


def main():
    """Restore component assignments for all user stories."""
    print("Restoring component assignments from GitHub labels...")

    with get_db_session() as session:
        user_stories = session.query(UserStory).all()
        updated_count = 0
        failed_count = 0

        for i, us in enumerate(user_stories, 1):
            print(f"Processing {i}/{len(user_stories)}: {us.user_story_id} (Issue #{us.github_issue_number})")

            github_data = get_github_issue_data(us.github_issue_number)
            if github_data:
                old_component = us.component
                component = extract_component_from_labels(github_data.get('labels', []))

                if component:
                    us.component = component
                    if old_component != component:
                        print(f"  Updated: {old_component or 'None'} -> {component}")
                        updated_count += 1
                    else:
                        print(f"  Already has component: {component}")
                else:
                    print(f"  No component label found")
            else:
                print(f"  Failed to get GitHub data")
                failed_count += 1

        print(f"\nCommitting changes...")
        session.commit()

        print(f"\n=== RESULTS ===")
        print(f"Updated: {updated_count} user stories")
        print(f"Failed: {failed_count} user stories")
        print(f"Total processed: {len(user_stories)} user stories")


if __name__ == "__main__":
    main()