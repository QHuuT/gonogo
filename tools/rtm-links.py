#!/usr/bin/env python3
"""
RTM (Requirements Traceability Matrix) Automation Tool - LEGACY VERSION

⚠️ DEPRECATION NOTICE (2025-09-22): This tool works with the old file-based RTM system.
   The project has migrated to a database-driven RTM system.

🚀 Use the new database RTM tools instead:
   - python tools/rtm-db.py (database management)
   - python tools/github_sync_manager.py (GitHub sync)
   - Web dashboard: http://localhost:8000/api/rtm/reports/matrix?format=html

Related Issue: US-00015 - Automated RTM link generation and validation
Epic: EP-00005 - RTM Automation
Migration: US-00060 - Complete migration to database RTM

Legacy Usage (for reference only):
    python tools/rtm-links.py validate docs/traceability/requirements-matrix.md
    python tools/rtm-links.py update docs/traceability/requirements-matrix.md --dry-run
    python tools/rtm-links.py generate-link EP-00001 --bold
"""

import os
import sys
from pathlib import Path
from typing import Optional

import click

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shared.utils.rtm_link_generator import RTMLinkGenerator


@click.group()
@click.option(
    "-c", "--config", "config_path", help="Path to RTM automation configuration file"
)
@click.option("-f", "--rtm-file", "rtm_file", help="Path to RTM file")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, config_path: Optional[str], rtm_file: Optional[str], verbose: bool):
    """RTM (Requirements Traceability Matrix) automation tool."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config_path
    ctx.obj["rtm_file"] = rtm_file or "docs/traceability/requirements-matrix.md"
    ctx.obj["verbose"] = verbose
    ctx.obj["generator"] = RTMLinkGenerator(config_path)


@cli.command()
@click.argument("rtm_file_path", required=False)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.option("--output", "-o", help="Output file path (default: stdout)")
@click.pass_context
def validate(
    ctx, rtm_file_path: Optional[str], output_format: str, output: Optional[str]
):
    """Validate RTM links."""
    generator = ctx.obj["generator"]
    rtm_path = rtm_file_path or ctx.obj["rtm_file"]

    if not os.path.exists(rtm_path):
        click.echo(f"Error: RTM file not found: {rtm_path}", err=True)
        sys.exit(1)

    if ctx.obj["verbose"]:
        click.echo(f"Validating RTM file: {rtm_path}")

    result = generator.validate_rtm_links(rtm_path)

    if output_format == "json":
        import json

        output_data = {
            "total_links": result.total_links,
            "valid_links": result.valid_links,
            "invalid_links": [
                {
                    "text": link.text,
                    "url": link.url,
                    "type": link.type,
                    "error_message": link.error_message,
                }
                for link in result.invalid_links
            ],
            "errors": result.errors,
            "warnings": result.warnings,
            "health_score": (
                (result.valid_links / result.total_links * 100)
                if result.total_links > 0
                else 0
            ),
        }
        output_text = json.dumps(output_data, indent=2)
    else:
        output_text = generator.generate_validation_report(result)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(output_text)
        click.echo(f"Validation report written to: {output}")
    else:
        click.echo(output_text)

    # Exit with error code if validation failed
    if result.invalid_links or result.errors:
        sys.exit(1)


@cli.command()
@click.argument("rtm_file_path", required=False)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be updated without making changes"
)
@click.option("--backup", is_flag=True, help="Create backup before updating")
@click.pass_context
def update(ctx, rtm_file_path: Optional[str], dry_run: bool, backup: bool):
    """Update RTM links to current format."""
    generator = ctx.obj["generator"]
    rtm_path = rtm_file_path or ctx.obj["rtm_file"]

    if not os.path.exists(rtm_path):
        click.echo(f"Error: RTM file not found: {rtm_path}", err=True)
        sys.exit(1)

    if ctx.obj["verbose"]:
        action = "Dry run update" if dry_run else "Updating"
        click.echo(f"{action} RTM file: {rtm_path}")

    # Create backup if requested and not dry run
    if backup and not dry_run:
        backup_path = f"{rtm_path}.backup"
        import shutil

        shutil.copy2(rtm_path, backup_path)
        click.echo(f"Backup created: {backup_path}")

    updates = generator.update_rtm_links(rtm_path, dry_run=dry_run)

    if "error" in updates:
        click.echo(f"Error: {updates['error']}", err=True)
        sys.exit(1)

    # Report results
    total_updates = sum(updates.values())

    if dry_run:
        click.echo("DRY RUN - No changes made")

    click.echo("RTM Link Update Results:")
    click.echo(f"  Epic links updated: {updates['epic_links']}")
    click.echo(f"  User story links updated: {updates['user_story_links']}")
    click.echo(f"  Defect links updated: {updates['defect_links']}")
    click.echo(f"  File links updated: {updates['file_links']}")
    click.echo(f"  Total updates: {total_updates}")

    if total_updates == 0:
        click.echo("No updates needed - all links are current")
    elif not dry_run:
        click.echo(f"RTM file updated successfully: {rtm_path}")


@cli.command()
@click.argument("issue_id")
@click.option("--bold", is_flag=True, help="Make issue ID bold")
@click.option(
    "--copy", is_flag=True, help="Copy result to clipboard (requires pyperclip)"
)
@click.pass_context
def generate_link(ctx, issue_id: str, bold: bool, copy: bool):
    """Generate a single GitHub issue link."""
    generator = ctx.obj["generator"]

    link = generator.generate_github_issue_link(issue_id, bold=bold)

    click.echo(link)

    if copy:
        try:
            import pyperclip

            pyperclip.copy(link)
            click.echo("Link copied to clipboard!")
        except ImportError:
            click.echo("Warning: pyperclip not installed, cannot copy to clipboard")


@cli.command()
@click.argument("feature_file")
@click.argument("scenario_name")
@click.option(
    "--rtm-path",
    default="docs/traceability/requirements-matrix.md",
    help="RTM file path for relative link calculation",
)
@click.option(
    "--copy", is_flag=True, help="Copy result to clipboard (requires pyperclip)"
)
@click.pass_context
def generate_bdd_link(
    ctx, feature_file: str, scenario_name: str, rtm_path: str, copy: bool
):
    """Generate a BDD scenario link."""
    generator = ctx.obj["generator"]

    link = generator.generate_bdd_scenario_link(feature_file, scenario_name, rtm_path)

    click.echo(link)

    if copy:
        try:
            import pyperclip

            pyperclip.copy(link)
            click.echo("Link copied to clipboard!")
        except ImportError:
            click.echo("Warning: pyperclip not installed, cannot copy to clipboard")


@cli.command()
@click.pass_context
def config_info(ctx):
    """Display current configuration."""
    generator = ctx.obj["generator"]
    config = generator.config

    click.echo("RTM Automation Configuration:")
    click.echo("=" * 30)
    click.echo(f"GitHub Owner: {generator.github_owner}")
    click.echo(f"GitHub Repo: {generator.github_repo}")
    click.echo(f"Config File: {ctx.obj['config_path'] or 'Default configuration'}")
    click.echo()

    click.echo("Link Patterns:")
    for pattern_type, pattern in generator.link_patterns.items():
        click.echo(f"  {pattern_type}: {pattern}")

    click.echo()
    click.echo("Validation Settings:")
    validation_config = config.get("validation", {})
    for setting, value in validation_config.items():
        click.echo(f"  {setting}: {value}")


@cli.command()
@click.pass_context
def doctor(ctx):
    """Run diagnostic checks on RTM setup."""
    generator = ctx.obj["generator"]
    rtm_path = ctx.obj["rtm_file"]

    click.echo("RTM Automation Health Check")
    click.echo("=" * 30)

    # Check RTM file exists
    if os.path.exists(rtm_path):
        click.echo(f"✅ RTM file found: {rtm_path}")
    else:
        click.echo(f"❌ RTM file not found: {rtm_path}")
        return

    # Check RTM file is readable
    try:
        with open(rtm_path, "r", encoding="utf-8") as f:
            content = f.read()
        click.echo(f"✅ RTM file is readable ({len(content)} characters)")
    except Exception as e:
        click.echo(f"❌ Cannot read RTM file: {e}")
        return

    # Check for required directories
    required_dirs = ["docs/traceability", "tests/bdd/features", "src", ".github"]

    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            click.echo(f"✅ Directory exists: {dir_path}")
        else:
            click.echo(f"⚠️  Directory not found: {dir_path}")

    # Check Python dependencies
    try:
        import yaml

        click.echo("✅ PyYAML available for configuration")
    except ImportError:
        click.echo("⚠️  PyYAML not available (configuration will use defaults)")

    try:
        import pyperclip

        click.echo("✅ pyperclip available for clipboard operations")
    except ImportError:
        click.echo("⚠️  pyperclip not available (clipboard copy disabled)")

    # Validate RTM content
    click.echo("\nRunning RTM validation...")
    result = generator.validate_rtm_links(rtm_path)

    if result.total_links == 0:
        click.echo("⚠️  No links found in RTM file")
    else:
        health_score = (result.valid_links / result.total_links) * 100
        if health_score >= 90:
            status = "✅"
        elif health_score >= 70:
            status = "⚠️ "
        else:
            status = "❌"

        click.echo(
            f"{status} RTM Health: {health_score:.1f}% ({result.valid_links}/{result.total_links} links valid)"
        )

    if result.errors:
        click.echo(f"❌ {len(result.errors)} validation errors found")

    if result.warnings:
        click.echo(f"⚠️  {len(result.warnings)} warnings found")

    click.echo("\nDiagnostic complete!")


if __name__ == "__main__":
    cli()
