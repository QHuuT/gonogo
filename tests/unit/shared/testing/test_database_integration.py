"""
Unit tests for RTM Test-Database Integration.

Tests the database integration functionality for automatic test execution tracking.

Related Issue: US-00057 - Test execution integration with database
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.shared.testing.database_integration import (
    TestDiscovery,
    TestDatabaseSync,
    TestExecutionTracker,
    BDDScenarioParser
)


class TestTestDiscovery:
    """Test TestDiscovery functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.discovery = TestDiscovery()

    def test_epic_pattern_matching(self):
        """Test Epic reference pattern matching."""
        content = """
        # This test is related to EP-00057
        def test_something():
            # Testing for EP-12345
            pass
        """
        epic_refs = self.discovery._extract_epic_references(content)
        assert "EP-00057" in epic_refs
        assert "EP-12345" in epic_refs

    def test_user_story_pattern_matching(self):
        """Test User Story reference pattern matching."""
        content = """
        Related to US-00057 and also US-99999
        """
        us_refs = self.discovery._extract_user_story_references(content)
        assert "US-00057" in us_refs
        assert "US-99999" in us_refs

    def test_defect_pattern_matching(self):
        """Test Defect reference pattern matching."""
        content = """
        Fixes DEF-00001 and addresses DEF-12345
        """
        def_refs = self.discovery._extract_defect_references(content)
        assert "DEF-00001" in def_refs
        assert "DEF-12345" in def_refs

    def test_generate_test_title(self):
        """Test test title generation from function names."""
        assert self.discovery._generate_test_title("test_user_login") == "Test: User Login"
        assert self.discovery._generate_test_title("test_epic_progress_calculation") == "Test: Epic Progress Calculation"

    def test_analyze_test_file_with_references(self):
        """Test analyzing a test file with Epic/US references."""
        test_content = '''
"""
Test file for EP-00057 functionality.
Related to US-00057.
"""

def test_database_integration():
    """Test database integration - EP-00057."""
    pass

def test_user_story_linking():
    """Test for US-00057."""
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write(test_content)
            tmp.flush()
            tmp_path = Path(tmp.name)

        try:
            test_metadata = self.discovery._analyze_test_file(tmp_path, 'unit')

            assert len(test_metadata) == 2
            assert test_metadata[0]['test_function_name'] == 'test_database_integration'
            assert test_metadata[0]['test_type'] == 'unit'
            assert 'EP-00057' in test_metadata[0]['epic_references']
            assert 'US-00057' in test_metadata[0]['user_story_references']

        finally:
            try:
                tmp_path.unlink()
            except (PermissionError, FileNotFoundError):
                pass  # Windows may lock the file, ignore cleanup errors

    def test_analyze_test_file_without_references(self):
        """Test analyzing a test file without Epic/US references."""
        test_content = '''
def test_simple_function():
    """Simple test without references."""
    assert True
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write(test_content)
            tmp.flush()
            tmp_path = Path(tmp.name)

        try:
            test_metadata = self.discovery._analyze_test_file(tmp_path, 'unit')

            assert len(test_metadata) == 1
            assert test_metadata[0]['test_function_name'] == 'test_simple_function'
            assert test_metadata[0]['epic_references'] == []
            assert test_metadata[0]['user_story_references'] == []

        finally:
            try:
                tmp_path.unlink()
            except (PermissionError, FileNotFoundError):
                pass  # Windows may lock the file, ignore cleanup errors

    @patch('src.shared.testing.database_integration.Path.glob')
    def test_discover_tests(self, mock_glob):
        """Test test discovery functionality."""
        # Mock test files
        mock_test_file = Mock()
        mock_test_file.is_file.return_value = True
        mock_test_file.name = 'test_example.py'
        mock_test_file.relative_to.return_value = Path('tests/unit/test_example.py')

        mock_glob.return_value = [mock_test_file]

        with patch.object(self.discovery, '_analyze_test_file') as mock_analyze:
            mock_analyze.return_value = [{
                'test_file_path': 'tests/unit/test_example.py',
                'test_function_name': 'test_example',
                'test_type': 'unit',
                'epic_references': ['EP-00057']
            }]

            tests = self.discovery.discover_tests()

            assert len(tests) == 5  # One for each test type pattern
            mock_analyze.assert_called()


