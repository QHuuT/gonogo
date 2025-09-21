#!/usr/bin/env python3
"""
RTM Report Generator - Live Data

Generates Requirements Traceability Matrix reports using live data from the RTM database.
Connects to the production database and creates interactive HTML reports with real project data.

Related Issue: US-00059 - Dynamic RTM generation and reporting
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from be.database import get_db_session
    from be.models.traceability import Defect, Epic, Test, UserStory
    from be.services.rtm_report_generator import RTMReportGenerator

    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Database modules not available: {e}")
    DATABASE_AVAILABLE = False


class DynamicRTMDemo:
    """Demo tool for dynamic RTM generation capabilities."""

    def __init__(self):
        self.db_session = None
        self.report_generator = None

    def initialize_database(self) -> bool:
        """Initialize database connection and report generator."""
        if not DATABASE_AVAILABLE:
            print("[ERROR] Database modules not available")
            return False

        try:
            self.db_session = get_db_session()
            self.report_generator = RTMReportGenerator(self.db_session)
            print("[OK] Database connection established")
            return True
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False

    def show_system_status(self):
        """Display current RTM system status."""
        print("\nRTM System Status")
        print("=" * 50)

        if not self.initialize_database():
            print("Database: [X] Not available")
            return

        try:
            # Get basic counts
            epic_count = self.db_session.query(Epic).count()
            us_count = self.db_session.query(UserStory).count()
            test_count = self.db_session.query(Test).count()
            defect_count = self.db_session.query(Defect).count()

            print(f"Database: [OK] Connected")
            print(f"Total Epics: {epic_count}")
            print(f"Total User Stories: {us_count}")
            print(f"Total Tests: {test_count}")
            print(f"Total Defects: {defect_count}")

            # Epic status distribution
            if epic_count > 0:
                print("\nEpic Status Distribution:")
                epics = self.db_session.query(Epic).all()
                status_counts = {}
                for epic in epics:
                    status_counts[epic.status] = status_counts.get(epic.status, 0) + 1

                for status, count in status_counts.items():
                    print(f"  {status}: {count}")

        except Exception as e:
            print(f"[ERROR] Error querying database: {e}")
        finally:
            if self.db_session:
                self.db_session.close()

    def generate_json_report(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate RTM matrix in JSON format."""
        if not self.initialize_database():
            return {"error": "Database not available"}

        try:
            filters = filters or {}
            report = self.report_generator.generate_json_matrix(filters)
            return report
        except Exception as e:
            return {"error": f"Report generation failed: {e}"}
        finally:
            if self.db_session:
                self.db_session.close()

    def generate_markdown_report(self, filters: Dict[str, Any] = None) -> str:
        """Generate RTM matrix in Markdown format."""
        if not self.initialize_database():
            return "[ERROR] Database not available"

        try:
            filters = filters or {}
            report = self.report_generator.generate_markdown_matrix(filters)
            return report
        except Exception as e:
            return f"[ERROR] Report generation failed: {e}"
        finally:
            if self.db_session:
                self.db_session.close()

    def generate_html_report(self, filters: Dict[str, Any] = None) -> str:
        """Generate RTM matrix in HTML format."""
        if not self.initialize_database():
            return "<html><body><h1>Database not available</h1></body></html>"

        try:
            filters = filters or {}
            report = self.report_generator.generate_html_matrix(filters)
            return report
        except Exception as e:
            return f"<html><body><h1>Report generation failed: {e}</h1></body></html>"
        finally:
            if self.db_session:
                self.db_session.close()

    def demo_dashboard_data(self):
        """Demonstrate dashboard data generation."""
        if not self.initialize_database():
            return

        print("\nDashboard Data Demo")
        print("=" * 50)

        try:
            # Simulate dashboard data query
            dashboard_data = {
                "timestamp": "2025-09-21T12:00:00Z",
                "epic_status": {"planned": 2, "in_progress": 3, "completed": 1},
                "user_story_status": {"planned": 5, "in_progress": 8, "completed": 12},
                "test_execution": {"passed": 45, "failed": 3, "skipped": 2},
                "defect_severity": {"critical": 1, "high": 2, "medium": 5, "low": 3},
                "recent_activity": {"test_executions": 25, "new_defects": 2},
                "summary": {
                    "total_epics": self.db_session.query(Epic).count(),
                    "total_user_stories": self.db_session.query(UserStory).count(),
                    "total_tests": self.db_session.query(Test).count(),
                    "total_defects": self.db_session.query(Defect).count(),
                },
            }

            print("Dashboard Data Structure:")
            print(json.dumps(dashboard_data, indent=2))

        except Exception as e:
            print(f"[ERROR] Dashboard demo failed: {e}")
        finally:
            if self.db_session:
                self.db_session.close()

    def demo_epic_progress(self):
        """Demonstrate epic progress reporting."""
        if not self.initialize_database():
            return

        print("\nEpic Progress Demo")
        print("=" * 50)

        try:
            progress_report = self.report_generator.generate_epic_progress_json(
                include_charts=True
            )

            print("Epic Progress Report Structure:")
            print(f"Generated at: {progress_report['metadata']['generated_at']}")
            print(f"Total epics: {progress_report['metadata']['total_epics']}")

            if progress_report["epic_progress"]:
                print("\nFirst Epic Details:")
                first_epic = progress_report["epic_progress"][0]
                print(f"Epic ID: {first_epic['epic']['epic_id']}")
                print(f"Title: {first_epic['epic']['title']}")
                print(
                    f"Completion: {first_epic['metrics']['completion_percentage']:.1f}%"
                )
                print(f"User Stories: {first_epic['metrics']['user_stories_count']}")
                print(f"Tests: {first_epic['metrics']['tests_count']}")
                print(f"Test Pass Rate: {first_epic['metrics']['test_pass_rate']:.1f}%")

            print(f"\nOverall Summary:")
            print(
                f"Overall completion: {progress_report['summary']['overall_completion']:.1f}%"
            )
            print(
                f"Total story points: {progress_report['summary']['total_story_points']}"
            )

        except Exception as e:
            print(f"[ERROR] Epic progress demo failed: {e}")
        finally:
            if self.db_session:
                self.db_session.close()

    def save_report(self, content: str, filename: str):
        """Save report content to file."""
        output_dir = Path("quality/reports/dynamic_rtm")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            if filename.endswith(".json"):
                if isinstance(content, dict):
                    json.dump(content, f, indent=2)
                else:
                    f.write(content)
            else:
                f.write(content)

        print(f"[OK] Report saved to: {output_path}")

    def run_comprehensive_demo(self):
        """Run comprehensive demonstration of all features."""
        print("Dynamic RTM Generation Demo")
        print("=" * 60)

        # 1. System Status
        self.show_system_status()

        # 2. Dashboard Data Demo
        self.demo_dashboard_data()

        # 3. Epic Progress Demo
        self.demo_epic_progress()

        # 4. Generate Sample Reports
        print("\nGenerating Sample Reports")
        print("=" * 50)

        # JSON Report
        print("Generating JSON RTM matrix...")
        json_report = self.generate_json_report()
        if "error" not in json_report:
            self.save_report(json_report, "rtm_matrix_sample.json")
        else:
            print(f"[ERROR] JSON report failed: {json_report['error']}")

        # Markdown Report
        print("Generating Markdown RTM matrix...")
        markdown_report = self.generate_markdown_report()
        if not markdown_report.startswith("[ERROR]"):
            self.save_report(markdown_report, "rtm_matrix_sample.md")
        else:
            print(markdown_report)

        # HTML Report
        print("Generating HTML RTM matrix...")
        html_report = self.generate_html_report()
        if not html_report.startswith("<html><body><h1>Database not available"):
            self.save_report(html_report, "rtm_matrix_sample.html")
        else:
            print("[ERROR] HTML report failed: Database not available")

        print(
            "\n[OK] Demo completed! Check quality/reports/dynamic_rtm/ for generated files."
        )

    def show_api_examples(self):
        """Show API endpoint examples."""
        print("\nAPI Endpoint Examples")
        print("=" * 50)

        base_url = "http://localhost:8000/api/rtm"

        endpoints = [
            ("Dashboard", f"{base_url}/dashboard"),
            ("Dashboard Data", f"{base_url}/reports/dashboard-data"),
            ("JSON Matrix", f"{base_url}/reports/matrix?format=json"),
            ("HTML Matrix", f"{base_url}/reports/matrix?format=html"),
            ("Markdown Matrix", f"{base_url}/reports/matrix?format=markdown"),
            ("Epic Progress (JSON)", f"{base_url}/reports/epic-progress?format=json"),
            ("Epic Progress (HTML)", f"{base_url}/reports/epic-progress?format=html"),
            ("Test Coverage", f"{base_url}/reports/test-coverage?format=json"),
            ("Defect Analysis", f"{base_url}/reports/defect-analysis?format=json"),
            ("CSV Export", f"{base_url}/reports/export/full-matrix?format=csv"),
        ]

        print("Available endpoints:")
        for name, url in endpoints:
            print(f"  {name}: {url}")

        print("\nFiltering examples:")
        print(f"  Filter by Epic: {base_url}/reports/matrix?epic_filter=EP-00005")
        print(
            f"  Filter by Status: {base_url}/reports/matrix?status_filter=in_progress"
        )
        print(f"  Filter by Priority: {base_url}/reports/matrix?priority_filter=high")
        print(
            f"  Multiple filters: {base_url}/reports/matrix?status_filter=in_progress&include_tests=true"
        )


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Dynamic RTM Generation Demo Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/dynamic_rtm_demo.py --status           # Show system status
  python tools/dynamic_rtm_demo.py --demo             # Run comprehensive demo
  python tools/dynamic_rtm_demo.py --json             # Generate JSON report only
  python tools/dynamic_rtm_demo.py --markdown         # Generate Markdown report only
  python tools/dynamic_rtm_demo.py --html             # Generate HTML report only
  python tools/dynamic_rtm_demo.py --api-examples     # Show API endpoint examples
        """,
    )

    parser.add_argument("--status", action="store_true", help="Show RTM system status")
    parser.add_argument("--demo", action="store_true", help="Run comprehensive demo")
    parser.add_argument("--json", action="store_true", help="Generate JSON report only")
    parser.add_argument(
        "--markdown", action="store_true", help="Generate Markdown report only"
    )
    parser.add_argument("--html", action="store_true", help="Generate HTML report only")
    parser.add_argument(
        "--api-examples", action="store_true", help="Show API endpoint examples"
    )
    parser.add_argument("--epic-filter", type=str, help="Filter by epic ID")
    parser.add_argument("--status-filter", type=str, help="Filter by status")
    parser.add_argument("--priority-filter", type=str, help="Filter by priority")
    parser.add_argument(
        "--include-demo-data",
        action="store_true",
        help="Include demo epics (EP-DEMO-*) in the report",
    )

    args = parser.parse_args()

    demo = DynamicRTMDemo()

    # Build filters from command line args
    filters = {}
    if args.epic_filter:
        filters["epic_id"] = args.epic_filter
    if args.status_filter:
        filters["status"] = args.status_filter
    if args.priority_filter:
        filters["priority"] = args.priority_filter
    if args.include_demo_data:
        filters["include_demo_data"] = True

    if args.status:
        demo.show_system_status()
    elif args.demo:
        demo.run_comprehensive_demo()
    elif args.json:
        report = demo.generate_json_report(filters)
        if "error" in report:
            print(f"[ERROR] {report['error']}")
        else:
            # Use descriptive filename based on filters
            if any(filters.values()):
                filename = "rtm_matrix_filtered.json"
            else:
                filename = "rtm_matrix_complete.json"
            demo.save_report(report, filename)
    elif args.markdown:
        report = demo.generate_markdown_report(filters)
        if report.startswith("[ERROR]"):
            print(report)
        else:
            # Use descriptive filename based on filters
            if any(filters.values()):
                filename = "rtm_matrix_filtered.md"
            else:
                filename = "rtm_matrix_complete.md"
            demo.save_report(report, filename)
    elif args.html:
        report = demo.generate_html_report(filters)
        if "Database not available" in report:
            print("[ERROR] Database not available")
        else:
            # Use descriptive filename based on filters
            if any(filters.values()):
                filename = "rtm_matrix_filtered.html"
            else:
                filename = "rtm_matrix_complete.html"
            demo.save_report(report, filename)
    elif args.api_examples:
        demo.show_api_examples()
    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
