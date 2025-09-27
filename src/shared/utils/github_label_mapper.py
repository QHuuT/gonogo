"""
GitHub Issue Label Mapper

Automatically assigns labels to GitHub issues based on template responses
and traceability matrix mappings. Follows GDPR compliance and project
management standards defined in the requirements matrix.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Import for database access
try:
    import sys

    sys.path.append("src")
    from be.database import SessionLocal
    from be.models.traceability.epic import Epic

    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logger.warning("Database models not available, falling back to static mappings")


@dataclass
class LabelMapping:
    """Represents a label mapping rule."""

    source_field: str
    source_value: str
    target_label: str
    priority: int = 0  # Higher priority mappings take precedence


@dataclass
class IssueData:
    """Structured representation of GitHub issue data."""

    title: str
    body: str
    existing_labels: List[str]
    issue_number: int


class DatabaseEpicMapper:
    """
    Retrieves epic mappings from the RTM database.

    Replaces file-based TraceabilityMatrixParser with real-time database queries.
    """

    def __init__(self) -> None:
        """Initialize the database epic mapper."""
        self._epic_mappings: Optional[Dict[str, Dict[str, str]]] = None

    def get_epic_mappings(self) -> Dict[str, Dict[str, str]]:
        """
        Extract epic-to-component mappings from RTM database.

        Returns:
            Dictionary mapping epic IDs to their properties
            Format: {"EP-00001": {"component": "frontend", "epic_label": "blog-content"}}
        """
        if self._epic_mappings is not None:
            return self._epic_mappings

        mappings = {}

        if not DATABASE_AVAILABLE:
            logger.warning("Database not available, using fallback mappings")
            return self._get_fallback_mappings()

        try:
            session = SessionLocal()
            epics = session.query(Epic).all()

            for epic in epics:
                # Get component (handle multiple components)
                component = epic.component if epic.component else "backend"
                if "," in component:
                    # Take the first component if multiple
                    component = component.split(",")[0].strip()

                # Get epic label name
                epic_label = epic.epic_label_name if epic.epic_label_name else epic.get_epic_label_name()

                mappings[epic.epic_id] = {
                    "component": component,
                    "epic_label": epic_label,
                }

            session.close()
            logger.info(f"Loaded {len(mappings)} epic mappings from database")

        except Exception as e:
            logger.error(f"Error loading epic mappings from database: {e}")
            mappings = self._get_fallback_mappings()

        self._epic_mappings = mappings
        return mappings

    def _get_fallback_mappings(self) -> Dict[str, Dict[str, str]]:
        """Fallback epic mappings when database is unavailable."""
        return {
            "EP-00001": {"component": "frontend", "epic_label": "blog-content"},
            "EP-00002": {"component": "backend", "epic_label": "comment-system"},
            "EP-00003": {"component": "security", "epic_label": "privacy-consent"},
            "EP-00004": {"component": "ci-cd", "epic_label": "github-workflow"},
            "EP-00005": {"component": "backend", "epic_label": "rtm"},
            "EP-00006": {"component": "ci-cd", "epic_label": "github-project"},
            "EP-00007": {"component": "testing", "epic_label": "test-reporting"},
        }


class TraceabilityMatrixParser:
    """Parses the requirements traceability matrix for epic mappings."""

    def __init__(self, matrix_path: Path) -> None:
        """Initialize with path to traceability matrix file."""
        self.matrix_path = matrix_path
        self._epic_mappings: Optional[Dict[str, Dict[str, str]]] = None

    def get_epic_mappings(self) -> Dict[str, Dict[str, str]]:
        """
        Extract epic-to-component mappings from traceability matrix.

        Returns:
            Dictionary mapping epic IDs to their properties
            Format: {"EP-001": {"component": "frontend", "epic_label": "blog-content"}}
        """
        if self._epic_mappings is not None:
            return self._epic_mappings

        mappings = {}

        try:
            if not self.matrix_path.exists():
                logger.warning(f"Traceability matrix not found: {self.matrix_path}")
                return self._get_default_mappings()

            content = self.matrix_path.read_text(encoding="utf-8")

            # Extract epic mappings from matrix content
            # This is a simplified parser - in production, you'd want more robust parsing
            epic_pattern = r"\*\*EP-(\d+)\*\*[^|]*\|\s*([^|]+?)\s*\|"
            matches = re.findall(epic_pattern, content, re.MULTILINE)

            for epic_num, description in matches:
                epic_id = f"EP-{epic_num.zfill(5)}"
                mappings[epic_id] = self._determine_component_from_description(description)

            # Fallback to default mappings if parsing fails
            if not mappings:
                mappings = self._get_default_mappings()

        except Exception as e:
            logger.error(f"Error parsing traceability matrix: {e}")
            mappings = self._get_default_mappings()

        self._epic_mappings = mappings
        return mappings

    def _get_default_mappings(self) -> Dict[str, Dict[str, str]]:
        """Default epic mappings as fallback."""
        return {
            "EP-00001": {"component": "frontend", "epic_label": "blog-content"},
            "EP-00002": {"component": "backend", "epic_label": "comment-system"},
            "EP-00003": {"component": "gdpr", "epic_label": "privacy-consent"},
            "EP-00004": {"component": "ci-cd", "epic_label": "github-workflow"},
        }

    def _determine_component_from_description(self, description: str) -> Dict[str, str]:
        """Determine component and epic label from epic description."""
        desc_lower = description.lower()

        if "blog" in desc_lower or "content" in desc_lower:
            return {"component": "frontend", "epic_label": "blog-content"}
        elif "comment" in desc_lower:
            return {"component": "backend", "epic_label": "comment-system"}
        elif "gdpr" in desc_lower or "privacy" in desc_lower:
            return {"component": "gdpr", "epic_label": "privacy-consent"}
        elif "github" in desc_lower or "workflow" in desc_lower:
            return {"component": "ci-cd", "epic_label": "github-workflow"}
        else:
            return {"component": "backend", "epic_label": "general"}


class GitHubIssueLabelMapper:
    """
    Maps GitHub issue template responses to appropriate labels.

    This class implements the automatic labeling logic based on:
    - Priority levels from templates
    - Epic-to-component mappings from traceability matrix
    - GDPR considerations
    - Release planning rules
    - Status management
    """

    def __init__(self, matrix_path: Optional[Path] = None, use_database: bool = True) -> None:
        """Initialize the label mapper."""
        if use_database and DATABASE_AVAILABLE:
            self.epic_mapper = DatabaseEpicMapper()
            logger.info("Using database epic mapper for dynamic label mapping")
        else:
            # Fallback to file-based parser
            if matrix_path is None:
                matrix_path = Path("docs/traceability/requirements-matrix.md")
            self.epic_mapper = TraceabilityMatrixParser(matrix_path)
            logger.info("Using file-based epic mapper (fallback)")
        self.priority_mappings = {
            "Critical": "priority/critical",
            "High": "priority/high",
            "Medium": "priority/medium",
            "Low": "priority/low",
        }

    def extract_form_value(self, issue_body: str, field_name: str) -> Optional[str]:
        """
        Extract form field value from GitHub issue body.

        Args:
            issue_body: The issue body text
            field_name: Name of the form field to extract

        Returns:
            The extracted value or None if not found
        """
        patterns = [
            rf"### {re.escape(field_name)}\s*\n\s*([^\n#]+)",
            rf"\*\*{re.escape(field_name)}\*\*[:\s]*([^\n]+)",
            rf"{re.escape(field_name)}[:\s]*([^\n]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, issue_body, re.IGNORECASE | re.MULTILINE)
            if match and match.group(1).strip() != "_No response_":
                return match.group(1).strip()

        return None

    def map_priority_labels(self, issue_data: IssueData) -> Set[str]:
        """Map priority dropdown to priority labels."""
        labels = set()
        priority = self.extract_form_value(issue_data.body, "Priority")

        if priority and priority in self.priority_mappings:
            labels.add(self.priority_mappings[priority])
            logger.info(f"Mapped priority '{priority}' to label")

        return labels

    def map_epic_labels(self, issue_data: IssueData) -> Set[str]:
        """Map epic information to component and epic labels."""
        labels: Set[str] = set()

        # Try multiple field names for epic reference
        epic_fields = ["Epic ID", "Parent Epic", "epic-id", "epic-link"]
        epic_id = None

        for field in epic_fields:
            epic_id = self.extract_form_value(issue_data.body, field)
            if epic_id:
                break

        if not epic_id:
            return labels

        # Extract EP-XXX pattern
        epic_match = re.search(r"EP-0*(\d+)", epic_id, re.IGNORECASE)
        if not epic_match:
            logger.warning(f"Invalid epic ID format: {epic_id}")
            return labels

        # Normalize epic ID format
        epic_num = int(epic_match.group(1))
        normalized_epic_id = f"EP-{epic_num:05d}"

        # Get mappings from epic mapper (database or file-based)
        epic_mappings = self.epic_mapper.get_epic_mappings()

        if normalized_epic_id in epic_mappings:
            mapping = epic_mappings[normalized_epic_id]

            # Add component label
            if "component" in mapping:
                labels.add(f"component/{mapping['component']}")

            # Add epic label
            if "epic_label" in mapping:
                labels.add(f"epic/{mapping['epic_label']}")

            logger.info(f"Mapped epic {normalized_epic_id} to labels: {labels}")
        else:
            logger.warning(f"No mapping found for epic: {normalized_epic_id}")

        return labels

    def map_gdpr_labels(self, issue_data: IssueData) -> Set[str]:
        """Map GDPR considerations to GDPR labels."""
        labels = set()
        body_lower = issue_data.body.lower()

        gdpr_mappings = {
            "gdpr/personal-data": [
                "involves personal data processing",
                "personal data processing",
                "processes personal data",
            ],
            "gdpr/consent-required": [
                "requires user consent",
                "data collection requires user consent",
                "gdpr compliance review required",
            ],
            "gdpr/privacy-review": [
                "privacy impact assessment needed",
                "privacy impact assessment",
            ],
            "gdpr/data-retention": ["data retention policies apply", "data retention"],
        }

        for label, keywords in gdpr_mappings.items():
            for keyword in keywords:
                if keyword.lower() in body_lower:
                    labels.add(label)
                    logger.info(f"Added GDPR label {label} based on keyword: {keyword}")
                    break

        return labels

    def map_release_labels(self, issue_data: IssueData) -> Set[str]:
        """
        Map issues to release labels based on priority and epic.

        Business rules:
        - Critical priority -> MVP
        - EP-002 (Comments) and EP-003 (GDPR) -> MVP (critical for compliance)
        - High priority -> v1.1
        - Medium/Low -> v1.2
        """
        labels = set()

        priority = self.extract_form_value(issue_data.body, "Priority")
        epic_id = self.extract_form_value(issue_data.body, "Epic ID") or self.extract_form_value(
            issue_data.body, "Parent Epic"
        )

        # Critical items go to MVP
        if priority == "Critical":
            labels.add("release/mvp")
            return labels

        # GDPR and Comment epics are MVP-critical
        if epic_id:
            epic_match = re.search(r"EP-0*([23])", epic_id, re.IGNORECASE)
            if epic_match:
                labels.add("release/mvp")
                return labels

        # High priority goes to v1.1
        if priority == "High":
            labels.add("release/v1.1")
        else:
            # Medium/Low goes to v1.2
            labels.add("release/v1.2")

        return labels

    def map_status_labels(self, issue_data: IssueData) -> Set[str]:
        """Map initial status based on issue content."""
        labels: Set[str] = set()

        # Don't override existing status labels
        existing_status = {label for label in issue_data.existing_labels if label.startswith("status/")}
        if existing_status:
            return labels

        body_lower = issue_data.body.lower()

        # Check for readiness indicators
        ready_indicators = [
            "ready for development",
            "ready to implement",
            "refined and ready",
        ]

        progress_indicators = [
            "in progress",
            "currently working",
            "started implementation",
        ]

        blocked_indicators = ["blocked by", "waiting for", "dependency not met"]

        if any(indicator in body_lower for indicator in blocked_indicators):
            labels.add("status/blocked")
        elif any(indicator in body_lower for indicator in progress_indicators):
            labels.add("status/in-progress")
        elif any(indicator in body_lower for indicator in ready_indicators):
            labels.add("status/ready")
        else:
            labels.add("status/backlog")

        return labels

    def generate_labels(self, issue_data: IssueData) -> List[str]:
        """
        Generate all appropriate labels for an issue.

        Args:
            issue_data: Structured issue information

        Returns:
            List of label names to apply to the issue
        """
        all_labels = set(issue_data.existing_labels)

        try:
            # Apply all mapping rules
            all_labels.update(self.map_priority_labels(issue_data))
            all_labels.update(self.map_epic_labels(issue_data))
            all_labels.update(self.map_gdpr_labels(issue_data))
            all_labels.update(self.map_release_labels(issue_data))
            all_labels.update(self.map_status_labels(issue_data))

            # Remove needs-triage if we've added meaningful labels
            if len(all_labels) > len(issue_data.existing_labels):
                all_labels.discard("needs-triage")

            logger.info(f"Generated labels for issue #{issue_data.issue_number}: {all_labels}")

        except Exception as e:
            logger.error(f"Error generating labels for issue #{issue_data.issue_number}: {e}")
            # Return original labels on error
            return issue_data.existing_labels

        return sorted(list(all_labels))
