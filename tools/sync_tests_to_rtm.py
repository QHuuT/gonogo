#!/usr/bin/env python3
"""
RTM Database Test Synchronization Tool

Syncs pytest markers from test files to RTM database, creating Test records
and associations with User Stories, Epics, and Components.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker

from be.database import Base
from be.models.traceability.epic import Epic
from be.models.traceability.test import Test
from be.models.traceability.user_story import UserStory
from be.models.traceability.defect import Defect


class RTMTestSynchronizer:
    def __init__(self, associations_file="test_associations.json", database_url="sqlite:///./gonogo.db"):
        self.associations_file = Path(associations_file)
        self.database_url = database_url
        self.associations = {}
        self.session = None
        self.stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'us_links': 0,
            'defect_links': 0,
            'component_inherited': 0
        }

    def connect_database(self):
        """Connect to RTM database."""
        print(f"Connecting to database: {self.database_url}")
        engine = create_engine(self.database_url, echo=False)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        print("Database connected\n")

    def load_associations(self):
        """Load test associations from JSON file."""
        print(f"Loading associations from {self.associations_file}...")
        with open(self.associations_file, 'r') as f:
            self.associations = json.load(f)
        print(f"Loaded {len(self.associations)} test file associations\n")

    def sync_all_tests(self):
        """Sync all test associations to RTM database."""
        print("Syncing test associations to RTM database...\n")

        for relative_path, assoc in self.associations.items():
            test_path = Path(assoc['file_path'])

            if not test_path.exists():
                print(f"SKIP: File not found - {test_path}")
                self.stats['skipped'] += 1
                continue

            if assoc['test_type'] == 'bdd':
                print(f"SKIP: BDD file (not synced to database) - {test_path}")
                self.stats['skipped'] += 1
                continue

            self._sync_test_file(test_path, assoc)

        self._print_summary()

    def _sync_test_file(self, test_path: Path, assoc: Dict):
        """Sync a single test file to database."""
        try:
            test_name = test_path.stem
            test_file_path = str(test_path).replace('\\', '/')

            existing_test = self.session.query(Test).filter(
                Test.test_file_path == test_file_path
            ).first()

            if existing_test:
                test_record = existing_test
                action = "UPDATE"
            else:
                test_record = Test(
                    title=test_name,
                    test_file_path=test_file_path,
                    test_type=assoc['test_type']
                )
                self.session.add(test_record)
                action = "CREATE"

            components = ','.join(assoc['components']) if assoc['components'] else None
            if components:
                test_record.component = components

            if assoc['epics']:
                primary_epic_id = self._get_epic_id(sorted(assoc['epics'])[0])
                if primary_epic_id:
                    test_record.epic_id = primary_epic_id

            self.session.flush()

            test_record.github_user_story_number = None
            if assoc.get('user_stories'):
                for us_marker in assoc['user_stories']:
                    us_number = self._extract_us_number(us_marker)
                    if us_number:
                        test_record.github_user_story_number = us_number
                        self.stats['us_links'] += 1
                        break

            test_record.github_defect_number = None
            defect_linked = False
            if assoc.get('defects'):
                for defect_marker in assoc['defects']:
                    issue_number, defect_obj = self._resolve_and_link_defect(defect_marker, test_record)
                    if issue_number is not None:
                        test_record.github_defect_number = issue_number
                        if defect_obj:
                            defect_linked = True
                        break

            if not test_record.component and test_record.github_user_story_number:
                test_record.inherit_component_from_user_story(self.session)
                if test_record.component:
                    self.stats['component_inherited'] += 1

            if defect_linked:
                self.stats['defect_links'] += 1

            self.session.commit()

            if action == "CREATE":
                self.stats['created'] += 1
                print(f"[CREATED] {test_name}")
            else:
                self.stats['updated'] += 1
                print(f"[UPDATED] {test_name}")

            if assoc['user_stories']:
                print(f"  User Stories: {', '.join(assoc['user_stories'])}")
            if assoc['epics']:
                print(f"  Epics: {', '.join(assoc['epics'])}")
            if test_record.component:
                print(f"  Component: {test_record.component}")

        except Exception as e:
            print(f"[ERROR] {test_path.name}: {e}")
            self.stats['errors'] += 1
            self.session.rollback()

    def _get_epic_id(self, epic_marker: str) -> Optional[int]:
        """Get Epic database ID from marker (e.g., EP-00005)."""
        epic = self.session.query(Epic).filter(
            Epic.epic_id == epic_marker
        ).first()

        return epic.id if epic else None

    def _extract_us_number(self, us_marker: str) -> Optional[int]:
        """Extract GitHub issue number from US marker (e.g., US-00054 -> 54)."""
        match = re.match(r'US-0*(\d+)', us_marker)
        if match:
            return int(match.group(1))
        return None

    def _resolve_and_link_defect(self, defect_marker: str, test_record: Test):
        """Resolve or create a Defect record from a marker string."""
        if not defect_marker:
            return None, None

        marker = str(defect_marker).strip().upper()
        match = re.search(r"DEF[-_\s]*0*(\d+)", marker)
        if not match:
            return None, None

        issue_number = int(match.group(1))
        defect_id = f"DEF-{issue_number:05d}"

        defect = (
            self.session.query(Defect)
            .filter(
                or_(
                    Defect.github_issue_number == issue_number,
                    Defect.defect_id == defect_id,
                )
            )
            .first()
        )

        if defect is None:
            defect = Defect(defect_id=defect_id, github_issue_number=issue_number)
            defect.title = defect.title or f"Placeholder defect {defect_id}"
            defect.description = (
                "Auto-generated via test sync; will be enriched on the next GitHub import."
            )
            defect.github_issue_state = defect.github_issue_state or "open"
            self.session.add(defect)
            self.session.flush()

        if test_record.id is None:
            self.session.flush()

        if test_record.github_user_story_number and not defect.github_user_story_number:
            defect.github_user_story_number = test_record.github_user_story_number

        if test_record.epic_id and not defect.epic_id:
            defect.epic_id = test_record.epic_id

        if not defect.test_id:
            defect.test_id = test_record.id

        if test_record.component and not defect.component:
            defect.component = test_record.component

        return issue_number, defect

    def _extract_epic_number(self, epic_marker: str) -> Optional[int]:
        """Extract GitHub issue number from Epic marker (e.g., EP-00005 -> 5)."""
        match = re.match(r'EP-0*(\d+)', epic_marker)
        if match:
            return int(match.group(1))
        return None

    def _print_summary(self):
        """Print synchronization summary."""
        print("\n" + "="*80)
        print("RTM DATABASE SYNC SUMMARY")
        print("="*80 + "\n")

        print(f"Test Records:")
        print(f"  Created: {self.stats['created']}")
        print(f"  Updated: {self.stats['updated']}")
        print(f"  Skipped: {self.stats['skipped']}")
        print(f"  Errors: {self.stats['errors']}")
        print()

        print(f"Associations:")
        print(f"  User Story links: {self.stats['us_links']}")
        print(f"  Defect links: {self.stats['defect_links']}")
        print(f"  Components inherited: {self.stats['component_inherited']}")
        print()

        total_in_db = self.session.query(Test).count()
        print(f"Total tests in database: {total_in_db}")
        print()

        print("NEXT STEPS:")
        print("1. Verify sync: python tools/rtm-db.py admin health-check")
        print("2. View RTM matrix: http://localhost:8000/api/rtm/reports/matrix?format=html")
        print("3. Proceed to Phase 6: Create automation and maintenance tools")

    def close(self):
        """Close database connection."""
        if self.session:
            self.session.close()


if __name__ == "__main__":
    synchronizer = RTMTestSynchronizer()

    try:
        synchronizer.load_associations()
        synchronizer.connect_database()
        synchronizer.sync_all_tests()
    finally:
        synchronizer.close()