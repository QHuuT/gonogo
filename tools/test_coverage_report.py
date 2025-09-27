#!/usr/bin/env python3
"""
Test Coverage Report Generator

Generates reports showing test coverage for User Stories, Epics, and Components.
"""

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from be.models.traceability.epic import Epic
from be.models.traceability.test import Test
from be.models.traceability.user_story import UserStory


class TestCoverageReporter:
    __test__ = False  # Tell pytest this is not a test class

    def __init__(self, database_url="sqlite:///./gonogo.db"):
        self.database_url = database_url
        self.session = None

    def connect_database(self):
        """Connect to RTM database."""
        engine = create_engine(self.database_url, echo=False)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def generate_report(self, user_story_filter=None):
        """Generate test coverage report."""
        print("=" * 80)
        print("TEST COVERAGE REPORT")
        print("=" * 80 + "\n")

        if user_story_filter:
            self._report_user_story(user_story_filter)
        else:
            self._report_overview()
            self._report_by_epic()
            self._report_by_component()
            self._report_by_type()

    def _report_overview(self):
        """Print overview statistics."""
        total_tests = self.session.query(Test).count()
        tests_with_us = (
            self.session.query(Test)
            .filter(Test.github_user_story_number.isnot(None))
            .count()
        )
        tests_with_epic = (
            self.session.query(Test).filter(Test.epic_id.isnot(None)).count()
        )
        tests_with_component = (
            self.session.query(Test).filter(Test.component.isnot(None)).count()
        )

        print("OVERVIEW:")
        print(f"  Total tests: {total_tests}")
        print(
            f"  Tests with User Story: {tests_with_us} ({tests_with_us * 100 // total_tests if total_tests else 0}%)"
        )
        print(
            f"  Tests with Epic: {tests_with_epic} ({tests_with_epic * 100 // total_tests if total_tests else 0}%)"
        )
        print(
            f"  Tests with Component: {tests_with_component} ({tests_with_component * 100 // total_tests if total_tests else 0}%)"
        )
        print()

    def _report_by_epic(self):
        """Print coverage by Epic."""
        print("COVERAGE BY EPIC:")
        print("-" * 80)

        epics = self.session.query(Epic).all()

        for epic in epics:
            test_count = (
                self.session.query(Test).filter(Test.epic_id == epic.id).count()
            )

            us_count = (
                self.session.query(UserStory)
                .filter(UserStory.epic_id == epic.id)
                .count()
            )

            print(f"  {epic.title or f'Epic #{epic.github_issue_number}'}:")
            print(f"    Tests: {test_count}")
            print(f"    User Stories: {us_count}")

        print()

    def _report_by_component(self):
        """Print coverage by Component."""
        print("COVERAGE BY COMPONENT:")
        print("-" * 80)

        tests = self.session.query(Test).all()
        component_tests = defaultdict(int)

        for test in tests:
            if test.component:
                components = [c.strip() for c in test.component.split(",")]
                for comp in components:
                    component_tests[comp] += 1

        for component in sorted(component_tests.keys()):
            count = component_tests[component]
            print(f"  {component}: {count} test(s)")

        print()

    def _report_by_type(self):
        """Print coverage by test type."""
        print("COVERAGE BY TEST TYPE:")
        print("-" * 80)

        tests = self.session.query(Test).all()
        type_counts = defaultdict(int)

        for test in tests:
            type_counts[test.test_type] += 1

        for test_type in sorted(type_counts.keys()):
            count = type_counts[test_type]
            print(f"  {test_type}: {count} test(s)")

        print()

    def _report_user_story(self, us_number: int):
        """Print detailed report for specific User Story."""
        user_story = (
            self.session.query(UserStory)
            .filter(UserStory.github_issue_number == us_number)
            .first()
        )

        if not user_story:
            print(f"User Story #{us_number} not found in database")
            return

        tests = (
            self.session.query(Test)
            .filter(Test.github_user_story_number == us_number)
            .all()
        )

        print(f"USER STORY: {user_story.title or f'US #{us_number}'}")
        print("-" * 80)
        print(f"  GitHub Issue: #{us_number}")
        if user_story.epic:
            print(
                f"  Epic: {user_story.epic.title or f'Epic #{user_story.epic.github_issue_number}'}"
            )
        print(f"  Component: {user_story.component or 'Not specified'}")
        print(f"  Total Tests: {len(tests)}")
        print()

        if tests:
            print("  TESTS:")
            by_type = defaultdict(list)
            for test in tests:
                by_type[test.test_type].append(test)

            for test_type in sorted(by_type.keys()):
                print(f"\n    {test_type.upper()} ({len(by_type[test_type])}):")
                for test in by_type[test_type]:
                    print(f"      - {test.title or test.test_file_path}")
        else:
            print("  No tests found for this User Story")

        print()

    def close(self):
        """Close database connection."""
        if self.session:
            self.session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate test coverage reports")
    parser.add_argument(
        "--user-story", type=int, help="Generate report for specific User Story number"
    )
    args = parser.parse_args()

    reporter = TestCoverageReporter()

    try:
        reporter.connect_database()
        reporter.generate_report(user_story_filter=args.user_story)
    finally:
        reporter.close()
