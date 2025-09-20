#!/usr/bin/env python3
"""
RTM Links CLI Tool

Command-line interface for RTM link generation and validation.
Provides easy access to RTM automation functionality.

Related Issue: US-00015 - Automated RTM link generation and validation
Epic: EP-00005 - RTM Automation

Usage:
  python tools/rtm-links.py --validate
  python tools/rtm-links.py --update --dry-run
  python tools/rtm-links.py --validate --report validation-report.md
"""

import sys
import os
from pathlib import Path

# Add src to Python path to import our modules
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import click
from shared.utils.rtm_link_generator import RTMLinkGenerator, RTMValidationResult


@click.group()
@click.option('--config', '-c',
              default='config/rtm-automation.yml',
              help='Path to RTM automation configuration file')
@click.option('--rtm-file', '-f',
              default='docs/traceability/requirements-matrix.md',
              help='Path to RTM file')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output')
@click.pass_context
def cli(ctx, config, rtm_file, verbose):
    """RTM (Requirements Traceability Matrix) automation tool."""
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['rtm_file'] = rtm_file
    ctx.obj['verbose'] = verbose

    # Initialize RTM generator
    try:
        ctx.obj['generator'] = RTMLinkGenerator(config)
    except Exception as e:
        click.echo(f"Error initializing RTM generator: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--report', '-r',
              help='Save validation report to file')
@click.option('--format', 'report_format',
              type=click.Choice(['markdown', 'json', 'text']),
              default='markdown',
              help='Report format')
@click.option('--fail-on-error', is_flag=True,
              help='Exit with error code if validation fails')
@click.pass_context
def validate(ctx, report, report_format, fail_on_error):
    """Validate RTM links."""
    generator = ctx.obj['generator']
    rtm_file = ctx.obj['rtm_file']
    verbose = ctx.obj['verbose']

    if not os.path.exists(rtm_file):
        click.echo(f"Error: RTM file not found: {rtm_file}", err=True)
        sys.exit(1)

    click.echo(f"Validating RTM links in {rtm_file}...")

    try:
        result = generator.validate_rtm_links(rtm_file)

        # Display summary
        click.echo(f"\n📊 Validation Summary:")
        click.echo(f"   Total links: {result.total_links}")
        click.echo(f"   Valid links: {result.valid_links}")
        click.echo(f"   Invalid links: {len(result.invalid_links)}")

        if result.total_links > 0:
            health_score = (result.valid_links / result.total_links) * 100
            if health_score == 100:
                click.echo(f"   Health score: {health_score:.1f}% ✅")
            elif health_score >= 90:
                click.echo(f"   Health score: {health_score:.1f}% ⚠️")
            else:
                click.echo(f"   Health score: {health_score:.1f}% ❌")

        # Display invalid links
        if result.invalid_links:
            click.echo(f"\n❌ Invalid Links:")
            for link in result.invalid_links:
                click.echo(f"   - {link.text}: {link.error_message}")

        # Display warnings
        if result.warnings:
            click.echo(f"\n⚠️  Warnings:")
            for warning in result.warnings:
                click.echo(f"   - {warning}")

        # Display errors
        if result.errors and verbose:
            click.echo(f"\n🚫 Errors:")
            for error in result.errors:
                click.echo(f"   - {error}")

        # Generate report if requested
        if report:
            report_content = generator.generate_validation_report(result)
            with open(report, 'w', encoding='utf-8') as f:
                f.write(report_content)
            click.echo(f"\n📄 Validation report saved to {report}")

        # Exit with error code if validation failed and requested
        if fail_on_error and len(result.invalid_links) > 0:
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error during validation: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--dry-run', is_flag=True, default=True,
              help='Show what would be updated without making changes')
@click.option('--force', is_flag=True,
              help='Actually perform updates (overrides dry-run)')
@click.option('--backup', is_flag=True, default=True,
              help='Create backup before updating')
