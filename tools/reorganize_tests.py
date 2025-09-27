#!/usr/bin/env python3
"""
Test Directory Reorganization Tool

Reorganizes test files into QA-optimized folder structure:
- unit/: by component
- integration/: by combination
- functional/: by epic (QA main workspace)
- e2e/: by use case
- bdd/: keep existing structure
"""

import json
import shutil
from pathlib import Path
from typing import Dict


class TestReorganizer:
    def __init__(
        self,
        associations_file="test_associations.json",
        test_root="tests",
        dry_run=True,
    ):
        self.associations_file = Path(associations_file)
        self.test_root = Path(test_root)
        self.dry_run = dry_run
        self.associations = {}
        self.moves = []

    def load_associations(self):
        """Load test associations from JSON file."""
        print(f"Loading associations from {self.associations_file}...")
        with open(self.associations_file, "r") as f:
            self.associations = json.load(f)
        print(f"Loaded {len(self.associations)} test file associations\n")

    def reorganize_all_tests(self):
        """Reorganize all test files based on type and associations."""
        print(f"{'DRY RUN: ' if self.dry_run else ''}Planning test reorganization...\n")

        for relative_path, assoc in self.associations.items():
            old_path = Path(assoc["file_path"])

            if not old_path.exists():
                print(f"SKIP: File not found - {old_path}")
                continue

            new_path = self._determine_new_path(old_path, assoc)

            if new_path and new_path != old_path:
                self.moves.append((old_path, new_path))

        self._print_plan()

        if not self.dry_run:
            self._execute_moves()

    def _determine_new_path(self, old_path: Path, assoc: Dict) -> Path:
        """Determine new path based on test type and associations."""
        test_type = assoc["test_type"]

        if test_type == "bdd":
            return None

        if test_type == "unit":
            return self._unit_path(old_path, assoc)
        elif test_type == "integration":
            return self._integration_path(old_path, assoc)
        elif test_type == "functional":
            return self._functional_path(old_path, assoc)
        elif test_type == "e2e":
            return self._e2e_path(old_path, assoc)
        elif test_type == "unknown":
            return self._unknown_path(old_path, assoc)

        return None

    def _unit_path(self, old_path: Path, assoc: Dict) -> Path:
        """Unit tests: organized by component."""
        component = assoc["components"][0] if assoc["components"] else "shared"

        subdir = ""
        if "models" in str(old_path):
            subdir = "models/"
        elif "tools" in str(old_path):
            subdir = "tools/"
        elif "shared" in str(old_path):
            if "testing" in str(old_path):
                subdir = "shared/testing/"
            else:
                subdir = "shared/"

        return self.test_root / "unit" / component / subdir / old_path.name

    def _integration_path(self, old_path: Path, assoc: Dict) -> Path:
        """Integration tests: organized by combination."""
        if "rtm" in str(old_path).lower():
            if "plugin" in old_path.name:
                return self.test_root / "integration" / "rtm_plugin" / old_path.name
            elif "end_to_end" in old_path.name:
                return self.test_root / "integration" / "rtm_workflow" / old_path.name
            elif "db" in old_path.name:
                return self.test_root / "integration" / "rtm_database" / old_path.name
            elif "api" in old_path.name:
                return self.test_root / "integration" / "rtm_api" / old_path.name
            elif "filter" in old_path.name:
                return self.test_root / "integration" / "rtm_filter" / old_path.name
            elif "browser" in old_path.name:
                return self.test_root / "integration" / "rtm_ui" / old_path.name
            else:
                return self.test_root / "integration" / "rtm_general" / old_path.name

        elif "github" in old_path.name.lower():
            return self.test_root / "integration" / "github_rtm" / old_path.name
        elif "gdpr" in old_path.name.lower():
            return self.test_root / "integration" / "gdpr_compliance" / old_path.name
        elif "database" in old_path.name.lower():
            return self.test_root / "integration" / "database_workflow" / old_path.name
        elif "component" in old_path.name.lower():
            return self.test_root / "integration" / "component_system" / old_path.name
        else:
            return self.test_root / "integration" / "general" / old_path.name

    def _functional_path(self, old_path: Path, assoc: Dict) -> Path:
        """Functional tests: organized by epic."""
        if not assoc["epics"]:
            return self.test_root / "functional" / "general" / old_path.name

        primary_epic = sorted(assoc["epics"])[0]

        epic_folders = {
            "EP-00001": "blog_management",
            "EP-00002": "comment_system",
            "EP-00003": "gdpr_compliance",
            "EP-00004": "github_integration",
            "EP-00005": "rtm_automation",
            "EP-00006": "testing_infrastructure",
            "EP-00007": "quality_assurance",
        }

        folder = epic_folders.get(primary_epic, f"epic_{primary_epic.lower()}")
        return self.test_root / "functional" / folder / old_path.name

    def _e2e_path(self, old_path: Path, assoc: Dict) -> Path:
        """E2E tests: organized by use case."""
        if "blog" in old_path.name.lower():
            return self.test_root / "e2e" / "complete_blog_workflow" / old_path.name
        elif "gdpr" in old_path.name.lower():
            return self.test_root / "e2e" / "gdpr_user_journey" / old_path.name
        else:
            return self.test_root / "e2e" / "general" / old_path.name

    def _unknown_path(self, old_path: Path, assoc: Dict) -> Path:
        """Unknown test type: place in appropriate category based on patterns."""
        if "security" in str(old_path).lower() or "gdpr" in str(old_path).lower():
            component = assoc["components"][0] if assoc["components"] else "security"
            return self.test_root / "unit" / component / old_path.name

        return self.test_root / "unit" / "general" / old_path.name

    def _print_plan(self):
        """Print reorganization plan."""
        print("=" * 80)
        print(f"{'DRY RUN - ' if self.dry_run else ''}TEST REORGANIZATION PLAN")
        print("=" * 80 + "\n")

        if not self.moves:
            print("No moves needed - all tests are already organized!\n")
            return

        by_type = {}
        for old_path, new_path in self.moves:
            test_type = new_path.parts[1] if len(new_path.parts) > 1 else "unknown"
            if test_type not in by_type:
                by_type[test_type] = []
            by_type[test_type].append((old_path, new_path))

        for test_type in sorted(by_type.keys()):
            print(f"\n{test_type.upper()} TESTS ({len(by_type[test_type])} files):")
            print("-" * 80)
            for old_path, new_path in by_type[test_type]:
                print(f"  {old_path}")
                print(f"    -> {new_path}")

        print(f"\n\nTOTAL MOVES: {len(self.moves)}")

        if self.dry_run:
            print("\n" + "=" * 80)
            print("This was a DRY RUN. No files were moved.")
            print("Run with --execute to actually move files.")
            print("=" * 80)

    def _execute_moves(self):
        """Execute the planned moves."""
        print("\n" + "=" * 80)
        print("EXECUTING REORGANIZATION...")
        print("=" * 80 + "\n")

        moved = 0
        errors = 0

        for old_path, new_path in self.moves:
            try:
                new_path.parent.mkdir(parents=True, exist_ok=True)

                shutil.move(str(old_path), str(new_path))
                print(f"[OK] Moved: {old_path.name}")
                moved += 1

            except Exception as e:
                print(f"[ERROR] Error moving {old_path.name}: {e}")
                errors += 1

        print("\n\nSUMMARY:")
        print(f"  Successfully moved: {moved}")
        print(f"  Errors: {errors}")

        if moved > 0:
            print("\n\nNEXT STEPS:")
            print("1. Update import paths in moved test files")
            print("2. Run: pytest tests/ -v to verify all tests still work")
            print("3. Update any documentation referencing old test paths")
            print("4. Proceed to Phase 5: Update RTM database associations")


if __name__ == "__main__":
    import sys

    dry_run = "--execute" not in sys.argv

    reorganizer = TestReorganizer(dry_run=dry_run)
    reorganizer.load_associations()
    reorganizer.reorganize_all_tests()
