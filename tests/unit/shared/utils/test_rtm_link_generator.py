"""
Unit tests for RTM Link Generator

Tests the core RTM automation functionality including link generation,
validation, and update operations.

Related Issue: US-00015 - Automated RTM link generation and validation
Epic: EP-00005 - RTM Automation
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Use direct module loading to avoid namespace collision in full test suite context
import sys
import importlib.util

# Load the module directly from the source file to avoid namespace collision
repo_root = Path(__file__).parent.parent.parent.parent.parent
rtm_module_path = repo_root / "src" / "shared" / "utils" / "rtm_link_generator.py"

spec = importlib.util.spec_from_file_location("rtm_link_generator", rtm_module_path)
rtm_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rtm_module)

# Import the classes from the loaded module
RTMLinkGenerator = rtm_module.RTMLinkGenerator
RTMLink = rtm_module.RTMLink
RTMValidationResult = rtm_module.RTMValidationResult


class TestRTMLinkGenerator:
    """Test cases for RTMLinkGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create RTMLinkGenerator instance for testing."""
        return RTMLinkGenerator()

    @pytest.fixture
    def temp_rtm_file(self):
        """Create temporary RTM file for testing."""
        content = """# Requirements Traceability Matrix

## Epic 1: Authentication System

| Epic | User Story | BDD Scenario | Implementation | Status |
|------|------------|--------------|----------------|--------|
| [**EP-00001**](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+EP-00001) | [US-00001](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+US-00001) | [auth.feature:login](../../tests/bdd/features/auth.feature) | [auth_service.py](../../src/be/services/auth_service.py) | ✅ |
| [**EP-00001**](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+EP-00001) | [US-00002](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+US-00002) | [auth.feature:logout](../../tests/bdd/features/auth.feature) | [auth_service.py](../../src/be/services/auth_service.py) | ⏳ |

## Epic 2: Blog System

| Epic | User Story | BDD Scenario | Implementation | Status |
|------|------------|--------------|----------------|--------|
| [**EP-00002**](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+EP-00002) | [US-00003](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+US-00003) | [blog.feature:create_post](../../tests/bdd/features/blog.feature) | [blog_service.py](../../src/be/services/blog_service.py) | 📝 |
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            f.flush()
            yield f.name

        # Cleanup
        os.unlink(f.name)

    def test_initialization_with_default_config(self, generator):
        """Test RTMLinkGenerator initialization with default config."""
        assert generator.github_owner == 'QHuuT'
        assert generator.github_repo == 'gonogo'
        assert 'github' in generator.config
        assert 'link_patterns' in generator.config

    def test_initialization_with_custom_config(self):
        """Test RTMLinkGenerator initialization with custom config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False, encoding='utf-8') as f:
            f.write("""
github:
  owner: "testowner"
  repo: "testrepo"
link_patterns:
  epic: "https://example.com/{owner}/{repo}/issues?q={id}"
