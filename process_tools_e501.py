#!/usr/bin/env python3
"""
Protocol-Compliant E501 Processor for Tools Directory
Following README.md mandatory syntax validation protocols.
"""
import subprocess
import ast
from pathlib import Path

def validate_syntax(file_path):
    """Validate Python syntax following README protocol."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True
    except SyntaxError as e:
        print(f"SYNTAX ERROR in {file_path}: {e}")
        return False

def fix_common_e501_patterns(file_path):
    """Apply common E501 fixes for tools directory while preserving functionality."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        lines = content.split('\n')
        modified_lines = []

        for line in lines:
            if len(line) > 79:
                # Long function calls
                if '(' in line and ')' in line and '=' in line and len(line) > 85:
                    # Function call assignment
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * indent

                    if ' = ' in line:
                        parts = line.split(' = ', 1)
                        if len(parts) == 2 and '(' in parts[1]:
                            var_name = parts[0]
                            func_call = parts[1]

                            modified_lines.append(f'{var_name} = \\')
                            modified_lines.append(f'{indent_str}    {func_call}')
                            continue

                elif '.append(' in line and len(line) > 85:
                    # Long append statements
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * indent

                    append_idx = line.find('.append(')
                    if append_idx != -1:
                        before_append = line[:append_idx + 8]  # Include .append(
                        after_append = line[append_idx + 8:-1]  # Remove closing )

                        modified_lines.append(f'{before_append}')
                        modified_lines.append(f'{indent_str}    {after_append}')
                        modified_lines.append(f'{indent_str})')
                        continue

                elif 'print(' in line and 'f"' in line and len(line) > 85:
                    # Long f-string print statements
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * indent

                    print_start = line.find('print(')
                    if print_start != -1:
                        before_print = line[:print_start + 6]  # Include print(
                        after_print = line[print_start + 6:-1]  # Remove closing )

                        if 'f"' in after_print and len(after_print) > 40:
                            # Try to split long f-strings
                            f_start = after_print.find('f"')
                            if f_start != -1:
                                f_content = after_print[f_start+2:-1]  # Remove f" and "

                                if len(f_content) > 40:
                                    mid_point = len(f_content) // 2
                                    # Find good split point
                                    split_chars = [' ', ', ', ': ', ' - ']
                                    best_split = mid_point

                                    for char in split_chars:
                                        split_idx = f_content.find(char, mid_point-20, mid_point+20)
                                        if split_idx != -1:
                                            best_split = split_idx + len(char)
                                            break

                                    if best_split != mid_point:
                                        part1 = f_content[:best_split].rstrip()
                                        part2 = f_content[best_split:].lstrip()

                                        modified_lines.append(f'{before_print}')
                                        modified_lines.append(f'{indent_str}    f"{part1}"')
                                        modified_lines.append(f'{indent_str}    f"{part2}"')
                                        modified_lines.append(f'{indent_str})')
                                        continue

                elif 'if ' in line and ' and ' in line and len(line) > 85:
                    # Long if conditions
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * indent

                    if_start = line.find('if ')
                    if if_start != -1:
                        condition = line[if_start+3:-1]  # Remove 'if ' and ':'

                        if ' and ' in condition:
                            parts = condition.split(' and ', 1)
                            if len(parts) == 2:
                                modified_lines.append(f'{indent_str}if {parts[0]} and \\')
                                modified_lines.append(f'{indent_str}   {parts[1]}:')
                                continue

            # If no pattern matched, keep original line
            modified_lines.append(line)

        new_content = '\n'.join(modified_lines)

        if new_content != original_content:
            # Validate syntax before writing
            try:
                ast.parse(new_content)
                with open(file_path, 'w', encoding='utf-8') as f:
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
    """Process tools files following README protocols."""
    tools_dir = Path('tools')
    processed = 0
    fixed = 0

    # Get all Python tools files
    tools_files = list(tools_dir.glob("*.py"))

    print(f"Processing {len(tools_files)} tools files...")

    for tools_file in tools_files:
        if not validate_syntax(tools_file):
            print(f"SKIP: {tools_file} has syntax errors")
            continue

        # Check for E501 violations
        try:
            result = subprocess.run(
                ['python', '-m', 'flake8', '--select=E501', str(tools_file)],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                continue  # No violations
        except Exception:
            continue

        # Apply fixes
        if fix_common_e501_patterns(tools_file):
            # Validate syntax after changes (mandatory protocol)
            if validate_syntax(tools_file):
                print(f"FIXED: {tools_file}")
                fixed += 1
            else:
                print(f"SYNTAX ERROR after fix in {tools_file}")

        processed += 1

        # Limit for safety
        if processed >= 60:
            break

    print(f"\nProcessed {processed} files, fixed {fixed} files")

if __name__ == '__main__':
    main()