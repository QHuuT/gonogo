"""
Simple test to demonstrate the enhanced test runner plugin functionality.
This test can run without external dependencies.
"""

import pytest


@pytest.mark.epic("EP-00007")
@pytest.mark.component("shared")
def test_plugin_mode_detection():
    """Test that can detect execution mode (basic functionality demo)."""
    # This is a simple test that should always pass
    assert True


@pytest.mark.epic("EP-00007")
@pytest.mark.component("shared")
def test_plugin_type_detection():
    """Test that can detect test type (basic functionality demo)."""
    # This test demonstrates test type filtering
    assert 1 + 1 == 2


@pytest.mark.epic("EP-00007")
@pytest.mark.component("shared")
@pytest.mark.detailed
def test_detailed_mode_marker():
    """Test with detailed mode marker."""
    # This test should show extra info in detailed mode
    test_data = {"key": "value", "number": 42}
    assert test_data["key"] == "value"
    assert test_data["number"] == 42


class TestRunnerPluginDemo:
    """Demo test class for plugin functionality."""

    def test_silent_mode_compatible(self):
        """Test that works well in silent mode."""
        assert "test" in "testing"

    def test_verbose_mode_compatible(self):
        """Test that provides good output in verbose mode."""
        items = [1, 2, 3, 4, 5]
        result = sum(items)
        assert result == 15

    def test_standard_mode_compatible(self):
        """Test that works with standard mode."""
        assert len("hello") == 5
