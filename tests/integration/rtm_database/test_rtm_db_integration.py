"""
Integration tests for RTM Database CLI tool.

Tests CLI functionality with real database operations to ensure
the tool works end-to-end.

Related Issue: US-00055 - CLI tools for database RTM management
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from be.database import get_db_session
from be.models.traceability import Epic, UserStory


@pytest.mark.epic("EP-00005")
@pytest.mark.user_story("US-00055")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
@pytest.mark.test_category("undefined")
@pytest.mark.priority("undefined")
class TestRTMDatabaseCLIIntegration:
    """Integration tests for RTM Database CLI."""

    def setup_method(self):
        """Set up test database."""
        self.db = get_db_session()
        # Clean up any existing test data
        self.db.query(UserStory).delete()
        self.db.query(Epic).delete()
        self.db.commit()

    def teardown_method(self):
        """Clean up after each test."""
        self.db.query(UserStory).delete()
        self.db.query(Epic).delete()
        self.db.commit()
        self.db.close()

    def run_cli_command(self, *args):
        """Run CLI command and return result."""
        cmd = ["python", "tools/rtm-db.py"] + list(args)
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent
        )
        return result

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.test_type("integration")
    @pytest.mark.component("backend")
    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_cli_help(self):
        """Test CLI help command."""
        result = self.run_cli_command("--help")
        assert result.returncode == 0
        assert "RTM Database Management CLI" in result.stdout

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.test_type("integration")
    @pytest.mark.component("backend")
    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_admin_health_check(self):
        """Test database health check command."""
        result = self.run_cli_command("admin", "health-check")
        assert result.returncode == 0
        assert "Database connection successful" in result.stdout

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.test_type("integration")
    @pytest.mark.component("backend")
    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_create_and_query_epic(self):
        """Test creating and querying an Epic."""
        # Create epic
        result = self.run_cli_command(
            "entities",
            "create-epic",
            "--epic-id",
            "EP-INT-01",
            "--title",
            "Integration Test Epic",
            "--priority",
            "high",
            "--description",
            "Test epic for integration testing",
        )
        assert result.returncode == 0
        assert "Created Epic EP-INT-01" in result.stdout

        # Verify epic exists in database
        epic = self.db.query(Epic).filter(Epic.epic_id == "EP-INT-01").first()
        assert epic is not None
        assert epic.title == "Integration Test Epic"
        assert epic.priority == "high"

        # Query epics via CLI
        result = self.run_cli_command("query", "epics")
        assert result.returncode == 0
        assert "EP-INT-01" in result.stdout
        assert "Integration Test Epic" in result.stdout

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.test_type("integration")
    @pytest.mark.component("backend")
    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_create_user_story_with_epic(self):
        """Test creating User Story linked to Epic."""
        # Create parent epic first
        epic = Epic(epic_id="EP-INT-02", title="Parent Epic", priority="medium")
        self.db.add(epic)
        self.db.commit()

        # Create user story via CLI
        result = self.run_cli_command(
            "entities",
            "create-user-story",
            "--user-story-id",
            "US-INT-01",
            "--epic-id",
            "EP-INT-02",
            "--github-issue",
            "123",
            "--title",
            "Integration Test User Story",
            "--story-points",
            "5",
            "--priority",
            "high",
        )
        assert result.returncode == 0
        assert "Created User Story US-INT-01" in result.stdout

        # Verify user story exists and is linked to epic
        user_story = (
            self.db.query(UserStory)
            .filter(UserStory.user_story_id == "US-INT-01")
            .first()
        )
        assert user_story is not None
        assert user_story.epic_id == epic.id
        assert user_story.story_points == 5
        assert user_story.github_issue_number == 123

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.test_type("integration")
    @pytest.mark.component("backend")
    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_epic_progress_calculation(self):
        """Test Epic progress calculation."""
        # Create epic and user story
        epic = Epic(epic_id="EP-INT-03", title="Progress Test Epic")
        self.db.add(epic)
        self.db.flush()

        user_story = UserStory(
            user_story_id="US-INT-02",
            epic_id=epic.id,
            github_issue_number=456,
            title="Progress Test User Story",
            story_points=8,
            implementation_status="done",
        )
        self.db.add(user_story)
        self.db.commit()

        # Query progress via CLI
        result = self.run_cli_command("query", "epic-progress", "EP-INT-03")
        assert result.returncode == 0
        assert "Epic Progress Report: EP-INT-03" in result.stdout
        assert "8/8 (100.0%)" in result.stdout  # All story points completed

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.test_type("integration")
    @pytest.mark.component("backend")
    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_json_output_format(self):
        """Test JSON output format."""
        # Create test epic
        epic = Epic(epic_id="EP-JSON-01", title="JSON Test Epic", priority="low")
        self.db.add(epic)
        self.db.commit()

        # Query with JSON format
        result = self.run_cli_command("query", "epics", "--format", "json")
        assert result.returncode == 0

        # Verify JSON is valid and contains expected data
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["epic_id"] == "EP-JSON-01"
        assert data[0]["title"] == "JSON Test Epic"

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.test_type("integration")
    @pytest.mark.component("backend")
    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_data_export(self):
        """Test data export functionality."""
        # Create test data
        epic = Epic(epic_id="EP-EXPORT-01", title="Export Test Epic")
        self.db.add(epic)
        self.db.flush()

        user_story = UserStory(
            user_story_id="US-EXPORT-01",
            epic_id=epic.id,
            github_issue_number=789,
            title="Export Test User Story",
        )
        self.db.add(user_story)
        self.db.commit()

        # Export data to temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp:
            result = self.run_cli_command("data", "export", "--output", tmp.name)
            assert result.returncode == 0
            assert f"Exported RTM data to {tmp.name}" in result.stdout

            # Verify exported file contains correct data
            tmp_path = Path(tmp.name)
            assert tmp_path.exists()

            with open(tmp_path, "r") as f:
                export_data = json.load(f)
                assert "epics" in export_data
                assert "user_stories" in export_data
                assert "export_timestamp" in export_data
                assert len(export_data["epics"]) == 1
                assert len(export_data["user_stories"]) == 1
                assert export_data["epics"][0]["epic_id"] == "EP-EXPORT-01"

            # Cleanup
            tmp_path.unlink()

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.test_type("integration")
    @pytest.mark.component("backend")
    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_admin_validation(self):
        """Test database validation functionality."""
        # Create valid data
        epic = Epic(epic_id="EP-VALID-01", title="Valid Epic")
        self.db.add(epic)
        self.db.flush()

        user_story = UserStory(
            user_story_id="US-VALID-01",
            epic_id=epic.id,
            github_issue_number=999,
            title="Valid User Story",
        )
        self.db.add(user_story)
        self.db.commit()

        # Run validation
        result = self.run_cli_command("admin", "validate")
        assert result.returncode == 0
        assert "All validation checks passed" in result.stdout

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.test_type("integration")
    @pytest.mark.component("backend")
    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_create_epic_duplicate_error(self):
        """Test error handling for duplicate Epic creation."""
        # Create epic via database
        epic = Epic(epic_id="EP-DUP-01", title="Duplicate Test Epic")
        self.db.add(epic)
        self.db.commit()

        # Try to create duplicate via CLI
        result = self.run_cli_command(
            "entities",
            "create-epic",
            "--epic-id",
            "EP-DUP-01",
            "--title",
            "Another Epic",
        )
        assert result.returncode == 0
        assert "Epic EP-DUP-01 already exists" in result.stdout

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.test_type("integration")
    @pytest.mark.component("backend")
    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_user_story_epic_not_found(self):
        """Test error handling when parent Epic not found."""
        result = self.run_cli_command(
            "entities",
            "create-user-story",
            "--user-story-id",
            "US-ORPHAN-01",
            "--epic-id",
            "EP-NONEXISTENT",
            "--github-issue",
            "999",
            "--title",
            "Orphan User Story",
        )
        assert result.returncode == 0
        assert "Epic EP-NONEXISTENT not found" in result.stdout

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.test_type("integration")
    @pytest.mark.component("backend")
    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_verbose_mode(self):
        """Test verbose output mode."""
        result = self.run_cli_command(
            "--verbose",
            "entities",
            "create-epic",
            "--epic-id",
            "EP-VERBOSE-01",
            "--title",
            "Verbose Test Epic",
            "--priority",
            "medium",
        )
        assert result.returncode == 0
        assert "Created Epic EP-VERBOSE-01" in result.stdout
        # Verbose mode output would include additional details

    @pytest.mark.epic("EP-00005")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.test_type("integration")
    @pytest.mark.component("backend")
    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_cli_error_handling(self):
        """Test CLI error handling for invalid commands."""
        # Test invalid subcommand
        result = self.run_cli_command("invalid-command")
        assert result.returncode != 0

        # Test missing required parameters
        result = self.run_cli_command("entities", "create-epic")
        assert result.returncode != 0

    @pytest.mark.test_type("integration")
    @pytest.mark.component("backend")
    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    @pytest.mark.skipif(True, reason="Requires markdown test file")
    def test_import_rtm_functionality(self):
        """Test RTM import functionality (requires test markdown file)."""
        # This test would require creating a test markdown file
        # and testing the import functionality
        pass
