#!/usr/bin/env python3
"""
Comprehensive GitHub Issues Restoration Script

This script restores ALL GitHub issues (epics, user stories, defects) to the RTM database.
It fetches data using GitHub CLI, maps labels to proper epic IDs, and creates all database
records with correct foreign key relationships.

Scope: 8 Epics + 66 User Stories + 10 Defects = 84 total items

Usage:
    python tools/restore_github_issues_comprehensive.py [--dry-run] [--repo REPO] [--verbose]

Requirements:
    - GitHub CLI (gh) must be installed and authenticated
    - Database connection must be available
    - All capabilities must exist in database (CAP-00001 through CAP-00004)

Related Issues:
    - Restores all issues per user requirements
    - Handles complete database schema with all NOT NULL constraints
    - Maps epic labels correctly to database IDs
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.append('src')

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from be.database import get_db_session, create_tables
from be.models.traceability.epic import Epic
from be.models.traceability.user_story import UserStory
from be.models.traceability.defect import Defect
from be.models.traceability.capability import Capability

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitHubIssueRestorer:
    """Main class for restoring GitHub issues to the database."""

    def __init__(self, repo: str = "your-org/your-repo", dry_run: bool = False, verbose: bool = False):
        self.repo = repo
        self.dry_run = dry_run
        self.verbose = verbose

        # Epic label to epic_id mapping based on GitHub labels
        self.epic_label_mapping = {
            "epic/multipersona-dashboard": "EP-00010",
            "epic/privacy-consent": "EP-00003",
            "epic/gdpr-comments": "EP-00002",
            "epic/blog-content": "EP-00001",
            "epic/test-logging": "EP-00007",
            "epic/github-project": "EP-00006",
            "epic/rtm-automation": "EP-00005",
            "epic/github-workflow": "EP-00004"
        }

        # Capability mapping from tools/capability_mapping.py
        self.epic_to_capability = {
            "EP-00001": "CAP-00003",  # Blog Content Management -> Blog Platform
            "EP-00002": "CAP-00004",  # GDPR-Compliant Comment System -> GDPR Compliance
            "EP-00003": "CAP-00004",  # Privacy and Consent Management -> GDPR Compliance
            "EP-00004": "CAP-00001",  # GitHub Workflow Integration -> GitHub Integration
            "EP-00005": "CAP-00002",  # RTM Automation -> Requirements Traceability
            "EP-00006": "CAP-00001",  # GitHub Project Management Integration -> GitHub Integration
            "EP-00007": "CAP-00002",  # Test logging and reporting -> Requirements Traceability
            "EP-00010": "CAP-00002",  # Multi-persona dashboard -> Requirements Traceability
        }

        # Epic details based on user requirements
        self.epic_details = {
            "EP-00010": {
                "title": "Dashboard de Traçabilité des Exigences Multi-Persona",
                "github_issue_number": 88,
                "priority": "high",
                "component": "frontend+backend",
                "gdpr_applicable": False
            },
            "EP-00003": {
                "title": "Privacy and Consent Management",
                "github_issue_number": 64,
                "priority": "critical",
                "component": "security",
                "gdpr_applicable": True
            },
            "EP-00002": {
                "title": "GDPR-Compliant Comment System",
                "github_issue_number": 63,
                "priority": "high",
                "component": "backend",
                "gdpr_applicable": True
            },
            "EP-00001": {
                "title": "Blog Content Management",
                "github_issue_number": 62,
                "priority": "high",
                "component": "frontend",
                "gdpr_applicable": False
            },
            "EP-00007": {
                "title": "Test logging and reporting",
                "github_issue_number": 17,
                "priority": "high",
                "component": "testing",
                "gdpr_applicable": True
            },
            "EP-00006": {
                "title": "GitHub Project Management Integration",
                "github_issue_number": 13,
                "priority": "high",
                "component": "backend",
                "gdpr_applicable": False
            },
            "EP-00005": {
                "title": "Requirements Traceability Matrix Automation",
                "github_issue_number": 7,
                "priority": "medium",
                "component": "backend",
                "gdpr_applicable": False
            },
            "EP-00004": {
                "title": "GitHub Workflow Integration",
                "github_issue_number": 1,
                "priority": "critical",
                "component": "ci-cd",
                "gdpr_applicable": True
            }
        }

        # Counters for statistics
        self.stats = {
            "epics_created": 0,
            "user_stories_created": 0,
            "defects_created": 0,
            "errors": 0
        }

    def run_github_cli(self, command: List[str]) -> str:
        """Execute GitHub CLI command and return output."""
        try:
            cmd = ["gh"] + command
            if self.verbose:
                logger.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',
                errors='replace'
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"GitHub CLI command failed: {' '.join(cmd)}")
            logger.error(f"Error: {e.stderr}")
            raise

    def fetch_all_issues(self) -> List[Dict]:
        """Fetch all issues from GitHub repository."""
        logger.info(f"Fetching all issues from {self.repo}...")

        # Fetch all issues including closed ones with comprehensive fields
        gh_command = [
            "issue", "list",
            "--repo", self.repo,
            "--state", "all",
            "--limit", "1000",
            "--json", "number,title,body,labels,state,assignees,createdAt,updatedAt,url"
        ]

        output = self.run_github_cli(gh_command)
        issues = json.loads(output)

        logger.info(f"Found {len(issues)} total issues")
        return issues

    def classify_issue(self, issue: Dict) -> Tuple[str, Optional[str]]:
        """Classify issue as epic, user-story, or defect and return epic_id if applicable."""
        labels = [label["name"] for label in issue.get("labels", [])]

        # Check for epic labels first
        for label in labels:
            if label.startswith("epic/"):
                epic_id = self.epic_label_mapping.get(label)
                if epic_id:
                    return "epic", epic_id

        # Check for type labels
        issue_type = None
        epic_id = None

        for label in labels:
            if label == "type/epic":
                issue_type = "epic"
            elif label == "type/user-story":
                issue_type = "user-story"
            elif label == "type/defect" or label == "type/bug":
                issue_type = "defect"
            elif label.startswith("epic/"):
                # For user stories and defects, find their parent epic
                epic_id = self.epic_label_mapping.get(label)

        # If no explicit type, infer from issue number patterns or epic labels
        if not issue_type:
            issue_number = issue["number"]
            title = issue["title"].lower()

            # Check if this is one of our known epics by issue number
            for known_epic_id, details in self.epic_details.items():
                if details["github_issue_number"] == issue_number:
                    return "epic", known_epic_id

            # Heuristic classification based on title patterns
            if any(word in title for word in ["epic", "feature", "capability"]):
                issue_type = "epic"
            elif any(word in title for word in ["defect", "bug", "fix", "error"]):
                issue_type = "defect"
            else:
                issue_type = "user-story"  # Default assumption

        return issue_type, epic_id

    def extract_component_from_labels(self, labels: List[str]) -> str:
        """Extract component from GitHub labels."""
        for label in labels:
            if label.startswith("component/"):
                component = label.replace("component/", "")
                # Map GitHub label components to database components
                component_mapping = {
                    "frontend": "frontend",
                    "backend": "backend",
                    "database": "database",
                    "security": "security",
                    "testing": "testing",
                    "ci-cd": "ci-cd",
                    "documentation": "documentation"
                }
                return component_mapping.get(component, component)

        return "backend"  # Default component

    def extract_priority_from_labels(self, labels: List[str]) -> str:
        """Extract priority from GitHub labels."""
        for label in labels:
            if label.startswith("priority/"):
                priority = label.replace("priority/", "")
                if priority in ["critical", "high", "medium", "low"]:
                    return priority

        return "medium"  # Default priority

    def extract_story_points_from_body(self, body: str) -> int:
        """Extract story points from issue body or title."""
        if not body:
            return 0

        # Look for patterns like "Story Points: 5" or "SP: 3" or "[5 pts]"
        import re
        patterns = [
            r"story\s*points?\s*:?\s*(\d+)",
            r"sp\s*:?\s*(\d+)",
            r"\[(\d+)\s*pts?\]",
            r"points?\s*:?\s*(\d+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, body.lower())
            if match:
                return int(match.group(1))

        return 0  # Default story points

    def get_capability_id_for_epic(self, epic_id: str, session: Session) -> Optional[int]:
        """Get database capability ID for an epic."""
        capability_id_str = self.epic_to_capability.get(epic_id)
        if not capability_id_str:
            return None

        capability = session.query(Capability).filter(
            Capability.capability_id == capability_id_str
        ).first()

        return capability.id if capability else None

    def get_epic_database_id(self, epic_id: str, session: Session) -> Optional[int]:
        """Get database ID for an epic by epic_id."""
        epic = session.query(Epic).filter(Epic.epic_id == epic_id).first()
        return epic.id if epic else None

    def create_epic(self, issue: Dict, epic_id: str, session: Session) -> bool:
        """Create an epic in the database."""
        try:
            labels = [label["name"] for label in issue.get("labels", [])]

            # Get epic details or use defaults
            epic_details = self.epic_details.get(epic_id, {})

            epic = Epic(
                epic_id=epic_id,
                title=issue["title"],
                description=issue.get("body", ""),
                status="completed" if issue["state"] == "closed" else "in_progress",
                github_issue_number=issue["number"],
                github_issue_url=issue["url"],
                priority=epic_details.get("priority", self.extract_priority_from_labels(labels)),
                component=epic_details.get("component", self.extract_component_from_labels(labels)),
                capability_id=self.get_capability_id_for_epic(epic_id, session),
                gdpr_applicable=epic_details.get("gdpr_applicable", any("gdpr" in label.lower() for label in labels)),

                # Set all required NOT NULL fields with defaults
                total_story_points=0,
                completed_story_points=0,
                completion_percentage=0.0,
                risk_level="medium",
                initial_scope_estimate=0,
                scope_creep_percentage=0.0,
                velocity_points_per_sprint=0.0,
                team_size=1,
                defect_density=0.0,
                test_coverage_percentage=0.0,
                code_review_score=0.0,
                technical_debt_hours=0,
                stakeholder_satisfaction_score=0.0,
                business_impact_score=0.0,
                roi_percentage=0.0,
                user_adoption_rate=0.0,
                metrics_calculation_frequency="daily"
            )

            if not self.dry_run:
                session.add(epic)
                session.commit()
                logger.info(f"✓ Created epic: {epic_id} - {issue['title']}")
            else:
                logger.info(f"[DRY RUN] Would create epic: {epic_id} - {issue['title']}")

            self.stats["epics_created"] += 1
            return True

        except Exception as e:
            logger.error(f"Failed to create epic {epic_id}: {e}")
            self.stats["errors"] += 1
            if not self.dry_run:
                session.rollback()
            return False

    def create_user_story(self, issue: Dict, epic_id: str, session: Session) -> bool:
        """Create a user story in the database."""
        try:
            labels = [label["name"] for label in issue.get("labels", [])]

            # Generate user story ID (US-XXXXX format)
            user_story_id = f"US-{issue['number']:05d}"

            # Get epic database ID
            epic_db_id = self.get_epic_database_id(epic_id, session)
            if not epic_db_id:
                logger.warning(f"Epic {epic_id} not found in database for user story {user_story_id}")
                return False

            user_story = UserStory(
                user_story_id=user_story_id,
                epic_id=epic_db_id,
                github_issue_number=issue["number"],
                title=issue["title"],
                description=issue.get("body", ""),
                status="completed" if issue["state"] == "closed" else "planned",
                github_issue_url=issue["url"],
                priority=self.extract_priority_from_labels(labels),
                component=self.extract_component_from_labels(labels),
                story_points=self.extract_story_points_from_body(issue.get("body", "")),
                implementation_status="completed" if issue["state"] == "closed" else "todo",
                has_bdd_scenarios=any("bdd" in label.lower() for label in labels),
                affects_gdpr=any("gdpr" in label.lower() for label in labels),
                github_issue_state=issue["state"]
            )

            if not self.dry_run:
                session.add(user_story)
                session.commit()
                logger.info(f"✓ Created user story: {user_story_id} -> {epic_id} - {issue['title']}")
            else:
                logger.info(f"[DRY RUN] Would create user story: {user_story_id} -> {epic_id} - {issue['title']}")

            self.stats["user_stories_created"] += 1
            return True

        except Exception as e:
            logger.error(f"Failed to create user story {issue['number']}: {e}")
            self.stats["errors"] += 1
            if not self.dry_run:
                session.rollback()
            return False

    def create_defect(self, issue: Dict, epic_id: Optional[str], session: Session) -> bool:
        """Create a defect in the database."""
        try:
            labels = [label["name"] for label in issue.get("labels", [])]

            # Generate defect ID (DEF-XXXXX format)
            defect_id = f"DEF-{issue['number']:05d}"

            # Get epic database ID if epic_id provided
            epic_db_id = None
            if epic_id:
                epic_db_id = self.get_epic_database_id(epic_id, session)

            # Extract severity from labels or default to medium
            severity = "medium"
            for label in labels:
                if label.startswith("severity/"):
                    severity = label.replace("severity/", "")
                    break

            defect = Defect(
                defect_id=defect_id,
                github_issue_number=issue["number"],
                title=issue["title"],
                description=issue.get("body", ""),
                status="resolved" if issue["state"] == "closed" else "open",
                github_issue_url=issue["url"],
                epic_id=epic_db_id,
                priority=self.extract_priority_from_labels(labels),
                severity=severity,
                component=self.extract_component_from_labels(labels),
                defect_type="bug",  # Default type

                # Set defaults for NOT NULL fields
                escaped_to_production=any("production" in label.lower() for label in labels),
                is_security_issue=any("security" in label.lower() for label in labels),
                affects_gdpr=any("gdpr" in label.lower() for label in labels),
                is_regression=any("regression" in label.lower() for label in labels),
                affects_customers=any("customer" in label.lower() for label in labels),
                estimated_hours=0.0,
                actual_hours=0.0,
                found_in_phase="development",  # Default phase
                github_issue_state=issue["state"]
            )

            if not self.dry_run:
                session.add(defect)
                session.commit()
                epic_ref = f" -> {epic_id}" if epic_id else ""
                logger.info(f"✓ Created defect: {defect_id}{epic_ref} - {issue['title']}")
            else:
                epic_ref = f" -> {epic_id}" if epic_id else ""
                logger.info(f"[DRY RUN] Would create defect: {defect_id}{epic_ref} - {issue['title']}")

            self.stats["defects_created"] += 1
            return True

        except Exception as e:
            logger.error(f"Failed to create defect {issue['number']}: {e}")
            self.stats["errors"] += 1
            if not self.dry_run:
                session.rollback()
            return False

    def ensure_capabilities_exist(self, session: Session) -> bool:
        """Ensure all required capabilities exist in the database."""
        capabilities_needed = [
            ("CAP-00001", "GitHub Integration", "Automations and integrations with GitHub workflows"),
            ("CAP-00002", "Requirements Traceability", "Traceability matrix, dashboards, and portfolio visibility"),
            ("CAP-00003", "Blog Platform", "Blog content experience and supporting platform capabilities"),
            ("CAP-00004", "GDPR Compliance", "Privacy, consent, and regulatory compliance capabilities")
        ]

        for cap_id, name, description in capabilities_needed:
            existing = session.query(Capability).filter(Capability.capability_id == cap_id).first()
            if not existing:
                if not self.dry_run:
                    capability = Capability(
                        capability_id=cap_id,
                        name=name,
                        description=description,
                        strategic_priority="high",
                        status="active"
                    )
                    session.add(capability)
                    logger.info(f"✓ Created capability: {cap_id} - {name}")
                else:
                    logger.info(f"[DRY RUN] Would create capability: {cap_id} - {name}")

        if not self.dry_run:
            session.commit()

        return True

    def process_issues(self, issues: List[Dict]) -> bool:
        """Process all issues and create database records."""
        logger.info("Processing issues and creating database records...")

        session = get_db_session()
        try:
            # Ensure capabilities exist first
            self.ensure_capabilities_exist(session)

            # Sort issues to process epics first
            epics = []
            user_stories = []
            defects = []

            for issue in issues:
                issue_type, epic_id = self.classify_issue(issue)

                if issue_type == "epic":
                    epics.append((issue, epic_id))
                elif issue_type == "user-story":
                    user_stories.append((issue, epic_id))
                elif issue_type == "defect":
                    defects.append((issue, epic_id))
                else:
                    logger.warning(f"Unknown issue type for #{issue['number']}: {issue['title']}")

            logger.info(f"Classified: {len(epics)} epics, {len(user_stories)} user stories, {len(defects)} defects")

            # Process epics first (required for foreign keys)
            logger.info("Creating epics...")
            for issue, epic_id in epics:
                if epic_id:
                    self.create_epic(issue, epic_id, session)

            # Process user stories
            logger.info("Creating user stories...")
            for issue, epic_id in user_stories:
                if epic_id:
                    self.create_user_story(issue, epic_id, session)
                else:
                    logger.warning(f"User story #{issue['number']} has no epic assignment: {issue['title']}")

            # Process defects
            logger.info("Creating defects...")
            for issue, epic_id in defects:
                self.create_defect(issue, epic_id, session)

            return True

        except Exception as e:
            logger.error(f"Error processing issues: {e}")
            if not self.dry_run:
                session.rollback()
            return False
        finally:
            session.close()

    def print_statistics(self):
        """Print restoration statistics."""
        logger.info("\n" + "="*60)
        logger.info("RESTORATION STATISTICS")
        logger.info("="*60)
        logger.info(f"Epics created:       {self.stats['epics_created']:3d}")
        logger.info(f"User Stories created: {self.stats['user_stories_created']:3d}")
        logger.info(f"Defects created:     {self.stats['defects_created']:3d}")
        logger.info(f"Total items:         {sum(self.stats[k] for k in ['epics_created', 'user_stories_created', 'defects_created']):3d}")
        logger.info(f"Errors:              {self.stats['errors']:3d}")
        logger.info("="*60)

        expected_total = 8 + 66 + 10  # 8 epics + 66 user stories + 10 defects
        actual_total = sum(self.stats[k] for k in ['epics_created', 'user_stories_created', 'defects_created'])

        if actual_total == expected_total:
            logger.info("✅ SUCCESS: All expected items were processed!")
        else:
            logger.warning(f"⚠️  Expected {expected_total} items, but processed {actual_total}")

    def run(self) -> bool:
        """Main execution method."""
        try:
            logger.info("Starting comprehensive GitHub issues restoration...")
            logger.info(f"Repository: {self.repo}")
            logger.info(f"Dry run: {self.dry_run}")

            # Create database tables if they don't exist
            if not self.dry_run:
                create_tables()
                logger.info("✓ Database tables ready")

            # Fetch all issues from GitHub
            issues = self.fetch_all_issues()

            # Process and create database records
            success = self.process_issues(issues)

            # Print statistics
            self.print_statistics()

            if success:
                logger.info("✅ GitHub issues restoration completed successfully!")
            else:
                logger.error("❌ GitHub issues restoration failed!")

            return success

        except Exception as e:
            logger.error(f"Restoration failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Restore all GitHub issues to the RTM database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry run to see what would be created
    python tools/restore_github_issues_comprehensive.py --dry-run

    # Restore all issues from specific repository
    python tools/restore_github_issues_comprehensive.py --repo your-org/your-repo

    # Verbose output for debugging
    python tools/restore_github_issues_comprehensive.py --verbose
        """
    )

    parser.add_argument(
        "--repo",
        default="your-org/your-repo",
        help="GitHub repository in format 'owner/repo' (default: your-org/your-repo)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and run restorer
    restorer = GitHubIssueRestorer(
        repo=args.repo,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    success = restorer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()