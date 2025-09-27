#!/usr/bin/env python3
"""
Test Log Post-Processor

Processes test log files to extract and prioritize failures, errors, and warnings,
placing them at the top for easy review.

Processing order:
1. Test failures (highest priority)
2. Errors (second priority)
3. Warnings (third priority)
4. Complete original log

Usage:
    python tools/process_test_logs.py quality/logs/unit_tests_20250926.log
    python tools/process_test_logs.py quality/logs/unit_tests_20250926.log \
        --output quality/logs/processed_unit_tests.log
"""

import re
import sys
import argparse
from pathlib import Path
from datetime import datetime


def extract_failures_and_traces(log_content):
    """
    Extract all test failures, group similar ones, and return complete
    stack traces with numbered tags.
    """
    lines = log_content.split('\n')

    # Find all FAILED test lines
    failed_tests = []
    for i, line in enumerate(lines):
        if ' FAILED ' in line and '::' in line:
            failed_tests.append((i, line.strip()))

    if not failed_tests:
        return [], [], []

    # Group similar failures
    failure_groups = group_similar_failures(failed_tests, log_content)

    # Find the FAILURES section which contains stack traces
    failures_section_start = None
    failures_section_end = None

    for i, line in enumerate(lines):
        if (line.strip() == "FAILURES" or
                "== FAILURES ==" in line):
            failures_section_start = i
            break

    if failures_section_start is not None:
        # Find the end of failures section (usually before short test summary)
        for i in range(failures_section_start + 1, len(lines)):
            if ("== short test summary info ==" in lines[i] or
                    "====" in lines[i] and "test session starts" in lines[i] or
                    (lines[i].strip() == "" and i + 1 < len(lines) and
                     "====" in lines[i + 1])):
                failures_section_end = i
                break

        if failures_section_end is None:
            failures_section_end = len(lines)

        # Extract and tag individual failures within the section
        failure_details = add_failure_tags(
            lines[failures_section_start:failures_section_end], failed_tests)
    else:
        failure_details = ""

    return failed_tests, failure_groups, failure_details


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
        if (line.startswith('_') and len(line) > 10 and
                line.endswith('_')):
            # This is likely a failure separator line like
            # "_________________ TestClass.test_method _________________"
            # Extract the test method name
            test_identifier = line.strip('_').strip()

            # Find matching test name and assign failure number
            failure_num = None
            for test_pattern, num in test_method_to_num.items():
                if (test_pattern in test_identifier or
                        test_identifier in test_pattern):
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


def group_similar_failures(failed_tests, log_content):
    """Group similar test failures by failure type and error message."""
    failure_groups = {}
    lines = log_content.split('\n')

    for line_num, test_line in failed_tests:
        # Extract test name and failure reason
        test_name = test_line.split(' FAILED ')[0].strip()

        # Find the actual failure details in the FAILURES section
        failure_type, failure_message = extract_failure_type_and_message(
            test_name, lines)

        # Create group key based on failure type and normalized message
        group_key = create_failure_group_key(failure_type, failure_message)

        if group_key not in failure_groups:
            failure_groups[group_key] = {
                'type': failure_type,
                'message': normalize_failure_message(failure_message),
                'affected_tests': [],
                'count': 0
            }

        failure_groups[group_key]['affected_tests'].append(test_name)
        failure_groups[group_key]['count'] += 1

    return list(failure_groups.values())


