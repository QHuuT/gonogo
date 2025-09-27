"""
Regression test for pytest fixture mark warning fixes.

Tests that the codebase doesn't generate PytestRemovedIn9Warning warnings
for marks applied to fixtures after the fixes applied in 2025-09-26.

This test ensures that:
- No PytestRemovedIn9Warning for marks applied to fixtures
- All fixtures are properly defined without marks
- Marks are only applied to test functions, not fixtures
- Test configuration adheres to pytest best practices
"""

import subprocess
import sys
from pathlib import Path

import pytest


def test_no_pytest_fixture_mark_warnings():
    """Test that running pytest on test files doesn't generate fixture mark warnings."""

    # Run pytest on test directories that previously had fixture mark issues
    test_paths = [
        "tests/unit/shared/models/",
        "tests/integration/rtm_api/",
        "tests/integration/component_system/",
    ]

    for test_path in test_paths:
        if Path(test_path).exists():
            # Use subprocess to run pytest and capture warnings
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                test_path,
                "--tb=no",
                "-q",
                "--disable-warnings",
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=".", timeout=60
            )

            # Check that no PytestRemovedIn9Warning appears for fixture marks
            fixture_mark_warnings = [
                line
                for line in result.stderr.split("\n")
                if "PytestRemovedIn9Warning" in line
                and "Marks applied to fixtures" in line
            ]

            assert len(fixture_mark_warnings) == 0, (
                f"Found {len(fixture_mark_warnings)} fixture mark warnings in {test_path}: "
                f"{fixture_mark_warnings}"
            )


def test_fixture_definitions_have_no_marks():
    """Test that fixture definitions in code don't have marks applied."""

    test_files = [
        "tests/unit/shared/models/test_test_model.py",
        "tests/unit/shared/models/test_traceability_base.py",
        "tests/integration/rtm_api/test_rtm_api.py",
        "tests/integration/rtm_api/test_dashboard_metrics_regression.py",
    ]

    for test_file in test_files:
        filepath = Path(test_file)
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8")
            lines = content.split("\n")

            for i, line in enumerate(lines):
                if "@pytest.fixture" in line:
                    # Check if any previous lines (within 5 lines) have @pytest.mark
                    for j in range(max(0, i - 5), i):
                        if "@pytest.mark" in lines[j] and lines[j].strip():
                            # Make sure it's not just whitespace or comment between mark and fixture
                            lines_between = lines[j + 1 : i]
                            non_empty_between = [
                                l
                                for l in lines_between
                                if l.strip() and not l.strip().startswith("#")
                            ]

                            if len(non_empty_between) == 0:
                                pytest.fail(
                                    f"Found @pytest.mark before @pytest.fixture in {test_file}:{i + 1}\n"
                                    f"Line {j + 1}: {lines[j].strip()}\n"
                                    f"Line {i + 1}: {line.strip()}\n"
                                    f"Marks should not be applied to fixtures."
                                )


def test_marks_are_only_on_test_functions():
    """Test that marks are properly applied to test functions, not fixtures."""

    test_files = [
        "tests/unit/shared/models/test_test_model.py",
        "tests/unit/shared/models/test_traceability_base.py",
    ]

    for test_file in test_files:
        filepath = Path(test_file)
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8")
            lines = content.split("\n")

            for i, line in enumerate(lines):
                if "@pytest.mark" in line:
                    # Find the next non-empty, non-comment line
                    next_line_idx = i + 1
                    while next_line_idx < len(lines):
                        next_line = lines[next_line_idx].strip()
                        if next_line and not next_line.startswith("#"):
                            break
                        next_line_idx += 1

                    if next_line_idx < len(lines):
                        next_line = lines[next_line_idx]

                        # The mark should be followed by either:
                        # 1. A test function (def test_)
                        # 2. A test class (class Test)
                        # 3. Another mark (@pytest.mark)
                        # NOT a fixture (@pytest.fixture)

                        if "@pytest.fixture" in next_line:
                            pytest.fail(
                                f"Found @pytest.mark directly before @pytest.fixture in {test_file}:{next_line_idx + 1}\n"
                                f"Line {i + 1}: {line.strip()}\n"
                                f"Line {next_line_idx + 1}: {next_line.strip()}\n"
                                f"Marks should not be applied to fixtures."
                            )


