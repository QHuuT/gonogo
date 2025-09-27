"""
Regression Test: Syntax Validation

Prevents syntax errors from being introduced during code refactoring,
specifically targeting patterns that caused failures during line length fixes.

Related Issue: SYNTAX-2025-001 - Critical syntax errors during technical debt cleanup
"""

import ast
import glob
import re
from pathlib import Path
from typing import List, Tuple

import pytest


class TestSyntaxValidation:
    """Comprehensive syntax validation to prevent regression of syntax errors."""

    def test_all_python_files_have_valid_syntax(self):
        """Ensure all Python files in src/ have valid syntax."""
        python_files = glob.glob("src/**/*.py", recursive=True)
        syntax_errors = []

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast.parse(content, filename=file_path)
            except SyntaxError as e:
                syntax_errors.append(f"{file_path}:{e.lineno}: {e.msg}")
            except Exception as e:
                syntax_errors.append(f"{file_path}: Unexpected error: {e}")

        if syntax_errors:
            pytest.fail(
                f"Syntax errors found in {len(syntax_errors)} files:\n" +
                "\n".join(syntax_errors)
            )

    def test_sqlalchemy_table_args_patterns(self):
        """Validate SQLAlchemy __table_args__ don't have extra parentheses."""
        model_files = glob.glob("src/be/models/**/*.py", recursive=True)
        issues = []

        for file_path in model_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()

                # Look for __table_args__ definitions
                in_table_args = False
                paren_count = 0

                for i, line in enumerate(lines, 1):
                    if "__table_args__" in line and "=" in line:
                        in_table_args = True
                        paren_count = line.count('(') - line.count(')')
                    elif in_table_args:
                        paren_count += line.count('(') - line.count(')')

                        # Check for suspicious patterns that caused our bug
                        if re.search(r'^\s*\),\s*\),\s*$', line):
                            issues.append(
                                f"{file_path}:{i}: Potential extra closing parenthesis in __table_args__"
                            )

                        if paren_count <= 0:
                            in_table_args = False

        if issues:
            pytest.fail(f"SQLAlchemy table args issues:\n" + "\n".join(issues))

    def test_f_string_literal_newlines(self):
        """Detect literal newlines in f-strings that cause syntax errors."""
        python_files = glob.glob("src/**/*.py", recursive=True)
        issues = []

        for file_path in python_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()

                for i, line in enumerate(lines, 1):
                    # Look for f-strings with literal \n
                    if re.search(r'f"[^"]*\\n\s*"', line) or re.search(r"f'[^']*\\n\s*'", line):
                        issues.append(
                            f"{file_path}:{i}: Potential literal newline in f-string"
                        )

        if issues:
            pytest.fail(f"F-string literal newline issues:\n" + "\n".join(issues))

    def test_regex_patterns_use_raw_strings(self):
        """Ensure regex patterns with escape sequences use raw strings."""
        python_files = glob.glob("src/**/*.py", recursive=True) + glob.glob("tests/**/*.py", recursive=True)
        issues = []

        for file_path in python_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()

                for i, line in enumerate(lines, 1):
                    # Look for f-strings or regular strings with regex escape sequences
                    if re.search(r'f"[^"]*\\[()[\]{}.*+?^$|\\][^"]*"', line):
                        if not line.strip().startswith('rf"'):
                            issues.append(
                                f"{file_path}:{i}: F-string with regex escapes should use rf'' prefix"
                            )

        if issues:
            pytest.fail(f"Regex pattern raw string issues:\n" + "\n".join(issues))

    def test_common_syntax_error_patterns(self):
        """Test for common patterns that cause syntax errors during refactoring."""
        python_files = glob.glob("src/**/*.py", recursive=True)
        issues = []

        for file_path in python_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()

                for i, line in enumerate(lines, 1):
                    # Check for common problematic patterns
                    checks = [
                        (r'^\s*\),\s*\),\s*$', "Double closing parentheses"),
                        (r'f"[^"]*"\s*\\\s*$', "F-string with trailing backslash"),
                        (r'"""[^"]*\\n[^"]*"""', "Triple quote with literal newline"),
                    ]

                    for pattern, description in checks:
                        if re.search(pattern, line):
                            issues.append(f"{file_path}:{i}: {description}")

        if issues:
            pytest.fail(f"Common syntax error patterns found:\n" + "\n".join(issues))


class TestSpecificVulnerableFiles:
    """Test files that were specifically affected by syntax errors."""

    def test_traceability_models_syntax(self):
        """Ensure traceability models maintain valid syntax."""
        model_files = [
            "src/be/models/traceability/test.py",
            "src/be/models/traceability/epic.py",
            "src/be/models/traceability/user_story.py",
            "src/be/models/traceability/defect.py",
        ]

        for file_path in model_files:
            if Path(file_path).exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                try:
                    ast.parse(content, filename=file_path)
                except SyntaxError as e:
                    pytest.fail(f"Syntax error in {file_path}:{e.lineno}: {e.msg}")

    def test_rtm_plugins_syntax(self):
        """Ensure RTM plugins maintain valid syntax."""
        plugin_files = glob.glob("src/shared/utils/rtm_plugins/**/*.py", recursive=True)

        for file_path in plugin_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            try:
                ast.parse(content, filename=file_path)
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {file_path}:{e.lineno}: {e.msg}")

    def test_integration_test_syntax(self):
        """Ensure integration tests maintain valid syntax."""
        test_files = glob.glob("tests/integration/**/*.py", recursive=True)

        for file_path in test_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            try:
                ast.parse(content, filename=file_path)
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {file_path}:{e.lineno}: {e.msg}")


if __name__ == "__main__":
    # Allow running this test directly for quick validation
    pytest.main([__file__, "-v"])