"""
Base Link Generator Plugin

Abstract base class for RTM link generators.
Provides interface for creating custom link generation logic.

Related Issue: US-00017 - Comprehensive testing and extensibility framework
Epic: EP-00005 - RTM Automation
"""

from abc import abstractmethod
from typing import Dict, Optional

from . import RTMPlugin


class BaseLinkGenerator(RTMPlugin):
    """Base class for RTM link generators."""

    @abstractmethod
    def can_handle(self, reference_type: str) -> bool:
        """
        Return True if this generator can handle the reference type.

        Args:
            reference_type: Type of reference (e.g., 'epic', 'user_story',
                'file')

        Returns:
            True if this generator handles the reference type
        """
        pass

    @abstractmethod
    def generate_link(self, reference: str, context: Dict) -> Optional[str]:
        """
        Generate clickable markdown link for the reference.

        Args:
            reference: The reference identifier (e.g., 'EP-00001',
                'auth.feature')
            context: Additional context information

        Returns:
            Markdown link string or None if cannot generate
        """
        pass

    def validate_link(self, reference: str, context: Dict) -> bool:
        """
        Validate that the reference exists and link is correct.

        Args:
            reference: The reference identifier
            context: Additional context information

        Returns:
            True if link is valid
        """
        return True  # Default implementation assumes valid

    def extract_id(self, reference: str) -> str:
        """
        Extract ID from reference string.

        Args:
            reference: Reference string (e.g., 'EP-00001')

        Returns:
            Extracted ID (e.g., '00001')
        """
        if "-" in reference:
            return reference.split("-", 1)[1]
        return reference

    def get_priority(self) -> int:
        """
        Get generator priority (higher = checked first).

        Returns:
            Priority value (0-100)
        """
        return 50  # Default priority


class GitHubIssueLinkGenerator(BaseLinkGenerator):
    """Default GitHub issue link generator."""

    @property
    def name(self) -> str:
        return "github_issues"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Generate links for GitHub issues (EP-XXXXX, US-XXXXX, DEF-XXXXX)"
        )

    def can_handle(self, reference_type: str) -> bool:
        """Handle GitHub issue types."""
        return reference_type in ["epic", "user_story", "defect"]

    def generate_link(self, reference: str, context: Dict) -> Optional[str]:
        """Generate GitHub issue search link."""
        config = context.get("config", {})
        github_config = config.get("github", {})

        owner = github_config.get("owner", "QHuuT")
        repo = github_config.get("repo", "gonogo")

        # Determine if bold formatting is needed (epics)
        bold = reference.startswith("EP-")

        url = (
            f"https://github.com/{owner}/{repo}/issues?q=is%3Aissue+"
            f"{reference}"
        )

        if bold:
            return f"[**{reference}**]({url})"
        else:
            return f"[{reference}]({url})"

    def validate_link(self, reference: str, context: Dict) -> bool:
        """Validate GitHub issue ID format."""
        import re

        pattern = r"^(EP|US|DEF)-\d{5}$"
        return bool(re.match(pattern, reference))


class BDDScenarioLinkGenerator(BaseLinkGenerator):
    """BDD scenario link generator."""

    @property
    def name(self) -> str:
        return "bdd_scenarios"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Generate links for BDD feature scenarios"

    def can_handle(self, reference_type: str) -> bool:
        """Handle BDD scenario references."""
        return reference_type == "bdd_scenario"

    def generate_link(self, reference: str, context: Dict) -> Optional[str]:
        """Generate BDD scenario link."""
        # Expected format: "feature-name.feature:scenario_name"
        if ":" not in reference:
            return None

        feature_file, scenario_name = reference.split(":", 1)

        # Build relative path
        rtm_file = context.get(
            "rtm_file", "docs/traceability/requirements-matrix.md"
        )
        rtm_dir = os.path.dirname(rtm_file)

        # Default BDD features location
        features_dir = context.get("bdd_features_dir", "tests/bdd/features")
        feature_path = os.path.join(features_dir, feature_file)

        # Calculate relative path
        import os

        try:
            relative_path = os.path.relpath(feature_path, rtm_dir)
            relative_path = relative_path.replace("\\", "/")
        except ValueError:
            relative_path = feature_path

        return f"[{reference}]({relative_path})"

    def validate_link(self, reference: str, context: Dict) -> bool:
        """Validate that BDD feature file exists."""
        if ":" not in reference:
            return False

        feature_file, _ = reference.split(":", 1)

        rtm_file = context.get(
            "rtm_file", "docs/traceability/requirements-matrix.md"
        )
        rtm_dir = os.path.dirname(rtm_file)
        features_dir = context.get("bdd_features_dir", "tests/bdd/features")
        feature_path = os.path.join(rtm_dir, features_dir, feature_file)

        import os

        return os.path.exists(feature_path)