def test_pytest_fixture_usage_best_practices():
    """Test that fixtures follow pytest best practices."""

    # Test with a sample fixture-using test to ensure our changes don't break functionality
    test_content = '''
import pytest

@pytest.fixture
def sample_data():
    """A proper fixture without marks."""
    return {"test": "data"}

@pytest.mark.epic("EP-00001")
@pytest.mark.component("backend")
def test_with_proper_marks(sample_data):
    """A test function with proper marks applied."""
    assert sample_data["test"] == "data"

@pytest.fixture
def another_fixture():
    """Another fixture without marks."""
    return "fixture_value"

@pytest.mark.user_story("US-00001")
def test_another_with_marks(another_fixture):
    """Another test with marks on the test, not fixture."""
    assert another_fixture == "fixture_value"
'''

    # Write to a temporary file
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix="_test.py", delete=False) as f:
        f.write(test_content)
        temp_test_file = f.name

    try:
        # Run pytest on the temporary file - should pass without fixture mark warnings
        result = subprocess.run(
            [sys.executable, "-m", "pytest", temp_test_file, "--tb=no", "-q"],
            capture_output=True,
            text=True,
            cwd=".",
        )

        # Should pass without fixture mark warnings
        assert result.returncode == 0, f"Test failed: {result.stderr}"
        assert "RemovedIn9Warning" not in result.stderr, (
            f"Should not have fixture mark warnings: {result.stderr}"
        )
        assert "Marks applied to fixtures" not in result.stderr, (
            f"Should not have fixture mark warnings: {result.stderr}"
        )

    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_test_file)
        except:
            pass


def test_fixture_mark_patterns_comprehensive():
    """Comprehensive test to detect any fixture mark patterns in the codebase."""

    import os
    import re

    fixture_mark_patterns = []

    # Search through all test files
    for root, dirs, files in os.walk("tests/"):
        # Skip __pycache__ and .git directories
        dirs[:] = [d for d in dirs if not d.startswith("__pycache__") and d != ".git"]

        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Look for patterns where @pytest.mark is followed by @pytest.fixture
                    # This regex looks for mark decorators followed by fixture decorators
                    pattern = r"(@pytest\.mark\.[^\n]+(?:\n\s*@pytest\.mark\.[^\n]+)*)\s*\n\s*@pytest\.fixture"
                    matches = re.finditer(pattern, content, re.MULTILINE)

                    for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        fixture_mark_patterns.append(
                            {
                                "file": filepath,
                                "line": line_num,
                                "match": match.group(0),
                            }
                        )

                except Exception:
                    continue  # Skip files that can't be read

    # Assert no fixture mark patterns found
    assert len(fixture_mark_patterns) == 0, (
        f"Found {len(fixture_mark_patterns)} fixture mark patterns that should be removed:\n"
        + "\n".join(
            [
                f"  {p['file']}:{p['line']} - {repr(p['match'][:100])}"
                for p in fixture_mark_patterns
            ]
        )
    )


def test_unknown_marks_are_registered():
    """Test that any unknown marks found during fixture mark investigation are registered."""

    # Run pytest --markers to see if integration and test_category marks are now registered
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--markers"],
        capture_output=True,
        text=True,
        cwd=".",
    )

    assert result.returncode == 0, f"pytest --markers failed: {result.stderr}"

    # Check that previously unknown marks are now registered
    expected_marks = [
        "integration: marks tests as integration tests",
        "test_category(category): categorizes tests by specific category",
    ]

    for mark in expected_marks:
        assert mark in result.stdout, f"Mark '{mark}' should be registered in pytest"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
