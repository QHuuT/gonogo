#!/usr/bin/env python3
"""
Update GitHub Issues to Match New Template Format

Updates existing GitHub issues to include all the new template fields
based on database data and missing template information.
"""

import requests
import re
import os
import sys
import json

sys.path.append("src")

from be.database import SessionLocal
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


def update_github_issue(issue_number, new_body, dry_run=True):
    """Update a GitHub issue with new body content."""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("No GitHub token available")
        return False

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    url = f"https://api.github.com/repos/QHuuT/gonogo/issues/{issue_number}"
    data = {"body": new_body}

    if dry_run:
        print(f"DRY RUN - Would update issue #{issue_number}")
        return True

    response = requests.patch(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"Updated issue #{issue_number}")
        return True
    else:
        print(f"Failed to update issue #{issue_number}: {response.status_code}")
        return False


def generate_user_story_body(issue, db_user_story=None):
    """Generate new body for user story based on template fields."""
    body_parts = []

    # Extract existing content or use database values
    title = issue.get("title", "")
    existing_body = issue.get("body", "")

    # User Story section
    body_parts.append("## User Story")

    # Try to extract existing user story format
    us_match = re.search(
        r"\*\*As a\*\* (.+?)\n\*\*I want\*\* (.+?)\n\*\*So that\*\* (.+?)(?:\n|$)",
        existing_body,
    )
    if us_match:
        body_parts.append(f"**As a** {us_match.group(1)}")
        body_parts.append(f"**I want** {us_match.group(2)}")
        body_parts.append(f"**So that** {us_match.group(3)}")
    else:
        body_parts.append("**As a** blog visitor")
        body_parts.append("**I want** [to be defined]")
        body_parts.append("**So that** [benefit to be defined]")

    body_parts.append("")

    # Business Value
    body_parts.append("## Business Value")
    if db_user_story and db_user_story.business_value:
        body_parts.append(db_user_story.business_value)
    else:
        bv_match = re.search(
            r"## Business Value\s*\n(.*?)(?=\n##|\n---|$)", existing_body, re.DOTALL
        )
        if bv_match:
            body_parts.append(bv_match.group(1).strip())
        else:
            body_parts.append("[Business value to be defined]")

    body_parts.append("")

    # Story Points
    body_parts.append("## Story Points")
    if db_user_story and db_user_story.story_points:
        body_parts.append(str(db_user_story.story_points))
    else:
        sp_match = re.search(r"Story Points?[:\s]*(\d+)", existing_body, re.IGNORECASE)
        if sp_match:
            body_parts.append(sp_match.group(1))
        else:
            body_parts.append("0")

    body_parts.append("")

    # Priority
    body_parts.append("## Priority")
    if db_user_story and db_user_story.priority:
        body_parts.append(db_user_story.priority)
    else:
        body_parts.append("medium")

    body_parts.append("")

    # Component
    body_parts.append("## Component")
    if db_user_story and db_user_story.component:
        body_parts.append(db_user_story.component)
    else:
        body_parts.append("[Component to be assigned]")

    body_parts.append("")

    # Acceptance Criteria
    body_parts.append("## Acceptance Criteria - Functional Requirements")
    if db_user_story and db_user_story.acceptance_criteria:
        body_parts.append(db_user_story.acceptance_criteria)
    else:
        ac_match = re.search(
            r"## Acceptance Criteria[^#]*?\n(.*?)(?=\n##|\n---|$)",
            existing_body,
            re.DOTALL,
        )
        if ac_match:
            body_parts.append(ac_match.group(1).strip())
        else:
            body_parts.append(
                "- [ ] **Given** [context], **When** [action], **Then** [expected result]"
            )

    body_parts.append("")

    # GDPR Considerations
    body_parts.append("## GDPR Considerations")
    if db_user_story and db_user_story.affects_gdpr:
        body_parts.append("- [x] Involves personal data processing")
        if db_user_story.gdpr_considerations:
            body_parts.append("")
            body_parts.append("### GDPR Details")
            body_parts.append(db_user_story.gdpr_considerations)
    else:
        body_parts.append("- [ ] Involves personal data processing")
        body_parts.append("- [ ] GDPR compliance review needed")
        body_parts.append("- [x] Not applicable")

    body_parts.append("")

    # Dependencies
    body_parts.append("## Dependencies")
    if db_user_story and db_user_story.depends_on_issues:
        try:
            depends_on = (
                json.loads(db_user_story.depends_on_issues)
                if db_user_story.depends_on_issues != "[]"
                else []
            )
            if depends_on:
                for dep in depends_on:
                    body_parts.append(f"- #{dep}")
            else:
                body_parts.append("None")
        except:
            body_parts.append("None")
    else:
        body_parts.append("None")

    body_parts.append("")

    # Blocks
    body_parts.append("## Blocks")
    if db_user_story and db_user_story.blocks_issues:
        try:
            blocks = (
                json.loads(db_user_story.blocks_issues)
                if db_user_story.blocks_issues != "[]"
                else []
            )
            if blocks:
                for block in blocks:
                    body_parts.append(f"- #{block}")
            else:
                body_parts.append("None")
        except:
            body_parts.append("None")
    else:
        body_parts.append("None")

    body_parts.append("")

    # Sprint
    if db_user_story and db_user_story.sprint:
        body_parts.append("## Sprint")
        body_parts.append(db_user_story.sprint)
        body_parts.append("")

    # Target Release Version
    body_parts.append("## Target Release Version")
    if db_user_story and db_user_story.target_release_version:
        body_parts.append(db_user_story.target_release_version)
    else:
        # Extract from labels if available
        labels = db_user_story.github_labels if db_user_story else "[]"
        version_match = re.search(r'release/([^"]+)', labels)
        if version_match:
            body_parts.append(version_match.group(1))
        else:
            body_parts.append("Future Release")
    body_parts.append("")

    # BDD Scenarios
    body_parts.append("## BDD Scenarios")
    if db_user_story and db_user_story.has_bdd_scenarios:
        body_parts.append("- [x] Has BDD scenarios defined")
    else:
        body_parts.append("- [ ] Has BDD scenarios defined")
        body_parts.append("- [x] BDD scenarios need to be created")

    return "\n".join(body_parts)


