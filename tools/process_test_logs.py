#!/usr/bin/env python3
"""
Test Log Post-Processor

Processes test log files to extract failures and stack traces,
placing them at the top for easy review.

Usage:
    python tools/process_test_logs.py quality/logs/unit_tests_20250926.log
    python tools/process_test_logs.py quality/logs/unit_tests_20250926.log --output quality/logs/processed_unit_tests.log
"""

import re
import sys
import argparse
from pathlib import Path
from datetime import datetime


def extract_failures_and_traces(log_content):
    """Extract all test failures and their complete stack traces with numbered tags."""
    failures = []
    lines = log_content.split('\n')

    # Find all FAILED test lines
    failed_tests = []
    for i, line in enumerate(lines):
        if ' FAILED ' in line and '::' in line:
            failed_tests.append((i, line.strip()))

    if not failed_tests:
        return [], []

    # Find the FAILURES section which contains stack traces
    failures_section_start = None
    failures_section_end = None

    for i, line in enumerate(lines):
        if line.strip() == "FAILURES" or "== FAILURES ==" in line:
            failures_section_start = i
            break

    if failures_section_start is not None:
        # Find the end of failures section (usually before short test summary)
        for i in range(failures_section_start + 1, len(lines)):
            if ("== short test summary info ==" in lines[i] or
                "====" in lines[i] and "test session starts" in lines[i] or
                lines[i].strip() == "" and i + 1 < len(lines) and "====" in lines[i + 1]):
                failures_section_end = i
                break

        if failures_section_end is None:
            failures_section_end = len(lines)

        # Extract and tag individual failures within the section
        failure_details = add_failure_tags(lines[failures_section_start:failures_section_end], failed_tests)
    else:
        failure_details = ""

    return failed_tests, failure_details


def add_failure_tags(failure_lines, failed_tests):
    """Add numbered tags to each failure for easy identification."""
    if not failure_lines or not failed_tests:
        return '\n'.join(failure_lines)

    tagged_lines = []

    # Create a mapping of test method names to failure numbers
    test_method_to_num = {}
    for i, (line_num, test_line) in enumerate(failed_tests, 1):
        # Extract test name from the failed test line
        if '::' in test_line:
            full_test_name = test_line.split(' FAILED ')[0].strip()
            # Extract just the method name (last part after ::)
            if '::' in full_test_name:
                method_name = full_test_name.split('::')[-1]
                test_method_to_num[method_name] = i
                # Also map the full class.method format
                class_method = '.'.join(full_test_name.split('::')[-2:])
                test_method_to_num[class_method] = i

    i = 0
    while i < len(failure_lines):
        line = failure_lines[i]

        # Check if this line starts a new failure section
        if line.startswith('_') and len(line) > 10 and line.endswith('_'):
            # This is likely a failure separator line like "_________________ TestClass.test_method _________________"
            # Extract the test method name
            test_identifier = line.strip('_').strip()

            # Find matching test name and assign failure number
            failure_num = None
            for test_pattern, num in test_method_to_num.items():
                if test_pattern in test_identifier or test_identifier in test_pattern:
                    failure_num = num
                    break

            if failure_num:
                # Add the failure tag before the separator line
                tag_line = f"[FAILED TEST NO-{failure_num}] {test_identifier}"
                tagged_lines.append('')
                tagged_lines.append('=' * 80)
                tagged_lines.append(tag_line)
                tagged_lines.append('=' * 80)
                tagged_lines.append(line)  # Keep the original separator line
            else:
                tagged_lines.append(line)
        else:
            tagged_lines.append(line)

        i += 1

    return '\n'.join(tagged_lines)


def create_summary_header(failed_tests, total_tests_info):
    """Create a summary header for the processed log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    header = f"""
{'='*80}
TEST FAILURE SUMMARY - PROCESSED LOG
Generated: {timestamp}
{'='*80}

