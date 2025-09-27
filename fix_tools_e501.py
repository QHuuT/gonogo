#!/usr/bin/env python3
"""
Automated E501 Line Length Fixer for Tools Directory
Batch processes E501 violations with common patterns.
"""

import subprocess
import re
from pathlib import Path


def get_e501_violations(file_path):
    """Get E501 violations for a file."""
    try:
        result = subprocess.run(
            [
                "python",
                "-m",
                "flake8",
                "--select=E501",
                "--show-source",
                str(file_path),
            ],
            capture_output=True,
            text=True,
            cwd="tools",
        )
        if result.returncode == 0:
            return []  # No violations

        violations = []
        lines = result.stdout.strip().split("\n")
        for line in lines:
            if ":E501:" in line and "line too long" in line:
                parts = line.split(":")
                if len(parts) >= 2:
                    line_num = int(parts[1])
                    violations.append(line_num)
        return violations
    except Exception as e:
        print(f"Error checking {file_path}: {e}")
        return []


def apply_common_e501_fixes(file_path):
    """Apply common E501 line length fixes."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Common fix patterns
        fixes = [
            # Long f-strings
            (r'([ ]*)print\(f"(.{80,})"\)', r'\1print(\n\1    f"\2"\n\1)'),
            # Long argument lists
            (r"(\w+)\(([^)]{80,})\)", r"\1(\n    \2\n)"),
            # Long string concatenations
            (r'(["\'])(.{80,})\1', r"\1\2\1"),
        ]

        # Apply simple line breaks for long lines
        lines = content.split("\n")
        new_lines = []

        for line in lines:
            if len(line) > 79:
                # Simple heuristic fixes
                if "print(f" in line and len(line) > 79:
                    # Split long print statements
                    indent = len(line) - len(line.lstrip())
                    indent_str = " " * indent
                    if 'print(f"' in line:
                        match = re.match(r'(\s*)print\(f"(.+)"\)', line)
                        if match:
                            prefix = match.group(1)
                            msg = match.group(2)
                            if len(msg) > 60:
                                # Simple split at comma or space
                                split_points = [
                                    m.start() for m in re.finditer(r"[, ]", msg)
                                ]
                                mid_point = len(msg) // 2
                                best_split = min(
                                    split_points, key=lambda x: abs(x - mid_point)
                                )
                                if best_split > 20 and best_split < len(msg) - 20:
                                    part1 = msg[:best_split]
                                    part2 = msg[best_split:].lstrip()
                                    new_lines.append(f"{prefix}print(")
                                    new_lines.append(f'{prefix}    f"{part1}"')
                                    new_lines.append(f'{prefix}    f"{part2}"')
                                    new_lines.append(f"{prefix})")
                                    continue

                # For other long lines, just add them as-is for now
                new_lines.append(line)
            else:
                new_lines.append(line)

        content = "\n".join(new_lines)

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        return False

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    """Main function."""
    tools_dir = Path("tools")
    python_files = list(tools_dir.glob("*.py"))

    processed = 0
    fixed = 0

    for py_file in python_files:
        if py_file.name in [
            "add_epic_metrics_columns.py",
            "add_test_markers.py",
            "update_user_story_from_github.py",
            "validate_test_associations.py",
        ]:
            continue  # Already processed

        print(f"Processing {py_file.name}...")

        # Check syntax first
        try:
            subprocess.run(
                ["python", "-m", "py_compile", str(py_file)],
                check=True,
                capture_output=True,
                cwd="tools",
            )
        except subprocess.CalledProcessError:
            print(f"  SKIP: Syntax error in {py_file.name}")
            continue

        violations_before = get_e501_violations(py_file.name)
        if not violations_before:
            print("  OK: No E501 violations")
            processed += 1
            continue

        print(f"  Found {len(violations_before)} E501 violations")

        # Apply fixes
        if apply_common_e501_fixes(py_file):
            # Check if violations were reduced
            violations_after = get_e501_violations(py_file.name)
            if len(violations_after) < len(violations_before):
                print(
                    f"  FIXED: {len(violations_before) - len(violations_after)} violations"
                )
                fixed += 1
            else:
                print(f"  PARTIAL: Still has {len(violations_after)} violations")

        processed += 1

        if processed >= 10:  # Limit for testing
            break

    print(f"\nProcessed {processed} files, fixed {fixed} files")


if __name__ == "__main__":
    main()