def extract_failure_type_and_message(test_name, lines):
    """
    Extract failure type and message for a specific test from the
    failure details.
    """
    # Find the test name in the failure section
    test_method = (
        test_name.split('::')[-1] if '::' in test_name else test_name)

    in_test_failure = False
    failure_type = "TestFailure"
    failure_message = "Test failed"

    for i, line in enumerate(lines):
        # Look for the failure separator line for this test
        if (test_method in line and line.startswith('_') and
                line.endswith('_')):
            in_test_failure = True
            continue

        # If we're in the test failure section, look for error patterns
        if in_test_failure:
            # Stop when we hit the next test failure or end of section
            if (line.startswith('_') and line.endswith('_') and
                    test_method not in line):
                break

            # Look for common assertion/error patterns
            if 'AssertionError:' in line:
                failure_type = "AssertionError"
                failure_message = (
                    line.split('AssertionError:')[1].strip()
                    if ':' in line else line.strip())
                break
            elif ('assert ' in line and
                  (' == ' in line or ' != ' in line or ' in ' in line)):
                failure_type = "AssertionError"
                failure_message = line.strip()
                break
            elif any(error in line for error in [
                    'Error:', 'Exception:', 'ImportError:',
                    'AttributeError:', 'KeyError:', 'ValueError:',
                    'TypeError:']):
                # Extract error type and message
                for error_pattern in ['Error:', 'Exception:']:
                    if error_pattern in line:
                        error_parts = line.split(error_pattern, 1)
                        if len(error_parts) == 2:
                            failure_type = (
                                error_parts[0].split()[-1] + "Error"
                                if error_parts[0] else "Error")
                            failure_message = error_parts[1].strip()
                            break
                break
            elif ('>' in line and
                  ('assert' in line.lower() or 'expect' in line.lower())):
                failure_type = "AssertionError"
                failure_message = line.strip()
                break

    return failure_type, failure_message


def create_failure_group_key(failure_type, message):
    """Create a grouping key for similar failures."""
    # Normalize the message for grouping similar failures
    normalized = re.sub(r'\d+', '<NUM>', message)  # Replace numbers
    normalized = re.sub(
        r'[\'"][^\'\"]*[\'"]', '<STRING>', normalized)  # Replace strings
    normalized = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '<EMAIL>', normalized)  # Replace emails
    normalized = re.sub(
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '<IP>', normalized)  # Replace IPs
    normalized = re.sub(r'0x[0-9a-fA-F]+', '<HEX>', normalized)  # Replace hex values
    normalized = re.sub(r'/[^/\s]+/', '<PATH>/', normalized)  # Replace paths

    return f"{failure_type}:{normalized[:60]}"


def normalize_failure_message(message):
    """Normalize failure message for display."""
    if len(message) > 150:
        return message[:150] + "..."
    return message


def create_summary_header(failed_tests, failure_groups, errors, warnings, total_tests_info):
    """Create a summary header for the processed log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    header = f"""
{'='*80}
TEST LOG ANALYSIS - PROCESSED LOG
Generated: {timestamp}
{'='*80}