def generate_defect_body(issue, db_defect=None):
    """Generate new body for defect based on template fields."""
    body_parts = []

    title = issue.get("title", "")
    existing_body = issue.get("body", "")

    # Steps to Reproduce
    body_parts.append("## Steps to Reproduce")
    if db_defect and db_defect.steps_to_reproduce:
        body_parts.append(db_defect.steps_to_reproduce)
    else:
        str_match = re.search(
            r"## Steps to Reproduce\s*\n(.*?)(?=\n##|\n---|$)", existing_body, re.DOTALL
        )
        if str_match:
            body_parts.append(str_match.group(1).strip())
        else:
            body_parts.append("1. [Step to reproduce the issue]")

    body_parts.append("")

    # Expected Behavior
    body_parts.append("## Expected Behavior")
    if db_defect and db_defect.expected_behavior:
        body_parts.append(db_defect.expected_behavior)
    else:
        eb_match = re.search(
            r"## Expected Behavior\s*\n(.*?)(?=\n##|\n---|$)", existing_body, re.DOTALL
        )
        if eb_match:
            body_parts.append(eb_match.group(1).strip())
        else:
            body_parts.append("[What should happen]")

    body_parts.append("")

    # Actual Behavior
    body_parts.append("## Actual Behavior")
    if db_defect and db_defect.actual_behavior:
        body_parts.append(db_defect.actual_behavior)
    else:
        ab_match = re.search(
            r"## Actual Behavior\s*\n(.*?)(?=\n##|\n---|$)", existing_body, re.DOTALL
        )
        if ab_match:
            body_parts.append(ab_match.group(1).strip())
        else:
            body_parts.append("[What actually happens]")

    body_parts.append("")

    # Business Impact
    body_parts.append("## Business Impact")
    if db_defect and db_defect.customer_impact_details:
        body_parts.append(db_defect.customer_impact_details)
    else:
        bi_match = re.search(
            r"## Business Impact\s*\n(.*?)(?=\n##|\n---|$)", existing_body, re.DOTALL
        )
        if bi_match:
            body_parts.append(bi_match.group(1).strip())
        else:
            body_parts.append("[Impact on users and business]")

    body_parts.append("")

    # Defect Type
    body_parts.append("## Defect Type")
    if db_defect and db_defect.defect_type:
        body_parts.append(db_defect.defect_type)
    else:
        body_parts.append("bug")

    body_parts.append("")

    # Severity
    body_parts.append("## Severity")
    if db_defect and db_defect.severity:
        # Map existing severity values to new options including blocking
        severity_mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "blocker": "blocking",
            "block": "blocking",
        }
        mapped_severity = severity_mapping.get(
            db_defect.severity.lower(), db_defect.severity
        )
        body_parts.append(mapped_severity)
    else:
        body_parts.append("medium")

    body_parts.append("")

    # Priority
    body_parts.append("## Priority")
    if db_defect and db_defect.priority:
        body_parts.append(db_defect.priority)
    else:
        body_parts.append("medium")

    body_parts.append("")

    # Environment
    body_parts.append("## Environment")
    if db_defect and db_defect.environment:
        # Map existing environment values to new dropdown options
        env_mapping = {
            "production": "Prod",
            "prod": "Prod",
            "demo": "Demo",
            "demonstration": "Demo",
            "staging": "Staging",
            "stage": "Staging",
            "development": "Dev",
            "dev": "Dev",
            "local": "Dev",
        }
        mapped_env = env_mapping.get(db_defect.environment.lower(), "Dev")
        body_parts.append(mapped_env)
    else:
        body_parts.append("Dev")
    body_parts.append("")

    # Browser Version
    if db_defect and db_defect.browser_version:
        body_parts.append("## Browser Version")
        body_parts.append(db_defect.browser_version)
        body_parts.append("")

    # OS Version
    if db_defect and db_defect.os_version:
        body_parts.append("## OS Version")
        body_parts.append(db_defect.os_version)
        body_parts.append("")

    # Found in Phase
    if db_defect and db_defect.found_in_phase:
        body_parts.append("## Found in Phase")
        body_parts.append(db_defect.found_in_phase)
        body_parts.append("")

    # Component
    body_parts.append("## Component")
    if db_defect and db_defect.component:
        body_parts.append(db_defect.component)
    else:
        body_parts.append("[Component to be assigned]")

    body_parts.append("")

    # Quality Flags
    body_parts.append("## Quality Flags")
    flags = []
    if db_defect:
        if db_defect.escaped_to_production:
            flags.append("- [x] Escaped to production")
        else:
            flags.append("- [ ] Escaped to production")

        if db_defect.is_security_issue:
            flags.append("- [x] Security issue")
        else:
            flags.append("- [ ] Security issue")

        if db_defect.is_regression:
            flags.append("- [x] Regression from previous version")
        else:
            flags.append("- [ ] Regression from previous version")

        if db_defect.affects_customers:
            flags.append("- [x] Affects customers")
        else:
            flags.append("- [ ] Affects customers")

        if db_defect.affects_gdpr:
            flags.append("- [x] GDPR/Privacy impact")
        else:
            flags.append("- [ ] GDPR/Privacy impact")
    else:
        flags = [
            "- [ ] Escaped to production",
            "- [ ] Security issue",
            "- [ ] Regression from previous version",
            "- [ ] Affects customers",
            "- [ ] GDPR/Privacy impact",
        ]

    body_parts.extend(flags)
    body_parts.append("")

    # Root Cause Analysis
    if db_defect and db_defect.root_cause:
        body_parts.append("## Root Cause Analysis")
        body_parts.append(db_defect.root_cause)
        body_parts.append("")

    # Estimated Hours
    if db_defect and db_defect.estimated_hours:
        body_parts.append("## Estimated Hours")
        body_parts.append(str(db_defect.estimated_hours))
        body_parts.append("")

    # Actual Hours
    if db_defect and db_defect.actual_hours:
        body_parts.append("## Actual Hours")
        body_parts.append(str(db_defect.actual_hours))
        body_parts.append("")

    return "\n".join(body_parts)


