#!/usr/bin/env python3
"""
Collect Test Component Markers

Extracts component information from pytest markers in test files and updates
the Test model in the database.
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from be.database import get_db_session
from be.models.traceability import Test


class ComponentMarkerCollector(ast.NodeVisitor):
    """AST visitor to collect pytest markers from test files."""

    def __init__(self):
        self.markers = {}  # function_name -> {component, epic, user_story, etc}
        self.class_markers = {}  # current class markers

    def visit_ClassDef(self, node):
        """Visit class definitions to collect class-level markers."""
        self.class_markers = self._extract_markers_from_decorators(node.decorator_list)
        self.generic_visit(node)
        # Clear class markers after processing class
        self.class_markers = {}

    def visit_FunctionDef(self, node):
        """Visit function definitions to collect test markers."""
        if node.name.startswith('test_'):
            function_markers = self._extract_markers_from_decorators(node.decorator_list)
            # Combine class markers with function markers (function takes precedence)
            all_markers = {**self.class_markers, **function_markers}
            if all_markers:
                self.markers[node.name] = all_markers
        self.generic_visit(node)

    def _extract_markers_from_decorators(self, decorator_list) -> Dict[str, str]:
        """Extract pytest markers from decorator list."""
        markers = {}

        for decorator in decorator_list:
            # Handle pytest.mark.name(value) form
            if isinstance(decorator, ast.Call):
                if (hasattr(decorator.func, 'attr') and
                    hasattr(decorator.func.value, 'attr') and
                    decorator.func.value.attr == 'mark'):

                    marker_name = decorator.func.attr

                    # Extract marker value if present
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        marker_value = decorator.args[0].value
                        markers[marker_name] = marker_value
                    else:
                        # Marker without value (like @pytest.mark.detailed)
                        markers[marker_name] = True

            # Handle pytest.mark.name form (without parentheses)
            elif isinstance(decorator, ast.Attribute):
                if (hasattr(decorator.value, 'attr') and
                    decorator.value.attr == 'mark'):
                    marker_name = decorator.attr
                    markers[marker_name] = True

        return markers


def collect_markers_from_file(file_path: Path) -> Dict[str, Dict[str, str]]:
    """Collect pytest markers from a single test file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        collector = ComponentMarkerCollector()
        collector.visit(tree)

        return collector.markers
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return {}


def find_test_files(test_dir: Path) -> List[Path]:
    """Find all Python test files."""
    test_files = []
    for pattern in ['test_*.py', '*_test.py']:
        test_files.extend(test_dir.rglob(pattern))
    return test_files


def update_test_components():
    """Update test components in database from pytest markers."""
    print("Collecting component markers from test files...")

    # Find test files
    test_dir = Path(__file__).parent.parent / "tests"
    test_files = find_test_files(test_dir)

    print(f"Found {len(test_files)} test files")

    # Collect all markers
    all_markers = {}
    for test_file in test_files:
        rel_path = test_file.relative_to(Path(__file__).parent.parent)
        file_markers = collect_markers_from_file(test_file)

        if file_markers:
            print(f"  {rel_path}: {len(file_markers)} test functions with markers")
            all_markers[str(rel_path)] = file_markers

    print(f"\nCollected markers from {len(all_markers)} files")

    # Update database
    with get_db_session() as session:
        tests = session.query(Test).all()
        updated_count = 0

        for test in tests:
            # Normalize file path for comparison
            test_file_key = test.test_file_path.replace("\\", "/")

            if test_file_key in all_markers:
                file_markers = all_markers[test_file_key]
                function_name = test.test_function_name

                if function_name in file_markers:
                    markers = file_markers[function_name]

                    # Update component (force if exists)
                    if 'component' in markers:
                        old_component = test.component
                        test.component = markers['component']
                        if old_component != test.component:
                            print(f"  {test.test_file_path}::{test.test_function_name}")
                            print(f"    Component: {old_component or 'None'} -> {test.component}")
                            updated_count += 1

                    # Update test category from various marker types (always check)
                    if True:  # Force category update
                        category = None

                        # Check explicit category markers
                        if 'test_category' in markers:
                            category = markers['test_category']
                        elif 'category' in markers:
                            category = markers['category']
                        # Check boolean marker flags
                        elif markers.get('smoke'):
                            category = 'smoke'
                        elif markers.get('edge'):
                            category = 'edge'
                        elif markers.get('regression'):
                            category = 'regression'
                        elif markers.get('detailed'):
                            category = 'detailed'
                        elif markers.get('performance'):
                            category = 'performance'
                        elif markers.get('critical'):
                            category = 'smoke'  # critical tests are usually smoke tests
                        # Infer from file path if no explicit marker
                        elif 'security' in test.test_file_path.lower():
                            category = 'compliance-gdpr'
                        elif 'integration' in test.test_file_path.lower():
                            category = 'regression'
                        elif 'unit' in test.test_file_path.lower():
                            category = 'smoke'

                        if category and category != test.test_category:
                            old_category = test.test_category
                            test.test_category = category
                            print(f"    Category: {old_category or 'None'} -> {test.test_category}")
                            updated_count += 1

                    # Update test priority
                    if 'priority' in markers and test.test_priority == 'medium':
                        old_priority = test.test_priority
                        test.test_priority = markers['priority']
                        if old_priority != test.test_priority:
                            print(f"    Priority: {old_priority} -> {test.test_priority}")
                            updated_count += 1

        session.commit()
        print(f"\nUpdated {updated_count} tests with component information")


if __name__ == "__main__":
    update_test_components()