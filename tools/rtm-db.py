#!/usr/bin/env python3
"""
CLI tool for database RTM (Requirements Traceability Matrix) management.

Provides comprehensive command-line interface for managing traceability data
in the hybrid GitHub + Database RTM architecture.

Related Issue: US-00055 - CLI tools for database RTM management
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Architecture Decision: ADR-003 - Hybrid GitHub + Database RTM Architecture
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.progress import track
from rich.table import Table
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from be.database import get_db_session
from be.models.traceability import Defect, Epic, GitHubSync, Test, UserStory
from be.services.rtm_parser import RTMDataMigrator

console = Console()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--database-url", help="Override database URL")
@click.pass_context
def cli(ctx, verbose, database_url):
    """RTM Database Management CLI - Manage traceability data with command-line tools."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["database_url"] = database_url

    if verbose:
        console.print("[blue]RTM Database CLI - Verbose mode enabled[/blue]")


# Entity CRUD Commands Group
@cli.group()
def entities():
    """Manage RTM entities (Epics, User Stories, Tests, Defects)."""
    pass


@entities.command()
@click.option("--epic-id", required=True, help="Epic ID (e.g., EP-00005)")
@click.option("--title", required=True, help="Epic title")
@click.option("--description", help="Epic description")
@click.option("--business-value", help="Business value statement")
@click.option(
    "--priority", default="medium", help="Priority: critical, high, medium, low"
)
@click.option(
    "--status",
    default="planned",
    help="Status: planned, in_progress, completed, blocked",
)
@click.pass_context
def create_epic(ctx, epic_id, title, description, business_value, priority, status):
    """Create a new Epic."""
    db = get_db_session()
    try:
        # Check if epic already exists
        existing = db.query(Epic).filter(Epic.epic_id == epic_id).first()
        if existing:
            click.echo(f"Epic {epic_id} already exists")
            return

        epic = Epic(
            epic_id=epic_id,
            title=title,
            description=description,
            business_value=business_value,
            priority=priority,
            status=status,
        )
        db.add(epic)
        db.commit()

        click.echo(f"Created Epic {epic_id}")
        if ctx.obj["verbose"]:
            click.echo(f"Priority: {priority}, Status: {status}")

    except IntegrityError as e:
        db.rollback()
        click.echo(f"Database error: {e}")
    finally:
        db.close()


@entities.command()
@click.option("--user-story-id", required=True, help="User Story ID (e.g., US-00055)")
@click.option("--epic-id", required=True, help="Parent Epic ID (e.g., EP-00005)")
@click.option("--github-issue", type=int, required=True, help="GitHub issue number")
@click.option("--title", required=True, help="User Story title")
@click.option("--description", help="User Story description")
@click.option("--story-points", type=int, default=0, help="Story points estimate")
@click.option(
    "--priority", default="medium", help="Priority: critical, high, medium, low"
)
@click.pass_context
def create_user_story(
    ctx,
    user_story_id,
    epic_id,
    github_issue,
    title,
    description,
    story_points,
    priority,
):
    """Create a new User Story."""
    db = get_db_session()
    try:
        # Find parent epic
        epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
        if not epic:
            click.echo(f"Epic {epic_id} not found")
            return

        # Check if user story already exists
        existing = (
            db.query(UserStory).filter(UserStory.user_story_id == user_story_id).first()
        )
        if existing:
            click.echo(f"User Story {user_story_id} already exists")
            return

        user_story = UserStory(
            user_story_id=user_story_id,
            epic_id=epic.id,
            github_issue_number=github_issue,
            title=title,
            description=description,
            story_points=story_points,
            priority=priority,
        )
        db.add(user_story)
        db.commit()

        click.echo(f"Created User Story {user_story_id}")
        if ctx.obj["verbose"]:
            click.echo(f"Epic: {epic_id}, GitHub Issue: #{github_issue}, Points: {story_points}")

    except IntegrityError as e:
        db.rollback()
        click.echo(f"Database error: {e}")
    finally:
        db.close()


@entities.command()
@click.option(
    "--test-type",
    required=True,
    help="Test type: unit, integration, e2e, security, bdd",
)
@click.option("--test-file", required=True, help="Test file path")
@click.option("--title", required=True, help="Test title")
@click.option("--epic-id", help="Optional Epic ID to link to")
@click.option("--function-name", help="Test function name")
@click.option("--bdd-scenario", help="BDD scenario name")
@click.pass_context
def create_test(ctx, test_type, test_file, title, epic_id, function_name, bdd_scenario):
    """Create a new Test record."""
    db = get_db_session()
    try:
        epic_db_id = None
        if epic_id:
            epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
            if epic:
                epic_db_id = epic.id
            else:
                click.echo(f"Warning: Epic {epic_id} not found")

        test = Test(
            test_type=test_type,
            test_file_path=test_file,
            title=title,
            epic_id=epic_db_id,
            test_function_name=function_name,
            bdd_scenario_name=bdd_scenario,
        )
        db.add(test)
        db.commit()

        click.echo(f"Created Test: {title}")
        if ctx.obj["verbose"]:
            click.echo(f"Type: {test_type}, File: {test_file}")

    except IntegrityError as e:
        db.rollback()
        click.echo(f"Database error: {e}")
    finally:
        db.close()


