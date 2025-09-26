"""
Unit tests for GitHub Issue Label Mapper

Tests the automatic label assignment functionality including:
- Priority mapping
- Epic-to-component mapping based on traceability matrix
- GDPR label assignment
- Release planning logic
- Status management
"""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, mock_open, patch

import pytest

from src.shared.utils.github_label_mapper import (
    GitHubIssueLabelMapper,
    IssueData,
    LabelMapping,
    TraceabilityMatrixParser,
)


@pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
@pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
class TestTraceabilityMatrixParser:
    """Test traceability matrix parsing functionality."""

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_init_with_path(self):
        """Test initialization with matrix path."""
        path = Path("test/matrix.md")
        parser = TraceabilityMatrixParser(path)
        assert parser.matrix_path == path
        assert parser._epic_mappings is None

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_get_default_mappings(self):
        """Test default epic mappings fallback."""
        parser = TraceabilityMatrixParser(Path("nonexistent.md"))
        mappings = parser._get_default_mappings()

        expected = {
            "EP-00001": {"component": "frontend", "epic_label": "blog-content"},
            "EP-00002": {"component": "backend", "epic_label": "comment-system"},
            "EP-00003": {"component": "gdpr", "epic_label": "privacy-consent"},
            "EP-00004": {"component": "ci-cd", "epic_label": "github-workflow"},
        }

        assert mappings == expected

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_determine_component_from_description(self):
        """Test component determination from epic description."""
        parser = TraceabilityMatrixParser(Path("test.md"))

        test_cases = [
            (
                "Blog Content Management",
                {"component": "frontend", "epic_label": "blog-content"},
            ),
            (
                "Comment System Implementation",
                {"component": "backend", "epic_label": "comment-system"},
            ),
            (
                "GDPR Privacy Compliance",
                {"component": "gdpr", "epic_label": "privacy-consent"},
            ),
            (
                "GitHub Workflow Integration",
                {"component": "ci-cd", "epic_label": "github-workflow"},
            ),
            ("Unknown Epic Type", {"component": "backend", "epic_label": "general"}),
        ]

        for description, expected in test_cases:
            result = parser._determine_component_from_description(description)
            assert result == expected

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_get_epic_mappings_from_file(self, mock_read_text, mock_exists):
        """Test parsing epic mappings from matrix file."""
        mock_exists.return_value = True
        mock_read_text.return_value = """
        | **EP-00001** | Blog Content Management | US-00001, US-00002 | 8 | High | 📝 Planned |
        | **EP-00002** | GDPR-Compliant Comment System | US-00003, US-00004 | 16 | High | 📝 Planned |
        """

        parser = TraceabilityMatrixParser(Path("test.md"))
        mappings = parser.get_epic_mappings()

        assert "EP-00001" in mappings
        assert mappings["EP-00001"]["epic_label"] == "blog-content"
        assert "EP-00002" in mappings
        assert mappings["EP-00002"]["epic_label"] == "comment-system"

    @patch("pathlib.Path.exists")
    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_get_epic_mappings_file_not_found(self, mock_exists):
        """Test fallback when matrix file doesn't exist."""
        mock_exists.return_value = False

        parser = TraceabilityMatrixParser(Path("nonexistent.md"))
        mappings = parser.get_epic_mappings()

        # Should return default mappings
        assert len(mappings) == 4
        assert "EP-00001" in mappings


@pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
@pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
class TestGitHubIssueLabelMapper:
    """Test the main label mapping functionality."""

    @pytest.fixture
    def mapper(self):
        """Create a label mapper instance for testing."""
        with patch("src.shared.utils.github_label_mapper.TraceabilityMatrixParser"):
            return GitHubIssueLabelMapper()

    @pytest.fixture
    def sample_issue_data(self):
        """Create sample issue data for testing."""
        return IssueData(
            title="Test Issue",
            body="### Priority\n\nHigh\n\n### Epic ID\n\nEP-00001\n\n",
            existing_labels=["needs-triage"],
            issue_number=123,
        )

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_extract_form_value_basic(self, mapper):
        """Test basic form value extraction."""
        issue_body = """
        ### Priority

        High

        ### Epic ID

        EP-00001
        """

        assert mapper.extract_form_value(issue_body, "Priority") == "High"
        assert mapper.extract_form_value(issue_body, "Epic ID") == "EP-00001"
        assert mapper.extract_form_value(issue_body, "Nonexistent") is None

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_extract_form_value_no_response(self, mapper):
        """Test handling of '_No response_' values."""
        issue_body = """
        ### Priority

        _No response_
        """

        assert mapper.extract_form_value(issue_body, "Priority") is None

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_extract_form_value_alternative_formats(self, mapper):
        """Test extraction from different markdown formats."""
        test_cases = [
            ("**Priority**: Critical", "Priority", "Critical"),
            ("Priority: Medium", "Priority", "Medium"),
            ("### Priority\n\nLow", "Priority", "Low"),
        ]

        for body, field, expected in test_cases:
            result = mapper.extract_form_value(body, field)
            assert result == expected

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_map_priority_labels(self, mapper, sample_issue_data):
        """Test priority label mapping."""
        test_cases = [
            ("Critical", {"priority/critical"}),
            ("High", {"priority/high"}),
            ("Medium", {"priority/medium"}),
            ("Low", {"priority/low"}),
            ("Invalid", set()),
        ]

        for priority, expected in test_cases:
            issue_data = IssueData(
                title="Test",
                body=f"### Priority\n\n{priority}",
                existing_labels=[],
                issue_number=1,
            )
            result = mapper.map_priority_labels(issue_data)
            assert result == expected

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_map_epic_labels(self, mapper):
        """Test epic-to-component label mapping."""
        # Mock the epic_mapper method properly
        mock_get_epic_mappings = Mock(return_value={
            "EP-00001": {"component": "frontend", "epic_label": "blog-content"},
            "EP-00002": {"component": "backend", "epic_label": "comment-system"},
        })
        mapper.epic_mapper.get_epic_mappings = mock_get_epic_mappings

        test_cases = [
            ("EP-00001", {"component/frontend", "epic/blog-content"}),
            ("EP-00002", {"component/backend", "epic/comment-system"}),
            ("EP-999", set()),  # Unknown epic
            ("Invalid", set()),  # Invalid format
        ]

        for epic_id, expected in test_cases:
            issue_data = IssueData(
                title="Test",
                body=f"### Epic ID\n\n{epic_id}",
                existing_labels=[],
                issue_number=1,
            )
            result = mapper.map_epic_labels(issue_data)
            assert result == expected

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_map_gdpr_labels(self, mapper):
        """Test GDPR label mapping based on content."""
        test_cases = [
            ("This story involves personal data processing", {"gdpr/personal-data"}),
            ("Data collection requires user consent", {"gdpr/consent-required"}),
            ("Privacy impact assessment needed", {"gdpr/privacy-review"}),
            ("Data retention policies apply", {"gdpr/data-retention"}),
            (
                "This story involves personal data processing and requires user consent",
                {"gdpr/personal-data", "gdpr/consent-required"},
            ),
            ("No GDPR content here", set()),
        ]

        for body_text, expected in test_cases:
            issue_data = IssueData(
                title="Test", body=body_text, existing_labels=[], issue_number=1
            )
            result = mapper.map_gdpr_labels(issue_data)
            assert result == expected

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_map_release_labels(self, mapper):
        """Test release label mapping logic."""
        test_cases = [
            # Critical priority -> MVP
            ("Critical", "EP-00001", {"release/mvp"}),
            # GDPR epic -> MVP
            ("High", "EP-00003", {"release/mvp"}),
            # Comment epic -> MVP
            ("Medium", "EP-00002", {"release/mvp"}),
            # High priority, non-critical epic -> v1.1
            ("High", "EP-00001", {"release/v1.1"}),
            # Medium/Low priority -> v1.2
            ("Medium", "EP-00001", {"release/v1.2"}),
            ("Low", "EP-00004", {"release/v1.2"}),
        ]

        for priority, epic_id, expected in test_cases:
            issue_data = IssueData(
                title="Test",
                body=f"### Priority\n\n{priority}\n\n### Epic ID\n\n{epic_id}",
                existing_labels=[],
                issue_number=1,
            )
            result = mapper.map_release_labels(issue_data)
            assert result == expected

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_map_status_labels(self, mapper):
        """Test status label mapping."""
        test_cases = [
            ("ready for development", {"status/ready"}),
            ("in progress", {"status/in-progress"}),
            ("blocked by dependency", {"status/blocked"}),
            ("no special indicators", {"status/backlog"}),
        ]

        for body_text, expected in test_cases:
            issue_data = IssueData(
                title="Test", body=body_text, existing_labels=[], issue_number=1
            )
            result = mapper.map_status_labels(issue_data)
            assert result == expected

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_map_status_labels_preserves_existing(self, mapper):
        """Test that existing status labels are preserved."""
        issue_data = IssueData(
            title="Test",
            body="ready for development",
            existing_labels=["status/in-review"],
            issue_number=1,
        )
        result = mapper.map_status_labels(issue_data)
        assert result == set()  # Should not add new status labels

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_generate_labels_integration(self, mapper):
        """Test full label generation integration."""
        # Mock the epic_mapper method properly
        mock_get_epic_mappings = Mock(return_value={
            "EP-00003": {"component": "gdpr", "epic_label": "privacy-consent"}
        })
        mapper.epic_mapper.get_epic_mappings = mock_get_epic_mappings

        issue_data = IssueData(
            title="GDPR User Story",
            body="""
            ### Priority

            Critical

            ### Parent Epic

            EP-00003

            This story involves personal data processing and requires user consent.
            """,
            existing_labels=["user-story", "needs-triage"],
            issue_number=456,
        )

        result = mapper.generate_labels(issue_data)

        # Should include original labels (except needs-triage) plus generated ones
        expected_labels = {
            "user-story",
            "priority/critical",
            "component/gdpr",
            "epic/privacy-consent",
            "gdpr/personal-data",
            "gdpr/consent-required",
            "release/mvp",
            "status/backlog",
        }

        assert set(result) == expected_labels
        assert "needs-triage" not in result

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_generate_labels_error_handling(self, mapper):
        """Test error handling in label generation."""
        # Mock an error in one of the mapping methods
        with patch.object(
            mapper, "map_priority_labels", side_effect=Exception("Test error")
        ):
            issue_data = IssueData(
                title="Test",
                body="Test content",
                existing_labels=["original"],
                issue_number=1,
            )

            result = mapper.generate_labels(issue_data)
            # Should return original labels on error
            assert result == ["original"]

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_epic_mapper_attribute_regression(self, mapper):
        """Regression test for epic_mapper attribute naming.

        This test documents the correct attribute name 'epic_mapper' vs the
        incorrect 'matrix_parser' that was causing AttributeError failures.
        It validates proper mocking patterns for the epic mapping functionality.
        """
        # Verify the mapper has the correct epic_mapper attribute
        assert hasattr(mapper, 'epic_mapper'), "GitHubIssueLabelMapper should have epic_mapper attribute"
        assert not hasattr(mapper, 'matrix_parser'), "GitHubIssueLabelMapper should NOT have matrix_parser attribute"

        # Test proper mocking pattern for epic_mapper.get_epic_mappings
        mock_mappings = {
            "EP-12345": {"component": "frontend", "epic_label": "test-epic"},
            "EP-67890": {"component": "backend", "epic_label": "api-epic"},
        }

        # This is the CORRECT way to mock the epic mapper method
        mock_get_epic_mappings = Mock(return_value=mock_mappings)
        mapper.epic_mapper.get_epic_mappings = mock_get_epic_mappings

        # Verify the mock works correctly
        issue_data = IssueData(
            title="Test Epic Mapping",
            body="### Epic ID\n\nEP-12345",
            existing_labels=[],
            issue_number=1,
        )

        result = mapper.map_epic_labels(issue_data)
        expected_labels = {"component/frontend", "epic/test-epic"}
        assert result == expected_labels

        # Verify the mock was called
        mock_get_epic_mappings.assert_called_once()

        # Test that trying to access matrix_parser would fail (demonstrating the original bug)
        with pytest.raises(AttributeError, match="'GitHubIssueLabelMapper' object has no attribute 'matrix_parser'"):
            _ = mapper.matrix_parser


@pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
@pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
class TestIssueData:
    """Test the IssueData dataclass."""

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_issue_data_creation(self):
        """Test IssueData creation and attributes."""
        issue_data = IssueData(
            title="Test Issue",
            body="Issue body content",
            existing_labels=["label1", "label2"],
            issue_number=123,
        )

        assert issue_data.title == "Test Issue"
        assert issue_data.body == "Issue body content"
        assert issue_data.existing_labels == ["label1", "label2"]
        assert issue_data.issue_number == 123


@pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
@pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
class TestLabelMapping:
    """Test the LabelMapping dataclass."""

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_label_mapping_creation(self):
        """Test LabelMapping creation with default priority."""
        mapping = LabelMapping(
            source_field="Priority", source_value="High", target_label="priority/high"
        )

        assert mapping.source_field == "Priority"
        assert mapping.source_value == "High"
        assert mapping.target_label == "priority/high"
        assert mapping.priority == 0

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_label_mapping_with_priority(self):
        """Test LabelMapping creation with custom priority."""
        mapping = LabelMapping(
            source_field="Epic",
            source_value="EP-00001",
            target_label="epic/blog-content",
            priority=10,
        )

        assert mapping.priority == 10


# Integration tests
@pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
@pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
class TestLabelMapperIntegration:
    """Integration tests with real-like data."""

    @pytest.fixture
    def integration_mapper(self, tmp_path):
        """Create mapper with temporary matrix file."""
        matrix_content = """
        # Requirements Traceability Matrix

        | Epic | Req ID | Requirement Description | Priority | User Story |
        |------|--------|------------------------|----------|------------|
        | **EP-00001** | **BR-001** | Blog Content Management | High | US-001 |
        | **EP-00002** | **BR-002** | GDPR-Compliant Comment System | High | US-003 |
        | **EP-00003** | **GDPR-001** | Privacy and Consent Management | Critical | US-006 |
        | **EP-00004** | **WF-001** | GitHub Workflow Integration | High | US-009 |
        """

        matrix_file = tmp_path / "requirements-matrix.md"
        matrix_file.write_text(matrix_content)

        return GitHubIssueLabelMapper(matrix_file)

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_full_epic_workflow(self, integration_mapper):
        """Test complete epic label assignment workflow."""
        epic_issue = IssueData(
            title="EP-00003: Privacy and Consent Management",
            body="""
            ### Epic ID

            EP-00003

            ### Priority

            Critical

            ### GDPR Considerations

            - [x] This epic involves personal data processing
            - [x] GDPR compliance review required
            - [x] Privacy impact assessment needed

            This epic will implement comprehensive GDPR compliance.
            """,
            existing_labels=["epic", "needs-triage"],
            issue_number=100,
        )

        labels = integration_mapper.generate_labels(epic_issue)

        # Verify all expected labels are present
        expected_labels = {
            "epic",
            "priority/critical",
            "component/gdpr",
            "epic/privacy-consent",
            "gdpr/personal-data",
            "gdpr/consent-required",
            "gdpr/privacy-review",
            "release/mvp",
            "status/backlog",
        }

        assert set(labels) == expected_labels
        assert "needs-triage" not in labels

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003", "EP-00004")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00004", "US-00015")
    def test_user_story_inheritance(self, integration_mapper):
        """Test user story label inheritance from parent epic."""
        user_story_issue = IssueData(
            title="US-00015: Cookie Consent Banner",
            body="""
            ### User Story ID

            US-015

            ### Parent Epic

            EP-00003

            ### Priority

            High

            ### User Story

            **As a** website visitor
            **I want** to see a clear cookie consent banner
            **So that** I can make informed decisions about data processing

            ### GDPR Considerations

            - [x] This story involves personal data processing
            - [x] Data collection requires user consent

            The story is ready for development.
            """,
            existing_labels=["user-story"],
            issue_number=200,
        )

        labels = integration_mapper.generate_labels(user_story_issue)

        # Should inherit component/epic from parent EP-00003
        # High priority + EP-00003 should go to MVP
        expected_labels = {
            "user-story",
            "priority/high",
            "component/gdpr",
            "epic/privacy-consent",
            "gdpr/personal-data",
            "gdpr/consent-required",
            "release/mvp",
            "status/ready",  # "ready for development" detected
        }

        assert set(labels) == expected_labels
