#!/usr/bin/env python3
"""
CLI tool for RTM Test-Database Integration.

Provides command-line interface for managing test execution integration
with the RTM database system.

Related Issue: US-00057 - Test execution integration with database
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shared.testing.database_integration import (
    BDDScenarioParser,
    TestDatabaseSync,
    TestDiscovery,
    TestExecutionTracker,
)

# Import epic inheritance system
from epic_label_inheritance import (
    inherit_epic_labels_for_tests,
    run_comprehensive_epic_inheritance,
)

console = Console()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, verbose):
    """RTM Test-Database Integration CLI - Manage test execution integration."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    if verbose:
        console.print(
            "[blue]RTM Test-Database Integration CLI - Verbose mode enabled[/blue]"
        )


@cli.group()
def discover():
    """Test discovery and database synchronization."""
    pass


@discover.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be discovered without database changes",
)
@click.pass_context
def tests(ctx, dry_run):
    """Discover all test files and sync to database."""
    discovery = TestDiscovery()

    try:
        with console.status("[bold green]Discovering tests..."):
            discovered_tests = discovery.discover_tests()

        console.print(f"[green]Discovered {len(discovered_tests)} tests[/green]")

        if ctx.obj["verbose"] or dry_run:
            # Show breakdown by test type
            test_types = {}
            for test in discovered_tests:
                test_type = test["test_type"]
                test_types[test_type] = test_types.get(test_type, 0) + 1

            table = Table(title="Test Discovery Summary")
            table.add_column("Test Type", style="cyan")
            table.add_column("Count", style="white")

            for test_type, count in test_types.items():
                table.add_row(test_type, str(count))

            console.print(table)

        if not dry_run:
            with console.status("[bold green]Syncing to database..."):
                sync = TestDatabaseSync()
                stats = sync.sync_tests_to_database()

            console.print("[green]Sync completed![/green]")
            console.print(f"Created: {stats['created']}, Updated: {stats['updated']}")
            console.print(f"Linked to Epics: {stats['linked_to_epics']}")

            if stats["errors"] > 0:
                console.print(f"[yellow]Errors: {stats['errors']}[/yellow]")

    except Exception as e:
        console.print(f"[red]Discovery failed: {e}[/red]")
        if ctx.obj["verbose"]:
            import traceback

            console.print(traceback.format_exc())


@discover.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show epic inheritance analysis without database changes",
)
@click.option(
    "--entity-type",
    type=click.Choice(["tests", "user-stories", "defects", "all"]),
    default="all",
    help="Which entity types to process for epic inheritance",
)
@click.pass_context
def epics(ctx, dry_run, entity_type):
    """Discover and apply epic inheritance for all test types and entities."""
    try:
        with console.status(
            f"[bold green]Processing epic inheritance for {entity_type}..."
        ):
            if entity_type == "all":
                results = run_comprehensive_epic_inheritance(dry_run=dry_run)
            else:
                # Import database session for specific entity types
                from be.database import SessionLocal

                session = SessionLocal()
                try:
                    if entity_type == "tests":
                        results = {
                            "test_stats": inherit_epic_labels_for_tests(
                                session, dry_run
                            )
                        }
                    elif entity_type == "user-stories":
                        from epic_label_inheritance import (
                            inherit_epic_labels_for_user_stories,
                        )

                        results = {
                            "user_story_stats": inherit_epic_labels_for_user_stories(
                                session, dry_run
                            )
                        }
                    elif entity_type == "defects":
                        from epic_label_inheritance import (
                            inherit_epic_labels_for_defects,
                        )

                        results = {
                            "defect_stats": inherit_epic_labels_for_defects(
                                session, dry_run
                            )
                        }

                    if not dry_run:
                        session.commit()
                    else:
                        session.rollback()

                    results["success"] = True
                except Exception as e:
                    session.rollback()
                    raise e
                finally:
                    session.close()

        # Display results in a formatted table
        console.print("[green]Epic inheritance processing completed![/green]")

        # User Stories results
        if "user_story_stats" in results:
            us_stats = results["user_story_stats"]
            table = Table(title="User Story Epic Inheritance")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            table.add_row(
                "Total User Stories", str(us_stats.get("total_user_stories", 0))
            )
            table.add_row("Processed", str(us_stats.get("user_stories_processed", 0)))
            table.add_row("Labels Added", str(us_stats.get("labels_added", 0)))
            table.add_row("GitHub Updates", str(us_stats.get("github_updates", 0)))
            console.print(table)

        # Defects results
        if "defect_stats" in results:
            defect_stats = results["defect_stats"]
            table = Table(title="Defect Epic Inheritance")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            table.add_row("Total Defects", str(defect_stats.get("total_defects", 0)))
            table.add_row("Processed", str(defect_stats.get("defects_processed", 0)))
            table.add_row("Labels Added", str(defect_stats.get("labels_added", 0)))
            table.add_row("GitHub Updates", str(defect_stats.get("github_updates", 0)))
            console.print(table)

        # Tests results
        if "test_stats" in results:
            test_stats = results["test_stats"]
            table = Table(title="Test Epic Inheritance")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            table.add_row("Total Tests", str(test_stats.get("total_tests", 0)))
            table.add_row("With Epic Links", str(test_stats.get("tests_with_epics", 0)))
            table.add_row(
                "Without Epic Links", str(test_stats.get("tests_without_epics", 0))
            )
            table.add_row("Database Updates", str(test_stats.get("tests_processed", 0)))

            # Show inheritance sources
            if test_stats.get("inheritance_sources"):
                console.print("\n[bold]Inheritance Sources:[/bold]")
                for source, count in test_stats["inheritance_sources"].items():
                    console.print(f"  • {source}: {count}")

            console.print(table)

        # Summary
        if "summary" in results:
            summary = results["summary"]
            console.print("\n[bold green]Summary:[/bold green]")
            console.print(
                f"  Total Entities Processed: {summary.get('total_entities_processed', 0)}"
            )
            console.print(
                f"  Total Labels Added: {summary.get('total_labels_added', 0)}"
            )
            console.print(
                f"  Total GitHub Updates: {summary.get('total_github_updates', 0)}"
            )
            console.print(f"  Total Errors: {summary.get('total_errors', 0)}")

        if dry_run:
            console.print("\n[yellow]DRY RUN - No changes were applied[/yellow]")
        else:
            console.print("\n[green]Changes have been applied successfully![/green]")

    except Exception as e:
        console.print(f"[red]Epic inheritance processing failed: {e}[/red]")
        if ctx.obj["verbose"]:
            import traceback

            console.print(traceback.format_exc())