FAILED TESTS OVERVIEW:
{'-'*50}
"""

    if failed_tests:
        header += f"[FAILED] {len(failed_tests)} test(s) failed:\n\n"
        for i, (line_num, test_line) in enumerate(failed_tests, 1):
            # Extract just the test name from the line
            if '::' in test_line:
                test_name = test_line.split(' FAILED ')[0].strip()
                header += f"[FAILED TEST NO-{i}] {test_name}\n"
            else:
                header += f"[FAILED TEST NO-{i}] {test_line}\n"
    else:
        header += "[SUCCESS] No test failures found!\n"

    header += f"\n{'-'*50}\n"

    # Add test summary if available
    if total_tests_info:
        header += f"EXECUTION SUMMARY:\n{total_tests_info}\n{'-'*50}\n"

    return header


def extract_test_summary(log_content):
    """Extract the test execution summary from the log."""
    lines = log_content.split('\n')

    # Look for the final test summary line
    summary_patterns = [
        r'==+ .* in [\d\.]+ seconds? ==+',
        r'==+ \d+ failed.* in [\d\.]+ seconds? ==+',
        r'==+ \d+ passed.* in [\d\.]+ seconds? ==+'
    ]

    for line in reversed(lines):
        for pattern in summary_patterns:
            if re.search(pattern, line):
                return line.strip()

    return None


def process_log_file(input_file, output_file=None):
    """Process the test log file to prioritize failures."""

    # Read the original log file with multiple encoding attempts
    original_content = None
    encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

    for encoding in encodings_to_try:
        try:
            with open(input_file, 'r', encoding=encoding) as f:
                original_content = f.read()
            print(f"[INFO] Successfully read file using {encoding} encoding")
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Error reading {input_file} with {encoding}: {e}")
            continue

    if original_content is None:
        print(f"[ERROR] Could not read {input_file} with any supported encoding")
        return False

    # Extract failures and stack traces
    failed_tests, failure_details = extract_failures_and_traces(original_content)
    test_summary = extract_test_summary(original_content)

    # Create the processed content
    header = create_summary_header(failed_tests, test_summary)

    processed_content = header

    if failure_details:
        processed_content += f"\n{'='*80}\n"
        processed_content += "DETAILED FAILURE INFORMATION:\n"
        processed_content += f"{'='*80}\n\n"
        processed_content += failure_details
        processed_content += f"\n\n{'='*80}\n"
        processed_content += "COMPLETE ORIGINAL LOG:\n"
        processed_content += f"{'='*80}\n\n"
    else:
        processed_content += f"\n{'='*80}\n"
        processed_content += "COMPLETE ORIGINAL LOG:\n"
        processed_content += f"{'='*80}\n\n"

    # Append the complete original log
    processed_content += original_content

    # Determine output file
    if output_file is None:
        input_path = Path(input_file)
        output_file = input_path.parent / f"processed_{input_path.name}"

    # Write the processed log
    try:
        with open(output_file, 'w', encoding='utf-8', errors='replace') as f:
            f.write(processed_content)

        print(f"[SUCCESS] Processed log created: {output_file}")

        if failed_tests:
            print(f"[FAILURES] Found {len(failed_tests)} failed test(s)")
            print(f"[INFO] Failures are now at the top of: {output_file}")
        else:
            print("[SUCCESS] No test failures found!")

        return True

    except Exception as e:
        print(f"Error writing {output_file}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Process test logs to prioritize failures and stack traces",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a log file (creates processed_filename.log)
  python tools/process_test_logs.py quality/logs/unit_tests_20250926.log

  # Specify custom output file
  python tools/process_test_logs.py quality/logs/unit_tests_20250926.log --output quality/logs/failures_first.log

  # Process the latest test log
  python tools/process_test_logs.py $(ls -t quality/logs/test_*.log | head -1)
        """
    )

    parser.add_argument('input_file', help='Path to the test log file to process')
    parser.add_argument('--output', '-o', help='Output file path (default: processed_<input_filename>)')

    args = parser.parse_args()

    # Validate input file
    if not Path(args.input_file).exists():
        print(f"[ERROR] Input file not found: {args.input_file}")
        sys.exit(1)

    # Process the log file
    success = process_log_file(args.input_file, args.output)

    if not success:
        sys.exit(1)

    print(f"\n[TIP] View failures quickly with:")
    output_path = args.output or Path(args.input_file).parent / f"processed_{Path(args.input_file).name}"
    print(f"   head -50 {output_path}")


if __name__ == "__main__":
    main()