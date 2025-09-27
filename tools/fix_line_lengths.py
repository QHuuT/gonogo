#!/usr/bin/env python3
"""
Automated Line Length Fixer

Systematically fixes common E501 line length violations using pattern matching.
Part of comprehensive technical debt resolution.
"""

import re
import subprocess
import sys
from pathlib import Path


def run_flake8(path):
    """Get E501 violations for a file."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", path, "--select=E501"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except Exception:
        return []


def fix_common_patterns(content):
    """Fix common line length violation patterns."""

    # Pattern 1: Long function calls with multiple arguments
    content = re.sub(
        r"(\w+\()([^)]{80,})\)",
        lambda m: format_function_call(m.group(1), m.group(2)),
        content,
    )

    # Pattern 2: Long dictionary definitions
    content = re.sub(
        r"(\{)([^}]{80,})(\})",
        lambda m: format_dict(m.group(1), m.group(2), m.group(3)),
        content,
    )

    # Pattern 3: Long string concatenations
    content = re.sub(r'f"([^"]{80,})"', lambda m: format_f_string(m.group(1)), content)

    return content


def format_function_call(opener, args_str):
    """Format long function calls."""
    if len(opener + args_str + ")") <= 79:
        return opener + args_str + ")"

    # Split arguments by comma
    args = [arg.strip() for arg in args_str.split(",")]
    if len(args) <= 1:
        return opener + args_str + ")"

    formatted = opener + "\n"
    for i, arg in enumerate(args):
        if i < len(args) - 1:
            formatted += f"    {arg},\n"
        else:
            formatted += f"    {arg}\n"
    formatted += ")"
    return formatted


def format_dict(opener, content_str, closer):
    """Format long dictionary definitions."""
    if len(opener + content_str + closer) <= 79:
        return opener + content_str + closer

    # Simple formatting for now
    return opener + "\n    " + content_str.replace(", ", ",\n    ") + "\n" + closer


def format_f_string(content_str):
    """Format long f-strings."""
    if len(content_str) <= 75:  # Account for f" and "
        return f'f"{content_str}"'

    # Break at natural points
    parts = content_str.split(" ")
    if len(parts) > 1:
        mid = len(parts) // 2
        part1 = " ".join(parts[:mid])
        part2 = " ".join(parts[mid:])
        return f'(\n    f"{part1} "\n    f"{part2}"\n)'

    return f'f"{content_str}"'


def fix_file(file_path):
    """Fix line length violations in a single file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_violations = len(run_flake8(file_path))
        if original_violations == 0:
            return 0

        # Apply fixes
        fixed_content = fix_common_patterns(content)

        # Write back if changed
        if fixed_content != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)

            new_violations = len(run_flake8(file_path))
            return max(0, original_violations - new_violations)

        return 0
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return 0


def main():
    """Main function to fix line lengths in src/ directory."""
    src_dir = Path(__file__).parent.parent / "src"
    total_fixed = 0

    print("Running automated line length fixes...")

    # Find Python files with E501 violations
    python_files = list(src_dir.rglob("*.py"))

    for file_path in python_files:
        try:
            violations_before = len(run_flake8(str(file_path)))
            if violations_before > 0:
                fixed = fix_file(str(file_path))
                if fixed > 0:
                    total_fixed += fixed
                    print(f"FIXED {file_path.relative_to(src_dir)}:{fixed} violations")
        except Exception as e:
            print(f"ERROR processing {file_path}: {e}")

    print(f"\nTotal violations fixed: {total_fixed}")

    # Run final count
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "src/", "--select=E501", "--count"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        remaining = (
            result.stdout.strip().split("\n")[-1] if result.stdout.strip() else "0"
        )
        print(f"Remaining E501 violations in src/: {remaining}")
    except Exception:
        print("Could not determine remaining violation count")


if __name__ == "__main__":
    main()
