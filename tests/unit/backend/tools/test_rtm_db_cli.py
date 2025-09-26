"""
Unit tests for RTM Database CLI tool.

Tests all CLI commands and database operations for the RTM management tool.

Related Issue: US-00055 - CLI tools for database RTM management
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import importlib.util
import json

# Import the CLI module
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

# Load CLI module directly to avoid import path issues
repo_root = Path(__file__).parent.parent.parent.parent.parent
cli_path = repo_root / "tools" / "rtm-db.py"

spec = importlib.util.spec_from_file_location("rtm_db_cli", cli_path)
rtm_db_cli = importlib.util.module_from_spec(spec)
sys.modules["rtm_db_cli"] = rtm_db_cli

# Mock the imports before loading the module
with patch.dict(
    "sys.modules",
    {
        "be.database": Mock(),
        "be.models.traceability": Mock(),
        "be.services.rtm_parser": Mock(),
        "rich.console": Mock(),
        "rich.table": Mock(),
        "rich.progress": Mock(),
    },
):
    spec.loader.exec_module(rtm_db_cli)


@pytest.mark.epic("EP-00005", "EP-99999")
@pytest.mark.user_story("US-00055")
@pytest.mark.component("backend")
class TestRTMDatabaseCLI:
    """Test RTM Database CLI functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.mock_db = Mock()
        self.mock_epic = Mock()
        self.mock_user_story = Mock()
        self.mock_test = Mock()
        self.mock_defect = Mock()

        # Configure mock objects
        self.mock_epic.epic_id = "EP-00005"
        self.mock_epic.title = "Test Epic"
        self.mock_epic.status = "planned"
        self.mock_epic.priority = "high"
        self.mock_epic.completion_percentage = 25.0
        self.mock_epic.to_dict.return_value = {
            "epic_id": "EP-00005",
            "title": "Test Epic",
            "status": "planned",
            "priority": "high",
        }

        self.mock_user_story.user_story_id = "US-00055"
        self.mock_user_story.title = "Test User Story"
        self.mock_user_story.epic_id = 1
        self.mock_user_story.github_issue_number = 55
        self.mock_user_story.implementation_status = "todo"
        self.mock_user_story.story_points = 8
        self.mock_user_story.to_dict.return_value = {
            "user_story_id": "US-00055",
            "title": "Test User Story",
            "implementation_status": "todo",
        }

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_create_epic_success(self, mock_get_db):
        """Test successful Epic creation."""
        mock_get_db.return_value = self.mock_db
        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            None  # No existing epic
        )

        result = self.runner.invoke(
            rtm_db_cli.cli,
            [
                "entities",
                "create-epic",
                "--epic-id",
                "EP-00005",
                "--title",
                "Test Epic",
                "--description",
                "Test Description",
                "--priority",
                "high",
            ],
        )

        assert result.exit_code == 0
        assert "Created Epic EP-00005" in result.output
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_create_epic_already_exists(self, mock_get_db):
        """Test Epic creation when epic already exists."""
        mock_get_db.return_value = self.mock_db
        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            self.mock_epic
        )

        result = self.runner.invoke(
            rtm_db_cli.cli,
            [
                "entities",
                "create-epic",
                "--epic-id",
                "EP-00005",
                "--title",
                "Test Epic",
            ],
        )

        assert result.exit_code == 0
        assert "Epic EP-00005 already exists" in result.output
        self.mock_db.add.assert_not_called()

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_create_user_story_success(self, mock_get_db):
        """Test successful User Story creation."""
        mock_get_db.return_value = self.mock_db

        # Mock epic lookup
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            self.mock_epic,  # Epic found
            None,  # User story doesn't exist
        ]

        result = self.runner.invoke(
            rtm_db_cli.cli,
            [
                "entities",
                "create-user-story",
                "--user-story-id",
                "US-00055",
                "--epic-id",
                "EP-00005",
                "--github-issue",
                "55",
                "--title",
                "Test User Story",
                "--story-points",
                "8",
            ],
        )

        assert result.exit_code == 0
        assert "Created User Story US-00055" in result.output
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_create_user_story_epic_not_found(self, mock_get_db):
        """Test User Story creation when parent Epic not found."""
        mock_get_db.return_value = self.mock_db
        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            None  # Epic not found
        )

        result = self.runner.invoke(
            rtm_db_cli.cli,
            [
                "entities",
                "create-user-story",
                "--user-story-id",
                "US-00055",
                "--epic-id",
                "EP-99999",
                "--github-issue",
                "55",
                "--title",
                "Test User Story",
            ],
        )

        assert result.exit_code == 0
        assert "Epic EP-99999 not found" in result.output
        self.mock_db.add.assert_not_called()

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_create_test_success(self, mock_get_db):
        """Test successful Test creation."""
        mock_get_db.return_value = self.mock_db
        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            self.mock_epic
        )

        result = self.runner.invoke(
            rtm_db_cli.cli,
            [
                "entities",
                "create-test",
                "--test-type",
                "unit",
                "--test-file",
                "tests/unit/test_example.py",
                "--title",
                "Test Example",
                "--epic-id",
                "EP-00005",
                "--function-name",
                "test_function",
            ],
        )

        assert result.exit_code == 0
        assert "Created Test: Test Example" in result.output
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_query_epics_table_format(self, mock_get_db):
        """Test querying Epics with table format."""
        mock_get_db.return_value = self.mock_db
        self.mock_db.query.return_value.all.return_value = [self.mock_epic]

        result = self.runner.invoke(rtm_db_cli.cli, ["query", "epics"])

        assert result.exit_code == 0
        # Note: Rich table output is complex to test, just verify no errors

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_query_epics_json_format(self, mock_get_db):
        """Test querying Epics with JSON format."""
        mock_get_db.return_value = self.mock_db
        self.mock_db.query.return_value.all.return_value = [self.mock_epic]

        result = self.runner.invoke(
            rtm_db_cli.cli, ["query", "epics", "--format", "json"]
        )

        assert result.exit_code == 0
        # Verify JSON is parseable
        try:
            json.loads(result.output.strip())
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_query_epics_with_filters(self, mock_get_db):
        """Test querying Epics with status and priority filters."""
        mock_get_db.return_value = self.mock_db
        mock_query = Mock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [self.mock_epic]

        result = self.runner.invoke(
            rtm_db_cli.cli,
            ["query", "epics", "--status", "planned", "--priority", "high"],
        )

        assert result.exit_code == 0
        # Verify filters were applied
        assert mock_query.filter.call_count == 2

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_query_user_stories(self, mock_get_db):
        """Test querying User Stories."""
        mock_get_db.return_value = self.mock_db
        self.mock_db.query.return_value.all.return_value = [self.mock_user_story]

        result = self.runner.invoke(rtm_db_cli.cli, ["query", "user-stories"])

        assert result.exit_code == 0

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_query_user_stories_by_epic(self, mock_get_db):
        """Test querying User Stories filtered by Epic."""
        mock_get_db.return_value = self.mock_db

        # Mock epic lookup query for epic-id filtering
        mock_epic_query = Mock()
        mock_epic_query.filter.return_value.first.return_value = self.mock_epic

        # Mock user story query
        mock_us_query = Mock()
        mock_us_query.filter.return_value = mock_us_query
        mock_us_query.all.return_value = [self.mock_user_story]

        # Mock epic lookup query for display (inside the loop)
        mock_epic_display_query = Mock()
        mock_epic_display_query.filter.return_value.first.return_value = self.mock_epic

        # Set up query side effects in order
        self.mock_db.query.side_effect = [
            mock_us_query,              # UserStory query (first call)
            mock_epic_query,            # Epic lookup by epic_id (second call)
            mock_epic_display_query,    # Epic lookup by id for display (third call, inside loop)
        ]

        result = self.runner.invoke(
            rtm_db_cli.cli, ["query", "user-stories", "--epic-id", "EP-00005"]
        )

        assert result.exit_code == 0

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_epic_progress_detailed(self, mock_get_db):
        """Test detailed Epic progress report."""
        mock_get_db.return_value = self.mock_db

        # Mock all the queries for progress calculation
        mock_epic_query = Mock()
        mock_us_query = Mock()
        mock_test_query = Mock()
        mock_defect_query = Mock()

        self.mock_db.query.side_effect = [
            mock_epic_query,  # Epic lookup
            mock_us_query,  # UserStory query
            mock_test_query,  # Test query
            mock_defect_query,  # Defect query
            mock_epic_query,  # Epic lookup for display
        ]

        mock_epic_query.filter.return_value.first.return_value = self.mock_epic
        mock_us_query.filter.return_value.all.return_value = [self.mock_user_story]
        mock_test_query.filter.return_value.all.return_value = []
        mock_defect_query.filter.return_value.all.return_value = []

        result = self.runner.invoke(
            rtm_db_cli.cli, ["query", "epic-progress", "EP-00005"]
        )

        assert result.exit_code == 0
        assert "Epic Progress Report" in result.output

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_epic_progress_not_found(self, mock_get_db):
        """Test Epic progress for non-existent Epic."""
        mock_get_db.return_value = self.mock_db
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.runner.invoke(
            rtm_db_cli.cli, ["query", "epic-progress", "EP-99999"]
        )

        assert result.exit_code == 0
        assert "Epic EP-99999 not found" in result.output

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_data_export_json(self, mock_get_db):
        """Test data export in JSON format."""
        mock_get_db.return_value = self.mock_db

        # Mock all entity queries
        mock_epic_query = Mock()
        mock_us_query = Mock()
        mock_defect_query = Mock()

        self.mock_db.query.side_effect = [
            mock_epic_query,
            mock_us_query,
            mock_defect_query,
        ]

        mock_epic_query.all.return_value = [self.mock_epic]
        mock_us_query.all.return_value = [self.mock_user_story]
        mock_defect_query.all.return_value = []

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp:
            result = self.runner.invoke(
                rtm_db_cli.cli, ["data", "export", "--output", tmp.name]
            )

            assert result.exit_code == 0
            assert f"Exported RTM data to {tmp.name}" in result.output

            # Verify file was created and contains valid JSON
            tmp_path = Path(tmp.name)
            assert tmp_path.exists()

            with open(tmp_path, "r") as f:
                data = json.load(f)
                assert "epics" in data
                assert "user_stories" in data
                assert "defects" in data
                assert "export_timestamp" in data

            # Cleanup (Windows-safe)
            try:
                tmp_path.unlink()
            except PermissionError:
                # Windows sometimes holds file handles, ignore cleanup errors
                pass

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_admin_health_check(self, mock_get_db):
        """Test database health check."""
        mock_get_db.return_value = self.mock_db

        # Mock count queries
        mock_query = Mock()
        self.mock_db.query.return_value = mock_query
        mock_query.count.side_effect = [
            5,
            10,
            15,
            3,
            2,
        ]  # Epic, US, Test, Defect, Sync counts
        mock_query.filter.return_value.count.side_effect = [0, 1]  # Orphaned counts

        result = self.runner.invoke(rtm_db_cli.cli, ["admin", "health-check"])

        assert result.exit_code == 0
        assert "Database connection successful" in result.output

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_admin_validate_no_issues(self, mock_get_db):
        """Test data validation with no issues found."""
        mock_get_db.return_value = self.mock_db

        # Mock queries for validation checks
        mock_query = Mock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value.all.return_value = []  # No orphaned records
        mock_query.all.return_value = [
            self.mock_epic,
            self.mock_user_story,
        ]  # Valid entities

        result = self.runner.invoke(rtm_db_cli.cli, ["admin", "validate"])

        assert result.exit_code == 0
        assert "All validation checks passed" in result.output

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_admin_validate_with_issues(self, mock_get_db):
        """Test data validation with issues found."""
        mock_get_db.return_value = self.mock_db

        # Mock orphaned records
        orphaned_us = Mock()
        orphaned_us.user_story_id = "US-ORPHAN"

        mock_query = Mock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value.all.side_effect = [
            [orphaned_us],  # Orphaned user stories
            [],  # Invalid GitHub issues
        ]
        mock_query.all.side_effect = [
            [self.mock_epic],  # Epics for duplicate check
            [self.mock_user_story],  # User stories for duplicate check
        ]

        result = self.runner.invoke(rtm_db_cli.cli, ["admin", "validate"])

        assert result.exit_code == 0
        assert "Found 1 validation issues" in result.output

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_admin_reset_without_confirm(self, mock_get_db):
        """Test database reset without confirmation."""
        result = self.runner.invoke(rtm_db_cli.cli, ["admin", "reset"])

        assert result.exit_code == 0
        assert "Use --confirm to proceed" in result.output

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_admin_reset_with_confirm(self, mock_get_db):
        """Test database reset with confirmation."""
        mock_get_db.return_value = self.mock_db

        # Mock query for deletion
        mock_query = Mock()
        self.mock_db.query.return_value = mock_query
        mock_query.delete.return_value = None

        result = self.runner.invoke(rtm_db_cli.cli, ["admin", "reset", "--confirm"])

        assert result.exit_code == 0
        assert "Database reset completed" in result.output
        self.mock_db.commit.assert_called_once()

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_github_sync_status_no_records(self, mock_get_db):
        """Test GitHub sync status with no records."""
        mock_get_db.return_value = self.mock_db

        mock_query = Mock()
        self.mock_db.query.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = []

        result = self.runner.invoke(rtm_db_cli.cli, ["github", "sync-status"])

        assert result.exit_code == 0
        assert "No sync records found" in result.output

    @patch("rtm_db_cli.get_db_session")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_github_sync_status_with_records(self, mock_get_db):
        """Test GitHub sync status with records."""
        mock_get_db.return_value = self.mock_db

        # Mock sync record
        mock_sync = Mock()
        mock_sync.github_issue_number = 55
        mock_sync.sync_status = "completed"
        mock_sync.last_sync_time = datetime(2025, 9, 21, 12, 0, 0)
        mock_sync.sync_errors = None

        mock_query = Mock()
        self.mock_db.query.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = [
            mock_sync
        ]

        result = self.runner.invoke(rtm_db_cli.cli, ["github", "sync-status"])

        assert result.exit_code == 0

    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_cli_help(self):
        """Test CLI help output."""
        result = self.runner.invoke(rtm_db_cli.cli, ["--help"])
        assert result.exit_code == 0
        assert "RTM Database Management CLI" in result.output

    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_entities_help(self):
        """Test entities subcommand help."""
        result = self.runner.invoke(rtm_db_cli.cli, ["entities", "--help"])
        assert result.exit_code == 0
        assert "Manage RTM entities" in result.output

    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_query_help(self):
        """Test query subcommand help."""
        result = self.runner.invoke(rtm_db_cli.cli, ["query", "--help"])
        assert result.exit_code == 0
        assert "Query and report on RTM data" in result.output

    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_data_help(self):
        """Test data subcommand help."""
        result = self.runner.invoke(rtm_db_cli.cli, ["data", "--help"])
        assert result.exit_code == 0
        assert "Data import, export, and migration operations" in result.output

    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_admin_help(self):
        """Test admin subcommand help."""
        result = self.runner.invoke(rtm_db_cli.cli, ["admin", "--help"])
        assert result.exit_code == 0
        assert "Database administration and maintenance" in result.output

    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_github_help(self):
        """Test github subcommand help."""
        result = self.runner.invoke(rtm_db_cli.cli, ["github", "--help"])
        assert result.exit_code == 0
        assert "GitHub integration and synchronization" in result.output

    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_verbose_mode(self):
        """Test verbose mode flag."""
        result = self.runner.invoke(rtm_db_cli.cli, ["--verbose", "--help"])
        assert result.exit_code == 0
        # Verbose mode should be enabled, but hard to test without actual operations

    @patch("rtm_db_cli.RTMDataMigrator")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_import_rtm_file_not_found(self, mock_migrator):
        """Test RTM import with non-existent file."""
        result = self.runner.invoke(
            rtm_db_cli.cli, ["data", "import-rtm", "/nonexistent/file.md"]
        )

        assert result.exit_code == 0
        assert "File /nonexistent/file.md not found" in result.output

    @patch("rtm_db_cli.RTMDataMigrator")
    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_import_rtm_dry_run(self, mock_migrator):
        """Test RTM import with dry run."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as tmp:
            tmp.write("# Test RTM File\n")
            tmp.flush()

            result = self.runner.invoke(
                rtm_db_cli.cli, ["data", "import-rtm", tmp.name, "--dry-run"]
            )

            assert result.exit_code == 0
            assert "DRY RUN" in result.output

            # Cleanup
            Path(tmp.name).unlink()


@pytest.mark.epic("EP-00005", "EP-99999")
@pytest.mark.user_story("US-00055")
@pytest.mark.component("backend")
class TestRTMDatabaseCLIIntegration:
    """Integration tests for RTM Database CLI with real database operations."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        # This would set up a real test database
        # For now, we'll use mocks in unit tests
        pass

    @pytest.mark.epic("EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00055")
    @pytest.mark.component("backend")
    def test_full_workflow_integration(self):
        """Test complete workflow: create epic -> create user story -> query progress."""
        # This would test the full CLI workflow with a real database
        # Implementation would depend on test database setup
        pass