@discover.command()
@click.option(
    "--dry-run", is_flag=True, help="Show what would be linked without database changes"
)
@click.pass_context
def scenarios(ctx, dry_run):
    """Discover BDD scenarios and link to User Stories."""
    bdd_parser = BDDScenarioParser()

    try:
        with console.status("[bold green]Parsing BDD scenarios..."):
            scenarios = bdd_parser.parse_feature_files()

        console.print(f"[green]Found {len(scenarios)} BDD scenarios[/green]")

        if ctx.obj["verbose"] or dry_run:
            # Show scenarios with User Story references
            table = Table(title="BDD Scenarios Found")
            table.add_column("Feature File", style="cyan")
            table.add_column("Scenario", style="white")
            table.add_column("User Story Refs", style="yellow")

            for scenario in scenarios[:10]:  # Show first 10
                us_refs = ", ".join(scenario["user_story_references"]) or "None"
                table.add_row(
                    Path(scenario["feature_file"]).name,
                    (
                        scenario["scenario_name"][:40] + "..."
                        if len(scenario["scenario_name"]) > 40
                        else scenario["scenario_name"]
                    ),
                    us_refs,
                )

            if len(scenarios) > 10:
                table.add_row("...", f"+ {len(scenarios) - 10} more scenarios", "...")

            console.print(table)

        if not dry_run:
            with console.status("[bold green]Linking to User Stories..."):
                stats = bdd_parser.link_scenarios_to_user_stories()

            console.print("[green]Linking completed![/green]")
            console.print(f"Scenarios linked: {stats['scenarios_linked']}")
            console.print(f"User Stories updated: {stats['user_stories_updated']}")

            if stats["errors"] > 0:
                console.print(f"[yellow]Errors: {stats['errors']}[/yellow]")

    except Exception as e:
        console.print(f"[red]BDD scenario linking failed: {e}[/red]")
        if ctx.obj["verbose"]:
            import traceback

            console.print(traceback.format_exc())


@cli.group()
def run():
    """Enhanced test execution with database integration."""
    pass