class TestTestDatabaseSync:
    """Test TestDatabaseSync functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sync = TestDatabaseSync()
        self.mock_db = Mock()

    @patch('src.shared.testing.database_integration.get_db_session')
    def test_create_or_update_test_new(self, mock_get_db):
        """Test creating a new test record."""
        mock_get_db.return_value = self.mock_db
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        test_data = {
            'test_file_path': 'tests/unit/test_example.py',
            'test_function_name': 'test_example',
            'test_type': 'unit',
            'title': 'Test: Example',
            'line_number': 10,
            'bdd_scenario_name': None
        }

        result = self.sync._create_or_update_test(self.mock_db, test_data)

        assert result == 'created'
        self.mock_db.add.assert_called_once()

    @patch('src.shared.testing.database_integration.get_db_session')
    def test_create_or_update_test_existing(self, mock_get_db):
        """Test updating an existing test record."""
        mock_get_db.return_value = self.mock_db
        mock_existing_test = Mock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_test

        test_data = {
            'test_file_path': 'tests/unit/test_example.py',
            'test_function_name': 'test_example',
            'test_type': 'unit',
            'title': 'Test: Example Updated',
            'bdd_scenario_name': None
        }

        result = self.sync._create_or_update_test(self.mock_db, test_data)

        assert result == 'updated'
        assert mock_existing_test.title == 'Test: Example Updated'
        self.mock_db.add.assert_not_called()

    @patch('src.shared.testing.database_integration.get_db_session')
    def test_link_test_to_epic_success(self, mock_get_db):
        """Test successfully linking test to Epic."""
        mock_get_db.return_value = self.mock_db

        # Mock Epic query
        mock_epic = Mock()
        mock_epic.id = 1
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_epic,  # Epic found
            Mock()      # Test found
        ]

        test_data = {
            'test_file_path': 'tests/unit/test_example.py',
            'test_function_name': 'test_example',
            'epic_references': ['EP-00057']
        }

        result = self.sync._link_test_to_epic(self.mock_db, test_data)

        assert result is True

    @patch('src.shared.testing.database_integration.get_db_session')
    def test_link_test_to_epic_no_epic(self, mock_get_db):
        """Test linking test to Epic when Epic doesn't exist."""
        mock_get_db.return_value = self.mock_db
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        test_data = {
            'epic_references': ['EP-99999']
        }

        result = self.sync._link_test_to_epic(self.mock_db, test_data)

        assert result is False


