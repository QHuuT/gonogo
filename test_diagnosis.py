#!/usr/bin/env python3
"""
Test Diagnosis Tool - Analyze if tests actually run code or are just placeholders
"""

import ast
import re
from pathlib import Path
from collections import defaultdict

class TestDiagnostics:
    def __init__(self, test_root='tests'):
        self.test_root = Path(test_root)
        self.results = defaultdict(list)

    def analyze_all_tests(self):
        """Analyze all test files."""
        print("="*80)
        print("TEST DIAGNOSTICS - GoNoGo Test Suite Analysis")
        print("="*80)

        test_files = list(self.test_root.rglob('test_*.py'))

        print(f"\nAnalyzing {len(test_files)} test files...\n")

        for test_file in test_files:
            if 'bdd' in str(test_file):
                continue  # Skip BDD files for now
            self.analyze_test_file(test_file)

        self.print_summary()

    def analyze_test_file(self, file_path: Path):
        """Analyze a single test file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)

            relative_path = file_path.relative_to(self.test_root)

            # Find all test functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    self.analyze_test_function(relative_path, node, content)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def analyze_test_function(self, file_path, node, content):
        """Analyze individual test function."""
        func_name = node.name

        # Get function body
        func_lines = ast.get_source_segment(content, node)
        if not func_lines:
            return

        # Check various patterns
        is_placeholder = self.is_placeholder(func_lines)
        is_trivial = self.is_trivial(func_lines)
        has_assertions = self.has_assertions(func_lines)
        has_mocks = self.has_mocks(func_lines)
        uses_fixtures = self.uses_fixtures(node)
        reads_files = self.reads_files(func_lines)
        makes_http_calls = self.makes_http_calls(func_lines)

        # Categorize the test
        category = self.categorize_test(
            is_placeholder, is_trivial, has_assertions,
            has_mocks, uses_fixtures, reads_files, makes_http_calls
        )

        test_info = {
            'file': str(file_path),
            'function': func_name,
            'lines': len(func_lines.split('\n')),
            'has_assertions': has_assertions,
            'has_mocks': has_mocks,
            'uses_fixtures': uses_fixtures,
            'reads_files': reads_files,
            'makes_http_calls': makes_http_calls,
            'category': category
        }

        self.results[category].append(test_info)

    def is_placeholder(self, code):
        """Check if test is just a placeholder."""
        # Common placeholder patterns
        patterns = [
            r'^\s*pass\s*$',
            r'^\s*\.\.\.\s*$',
            r'assert\s+True\s*$',
            r'assert\s+1\s*==\s*1',
            r'# TODO',
            r'# FIXME',
            r'# Not implemented',
            r'raise NotImplementedError'
        ]

        for pattern in patterns:
            if re.search(pattern, code, re.MULTILINE | re.IGNORECASE):
                return True
        return False

    def is_trivial(self, code):
        """Check if test is trivial (too simple)."""
        # Count actual code lines (excluding comments, docstrings, whitespace)
        lines = [line.strip() for line in code.split('\n')]
        code_lines = [l for l in lines if l and not l.startswith('#') and not l.startswith('"""') and not l.startswith("'''")]

        # Exclude def line and return/pass
        actual_code = [l for l in code_lines if not l.startswith('def ') and l not in ['pass', 'return', '...', 'return None']]

        return len(actual_code) <= 2

    def has_assertions(self, code):
        """Check if test has assertions."""
        return bool(re.search(r'\bassert\b', code))

    def has_mocks(self, code):
        """Check if test uses mocking."""
        mock_patterns = [
            r'@patch', r'Mock\(', r'MagicMock', r'mock\.',
            r'monkeypatch', r'mocker\.', r'pytest\.fixture'
        ]
        return any(re.search(pattern, code) for pattern in mock_patterns)

    def uses_fixtures(self, node):
        """Check if function uses pytest fixtures."""
        return len(node.args.args) > 1 or (len(node.args.args) == 1 and node.args.args[0].arg != 'self')

    def reads_files(self, code):
        """Check if test reads files."""
        patterns = [r'open\(', r'\.read\(', r'Path\(', r'\.exists\(', r'\.read_text\(']
        return any(re.search(pattern, code) for pattern in patterns)

    def makes_http_calls(self, code):
        """Check if test makes HTTP calls."""
        patterns = [
            r'requests\.', r'client\.get', r'client\.post',
            r'\.get\(.*http', r'TestClient', r'response\s*='
        ]
        return any(re.search(pattern, code) for pattern in patterns)

    def categorize_test(self, is_placeholder, is_trivial, has_assertions,
                       has_mocks, uses_fixtures, reads_files, makes_http_calls):
        """Categorize test based on analysis."""
        if is_placeholder:
            return 'placeholder'
        if is_trivial and not has_assertions:
            return 'trivial_no_assert'
        if is_trivial and has_assertions:
            return 'trivial_with_assert'
        if has_mocks or uses_fixtures:
            return 'proper_unit_test'
        if reads_files:
            return 'file_based_test'
        if makes_http_calls:
            return 'integration_test'
        if has_assertions:
            return 'basic_test'
        return 'unclear'

    def print_summary(self):
        """Print diagnostic summary."""
        print("\n" + "="*80)
        print("DIAGNOSTIC SUMMARY")
        print("="*80)

        total_tests = sum(len(tests) for tests in self.results.values())

        print(f"\nTotal tests analyzed: {total_tests}\n")

        # Category breakdown
        categories = [
            ('placeholder', 'PLACEHOLDER/TODO Tests', '⚠️'),
            ('trivial_no_assert', 'Trivial Tests (No Assertions)', '⚠️'),
            ('trivial_with_assert', 'Trivial Tests (With Assertions)', '⚡'),
            ('proper_unit_test', 'Proper Unit Tests', '✅'),
            ('integration_test', 'Integration Tests', '✅'),
            ('file_based_test', 'File-Based Tests', '✅'),
            ('basic_test', 'Basic Tests', '✅'),
            ('unclear', 'Unclear Tests', '❓')
        ]

        for cat_key, cat_name, emoji in categories:
            tests = self.results[cat_key]
            if tests:
                pct = len(tests) * 100 / total_tests
                print(f"{cat_name}: {len(tests)} ({pct:.1f}%)")

                # Show examples
                if cat_key in ['placeholder', 'trivial_no_assert']:
                    print(f"  Examples:")
                    for test in tests[:3]:
                        print(f"    - {test['file']} :: {test['function']}")

        # Recommendations
        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80)

        placeholders = self.results['placeholder']
        trivial_no_assert = self.results['trivial_no_assert']

        if placeholders:
            print(f"\n1. REMOVE OR IMPLEMENT {len(placeholders)} placeholder tests:")
            for test in placeholders[:5]:
                print(f"   - {test['file']} :: {test['function']}")

        if trivial_no_assert:
            print(f"\n2. FIX OR REMOVE {len(trivial_no_assert)} trivial tests without assertions:")
            for test in trivial_no_assert[:5]:
                print(f"   - {test['file']} :: {test['function']}")

        proper_tests = (
            len(self.results['proper_unit_test']) +
            len(self.results['integration_test']) +
            len(self.results['file_based_test']) +
            len(self.results['basic_test'])
        )

        print(f"\n3. KEEP {proper_tests} legitimate tests ({proper_tests*100/total_tests:.1f}%)")

        print("\n" + "="*80)


if __name__ == '__main__':
    diagnostics = TestDiagnostics()
    diagnostics.analyze_all_tests()