# Query and Reporting Commands Group
@cli.group()
def query():
    """Query and report on RTM data."""
    pass


@query.command()
@click.option("--format", default="table", help="Output format: table, json")
@click.option("--status", help="Filter by status")
@click.option("--priority", help="Filter by priority")
@click.pass_context
def epics(ctx, format, status, priority):
    """List all Epics with optional filtering."""
    db = get_db_session()
    try:
        query_obj = db.query(Epic)

        if status:
            query_obj = query_obj.filter(Epic.status == status)
        if priority:
            query_obj = query_obj.filter(Epic.priority == priority)

        epics_list = query_obj.all()

        if format == "json":
            data = [epic.to_dict() for epic in epics_list]
            click.echo(json.dumps(data, indent=2, default=str))
        else:
            table = Table(title="RTM Epics")
            table.add_column("Epic ID", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Status", style="green")
            table.add_column("Priority", style="yellow")
            table.add_column("Completion %", style="blue")

            for epic in epics_list:
                table.add_row(
                    epic.epic_id,
                    epic.title[:50] + "..." if len(epic.title) > 50 else epic.title,
                    epic.status,
                    epic.priority,
                    f"{epic.completion_percentage or 0:.1f}%",
                )

            console.print(table)
            console.print(f"\n[blue]Total Epics: {len(epics_list)}[/blue]")

    finally:
        db.close()


@query.command()
@click.option("--epic-id", help="Filter by Epic ID")
@click.option("--status", help="Filter by implementation status")
@click.option("--format", default="table", help="Output format: table, json")
@click.pass_context
def user_stories(ctx, epic_id, status, format):
    """List User Stories with optional filtering."""
    db = get_db_session()
    try:
        query_obj = db.query(UserStory)

        if epic_id:
            epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
            if epic:
                query_obj = query_obj.filter(UserStory.epic_id == epic.id)
            else:
                click.echo(f"Epic {epic_id} not found")
                return

        if status:
            query_obj = query_obj.filter(UserStory.implementation_status == status)

        user_stories_list = query_obj.all()

        if format == "json":
            data = [us.to_dict() for us in user_stories_list]
            click.echo(json.dumps(data, indent=2, default=str))
        else:
            table = Table(title="RTM User Stories")
            table.add_column("US ID", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Epic", style="magenta")
            table.add_column("Status", style="green")
            table.add_column("Points", style="yellow")
            table.add_column("GitHub #", style="blue")

            for us in user_stories_list:
                epic_name = "N/A"
                if us.epic_id:
                    epic = db.query(Epic).filter(Epic.id == us.epic_id).first()
                    if epic:
                        epic_name = epic.epic_id

                table.add_row(
                    us.user_story_id,
                    us.title[:40] + "..." if len(us.title) > 40 else us.title,
                    epic_name,
                    us.implementation_status,
                    str(us.story_points),
                    f"#{us.github_issue_number}" if us.github_issue_number else "N/A",
                )

            console.print(table)
            console.print(
                f"\n[blue]Total User Stories: {len(user_stories_list)}[/blue]"
            )

    finally:
        db.close()


@query.command()
@click.argument("epic_id")
@click.option("--format", default="table", help="Output format: table, json")
@click.pass_context
def epic_progress(ctx, epic_id, format):
    """Show detailed progress for a specific Epic."""
    db = get_db_session()
    try:
        epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
        if not epic:
            click.echo(f"Epic {epic_id} not found")
            return

        user_stories = db.query(UserStory).filter(UserStory.epic_id == epic.id).all()
        tests = db.query(Test).filter(Test.epic_id == epic.id).all()
        defects = db.query(Defect).filter(Defect.epic_id == epic.id).all()

        # Calculate metrics
        total_story_points = sum(us.story_points for us in user_stories)
        completed_story_points = sum(
            us.story_points
            for us in user_stories
            if us.implementation_status in ["done", "completed"]
        )

        test_pass_rate = 0.0
        if tests:
            passed_tests = sum(
                1 for test in tests if test.last_execution_status == "passed"
            )
            test_pass_rate = (passed_tests / len(tests)) * 100

        critical_defects = sum(1 for defect in defects if defect.severity == "critical")
        open_defects = sum(
            1 for defect in defects if defect.status in ["open", "in_progress"]
        )

        if format == "json":
            data = {
                "epic": epic.to_dict(),
                "metrics": {
                    "total_story_points": total_story_points,
                    "completed_story_points": completed_story_points,
                    "completion_percentage": (
                        (completed_story_points / total_story_points * 100)
                        if total_story_points > 0
                        else 0
                    ),
                    "user_stories_count": len(user_stories),
                    "tests_count": len(tests),
                    "test_pass_rate": test_pass_rate,
                    "defects_count": len(defects),
                    "critical_defects": critical_defects,
                    "open_defects": open_defects,
                },
            }
            click.echo(json.dumps(data, indent=2, default=str))
        else:
            click.echo(f"\nEpic Progress Report: {epic_id}")
            click.echo(f"Title: {epic.title}")
            click.echo(f"Status: {epic.status}")
            click.echo(f"Priority: {epic.priority}\n")

            # Progress metrics table
            metrics_table = Table(title="Progress Metrics")
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="white")

            completion_pct = (
                (completed_story_points / total_story_points * 100)
                if total_story_points > 0
                else 0
            )
            metrics_table.add_row(
                "Story Points",
                f"{completed_story_points}/{total_story_points} ({completion_pct:.1f}%)",
            )
            metrics_table.add_row("User Stories", str(len(user_stories)))
            metrics_table.add_row(
                "Tests", f"{len(tests)} (pass rate: {test_pass_rate:.1f}%)"
            )
            metrics_table.add_row(
                "Defects",
                f"{len(defects)} ({critical_defects} critical, {open_defects} open)",
            )

            console.print(metrics_table)

    finally:
        db.close()


# Data Management Commands Group
@cli.group()
def data():
    """Data import, export, and migration operations."""
    pass


@data.command()
@click.argument("file_path")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be imported without making changes"
)
@click.pass_context
def import_rtm(ctx, file_path, dry_run):
    """Import RTM data from markdown file."""
    if not Path(file_path).exists():
        console.print(f"[red]Error: File {file_path} not found[/red]")
        return

    if dry_run:
        console.print(f"[yellow]DRY RUN: Would import from {file_path}[/yellow]")
        # TODO: Implement dry-run parsing preview
        return

    try:
        migrator = RTMDataMigrator()

        with console.status("[bold green]Importing RTM data..."):
            results = migrator.migrate_from_file(file_path)

        console.print(f"[green]Import completed successfully![/green]")
        console.print(f"Epics: {results['epics']}")
        console.print(f"User Stories: {results['user_stories']}")
        console.print(f"Tests: {results['tests']}")
        console.print(f"Defects: {results['defects']}")

    except Exception as e:
        console.print(f"[red]Import failed: {e}[/red]")
        if ctx.obj["verbose"]:
            import traceback

            console.print(traceback.format_exc())


