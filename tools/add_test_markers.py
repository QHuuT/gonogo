#!/usr/bin/env python3
"""
Test Marker Addition Tool

Automatically adds pytest markers to test files based on discovered associations.
Reads test_associations.json and adds appropriate @pytest.mark decorators.
"""

import json
import re
from pathlib import Path
from typing import Dict, List


class TestMarkerAdder:
    def __init__(self, associations_file="test_associations.json", test_root="tests"):
        self.associations_file = Path(associations_file)
        self.test_root = Path(test_root)
        self.associations = {}
        self.modified_files = []
        self.skipped_files = []

    def load_associations(self):
        """Load test associations from JSON file."""
        print(f"Loading associations from {self.associations_file}...")
        with open(self.associations_file, "r") as f:
            self.associations = json.load(f)
        print(f"Loaded {len(self.associations)} test file associations\n")

    def add_markers_to_all_tests(self):
        """Add markers to all test files based on associations."""
        print("Adding pytest markers to test files...\n")

        for relative_path, assoc in self.associations.items():
            file_path = Path(assoc["file_path"])

            if not file_path.exists():
                print(f"SKIP: File not found - {file_path}")
                self.skipped_files.append(str(file_path))
                continue

            if file_path.suffix == ".feature":
                print(f"SKIP: BDD featurefile (markers not applicable) - {file_path}")
                self.skipped_files.append(str(file_path))
                continue

            self._add_markers_to_file(file_path, assoc)

        self._print_summary()

    def _add_markers_to_file(self, file_path: Path, associations: Dict):
        """Add markers to a single Python test file."""
        try:
            content = file_path.read_text(encoding="utf-8")

            if (
                not associations["user_stories"]
                and not associations["epics"]
                and not associations["components"]
            ):
                print(f"SKIP: No associations to add - {file_path}")
                self.skipped_files.append(str(file_path))
                return

            marker_lines = self._build_marker_lines(associations)

            if not marker_lines:
                print(f"SKIP: No valid markers to add - {file_path}")
                self.skipped_files.append(str(file_path))
                return

            new_content = self._insert_markers(content, marker_lines, file_path)

            if new_content != content:
                file_path.write_text(new_content, encoding="utf-8")
                self.modified_files.append(str(file_path))
                print(f"UPDATED: {file_path}")
                for marker in marker_lines:
                    print(f"  + {marker}")
            else:
                print(f"SKIP: Markers already present - {file_path}")
                self.skipped_files.append(str(file_path))

        except Exception as e:
            print(f"ERROR: {file_path} - {e}")
            self.skipped_files.append(str(file_path))

    def _build_marker_lines(self, associations: Dict) -> List[str]:
        """Build pytest marker decorator lines."""
        markers = []

        if associations["epics"]:
            epic_values = ", ".join(
                f'"{epic}"' for epic in sorted(associations["epics"])
            )
            markers.append(f"@pytest.mark.epic({epic_values})")

        if associations["user_stories"]:
            us_values = ", ".join(
                f'"{us}"' for us in sorted(associations["user_stories"])
            )
            markers.append(f"@pytest.mark.user_story({us_values})")

        if associations["components"]:
            comp_values = ", ".join(
                f'"{comp}"' for comp in sorted(associations["components"])
            )
            markers.append(f"@pytest.mark.component({comp_values})")

        return markers

    def _insert_markers(
        self, content: str, marker_lines: List[str], file_path: Path
    ) -> str:
        """Insert markers before test functions/classes."""
        lines = content.split("\n")
        new_lines = []
        i = 0
        markers_added = False

        if not self._has_pytest_import(content):
            import_added = False
            for idx, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    if not import_added:
                        new_lines.append("import pytest")
                        import_added = True
                    new_lines.append(line)
                elif import_added:
                    if line.strip() == "":
                        new_lines.append(line)
                    else:
                        break
                else:
                    new_lines.append(line)

            if not import_added:
                new_lines.insert(0, "import pytest")
                new_lines.insert(1, "")

            i = len(new_lines)
            lines = new_lines + lines[i:]
            new_lines = []

        while i < len(lines):
            line = lines[i]

            if self._is_test_definition(line) and not self._already_has_markers(
                lines, i
            ):
                indent = self._get_indent(line)
                for marker in marker_lines:
                    new_lines.append(f"{indent}{marker}")
                markers_added = True

            new_lines.append(line)
            i += 1

        if not markers_added:
            print("  WARNING: Could not find test function/class to add markers to")
            return content

        return "\n".join(new_lines)

    def _has_pytest_import(self, content: str) -> bool:
        """Check if pytest is already imported."""
        return bool(
            re.search(r"^import pytest", content, re.MULTILINE)
            or re.search(r"^from pytest import", content, re.MULTILINE)
        )

    def _is_test_definition(self, line: str) -> bool:
        """Check if line is a test function or class definition."""
        stripped = line.strip()
        return (
            stripped.startswith("def test_")
            or stripped.startswith("class Test")
            or stripped.startswith("async def test_")
        )

    def _already_has_markers(self, lines: List[str], current_idx: int) -> bool:
        """Check if markers are already present before this test."""
        for i in range(max(0, current_idx - 10), current_idx):
            if "@pytest.mark." in lines[i]:
                return True
        return False

    def _get_indent(self, line: str) -> str:
        """Get the indentation of a line."""
        return line[: len(line) - len(line.lstrip())]

    def _print_summary(self):
        """Print summary of marker addition."""
        print("\n" + "=" * 80)
        print("TEST MARKER ADDITION SUMMARY")
        print("=" * 80 + "\n")

        print(f"Total files processed: {len(self.associations)}")
        print(f"Files modified: {len(self.modified_files)}")
        print(f"Files skipped: {len(self.skipped_files)}")
        print()

        if self.modified_files:
            print("MODIFIED FILES:")
            for file in self.modified_files:
                print(f"  - {file}")
            print()

        print("\nNEXT STEPS:")
        print("1. Review modified test files to verify markers are correct")
        print("2. Run tests to ensure markers work: pytest -m 'user_story'")
        print("3. Handle orphaned tests manually (see TEST_REORGANIZATION_PLAN.md)")
        print("4. Proceed to Phase 4: Reorganize test directory structure")


if __name__ == "__main__":
    adder = TestMarkerAdder()
    adder.load_associations()
    adder.add_markers_to_all_tests()