class TestTestExecutionTracker:
    """Test TestExecutionTracker functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = TestExecutionTracker()
        self.mock_db = Mock()

    def test_start_and_end_session(self):
        """Test session management."""
        with patch('src.shared.testing.database_integration.get_db_session') as mock_get_db:
            mock_get_db.return_value = self.mock_db

            self.tracker.start_test_session()
            assert self.tracker.db_session == self.mock_db

            self.tracker.end_test_session()
            self.mock_db.commit.assert_called_once()
            self.mock_db.close.assert_called_once()
            assert self.tracker.db_session is None

    def test_record_test_result_success(self):
        """Test recording successful test result."""
        self.tracker.db_session = self.mock_db

        mock_test = Mock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_test

        result = self.tracker.record_test_result(
            'tests/unit/test_example.py::test_function',
            'passed',
            150.5
        )

        assert result is True
        mock_test.update_execution_result.assert_called_once_with('passed', 150.5, None)

    def test_record_test_result_no_session(self):
        """Test recording test result without session."""
        result = self.tracker.record_test_result(
            'tests/unit/test_example.py::test_function',
            'passed'
        )

        assert result is False

    def test_record_test_result_invalid_test_id(self):
        """Test recording test result with invalid test ID."""
        self.tracker.db_session = self.mock_db

        result = self.tracker.record_test_result('invalid_test_id', 'passed')

        assert result is False

    def test_create_defect_from_failure(self):
        """Test creating defect from test failure."""
        self.tracker.db_session = self.mock_db

        # Mock test lookup - first query finds the test
        mock_test = Mock()
        mock_test.id = 1
        mock_test.epic_id = 2

        # Mock defect count query - second query counts defects
        mock_defect_count_query = Mock()
        mock_defect_count_query.count.return_value = 5

        # Set up side effects for the two different queries
        def mock_query_side_effect(model):
            if 'Test' in str(model):
                return Mock(filter=Mock(return_value=Mock(first=Mock(return_value=mock_test))))
            else:  # Defect query
                return mock_defect_count_query

        self.mock_db.query.side_effect = mock_query_side_effect

        defect_id = self.tracker.create_defect_from_failure(
            'tests/unit/test_example.py::test_function',
            'AssertionError: Test failed',
            'Traceback...'
        )

        assert defect_id == 'DEF-00006'
        self.mock_db.add.assert_called_once()

    def test_determine_failure_severity(self):
        """Test failure severity determination."""
        assert self.tracker._determine_failure_severity('AssertionError: test failed') == 'medium'
        assert self.tracker._determine_failure_severity('ImportError: module not found') == 'high'
        assert self.tracker._determine_failure_severity('Security validation failed') == 'critical'
        assert self.tracker._determine_failure_severity('Unknown error') == 'low'


class TestBDDScenarioParser:
    """Test BDDScenarioParser functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = BDDScenarioParser()

    def test_scenario_pattern_matching(self):
        """Test scenario pattern matching."""
        content = """
Feature: User Authentication

  Scenario: User login with valid credentials
    Given a user exists
    When they login
    Then they should be authenticated

  Scenario Outline: User login attempts
    Given a user with <status>
    When they attempt login
    Then the result is <result>
"""
        scenarios = self.parser.scenario_pattern.findall(content)
        assert len(scenarios) == 2
        assert "User login with valid credentials" in scenarios
        assert "Outline: User login attempts" in scenarios

    def test_extract_user_story_context(self):
        """Test extracting User Story references from context."""
        content = """
# US-00057: Test execution integration
Feature: Test Database Integration

  Background:
    Given the system is configured for US-00057

  Scenario: Test discovery
    Given tests exist in the system
"""
        # Test context extraction around position 150 (roughly at "Scenario:")
        position = content.find("Scenario:")
        user_story_refs = self.parser._extract_user_story_context(content, position)

        assert "US-00057" in user_story_refs

    def test_parse_feature_content(self):
        """Test parsing feature file content."""
        content = """
# Related to US-00057
Feature: Test Integration

  Scenario: Basic test discovery
    Given tests exist
    When discovery runs
    Then tests are found

  Scenario: Epic linking
    Given Epic references exist in US-00057
    When linking occurs
    Then tests are linked
"""
        feature_file = Path.cwd() / 'tests/bdd/features/test_integration.feature'
        scenarios = self.parser._parse_feature_content(feature_file, content)

        assert len(scenarios) == 2
        assert scenarios[0]['scenario_name'] == 'Basic test discovery'
        assert scenarios[1]['scenario_name'] == 'Epic linking'
        assert 'US-00057' in scenarios[0]['user_story_references']
        assert 'US-00057' in scenarios[1]['user_story_references']

    @patch('src.shared.testing.database_integration.get_db_session')
    def test_link_scenario_to_user_story_success(self, mock_get_db):
        """Test successfully linking scenario to User Story."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock User Story lookup
        mock_user_story = Mock()
        mock_user_story.epic_id = 1
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user_story,  # User Story found
            None              # Test doesn't exist
        ]

        scenario = {
            'feature_file': 'tests/bdd/features/test.feature',
            'scenario_name': 'Test Scenario',
            'line_number': 10,
            'user_story_references': ['US-00057']
        }

        result = self.parser._link_scenario_to_user_story(mock_db, scenario)

        assert result is True
        mock_db.add.assert_called_once()

    @patch('src.shared.testing.database_integration.get_db_session')
    def test_link_scenario_to_user_story_no_user_story(self, mock_get_db):
        """Test linking scenario when User Story doesn't exist."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        scenario = {
            'user_story_references': ['US-99999']
        }

        result = self.parser._link_scenario_to_user_story(mock_db, scenario)

        assert result is False


class TestIntegrationWorkflow:
    """Test complete integration workflow."""

    @patch('src.shared.testing.database_integration.get_db_session')
    @patch('src.shared.testing.database_integration.TestDiscovery.discover_tests')
    def test_full_sync_workflow(self, mock_discover, mock_get_db):
        """Test complete test discovery and sync workflow."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock discovered tests
        mock_discover.return_value = [{
            'test_file_path': 'tests/unit/test_example.py',
            'test_function_name': 'test_example',
            'test_type': 'unit',
            'title': 'Test: Example',
            'line_number': 10,
            'epic_references': ['EP-00057'],
            'user_story_references': [],
            'defect_references': [],
            'bdd_scenario_name': None
        }]

        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,    # Test doesn't exist (create)
            Mock(),  # Epic exists (link)
            Mock()   # Test exists for linking
        ]

        sync = TestDatabaseSync()
        stats = sync.sync_tests_to_database()

        assert stats['discovered'] == 1
        assert stats['created'] == 1
        assert stats['linked_to_epics'] == 1
        assert stats['errors'] == 0

    def test_pytest_plugin_integration(self):
        """Test integration with pytest plugin."""
        from src.shared.testing.database_pytest_plugin import DatabaseIntegrationPlugin

        plugin = DatabaseIntegrationPlugin()
        assert plugin.test_tracker is not None
        assert plugin.test_sync is not None
        assert plugin.bdd_parser is not None