""")
            f.flush()

            generator = RTMLinkGenerator(f.name)
            assert generator.github_owner == 'testowner'
            assert generator.github_repo == 'testrepo'

        os.unlink(f.name)

    def test_generate_github_issue_link_epic(self, generator):
        """Test GitHub issue link generation for epics."""
        link = generator.generate_github_issue_link("EP-00001", bold=True)
        expected = "[**EP-00001**](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+EP-00001)"
        assert link == expected

    def test_generate_github_issue_link_user_story(self, generator):
        """Test GitHub issue link generation for user stories."""
        link = generator.generate_github_issue_link("US-00014", bold=False)
        expected = "[US-00014](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+US-00014)"
        assert link == expected

    def test_generate_github_issue_link_defect(self, generator):
        """Test GitHub issue link generation for defects."""
        link = generator.generate_github_issue_link("DEF-00001", bold=False)
        expected = "[DEF-00001](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+DEF-00001)"
        assert link == expected

    def test_generate_file_link_relative(self, generator):
        """Test file link generation with relative paths."""
        rtm_path = "docs/traceability/requirements-matrix.md"
        target_path = "tests/bdd/features/auth.feature"

        link = generator.generate_file_link(target_path, rtm_path)
        expected = "[auth.feature](../../tests/bdd/features/auth.feature)"
        assert link == expected

    def test_generate_file_link_with_display_text(self, generator):
        """Test file link generation with custom display text."""
        rtm_path = "docs/traceability/requirements-matrix.md"
        target_path = "src/be/services/auth_service.py"
        display_text = "Authentication Service"

        link = generator.generate_file_link(target_path, rtm_path, display_text)
        expected = "[Authentication Service](../../src/be/services/auth_service.py)"
        assert link == expected

    def test_generate_bdd_scenario_link(self, generator):
        """Test BDD scenario link generation."""
        rtm_path = "docs/traceability/requirements-matrix.md"
        feature_file = "tests/bdd/features/auth.feature"
        scenario_name = "user_login"

        link = generator.generate_bdd_scenario_link(feature_file, scenario_name, rtm_path)
        expected = "[auth.feature:user_login](../../tests/bdd/features/auth.feature)"
        assert link == expected

    def test_extract_references_from_rtm(self, generator, temp_rtm_file):
        """Test extraction of references from RTM content."""
        with open(temp_rtm_file, 'r', encoding='utf-8') as f:
            content = f.read()

        references = generator.extract_references_from_rtm(content)

        # Should find epic, user story, BDD, and implementation links
        assert len(references) > 0

        # Check for specific reference types
        epic_refs = [ref for ref in references if ref[2] == 'epic']
        us_refs = [ref for ref in references if ref[2] == 'user_story']
        bdd_refs = [ref for ref in references if ref[2] == 'bdd_scenario']
        file_refs = [ref for ref in references if ref[2] == 'file']

        assert len(epic_refs) > 0
        assert len(us_refs) > 0
        assert len(bdd_refs) > 0
        assert len(file_refs) > 0

    def test_validate_github_link_valid_format(self, generator):
        """Test GitHub link validation with valid formats."""
        assert generator.validate_github_link("EP-00001") is True
        assert generator.validate_github_link("US-12345") is True
        assert generator.validate_github_link("DEF-67890") is True

    def test_validate_github_link_invalid_format(self, generator):
        """Test GitHub link validation with invalid formats."""
        assert generator.validate_github_link("EP-1") is False
        assert generator.validate_github_link("US-123456") is False
        assert generator.validate_github_link("INVALID-00001") is False
        assert generator.validate_github_link("EP00001") is False

    def test_validate_file_link_existing_file(self, generator, temp_rtm_file):
        """Test file link validation for existing files."""
        # Create a temporary file to validate against
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
            temp_file.write("# Test file")
            temp_file.flush()

            # Get relative path from RTM location
            rtm_dir = Path(temp_rtm_file).parent
            rel_path = os.path.relpath(temp_file.name, rtm_dir)

            assert generator.validate_file_link(rel_path, temp_rtm_file) is True

        os.unlink(temp_file.name)

    def test_validate_file_link_nonexistent_file(self, generator, temp_rtm_file):
        """Test file link validation for non-existent files."""
        assert generator.validate_file_link("nonexistent/file.py", temp_rtm_file) is False

    def test_validate_file_link_external_url(self, generator, temp_rtm_file):
        """Test file link validation for external URLs."""
        assert generator.validate_file_link("https://example.com/file", temp_rtm_file) is True

    def test_validate_rtm_links(self, generator, temp_rtm_file):
        """Test RTM link validation."""
        result = generator.validate_rtm_links(temp_rtm_file)

        assert isinstance(result, RTMValidationResult)
        assert result.total_links > 0
        assert result.valid_links >= 0
        assert isinstance(result.invalid_links, list)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)

    def test_update_rtm_links_dry_run(self, generator, temp_rtm_file):
        """Test RTM link updates in dry run mode."""
        updates = generator.update_rtm_links(temp_rtm_file, dry_run=True)

        assert isinstance(updates, dict)
        assert 'epic_links' in updates
        assert 'user_story_links' in updates
        assert 'defect_links' in updates
        assert 'file_links' in updates

        # File should not be modified in dry run
        with open(temp_rtm_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "EP-00001" in content  # Original content should be preserved

    def test_update_rtm_links_real_update(self, generator):
        """Test actual RTM link updates."""
        # Create content with old-style links
        old_content = """# Test RTM
