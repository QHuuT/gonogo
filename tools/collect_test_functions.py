#!/usr/bin/env python3
"""
Collect individual test functions from pytest and create detailed test records.
"""

import ast
import json
import re
from pathlib import Path


class TestFunctionCollector(ast.NodeVisitor):
    """AST visitor to extract test functions and their markers."""

    def __init__(self):
        self.functions = []
        self.current_class = None
        self.class_markers = {}

    def visit_ClassDef(self, node):
        """Visit class definitions to collect class-level markers."""
        old_class = self.current_class
        self.current_class = node.name

        # Collect class-level markers
        class_epics = set()
        class_user_stories = set()
        class_components = set()

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if hasattr(decorator.func, "attr"):
                    marker_name = decorator.func.attr
                    if marker_name == "epic" and decorator.args:
                        if isinstance(decorator.args[0], ast.Constant):
                            class_epics.add(decorator.args[0].value)
                    elif marker_name == "user_story" and decorator.args:
                        if isinstance(decorator.args[0], ast.Constant):
                            class_user_stories.add(decorator.args[0].value)
                    elif marker_name == "component" and decorator.args:
                        if isinstance(decorator.args[0], ast.Constant):
                            class_components.add(decorator.args[0].value)

        self.class_markers[node.name] = {
            "epics": class_epics,
            "user_stories": class_user_stories,
            "components": class_components,
        }

        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node):
        """Visit function definitions to find test functions."""
        # Only collect test functions (start with test_)
        if not node.name.startswith("test_"):
            return

        # Collect function-level markers
        func_epics = set()
        func_user_stories = set()
        func_components = set()
        func_defects = set()

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if hasattr(decorator.func, "attr"):
                    marker_name = decorator.func.attr
                    if marker_name == "epic" and decorator.args:
                        if isinstance(decorator.args[0], ast.Constant):
                            func_epics.add(decorator.args[0].value)
                    elif marker_name == "user_story" and decorator.args:
                        if isinstance(decorator.args[0], ast.Constant):
                            func_user_stories.add(decorator.args[0].value)
                    elif marker_name == "component" and decorator.args:
                        if isinstance(decorator.args[0], ast.Constant):
                            func_components.add(decorator.args[0].value)

        # Merge with class-level markers if in a class
        if self.current_class and self.current_class in self.class_markers:
            class_m = self.class_markers[self.current_class]
            func_epics.update(class_m["epics"])
            func_user_stories.update(class_m["user_stories"])
            func_components.update(class_m["components"])

        # Extract docstring
        docstring = ast.get_docstring(node) or ""
        if docstring:
            for match in re.findall(r"(DEF-\d{3,5})", docstring, re.IGNORECASE):
                func_defects.add(f"DEF-{match.upper().split('-')[-1].zfill(5)}")

        self.functions.append(
            {
                "name": node.name,
                "class_name": self.current_class,
                "epics": list(func_epics),
                "user_stories": list(func_user_stories),
                "components": list(func_components),
                "defects": list(func_defects),
                "docstring": docstring.split("\n")[0] if docstring else "",
            }
        )


def collect_test_functions(test_root="tests"):
    """Collect all test functions from test files."""
    test_root = Path(test_root)
    all_functions = {}

    # Find all Python test files
    test_files = list(test_root.rglob("test_*.py"))

    for test_file in test_files:
        try:
            # Skip BDD step definitions
            if "bdd" in str(test_file):
                continue

            # Parse the file
            with open(test_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            # Collect functions
            collector = TestFunctionCollector()
            collector.visit(tree)

            if collector.functions:
                relative_path = test_file.relative_to(test_root)
                file_key = str(relative_path)
                all_functions[file_key] = {
                    "file_path": str(test_file),
                    "functions": collector.functions,
                }
        except Exception as e:
            print(f"Error parsing {test_file}: {e}")

    return all_functions


def main():
    print("Collecting test functions from pytest files...")
    functions = collect_test_functions()

    # Save to JSON
    output_file = "test_functions.json"
    with open(output_file, "w") as f:
        json.dump(functions, f, indent=2)

    # Print summary
    total_files = len(functions)
    total_functions = sum(len(f["functions"]) for f in functions.values())

    print("\nCollected:")
    print(f"  Test files: {total_files}")
    print(f"  Test functions: {total_functions}")
    print(f"  Saved to: {output_file}")

    # Show sample
    if functions:
        sample_file = list(functions.keys())[0]
        sample = functions[sample_file]
        print(f"\nSample from {sample_file}:")
        for func in sample["functions"][:3]:
            print(
                f"  - {func['name']}: epics={func['epics']}, us={func['user_stories']}"
            )


if __name__ == "__main__":
    main()
