"""
RTM End-to-End Integration Tests

Tests the complete RTM automation workflow including:
- Real file operations
- Plugin system integration
- CLI tool functionality
- Configuration handling

Related Issue: US-00017 - Comprehensive testing and extensibility framework
Epic: EP-00005 - RTM Automation
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from shared.utils.rtm_link_generator import RTMLinkGenerator
from shared.utils.rtm_plugins import PluginManager


@pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
@pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00014", "US-00017")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
@pytest.mark.test_category("undefined")
@pytest.mark.priority("undefined")
class TestRTMEndToEnd:
    """End-to-end integration tests for RTM automation."""

    @pytest.fixture
    def sample_rtm_content(self):
        """Sample RTM content for testing."""
        return """# Requirements Traceability Matrix

**Project**: Test Project
**Version**: 1.0
**Last Updated**: 2025-09-20

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

    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        return {
            "github": {"owner": "TestOwner", "repo": "TestRepo"},
            "link_patterns": {
                "epic": "https://github.com/{owner}/{repo}/issues?q=is%3Aissue+{id}",
                "user_story": "https://github.com/{owner}/{repo}/issues?q=is%3Aissue+{id}",
            },
        }

    @pytest.fixture
    def temp_project_structure(self, sample_rtm_content, sample_config):
        """Create temporary project structure for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create project structure
            docs_dir = temp_path / "docs" / "traceability"
            docs_dir.mkdir(parents=True)

            tests_dir = temp_path / "tests" / "bdd" / "features"
            tests_dir.mkdir(parents=True)

            src_dir = temp_path / "src" / "be" / "services"
            src_dir.mkdir(parents=True)

            config_dir = temp_path / "config"
            config_dir.mkdir(parents=True)

            # Create RTM file
            rtm_file = docs_dir / "requirements-matrix.md"
            rtm_file.write_text(sample_rtm_content)

            # Create sample BDD files
            (tests_dir / "auth.feature").write_text("Feature: Authentication")
            (tests_dir / "blog.feature").write_text("Feature: Blog")

            # Create sample implementation files
            (src_dir / "auth_service.py").write_text("# Auth service")
            (src_dir / "blog_service.py").write_text("# Blog service")

            # Create config file
            import yaml

            config_file = config_dir / "rtm-automation.yml"
            config_file.write_text(yaml.dump(sample_config))

            yield {
                "project_dir": temp_path,
                "rtm_file": rtm_file,
                "config_file": config_file,
            }

    def test_rtm_generator_with_real_files(self, temp_project_structure):
        """Test RTM generator with real file structure."""
        project_dir = temp_project_structure["project_dir"]
        rtm_file = temp_project_structure["rtm_file"]
        config_file = temp_project_structure["config_file"]

        # Change to project directory
        original_cwd = os.getcwd()
        try:
            os.chdir(project_dir)

            # Initialize generator with config
            generator = RTMLinkGenerator(str(config_file))

            # Validate links
            result = generator.validate_rtm_links(str(rtm_file))

            # Should have some links
            assert result.total_links > 0
            assert result.valid_links > 0

            # Check specific validations
            github_links = [
                link for link in result.invalid_links if "github" in link.url
            ]
            # GitHub links should be valid (format-wise)
            assert len(github_links) == 0 or all(
                link.error_message and "format" not in link.error_message.lower()
                for link in github_links
            )

        finally:
            os.chdir(original_cwd)

    def test_rtm_update_with_real_files(self, temp_project_structure):
        """Test RTM update functionality with real files."""
        project_dir = temp_project_structure["project_dir"]
        rtm_file = temp_project_structure["rtm_file"]
        config_file = temp_project_structure["config_file"]

        original_cwd = os.getcwd()
        try:
            os.chdir(project_dir)

            generator = RTMLinkGenerator(str(config_file))

            # Read original content
            original_content = rtm_file.read_text()

            # Perform dry run update
            updates = generator.update_rtm_links(str(rtm_file), dry_run=True)

            # Should detect potential updates
            assert isinstance(updates, dict)
            assert all(isinstance(count, int) for count in updates.values())

            # File should be unchanged in dry run
            assert rtm_file.read_text() == original_content

            # Perform real update
            updates = generator.update_rtm_links(str(rtm_file), dry_run=False)

            # File should be modified if updates were made
            if sum(updates.values()) > 0:
                updated_content = rtm_file.read_text()
                assert updated_content != original_content
                assert "TestOwner/TestRepo" in updated_content

        finally:
            os.chdir(original_cwd)

    def test_cli_tool_integration(self, temp_project_structure):
        """Test CLI tool with real project structure."""
        project_dir = temp_project_structure["project_dir"]
        rtm_file = temp_project_structure["rtm_file"]

        # Get CLI tool path
        cli_tool = (
            Path(__file__).parent.parent.parent.parent / "tools" / "rtm-links-simple.py"
        )

        original_cwd = os.getcwd()
        try:
            os.chdir(project_dir)

            # Test validation
            result = subprocess.run(
                [
                    sys.executable,
                    str(cli_tool),
                    "--validate",
                    "--rtm-file",
                    str(rtm_file),
                ],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0
            assert "Total links:" in result.stdout
            assert "Valid links:" in result.stdout
            assert "Health score:" in result.stdout

            # Test update
            result = subprocess.run(
                [
                    sys.executable,
                    str(cli_tool),
                    "--update",
                    "--rtm-file",
                    str(rtm_file),
                ],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0
            assert "Updates that would be made:" in result.stdout

        finally:
            os.chdir(original_cwd)

    def test_plugin_system_integration(self):
        """Test plugin system discovery and loading."""
        plugin_manager = PluginManager()

        # Discover plugins
        plugin_manager.discover_plugins()

        # Should find built-in plugins
        plugins = plugin_manager.list_plugins()
        assert isinstance(plugins, dict)

        # Check for expected plugin types
        expected_types = ["link_generators", "validators", "parsers"]
        for plugin_type in expected_types:
            assert plugin_type in plugins

    def test_configuration_variations(self, temp_project_structure):
        """Test different configuration scenarios."""
        config_file = temp_project_structure["config_file"]

        # Test missing config file
        generator = RTMLinkGenerator("nonexistent-config.yml")
        assert generator.github_owner == "QHuuT"  # Default

        # Test custom config
        generator = RTMLinkGenerator(str(config_file))
        assert generator.github_owner == "TestOwner"  # From config

    def test_error_handling_integration(self, temp_project_structure):
        """Test error handling in integration scenarios."""
        project_dir = temp_project_structure["project_dir"]
        config_file = temp_project_structure["config_file"]

        original_cwd = os.getcwd()
        try:
            os.chdir(project_dir)

            generator = RTMLinkGenerator(str(config_file))

            # Test with non-existent RTM file
            with pytest.raises((FileNotFoundError, OSError)):
                generator.validate_rtm_links("nonexistent-rtm.md")

            # Test with empty RTM file
            empty_rtm = project_dir / "empty-rtm.md"
            empty_rtm.write_text("")

            result = generator.validate_rtm_links(str(empty_rtm))
            assert result.total_links == 0
            assert result.valid_links == 0

        finally:
            os.chdir(original_cwd)

    def test_link_generation_accuracy(self, temp_project_structure):
        """Test accuracy of generated links."""
        config_file = temp_project_structure["config_file"]
        generator = RTMLinkGenerator(str(config_file))

        # Test epic link
        epic_link = generator.generate_github_issue_link("EP-00001", bold=True)
        assert (
            epic_link
            == "[**EP-00001**](https://github.com/TestOwner/TestRepo/issues?q=is%3Aissue+EP-00001)"
        )

        # Test user story link
        us_link = generator.generate_github_issue_link("US-00014", bold=False)
        assert (
            us_link
            == "[US-00014](https://github.com/TestOwner/TestRepo/issues?q=is%3Aissue+US-00014)"
        )

        # Test file link
        rtm_path = temp_project_structure["rtm_file"]
        file_link = generator.generate_file_link(
            "tests/bdd/features/auth.feature", str(rtm_path)
        )
        assert "auth.feature" in file_link
        assert "](" in file_link

    def test_validation_report_generation(self, temp_project_structure):
        """Test validation report generation."""
        project_dir = temp_project_structure["project_dir"]
        rtm_file = temp_project_structure["rtm_file"]
        config_file = temp_project_structure["config_file"]

        original_cwd = os.getcwd()
        try:
            os.chdir(project_dir)

            generator = RTMLinkGenerator(str(config_file))
            result = generator.validate_rtm_links(str(rtm_file))

            # Generate report
            report = generator.generate_validation_report(result)

            # Check report content
            assert "RTM Link Validation Report" in report
            assert "Total Links" in report
            assert "Valid Links" in report
            assert "Health Score" in report

            # Should contain actual values
            assert str(result.total_links) in report
            assert str(result.valid_links) in report

        finally:
            os.chdir(original_cwd)


@pytest.mark.epic("EP-00001", "EP-00002", "EP-00005")
@pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00014", "US-00017")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
@pytest.mark.test_category("undefined")
@pytest.mark.priority("undefined")
class TestRTMPerformance:
    """Performance tests for RTM automation."""

    def test_large_rtm_performance(self):
        """Test performance with large RTM file."""
        # Create large RTM content
        large_content = "# Requirements Traceability Matrix\n\n"
        large_content += "| Epic | User Story | Status |\n"
        large_content += "|------|------------|--------|\n"

        # Add 1000 rows
        for i in range(1000):
            epic_id = f"EP-{i+1:05d}"
            us_id = f"US-{i+1:05d}"
            large_content += f"| [**{epic_id}**](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+{epic_id}) | [{us_id}](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+{us_id}) | ✅ |\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(large_content)
            f.flush()

            generator = RTMLinkGenerator()

            # Time the validation
            import time

            start_time = time.time()
            result = generator.validate_rtm_links(f.name)
            end_time = time.time()

            # Should complete within reasonable time (10 seconds for 1000 rows)
            duration = end_time - start_time
            assert duration < 10.0, f"Validation took too long: {duration:.2f}s"

            # Should find all links
            assert result.total_links == 2000  # 1000 epics + 1000 user stories

        os.unlink(f.name)


if __name__ == "__main__":
    pytest.main([__file__])
