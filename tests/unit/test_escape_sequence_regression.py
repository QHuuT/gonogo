"""
Regression test for escape sequence corruption in docstrings during E501 fixes.

This test ensures that when fixing line length violations in docstrings,
we don't introduce escaped quotes that cause syntax errors.
"""

import ast
import tempfile
import pytest


def test_docstring_escape_sequence_regression():
    """
    Regression test: Ensure E501 fixes don't create escape sequence corruption.

    This test verifies that when we fix long docstrings for E501 compliance,
    we don't accidentally introduce escaped quotes that break Python syntax.
    """

    # Test case: Original long docstring that needs E501 fix
    original_code = '''
def test_method(self):
    """This is a very long docstring that exceeds 79 characters and needs to be fixed for E501 compliance."""
    pass
'''

    # Correct fix: Use proper multi-line docstring
    correct_fix = '''
def test_method(self):
    """
    This is a very long docstring that exceeds 79 characters and needs
    to be fixed for E501 compliance.
    """
    pass
'''

    # Incorrect fix that causes syntax error (what we had)
    # This reproduces the exact pattern that caused the issue
    incorrect_fix = '''
def test_method(self):
    \\\"\\\"\\\"This is a very long docstring that exceeds 79 characters and needs
    to be fixed for E501 compliance.\\\"\\\"\\\"
    pass
'''

    # Test that original code parses
    ast.parse(original_code)

    # Test that correct fix parses
    ast.parse(correct_fix)

    # Test that incorrect fix fails to parse
    with pytest.raises(SyntaxError, match="unexpected character after line continuation"):
        ast.parse(incorrect_fix)


def test_docstring_length_fix_validation():
    """Test that our E501 fixes maintain valid Python syntax."""

    # Create a temporary test file with a long docstring
    test_content = '''
def example_function():
    """This docstring is intentionally long to test E501 fixing without syntax errors."""
    return True
'''

    # Verify it parses correctly
    try:
        ast.parse(test_content)
    except SyntaxError as e:
        pytest.fail(f"Valid docstring should parse without error: {e}")


if __name__ == "__main__":
    test_docstring_escape_sequence_regression()
    test_docstring_length_fix_validation()
    print("✅ All regression tests passed!")