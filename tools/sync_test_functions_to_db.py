#!/usr/bin/env python3
"""
Sync individual test functions to database with proper function names and markers.
"""

import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.be.models.traceability.test import Test
from src.be.models.traceability.epic import Epic


class TestFunctionSync:
    def __init__(self, database_url='sqlite:///./gonogo.db'):
        self.database_url = database_url
        self.session = None
        self.stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0
        }

    def connect(self):
        """Connect to database."""
        engine = create_engine(self.database_url, echo=False)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def load_functions(self, functions_file='test_functions.json'):
        """Load test functions from JSON."""
        with open(functions_file, 'r') as f:
            return json.load(f)

    def get_epic_db_id(self, epic_marker: str):
        """Get epic database ID from marker like EP-00001."""
        epic = self.session.query(Epic).filter(Epic.epic_id == epic_marker).first()
        return epic.id if epic else None

    def sync_functions(self):
        """Sync all test functions to database."""
        functions_data = self.load_functions()

        print(f"Syncing {len(functions_data)} test files...")

        for file_key, file_data in functions_data.items():
            file_path = file_data['file_path'].replace('\\', '/')
            functions = file_data['functions']

            print(f"\n{file_key}: {len(functions)} functions")

            for func in functions:
                self._sync_function(file_path, func)

        self.session.commit()
        self._print_summary()

    def _sync_function(self, file_path: str, func_data: dict):
        """Sync a single test function."""
        func_name = func_data['name']
        class_name = func_data.get('class_name')

        # Build full test identifier
        if class_name:
            title = f"{class_name}::{func_name}"
        else:
            title = func_name

        # Check if test already exists
        existing = self.session.query(Test).filter(
            Test.test_file_path == file_path,
            Test.test_function_name == func_name
        ).first()

        if existing:
            test_record = existing
            action = "UPDATE"
        else:
            # Determine test type from path
            if '/unit/' in file_path:
                test_type = 'unit'
            elif '/integration/' in file_path:
                test_type = 'integration'
            elif '/e2e/' in file_path:
                test_type = 'e2e'
            else:
                test_type = 'unit'

            test_record = Test(
                title=title,
                test_file_path=file_path,
                test_function_name=func_name,
                test_type=test_type,
                description=func_data.get('docstring', '')
            )
            self.session.add(test_record)
            action = "CREATE"

        # Update epic
        if func_data['epics']:
            primary_epic_id = self.get_epic_db_id(func_data['epics'][0])
            if primary_epic_id:
                test_record.epic_id = primary_epic_id

        # Update component
        if func_data['components']:
            test_record.component = ','.join(func_data['components'])

        # Update user story (take first one)
        if func_data['user_stories']:
            us_marker = func_data['user_stories'][0]
            # Extract number from US-00001
            import re
            match = re.match(r'US-0*(\d+)', us_marker)
            if match:
                test_record.github_user_story_number = int(match.group(1))

        if action == "CREATE":
            self.stats['created'] += 1
            print(f"  [NEW] {func_name}")
        else:
            self.stats['updated'] += 1

        self.session.flush()

    def _print_summary(self):
        """Print sync summary."""
        print("\n" + "="*80)
        print("TEST FUNCTION SYNC SUMMARY")
        print("="*80)
        print(f"Created: {self.stats['created']}")
        print(f"Updated: {self.stats['updated']}")
        print(f"Skipped: {self.stats['skipped']}")
        print(f"Total: {self.stats['created'] + self.stats['updated']}")


def main():
    sync = TestFunctionSync()
    sync.connect()
    sync.sync_functions()


if __name__ == '__main__':
    main()