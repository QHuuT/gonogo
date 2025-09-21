"""
Requirements Traceability Matrix (RTM) Link Generator

Core engine for automating RTM link generation and validation.
Supports plugin architecture for extensibility.

Related Issue: US-00015 - Automated RTM link generation and validation
Epic: EP-00005 - RTM Automation
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import yaml


@dataclass
class RTMLink:
    """Represents a link in the RTM."""

    text: str
    url: str
    type: str  # 'epic', 'user_story', 'defect', 'bdd_scenario', 'file', 'gdpr'
    valid: bool = True
    error_message: Optional[str] = None


@dataclass
class RTMValidationResult:
    """Results of RTM validation."""

    total_links: int
    valid_links: int
    invalid_links: List[RTMLink] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class RTMLinkGenerator:
    """Core RTM link generator with plugin support."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize RTM link generator with configuration."""
        self.config = self._load_config(config_path)
        self.github_owner = self.config.get("github", {}).get("owner", "QHuuT")
        self.github_repo = self.config.get("github", {}).get("repo", "gonogo")
        self.link_patterns = self.config.get("link_patterns", {})

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "github": {"owner": "QHuuT", "repo": "gonogo"},
            "link_patterns": {
                "epic": "https://github.com/{owner}/{repo}/issues?q=is%3Aissue+{id}",
                "user_story": "https://github.com/{owner}/{repo}/issues?q=is%3Aissue+{id}",
                "defect": "https://github.com/{owner}/{repo}/issues?q=is%3Aissue+{id}",
                "gdpr": "../context/compliance/gdpr-requirements.md#{id}",
                "bdd_scenario": "../../{path}",
                "file": "../../{path}",
            },
            "validation": {
                "check_file_existence": True,
                "check_github_format": True,
                "require_https": False,
            },
        }

        if not config_path or not os.path.exists(config_path):
            return default_config

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
                # Merge with defaults
                config = default_config.copy()
                if user_config:
                    config.update(user_config)
                return config
        except Exception:
            # Return defaults if config loading fails
            return default_config

    def generate_github_issue_link(self, issue_id: str, bold: bool = False) -> str:
        """Generate GitHub issue search link."""
        # Determine issue type from ID
        if issue_id.startswith("EP-"):
            pattern = self.link_patterns.get("epic")
        elif issue_id.startswith("US-"):
            pattern = self.link_patterns.get("user_story")
        elif issue_id.startswith("DEF-"):
            pattern = self.link_patterns.get("defect")
        else:
            pattern = self.link_patterns.get("user_story")  # Default

        url = pattern.format(
            owner=self.github_owner, repo=self.github_repo, id=issue_id
        )

        text = f"**{issue_id}**" if bold else issue_id
        return f"[{text}]({url})"

    def generate_file_link(
        self, target_path: str, rtm_path: str, display_text: Optional[str] = None
    ) -> str:
        """Generate relative file link from RTM location."""
        # If it's an external URL, return as-is
        if target_path.startswith(("http://", "https://")):
            text = display_text or target_path
            return f"[{text}]({target_path})"

        # Calculate relative path
        rtm_dir = Path(rtm_path).parent
        target_full_path = Path(target_path)

        try:
            relative_path = os.path.relpath(target_path, rtm_dir)
            # Convert Windows paths to forward slashes for URLs
            relative_path = relative_path.replace("\\", "/")
        except ValueError:
            # If relative path calculation fails, use original path
            relative_path = target_path.replace("\\", "/")

        # Generate display text
        if display_text:
            text = display_text
        else:
            text = Path(target_path).name

        return f"[{text}]({relative_path})"

    def generate_bdd_scenario_link(
        self, feature_file: str, scenario_name: str, rtm_path: str
    ) -> str:
        """Generate BDD scenario link."""
        feature_name = Path(feature_file).stem
        display_text = f"{feature_name}.feature:{scenario_name}"
        return self.generate_file_link(feature_file, rtm_path, display_text)

    def extract_references_from_rtm(self, content: str) -> List[Tuple[str, str, str]]:
        """Extract all references from RTM content."""
        references = []

        # Pattern to match markdown links: [text](url)
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        matches = re.findall(link_pattern, content)

        for text, url in matches:
            # Determine link type based on content
            if re.match(r"^\*?\*?EP-\d{5}\*?\*?$", text):
                ref_type = "epic"
            elif re.match(r"^US-\d{5}$", text):
                ref_type = "user_story"
            elif re.match(r"^DEF-\d{5}$", text):
                ref_type = "defect"
            elif ".feature:" in text:
                ref_type = "bdd_scenario"
            elif "gdpr" in url.lower():
                ref_type = "gdpr"
            elif url.startswith(("http://", "https://")):
                ref_type = "external"
            else:
                ref_type = "file"

            references.append((text, url, ref_type))

        return references

    def validate_github_link(self, issue_id: str) -> bool:
        """Validate GitHub issue ID format."""
        # Valid formats: EP-00001, US-12345, DEF-67890
        patterns = [r"^EP-\d{5}$", r"^US-\d{5}$", r"^DEF-\d{5}$"]

        return any(re.match(pattern, issue_id) for pattern in patterns)

    def validate_file_link(self, file_path: str, rtm_path: str) -> bool:
        """Validate file link existence."""
        # External URLs are considered valid
        if file_path.startswith(("http://", "https://")):
            return True

        # Check if file exists relative to RTM location
        rtm_dir = Path(rtm_path).parent
        full_path = rtm_dir / file_path

        return full_path.exists()

    def validate_rtm_links(self, rtm_file_path: str) -> RTMValidationResult:
        """Validate all links in RTM file."""
        try:
            with open(rtm_file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return RTMValidationResult(
                total_links=0, valid_links=0, errors=[f"Failed to read RTM file: {e}"]
            )

        references = self.extract_references_from_rtm(content)
        total_links = len(references)
        valid_links = 0
        invalid_links = []
        warnings = []

        for text, url, ref_type in references:
            link = RTMLink(text=text, url=url, type=ref_type)

            # Validate based on type
            if ref_type in ["epic", "user_story", "defect"]:
                # Extract ID from text
                clean_text = text.replace("*", "")
                if self.validate_github_link(clean_text):
                    valid_links += 1
                else:
                    link.valid = False
                    link.error_message = f"Invalid GitHub issue format: {clean_text}"
                    invalid_links.append(link)

            elif ref_type == "file" or ref_type == "bdd_scenario":
                if self.validate_file_link(url, rtm_file_path):
                    valid_links += 1
                else:
                    link.valid = False
                    link.error_message = f"File not found: {url}"
                    invalid_links.append(link)

            else:
                # For other types (external, gdpr), assume valid
                valid_links += 1

        return RTMValidationResult(
            total_links=total_links,
            valid_links=valid_links,
            invalid_links=invalid_links,
            warnings=warnings,
        )

    def update_rtm_links(
        self, rtm_file_path: str, dry_run: bool = False
    ) -> Dict[str, int]:
        """Update RTM links to current format."""
        try:
            with open(rtm_file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return {"error": "Failed to read RTM file"}

        original_content = content
        updates = {
            "epic_links": 0,
            "user_story_links": 0,
            "defect_links": 0,
            "file_links": 0,
        }

        # Update GitHub issue links to current format
        def replace_github_link(match):
            text = match.group(1)
            old_url = match.group(2)

            # Extract issue ID from text
            clean_text = text.replace("*", "")

            if self.validate_github_link(clean_text):
                new_link = self.generate_github_issue_link(clean_text, "**" in text)

                # Count updates
                if clean_text.startswith("EP-"):
                    updates["epic_links"] += 1
                elif clean_text.startswith("US-"):
                    updates["user_story_links"] += 1
                elif clean_text.startswith("DEF-"):
                    updates["defect_links"] += 1

                # Extract just the URL from the new link
                new_url_match = re.search(r"\(([^)]+)\)$", new_link)
                if new_url_match:
                    return f"[{text}]({new_url_match.group(1)})"

            return match.group(0)  # Return original if no update

        # Replace GitHub issue links
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        content = re.sub(link_pattern, replace_github_link, content)

        # Write back if not dry run and content changed
        if not dry_run and content != original_content:
            try:
                with open(rtm_file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception:
                updates["error"] = "Failed to write updated RTM file"

        return updates

    def generate_validation_report(self, result: RTMValidationResult) -> str:
        """Generate human-readable validation report."""
        report = []
        report.append("RTM Link Validation Report")
        report.append("=" * 30)
        report.append("")

        # Summary
        report.append(f"Total Links: {result.total_links}")
        report.append(f"Valid Links: {result.valid_links}")
        report.append(f"Invalid Links: {len(result.invalid_links)}")

        if result.total_links > 0:
            health_score = (result.valid_links / result.total_links) * 100
            report.append(f"Health Score: {health_score:.1f}%")

        report.append("")

        # Invalid links
        if result.invalid_links:
            report.append("Invalid Links:")
            report.append("-" * 15)
            for link in result.invalid_links:
                report.append(f"- {link.text}: {link.error_message}")
            report.append("")

        # Errors
        if result.errors:
            report.append("Errors:")
            report.append("-" * 7)
            for error in result.errors:
                report.append(f"- {error}")
            report.append("")

        # Warnings
        if result.warnings:
            report.append("Warnings:")
            report.append("-" * 9)
            for warning in result.warnings:
                report.append(f"- {warning}")
            report.append("")

        return "\n".join(report)
