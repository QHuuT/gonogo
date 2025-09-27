"""
Base Validator Plugin

Abstract base class for RTM validators.
Provides interface for creating custom validation logic.

Related Issue: US-00017 - Comprehensive testing and extensibility framework
Epic: EP-00005 - RTM Automation
"""

from abc import abstractmethod
from typing import Dict, List

from . import RTMPlugin


class BaseValidator(RTMPlugin):
    """Base class for RTM validators."""

    @abstractmethod
    def validate_requirement(self, requirement: Dict) -> List[str]:
        """
        Validate a single requirement row.

        Args:
            requirement: Dictionary containing requirement data

        Returns:
            List of validation error messages (empty if valid)
        """
        pass

    def validate_cross_references(self, rtm_data: Dict) -> List[str]:
        """
        Validate cross-references between different RTM sections.

        Args:
            rtm_data: Complete RTM data structure

        Returns:
            List of validation error messages
        """
        return []  # Default: no cross-reference validation

    def validate_format(self, content: str) -> List[str]:
        """
        Validate RTM content format.

        Args:
            content: Raw RTM file content

        Returns:
            List of format validation errors
        """
        return []  # Default: no format validation

    def get_validation_priority(self) -> int:
        """
        Get validator priority (higher = run first).

        Returns:
            Priority value (0-100)
        """
        return 50  # Default priority


class StandardValidator(BaseValidator):
    """Standard RTM validation rules."""

    @property
    def name(self) -> str:
        return "standard_validation"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Standard RTM validation rules"

    def validate_requirement(self, requirement: Dict) -> List[str]:
        """Validate standard requirement fields."""
        errors = []

        # Check required fields
        required_fields = ["epic", "user_story", "status"]
        for field in required_fields:
            if not requirement.get(field):
                errors.append(f"Missing required field: {field}")

        # Validate status values
        valid_statuses = ["✅", "⏳", "📝", "❌", "⚠️"]
        status = requirement.get("status")
        if status and status not in valid_statuses:
            errors.append(f"Invalid status: {status}")

        # Validate epic format
        epic = requirement.get("epic")
        if epic:
            import re

            if not re.match(r"EP-\d{5}", epic):
                errors.append(f"Invalid epic format: {epic}")

        # Validate user story format
        user_story = requirement.get("user_story")
        if user_story:
            import re

            if not re.match(r"US-\d{5}", user_story):
                errors.append(f"Invalid user story format: {user_story}")

        return errors

    def validate_cross_references(self, rtm_data: Dict) -> List[str]:
        """Validate epic-to-user-story relationships."""
        errors = []

        epics = rtm_data.get("epics", {})
        requirements = rtm_data.get("requirements", [])

        # Check that all user stories reference valid epics
        referenced_epics = set()
        for req in requirements:
            epic = req.get("epic")
            if epic:
                referenced_epics.add(epic)

        # Check for orphaned epics
        defined_epics = set(epics.keys())
        orphaned = defined_epics - referenced_epics
        if orphaned:
            errors.append(
                f"Orphaned epics (not referenced): {sorted(orphaned)}"
            )

        # Check for undefined epics
        undefined = referenced_epics - defined_epics
        if undefined:
            errors.append(
                f"Undefined epics (referenced but not defined): "
                f"{sorted(undefined)}"
            )

        return errors


class FormatValidator(BaseValidator):
    """RTM format validation."""

    @property
    def name(self) -> str:
        return "format_validation"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "RTM markdown format validation"

    def validate_requirement(self, requirement: Dict) -> List[str]:
        """No requirement-level format validation."""
        return []

    def validate_format(self, content: str) -> List[str]:
        """Validate RTM markdown format."""
        errors = []

        lines = content.split("\n")

        # Check for required sections
        required_sections = [
            "# Requirements Traceability Matrix",
            "## Epic",
            "| Epic | User Story |",
        ]

        for section in required_sections:
            if not any(section in line for line in lines):
                errors.append(f"Missing required section: {section}")

        # Validate table structure
        table_headers_found = False
        for line in lines:
            if "| Epic | User Story |" in line:
                table_headers_found = True
                # Check if separator line follows
                next_line_idx = lines.index(line) + 1
                if next_line_idx < len(lines):
                    next_line = lines[next_line_idx]
                    if not next_line.startswith("|--"):
                        errors.append(
                            "Table header not followed by separator line"
                        )
                break

        if not table_headers_found:
            errors.append("No RTM table structure found")

        return errors

    def get_validation_priority(self) -> int:
        """Format validation should run first."""
        return 90
