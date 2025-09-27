"""
GitHub Database Sync Simulator for testing.

Simulates the GitHub → Database synchronization logic from the GitHub Actions workflow
without requiring actual GitHub API calls.

Related Issue: US-00056 - GitHub Actions database integration
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import re
from datetime import datetime
from typing import Any, Dict, Optional

from src.be.models.traceability import Defect, Epic, GitHubSync, UserStory


class GitHubDatabaseSyncSimulator:
    """Simulates GitHub → Database synchronization for testing."""

    def __init__(self, issue_number: int = 1):
        """Initialize simulator with optional issue number."""
        self.issue_number = issue_number

    def parse_issue_type(self, issue_data: Dict[str, Any]) -> Optional[str]:
        """Determine issue type (Epic, User Story, Defect) from title and labels."""
        title = issue_data.get("title", "").upper()
        labels = [label["name"] for label in issue_data.get("labels", [])]

        if title.startswith("EP-") or "epic" in labels:
            return "epic"
        elif title.startswith("US-") or "user-story" in labels:
            return "user_story"
        elif title.startswith("DEF-") or "defect" in labels or "bug" in labels:
            return "defect"

        return None

    def extract_entity_id(self, title: str, entity_type: str) -> Optional[str]:
        """Extract entity ID from title (EP-XXXXX, US-XXXXX, DEF-XXXXX)."""
        patterns = {
            "epic": r"(EP-\d{5})",
            "user_story": r"(US-\d{5})",
            "defect": r"(DEF-\d{5})",
        }

        pattern = patterns.get(entity_type)
        if pattern:
            match = re.search(pattern, title.upper())
            return match.group(1) if match else None

        return None

    def parse_epic_reference(self, body: str) -> Optional[str]:
        """Extract parent epic reference from issue body."""
        match = re.search(
            r"\*?\*?Parent Epic\*?\*?[:\s]*EP-(\d{5})", body, re.IGNORECASE
        )
        return f"EP-{match.group(1)}" if match else None

    def parse_story_points(self, body: str) -> int:
        """Extract story points from issue body."""
        match = re.search(r"\*?\*?Story Points\*?\*?[:\s]*(\d+)", body, re.IGNORECASE)
        return int(match.group(1)) if match else 0

    def parse_priority(self, labels: list) -> str:
        """Extract priority from labels."""
        priority_map = {
            "priority/critical": "critical",
            "priority/high": "high",
            "priority/medium": "medium",
            "priority/low": "low",
        }

        for label in labels:
            if label in priority_map:
                return priority_map[label]

        return "medium"

    def parse_severity(self, labels: list) -> str:
        """Extract severity from labels (for defects)."""
        severity_map = {
            "severity/critical": "critical",
            "severity/high": "high",
            "severity/medium": "medium",
            "severity/low": "low",
        }

        for label in labels:
            if label in severity_map:
                return severity_map[label]

        return "medium"

    def sync_epic(self, db, issue_data: Dict[str, Any], entity_id: str) -> bool:
        """Sync Epic to database."""
        try:
            # Check if Epic already exists
            existing = db.query(Epic).filter(Epic.epic_id == entity_id).first()

            title = issue_data["title"]
            description = issue_data.get("body", "")
            labels = [label["name"] for label in issue_data.get("labels", [])]
            priority = self.parse_priority(labels)
            status = "completed" if issue_data["state"] == "closed" else "planned"

            if existing:
                # Update existing Epic
                existing.title = title
                existing.description = description
                existing.priority = priority
                existing.status = status
            else:
                # Create new Epic
                epic = Epic(
                    epic_id=entity_id,
                    title=title,
                    description=description,
                    priority=priority,
                    status=status,
                )
                db.add(epic)

            return True
        except Exception:
            return False

    def sync_user_story(self, db, issue_data: Dict[str, Any], entity_id: str) -> bool:
        """Sync User Story to database."""
        try:
            # Check if User Story already exists
            existing = (
                db.query(UserStory).filter(UserStory.user_story_id == entity_id).first()
            )

            title = issue_data["title"]
            description = issue_data.get("body", "")
            labels = [label["name"] for label in issue_data.get("labels", [])]
            priority = self.parse_priority(labels)
            story_points = self.parse_story_points(description)
            github_issue_number = issue_data["number"]

            # Find parent Epic
            epic_reference = self.parse_epic_reference(description)
            epic_id = None
            if epic_reference:
                epic = db.query(Epic).filter(Epic.epic_id == epic_reference).first()
                if epic:
                    epic_id = epic.id

            # Determine implementation status
            implementation_status = (
                "done" if issue_data["state"] == "closed" else "todo"
            )

            if existing:
                # Update existing User Story
                existing.title = title
                existing.description = description
                existing.priority = priority
                existing.story_points = story_points
                existing.implementation_status = implementation_status
                existing.github_issue_state = issue_data["state"]
                if epic_id:
                    existing.epic_id = epic_id
            else:
                # Only create User Story if we have a valid epic reference or no epic reference is needed
                if epic_id or not epic_reference:
                    user_story = UserStory(
                        user_story_id=entity_id,
                        epic_id=epic_id,
                        github_issue_number=github_issue_number,
                        github_issue_state=issue_data["state"],
                        title=title,
                        description=description,
                        story_points=story_points,
                        priority=priority,
                        implementation_status=implementation_status,
                    )
                    db.add(user_story)
                else:
                    # Epic reference was found but Epic doesn't exist in database
                    return False

            return True
        except Exception:
            return False

    def sync_defect(self, db, issue_data: Dict[str, Any], entity_id: str) -> bool:
        """Sync Defect to database."""
        try:
            # Check if Defect already exists
            existing = db.query(Defect).filter(Defect.defect_id == entity_id).first()

            title = issue_data["title"]
            description = issue_data.get("body", "")
            labels = [label["name"] for label in issue_data.get("labels", [])]
            priority = self.parse_priority(labels)
            severity = self.parse_severity(labels)
            github_issue_number = issue_data["number"]
            status = "resolved" if issue_data["state"] == "closed" else "open"

            # Determine defect type
            defect_type = "security" if "security" in labels else "bug"

            if existing:
                # Update existing Defect
                existing.title = title
                existing.description = description
                existing.priority = priority
                existing.severity = severity
                existing.status = status
                existing.defect_type = defect_type
            else:
                # Create new Defect
                defect = Defect(
                    defect_id=entity_id,
                    github_issue_number=github_issue_number,
                    title=title,
                    description=description,
                    severity=severity,
                    priority=priority,
                    status=status,
                    defect_type=defect_type,
                )
                db.add(defect)

            return True
        except Exception:
            return False

    def record_sync_status(self, db, success: bool, entity_id: Optional[str] = None):
        """Record sync operation status."""
        try:
            sync_record = GitHubSync(
                github_issue_number=self.issue_number,
                sync_status="completed" if success else "failed",
                last_sync_time=datetime.utcnow(),
                sync_errors=(
                    None
                    if success
                    else f"Failed to sync {entity_id or 'unknown entity'}"
                ),
            )
            db.add(sync_record)
        except Exception:
            pass