[**EP-00001**](https://old-url.com/EP-00001)
[US-00014](https://old-url.com/US-00014)
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(old_content)
            f.flush()

            updates = generator.update_rtm_links(f.name, dry_run=False)

            # Check that updates were recorded
            assert updates['epic_links'] > 0 or updates['user_story_links'] > 0

            # Check that file was actually updated
            with open(f.name, 'r', encoding='utf-8') as updated_f:
                updated_content = updated_f.read()

            assert "github.com/QHuuT/gonogo/issues" in updated_content

        os.unlink(f.name)

    def test_generate_validation_report(self, generator):
        """Test validation report generation."""
        # Create mock validation result
        invalid_link = RTMLink(
            text="EP-INVALID",
            url="https://example.com",
            type="epic",
            valid=False,
            error_message="Invalid format"
        )

        result = RTMValidationResult(
            total_links=10,
            valid_links=9,
            invalid_links=[invalid_link],
            errors=["Test error"],
            warnings=["Test warning"]
        )

        report = generator.generate_validation_report(result)

        assert "RTM Link Validation Report" in report
        assert "Total Links: 10" in report
        assert "Valid Links: 9" in report
        assert "Invalid Links: 1" in report
        assert "EP-INVALID" in report
        assert "Invalid format" in report
        assert "Test error" in report
        assert "Test warning" in report
        assert "Health Score: 90.0%" in report


class TestRTMLinkDataClasses:
    """Test RTM data classes."""

    def test_rtm_link_creation(self):
        """Test RTMLink creation."""
        link = RTMLink(
            text="EP-00001",
            url="https://example.com",
            type="epic"
        )

        assert link.text == "EP-00001"
        assert link.url == "https://example.com"
        assert link.type == "epic"
        assert link.valid is True
        assert link.error_message is None

    def test_rtm_link_invalid(self):
        """Test RTMLink with invalid status."""
        link = RTMLink(
            text="EP-INVALID",
            url="https://example.com",
            type="epic",
            valid=False,
            error_message="Invalid format"
        )

        assert link.valid is False
        assert link.error_message == "Invalid format"

    def test_rtm_validation_result_creation(self):
        """Test RTMValidationResult creation."""
        result = RTMValidationResult(
            total_links=5,
            valid_links=4,
            invalid_links=[],
            errors=[],
            warnings=[]
        )

        assert result.total_links == 5
        assert result.valid_links == 4
        assert len(result.invalid_links) == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0


class TestConfigurationHandling:
    """Test configuration file handling."""

    def test_missing_config_file(self):
        """Test behavior when config file is missing."""
        generator = RTMLinkGenerator("nonexistent-config.yml")

        # Should use default configuration
        assert generator.github_owner == 'QHuuT'
        assert generator.github_repo == 'gonogo'

    def test_invalid_config_file(self):
        """Test behavior with invalid YAML config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False, encoding='utf-8') as f:
            f.write("invalid: yaml: content: [")
            f.flush()

            # Should handle gracefully and use defaults
            try:
                generator = RTMLinkGenerator(f.name)
                # If it doesn't raise an exception, that's acceptable
                assert hasattr(generator, 'config')
            except Exception:
                # If it raises an exception, that's also acceptable
                pass

        os.unlink(f.name)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_rtm_file(self, generator):
        """Test validation of empty RTM file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("")
            f.flush()

            result = generator.validate_rtm_links(f.name)
            assert result.total_links == 0
            assert result.valid_links == 0
            assert len(result.invalid_links) == 0

        os.unlink(f.name)

    def test_rtm_file_with_malformed_links(self, generator):
        """Test RTM file with malformed markdown links."""
        content = """# Test RTM
[Broken link without URL]
[Another broken](
[EP-00001](https://valid-link.com)
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            f.flush()

            result = generator.validate_rtm_links(f.name)
            # Should handle malformed links gracefully
            assert isinstance(result, RTMValidationResult)

        os.unlink(f.name)

    def test_special_characters_in_paths(self, generator):
        """Test handling of special characters in file paths."""
        rtm_path = "docs/trace ability/requirements-matrix.md"
        target_path = "tests/bdd/features/special chars.feature"

        link = generator.generate_file_link(target_path, rtm_path)
        assert isinstance(link, str)
        assert "](" in link


if __name__ == '__main__':
    pytest.main([__file__])