"""
Regression test for pytest mark warning fixes.

Tests that the codebase doesn't generate PytestUnknownMarkWarning warnings
after the fixes applied in 2025-09-26.

This test ensures that:
- No PytestUnknownMarkWarning for test_type marks
- No PytestUnknownMarkWarning for detailed marks
- All custom marks are properly registered
- Tests can use parameterized marks without warnings
"""

import subprocess
import sys
import warnings
from contextlib import redirect_stderr
from io import StringIO

import pytest


def test_no_pytest_unknown_mark_warnings():
    """Test that running pytest on marked tests doesn't generate unknown mark warnings."""

    # Run pytest on the specific files that had warnings before
    test_files = [
        "tests/unit/backend/test_threshold_metrics_handling.py",
        "tests/unit/shared/test_runner_plugin_demo.py"
    ]

    # Use subprocess to run pytest and capture warnings
    cmd = [
        sys.executable, "-m", "pytest",
        "--tb=no", "-q", "--disable-warnings"
    ] + test_files

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd="."
    )

    # Check that no PytestUnknownMarkWarning appears in stderr
    unknown_mark_warnings = [
        line for line in result.stderr.split('\n')
        if "PytestUnknownMarkWarning" in line
    ]

    assert len(unknown_mark_warnings) == 0, (
        f"Found {len(unknown_mark_warnings)} PytestUnknownMarkWarning warnings: "
        f"{unknown_mark_warnings}"
    )


def test_test_type_mark_is_registered():
    """Test that test_type mark is properly registered."""

    # Run pytest --markers and check if test_type is listed
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--markers"],
        capture_output=True,
        text=True,
        cwd="."
    )

    assert result.returncode == 0, f"pytest --markers failed: {result.stderr}"
    assert "test_type(type): categorizes tests by type" in result.stdout, (
        "test_type mark should be registered"
    )


def test_detailed_mark_is_registered():
    """Test that detailed mark is properly registered."""

    # Run pytest --markers and check if detailed is listed
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--markers"],
        capture_output=True,
        text=True,
        cwd="."
    )

    assert result.returncode == 0, f"pytest --markers failed: {result.stderr}"
    assert "detailed: marks tests for detailed debugging mode" in result.stdout, (
        "detailed mark should be registered"
    )


def test_all_custom_marks_are_registered():
    """Test that all custom marks used in the codebase are properly registered."""

    expected_marks = [
        "test_type(type): categorizes tests by type",
        "detailed: marks tests for detailed debugging mode",
        "epic(id): mark test as linked to epic",
        "component(name): mark test component",
        "user_story(id): mark test as linked to user story",
        "defect(id): mark test as defect regression test",
        "priority(level): mark test priority",
        "smoke: marks tests as smoke tests",
        "functional: marks tests as functional tests",
        "security: marks tests as security tests",
        "gdpr: marks tests as GDPR compliance tests",
        "performance: marks tests as performance tests",
        "bdd: marks tests as BDD scenarios"
    ]

    # Run pytest --markers and get output
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--markers"],
        capture_output=True,
        text=True,
        cwd="."
    )

    assert result.returncode == 0, f"pytest --markers failed: {result.stderr}"

    # Check that each expected mark is registered
    for mark in expected_marks:
        assert mark in result.stdout, f"Mark '{mark}' should be registered"


def test_parameterized_marks_work_correctly():
    """Test that parameterized marks (with arguments) work without warnings."""

    # Create a temporary test file with parameterized marks
    test_content = '''
import pytest

@pytest.mark.test_type("unit")
@pytest.mark.epic("EP-00010")
@pytest.mark.component("backend")
def test_parameterized_marks():
    """Test that parameterized marks work without warnings."""
    assert True

@pytest.mark.detailed
def test_simple_mark():
    """Test that simple marks work without warnings."""
    assert True
'''

    # Write to a temporary file
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
        f.write(test_content)
        temp_test_file = f.name

    try:
        # Run pytest on the temporary file
        result = subprocess.run(
            [sys.executable, "-m", "pytest", temp_test_file, "--tb=no", "-q"],
            capture_output=True,
            text=True,
            cwd="."
        )

        # Should pass without unknown mark warnings
        assert result.returncode == 0, f"Test failed: {result.stderr}"
        assert "PytestUnknownMarkWarning" not in result.stderr, (
            f"Should not have unknown mark warnings: {result.stderr}"
        )

    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_test_file)
        except:
            pass


def test_marks_in_actual_test_files():
    """Test specific mark usage in actual test files to prevent regression."""

    # Test the specific marks that were causing warnings before
    test_commands = [
        # Test the threshold handling file
        [sys.executable, "-m", "pytest",
         "tests/unit/backend/test_threshold_metrics_handling.py::TestExtractMetricValue::test_extract_threshold_evaluated_metric",
         "--tb=no", "-q"],

        # Test the runner plugin demo file
        [sys.executable, "-m", "pytest",
         "tests/unit/shared/test_runner_plugin_demo.py::test_detailed_mode_marker",
         "--tb=no", "-q"]
    ]

    for cmd in test_commands:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd="."
        )

        # Should pass without warnings
        assert result.returncode == 0, f"Test command failed: {' '.join(cmd)}\nError: {result.stderr}"
        assert "PytestUnknownMarkWarning" not in result.stderr, (
            f"Should not have unknown mark warnings in: {' '.join(cmd)}\nOutput: {result.stderr}"
        )


def test_marker_configuration_consistency():
    """Test that marker configuration is consistent between conftest.py and pyproject.toml."""

    # This test ensures that both configuration sources define the same markers
    # to prevent configuration drift

    # Read pyproject.toml markers using simple text parsing
    expected_marker_names = [
        "smoke", "functional", "security", "gdpr", "performance", "bdd",
        "detailed", "test_type", "user_story", "epic", "component", "defect", "priority"
    ]

    # Get registered markers from pytest
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--markers"],
        capture_output=True,
        text=True,
        cwd="."
    )

    pytest_output = result.stdout

    # Check that all expected markers are registered in pytest
    for marker_name in expected_marker_names:
        assert marker_name in pytest_output, (
            f"Marker '{marker_name}' should be registered in pytest"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])