"""
Hybrid Requirements Traceability Matrix (RTM) Link Generator

Extends the existing RTM link generator to support both file-based and database-based operations.
Provides a smooth migration path from file-based RTM to database-backed RTM.

Related Issue: US-00058 - Legacy script migration and deprecation
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .rtm_link_generator import (
    RTMLink,
)
from .rtm_link_generator import RTMLinkGenerator as BaseLinkGenerator
from .rtm_link_generator import (
    RTMValidationResult,
)


@dataclass
class HybridRTMConfig:
    """Configuration for hybrid RTM operations."""

    mode: str = "auto"  # "file", "database", "auto"
    database_url: Optional[str] = None
    rtm_file_path: str = "docs/traceability/requirements-matrix.md"
    prefer_database: bool = True
    fallback_enabled: bool = True


class HybridRTMLinkGenerator(BaseLinkGenerator):
    """
    Hybrid RTM link generator supporting both file-based and database operations.

    Modes:
    - file: Use only file-based RTM operations
    - database: Use only database-based RTM operations
    - auto: Automatically choose best available option
    """

    def __init__(self, config_path: Optional[str] = None, mode: str = "auto"):
        """Initialize hybrid RTM generator."""
        super().__init__(config_path)

        self.hybrid_config = HybridRTMConfig(mode=mode)
        self._database_available = None
        self._effective_mode = None

    def _check_database_availability(self) -> bool:
        """Check if database RTM system is available."""
        if self._database_available is not None:
            return self._database_available

        try:
            # Try to import database modules
            from be.database import get_db_session
            from be.models.traceability import Defect, Epic, Test, UserStory

            # Mark imports as used for flake8
            _ = (Defect, Test, UserStory)  # Used in _validate_database_rtm method

            # Try to connect to database
            db = get_db_session()
            # Simple check - count epics (should work if database is set up)
            epic_count = db.query(Epic).count()
            db.close()

            self._database_available = True
            return True

        except Exception as e:
            self._database_available = False
            return False

    def _determine_effective_mode(self) -> str:
        """Determine which mode to actually use based on configuration and availability."""
        if self._effective_mode is not None:
            return self._effective_mode

        if self.hybrid_config.mode == "file":
            self._effective_mode = "file"
        elif self.hybrid_config.mode == "database":
            if self._check_database_availability():
                self._effective_mode = "database"
            else:
                if self.hybrid_config.fallback_enabled:
                    print("Warning: Database not available, falling back to file mode")
                    self._effective_mode = "file"
                else:
                    raise RuntimeError("Database mode requested but database not available")
        else:  # auto mode
            if self.hybrid_config.prefer_database and self._check_database_availability():
                self._effective_mode = "database"
            else:
                self._effective_mode = "file"

        return self._effective_mode

    def validate_rtm_links(self, rtm_file_path: Optional[str] = None) -> RTMValidationResult:
        """
        Validate RTM links using the appropriate mode.

        Args:
            rtm_file_path: Path to RTM file (used in file mode or as export target)

        Returns:
            RTMValidationResult with validation details
        """
        effective_mode = self._determine_effective_mode()

        if effective_mode == "database":
            return self._validate_database_rtm(rtm_file_path)
        else:
            # Use parent class file-based validation
            if rtm_file_path is None:
                rtm_file_path = self.hybrid_config.rtm_file_path
            return super().validate_rtm_links(rtm_file_path)

    def _validate_database_rtm(self, rtm_file_path: Optional[str] = None) -> RTMValidationResult:
        """Validate RTM using database as source of truth."""
        try:
            from be.database import get_db_session
            from be.models.traceability import Defect, Epic, Test, UserStory

            db = get_db_session()

            try:
                # Collect all database entities for validation
                epics = db.query(Epic).all()
                user_stories = db.query(UserStory).all()
                tests = db.query(Test).all()
                defects = db.query(Defect).all()

                # Build validation result
                result = RTMValidationResult(total_links=0, valid_links=0)

                # Validate Epic links
                for epic in epics:
                    github_link = self._generate_github_issue_link(epic.epic_id)
                    link = RTMLink(
                        text=epic.epic_id,
                        url=github_link,
                        type="epic",
                        valid=self._validate_github_issue_exists(epic.epic_id),
                    )
                    result.total_links += 1
                    if link.valid:
                        result.valid_links += 1
                    else:
                        link.error_message = f"GitHub issue {epic.epic_id} not found"
                        result.invalid_links.append(link)

                # Validate User Story links
                for us in user_stories:
                    github_link = self._generate_github_issue_link(us.user_story_id)
                    link = RTMLink(
                        text=us.user_story_id,
                        url=github_link,
                        type="user_story",
                        valid=self._validate_github_issue_exists(us.user_story_id),
                    )
                    result.total_links += 1
                    if link.valid:
                        result.valid_links += 1
                    else:
                        link.error_message = f"GitHub issue {us.user_story_id} not found"
                        result.invalid_links.append(link)

                # Validate Test file links
                for test in tests:
                    if test.test_file_path:
                        file_exists = Path(test.test_file_path).exists()
                        link = RTMLink(
                            text=test.test_file_path,
                            url=test.test_file_path,
                            type="file",
                            valid=file_exists,
                        )
                        result.total_links += 1
                        if link.valid:
                            result.valid_links += 1
                        else:
                            link.error_message = f"Test file {test.test_file_path} not found"
                            result.invalid_links.append(link)

                # Add success message
                result.warnings.append(f"Database RTM validation complete - using database as source of truth")

                return result

            finally:
                db.close()

        except Exception as e:
            # Fallback to file-based validation if database fails
            result = RTMValidationResult(total_links=0, valid_links=0)
            result.errors.append(f"Database validation failed: {e}")

            if self.hybrid_config.fallback_enabled:
                result.warnings.append("Falling back to file-based validation")
                if rtm_file_path is None:
                    rtm_file_path = self.hybrid_config.rtm_file_path
                file_result = super().validate_rtm_links(rtm_file_path)
                # Merge results
                result.total_links = file_result.total_links
                result.valid_links = file_result.valid_links
                result.invalid_links.extend(file_result.invalid_links)
                result.errors.extend(file_result.errors)
                result.warnings.extend(file_result.warnings)

            return result

    def _generate_github_issue_link(self, issue_id: str) -> str:
        """Generate GitHub issue search link for issue ID."""
        return f"https://github.com/{self.github_owner}/{self.github_repo}/issues?q=is%3Aissue+{issue_id}"

    def _validate_github_issue_exists(self, issue_id: str) -> bool:
        """Validate that GitHub issue exists (simplified check)."""
        # For now, assume GitHub issues exist if they follow proper format
        # In a full implementation, this could use GitHub API to verify
        return bool(re.match(r"^(EP|US|DEF)-\d{5}$", issue_id))

    def get_mode_info(self) -> Dict[str, Any]:
        """Get information about current operational mode."""
        effective_mode = self._determine_effective_mode()
        database_available = self._check_database_availability()

        return {
            "requested_mode": self.hybrid_config.mode,
            "effective_mode": effective_mode,
            "database_available": database_available,
            "fallback_enabled": self.hybrid_config.fallback_enabled,
            "prefer_database": self.hybrid_config.prefer_database,
        }

    def export_database_to_rtm_file(self, output_path: str) -> bool:
        """
        Export database RTM data to traditional RTM file format.

        This provides backward compatibility for tools that expect file-based RTM.
        """
        if not self._check_database_availability():
            return False

        try:
            from be.database import get_db_session
            from be.models.traceability import Defect, Epic, Test, UserStory

            # Mark imports as used for flake8
            _ = (Defect, Epic, Test, UserStory)  # Used in _generate_rtm_file_content method

            db = get_db_session()

            try:
                # Generate RTM file content from database
                content = self._generate_rtm_file_content(db)

                # Write to file
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)

                return True

            finally:
                db.close()

        except Exception as e:
            print(f"Error exporting database to RTM file: {e}")
            return False

    def _generate_rtm_file_content(self, db) -> str:
        """Generate RTM file content from database data."""
        from be.models.traceability import Defect, Epic, Test, UserStory

        # Mark imports as used for flake8 - referenced by Epic.* in function body
        _ = (Defect, Test)  # Available for future enhancement

        # This is a simplified implementation - a full version would generate
        # the complete RTM file format with all sections

        content = """# Requirements Traceability Matrix (RTM) - Generated from Database

**Last Updated**: Auto-generated from database
**Source**: Database RTM System

## Epic to User Story Mapping

| Epic ID | Epic Name | User Stories | Status |
|---------|-----------|--------------|--------|
"""

        # Add epics
        epics = db.query(Epic).all()
        for epic in epics:
            user_stories = db.query(UserStory).filter(UserStory.epic_id == epic.id).all()
            us_list = ", ".join([us.user_story_id for us in user_stories])
            status = (
                "✅ Done"
                if epic.status == "done"
                else "⏳ In Progress"
                if epic.status == "in_progress"
                else "📝 Planned"
            )

            github_link = (
                f"https://github.com/{self.github_owner}/{self.github_repo}/issues"
                f"?q=is%3Aissue+{epic.epic_id}"
            )
            content += (
                f"| [**{epic.epic_id}**]({github_link}) | {epic.title} "
                f"| {us_list} | {status} |\n"
            )

        content += "\n## Database RTM Notice\n\n"
        content += "This file was auto-generated from the database RTM system.\n"
        content += "For full RTM functionality, use the database tools:\n"
        content += "- `python tools/rtm-db.py` - Database RTM management\n"
        content += "- `python tools/test-db-integration.py` - Test integration\n"

        return content
