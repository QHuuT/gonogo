#!/usr/bin/env python3
"""
Fix broken string literals from automated line length fixes.
"""

import re
from pathlib import Path


def fix_broken_strings(file_path):
    """Fix broken string literals in a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Fix pattern: description="text without closing quote on same line
    # Look for description="..." followed by newline without closing quote
    pattern = r'description="([^"]*)\n([^"]*)"'
    replacement = r'description="\1 \2"'
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    # Fix specific broken patterns found in the file
    fixes = [
        # Filter descriptions
        (
            'description="Filter by component (supports comma-separated values\n)"',
            'description="Filter by component (supports comma-separated values)"',
        ),
        (
            'description="Exclude components (supports comma-separated values\n)"',
            'description="Exclude components (supports comma-separated values)"',
        ),
        (
            'description="Filter user stories by status: all,\n',
            'description="Filter user stories by status: all, ',
        ),
        (
            'description="Filter tests by type: all,\n',
            'description="Filter tests by type: all, ',
        ),
        (
            'description="Filter defects by priority: all,\n',
            'description="Filter defects by priority: all, ',
        ),
        (
            'description="Filter defects by status: all,\n',
            'description="Filter defects by status: all, ',
        ),
        ('description="Output format: json,\n', 'description="Output format: json, '),
        (
            'description="Dashboard persona: PM,\n',
            'description="Dashboard persona: PM, ',
        ),
        ('description="Export format: pdf,\n', 'description="Export format: pdf, '),
    ]

    for old, new in fixes:
        content = content.replace(old, new)

    # Additional pattern to fix multi-line strings that got broken
    # Pattern: "text\nmore_text"
    pattern = r'"([^"]*)\n([^"]*)"'

    def fix_multiline_string(match):
        line1 = match.group(1)
        line2 = match.group(2)
        # Only fix if it looks like a description that was broken
        if "description=" in line1 or any(
            word in line1.lower() for word in ["filter", "format", "persona", "export"]
        ):
            return f'"{line1} {line2.strip()}"'
        return match.group(0)

    content = re.sub(pattern, fix_multiline_string, content, flags=re.MULTILINE)

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main():
    file_path = Path(__file__).parent.parent / "src" / "be" / "api" / "rtm.py"

    if fix_broken_strings(file_path):
        print(f"Fixed broken strings in {file_path}")
    else:
        print(f"No fixes needed in {file_path}")


if __name__ == "__main__":
    main()