@data.command()
@click.option("--output", default="rtm_export.json", help="Output file path")
@click.option("--format", default="json", help="Export format: json, markdown")
@click.option("--include-tests", is_flag=True, help="Include test data in export")
@click.pass_context
def export(ctx, output, format, include_tests):
    """Export RTM data to file."""
    db = get_db_session()
    try:
        data = {
            "epics": [epic.to_dict() for epic in db.query(Epic).all()],
            "user_stories": [us.to_dict() for us in db.query(UserStory).all()],
            "defects": [defect.to_dict() for defect in db.query(Defect).all()],
            "export_timestamp": datetime.utcnow().isoformat(),
        }

        if include_tests:
            data["tests"] = [test.to_dict() for test in db.query(Test).all()]

        if format == "json":
            with open(output, "w") as f:
                json.dump(data, f, indent=2, default=str)
        elif format == "markdown":
            # TODO: Implement markdown export format
            click.echo("Markdown export not yet implemented")
            return

        click.echo(f"Exported RTM data to {output}")
        if ctx.obj["verbose"]:
            click.echo(f"Exported {len(data['epics'])} epics, {len(data['user_stories'])} user stories")

    finally:
        db.close()


# Database Administration Commands Group
@cli.group()
def admin():
    """Database administration and maintenance."""
    pass


@admin.command()
@click.pass_context
def health_check(ctx):
    """Check database health and connectivity."""
    try:
        db = get_db_session()

        # Test basic connectivity
        epic_count = db.query(Epic).count()
        us_count = db.query(UserStory).count()
        test_count = db.query(Test).count()
        defect_count = db.query(Defect).count()
        sync_count = db.query(GitHubSync).count()

        click.echo("Database connection successful")

        # Health metrics table
        health_table = Table(title="Database Health Status")
        health_table.add_column("Entity", style="cyan")
        health_table.add_column("Count", style="white")

        health_table.add_row("Epics", str(epic_count))
        health_table.add_row("User Stories", str(us_count))
        health_table.add_row("Tests", str(test_count))
        health_table.add_row("Defects", str(defect_count))
        health_table.add_row("GitHub Sync Records", str(sync_count))

        console.print(health_table)

        # Check for orphaned records
        orphaned_us = db.query(UserStory).filter(UserStory.epic_id.is_(None)).count()
        orphaned_tests = db.query(Test).filter(Test.epic_id.is_(None)).count()

        if orphaned_us > 0 or orphaned_tests > 0:
            console.print(f"\n[yellow]Warning: Found orphaned records:[/yellow]")
            console.print(f"User Stories without Epic: {orphaned_us}")
            console.print(f"Tests without Epic: {orphaned_tests}")

        db.close()

    except Exception as e:
        console.print(f"[red]Database health check failed: {e}[/red]")


