"""
Integration tests for RTM Test-Database Integration workflow.

Tests the complete workflow of test discovery, database sync, and execution tracking.

Related Issue: US-00057 - Test execution integration with database
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from be.database import get_db_session
from be.models.traceability import Defect, Epic, Test, UserStory
from shared.testing.database_integration import (
    BDDScenarioParser,
    TestDatabaseSync,
    TestDiscovery,
    TestExecutionTracker,
)


class TestDatabaseIntegrationWorkflow:
    """Integration tests for complete test-database integration workflow."""

    def setup_method(self):
        """Set up test database."""
        self.db = get_db_session()
        # Clean up test data
        self.db.query(Test).delete()
        self.db.query(Defect).delete()
        self.db.query(UserStory).delete()
        self.db.query(Epic).delete()
        self.db.commit()

    def teardown_method(self):
        """Clean up after tests."""
        self.db.query(Test).delete()
        self.db.query(Defect).delete()
        self.db.query(UserStory).delete()
        self.db.query(Epic).delete()
        self.db.commit()
        self.db.close()

    def test_test_discovery_and_sync_workflow(self):
        """Test complete test discovery and database sync workflow."""
        # Create test Epic for linking
        epic = Epic(
            epic_id="EP-00057", title="Test Execution Integration", status="in_progress"
        )
        self.db.add(epic)
        self.db.commit()

        # Create temporary test file with Epic reference
        test_content = '''
"""
Test file for EP-00057 functionality.
"""

def test_database_integration():
    """Test database integration functionality - EP-00057."""
    assert True

def test_another_function():
    """Another test without Epic reference."""
    assert True
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            tmp.write(test_content)
            tmp.flush()
            tmp_path = Path(tmp.name)

            try:
                # Test discovery
                discovery = TestDiscovery()
                with patch.object(discovery, "discover_tests") as mock_discover:
                    mock_discover.return_value = [
                        {
                            "test_file_path": str(tmp_path.relative_to(Path.cwd())),
                            "test_function_name": "test_database_integration",
                            "test_type": "unit",
                            "title": "Test: Database Integration",
                            "line_number": 6,
                            "epic_references": ["EP-00057"],
                            "user_story_references": [],
                            "defect_references": [],
                            "bdd_scenario_name": None,
                        },
                        {
                            "test_file_path": str(tmp_path.relative_to(Path.cwd())),
                            "test_function_name": "test_another_function",
                            "test_type": "unit",
                            "title": "Test: Another Function",
                            "line_number": 10,
                            "epic_references": [],
                            "user_story_references": [],
                            "defect_references": [],
                            "bdd_scenario_name": None,
                        },
                    ]

                    # Test sync
                    sync = TestDatabaseSync()
                    stats = sync.sync_tests_to_database()

                    assert stats["discovered"] == 2
                    assert stats["created"] == 2
                    assert stats["linked_to_epics"] == 1  # Only one has Epic reference

                # Verify tests were created in database
                tests = self.db.query(Test).all()
                assert len(tests) == 2

                # Verify Epic linking
                linked_test = (
                    self.db.query(Test)
                    .filter(Test.test_function_name == "test_database_integration")
                    .first()
                )
                assert linked_test is not None
                assert linked_test.epic_id == epic.id

                unlinked_test = (
                    self.db.query(Test)
                    .filter(Test.test_function_name == "test_another_function")
                    .first()
                )
                assert unlinked_test is not None
                assert unlinked_test.epic_id is None

            finally:
                tmp_path.unlink()

    def test_test_execution_tracking_workflow(self):
        """Test test execution result tracking workflow."""
        # Create test Epic and Test records
        epic = Epic(epic_id="EP-00057", title="Test Integration")
        self.db.add(epic)
        self.db.flush()

        test = Test(
            test_type="unit",
            test_file_path="tests/unit/test_example.py",
            test_function_name="test_example",
            title="Test: Example",
            epic_id=epic.id,
        )
        self.db.add(test)
        self.db.commit()

        # Test execution tracking
        tracker = TestExecutionTracker()
        tracker.start_test_session()

        try:
            # Record successful test
            result = tracker.record_test_result(
                "tests/unit/test_example.py::test_example", "passed", 120.5
            )
            assert result is True

            # Record failed test (should create defect)
            defect_id = tracker.create_defect_from_failure(
                "tests/unit/test_example.py::test_example",
                "AssertionError: Test assertion failed",
                "Traceback (most recent call last):\n  File test.py, line 1, in test\n    assert False",
            )
            assert defect_id is not None

            tracker.end_test_session()

            # Verify test result was recorded
            updated_test = self.db.query(Test).filter(Test.id == test.id).first()
            assert updated_test.last_execution_status == "passed"
            assert updated_test.last_execution_duration_ms == 120.5

            # Verify defect was created
            defect = self.db.query(Defect).filter(Defect.defect_id == defect_id).first()
            assert defect is not None
            assert defect.test_id == test.id
            assert defect.epic_id == epic.id
            assert defect.defect_type == "test_failure"
            assert "AssertionError" in defect.description

        finally:
            tracker.end_test_session()

    def test_bdd_scenario_linking_workflow(self):
        """Test BDD scenario to User Story linking workflow."""
        # Create test Epic and User Story
        epic = Epic(epic_id="EP-00057", title="Test Integration")
        self.db.add(epic)
        self.db.flush()

        user_story = UserStory(
            user_story_id="US-00057",
            epic_id=epic.id,
            github_issue_number=57,
            title="Test execution integration with database",
            story_points=8,
        )
        self.db.add(user_story)
        self.db.commit()

        # Create temporary BDD feature file
        feature_content = """
