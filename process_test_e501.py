#!/usr/bin/env python3
"""
Protocol-Compliant E501 Processor for Tests Directory
Following README.md mandatory syntax validation protocols.
"""

import subprocess
import ast
from pathlib import Path


def validate_syntax(file_path):
    """Validate Python syntax following README protocol."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        ast.parse(content)
        return True
    except SyntaxError as e:
        print(f"SYNTAX ERROR in {file_path}: {e}")
        return False


def fix_common_e501_patterns(file_path):
    """Apply common E501 fixes while preserving functionality."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        lines = content.split("\n")
        modified_lines = []

        for line in lines:
            if len(line) > 79:
                # Common patterns that can be safely split
                if "description=" in line and 'f"' in line:
                    # Long f-string descriptions
                    indent = len(line) - len(line.lstrip())
                    indent_str = " " * indent

                    if line.strip().endswith(","):
                        # Multi-line f-string with continuation
                        desc_start = line.find("description=")
                        if desc_start != -1:
                            before_desc = line[:desc_start]
                            desc_part = line[desc_start:].rstrip(",")

                            # Extract the f-string content
                            if 'f"' in desc_part:
                                f_start = desc_part.find('f"')
                                f_content = desc_part[
                                    f_start + 2 : -1
                                ]  # Remove f" and "

                                if len(f_content) > 40:  # If substantial content
                                    mid_point = len(f_content) // 2
                                    # Find good split point (space, comma, colon)
                                    split_chars = [" ", ", ", ": ", "; "]
                                    best_split = mid_point

                                    for char in split_chars:
                                        split_idx = f_content.find(
                                            char, mid_point - 20, mid_point + 20
                                        )
                                        if split_idx != -1:
                                            best_split = split_idx + len(char)
                                            break

                                    if best_split != mid_point:
                                        part1 = f_content[:best_split].rstrip()
                                        part2 = f_content[best_split:].lstrip()

                                        modified_lines.append(
                                            f"{before_desc}description=("
                                        )
                                        modified_lines.append(
                                            f'{indent_str}    f"{part1}"'
                                        )
                                        modified_lines.append(
                                            f'{indent_str}    f"{part2}"'
                                        )
                                        modified_lines.append(f"{indent_str}),")
                                        continue

                elif ".append(" in line and len(line) > 85:
                    # Long append statements
                    indent = len(line) - len(line.lstrip())
                    indent_str = " " * indent

                    append_idx = line.find(".append(")
                    if append_idx != -1:
                        before_append = line[: append_idx + 8]  # Include .append(
                        after_append = line[append_idx + 8 : -1]  # Remove closing )

                        modified_lines.append(f"{before_append}")
                        modified_lines.append(f"{indent_str}    {after_append}")
                        modified_lines.append(f"{indent_str})")
                        continue

                elif "assert" in line and len(line) > 85:
                    # Long assert statements
                    indent = len(line) - len(line.lstrip())
                    indent_str = " " * indent

                    if " == " in line or " in " in line:
                        for op in [" == ", " in ", " != "]:
                            if op in line:
                                parts = line.split(op, 1)
                                if len(parts) == 2:
                                    modified_lines.append(f"{parts[0]} \\")
                                    modified_lines.append(
                                        f"{indent_str}    {op.strip()} {parts[1]}"
                                    )
                                    break
                        else:
                            modified_lines.append(line)
                        continue

            # If no pattern matched, keep original line
            modified_lines.append(line)

        new_content = "\n".join(modified_lines)

        if new_content != original_content:
            # Validate syntax before writing
            try:
                ast.parse(new_content)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return True
            except SyntaxError:
                print(f"SYNTAX ERROR would occur in {file_path}, keeping original")
                return False

        return False  # No changes made

    except Exception as e:
        print(f"ERROR processing {file_path}: {e}")
        return False


def main():
    """Process test files following README protocols."""
    tests_dir = Path("tests")
    processed = 0
    fixed = 0

    # Get all Python test files
    test_files = list(tests_dir.rglob("*.py"))

    print(f"Processing {len(test_files)} test files...")

    for test_file in test_files:
        if not validate_syntax(test_file):
            print(f"SKIP: {test_file} has syntax errors")
            continue

        # Check for E501 violations
        try:
            result = subprocess.run(
                ["python", "-m", "flake8", "--select=E501", str(test_file)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                continue  # No violations
        except Exception:
            continue

        # Apply fixes
        if fix_common_e501_patterns(test_file):
            # Validate syntax after changes (mandatory protocol)
            if validate_syntax(test_file):
                print(f"FIXED: {test_file}")
                fixed += 1
            else:
                print(f"SYNTAX ERROR after fix in {test_file}")
                # Restore original would go here in production

        processed += 1

        # Limit for safety
        if processed >= 50:
            break

    print(f"\nProcessed {processed} files, fixed {fixed} files")


if __name__ == "__main__":
    main()
