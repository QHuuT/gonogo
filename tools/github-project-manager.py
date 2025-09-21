#!/usr/bin/env python3
"""
GitHub Project Manager

Automation tool for managing GitHub project integration with issues.
Handles project association, priority mapping, and hierarchical relationships.

Related to: Enhanced GitHub-first workflow protocol
Epic: EP-00005 (RTM Automation)

Usage:
    python tools/github-project-manager.py --associate-issue 12
    python tools/github-project-manager.py --update-hierarchy US-00018 EP-00005
    python tools/github-project-manager.py --sync-priorities
    python tools/github-project-manager.py --validate-dependencies
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class GitHubProjectManager:
    """Manages GitHub project integration and automation."""

    def __init__(self, project_name: str = "GoNoGo", owner: str = "QHuuT"):
        """Initialize the project manager."""
        self.project_name = project_name
        self.owner = owner
        self.project_id = None
        self._initialize_project()

    def _initialize_project(self) -> None:
        """Initialize and get project ID."""
        try:
            # Check if we have project access
            result = subprocess.run(
                ["gh", "auth", "status"], capture_output=True, text=True
            )

            if "project" not in result.stdout:
                print("⚠️  Warning: GitHub CLI doesn't have 'project' scope.")
                print("   Run: gh auth refresh -s project -h github.com")
                return

            # Get project ID
            result = subprocess.run(
                ["gh", "project", "list", "--owner", self.owner, "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
            )

            projects = json.loads(result.stdout)
            for project in projects:
                if project["title"] == self.project_name:
                    self.project_id = project["number"]
                    break

            if not self.project_id:
                print(f"⚠️  Project '{self.project_name}' not found.")
                print(f"   Available projects: {[p['title'] for p in projects]}")

        except subprocess.CalledProcessError as e:
            print(f"Error initializing project: {e}")
        except json.JSONDecodeError as e:
            print(f"Error parsing project data: {e}")

    def associate_issue_to_project(self, issue_number: int) -> bool:
        """Associate an issue with the GitHub project."""
        if not self.project_id:
            print("❌ No project ID available")
            return False

        try:
            # Get issue URL
            issue_url = f"https://github.com/{self.owner}/gonogo/issues/{issue_number}"

            # Add to project
            result = subprocess.run(
                ["gh", "project", "item-add", str(self.project_id), "--url", issue_url],
                capture_output=True,
                text=True,
                check=True,
            )

            print(f"✅ Issue #{issue_number} added to project '{self.project_name}'")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Error adding issue to project: {e}")
            return False

    def get_issue_details(self, issue_number: int) -> Optional[Dict]:
        """Get issue details from GitHub."""
        try:
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "view",
                    str(issue_number),
                    "--json",
                    "number,title,body,labels,state",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            return json.loads(result.stdout)

        except subprocess.CalledProcessError as e:
            print(f"❌ Error getting issue details: {e}")
            return None

    def extract_priority_from_labels(self, labels: List[Dict]) -> Optional[str]:
        """Extract priority from issue labels."""
        priority_map = {
            "priority/critical": "Critical",
            "priority/high": "High",
            "priority/medium": "Medium",
            "priority/low": "Low",
        }

        for label in labels:
            if label["name"] in priority_map:
                return priority_map[label["name"]]

        return None

    def extract_parent_from_body(self, body: str, issue_type: str) -> Optional[str]:
        """Extract parent relationship from issue body."""
        import re

        if issue_type == "user-story":
            # Look for "Parent Epic: EP-XXXXX" or "Epic: EP-XXXXX"
            pattern = r"(?:Parent Epic|Epic):\s*(EP-\d{5})"
            match = re.search(pattern, body, re.IGNORECASE)
            return match.group(1) if match else None

        elif issue_type == "defect":
            # Look for "Parent User Story: US-XXXXX"
            pattern = r"Parent User Story:\s*(US-\d{5})"
            match = re.search(pattern, body, re.IGNORECASE)
            return match.group(1) if match else None

        return None

    def extract_dependencies_from_body(self, body: str) -> Dict[str, List[str]]:
        """Extract dependency relationships from issue body."""
        import re

        dependencies = {"blocks": [], "blocked_by": [], "related": []}

        # Look for dependency patterns
        blocks_pattern = r"Blocks:\s*([#\d,\s]+)"
        blocked_by_pattern = r"Blocked by:\s*([#\d,\s]+)"
        related_pattern = r"Related to:\s*([#\d,\s]+)"

        def extract_issue_numbers(text: str) -> List[str]:
            """Extract issue numbers from text like '#12, #13'."""
            numbers = re.findall(r"#(\d+)", text)
            return [f"#{num}" for num in numbers]

        for pattern, key in [
            (blocks_pattern, "blocks"),
            (blocked_by_pattern, "blocked_by"),
            (related_pattern, "related"),
        ]:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                dependencies[key] = extract_issue_numbers(match.group(1))

        return dependencies

    def get_project_items(self) -> List[Dict]:
        """Get all items in the project."""
        if not self.project_id:
            return []

        try:
            result = subprocess.run(
                [
                    "gh",
                    "project",
                    "item-list",
                    str(self.project_id),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            data = json.loads(result.stdout)
            return data.get("items", [])

        except subprocess.CalledProcessError as e:
            print(f"❌ Error getting project items: {e}")
            return []

    def update_project_item_fields(
        self, issue_number: int, priority: str, parent: Optional[str] = None
    ) -> bool:
        """Update project item fields."""
        if not self.project_id:
            return False

        try:
            # Get project items to find the item ID
            items = self.get_project_items()
            item_id = None

            for item in items:
                if item.get("content", {}).get("number") == issue_number:
                    item_id = item.get("id")
                    break

            if not item_id:
                print(f"❌ Issue #{issue_number} not found in project")
                return False

            # Update priority
            if priority:
                subprocess.run(
                    [
                        "gh",
                        "project",
                        "item-edit",
                        "--id",
                        item_id,
                        "--field",
                        "Priority",
                        "--value",
                        priority,
                    ],
                    check=True,
                )

            # Update parent relationship
            if parent:
                field_name = (
                    "Epic Parent" if parent.startswith("EP-") else "User Story Parent"
                )
                subprocess.run(
                    [
                        "gh",
                        "project",
                        "item-edit",
                        "--id",
                        item_id,
                        "--field",
                        field_name,
                        "--value",
                        parent,
                    ],
                    check=True,
                )

            print(f"✅ Updated project fields for issue #{issue_number}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Error updating project fields: {e}")
            return False

    def sync_issue_to_project(self, issue_number: int) -> bool:
        """Sync an issue to project with all metadata."""
        print(f"🔄 Syncing issue #{issue_number} to project...")

        # Get issue details
        issue = self.get_issue_details(issue_number)
        if not issue:
            return False

        # Determine issue type
        issue_type = None
        for label in issue["labels"]:
            if label["name"] in ["epic", "user-story", "defect"]:
                issue_type = label["name"]
                break

        if not issue_type:
            print(f"⚠️  Issue #{issue_number} has no type label")
            return False

        # Associate with project
        if not self.associate_issue_to_project(issue_number):
            return False

        # Extract metadata
        priority = self.extract_priority_from_labels(issue["labels"])
        parent = self.extract_parent_from_body(issue["body"], issue_type)
        dependencies = self.extract_dependencies_from_body(issue["body"])

        # Update project fields
        if priority or parent:
            self.update_project_item_fields(issue_number, priority, parent)

        # Report dependencies
        if any(dependencies.values()):
            print(f"📋 Dependencies found for #{issue_number}:")
            for dep_type, issues in dependencies.items():
                if issues:
                    print(f"   {dep_type}: {', '.join(issues)}")

        return True

    def validate_project_consistency(self) -> List[str]:
        """Validate project consistency and hierarchy."""
        issues = []

        # Get all GitHub issues
        try:
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "list",
                    "--limit",
                    "100",
                    "--state",
                    "all",
                    "--json",
                    "number,title,labels",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            github_issues = json.loads(result.stdout)

        except subprocess.CalledProcessError as e:
            return [f"Error fetching GitHub issues: {e}"]

        # Get project items
        project_items = self.get_project_items()
        project_issue_numbers = {
            item.get("content", {}).get("number")
            for item in project_items
            if item.get("content", {}).get("number")
        }

        # Check for issues not in project
        for issue in github_issues:
            issue_number = issue["number"]
            has_type_label = any(
                label["name"] in ["epic", "user-story", "defect"]
                for label in issue["labels"]
            )

            if has_type_label and issue_number not in project_issue_numbers:
                issues.append(
                    f"Issue #{issue_number} has type label but not in project"
                )

        return issues

    def generate_dependency_report(self) -> None:
        """Generate a dependency report for all issues."""
        print("📊 Dependency Report")
        print("=" * 50)

        try:
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "list",
                    "--limit",
                    "100",
                    "--state",
                    "all",
                    "--json",
                    "number,title,body,labels",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            issues = json.loads(result.stdout)

            dependency_graph = {}
            for issue in issues:
                number = issue["number"]
                title = issue["title"]
                deps = self.extract_dependencies_from_body(issue["body"])

                if any(deps.values()):
                    dependency_graph[f"#{number}"] = {
                        "title": title,
                        "dependencies": deps,
                    }

            if not dependency_graph:
                print("No dependencies found.")
                return

            for issue_ref, data in dependency_graph.items():
                print(f"\n{issue_ref}: {data['title']}")
                for dep_type, dep_list in data["dependencies"].items():
                    if dep_list:
                        print(f"  {dep_type}: {', '.join(dep_list)}")

        except subprocess.CalledProcessError as e:
            print(f"❌ Error generating dependency report: {e}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="GitHub Project Manager")
    parser.add_argument(
        "--associate-issue", type=int, help="Associate issue number with project"
    )
    parser.add_argument(
        "--sync-issue", type=int, help="Sync issue with all project metadata"
    )
    parser.add_argument(
        "--validate-consistency",
        action="store_true",
        help="Validate project consistency",
    )
    parser.add_argument(
        "--dependency-report", action="store_true", help="Generate dependency report"
    )
    parser.add_argument("--project-name", default="GoNoGo", help="GitHub project name")
    parser.add_argument("--owner", default="QHuuT", help="GitHub owner/organization")

    args = parser.parse_args()

    manager = GitHubProjectManager(args.project_name, args.owner)

    if args.associate_issue:
        success = manager.associate_issue_to_project(args.associate_issue)
        sys.exit(0 if success else 1)

    if args.sync_issue:
        success = manager.sync_issue_to_project(args.sync_issue)
        sys.exit(0 if success else 1)

    if args.validate_consistency:
        issues = manager.validate_project_consistency()
        if issues:
            print("⚠️  Consistency issues found:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
        else:
            print("✅ Project consistency validated")

    if args.dependency_report:
        manager.generate_dependency_report()

    if not any(
        [
            args.associate_issue,
            args.sync_issue,
            args.validate_consistency,
            args.dependency_report,
        ]
    ):
        parser.print_help()


if __name__ == "__main__":
    main()