@click.pass_context
def update(ctx, dry_run, force, backup):
    """Update RTM links to current format."""
    generator = ctx.obj['generator']
    rtm_file = ctx.obj['rtm_file']
    verbose = ctx.obj['verbose']

    if not os.path.exists(rtm_file):
        click.echo(f"Error: RTM file not found: {rtm_file}", err=True)
        sys.exit(1)

    # Override dry_run if force is specified
    if force:
        dry_run = False

    click.echo(f"Updating RTM links in {rtm_file}...")
    if dry_run:
        click.echo("(Dry run - no changes will be made)")

    try:
        # Create backup if requested and not dry run
        if backup and not dry_run:
            backup_path = f"{rtm_file}.backup"
            import shutil
            shutil.copy2(rtm_file, backup_path)
            click.echo(f"📄 Backup created: {backup_path}")

        # Perform updates
        updates = generator.update_rtm_links(rtm_file, dry_run=dry_run)

        # Display results
        click.echo(f"\n🔄 Updates:")
        total_updates = 0
        for link_type, count in updates.items():
            if count > 0:
                click.echo(f"   - {link_type.replace('_', ' ').title()}: {count}")
                total_updates += count

        if total_updates == 0:
            click.echo("   - No updates needed ✅")
        elif dry_run:
            click.echo(f"\n📝 {total_updates} updates would be made")
            click.echo("   Use --force to apply changes")
        else:
            click.echo(f"\n✅ {total_updates} updates applied successfully")

    except Exception as e:
        click.echo(f"Error during update: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--issue-id', required=True,
              help='GitHub issue ID (e.g., EP-00001, US-00014)')
@click.option('--bold', is_flag=True,
              help='Generate bold link (for epics)')
@click.pass_context
def generate_link(ctx, issue_id, bold):
    """Generate a single GitHub issue link."""
    generator = ctx.obj['generator']

    try:
        link = generator.generate_github_issue_link(issue_id, bold=bold)
        click.echo(link)
    except Exception as e:
        click.echo(f"Error generating link: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--feature-file', required=True,
              help='Path to BDD feature file')
@click.option('--scenario', required=True,
              help='Scenario name')
@click.option('--rtm-file',
              help='RTM file path (for relative link calculation)')
@click.pass_context
def generate_bdd_link(ctx, feature_file, scenario, rtm_file):
    """Generate a BDD scenario link."""
    generator = ctx.obj['generator']

    if not rtm_file:
        rtm_file = ctx.obj['rtm_file']

    try:
        link = generator.generate_bdd_scenario_link(feature_file, scenario, rtm_file)
        click.echo(link)
    except Exception as e:
        click.echo(f"Error generating BDD link: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def config_info(ctx):
    """Display current configuration."""
    generator = ctx.obj['generator']
    config_path = ctx.obj['config']

    click.echo(f"📋 RTM Automation Configuration")
    click.echo(f"   Config file: {config_path}")
    click.echo(f"   RTM file: {ctx.obj['rtm_file']}")
    click.echo(f"   GitHub owner: {generator.github_owner}")
    click.echo(f"   GitHub repo: {generator.github_repo}")

    # Check if files exist
    if os.path.exists(config_path):
        click.echo(f"   Config status: ✅ Found")
    else:
        click.echo(f"   Config status: ⚠️  Using defaults")

    if os.path.exists(ctx.obj['rtm_file']):
        click.echo(f"   RTM file status: ✅ Found")
    else:
        click.echo(f"   RTM file status: ❌ Not found")


@cli.command()
@click.pass_context
def doctor(ctx):
    """Run diagnostic checks on RTM setup."""
    click.echo("🔍 RTM Setup Diagnostics")
    click.echo("")

    # Check Python environment
    click.echo("📋 Python Environment:")
    click.echo(f"   Python version: {sys.version.split()[0]}")

    # Check required directories
    directories = [
        'docs/traceability',
        'tests/bdd/features',
        'tests/bdd/step_definitions',
        'config'
    ]

    click.echo("\n📁 Directory Structure:")
    for directory in directories:
        if os.path.exists(directory):
            click.echo(f"   {directory}: ✅")
        else:
            click.echo(f"   {directory}: ❌ Missing")

    # Check key files
    files = [
        ctx.obj['rtm_file'],
        ctx.obj['config'],
        'docs/technical/documentation-workflow.md'
    ]

    click.echo("\n📄 Key Files:")
    for file_path in files:
        if os.path.exists(file_path):
            click.echo(f"   {file_path}: ✅")
        else:
            click.echo(f"   {file_path}: ❌ Missing")

    # Check RTM content if file exists
    if os.path.exists(ctx.obj['rtm_file']):
        try:
            generator = ctx.obj['generator']
            result = generator.validate_rtm_links(ctx.obj['rtm_file'])

            click.echo(f"\n🔗 RTM Link Health:")
            if result.total_links > 0:
                health_score = (result.valid_links / result.total_links) * 100
                click.echo(f"   Total links: {result.total_links}")
                click.echo(f"   Valid links: {result.valid_links}")
                click.echo(f"   Health score: {health_score:.1f}%")
            else:
                click.echo("   No links found in RTM")
        except Exception as e:
            click.echo(f"\n🔗 RTM Link Health: ❌ Error - {e}")


if __name__ == '__main__':
    cli()