@admin.command()
@click.option("--fix", is_flag=True, help="Automatically fix issues")
@click.pass_context
def validate(ctx, fix):
    """Validate data integrity and relationships."""
    db = get_db_session()
    issues = []

    try:
        # Check for missing Epic references
        orphaned_us = db.query(UserStory).filter(UserStory.epic_id.is_(None)).all()
        if orphaned_us:
            issues.append(
                f"Found {len(orphaned_us)} User Stories without Epic reference"
            )

        # Check for invalid GitHub issue numbers
        invalid_gh_issues = (
            db.query(UserStory).filter(UserStory.github_issue_number.is_(None)).all()
        )
        if invalid_gh_issues:
            issues.append(
                f"Found {len(invalid_gh_issues)} User Stories without GitHub issue number"
            )

        # Check for duplicate entity IDs
        epic_ids = [epic.epic_id for epic in db.query(Epic).all()]
        if len(epic_ids) != len(set(epic_ids)):
            issues.append("Found duplicate Epic IDs")

        us_ids = [us.user_story_id for us in db.query(UserStory).all()]
        if len(us_ids) != len(set(us_ids)):
            issues.append("Found duplicate User Story IDs")

        if issues:
            console.print(f"[red]Found {len(issues)} validation issues:[/red]")
            for issue in issues:
                console.print(f"  - {issue}")

            if fix:
                console.print("\n[yellow]Auto-fix not yet implemented[/yellow]")
        else:
            console.print("[green]All validation checks passed[/green]")

    finally:
        db.close()


@admin.command()
@click.option("--confirm", is_flag=True, help="Confirm deletion of all data")
@click.pass_context
def reset(ctx, confirm):
    """Reset database (delete all RTM data)."""
    if not confirm:
        console.print(
            "[red]This will delete ALL RTM data. Use --confirm to proceed.[/red]"
        )
        return

    db = get_db_session()
    try:
        # Delete in order to respect foreign key constraints
        db.query(GitHubSync).delete()
        db.query(Test).delete()
        db.query(Defect).delete()
        db.query(UserStory).delete()
        db.query(Epic).delete()
        db.commit()

        console.print("[green]Database reset completed[/green]")

    except Exception as e:
        db.rollback()
        console.print(f"[red]Reset failed: {e}[/red]")
    finally:
        db.close()


# GitHub Integration Commands Group
@cli.group()
def github():
    """GitHub integration and synchronization."""
    pass


@github.command()
@click.option("--issue-number", type=int, help="Sync specific issue number")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be synced without making changes"
)
@click.pass_context
def sync(ctx, issue_number, dry_run):
    """Sync database with GitHub issues."""
    # TODO: Implement GitHub sync functionality
    # This would integrate with the GitHub Actions workflow logic
    console.print(
        "[yellow]GitHub sync not yet implemented - use GitHub Actions workflow[/yellow]"
    )


@github.command()
@click.pass_context
def sync_status(ctx):
    """Show GitHub synchronization status."""
    db = get_db_session()
    try:
        recent_syncs = (
            db.query(GitHubSync)
            .order_by(GitHubSync.last_sync_time.desc())
            .limit(10)
            .all()
        )

        if not recent_syncs:
            console.print("[yellow]No sync records found[/yellow]")
            return

        table = Table(title="Recent GitHub Sync Status")
        table.add_column("Issue #", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Last Sync", style="green")
        table.add_column("Errors", style="red")

        for sync in recent_syncs:
            status_color = "green" if sync.sync_status == "completed" else "red"
            table.add_row(
                str(sync.github_issue_number),
                f"[{status_color}]{sync.sync_status}[/{status_color}]",
                (
                    sync.last_sync_time.strftime("%Y-%m-%d %H:%M:%S")
                    if sync.last_sync_time
                    else "N/A"
                ),
                (
                    sync.sync_errors[:50] + "..."
                    if sync.sync_errors and len(sync.sync_errors) > 50
                    else sync.sync_errors or "None"
                ),
            )

        console.print(table)

    finally:
        db.close()


if __name__ == "__main__":
    cli()
