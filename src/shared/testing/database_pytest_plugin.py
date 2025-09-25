"""
Enhanced Pytest Plugin for Database Integration.

Extends the existing pytest integration to automatically sync test execution
results with the RTM database system.

Related Issue: US-00057 - Test execution integration with database
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import time
from datetime import datetime
from typing import Dict, Optional

import pytest

from .database_integration import (
    BDDScenarioParser,
    TestDatabaseSync,
    TestExecutionTracker,
)
from .pytest_integration import FailureTrackingPlugin


class DatabaseIntegrationPlugin:
    """Pytest plugin for automatic database integration with RTM system."""

    def __init__(self):
        """Initialize the database integration plugin."""
        self.test_tracker = TestExecutionTracker()
        self.test_sync = TestDatabaseSync()
        self.bdd_parser = BDDScenarioParser()
        self.session_start_time = None
        self.session_stats = {
            "tests_discovered": 0,
            "tests_synced": 0,
            "scenarios_linked": 0,
            "defects_created": 0,
            "execution_results_recorded": 0,
        }

    def pytest_sessionstart(self, session):
        """Initialize database integration at start of test session."""
        self.session_start_time = datetime.utcnow()
        self.test_tracker.start_test_session()

        try:
            # Sync discovered tests to database
            if (
                hasattr(session.config.option, "sync_tests")
                and session.config.option.sync_tests
            ):
                print("🔄 Syncing discovered tests to database...")
                sync_stats = self.test_sync.sync_tests_to_database()
                self.session_stats.update(
                    {
                        "tests_discovered": sync_stats["discovered"],
                        "tests_synced": sync_stats["created"] + sync_stats["updated"],
                    }
                )
                print(f"   Discovered: {sync_stats['discovered']} tests")
                print(
                    f"   Created: {sync_stats['created']}, Updated: {sync_stats['updated']}"
                )
                print(f"   Linked to Epics: {sync_stats['linked_to_epics']}")

            # Link BDD scenarios to User Stories
            if (
                hasattr(session.config.option, "link_scenarios")
                and session.config.option.link_scenarios
            ):
                print("🔗 Linking BDD scenarios to User Stories...")
                bdd_stats = self.bdd_parser.link_scenarios_to_user_stories()
                self.session_stats["scenarios_linked"] = bdd_stats["scenarios_linked"]
                print(f"   Scenarios linked: {bdd_stats['scenarios_linked']}")

        except Exception as e:
            print(f"Warning: Database sync failed: {e}")

    def pytest_runtest_logreport(self, report):
        """Record test execution results in database."""
        if report.when == "call":  # Only process call phase results
            test_id = report.nodeid
            status = self._convert_pytest_status(report.outcome)
            duration_ms = (
                getattr(report, "duration", 0) * 1000
            )  # Convert to milliseconds

            error_message = None
            if report.outcome == "failed":
                error_message = (
                    str(report.longrepr.reprcrash.message)
                    if report.longrepr and hasattr(report.longrepr, "reprcrash")
                    else "Unknown error"
                )

            # Record test result
            try:
                if self.test_tracker.record_test_result(
                    test_id, status, duration_ms, error_message
                ):
                    self.session_stats["execution_results_recorded"] += 1

                # Create defect for failures
                if report.outcome == "failed":
                    stack_trace = str(report.longrepr) if report.longrepr else ""
                    defect_id = self.test_tracker.create_defect_from_failure(
                        test_id, error_message, stack_trace
                    )
                    if defect_id:
                        self.session_stats["defects_created"] += 1
                        print(
                            f"🐛 Created defect {defect_id} for failed test: {test_id}"
                        )

            except Exception as e:
                print(f"Warning: Failed to record test result for {test_id}: {e}")

    def pytest_sessionfinish(self, session, exitstatus):
        """Finalize database integration and generate summary."""
        try:
            self.test_tracker.end_test_session()

            # Generate summary
            session_duration = (
                datetime.utcnow() - self.session_start_time
            ).total_seconds()
            print(f"\n📊 Database Integration Summary:")
            print(f"   Session duration: {session_duration:.1f}s")
            print(f"   Tests discovered: {self.session_stats['tests_discovered']}")
            print(f"   Tests synced to DB: {self.session_stats['tests_synced']}")
            print(
                f"   Execution results recorded: {self.session_stats['execution_results_recorded']}"
            )
            print(f"   BDD scenarios linked: {self.session_stats['scenarios_linked']}")
            print(f"   Defects created: {self.session_stats['defects_created']}")

            if self.session_stats["defects_created"] > 0:
                print(f"   ⚠️  New defects require attention in RTM database")

        except Exception as e:
            print(f"Warning: Error finalizing database integration: {e}")

    def _convert_pytest_status(self, outcome: str) -> str:
        """Convert pytest outcome to database test status."""
        status_mapping = {
            "passed": "passed",
            "failed": "failed",
            "skipped": "skipped",
            "error": "error",
        }
        return status_mapping.get(outcome, "unknown")


def pytest_addoption(parser):
    """Add custom command line options for database integration."""
    group = parser.getgroup("database_integration")
    group.addoption(
        "--sync-tests",
        action="store_true",
        default=False,
        help="Sync discovered tests to database before execution",
    )
    group.addoption(
        "--link-scenarios",
        action="store_true",
        default=False,
        help="Link BDD scenarios to User Stories in database",
    )
    group.addoption(
        "--auto-defects",
        action="store_true",
        default=False,
        help="Automatically create defects from test failures",
    )


def pytest_configure(config):
    """Register the database integration plugin with pytest."""
    if not hasattr(config, "_database_integration_plugin"):
        plugin = DatabaseIntegrationPlugin()
        config.pluginmanager.register(plugin, "database_integration")
        config._database_integration_plugin = plugin


# Integration with existing plugins
class EnhancedTestRunner:
    """Enhanced test runner that combines failure tracking with database integration."""

    @staticmethod
    def run_tests_with_database_sync():
        """
        Run tests with full database synchronization.

        This is a helper method for development workflow commands.
        """
        import subprocess
        import sys

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--sync-tests",
            "--link-scenarios",
            "--auto-defects",
            "-v",
        ]

        try:
            result = subprocess.run(cmd, capture_output=False, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error running tests with database sync: {e}")
            return False

    @staticmethod
    def discover_and_sync_tests_only():
        """
        Discover tests and sync to database without running them.

        Useful for initial setup or after adding new tests.
        """
        try:
            test_sync = TestDatabaseSync()
            stats = test_sync.sync_tests_to_database()

            print("📊 Test Discovery and Sync Complete:")
            print(f"   Tests discovered: {stats['discovered']}")
            print(f"   Tests created: {stats['created']}")
            print(f"   Tests updated: {stats['updated']}")
            print(f"   Tests linked to Epics: {stats['linked_to_epics']}")
            print(f"   Errors: {stats['errors']}")

            return stats["errors"] == 0

        except Exception as e:
            print(f"Error during test discovery and sync: {e}")
            return False

    @staticmethod
    def link_bdd_scenarios():
        """
        Link BDD scenarios to User Stories without running tests.

        Useful for updating scenario-to-User Story mappings.
        """
        try:
            bdd_parser = BDDScenarioParser()
            stats = bdd_parser.link_scenarios_to_user_stories()

            print("📊 BDD Scenario Linking Complete:")
            print(f"   Scenarios found: {stats['scenarios_found']}")
            print(f"   Scenarios linked: {stats['scenarios_linked']}")
            print(f"   User Stories updated: {stats['user_stories_updated']}")
            print(f"   Errors: {stats['errors']}")

            return stats["errors"] == 0

        except Exception as e:
            print(f"Error during BDD scenario linking: {e}")
            return False


# Command line interface integration
def main():
    """Command line interface for database integration utilities."""
    import argparse

    parser = argparse.ArgumentParser(
        description="RTM Database Test Integration Utilities"
    )
    parser.add_argument(
        "command",
        choices=["discover", "link-scenarios", "run-with-sync"],
        help="Command to execute",
    )

    args = parser.parse_args()
    runner = EnhancedTestRunner()

    if args.command == "discover":
        success = runner.discover_and_sync_tests_only()
    elif args.command == "link-scenarios":
        success = runner.link_bdd_scenarios()
    elif args.command == "run-with-sync":
        success = runner.run_tests_with_database_sync()
    else:
        print(f"Unknown command: {args.command}")
        success = False

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())

