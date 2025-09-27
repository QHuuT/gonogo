#!/usr/bin/env python3
"""
GitHub Sync Manager Tool

Comprehensive tool to sync GitHub issues with RTM database entities.
Keeps cached GitHub metadata up-to-date for accurate progress calculations.

Related Issue: User request - Fix GitHub-database syncing mapping issues
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from be.database import get_db_session
    from be.models.traceability import Defect, Epic, GitHubSync, Test, UserStory, Capability

    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Error: Database modules not available: {e}")
    DATABASE_AVAILABLE = False

try:
    from tools.capability_mapping import (
        EPIC_TO_CAPABILITY_MAP,
        CAPABILITY_CATALOG,
        capability_label_name,
    )
except ImportError:
    EPIC_TO_CAPABILITY_MAP = {}
    CAPABILITY_CATALOG = {}


@dataclass
class SyncResult:
    """Result of a sync operation."""

    entity_type: str
    entity_id: str
    github_issue_number: int
    old_status: str
    new_status: str
    updated: bool
    error: Optional[str] = None


@dataclass
class SyncSummary:
    """Summary of sync operations."""

    total_entities: int = 0
    updated_entities: int = 0
    failed_entities: int = 0
    conflicted_entities: int = 0
    results: List[SyncResult] = None

    def __post_init__(self):
        if self.results is None:
            self.results = []


class GitHubSyncManager:
    """Comprehensive GitHub to database sync manager."""

    def __init__(
        self, dry_run: bool = False, verbose: bool = True, close_completed: bool = False
    ):
        self.dry_run = dry_run
        self.verbose = verbose
        self.close_completed = close_completed
        self.db_session = None
        self.github_issues = []
        self.sync_summary = SyncSummary()
        self.capability_label_suggestions: List[Dict[str, Any]] = []

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

    def fetch_github_issues(self, since_date: Optional[str] = None) -> bool:
        """Fetch GitHub issues using gh CLI with optional date filtering."""
        try:
            if self.verbose:
                print("Fetching GitHub issues...")

            # Build command with optional date filtering
            cmd = [
                "gh",
                "issue",
                "list",
                "--limit",
                "1000",  # Increase limit for comprehensive sync
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

            all_issues = json.loads(result.stdout)

            # Filter by date if specified
            if since_date:
                try:
                    since_dt = \
                        datetime.fromisoformat(since_date.replace("Z", "+00:00"))
                    self.github_issues = [
                        issue
                        for issue in all_issues
                        if datetime.fromisoformat(
                            issue["updatedAt"].replace("Z", "+00:00")
                        )
                        >= since_dt
                    ]
                    if self.verbose:
                        print(
                            f"[OK] Filtered to {len(self.github_issues)} issues updated since {since_date}"
                        )
                except ValueError as e:
                    print(f"[ERROR] Invalid date format: {e}")
                    return False
            else:
                self.github_issues = all_issues

            if self.verbose:
                print(f"[OK] Fetched {len(self.github_issues)} GitHub issues")
            return True

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to fetch GitHub issues: {e}")
            print("Make sure 'gh' CLI is installed and authenticated")
            return False
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse GitHub response: {e}")
            return False

    def _gh_issue_state(self, number: int) -> Optional[str]:
        """Return cached GitHub state for an issue number, if available."""
        try:
            for it in self.github_issues:
                if it.get("number") == number:
                    return it.get("state")
        except Exception:
            return None
        return None

    def _close_github_issue_if_completed(self, issue_number: Optional[int], new_status: str) -> None:
        """Close GitHub issue when implementation status is completed/done (opt-in)."""
        if not getattr(self, "close_completed", False) or self.dry_run:
            return
        if not issue_number:
            return
        if new_status not in ("completed", "done"):
            return
        state = self._gh_issue_state(issue_number)
        if state and str(state).lower() == "closed":
            return
        try:
            subprocess.run([
                "gh", "issue", "close", str(issue_number),
                "-c", "Auto-closed by sync: implementation status set to completed"
            ], check=True)
            if self.verbose:
                print(f"  [CLOSED] GitHub issue #{issue_number} (status completed)")
        except subprocess.CalledProcessError as e:
            print(f"[WARN] Failed to close GitHub issue #{issue_number}: {e}")

    def get_issue_type_from_labels(self, labels: List[Dict]) -> str:
        """Determine issue type from labels."""
        label_names = [label.get("name", "").lower() for label in labels]

        if "epic" in label_names:
            return "epic"
        elif any("user-story" in label for label in label_names):
            return "user-story"
        elif any("defect" in label or "bug" in label for label in label_names):
            return "defect"
        else:
            return "unknown"

    def get_capability_id_from_labels(self, labels: List[Dict]) -> Optional[str]:
        """Extract capability ID from GitHub labels."""
        for label in labels:
            label_name = label.get("name", "")
            if label_name.startswith("capability/"):
                # Extract CAP-XXXXX from capability/CAP-00004
                capability_part = label_name.replace("capability/", "")
                if capability_part.startswith("CAP-"):
                    return capability_part
        return None

    def get_or_create_capability(self, capability_id: str) -> Optional[int]:
        """Get or create capability by ID, return the database ID."""
        capability = \
            self.db_session.query(Capability).filter_by(capability_id=capability_id).first()

        if not capability:
            # Create new capability with basic info
            capability_name = self.get_capability_name_from_id(capability_id)
            capability = Capability(
                capability_id=capability_id,
                name=capability_name,
                description=f"Auto-created from GitHub label {capability_id}"
            )
            self.db_session.add(capability)
            self.db_session.flush()  # Get the ID without committing

            if self.verbose:
                print(f"  [CREATED] Capability {capability_id}: {capability_name}")

        return capability.id

    def get_capability_name_from_id(self, capability_id: str) -> str:
        """Map capability ID to human-readable name."""
        capability_names = {
            "CAP-00001": "GitHub Integration",
            "CAP-00002": "Requirements Traceability",
            "CAP-00003": "Blog Platform",
            "CAP-00004": "GDPR Compliance"
        }
        return capability_names.get(capability_id, f"Capability {capability_id}")

    def sync_user_stories(self, epic_filter: Optional[str] = None) -> List[SyncResult]:
        """Sync user stories with GitHub issues."""
        results = []

        # Get all user stories from database
        query = self.db_session.query(UserStory)
        if epic_filter:
            # Filter by epic if specified
            epic = (
                self.db_session.query(Epic).filter(Epic.epic_id == epic_filter).first()
            )
            if epic:
                query = query.filter(UserStory.epic_id == epic.id)
            else:
                print(f"[WARNING] Epic {epic_filter} not found in database")
                return results

        user_stories = query.all()

        if self.verbose:
            print(f"Syncing {len(user_stories)} user stories...")

        for us in user_stories:
            # Find corresponding GitHub issue
            github_issue = None
            for issue in self.github_issues:
                if issue["number"] == us.github_issue_number:
                    github_issue = issue
                    break

            if not github_issue:
                results.append(
                    SyncResult(
                        entity_type="user_story",
                        entity_id=us.user_story_id,
                        github_issue_number=us.github_issue_number,
                        old_status=us.get_github_derived_status(),
                        new_status="N/A",
                        updated=False,
                        error="GitHub issue not found",
                    )
                )
                continue

            # Get current and new status
            old_status = us.get_github_derived_status()

            # Create updated GitHub data for status calculation
            old_github_state = us.github_issue_state
            old_github_labels = us.github_labels

            # Temporarily update to calculate new status
            us.github_issue_state = github_issue["state"]
            us.github_labels = str(github_issue.get("labels", []))
            new_status = us.get_github_derived_status()

            # Restore original values for now
            us.github_issue_state = old_github_state
            us.github_labels = old_github_labels

            # Check if update is needed
            needs_update = (
                old_status != new_status
                or us.github_issue_state != github_issue["state"]
                or us.github_labels != str(github_issue.get("labels", []))
                or us.implementation_status != new_status
            )

            if needs_update:
                if not self.dry_run:
                    # Use existing update method
                    us.update_from_github(github_issue)

                    # Track sync in GitHubSync table
                    self._track_sync_operation(
                        github_issue["number"],
                        "user_story",
                        "completed" if not self.dry_run else "pending",
                    )

                if self.verbose:
                    action = "[DRY-RUN]" if self.dry_run else "[UPDATED]"
                    print(
                        f"  {action} {us.user_story_id}: {old_status} -> {new_status}"
                    )

            results.append(
                SyncResult(
                    entity_type="user_story",
                    entity_id=us.user_story_id,
                    github_issue_number=us.github_issue_number,
                    old_status=old_status,
                    new_status=new_status,
                    updated=needs_update,
                )
            )

            # Optionally close the GitHub issue when implementation status is completed/done
            try:
                self._close_github_issue_if_completed(us.github_issue_number, new_status)
            except Exception as e:
                if self.verbose:
                    print(
                        f"  [WARN] close-if-completed"
                        f"failed for {us.user_story_id}: {e}"
                    )

        if not self.dry_run:
            self.db_session.commit()

        return results

    def sync_epics(self) -> List[SyncResult]:
        """Sync epics with GitHub issues."""
        results = []
        epics = self.db_session.query(Epic).all()

        if self.verbose:
            print(f"Syncing {len(epics)} epics...")

        for epic in epics:
            # Find corresponding GitHub issue
            github_issue = None
            for issue in self.github_issues:
                if issue["number"] == epic.github_issue_number:
                    github_issue = issue
                    break

            if not github_issue:
                results.append(
                    SyncResult(
                        entity_type="epic",
                        entity_id=epic.epic_id,
                        github_issue_number=epic.github_issue_number,
                        old_status=epic.status,
                        new_status="N/A",
                        updated=False,
                        error="GitHub issue not found",
                    )
                )
                continue

            # Simple status mapping for epics
            old_status = epic.status
            new_status = "completed" if github_issue["state"] == "closed" else "active"

            # Check capability assignment from labels
            old_capability_id = epic.capability_id
            new_capability_db_id = old_capability_id
            capability_label_id = None
            fallback_used = False
            capability_label_present = False

            labels = github_issue.get("labels", [])
            capability_from_label = self.get_capability_id_from_labels(labels)
            if capability_from_label:
                capability_label_id = capability_from_label
                capability_label_present = True
            else:
                default_capability = EPIC_TO_CAPABILITY_MAP.get(epic.epic_id)
                if default_capability:
                    capability_label_id = default_capability
                    fallback_used = True

            if capability_label_id:
                new_capability_db_id = \
                    self.get_or_create_capability(capability_label_id)

            # Check if status or capability needs update
            status_needs_update = old_status != new_status
            capability_needs_update = old_capability_id != new_capability_db_id
            needs_update = status_needs_update or capability_needs_update

            if needs_update:
                if not self.dry_run:
                    if status_needs_update:
                        epic.status = new_status
                    if capability_needs_update:
                        epic.capability_id = new_capability_db_id

                    # Track sync operation
                    self._track_sync_operation(
                        github_issue["number"],
                        "epic",
                        "completed" if not self.dry_run else "pending",
                    )

                if self.verbose:
                    action = "[DRY-RUN]" if self.dry_run else "[UPDATED]"
                    update_msg = f"  {action} {epic.epic_id}:"
                    if status_needs_update:
                        update_msg += f" status {old_status} -> {new_status}"
                    if capability_needs_update:
                        if old_capability_id:
                            if hasattr(self.db_session, "get"):
                                cap_old_obj = \
                                    self.db_session.get(Capability, old_capability_id)
                            else:
                                cap_old_obj = \
                                    self.db_session.query(Capability).get(old_capability_id)
                        else:
                            cap_old_obj = None
                        cap_old = cap_old_obj.capability_id if cap_old_obj else "None"
                        cap_new = capability_label_id if capability_label_id else "None"
                        update_msg += f" capability {cap_old} -> {cap_new}"
                    print(update_msg)

            if fallback_used and \
               not capability_label_present and capability_label_id:
                label_to_add = capability_label_name(capability_label_id)
                if self.verbose:
                    print(
                        f"  [INFO] {epic.epic_id}:"
                        f"missing GitHub label '{label_to_add}' for capability mapping"
                    )
                if epic.github_issue_number and not any(suggestion.get("epic_id") == epic.epic_id for suggestion in self.capability_label_suggestions):
                    capability_info = CAPABILITY_CATALOG.get(capability_label_id)
                    capability_name = capability_info.name if capability_info else capability_label_id
                    self.capability_label_suggestions.append(
                        {
                            "epic_id": epic.epic_id,
                            "github_issue_number": epic.github_issue_number,
                            "capability_id": capability_label_id,
                            "label": label_to_add,
                            "capability_name": capability_name,
                        }
                    )

            results.append(
                SyncResult(
                    entity_type="epic",
                    entity_id=epic.epic_id,
                    github_issue_number=epic.github_issue_number,
                    old_status=old_status,
                    new_status=new_status,
                    updated=needs_update,
                )
            )

        if not self.dry_run:
            self.db_session.commit()

        return results

    def sync_defects(self) -> List[SyncResult]:
        """Sync defects with GitHub issues."""
        results = []
        defects = self.db_session.query(Defect).all()

        if self.verbose:
            print(f"Syncing {len(defects)} defects...")

        for defect in defects:
            # Find corresponding GitHub issue
            github_issue = None
            for issue in self.github_issues:
                if (
                    hasattr(defect, "github_issue_number")
                    and issue["number"] == defect.github_issue_number
                ):
                    github_issue = issue
                    break

            if not github_issue:
                # Many defects might not have GitHub issues, that's OK
                continue

            old_status = defect.status
            # Map GitHub state to defect status
            new_status = "resolved" if github_issue["state"] == "closed" else "open"

            needs_update = old_status != new_status

            if needs_update:
                if not self.dry_run:
                    defect.status = new_status

                    # Track sync operation
                    self._track_sync_operation(
                        github_issue["number"],
                        "defect",
                        "completed" if not self.dry_run else "pending",
                    )

                if self.verbose:
                    action = "[DRY-RUN]" if self.dry_run else "[UPDATED]"
                    print(
                        f"  {action} {defect.defect_id}: {old_status} -> {new_status}"
                    )

            results.append(
                SyncResult(
                    entity_type="defect",
                    entity_id=getattr(defect, "defect_id", f"defect-{defect.id}"),
                    github_issue_number=getattr(defect, "github_issue_number", 0),
                    old_status=old_status,
                    new_status=new_status,
                    updated=needs_update,
                )
            )

        if not self.dry_run:
            self.db_session.commit()

        return results

    def _track_sync_operation(
        self, github_issue_number: int, issue_type: str, status: str
    ):
        """Track sync operation in GitHubSync table."""
        if self.dry_run:
            return

        # Check if sync record exists
        sync_record = (
            self.db_session.query(GitHubSync)
            .filter(
                GitHubSync.github_issue_number == github_issue_number,
                GitHubSync.github_issue_type == issue_type,
            )
            .first()
        )

        if sync_record:
            sync_record.sync_status = status
            sync_record.last_sync_time = datetime.now(timezone.utc)
            if status == "completed":
                sync_record.mark_sync_completed()
        else:
            # Create new sync record
            sync_record = GitHubSync(
                github_issue_number=github_issue_number,
                github_issue_type=issue_type,
                github_issue_title=f"Sync-{issue_type}-{github_issue_number}",
                sync_status=status,
                sync_source="manual",
            )
            self.db_session.add(sync_record)

    def validate_sync_results(self, results: List[SyncResult]) -> Tuple[int, int]:
        """Validate sync results and identify issues."""
        updated_count = sum(1 for r in results if r.updated)
        error_count = sum(1 for r in results if r.error)

        if self.verbose:
            print(f"\nSync Results Summary:")
            print(f"  Total entities: {len(results)}")
            print(f"  Updated: {updated_count}")
            print(f"  Errors: {error_count}")

            if error_count > 0:
                print(f"\nErrors encountered:")
                for result in results:
                    if result.error:
                        print(f"  {result.entity_id}: {result.error}")

        return updated_count, error_count

    def run_comprehensive_sync(
        self, epic_filter: Optional[str] = None, since_date: Optional[str] = None
    ) -> SyncSummary:
        """Run comprehensive sync of all entities."""
        print(
            f"{'[DRY-RUN] ' if self.dry_run else ''}Starting comprehensive GitHub sync..."
        )

        if epic_filter:
            print(f"Filtering by epic: {epic_filter}")
        if since_date:
            print(f"Only syncing issues updated since: {since_date}")

        # Fetch GitHub issues
        if not self.fetch_github_issues(since_date):
            return self.sync_summary

        # Sync each entity type
        all_results = []

        # Sync user stories
        us_results = self.sync_user_stories(epic_filter)
        all_results.extend(us_results)

        # Sync epics (unless filtering by specific epic)
        if not epic_filter:
            epic_results = self.sync_epics()
            all_results.extend(epic_results)

        # Sync defects
        defect_results = self.sync_defects()
        all_results.extend(defect_results)

        # Validate results
        updated_count, error_count = self.validate_sync_results(all_results)

        # Generate summary
        if self.capability_label_suggestions and self.verbose:
            print("\nCapability label suggestions:")
            for suggestion in self.capability_label_suggestions:
                gh_issue = suggestion.get("github_issue_number")
                label = suggestion.get("label")
                cap_name = suggestion.get("capability_name")
                epic_id = suggestion.get("epic_id")
                if gh_issue:
                    print(
                        f"  - {epic_id}: add"
                        f"'{label}' (\"{cap_name}\") to GitHub issue #{gh_issue}"
                    )
                else:
                    print(f"  - {epic_id}: add '{label}' (\"{cap_name}\")")
            print()

        self.sync_summary = SyncSummary(
            total_entities=len(all_results),
            updated_entities=updated_count,
            failed_entities=error_count,
            results=all_results,
        )

        return self.sync_summary

    def generate_progress_report(self) -> str:
        """Generate epic progress report after sync."""
        if not self.db_session:
            return "Database not available for progress report"

        report = []
        report.append("\n" + "=" * 60)
        report.append("EPIC PROGRESS REPORT (After Sync)")
        report.append("=" * 60)

        epics = self.db_session.query(Epic).all()
        for epic in epics:
            user_stories = [us for us in epic.user_stories]
            defects = []  # TODO: Add defects relationship if available

            total_items = len(user_stories) + len(defects)
            if total_items == 0:
                continue

            # Count completed items using the updated GitHub-derived status
            completed_user_stories = sum(
                1
                for us in user_stories
                if us.get_github_derived_status() in ["completed", "done"]
            )
            completed_defects = sum(
                1
                for d in defects
                if getattr(d, "status", "open") in ["closed", "resolved", "done"]
            )
            completed_items = completed_user_stories + completed_defects

            progress = \
                (completed_items / total_items * 100) if total_items > 0 else 0

            # Calculate story points
            total_story_points = sum(us.story_points or 0 for us in user_stories)
            completed_story_points = sum(
                us.story_points or 0
                for us in user_stories
                if us.get_github_derived_status() in ["completed", "done"]
            )

            report.append(f"\n{epic.epic_id}: {epic.title}")
            report.append(
                f"  Progress: {progress:.1f}% ({completed_items}/{total_items} items)"
            )
            report.append(
                f"  Story Points: {completed_story_points}/{total_story_points}"
            )
            report.append(
                f"  User Stories: {completed_user_stories}/{len(user_stories)} completed"
            )

        return "\n".join(report)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="GitHub to Database Sync Manager")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying them"
    )
    parser.add_argument("--epic", help="Sync only the specified epic (e.g., EP-00005)")
    parser.add_argument(
        "--since", help="Sync only issues updated since date (ISO format)"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Only validate current sync status"
    )
    parser.add_argument(
        "--progress-report", action="store_true", help="Generate epic progress report"
    )
    parser.add_argument("--quiet", action="store_true", help="Minimize output")
    parser.add_argument(
        "--close-completed",
        action="store_true",
        help=(
            "When a user story implementation status is completed/done, "
            "close its GitHub issue"
        ),
    )

    args = parser.parse_args()

    # Initialize sync manager
    sync_manager = GitHubSyncManager(
        dry_run=args.dry_run,
        verbose=not args.quiet,
        close_completed=args.close_completed,
    )

    if not sync_manager.initialize_database():
        sys.exit(1)

    try:
        if args.validate:
            # Just validate current state
            print("Validating current GitHub sync status...")
            # TODO: Implement validation-only mode
            print("Validation mode not yet implemented")
        elif args.progress_report:
            # Generate progress report only
            report = sync_manager.generate_progress_report()
            print(report)
        else:
            # Run comprehensive sync
            summary = sync_manager.run_comprehensive_sync(
                epic_filter=args.epic, since_date=args.since
            )

            # Print final summary
            print(
                f"\n{'[DRY-RUN] ' if args.dry_run else ''}Sync completed successfully!"
            )
            print(f"Total entities processed: {summary.total_entities}")
            print(f"Entities updated: {summary.updated_entities}")
            print(f"Errors: {summary.failed_entities}")

            # Generate progress report
            if not args.quiet:
                report = sync_manager.generate_progress_report()
                print(report)

    except KeyboardInterrupt:
        print("\nSync interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Sync failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