# Related to US-00057
Feature: Test Database Integration

  Background:
    Given the RTM database is configured

  Scenario: Test discovery and sync
    Given test files exist with Epic references
    When the discovery process runs
    Then tests are synced to the database
    And they are linked to the correct Epics

  Scenario: Test execution tracking
    Given tests are registered in the database
    When tests are executed with failures
    Then defects are automatically created
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".feature", delete=False
        ) as tmp:
            tmp.write(feature_content)
            tmp.flush()
            tmp_path = Path(tmp.name)

            try:
                # Test BDD scenario parsing and linking
                bdd_parser = BDDScenarioParser()
                with patch.object(bdd_parser, "parse_feature_files") as mock_parse:
                    mock_parse.return_value = [
                        {
                            "feature_file": str(tmp_path.relative_to(Path.cwd())),
                            "scenario_name": "Test discovery and sync",
                            "line_number": 8,
                            "user_story_references": ["US-00057"],
                            "test_type": "bdd",
                        },
                        {
                            "feature_file": str(tmp_path.relative_to(Path.cwd())),
                            "scenario_name": "Test execution tracking",
                            "line_number": 14,
                            "user_story_references": ["US-00057"],
                            "test_type": "bdd",
                        },
                    ]

                    # Link scenarios
                    stats = bdd_parser.link_scenarios_to_user_stories()

                    assert stats["scenarios_found"] == 2
                    assert stats["scenarios_linked"] == 2

                # Verify BDD test records were created
                bdd_tests = self.db.query(Test).filter(Test.test_type == "bdd").all()
                assert len(bdd_tests) == 2

                # Verify Epic linking through User Story
                for bdd_test in bdd_tests:
                    assert bdd_test.epic_id == epic.id

            finally:
                tmp_path.unlink()

    def test_end_to_end_integration_workflow(self):
        """Test complete end-to-end integration workflow."""
        # Create Epic and User Story
        epic = Epic(epic_id="EP-00057", title="Test Integration Epic")
        self.db.add(epic)
        self.db.flush()

        user_story = UserStory(
            user_story_id="US-00057",
            epic_id=epic.id,
            github_issue_number=57,
            title="Database Integration User Story",
        )
        self.db.add(user_story)
        self.db.commit()

        # Step 1: Test Discovery and Sync
        discovery = TestDiscovery()
        sync = TestDatabaseSync()

        with patch.object(discovery, "discover_tests") as mock_discover:
            mock_discover.return_value = [
                {
                    "test_file_path": "tests/integration/test_workflow.py",
                    "test_function_name": "test_end_to_end_workflow",
                    "test_type": "integration",
                    "title": "Test: End To End Workflow",
                    "epic_references": ["EP-00057"],
                    "user_story_references": ["US-00057"],
                    "defect_references": [],
                    "bdd_scenario_name": None,
                }
            ]

            sync_stats = sync.sync_tests_to_database()
            assert sync_stats["created"] == 1
            assert sync_stats["linked_to_epics"] == 1

        # Step 2: BDD Scenario Linking
        bdd_parser = BDDScenarioParser()
        with patch.object(bdd_parser, "parse_feature_files") as mock_bdd:
            mock_bdd.return_value = [
                {
                    "feature_file": "tests/bdd/features/integration.feature",
                    "scenario_name": "End to end workflow",
                    "user_story_references": ["US-00057"],
                    "test_type": "bdd",
                }
            ]

            bdd_stats = bdd_parser.link_scenarios_to_user_stories()
            assert bdd_stats["scenarios_linked"] == 1

        # Step 3: Test Execution Tracking
        tracker = TestExecutionTracker()
        tracker.start_test_session()

        try:
            # Simulate test execution results
            tracker.record_test_result(
                "tests/integration/test_workflow.py::test_end_to_end_workflow",
                "failed",
                250.0,
                "Integration test failure",
            )

            # Should create defect
            defect_id = tracker.create_defect_from_failure(
                "tests/integration/test_workflow.py::test_end_to_end_workflow",
                "Integration test failure",
                "Full stack trace here...",
            )
            assert defect_id is not None

        finally:
            tracker.end_test_session()

        # Verify complete integration
        tests = self.db.query(Test).all()
        assert len(tests) == 2  # One regular test + one BDD test

        epic_tests = self.db.query(Test).filter(Test.epic_id == epic.id).all()
        assert len(epic_tests) == 2  # Both linked to Epic

        defects = (
            self.db.query(Defect).filter(Defect.defect_type == "test_failure").all()
        )
        assert len(defects) == 1
        assert defects[0].epic_id == epic.id

        # Calculate Epic progress
        total_tests = len(epic_tests)
        failed_tests = len(
            [t for t in epic_tests if t.last_execution_status == "failed"]
        )
        passed_tests = len(
            [t for t in epic_tests if t.last_execution_status == "passed"]
        )

        # Update Epic completion based on test results
        if total_tests > 0:
            epic.completion_percentage = (passed_tests / total_tests) * 100
            self.db.commit()

        assert epic.completion_percentage == 0.0  # No tests passed in this scenario

    def test_error_handling_and_recovery(self):
        """Test error handling and recovery in integration workflow."""
        # Test with invalid Epic reference
        sync = TestDatabaseSync()

        with patch.object(sync.discovery, "discover_tests") as mock_discover:
            mock_discover.return_value = [
                {
                    "test_file_path": "tests/unit/test_invalid.py",
                    "test_function_name": "test_invalid_epic_ref",
                    "test_type": "unit",
                    "title": "Test: Invalid Epic Ref",
                    "epic_references": ["EP-99999"],  # Non-existent Epic
                    "user_story_references": [],
                    "defect_references": [],
                    "bdd_scenario_name": None,
                }
            ]

            stats = sync.sync_tests_to_database()

            # Should create test but not link to Epic
            assert stats["created"] == 1
            assert stats["linked_to_epics"] == 0  # No Epic to link to

        # Verify test was still created
        tests = self.db.query(Test).all()
        assert len(tests) == 1
        assert tests[0].epic_id is None  # Not linked

    def test_duplicate_test_handling(self):
        """Test handling of duplicate test discoveries."""
        # Create initial test
        test = Test(
            test_type="unit",
            test_file_path="tests/unit/test_duplicate.py",
            test_function_name="test_duplicate",
            title="Test: Original Title",
        )
        self.db.add(test)
        self.db.commit()

        # Discover same test with updated information
        sync = TestDatabaseSync()
        with patch.object(sync.discovery, "discover_tests") as mock_discover:
            mock_discover.return_value = [
                {
                    "test_file_path": "tests/unit/test_duplicate.py",
                    "test_function_name": "test_duplicate",
                    "test_type": "unit",
                    "title": "Test: Updated Title",
                    "epic_references": [],
                    "user_story_references": [],
                    "defect_references": [],
                    "bdd_scenario_name": None,
                }
            ]

            stats = sync.sync_tests_to_database()

            # Should update existing test, not create new one
            assert stats["created"] == 0
            assert stats["updated"] == 1

        # Verify test was updated
        updated_test = (
            self.db.query(Test)
            .filter(Test.test_function_name == "test_duplicate")
            .first()
        )
        assert updated_test.title == "Test: Updated Title"

        # Verify only one test exists
        all_tests = self.db.query(Test).all()
        assert len(all_tests) == 1