ISSUES OVERVIEW:
{'-'*50}
"""

    # Failures section - show both grouped and individual counts
    if failed_tests:
        if failure_groups and len(failure_groups) < len(failed_tests):
            # Show grouping when there are similar failures
            total_failures = sum(group['count'] for group in failure_groups)
            header += f"[FAILED] {len(failure_groups)} failure group(s), {total_failures} total test(s) failed:\n\n"
            for i, group in enumerate(failure_groups, 1):
                count_text = f" ({group['count']} test{'s' if group['count'] > 1 else ''})" if group['count'] > 1 else ""
                failure_summary = group['message'][:60] + "..." if len(group['message']) > 60 else group['message']
                header += f"[FAILURE GROUP NO-{i}] {group['type']}{count_text}: {failure_summary}\n"
        else:
            # Show individual failures when no meaningful grouping
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

    # Errors section
    if errors:
        total_errors = sum(group['count'] for group in errors)
        header += f"[ERRORS] {len(errors)} error group(s), {total_errors} total error(s) found:\n\n"
        for i, error_group in enumerate(errors, 1):
            count_text = f" ({error_group['count']} occurrences)" if error_group['count'] > 1 else ""
            error_summary = error_group['message'][:60] + "..." if len(error_group['message']) > 60 else error_group['message']
            header += f"[ERROR GROUP NO-{i}] {error_group['type']}{count_text}: {error_summary}\n"
    else:
        header += "[SUCCESS] No errors found!\n"

    header += f"\n{'-'*50}\n"

    # Warnings section
    if warnings:
        total_warnings = sum(group['count'] for group in warnings)
        header += f"[WARNINGS] {len(warnings)} warning group(s), {total_warnings} total warning(s) found:\n\n"
        for i, warning_group in enumerate(warnings, 1):
            count_text = f" ({warning_group['count']} occurrences)" if warning_group['count'] > 1 else ""
            warning_summary = warning_group['message'][:60] + "..." if len(warning_group['message']) > 60 else warning_group['message']
            header += f"[WARNING GROUP NO-{i}] {warning_group['type']}{count_text}: {warning_summary}\n"
    else:
        header += "[SUCCESS] No warnings found!\n"

    header += f"\n{'-'*50}\n"

    # Add test summary if available
    if total_tests_info:
        header += f"EXECUTION SUMMARY:\n{total_tests_info}\n{'-'*50}\n"

    return header


def extract_errors_and_warnings(log_content):
    """Extract and group errors and warnings from the log content with smart grouping."""
    lines = log_content.split('\n')

    # Extract pytest warning summary counts
    warning_groups = extract_pytest_warning_groups(log_content)

    # Extract individual errors with grouping
    error_groups = extract_and_group_errors(lines)

    return error_groups, warning_groups


def extract_pytest_warning_groups(log_content):
    """Extract warning groups from pytest warnings summary with counts."""
    lines = log_content.split('\n')
    warning_groups = {}

    # Find warnings summary section
    in_warnings_section = False
    warning_counts = {}

    for i, line in enumerate(lines):
        # Start of warnings summary
        if "warnings summary" in line:
            in_warnings_section = True
            continue

        # End of warnings summary (next section starts)
        if in_warnings_section and line.startswith("===="):
            break

        if in_warnings_section:
            # Parse aggregated warning counts per file
            if " warnings" in line and ": " in line:
                # e.g., "tests/unit/security/test_gdpr_compliance.py: 28 warnings"
                match = re.search(r'(.+?):\s+(\d+)\s+warnings?', line)
                if match:
                    file_path = match.group(1).strip()
                    count = int(match.group(2))
                    warning_counts[file_path] = warning_counts.get(file_path, 0) + count

            # Parse warning details and group by type
            elif "Warning:" in line or "warning" in line.lower():
                warning_type = extract_warning_type(line)
                if warning_type:
                    if warning_type not in warning_groups:
                        warning_groups[warning_type] = {
                            'type': warning_type,
                            'message': extract_warning_message(line),
                            'locations': [],
                            'count': 0
                        }

                    # Add location if we can extract it
                    location = extract_location_from_line(line, lines, i)
                    if location:
                        warning_groups[warning_type]['locations'].append(location)

    # Calculate total counts for each warning type
    for warning_type, group in warning_groups.items():
        # Estimate count based on similar patterns in the log
        group['count'] = estimate_warning_count(warning_type, log_content, warning_counts)

    return list(warning_groups.values())


def extract_and_group_errors(lines):
    """Extract and group errors by type."""
    error_groups = {}

    # Common error patterns with grouping keys - more precise to avoid false positives
    error_patterns = [
        (r'AssertionError:\s*(.+)', 'AssertionError'),
        (r'PermissionError:\s*(.+)', 'PermissionError'),
        (r'ImportError:\s*(.+)', 'ImportError'),
        (r'AttributeError:\s*(.+)', 'AttributeError'),
        (r'KeyError:\s*(.+)', 'KeyError'),
        (r'ValueError:\s*(.+)', 'ValueError'),
        (r'TypeError:\s*(.+)', 'TypeError'),
        (r'ConnectionError:\s*(.+)', 'ConnectionError'),
        (r'FileNotFoundError:\s*(.+)', 'FileNotFoundError'),
        (r'Exception:\s*(.+)', 'Exception'),
        # More specific ERROR patterns to avoid false positives
        (r'ERROR\s+at\s+(.+)', 'ERROR'),
        (r'ERROR:\s+(.+)', 'ERROR'),
        (r'FAILED\s+[^P](.+)', 'FAILED'),  # Exclude "FAILED PASSED" which is not an error
        # Generic error pattern - be more restrictive
        (r'(\w+Error):\s*(.+)', 'GenericError')
    ]

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Skip pytest progress indicators and other false positives
        if any(skip_pattern in line_stripped for skip_pattern in [
            'PASSED [', 'FAILED [', 'SKIPPED [',  # pytest progress indicators
            '% passed', '% failed', '% skipped',   # percentage indicators
            'warnings summary',                     # section headers
            '====', '----'                         # separators
        ]):
            continue

        for pattern, error_type in error_patterns:
            match = re.search(pattern, line_stripped, re.IGNORECASE)
            if match:
                error_message = match.group(1).strip()

                # Create group key based on error type and similar message
                group_key = create_error_group_key(error_type, error_message)

                if group_key not in error_groups:
                    error_groups[group_key] = {
                        'type': error_type,
                        'message': normalize_error_message(error_message),
                        'locations': [],
                        'count': 0
                    }

                # Add location
                location = f"Line {i + 1}"
                file_location = extract_file_from_error_context(lines, i)
                if file_location:
                    location = f"{file_location}:{i + 1}"

                error_groups[group_key]['locations'].append(location)
                error_groups[group_key]['count'] += 1
                break

    return list(error_groups.values())


def extract_warning_type(line):
    """Extract warning type from a warning line."""
    warning_types = [
        'DeprecationWarning', 'UserWarning', 'FutureWarning', 'PendingDeprecationWarning',
        'RuntimeWarning', 'SyntaxWarning', 'ImportWarning', 'ResourceWarning',
        'PytestDeprecationWarning', 'PytestUnknownMarkWarning', 'PytestCollectionWarning',
        'MovedIn20Warning', 'PydanticDeprecatedSince20', 'LegacyAPIWarning'
    ]

    for warning_type in warning_types:
        if warning_type in line:
            return warning_type

    if "Warning" in line:
        return "Warning"

    return None


def extract_warning_message(line):
    """Extract the core warning message."""
    # Remove file paths and line numbers, keep the essential message
    if ":" in line:
        parts = line.split(":")
        for part in reversed(parts):
            if len(part.strip()) > 20 and not part.strip().isdigit():
                return part.strip()[:100] + "..."

    return line.strip()[:100] + "..."


def is_external_warning(line):
    """Check if a warning comes from external dependencies."""
    external_indicators = [
        'site-packages',
        'sqlalchemy',
        'pytest_asyncio',
        'starlette',
        'httpx',
        'pydantic',
        'fastapi'
    ]

    return any(indicator in line.lower() for indicator in external_indicators)


def classify_warning_source(line):
    """Classify warning as internal, external, or unknown."""
    if is_external_warning(line):
        return "external"
    elif any(indicator in line.lower() for indicator in ['src/', 'tests/', 'tools/']):
        return "internal"
    else:
        return "unknown"


def extract_location_from_line(line, lines, index):
    """Extract file location from warning line or context."""
    # Look for file paths in the line or nearby lines
    file_patterns = [
        r'([A-Za-z]:[\\\/].+\.py):\d+',
        r'(tests[\\\/].+\.py):\d+',
        r'(src[\\\/].+\.py):\d+',
        r'([\\\/].+\.py):\d+'
    ]

    # Check current line and a few lines before
    for check_line in lines[max(0, index-2):index+1]:
        for pattern in file_patterns:
            match = re.search(pattern, check_line)
            if match:
                return match.group(1)

    return f"Line {index + 1}"


def estimate_warning_count(warning_type, log_content, warning_counts):
    """Estimate the count of warnings based on file counts and content analysis."""
    # Sum up counts from files that likely contain this warning type
    total_count = 0

    # Count occurrences of the warning type in the content
    type_occurrences = log_content.count(warning_type)

    if type_occurrences > 0:
        # Use actual count if we can determine it
        total_count = type_occurrences
    else:
        # Estimate based on file warning counts
        total_count = sum(warning_counts.values()) // len(warning_counts) if warning_counts else 1

    return max(1, total_count)


def create_error_group_key(error_type, message):
    """Create a grouping key for similar errors."""
    # Normalize the message for grouping
    normalized = re.sub(r'\d+', 'N', message)  # Replace numbers
    normalized = re.sub(r'[\'"][^\'\"]*[\'"]', 'STRING', normalized)  # Replace strings
    normalized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'EMAIL', normalized)  # Replace emails
    normalized = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', 'IP', normalized)  # Replace IPs

    return f"{error_type}:{normalized[:50]}"


def normalize_error_message(message):
    """Normalize error message for display."""
    if len(message) > 100:
        return message[:100] + "..."
    return message


def extract_file_from_error_context(lines, index):
    """Extract file path from error context."""
    # Look for file paths in nearby lines
    for i in range(max(0, index-5), min(len(lines), index+3)):
        line = lines[i]
        if ".py:" in line and ("tests/" in line or "src/" in line):
            match = re.search(r'([^\s]+\.py)', line)
            if match:
                return match.group(1)
    return None


def format_errors_section(error_groups):
    """Format the errors section with grouped errors and numbered tags."""
    if not error_groups:
        return ""

    total_errors = sum(group['count'] for group in error_groups)
    section = f"\n{'='*80}\n"
    section += f"ERROR DETAILS ({len(error_groups)} error group(s), {total_errors} total error(s) found):\n"
    section += f"{'='*80}\n\n"

    for i, group in enumerate(error_groups, 1):
        count_text = f" ({group['count']} occurrence{'s' if group['count'] > 1 else ''})" if group['count'] > 1 else ""
        section += f"[ERROR GROUP NO-{i}] {group['type']}{count_text}\n"
        section += f"{'='*60}\n"
        section += f"Message: {group['message']}\n"

        if group['locations']:
            section += f"Locations:\n"
            for location in group['locations'][:5]:  # Show up to 5 locations
                section += f"  - {location}\n"
            if len(group['locations']) > 5:
                section += f"  ... and {len(group['locations']) - 5} more locations\n"

        section += f"{'='*60}\n\n"

    return section


def format_warnings_section(warning_groups):
    """Format the warnings section with grouped warnings, separating internal and external warnings."""
    if not warning_groups:
        return ""

    # Separate internal and external warnings
    internal_groups = []
    external_groups = []

    for group in warning_groups:
        # Classify based on locations
        is_external = any(is_external_warning(loc) for loc in group.get('locations', []))
        if is_external:
            external_groups.append(group)
        else:
            internal_groups.append(group)

    total_warnings = sum(group['count'] for group in warning_groups)
    internal_count = sum(group['count'] for group in internal_groups)
    external_count = sum(group['count'] for group in external_groups)

    section = f"\n{'='*80}\n"
    section += f"WARNING DETAILS ({len(warning_groups)} warning group(s), {total_warnings} total warning(s) found):\n"
    section += f"Internal Code: {len(internal_groups)} group(s), {internal_count} warning(s)\n"
    section += f"External Dependencies: {len(external_groups)} group(s), {external_count} warning(s)\n"
    section += f"{'='*80}\n\n"

    # Show internal warnings first (higher priority)
    if internal_groups:
        section += f"🔍 INTERNAL CODE WARNINGS (Action Required)\n"
        section += f"{'='*60}\n\n"

        for i, group in enumerate(internal_groups, 1):
            count_text = f" ({group['count']} occurrence{'s' if group['count'] > 1 else ''})" if group['count'] > 1 else ""
            section += f"[INTERNAL WARNING NO-{i}] {group['type']}{count_text}\n"
            section += f"{'='*50}\n"
            section += f"Message: {group['message']}\n"

            if group['locations']:
                section += f"Locations:\n"
                for location in group['locations'][:5]:
                    section += f"  - {location}\n"
                if len(group['locations']) > 5:
                    section += f"  ... and {len(group['locations']) - 5} more locations\n"

            section += f"{'='*50}\n\n"

    # Show external warnings separately (lower priority)
    if external_groups:
        section += f"📦 EXTERNAL DEPENDENCY WARNINGS (Monitor Only)\n"
        section += f"{'='*60}\n"
        section += f"Note: These warnings come from external libraries and require no action from our team.\n"
        section += f"Monitor dependency updates for potential fixes.\n\n"

        for i, group in enumerate(external_groups, 1):
            count_text = f" ({group['count']} occurrence{'s' if group['count'] > 1 else ''})" if group['count'] > 1 else ""
            section += f"[EXTERNAL WARNING NO-{i}] {group['type']}{count_text}\n"
            section += f"{'='*50}\n"
            section += f"Message: {group['message']}\n"

            if group['locations']:
                section += f"Source Library:\n"
                for location in group['locations'][:3]:  # Show fewer external locations
                    section += f"  - {location}\n"
                if len(group['locations']) > 3:
                    section += f"  ... and {len(group['locations']) - 3} more locations\n"

            section += f"{'='*50}\n\n"

    return section


def format_failure_groups_section(failure_groups):
    """Format the failure groups section with grouped failures and detailed information."""
    if not failure_groups:
        return ""

    total_failures = sum(group['count'] for group in failure_groups)
    section = f"\n{'='*80}\n"
    section += f"FAILURE GROUP DETAILS ({len(failure_groups)} failure group(s), {total_failures} total test(s) failed):\n"
    section += f"{'='*80}\n\n"

    for i, group in enumerate(failure_groups, 1):
        count_text = f" ({group['count']} test{'s' if group['count'] > 1 else ''})" if group['count'] > 1 else ""
        section += f"[FAILURE GROUP NO-{i}] {group['type']}{count_text}\n"
        section += f"{'='*60}\n"
        section += f"Failure Pattern: {group['message']}\n"

        if group['affected_tests']:
            section += f"Affected Tests:\n"
            for test in group['affected_tests'][:10]:  # Show up to 10 tests
                section += f"  - {test}\n"
            if len(group['affected_tests']) > 10:
                section += f"  ... and {len(group['affected_tests']) - 10} more tests\n"

        section += f"{'='*60}\n\n"

    return section


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
    """Process the test log file to prioritize failures, errors, and warnings."""

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

    # Extract failures, errors, warnings and stack traces
    failed_tests, failure_groups, failure_details = extract_failures_and_traces(original_content)
    errors, warnings = extract_errors_and_warnings(original_content)
    test_summary = extract_test_summary(original_content)

    # Create the processed content
    header = create_summary_header(failed_tests, failure_groups, errors, warnings, test_summary)
    processed_content = header

    # Add failure group details (highest priority) if there are meaningful groups
    if failure_groups and len(failure_groups) < len(failed_tests):
        failure_groups_section = format_failure_groups_section(failure_groups)
        if failure_groups_section:
            processed_content += failure_groups_section

    # Add detailed failure information
    if failure_details:
        processed_content += f"\n{'='*80}\n"
        processed_content += "DETAILED FAILURE INFORMATION:\n"
        processed_content += f"{'='*80}\n\n"
        processed_content += failure_details

    # Add error details (second priority)
    error_section = format_errors_section(errors)
    if error_section:
        processed_content += error_section

    # Add warning details (third priority)
    warning_section = format_warnings_section(warnings)
    if warning_section:
        processed_content += warning_section

    # Add separator before original log
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

        # Report findings
        if failed_tests:
            if failure_groups and len(failure_groups) < len(failed_tests):
                total_failures = sum(group['count'] for group in failure_groups)
                print(f"[FAILURES] Found {len(failure_groups)} failure group(s) ({total_failures} total failed test(s))")
            else:
                print(f"[FAILURES] Found {len(failed_tests)} failed test(s)")
        else:
            print("[SUCCESS] No test failures found!")

        if errors:
            total_errors = sum(group['count'] for group in errors)
            print(f"[ERRORS] Found {len(errors)} error group(s) ({total_errors} total error(s))")
        else:
            print("[SUCCESS] No errors found!")

        if warnings:
            total_warnings = sum(group['count'] for group in warnings)
            print(f"[WARNINGS] Found {len(warnings)} warning group(s) ({total_warnings} total warning(s))")
        else:
            print("[SUCCESS] No warnings found!")

        if failed_tests or errors or warnings:
            print(f"[INFO] Issues are now grouped and prioritized at the top of: {output_file}")

        return True

    except Exception as e:
        print(f"Error writing {output_file}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Process test logs to prioritize failures, errors, warnings, and stack traces",
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