"""
Plugin System Integration Tests

Tests the RTM plugin system with real plugin loading and execution.

Related Issue: US-00017 - Comprehensive testing and extensibility framework
Epic: EP-00005 - RTM Automation
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from shared.utils.rtm_plugins import PluginManager, RTMPlugin
from shared.utils.rtm_plugins.base_link_generator import (
    BaseLinkGenerator,
    GitHubIssueLinkGenerator,
)
from shared.utils.rtm_plugins.base_rtm_parser import (
    BaseRTMParser,
    StandardMarkdownParser,
)
from shared.utils.rtm_plugins.base_validator import BaseValidator, StandardValidator


@pytest.mark.epic("EP-00001", "EP-00005")
@pytest.mark.user_story("US-00014", "US-00017", "US-12345")
@pytest.mark.component("backend")
class TestCustomPlugin(RTMPlugin):
    """Test custom plugin for testing."""

    @property
    def name(self) -> str:
        return "test_plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Test plugin for integration testing"


class CustomLinkGenerator(BaseLinkGenerator):
    """Custom link generator for testing."""

    @property
    def name(self) -> str:
        return "custom_link_generator"

    @property
    def version(self) -> str:
        return "1.0.0"

    def can_handle(self, reference_type: str) -> bool:
        return reference_type == "custom"

    def generate_link(self, reference: str, context: dict) -> str:
        return f"[{reference}](https://custom.example.com/{reference})"


class CustomValidator(BaseValidator):
    """Custom validator for testing."""

    @property
    def name(self) -> str:
        return "custom_validator"

    @property
    def version(self) -> str:
        return "1.0.0"

    def validate_requirement(self, requirement: dict) -> list:
        errors = []
        if requirement.get("custom_field") == "invalid":
            errors.append("Custom validation failed")
        return errors


@pytest.mark.epic("EP-00001", "EP-00005")
@pytest.mark.user_story("US-00014", "US-00017", "US-12345")
@pytest.mark.component("backend")
class TestPluginManager:
    """Test plugin manager functionality."""

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00014", "US-00017", "US-12345")
    @pytest.mark.component("backend")
    def test_plugin_manager_initialization(self):
        """Test plugin manager initialization."""
        manager = PluginManager()

        assert isinstance(manager.plugins, dict)
        assert isinstance(manager.plugin_types, dict)
        assert "link_generators" in manager.plugin_types
        assert "validators" in manager.plugin_types
        assert "parsers" in manager.plugin_types

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00014", "US-00017", "US-12345")
    @pytest.mark.component("backend")
    def test_manual_plugin_registration(self):
        """Test manual plugin registration."""
        manager = PluginManager()

        # Register test plugin
        test_plugin = TestCustomPlugin()
        manager.register_plugin(test_plugin, "link_generators")

        # Verify registration
        assert test_plugin.name in manager.plugins
        assert test_plugin in manager.plugin_types["link_generators"]

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00014", "US-00017", "US-12345")
    @pytest.mark.component("backend")
    def test_plugin_retrieval(self):
        """Test plugin retrieval methods."""
        manager = PluginManager()

        # Register plugins
        link_gen = CustomLinkGenerator()
        validator = CustomValidator()

        manager.register_plugin(link_gen, "link_generators")
        manager.register_plugin(validator, "validators")

        # Test get_plugin
        retrieved_link_gen = manager.get_plugin("custom_link_generator")
        assert retrieved_link_gen is link_gen

        # Test get_plugins_by_type
        link_generators = manager.get_plugins_by_type("link_generators")
        assert link_gen in link_generators

        validators = manager.get_plugins_by_type("validators")
        assert validator in validators

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00014", "US-00017", "US-12345")
    @pytest.mark.component("backend")
    def test_list_plugins(self):
        """Test plugin listing functionality."""
        manager = PluginManager()

        # Register some plugins
        manager.register_plugin(CustomLinkGenerator(), "link_generators")
        manager.register_plugin(CustomValidator(), "validators")

        # List all plugins
        plugin_list = manager.list_plugins()

        assert isinstance(plugin_list, dict)
        assert "link_generators" in plugin_list
        assert "validators" in plugin_list

        # Check link generators
        link_gens = plugin_list["link_generators"]
        assert len(link_gens) == 1
        assert link_gens[0]["name"] == "custom_link_generator"
        assert link_gens[0]["version"] == "1.0.0"

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00014", "US-00017", "US-12345")
    @pytest.mark.component("backend")
    def test_invalid_plugin_type_registration(self):
        """Test registration with invalid plugin type."""
        manager = PluginManager()
        plugin = TestCustomPlugin()

        with pytest.raises(ValueError):
            manager.register_plugin(plugin, "invalid_type")


@pytest.mark.epic("EP-00001", "EP-00005")
@pytest.mark.user_story("US-00014", "US-00017", "US-12345")
@pytest.mark.component("backend")
class TestBuiltInPlugins:
    """Test built-in plugin functionality."""

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00014", "US-00017", "US-12345")
    @pytest.mark.component("backend")
    def test_github_issue_link_generator(self):
        """Test GitHub issue link generator."""
        generator = GitHubIssueLinkGenerator()

        # Test properties
        assert generator.name == "github_issues"
        assert generator.version == "1.0.0"

        # Test can_handle
        assert generator.can_handle("epic") is True
        assert generator.can_handle("user_story") is True
        assert generator.can_handle("defect") is True
        assert generator.can_handle("custom") is False

        # Test link generation
        context = {"config": {"github": {"owner": "TestOwner", "repo": "TestRepo"}}}

        epic_link = generator.generate_link("EP-00001", context)
        assert (
            epic_link
            == "[**EP-00001**](https://github.com/TestOwner/TestRepo/issues?q=is%3Aissue+EP-00001)"
        )

        us_link = generator.generate_link("US-00014", context)
        assert (
            us_link
            == "[US-00014](https://github.com/TestOwner/TestRepo/issues?q=is%3Aissue+US-00014)"
        )

        # Test validation
        assert generator.validate_link("EP-00001", context) is True
        assert generator.validate_link("US-12345", context) is True
        assert generator.validate_link("INVALID-123", context) is False

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00014", "US-00017", "US-12345")
    @pytest.mark.component("backend")
    def test_standard_validator(self):
        """Test standard validator."""
        validator = StandardValidator()

        # Test properties
        assert validator.name == "standard_validation"
        assert validator.version == "1.0.0"

        # Test valid requirement
        valid_req = {"epic": "EP-00001", "user_story": "US-00014", "status": "✅"}

        errors = validator.validate_requirement(valid_req)
        assert len(errors) == 0

        # Test invalid requirement
        invalid_req = {
            "epic": "INVALID",
            "user_story": "ALSO_INVALID",
            "status": "UNKNOWN",
        }

        errors = validator.validate_requirement(invalid_req)
        assert len(errors) > 0
        assert any("Invalid epic format" in error for error in errors)
        assert any("Invalid user story format" in error for error in errors)
        assert any("Invalid status" in error for error in errors)

        # Test missing fields
        incomplete_req = {}
        errors = validator.validate_requirement(incomplete_req)
        assert len(errors) > 0
        assert any("Missing required field" in error for error in errors)

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00014", "US-00017", "US-12345")
    @pytest.mark.component("backend")
    def test_standard_markdown_parser(self):
        """Test standard markdown parser."""
        parser = StandardMarkdownParser()

        # Test properties
        assert parser.name == "standard_markdown"
        assert parser.version == "1.0.0"

        # Test can_parse
        valid_content = """# Requirements Traceability Matrix