@run.command()
@click.option("--sync-tests", is_flag=True, help="Sync discovered tests before running")
@click.option(
    "--link-scenarios", is_flag=True, help="Link BDD scenarios before running"
)
@click.option("--auto-defects", is_flag=True, help="Auto-create defects from failures")
@click.option(
    "--test-type", help="Run specific test type (unit, integration, e2e, security)"
)
@click.pass_context
def tests(ctx, sync_tests, link_scenarios, auto_defects, test_type):
    """Run tests with database integration."""
    import subprocess

    # Handle database integration before running tests
    if sync_tests:
        console.print("[blue]Syncing discovered tests to database...[/blue]")
        try:
            sync = TestDatabaseSync()
            stats = sync.sync_tests_to_database()
            console.print(
                f"[green]Synced {stats['created'] + stats['updated']} tests[/green]"
            )
        except Exception as e:
            console.print(f"[yellow]Warning: Test sync failed: {e}[/yellow]")

    if link_scenarios:
        console.print("[blue]Linking BDD scenarios to User Stories...[/blue]")
        try:
            bdd_parser = BDDScenarioParser()
            stats = bdd_parser.link_scenarios_to_user_stories()
            console.print(
                f"[green]Linked {stats['scenarios_linked']} scenarios[/green]"
            )
        except Exception as e:
            console.print(f"[yellow]Warning: Scenario linking failed: {e}[/yellow]")

    # Build pytest command without problematic flags
    cmd = [sys.executable, "-m", "pytest"]

    if test_type:
        cmd.append(f"tests/{test_type}/")
    else:
        cmd.append("tests/")

    cmd.extend(["-v"])

    if ctx.obj["verbose"]:
        console.print(f"[blue]Running command: {' '.join(cmd)}[/blue]")

    try:
        result = subprocess.run(cmd, cwd=Path.cwd())

        # Update test execution results based on pytest outcome
        console.print("[blue]Updating test execution results in database...[/blue]")
        try:
            tracker = TestExecutionTracker()
            tracker.start_test_session()

            from be.database import get_db_session
            from be.models.traceability import Test
            from datetime import datetime

            db = get_db_session()
            test_query = db.query(Test)
            if test_type:
                # Filter by test type if specified - handle both Windows and Unix paths
                from sqlalchemy import or_

                test_query = test_query.filter(
                    or_(
                        Test.test_file_path.like(f"tests/{test_type}/%"),
                        Test.test_file_path.like(f"tests\\{test_type}\\%"),
                    )
                )

            tests_to_update = test_query.all()
            updated_count = 0
            current_time = datetime.utcnow()

            console.print(f"[blue]Found {len(tests_to_update)} tests to update[/blue]")

            for test in tests_to_update:
                try:
                    # Update execution status based on overall pytest result
                    # For a more detailed implementation, we would parse pytest output
                    # to get individual test results, but this provides basic tracking
                    if result.returncode == 0:
                        # All tests passed
                        test.update_execution_result("passed", duration_ms=50.0)
                        status = "passed"
                    else:
                        # Some tests failed - mark as failed for conservatism
                        # In practice, some tests in this batch may have passed
                        test.update_execution_result("failed", duration_ms=50.0)
                        status = "failed"

                    # Ensure last_execution_time is updated
                    test.last_execution_time = current_time
                    updated_count += 1

                    if updated_count <= 3:  # Show first few updates for debugging
                        console.print(
                            f"[dim]Updated {test.test_function_name}: {status}[/dim]"
                        )

                except Exception as test_error:
                    console.print(
                        f"[yellow]Error updating test {test.test_function_name}: {test_error}[/yellow]"
                    )

            # Commit the transaction
            console.print(f"[blue]Committing {updated_count} test updates...[/blue]")
            db.commit()

            # Verify the updates
            verification_query = db.query(Test).filter(
                Test.last_execution_time.isnot(None)
            )
            if test_type:
                verification_query = verification_query.filter(
                    or_(
                        Test.test_file_path.like(f"tests/{test_type}/%"),
                        Test.test_file_path.like(f"tests\\{test_type}\\%"),
                    )
                )
            verified_count = verification_query.count()

            db.close()
            tracker.end_test_session()

            console.print(
                f"[green]Updated execution status for {updated_count} tests[/green]"
            )
            console.print(
                f"[green]Verified {verified_count} tests with execution data[/green]"
            )

            if result.returncode == 0:
                console.print("[green]All tests marked as PASSED[/green]")
            else:
                console.print(
                    "[yellow]Tests marked as FAILED due to pytest failures[/yellow]"
                )

        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not update test execution results: {e}[/yellow]"
            )
            import traceback

            console.print(f"[red]Full error: {traceback.format_exc()}[/red]")

        # Handle auto-defects after test execution if needed
        if auto_defects and result.returncode != 0:
            console.print("[blue]Auto-defects not yet implemented in CLI mode[/blue]")
            console.print(
                "[blue]Use direct pytest for now, or implement defect creation here[/blue]"
            )

        if result.returncode == 0:
            console.print(
                "[green]Tests completed successfully with database integration[/green]"
            )
        else:
            console.print("[yellow]Tests completed with some failures[/yellow]")

        return result.returncode

    except Exception as e:
        console.print(f"[red]Test execution failed: {e}[/red]")
        return 1


