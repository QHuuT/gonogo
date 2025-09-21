#!/usr/bin/env python3
"""
RTM Demo Report Generator - Test Data

Generates Requirements Traceability Matrix reports using demo/test data for development and testing.
Uses sample data to demonstrate RTM features without affecting production database.

Usage:
    python tools/rtm_demo.py --html                    # Generate demo HTML report
    python tools/rtm_demo.py --populate-test-data      # Populate database with test data
    python tools/rtm_demo.py --reset-to-demo           # Reset database to demo state

Related Issue: US-00059 - Dynamic RTM generation and reporting
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.be.database import get_db_session
from src.be.models.traceability import Epic, UserStory, Test, Defect
from src.be.services.rtm_report_generator import RTMReportGenerator


class RTMDemoDataGenerator:
    """Generate demo/test data for RTM reports."""

    def __init__(self):
        self.db = get_db_session()

    def create_demo_epics(self) -> List[Epic]:
        """Create demo epics for testing."""
        demo_epics = [
            {
                "epic_id": "EP-DEMO-001",
                "title": "Demo Blog Platform",
                "description": "A demonstration blog platform with basic features for RTM testing",
                "business_value": "Demo value proposition",
                "priority": "high",
                "status": "in_progress",
                "github_issue_number": 999
            },
            {
                "epic_id": "EP-DEMO-002",
                "title": "Demo User Management",
                "description": "Demo user authentication and profile management system",
                "business_value": "Demo user experience",
                "priority": "medium",
                "status": "planned",
                "github_issue_number": 998
            },
            {
                "epic_id": "EP-DEMO-003",
                "title": "Demo Security Features",
                "description": "Demo security and compliance features for testing",
                "business_value": "Demo security compliance",
                "priority": "high",
                "status": "completed",
                "github_issue_number": 997
            }
        ]

        epics = []
        for epic_data in demo_epics:
            # Check if epic already exists
            existing = self.db.query(Epic).filter(Epic.epic_id == epic_data["epic_id"]).first()
            if not existing:
                epic = Epic(**epic_data)
                self.db.add(epic)
                epics.append(epic)
            else:
                epics.append(existing)

        self.db.commit()
        return epics

    def create_demo_user_stories(self, epics: List[Epic]) -> List[UserStory]:
        """Create demo user stories for testing."""
        demo_stories = [
            {
                "user_story_id": "US-DEMO-001",
                "title": "Demo blog post creation",
                "description": "As a demo user, I want to create blog posts",
                "story_points": 5,
                "implementation_status": "completed",
                "github_issue_number": 901,
                "epic_id": epics[0].id
            },
            {
                "user_story_id": "US-DEMO-002",
                "title": "Demo blog post editing",
                "description": "As a demo user, I want to edit my blog posts",
                "story_points": 3,
                "implementation_status": "in_progress",
                "github_issue_number": 902,
                "epic_id": epics[0].id
            },
            {
                "user_story_id": "US-DEMO-003",
                "title": "Demo user registration",
                "description": "As a demo visitor, I want to register for an account",
                "story_points": 8,
                "implementation_status": "planned",
                "github_issue_number": 903,
                "epic_id": epics[1].id
            },
            {
                "user_story_id": "US-DEMO-004",
                "title": "Demo security audit logging",
                "description": "As a demo admin, I want all actions logged for security",
                "story_points": 5,
                "implementation_status": "completed",
                "github_issue_number": 904,
                "epic_id": epics[2].id
            }
        ]

        stories = []
        for story_data in demo_stories:
            existing = self.db.query(UserStory).filter(UserStory.user_story_id == story_data["user_story_id"]).first()
            if not existing:
                story = UserStory(**story_data)
                self.db.add(story)
                stories.append(story)
            else:
                stories.append(existing)

        self.db.commit()
        return stories

    def create_demo_tests(self, epics: List[Epic]) -> List[Test]:
        """Create demo tests for testing."""
        demo_tests = [
            {
                "title": "Demo Blog Post Creation Test",
                "test_file_path": "tests/demo/test_blog_creation.py",
                "test_function_name": "test_create_blog_post",
                "test_type": "unit",
                "last_execution_status": "passed",
                "execution_duration_ms": 150,
                "epic_id": epics[0].id
            },
            {
                "title": "Demo Blog Workflow Integration Test",
                "test_file_path": "tests/demo/test_blog_integration.py",
                "test_function_name": "test_blog_workflow",
                "test_type": "integration",
                "last_execution_status": "passed",
                "execution_duration_ms": 2500,
                "epic_id": epics[0].id
            },
            {
                "title": "Demo Complete User Journey E2E Test",
                "test_file_path": "tests/demo/test_user_e2e.py",
                "test_function_name": "test_complete_user_journey",
                "test_type": "e2e",
                "last_execution_status": "failed",
                "execution_duration_ms": 15000,
                "epic_id": epics[1].id
            },
            {
                "title": "Demo Security Audit Log Test",
                "test_file_path": "tests/demo/test_security_audit.py",
                "test_function_name": "test_security_logging",
                "test_type": "security",
                "last_execution_status": "passed",
                "execution_duration_ms": 800,
                "epic_id": epics[2].id
            }
        ]

        tests = []
        for test_data in demo_tests:
            # Check if test already exists by file path and function name
            existing = self.db.query(Test).filter(
                Test.test_file_path == test_data["test_file_path"],
                Test.test_function_name == test_data["test_function_name"]
            ).first()
            if not existing:
                test = Test(**test_data)
                test.last_execution_time = datetime.now() - timedelta(hours=2)
                self.db.add(test)
                tests.append(test)
            else:
                tests.append(existing)

        self.db.commit()
        return tests

    def create_demo_defects(self, epics: List[Epic]) -> List[Defect]:
        """Create demo defects for testing."""
        demo_defects = [
            {
                "defect_id": "DEF-DEMO-001",
                "title": "Demo blog save button not working",
                "description": "Demo defect: Save button doesn't respond on blog creation form",
                "priority": "high",
                "status": "open",
                "severity": "medium",
                "github_issue_number": 801,
                "epic_id": epics[0].id
            },
            {
                "defect_id": "DEF-DEMO-002",
                "title": "Demo user login timeout too short",
                "description": "Demo defect: Users get logged out too quickly",
                "priority": "medium",
                "status": "in_progress",
                "severity": "low",
                "github_issue_number": 802,
                "epic_id": epics[1].id
            },
            {
                "defect_id": "DEF-DEMO-003",
                "title": "Demo security vulnerability in auth",
                "description": "Demo defect: Critical security issue in authentication",
                "priority": "critical",
                "status": "resolved",
                "severity": "critical",
                "github_issue_number": 803,
                "epic_id": epics[2].id
            }
        ]

        defects = []
        for defect_data in demo_defects:
            existing = self.db.query(Defect).filter(Defect.defect_id == defect_data["defect_id"]).first()
            if not existing:
                defect = Defect(**defect_data)
                self.db.add(defect)
                defects.append(defect)
            else:
                defects.append(existing)

        self.db.commit()
        return defects

    def populate_demo_data(self):
        """Populate database with complete demo dataset."""
        print("[DEMO] Populating demo data...")

        epics = self.create_demo_epics()
        print(f"[DEMO] Created {len(epics)} demo epics")

        stories = self.create_demo_user_stories(epics)
        print(f"[DEMO] Created {len(stories)} demo user stories")

        tests = self.create_demo_tests(epics)
        print(f"[DEMO] Created {len(tests)} demo tests")

        defects = self.create_demo_defects(epics)
        print(f"[DEMO] Created {len(defects)} demo defects")

        print("[DEMO] Demo data population complete!")

    def reset_to_demo_only(self):
        """Reset database to contain only demo data."""
        print("[DEMO] Resetting database to demo-only state...")

        # Delete all non-demo data
        self.db.query(Test).filter(~Test.test_file_path.like("tests/demo/%")).delete()
        self.db.query(Defect).filter(~Defect.defect_id.like("DEF-DEMO-%")).delete()
        self.db.query(UserStory).filter(~UserStory.user_story_id.like("US-DEMO-%")).delete()
        self.db.query(Epic).filter(~Epic.epic_id.like("EP-DEMO-%")).delete()

        self.db.commit()

        # Populate with demo data
        self.populate_demo_data()
        print("[DEMO] Database reset to demo-only state complete!")

    def close(self):
        """Close database connection."""
        self.db.close()


def generate_demo_report(output_path: str = None):
    """Generate RTM report using demo/test data."""
    if not output_path:
        output_path = "quality/reports/dynamic_rtm/rtm_matrix_demo.html"

    print(f"[DEMO] Generating demo RTM report...")

    db = get_db_session()
    try:
        generator = RTMReportGenerator(db)
        html_content = generator.generate_html_matrix({"include_tests": True, "include_defects": True})
    finally:
        db.close()

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Save report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"[DEMO] Demo report saved to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="RTM Demo Report Generator")
    parser.add_argument("--html", action="store_true",
                       help="Generate demo HTML report")
    parser.add_argument("--populate-test-data", action="store_true",
                       help="Populate database with demo/test data")
    parser.add_argument("--reset-to-demo", action="store_true",
                       help="Reset database to demo-only state")
    parser.add_argument("--output", type=str,
                       help="Output file path for HTML report")

    args = parser.parse_args()

    if args.reset_to_demo:
        demo_gen = RTMDemoDataGenerator()
        try:
            demo_gen.reset_to_demo_only()
        finally:
            demo_gen.close()

    elif args.populate_test_data:
        demo_gen = RTMDemoDataGenerator()
        try:
            demo_gen.populate_demo_data()
        finally:
            demo_gen.close()

    elif args.html:
        generate_demo_report(args.output)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()