def update_github_issues_templates(dry_run=True):
    """Update GitHub issues to match new template format."""
    session = SessionLocal()

    try:
        issues = fetch_github_issues()
        if not issues:
            return

        print("\n=== Update GitHub Issues to New Template Format ===")
        print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")

        updated_count = 0

        for issue in issues:
            title = issue.get("title", "")
            issue_number = issue["number"]

            # Check if this is a user story
            us_id_match = re.search(r"US-\d{5}", title)
            if us_id_match:
                us_id = us_id_match.group(0)
                db_user_story = (
                    session.query(UserStory)
                    .filter(UserStory.user_story_id == us_id)
                    .first()
                )

                new_body = generate_user_story_body(issue, db_user_story)

                print(f"\n--- User Story #{issue_number}: {us_id} ---")
                if dry_run:
                    print("DRY RUN - New body preview:")
                    try:
                        preview = (
                            new_body[:200] + "..." if len(new_body) > 200 else new_body
                        )
                        print(preview.encode("utf-8", "replace").decode("utf-8"))
                    except:
                        print("[Preview not available due to encoding]")
                else:
                    if update_github_issue(issue_number, new_body, dry_run):
                        updated_count += 1
                continue

            # Check if this is a defect
            def_id_match = re.search(r"DEF-\d{5}", title)
            if def_id_match:
                def_id = def_id_match.group(0)
                db_defect = (
                    session.query(Defect).filter(Defect.defect_id == def_id).first()
                )

                new_body = generate_defect_body(issue, db_defect)

                print(f"\n--- Defect #{issue_number}: {def_id} ---")
                if dry_run:
                    print("DRY RUN - New body preview:")
                    try:
                        preview = (
                            new_body[:200] + "..." if len(new_body) > 200 else new_body
                        )
                        print(preview.encode("utf-8", "replace").decode("utf-8"))
                    except:
                        print("[Preview not available due to encoding]")
                else:
                    if update_github_issue(issue_number, new_body, dry_run):
                        updated_count += 1
                continue

        if dry_run:
            print("\nDRY RUN - Would update GitHub issues with new template format")
        else:
            print(f"\nUpdated {updated_count} GitHub issues with new template format")

    except Exception as e:
        print(f"Error updating GitHub issues: {e}")
        import traceback

        traceback.print_exc()
    finally:
        session.close()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Update GitHub issues to new template format"
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
        help="Actually execute the updates (overrides --dry-run)",
    )

    args = parser.parse_args()

    # If --execute is specified, turn off dry run
    dry_run = args.dry_run and not args.execute

    update_github_issues_templates(dry_run)


if __name__ == "__main__":
    main()
