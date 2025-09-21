#!/usr/bin/env python3
"""
RTM Sample Data Population Tool

Populates the RTM database with sample data to demonstrate the dynamic RTM functionality.
Creates realistic Epic, User Story, Test, and Defect data for demonstration purposes.

Related Issue: US-00059 - Dynamic RTM generation and reporting
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from be.database import get_db_session
    from be.models.traceability import Defect, Epic, Test, UserStory

    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Error: Database modules not available: {e}")
    DATABASE_AVAILABLE = False


def populate_sample_data():
    """Populate database with comprehensive sample RTM data."""
    if not DATABASE_AVAILABLE:
        print("❌ Database modules not available")
        return False

    try:
        db = get_db_session()

        print("Clearing existing data...")
        # Clear existing data
        db.query(Defect).delete()
        db.query(Test).delete()
        db.query(UserStory).delete()
        db.query(Epic).delete()
        db.commit()

        print("Creating sample Epics...")

        # Epic 1: Blog Content Management
        epic1 = Epic(
            epic_id="EP-00001",
            title="Blog Content Management",
            description="Core blog functionality for reading and managing posts",
            business_value="Provides core value proposition for blog visitors",
            priority="high",
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=30),
        )
        db.add(epic1)
        db.flush()

        # Epic 2: GDPR Comment System
        epic2 = Epic(
            epic_id="EP-00002",
            title="GDPR-Compliant Comment System",
            description="Privacy-compliant comment system with consent management",
            business_value="Enables user engagement while maintaining GDPR compliance",
            priority="high",
            status="in_progress",
            created_at=datetime.utcnow() - timedelta(days=25),
        )
        db.add(epic2)
        db.flush()

        # Epic 3: Privacy Management
        epic3 = Epic(
            epic_id="EP-00003",
            title="Privacy and Consent Management",
            description="Comprehensive GDPR privacy controls and user rights",
            business_value="Legal compliance and user trust",
            priority="critical",
            status="planned",
            created_at=datetime.utcnow() - timedelta(days=20),
        )
        db.add(epic3)
        db.flush()

        # Epic 4: GitHub Workflow Integration
        epic4 = Epic(
            epic_id="EP-00004",
            title="GitHub Workflow Integration",
            description="Automated GitHub workflows for issue management and epic linking",
            business_value="Streamlined development workflow and automated project management",
            priority="high",
            status="in_progress",
            created_at=datetime.utcnow() - timedelta(days=18),
        )
        db.add(epic4)
        db.flush()

        # Epic 5: RTM Automation (current epic)
        epic5 = Epic(
            epic_id="EP-00005",
            title="Requirements Traceability Matrix Automation",
            description="Database-backed RTM with dynamic reporting and GitHub integration",
            business_value="Improved project visibility and automated compliance tracking",
            priority="high",
            status="in_progress",
            created_at=datetime.utcnow() - timedelta(days=15),
        )
        db.add(epic5)
        db.flush()

        # Epic 6: Test Logging and Reporting
        epic6 = Epic(
            epic_id="EP-00006",
            title="Test Logging and Reporting",
            description="Enhanced test runner with execution modes and structured logging",
            business_value="Improved development efficiency and quality assurance",
            priority="high",
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=12),
        )
        db.add(epic6)
        db.flush()

        # Epic 7: Enhanced Archive Management
        epic7 = Epic(
            epic_id="EP-00007",
            title="Enhanced Archive Management",
            description="Current report tracking and automated cleanup capabilities",
            business_value="Optimized storage management and system performance",
            priority="high",
            status="planned",
            created_at=datetime.utcnow() - timedelta(days=8),
        )
        db.add(epic7)
        db.flush()

        print("Creating sample User Stories...")

        # User Stories for Epic 1 (Blog Management) - Fictional stories with high fictional GitHub issue numbers
        us1 = UserStory(
            user_story_id="US-00001",
            epic_id=epic1.id,
            github_issue_number=999,  # Fictional GitHub issue number
            title="View blog posts without barriers",
            description="As a blog visitor, I want to read posts without registration so that I can access content easily",
            story_points=5,
            priority="high",
            implementation_status="completed",
            created_at=datetime.utcnow() - timedelta(days=28),
        )
        db.add(us1)

        us2 = UserStory(
            user_story_id="US-00002",
            epic_id=epic1.id,
            github_issue_number=998,  # Fictional GitHub issue number
            title="Blog post navigation and discovery",
            description="As a blog visitor, I want to navigate between posts and discover content",
            story_points=3,
            priority="medium",
            implementation_status="completed",
            created_at=datetime.utcnow() - timedelta(days=26),
        )
        db.add(us2)

        # User Stories for Epic 2 (Comment System) - Fictional stories with high fictional GitHub issue numbers
        us3 = UserStory(
            user_story_id="US-00003",
            epic_id=epic2.id,
            github_issue_number=997,  # Fictional GitHub issue number
            title="GDPR-compliant comment submission",
            description="As a blog visitor, I want to submit comments with proper consent management",
            story_points=8,
            priority="high",
            implementation_status="in_progress",
            created_at=datetime.utcnow() - timedelta(days=24),
        )
        db.add(us3)

        us4 = UserStory(
            user_story_id="US-00004",
            epic_id=epic2.id,
            github_issue_number=996,  # Fictional GitHub issue number
            title="Comment display and moderation",
            description="As a blog owner, I want to display and moderate comments effectively",
            story_points=5,
            priority="medium",
            implementation_status="planned",
            created_at=datetime.utcnow() - timedelta(days=22),
        )
        db.add(us4)

        # User Stories for Epic 4 (GitHub Workflow) - Fictional stories with high fictional GitHub issue numbers
        us5 = UserStory(
            user_story_id="US-00049",
            epic_id=epic4.id,
            github_issue_number=995,  # Fictional GitHub issue number
            title="Enhanced epic linking automation",
            description="Automated GitHub workflows for issue management and epic linking",
            story_points=8,
            priority="high",
            implementation_status="completed",
            created_at=datetime.utcnow() - timedelta(days=12),
        )
        db.add(us5)

        us6 = UserStory(
            user_story_id="US-00033",
            epic_id=epic4.id,
            github_issue_number=994,  # Fictional GitHub issue number
            title="GitHub Projects dependencies integration",
            description="Implement blocking relationships using GitHub Projects",
            story_points=5,
            priority="medium",
            implementation_status="completed",
            created_at=datetime.utcnow() - timedelta(days=14),
        )
        db.add(us6)

        # User Stories for Epic 5 (RTM Automation)
        us7 = UserStory(
            user_story_id="US-00058",
            epic_id=epic5.id,
            github_issue_number=58,
            title="Legacy script migration and deprecation",
            description="Migrate file-based RTM tools to hybrid database system",
            story_points=8,
            priority="high",
            implementation_status="completed",
            created_at=datetime.utcnow() - timedelta(days=10),
        )
        db.add(us7)

        us8 = UserStory(
            user_story_id="US-00059",
            epic_id=epic5.id,
            github_issue_number=59,
            title="Dynamic RTM generation and reporting",
            description="Create real-time RTM reports with web dashboard and API",
            story_points=13,
            priority="high",
            implementation_status="completed",
            created_at=datetime.utcnow() - timedelta(days=8),
        )
        db.add(us8)

        us9 = UserStory(
            user_story_id="US-00060",
            epic_id=epic5.id,
            github_issue_number=60,
            title="Comprehensive documentation update",
            description="Update all documentation for database RTM system",
            story_points=5,
            priority="high",
            implementation_status="planned",
            created_at=datetime.utcnow() - timedelta(days=6),
        )
        db.add(us9)

        # User Stories for Epic 6 (Test Logging) - Fictional stories with high fictional GitHub issue numbers
        us10 = UserStory(
            user_story_id="US-00046",
            epic_id=epic6.id,
            github_issue_number=993,  # Fictional GitHub issue number
            title="Enhanced test runner with execution modes",
            description="Test runner with structured logging and execution modes",
            story_points=8,
            priority="high",
            implementation_status="completed",
            created_at=datetime.utcnow() - timedelta(days=10),
        )
        db.add(us10)

        us11 = UserStory(
            user_story_id="US-00047",
            epic_id=epic6.id,
            github_issue_number=992,  # Fictional GitHub issue number
            title="Test report generation with coverage",
            description="Generate HTML test reports with coverage integration",
            story_points=5,
            priority="medium",
            implementation_status="completed",
            created_at=datetime.utcnow() - timedelta(days=8),
        )
        db.add(us11)

        # User Stories for Epic 7 (Archive Management) - Using real GitHub issues that exist
        us12 = UserStory(
            user_story_id="US-00055",
            epic_id=epic7.id,
            github_issue_number=55,  # Real GitHub issue
            title="Current report tracking and cleanup",
            description="Track current reports and implement automated cleanup",
            story_points=5,
            priority="medium",
            implementation_status="planned",
            created_at=datetime.utcnow() - timedelta(days=6),
        )
        db.add(us12)

        us13 = UserStory(
            user_story_id="US-00056",
            epic_id=epic7.id,
            github_issue_number=56,  # Real GitHub issue
            title="Archive bundle creation and management",
            description="Create and manage archive bundles for long-term storage",
            story_points=8,
            priority="low",
            implementation_status="planned",
            created_at=datetime.utcnow() - timedelta(days=4),
        )
        db.add(us13)

        db.flush()  # Get user story IDs

        print("Creating sample Tests...")

        # Tests for Epic 1
        test1 = Test(
            test_type="unit",
            test_file_path="tests/unit/test_blog_content.py",
            title="Test blog post rendering",
            epic_id=epic1.id,
            test_function_name="test_render_blog_post",
            last_execution_status="passed",
            last_execution_time=datetime.utcnow() - timedelta(hours=2),
            execution_duration_ms=150.5,
            created_at=datetime.utcnow() - timedelta(days=25),
        )
        db.add(test1)

        test2 = Test(
            test_type="integration",
            test_file_path="tests/integration/test_blog_api.py",
            title="Test blog API endpoints",
            epic_id=epic1.id,
            test_function_name="test_blog_endpoints",
            last_execution_status="passed",
            last_execution_time=datetime.utcnow() - timedelta(hours=3),
            execution_duration_ms=890.2,
            created_at=datetime.utcnow() - timedelta(days=24),
        )
        db.add(test2)

        test3 = Test(
            test_type="bdd",
            test_file_path="tests/bdd/features/blog_content.feature",
            title="Blog content BDD scenarios",
            epic_id=epic1.id,
            bdd_scenario_name="view_blog_homepage",
            last_execution_status="passed",
            last_execution_time=datetime.utcnow() - timedelta(hours=1),
            execution_duration_ms=2100.8,
            created_at=datetime.utcnow() - timedelta(days=23),
        )
        db.add(test3)

        # Tests for Epic 2 (some failing)
        test4 = Test(
            test_type="unit",
            test_file_path="tests/unit/test_comment_system.py",
            title="Test comment validation",
            epic_id=epic2.id,
            test_function_name="test_comment_validation",
            last_execution_status="failed",
            last_execution_time=datetime.utcnow() - timedelta(hours=4),
            execution_duration_ms=75.3,
            last_error_message="AssertionError: GDPR consent validation failed",
            created_at=datetime.utcnow() - timedelta(days=20),
        )
        db.add(test4)

        test5 = Test(
            test_type="integration",
            test_file_path="tests/integration/test_comment_api.py",
            title="Test comment submission API",
            epic_id=epic2.id,
            test_function_name="test_submit_comment",
            last_execution_status="passed",
            last_execution_time=datetime.utcnow() - timedelta(hours=2),
            execution_duration_ms=456.7,
            created_at=datetime.utcnow() - timedelta(days=19),
        )
        db.add(test5)

        # Tests for Epic 4 (GitHub Workflow)
        test6 = Test(
            test_type="integration",
            test_file_path="tests/integration/test_github_workflow.py",
            title="Test GitHub workflow automation",
            epic_id=epic4.id,
            test_function_name="test_epic_linking_workflow",
            last_execution_status="passed",
            last_execution_time=datetime.utcnow() - timedelta(hours=1),
            execution_duration_ms=890.5,
            created_at=datetime.utcnow() - timedelta(days=10),
        )
        db.add(test6)

        test7 = Test(
            test_type="unit",
            test_file_path="tests/unit/test_github_integration.py",
            title="Test GitHub Projects integration",
            epic_id=epic4.id,
            test_function_name="test_project_dependencies",
            last_execution_status="passed",
            last_execution_time=datetime.utcnow() - timedelta(hours=2),
            execution_duration_ms=156.3,
            created_at=datetime.utcnow() - timedelta(days=8),
        )
        db.add(test7)

        # Tests for Epic 5 (RTM)
        test8 = Test(
            test_type="unit",
            test_file_path="tests/unit/test_rtm_generator.py",
            title="Test RTM report generation",
            epic_id=epic5.id,
            test_function_name="test_generate_rtm_matrix",
            last_execution_status="passed",
            last_execution_time=datetime.utcnow() - timedelta(minutes=30),
            execution_duration_ms=234.1,
            created_at=datetime.utcnow() - timedelta(days=5),
        )
        db.add(test8)

        test9 = Test(
            test_type="integration",
            test_file_path="tests/integration/test_rtm_api.py",
            title="Test RTM API endpoints",
            epic_id=epic5.id,
            test_function_name="test_rtm_endpoints",
            last_execution_status="passed",
            last_execution_time=datetime.utcnow() - timedelta(minutes=45),
            execution_duration_ms=1200.5,
            created_at=datetime.utcnow() - timedelta(days=4),
        )
        db.add(test9)

        test10 = Test(
            test_type="unit",
            test_file_path="tests/unit/test_dashboard.py",
            title="Test RTM dashboard functionality",
            epic_id=epic5.id,
            test_function_name="test_dashboard_widgets",
            last_execution_status="skipped",
            last_execution_time=datetime.utcnow() - timedelta(minutes=15),
            last_error_message="Dashboard tests require web driver",
            created_at=datetime.utcnow() - timedelta(days=3),
        )
        db.add(test10)

        # Tests for Epic 6 (Test Logging)
        test11 = Test(
            test_type="unit",
            test_file_path="tests/unit/test_report_generator.py",
            title="Test report generator functionality",
            epic_id=epic6.id,
            test_function_name="test_generate_html_report",
            last_execution_status="passed",
            last_execution_time=datetime.utcnow() - timedelta(hours=3),
            execution_duration_ms=345.2,
            created_at=datetime.utcnow() - timedelta(days=8),
        )
        db.add(test11)

        test12 = Test(
            test_type="integration",
            test_file_path="tests/integration/test_test_runner.py",
            title="Test enhanced test runner",
            epic_id=epic6.id,
            test_function_name="test_execution_modes",
            last_execution_status="passed",
            last_execution_time=datetime.utcnow() - timedelta(hours=1),
            execution_duration_ms=1890.7,
            created_at=datetime.utcnow() - timedelta(days=6),
        )
        db.add(test12)

        # Tests for Epic 7 (Archive Management)
        test13 = Test(
            test_type="unit",
            test_file_path="tests/unit/test_archive_cleanup.py",
            title="Test archive cleanup functionality",
            epic_id=epic7.id,
            test_function_name="test_cleanup_policies",
            last_execution_status="passed",
            last_execution_time=datetime.utcnow() - timedelta(hours=4),
            execution_duration_ms=234.5,
            created_at=datetime.utcnow() - timedelta(days=5),
        )
        db.add(test13)

        db.flush()  # Get test IDs

        print("Creating sample Defects...")

        # Defects
        defect1 = Defect(
            defect_id="DEF-00001",
            github_issue_number=101,
            title="Comment validation bypasses GDPR consent check",
            description="Users can submit comments without proper GDPR consent validation",
            severity="high",
            priority="high",
            status="open",
            epic_id=epic2.id,
            test_id=test4.id,
            is_security_issue=True,
            created_at=datetime.utcnow() - timedelta(days=2),
        )
        db.add(defect1)

        defect2 = Defect(
            defect_id="DEF-00002",
            github_issue_number=102,
            title="Blog post navigation broken on mobile",
            description="Navigation between blog posts fails on mobile devices",
            severity="medium",
            priority="medium",
            status="in_progress",
            epic_id=epic1.id,
            is_security_issue=False,
            created_at=datetime.utcnow() - timedelta(days=5),
        )
        db.add(defect2)

        defect3 = Defect(
            defect_id="DEF-00003",
            github_issue_number=103,
            title="RTM dashboard performance issue with large datasets",
            description="Dashboard becomes slow when loading many epics",
            severity="low",
            priority="low",
            status="planned",
            epic_id=epic5.id,
            is_security_issue=False,
            created_at=datetime.utcnow() - timedelta(days=1),
        )
        db.add(defect3)

        defect4 = Defect(
            defect_id="DEF-00004",
            github_issue_number=104,
            title="Critical security vulnerability in user data handling",
            description="Potential data exposure in comment system",
            severity="critical",
            priority="critical",
            status="open",
            epic_id=epic2.id,
            is_security_issue=True,
            created_at=datetime.utcnow() - timedelta(hours=6),
        )
        db.add(defect4)

        defect5 = Defect(
            defect_id="DEF-00008",
            github_issue_number=108,
            title="GitHub workflow timeout on large repositories",
            description="Epic linking automation fails with timeout on repositories with many issues",
            severity="medium",
            priority="medium",
            status="planned",
            epic_id=epic4.id,
            test_id=test6.id,
            is_security_issue=False,
            created_at=datetime.utcnow() - timedelta(hours=12),
        )
        db.add(defect5)

        # Commit all changes
        db.commit()

        print("[OK] Sample data populated successfully!")
        print("\nSummary:")
        print(f"  - Epics: {db.query(Epic).count()}")
        print(f"  - User Stories: {db.query(UserStory).count()}")
        print(f"  - Tests: {db.query(Test).count()}")
        print(f"  - Defects: {db.query(Defect).count()}")

        return True

    except Exception as e:
        print(f"[ERROR] Error populating sample data: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def show_sample_data_summary():
    """Show summary of populated sample data."""
    if not DATABASE_AVAILABLE:
        return

    try:
        db = get_db_session()

        print("\nSample Data Summary")
        print("=" * 50)

        epics = db.query(Epic).all()
        for epic in epics:
            user_stories = (
                db.query(UserStory).filter(UserStory.epic_id == epic.id).all()
            )
            tests = db.query(Test).filter(Test.epic_id == epic.id).all()
            defects = db.query(Defect).filter(Defect.epic_id == epic.id).all()

            total_points = sum(us.story_points for us in user_stories)
            completed_points = sum(
                us.story_points
                for us in user_stories
                if us.implementation_status in ["completed", "done"]
            )
            completion = (
                (completed_points / total_points * 100) if total_points > 0 else 0
            )

            print(f"\n{epic.epic_id}: {epic.title}")
            print(f"  Status: {epic.status} | Priority: {epic.priority}")
            print(f"  User Stories: {len(user_stories)} ({total_points} points)")
            print(
                f"  Completion: {completion:.1f}% ({completed_points}/{total_points} points)"
            )
            print(f"  Tests: {len(tests)} | Defects: {len(defects)}")

            if tests:
                passed = sum(1 for t in tests if t.last_execution_status == "passed")
                failed = sum(1 for t in tests if t.last_execution_status == "failed")
                skipped = sum(1 for t in tests if t.last_execution_status == "skipped")
                print(
                    f"  Test Results: {passed} passed, {failed} failed, {skipped} skipped"
                )

    except Exception as e:
        print(f"[ERROR] Error showing summary: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Populate RTM database with sample data"
    )
    parser.add_argument(
        "--populate", action="store_true", help="Populate database with sample data"
    )
    parser.add_argument(
        "--summary", action="store_true", help="Show summary of existing data"
    )

    args = parser.parse_args()

    if args.populate:
        if populate_sample_data():
            show_sample_data_summary()
    elif args.summary:
        show_sample_data_summary()
    else:
        parser.print_help()