@cli.group()
def status():
    """Check test-database integration status."""
    pass


@status.command()
@click.pass_context
def overview(ctx):
    """Show overall test-database integration status."""
    from be.database import get_db_session
    from be.models.traceability import Defect, Test

    try:
        db = get_db_session()

        # Get statistics
        total_tests = db.query(Test).count()
        bdd_tests = db.query(Test).filter(Test.test_type == "bdd").count()
        tests_with_epics = db.query(Test).filter(Test.epic_id.isnot(None)).count()
        test_failures = (
            db.query(Test).filter(Test.last_execution_status == "failed").count()
        )

        # Recent defects from test failures
        test_defects = (
            db.query(Defect).filter(Defect.defect_type == "test_failure").count()
        )

        db.close()

        # Display status
        table = Table(title="Test-Database Integration Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Status", style="green")

        table.add_row(
            "Total Tests in Database",
            str(total_tests),
            "OK" if total_tests > 0 else "WARN",
        )
        table.add_row(
            "BDD Scenarios Tracked", str(bdd_tests), "OK" if bdd_tests > 0 else "WARN"
        )
        table.add_row(
            "Tests Linked to Epics",
            str(tests_with_epics),
            "OK" if tests_with_epics > 0 else "WARN",
        )
        table.add_row(
            "Recent Test Failures",
            str(test_failures),
            "WARN" if test_failures > 0 else "OK",
        )
        table.add_row(
            "Defects from Test Failures",
            str(test_defects),
            "WARN" if test_defects > 0 else "OK",
        )

        console.print(table)

        # Integration health
        if total_tests == 0:
            console.print(
                "[yellow]Warning: No tests found in database. Run 'discover tests' first.[/yellow]"
            )
        elif tests_with_epics == 0:
            console.print(
                "[yellow]Warning: No tests linked to Epics. Check Epic references in test files.[/yellow]"
            )
        else:
            coverage_pct = (tests_with_epics / total_tests) * 100
            console.print(
                f"[green]Integration Health: {coverage_pct:.1f}% of tests linked to requirements[/green]"
            )

    except Exception as e:
        console.print(f"[red]Status check failed: {e}[/red]")


@cli.group()
def utils():
    """Utility commands for test-database integration."""
    pass


@utils.command()
@click.option(
    "--show-epic-refs", is_flag=True, help="Show Epic references found in tests"
)
@click.option("--show-orphaned", is_flag=True, help="Show tests not linked to any Epic")
@click.pass_context
def analyze(ctx, show_epic_refs, show_orphaned):
    """Analyze test-database integration patterns."""
    discovery = TestDiscovery()

    try:
        discovered_tests = discovery.discover_tests()

        if show_epic_refs:
            console.print("\n[bold cyan]Epic References Found in Tests:[/bold cyan]")
            epic_refs = {}
            for test in discovered_tests:
                for epic_ref in test["epic_references"]:
                    if epic_ref not in epic_refs:
                        epic_refs[epic_ref] = []
                    epic_refs[epic_ref].append(
                        f"{test['test_file_path']}::{test['test_function_name']}"
                    )

            for epic_id, tests in epic_refs.items():
                console.print(f"[yellow]{epic_id}[/yellow]: {len(tests)} tests")
                if ctx.obj["verbose"]:
                    for test in tests[:3]:  # Show first 3
                        console.print(f"  - {test}")
                    if len(tests) > 3:
                        console.print(f"  ... and {len(tests) - 3} more")

        if show_orphaned:
            console.print("\n[bold cyan]Tests Without Epic References:[/bold cyan]")
            orphaned = [
                test for test in discovered_tests if not test["epic_references"]
            ]
            console.print(f"Found {len(orphaned)} tests without Epic references")

            if ctx.obj["verbose"] and orphaned:
                for test in orphaned[:10]:  # Show first 10
                    console.print(
                        f"  - {test['test_file_path']}::{test['test_function_name']}"
                    )
                if len(orphaned) > 10:
                    console.print(f"  ... and {len(orphaned) - 10} more")

    except Exception as e:
        console.print(f"[red]Analysis failed: {e}[/red]")


if __name__ == "__main__":
    cli()