| Epic | User Story | Status |
|------|------------|--------|
| EP-00001 | US-00014 | ✅ |
"""

        assert parser.can_parse(valid_content) is True

        invalid_content = "This is not an RTM"
        assert parser.can_parse(invalid_content) is False

        # Test parse_requirements
        requirements = parser.parse_requirements(valid_content)
        assert len(requirements) == 1
        assert requirements[0]["epic"] == "EP-00001"
        assert requirements[0]["user_story"] == "US-00014"
        assert requirements[0]["status"] == "✅"

        # Test parse_metadata
        content_with_metadata = """# Requirements Traceability Matrix

**Project**: Test Project
**Version**: 1.0
**Last Updated**: 2025-09-20

| Epic | User Story | Status |
|------|------------|--------|
"""

        metadata = parser.parse_metadata(content_with_metadata)
        assert metadata["project"] == "Test Project"
        assert metadata["version"] == "1.0"
        assert metadata["last_updated"] == "2025-09-20"


@pytest.mark.epic("EP-00001", "EP-00005")
@pytest.mark.user_story("US-00014", "US-00017", "US-12345")
@pytest.mark.component("backend")
class TestPluginDiscovery:
    """Test plugin discovery mechanism."""

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00014", "US-00017", "US-12345")
    @pytest.mark.component("backend")
    def test_plugin_discovery_with_temp_plugins(self):
        """Test plugin discovery with temporary plugin files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create plugin directory structure
            link_gen_dir = os.path.join(temp_dir, "link_generators")
            os.makedirs(link_gen_dir)

            # Create a test plugin file
            plugin_content = """
from shared.utils.rtm_plugins.base_link_generator import BaseLinkGenerator

class TempLinkGenerator(BaseLinkGenerator):
    @property
    def name(self) -> str:
        return "temp_generator"

    @property
    def version(self) -> str:
        return "1.0.0"

    def can_handle(self, reference_type: str) -> bool:
        return reference_type == "temp"

    def generate_link(self, reference: str, context: dict) -> str:
        return f"[{reference}](https://temp.example.com/{reference})"
"""

            plugin_file = os.path.join(link_gen_dir, "temp_plugin.py")
            with open(plugin_file, "w") as f:
                f.write(plugin_content)

            # Test discovery
            manager = PluginManager()
            manager.discover_plugins(temp_dir)

            # Should find the temporary plugin
            plugins = manager.list_plugins()
            link_generators = plugins.get("link_generators", [])

            temp_plugin = next(
                (p for p in link_generators if p["name"] == "temp_generator"), None
            )
            assert temp_plugin is not None
            assert temp_plugin["version"] == "1.0.0"

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00014", "US-00017", "US-12345")
    @pytest.mark.component("backend")
    def test_plugin_discovery_error_handling(self):
        """Test plugin discovery with invalid plugin files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create plugin directory
            link_gen_dir = os.path.join(temp_dir, "link_generators")
            os.makedirs(link_gen_dir)

            # Create invalid plugin file
            invalid_plugin_file = os.path.join(link_gen_dir, "invalid_plugin.py")
            with open(invalid_plugin_file, "w") as f:
                f.write("invalid python syntax [[[")

            # Discovery should handle errors gracefully
            manager = PluginManager()
            manager.discover_plugins(temp_dir)  # Should not raise exception

            # Should still initialize properly
            assert isinstance(manager.plugins, dict)


@pytest.mark.epic("EP-00001", "EP-00005")
@pytest.mark.user_story("US-00014", "US-00017", "US-12345")
@pytest.mark.component("backend")
class TestPluginIntegration:
    """Test plugin integration with RTM system."""

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00014", "US-00017", "US-12345")
    @pytest.mark.component("backend")
    def test_custom_link_generator_integration(self):
        """Test custom link generator integration."""
        generator = CustomLinkGenerator()

        # Test basic functionality
        assert generator.can_handle("custom") is True
        assert generator.can_handle("epic") is False

        link = generator.generate_link("CUSTOM-001", {})
        assert link == "[CUSTOM-001](https://custom.example.com/CUSTOM-001)"

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00014", "US-00017", "US-12345")
    @pytest.mark.component("backend")
    def test_custom_validator_integration(self):
        """Test custom validator integration."""
        validator = CustomValidator()

        # Test valid requirement
        valid_req = {"custom_field": "valid"}
        errors = validator.validate_requirement(valid_req)
        assert len(errors) == 0

        # Test invalid requirement
        invalid_req = {"custom_field": "invalid"}
        errors = validator.validate_requirement(invalid_req)
        assert len(errors) == 1
        assert "Custom validation failed" in errors[0]

    @pytest.mark.epic("EP-00001", "EP-00005")
    @pytest.mark.user_story("US-00014", "US-00017", "US-12345")
    @pytest.mark.component("backend")
    def test_plugin_priority_system(self):
        """Test plugin priority system."""

        # Create plugins with different priorities
        class HighPriorityPlugin(BaseLinkGenerator):
            @property
            def name(self) -> str:
                return "high_priority"

            @property
            def version(self) -> str:
                return "1.0.0"

            def can_handle(self, reference_type: str) -> bool:
                return True

            def generate_link(self, reference: str, context: dict) -> str:
                return f"[HIGH]{reference}"

            def get_priority(self) -> int:
                return 90

        class LowPriorityPlugin(BaseLinkGenerator):
            @property
            def name(self) -> str:
                return "low_priority"

            @property
            def version(self) -> str:
                return "1.0.0"

            def can_handle(self, reference_type: str) -> bool:
                return True

            def generate_link(self, reference: str, context: dict) -> str:
                return f"[LOW]{reference}"

            def get_priority(self) -> int:
                return 10

        high_plugin = HighPriorityPlugin()
        low_plugin = LowPriorityPlugin()

        # Test priority values
        assert high_plugin.get_priority() > low_plugin.get_priority()

        # Plugin manager should be able to handle priorities
        manager = PluginManager()
        manager.register_plugin(high_plugin, "link_generators")
        manager.register_plugin(low_plugin, "link_generators")

        generators = manager.get_plugins_by_type("link_generators")
        assert len(generators) == 2


if __name__ == "__main__":
    pytest.main([__file__])
