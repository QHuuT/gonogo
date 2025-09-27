#!/usr/bin/env python3
"""
Real GitHub Data Import Tool

Imports actual GitHub issues into the RTM database to replace fictional sample data.
Pulls all real user stories, epics, and defects from the GitHub repository.

Related Issue: US-00061 - Enhanced RTM HTML report with improved traceability
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from be.database import get_db_session
    from be.models.traceability import Defect, Epic, Test, UserStory
    from shared.testing.database_integration import TestDiscovery

    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Error: Database modules not available: {e}")
    DATABASE_AVAILABLE = False


class GitHubDataImporter:
    """Import real GitHub data into RTM database."""

    def __init__(self):
        self.db_session = None
        self.github_issues = []

    def initialize_database(self) -> bool:
        """Initialize database connection."""
        if not DATABASE_AVAILABLE:
            print("[ERROR] Database modules not available")
            return False

        try:
            self.db_session = get_db_session()
            print("[OK] Database connection established")
            return True
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False

    def fetch_github_issues(self) -> bool:
        """Fetch all GitHub issues using gh CLI."""
        try:
            print("Fetching GitHub issues...")

            # Get all issues (open and closed)
            cmd = [
                "gh",
                "issue",
                "list",
                "--limit",
                "100",
                "--state",
                "all",
                "--json",
                "number,title,body,state,labels,assignees,createdAt,updatedAt",
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8", check=True
            )

            if not result.stdout:
                print("[ERROR] No data returned from GitHub CLI")
                return False

            self.github_issues = json.loads(result.stdout)

            print(f"[OK] Fetched {len(self.github_issues)} GitHub issues")
            return True

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to fetch GitHub issues: {e}")
            print("Make sure 'gh' CLI is installed and authenticated")
            return False
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse GitHub response: {e}")
            return False

    def parse_issue_type(self, labels: List[Dict]) -> str:
        """Determine issue type from labels."""
        label_names = [label.get("name", "").lower() for label in labels]

        # Check for exact label matches to avoid false positives
        if "epic" in label_names:
            return "epic"
        elif any("user-story" in label for label in label_names):
            return "user-story"
        elif any("defect" in label or "bug" in label for label in label_names):
            return "defect"
        else:
            return "unknown"

    def extract_epic_id(self, title: str, body: str) -> Optional[str]:
        """Extract epic ID from title or body."""
        import re

        # Look for EP-XXXXX pattern in title (handle various formats)
        epic_patterns = [
            r"EP-(\d{5})",  # EP-00001
            r"EP-(\d{4})",  # EP-0001
            r"EP-(\d{3})",  # EP-001
        ]

        for pattern in epic_patterns:
            epic_match = re.search(pattern, title)
            if epic_match:
                # Pad to 5 digits
                epic_num = epic_match.group(1).zfill(5)
                return f"EP-{epic_num}"

        # Look in body
        if body:
            for pattern in epic_patterns:
                epic_match = re.search(pattern, body)
                if epic_match:
                    epic_num = epic_match.group(1).zfill(5)
                    return f"EP-{epic_num}"

        return None

    def extract_user_story_id(self, title: str, body: str) -> Optional[str]:
        """Extract user story ID from title or body."""
        import re

        # Look for US-XXXXX pattern in title
        us_match = re.search(r"US-(\d{5})", title)
        if us_match:
            return f"US-{us_match.group(1)}"

        return None

    def extract_defect_id(self, title: str, body: str) -> Optional[str]:
        """Extract defect ID from title or body."""
        import re

        # Look for DEF-XXXXX pattern in title
        def_match = re.search(r"DEF-(\d{5})", title)
        if def_match:
            return f"DEF-{def_match.group(1)}"

        return None

    def get_priority_from_labels(self, labels: List[Dict]) -> str:
        """Extract priority from labels."""
        label_names = [label.get("name", "").lower() for label in labels]

        if any("priority/critical" in label for label in label_names):
            return "critical"
        elif any("priority/high" in label for label in label_names):
            return "high"
        elif any("priority/medium" in label for label in label_names):
            return "medium"
        elif any("priority/low" in label for label in label_names):
            return "low"
        else:
            return "medium"  # default

    def get_status_from_state_and_labels(self, state: str, labels: List[Dict]) -> str:
        """Determine status from GitHub state and labels."""
        label_names = [label.get("name", "").lower() for label in labels]

        if state == "closed":
            if any("status/done" in label for label in label_names):
                return "completed"
            else:
                return "completed"  # assume closed = completed
        else:  # open
            if any("status/in-progress" in label for label in label_names):
                return "in_progress"
            elif any("status/blocked" in label for label in label_names):
                return "blocked"
            elif any("status/ready" in label for label in label_names):
                return "planned"
            else:
                return "planned"  # default for open issues

    def extract_story_points(self, body: str) -> int:
        """Extract story points from issue body."""
        import re

        if not body:
            return 3  # default

        # Look for story points pattern
        sp_patterns = [
            r"story\s*points?\s*[:\-]?\s*(\d+)",
            r"points?\s*[:\-]?\s*(\d+)",
            r"sp\s*[:\-]?\s*(\d+)",
        ]

        for pattern in sp_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return 3  # default

    def clear_existing_data(self):
        """Clear existing sample data from database."""
        print("Clearing existing sample data...")

        # Clear tables only if they exist, handle missing tables gracefully
        tables_to_clear = [
            (Defect, "defects"),
            (Test, "tests"),
            (UserStory, "user_stories"),
            (Epic, "epics")
        ]

        for model_class, table_name in tables_to_clear:
            try:
                count = self.db_session.query(model_class).count()
                if count > 0:
                    self.db_session.query(model_class).delete()
                    print(f"  Cleared {count} records from {table_name}")
                else:
                    print(f"  {table_name} table is empty")
            except Exception as e:
                print(f"  {table_name} table doesn't exist or error: {e}")

        self.db_session.commit()
        print("[OK] Existing data cleared")

    def import_epics(self) -> Dict[str, int]:
        """Import epics from GitHub issues."""
        epic_issues = [
            issue
            for issue in self.github_issues
            if self.parse_issue_type(issue.get("labels", [])) == "epic"
        ]

        print(f"Importing {len(epic_issues)} epics...")
        epic_mapping = {}  # epic_id -> database id

        for issue in epic_issues:
            epic_id = self.extract_epic_id(issue["title"], issue.get("body", ""))
            if not epic_id:
                print(f"[WARNING] Could not extract epic ID from: {issue['title']}")
                continue

            # Check if epic already exists in database
            existing_epic = \
                self.db_session.query(Epic).filter(Epic.epic_id == epic_id).first()

            # Clean epic title by removing epic ID prefix (handle both ": " and " - " separators)
            cleaned_title = issue["title"]
            for separator in [f"{epic_id}: ", f"{epic_id} - "]:
                if cleaned_title.startswith(separator):
                    cleaned_title = cleaned_title.replace(separator, "", 1)
                    break

            if existing_epic:
                # Update existing epic
                existing_epic.title = cleaned_title
                existing_epic.description = \
                    issue.get("body", "")[:500] if issue.get("body") else ""
                existing_epic.priority = \
                    self.get_priority_from_labels(issue.get("labels", []))
                existing_epic.status = self.get_status_from_state_and_labels(
                    issue["state"], issue.get("labels", [])
                )
                existing_epic.github_issue_number = issue["number"]
                existing_epic.updated_at = datetime.fromisoformat(
                    issue["updatedAt"].replace("Z", "+00:00")
                )
                epic_mapping[epic_id] = existing_epic.id
                print(f"  {epic_id}: {existing_epic.title} (UPDATED)")
            else:
                # Create new epic
                epic = Epic(
                    epic_id=epic_id,
                    title=cleaned_title,
                    description=issue.get("body", "")[:500] if issue.get("body") else "",
                    business_value="Imported from GitHub",
                    priority=self.get_priority_from_labels(issue.get("labels", [])),
                    status=self.get_status_from_state_and_labels(
                        issue["state"], issue.get("labels", [])
                    ),
                    github_issue_number=issue["number"],
                    created_at=datetime.fromisoformat(
                        issue["createdAt"].replace("Z", "+00:00")
                    ),
                    updated_at=datetime.fromisoformat(
                        issue["updatedAt"].replace("Z", "+00:00")
                    ),
                )

                self.db_session.add(epic)
                self.db_session.flush()  # Get the ID
                epic_mapping[epic_id] = epic.id
                print(f"  {epic_id}: {epic.title} (NEW)")

        self.db_session.commit()
        print(f"[OK] Imported {len(epic_mapping)} epics")
        return epic_mapping

    def import_user_stories(self, epic_mapping: Dict[str, int]):
        """Import user stories from GitHub issues."""
        us_issues = [
            issue
            for issue in self.github_issues
            if self.parse_issue_type(issue.get("labels", [])) == "user-story"
        ]

        print(f"Importing {len(us_issues)} user stories...")

        processed_us_ids = set()  # Track processed user story IDs

        for issue in us_issues:
            us_id = self.extract_user_story_id(issue["title"], issue.get("body", ""))
            if not us_id:
                print(
                    f"[WARNING] Could not extract user story ID from: {issue['title']}"
                )
                continue

            # Skip if we've already processed this user story ID in this run
            if us_id in processed_us_ids:
                print(
                    f"[WARNING] Duplicate user"
                    f"story {us_id} in GitHub issues, skipping second occurrence"
                )
                continue
            processed_us_ids.add(us_id)

            # Try to find parent epic from body
            body = issue.get("body", "")
            epic_id = None
            epic_db_id = None

            # Look for parent epic reference
            import re

            epic_match = re.search(r"Parent Epic.*?EP-(\d{5})", body, re.IGNORECASE)
            if epic_match:
                epic_id = f"EP-{epic_match.group(1)}"
                epic_db_id = epic_mapping.get(epic_id)

            # If no epic found, assign to a default epic or skip
            if not epic_db_id:
                # Try to assign based on user story number ranges
                us_number = int(us_id.split("-")[1])
                if us_number <= 10:
                    epic_db_id = epic_mapping.get("EP-00001")  # Blog
                elif us_number <= 20:
                    epic_db_id = epic_mapping.get("EP-00002")  # Comments
                elif us_number <= 40:
                    epic_db_id = epic_mapping.get("EP-00003")  # Privacy
                elif us_number <= 50:
                    epic_db_id = epic_mapping.get("EP-00004")  # GitHub
                elif us_number <= 60:
                    epic_db_id = epic_mapping.get("EP-00005")  # RTM
                elif us_number <= 70:
                    epic_db_id = epic_mapping.get("EP-00006")  # Testing
                else:
                    epic_db_id = epic_mapping.get("EP-00007")  # Archive

                if not epic_db_id and epic_mapping:
                    epic_db_id = list(epic_mapping.values())[
                        0
                    ]  # fallback to first epic

            if not epic_db_id:
                print(f"[WARNING] No epic found for {us_id}, skipping")
                continue

            # Check if user story already exists
            existing_us = \
                self.db_session.query(UserStory).filter(UserStory.user_story_id == us_id).first()

            if existing_us:
                # Update existing user story
                existing_us.epic_id = epic_db_id
                existing_us.github_issue_number = issue["number"]
                existing_us.github_issue_state = issue["state"]
                existing_us.github_labels = str(issue.get("labels", []))
                existing_us.title = issue["title"].replace(f"{us_id}: ", "")
                existing_us.description = \
                    issue.get("body", "")[:500] if issue.get("body") else ""
                existing_us.story_points = \
                    self.extract_story_points(issue.get("body", ""))
                existing_us.priority = \
                    self.get_priority_from_labels(issue.get("labels", []))
                existing_us.implementation_status = self.get_status_from_state_and_labels(
                    issue["state"], issue.get("labels", [])
                )
                existing_us.updated_at = datetime.fromisoformat(
                    issue["updatedAt"].replace("Z", "+00:00")
                )
                print(f"  {us_id}: {existing_us.title} (UPDATED)")
            else:
                # Create new user story
                user_story = UserStory(
                    user_story_id=us_id,
                    epic_id=epic_db_id,
                    github_issue_number=issue["number"],
                    github_issue_state=issue["state"],
                    github_labels=str(issue.get("labels", [])),
                    title=issue["title"].replace(f"{us_id}: ", ""),
                    description=issue.get("body", "")[:500] if issue.get("body") else "",
                    story_points=self.extract_story_points(issue.get("body", "")),
                    priority=self.get_priority_from_labels(issue.get("labels", [])),
                    implementation_status=self.get_status_from_state_and_labels(
                        issue["state"], issue.get("labels", [])
                    ),
                    created_at=datetime.fromisoformat(
                        issue["createdAt"].replace("Z", "+00:00")
                    ),
                    updated_at=datetime.fromisoformat(
                        issue["updatedAt"].replace("Z", "+00:00")
                    ),
                )

                self.db_session.add(user_story)
                print(f"  {us_id}: {user_story.title} (NEW)")

        self.db_session.commit()
        print(f"[OK] Imported user stories")

    def import_defects(self, epic_mapping: Dict[str, int]):
        """Import defects from GitHub issues."""
        defect_issues = [
            issue
            for issue in self.github_issues
            if self.parse_issue_type(issue.get("labels", [])) == "defect"
        ]

        if not defect_issues:
            print("No defects found in GitHub issues")
            return

        print(f"Importing {len(defect_issues)} defects...")
        processed_defects = set()  # Track processed defect IDs to avoid duplicates

        for issue in defect_issues:
            defect_id = self.extract_defect_id(issue["title"], issue.get("body", ""))
            if not defect_id:
                print(
                    f"[WARNING] Could"
                    f"not extract defect ID from: {issue['title']}"
                )
                continue

            # Skip if defect already processed
            if defect_id in processed_defects:
                print(f"[WARNING] Duplicate defect {defect_id}, skipping")
                continue

            # Assign to first epic as fallback
            epic_db_id = list(epic_mapping.values())[0] if epic_mapping else None
            if not epic_db_id:
                continue

            defect = Defect(
                defect_id=defect_id,
                github_issue_number=issue["number"],
                title=issue["title"].replace(f"{defect_id}: ", ""),
                description=issue.get("body", "")[:500] if issue.get("body") else "",
                severity=self.get_priority_from_labels(issue.get("labels", [])),
                priority=self.get_priority_from_labels(issue.get("labels", [])),
                status=self.get_status_from_state_and_labels(
                    issue["state"], issue.get("labels", [])
                ),
                epic_id=epic_db_id,
                is_security_issue=any(
                    "security" in label.get("name", "").lower()
                    for label in issue.get("labels", [])
                ),
                created_at=datetime.fromisoformat(
                    issue["createdAt"].replace("Z", "+00:00")
                ),
                updated_at=datetime.fromisoformat(
                    issue["updatedAt"].replace("Z", "+00:00")
                ),
            )

            self.db_session.add(defect)
            processed_defects.add(defect_id)  # Mark as processed
            print(f"  {defect_id}: {defect.title}")

        self.db_session.commit()
        print(f"[OK] Imported defects")

    def import_tests(self, epic_mapping: Dict[str, int]):
        """Import tests from codebase and link to epics."""
        print("Discovering and importing tests from codebase...")

        try:
            test_discovery = TestDiscovery()
            discovered_tests = test_discovery.discover_tests()

            if not discovered_tests:
                print("No tests discovered in codebase")
                return

            print(f"Found {len(discovered_tests)} tests to import...")
            imported_count = 0

            for test_info in discovered_tests:
                # Extract epic ID from test metadata if available
                epic_references = test_info.get("epic_references", [])
                epic_db_id = None

                # Try to find epic based on references in test
                if epic_references:
                    for epic_ref in epic_references:
                        if epic_ref in epic_mapping:
                            epic_db_id = epic_mapping[epic_ref]
                            break

                # Fallback: assign to first epic if no specific mapping found
                if not epic_db_id and epic_mapping:
                    epic_db_id = list(epic_mapping.values())[0]

                if not epic_db_id:
                    continue

                # Create test record
                test = Test(
                    test_type=test_info["test_type"],
                    test_file_path=test_info["test_file_path"],
                    test_function_name=test_info.get("test_function_name"),
                    bdd_feature_file=test_info.get("bdd_feature_file"),
                    bdd_scenario_name=test_info.get("bdd_scenario_name"),
                    epic_id=epic_db_id,
                    title=test_info.get(
                        "title", f"Test: {test_info['test_file_path']}"
                    ),
                    description=f"{test_info['test_type']} test: {test_info.get('test_function_name', 'unknown')}",
                    last_execution_status="not_run",
                    test_priority="medium",
                    is_automated=True,
                )

                self.db_session.add(test)
                imported_count += 1
                print(
                    f"  {test_info['test_type']}: {test_info['test_file_path']} -> {test_info.get('test_function_name', 'unknown')}"
                )

            self.db_session.commit()
            print(f"[OK] Imported {imported_count} tests")

        except Exception as e:
            print(f"[ERROR] Test import failed: {e}")
            self.db_session.rollback()

    def import_real_data(self):
        """Import all real GitHub data."""
        if not self.initialize_database():
            return False

        if not self.fetch_github_issues():
            return False

        try:
            # PRESERVE existing data - only update/add new issues
            print("Preserving existing data, updating only changed issues...")

            # Import in order: epics first, then user stories, defects, then tests
            epic_mapping = self.import_epics()
            self.import_user_stories(epic_mapping)
            self.import_defects(epic_mapping)
            self.import_tests(epic_mapping)

            # Show summary
            epic_count = self.db_session.query(Epic).count()
            us_count = self.db_session.query(UserStory).count()
            defect_count = self.db_session.query(Defect).count()
            test_count = self.db_session.query(Test).count()

            print(f"\n[OK] Real GitHub data import completed!")
            print(f"  - Epics: {epic_count}")
            print(f"  - User Stories: {us_count}")
            print(f"  - Defects: {defect_count}")
            print(f"  - Tests: {test_count}")
            print(f"  - Total Issues Processed: {len(self.github_issues)}")

            return True

        except Exception as e:
            print(f"[ERROR] Import failed: {e}")
            self.db_session.rollback()
            return False
        finally:
            if self.db_session:
                self.db_session.close()


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Import real GitHub data into RTM database"
    )
    parser.add_argument(
        "--import",
        action="store_true",
        dest="do_import",
        help="Import real GitHub issues into database",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without making changes",
    )

    args = parser.parse_args()

    if args.do_import:
        importer = GitHubDataImporter()
        success = importer.import_real_data()
        if success:
            print("\n[OK] Ready to generate REAL RTM reports!")
            print("Run: python tools/dynamic_rtm_demo.py --html")
        else:
            print("\n[ERROR] Import failed")
            return 1
    elif args.dry_run:
        importer = GitHubDataImporter()
        if importer.fetch_github_issues():
            print(f"Would import {len(importer.github_issues)} GitHub issues")
            for issue in importer.github_issues[:5]:  # Show first 5
                issue_type = importer.parse_issue_type(issue.get("labels", []))
                print(f"  #{issue['number']}: {issue['title']} ({issue_type})")
            if len(importer.github_issues) > 5:
                print(f"  ... and {len(importer.github_issues) - 5} more")
    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
