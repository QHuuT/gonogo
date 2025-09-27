#!/usr/bin/env python3
"""
Test Association Validation Tool

Validates test-requirement associations and identifies issues:
- Orphaned tests (no US/Epic associations)
- Invalid US/Epic references
- Missing pytest markers
- Database sync status
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from be.models.traceability.epic import Epic
from be.models.traceability.test import Test
from be.models.traceability.user_story import UserStory


class TestAssociationValidator:
    def __init__(self, test_root="tests", database_url="sqlite:///./gonogo.db"):
        self.test_root = Path(test_root)
        self.database_url = database_url
        self.session = None
        self.issues = {
            "orphaned_tests": [],
            "invalid_us_refs": [],
            "invalid_epic_refs": [],
            "missing_markers": [],
            "not_in_db": [],
            "marker_db_mismatch": [],
        }

    def connect_database(self):
        """Connect to RTM database."""
        engine = create_engine(self.database_url, echo=False)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def validate_all(self):
        """Run all validation checks."""
        print("Validating test associations...\n")

        self._check_orphaned_tests()
        self._check_invalid_references()
        self._check_database_sync()

        self._print_report()

    def _check_orphaned_tests(self):
        """Find tests with no US or Epic associations."""
        print("Checking for orphaned tests...")

        test_files = list(self.test_root.rglob("test_*.py"))
        test_files += list(self.test_root.rglob("*_test.py"))

        for test_file in test_files:
            if "bdd" in str(test_file):
                continue

            content = test_file.read_text(encoding="utf-8")

            has_us_marker = bool(re.search(r"@pytest\.mark\.user_story", content))
            has_epic_marker = bool(re.search(r"@pytest\.mark\.epic", content))

            if not has_us_marker and not has_epic_marker:
                self.issues["orphaned_tests"].append(str(test_file))

        print(f"  Found {len(self.issues['orphaned_tests'])} orphaned tests\n")

    def _check_invalid_references(self):
        """Check for invalid US/Epic references in markers."""
        print("Checking for invalid US/Epic references...")

        test_files = list(self.test_root.rglob("test_*.py"))
        test_files += list(self.test_root.rglob("*_test.py"))

        valid_us_numbers = {
            us.github_issue_number for us in self.session.query(UserStory).all()
        }
        valid_epic_numbers = {
            epic.github_issue_number for epic in self.session.query(Epic).all()
        }

        for test_file in test_files:
            if "bdd" in str(test_file):
                continue

            content = test_file.read_text(encoding="utf-8")

            us_markers = re.findall(
                r'@pytest\.mark\.user_story\(["\']([^"\']+)', content
            )
            for us_marker in us_markers:
                us_refs = us_marker.replace('"', "").replace("'", "").split(",")
                for us_ref in us_refs:
                    us_ref = us_ref.strip()
                    match = re.match(r"US-0*(\d+)", us_ref)
                    if match:
                        us_number = int(match.group(1))
                        if us_number not in valid_us_numbers:
                            self.issues["invalid_us_refs"].append(
                                {"file": str(test_file), "reference": us_ref}
                            )

            epic_markers = re.findall(r'@pytest\.mark\.epic\(["\']([^"\']+)', content)
            for epic_marker in epic_markers:
                epic_refs = epic_marker.replace('"', "").replace("'", "").split(",")
                for epic_ref in epic_refs:
                    epic_ref = epic_ref.strip()
                    match = re.match(r"EP-0*(\d+)", epic_ref)
                    if match:
                        epic_number = int(match.group(1))
                        if epic_number not in valid_epic_numbers:
                            self.issues["invalid_epic_refs"].append(
                                {"file": str(test_file), "reference": epic_ref}
                            )

        print(f"  Found {len(self.issues['invalid_us_refs'])} invalid US references")
        print(
            f"  Found {len(self.issues['invalid_epic_refs'])} invalid Epic references\n"
        )

    def _check_database_sync(self):
        """Check if all test files are synced to database."""
        print("Checking database sync status...")

        test_files = list(self.test_root.rglob("test_*.py"))
        test_files += list(self.test_root.rglob("*_test.py"))

        db_test_paths = {test.test_file_path for test in self.session.query(Test).all()}

        for test_file in test_files:
            if "bdd" in str(test_file):
                continue

            test_path = str(test_file).replace("\\", "/")

            if test_path not in db_test_paths:
                self.issues["not_in_db"].append(str(test_file))

        print(f"  Found {len(self.issues['not_in_db'])} tests not in database\n")

    def _print_report(self):
        """Print validation report."""
        print("=" * 80)
        print("TEST ASSOCIATION VALIDATION REPORT")
        print("=" * 80 + "\n")

        total_issues = sum(len(v) for v in self.issues.values())

        if total_issues == 0:
            print("All validation checks passed!")
            print("\nNo issues found.")
            return

        print(f"Found {total_issues} total issues:\n")

        if self.issues["orphaned_tests"]:
            print(f"ORPHANED TESTS ({len(self.issues['orphaned_tests'])}):")
            print("-" * 80)
            for test in self.issues["orphaned_tests"][:10]:
                print(f"  - {test}")
            if len(self.issues["orphaned_tests"]) > 10:
                print(f"  ... and {len(self.issues['orphaned_tests']) - 10} more")
            print()

        if self.issues["invalid_us_refs"]:
            print(
                f"INVALID USER STORY REFERENCES "
                f"({len(self.issues['invalid_us_refs'])}):"
            )
            print("-" * 80)
            for issue in self.issues["invalid_us_refs"][:5]:
                print(f"  - {issue['file']}: {issue['reference']}")
            if len(self.issues["invalid_us_refs"]) > 5:
                print(f"  ... and {len(self.issues['invalid_us_refs']) - 5} more")
            print()

        if self.issues["invalid_epic_refs"]:
            print(f"INVALID EPIC REFERENCES ({len(self.issues['invalid_epic_refs'])}):")
            print("-" * 80)
            for issue in self.issues["invalid_epic_refs"][:5]:
                print(f"  - {issue['file']}: {issue['reference']}")
            if len(self.issues["invalid_epic_refs"]) > 5:
                print(f"  ... and {len(self.issues['invalid_epic_refs']) - 5} more")
            print()

        if self.issues["not_in_db"]:
            print(f"TESTS NOT IN DATABASE ({len(self.issues['not_in_db'])}):")
            print("-" * 80)
            for test in self.issues["not_in_db"][:10]:
                print(f"  - {test}")
            if len(self.issues["not_in_db"]) > 10:
                print(f"  ... and {len(self.issues['not_in_db']) - 10} more")
            print()

        print("\nRECOMMENDATIONS:")
        if self.issues["orphaned_tests"]:
            print("  - Review orphaned tests and add appropriate markers")
        if self.issues["invalid_us_refs"] or self.issues["invalid_epic_refs"]:
            print("  - Update invalid references or create corresponding GitHub issues")
        if self.issues["not_in_db"]:
            print("  - Run: python tools/sync_tests_to_rtm.py to sync to database")

    def close(self):
        """Close database connection."""
        if self.session:
            self.session.close()


if __name__ == "__main__":
    validator = TestAssociationValidator()

    try:
        validator.connect_database()
        validator.validate_all()
    finally:
        validator.close()
