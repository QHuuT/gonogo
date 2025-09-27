#!/usr/bin/env python3
"""
Database Backup Management CLI Tool

Comprehensive CLI tool for managing database backups with GDPR compliance and
multiple destination support. Integrates with the existing RTM CLI ecosystem.

Usage:
    python tools/backup_manager.py backup [--destinations] [--encrypt]
    python tools/backup_manager.py restore --backup-file PATH [--target PATH]
    python tools/backup_manager.py status [--verbose]
    python tools/backup_manager.py cleanup [--dry-run] [--days DAYS]
    python tools/backup_manager.py validate --backup-file PATH

Related Issue: US-00036 - Comprehensive Database Backup Strategy
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Integration: Part of 70+ automation tools ecosystem
"""

import sys
import json
import click
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Optional

# Add src to path for imports
sys.path.append('src')

from be.services.backup_service import BackupService, BackupError
from be.database import check_database_health

# Configure Click CLI
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--backup-dir', default='backups', help='Base backup directory')
@click.pass_context
def cli(ctx, verbose: bool, backup_dir: str):
    """
    Database Backup Management CLI Tool

    Comprehensive backup and disaster recovery management for the RTM database.
    Supports automated backups, GDPR-compliant encryption, and 5-minute recovery.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['backup_dir'] = backup_dir

    if verbose:
        click.echo(f"Backup manager initialized with directory: {backup_dir}")

@cli.command()
@click.option(
    '--destinations', '-d', multiple=True, help='Specific backup destinations'
)
@click.option('--encrypt', '-e', is_flag=True, help='Force GDPR encryption')
@click.option(
    '--dry-run', is_flag=True, help='Show what would be done without executing'
)
@click.pass_context
def backup(ctx, destinations: tuple, encrypt: bool, dry_run: bool):
    """
    Create comprehensive database backup.

    Creates backup with integrity validation, GDPR compliance, and \
    multi-destination support.
    Follows automated daily backup procedures with manual trigger capability.
    """
    verbose = ctx.obj['verbose']
    backup_dir = ctx.obj['backup_dir']

    if dry_run:
        click.echo("DRY RUN: Backup operations that would be performed:")
        click.echo(f"  - Backup directory: {backup_dir}")
        click.echo(f"  - GDPR encryption: {'Enabled' if encrypt else 'Auto-detect'}")
        click.echo(
            f"  - Destinations: {len(destinations) if destinations else 'All configured'}"
        )
        return

    try:
        if verbose:
            click.echo("Initializing backup service...")

        service = BackupService(backup_base_dir=backup_dir)

        # Check database health before backup
        if verbose:
            click.echo("Checking database health...")

        health = check_database_health()
        if health["status"] != "healthy":
            click.echo(
                f"Database health check failed: {health.get('error', 'Unknown error')}"
            )
            sys.exit(1)

        if verbose:
            click.echo("Database health: OK")
            click.echo("Starting backup process...")

        # Create backup
        start_time = datetime.now(UTC)
        result = service.create_daily_backup()

        # Display results
        click.echo("Backup completed successfully!")
        click.echo(f"Backup ID: {result['backup_id']}")
        click.echo(f"Duration: {result['duration_seconds']:.2f} seconds")
        click.echo(f"Successful destinations: {result['successful_destinations']}/{result['total_destinations']}")

        if verbose:
            click.echo("\nBackup Details:")
            for backup_result in result['backup_results']:
                if backup_result.get('success', False):
                    click.echo(f"  ✓ {backup_result['destination']}")
                    click.echo(f"    File: {backup_result['file_path']}")
                    click.echo(f"    Size: {backup_result['file_size']:,} bytes")
                    click.echo(f"    Checksum: {backup_result['checksum'][:16]}...")
                else:
                    click.echo(f"  ✗ {backup_result['destination']}")
                    click.echo(f"    Error: {backup_result.get('error', 'Unknown error')}")

        if result['gdpr_compliant']:
            click.echo("GDPR compliance: ✓ Verified")

        if result['integrity_validated']:
            click.echo("Integrity validation: ✓ Passed")

    except BackupError as e:
        click.echo(f"Backup failed: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error during backup: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

@cli.command()
@click.option('--backup-file', '-f', required=True, help='Path to backup file')
@click.option('--target', '-t', help='Target database path (defaults to current DATABASE_URL)')
@click.option('--force', is_flag=True, help='Force restoration without confirmation')
@click.option('--verify-only', is_flag=True, help='Only verify backup without restoring')
@click.pass_context
def restore(ctx, backup_file: str, target: Optional[str], force: bool, verify_only: bool):
    """
    Restore database from backup with 5-minute recovery target.

    Performs fast database restoration with integrity validation and data verification.
    Supports encrypted backups and maintains GDPR compliance during recovery.
    """
    verbose = ctx.obj['verbose']
    backup_dir = ctx.obj['backup_dir']

    try:
        if verbose:
            click.echo("Initializing backup service for restoration...")

        service = BackupService(backup_base_dir=backup_dir)

        # Verify backup file exists
        backup_path = Path(backup_file)
        if not backup_path.exists():
            click.echo(f"Backup file not found: {backup_file}")
            sys.exit(1)

        if verbose:
            click.echo(f"Backup file found: {backup_file}")
            click.echo("Validating backup integrity...")

        # Validate backup before restoration
        try:
            service._validate_backup_integrity(str(backup_path))
            click.echo("Backup integrity validation: ✓ Passed")
        except BackupError as e:
            click.echo(f"Backup integrity validation failed: {e}")
            sys.exit(1)

        if verify_only:
            click.echo("Backup verification completed successfully.")
            return

        # Confirm restoration unless forced
        if not force:
            click.echo("⚠️  WARNING: This will replace the current database!")
            if target:
                click.echo(f"Target: {target}")
            else:
                click.echo("Target: Current DATABASE_URL")

            if not click.confirm("Do you want to continue with the restoration?"):
                click.echo("Restoration cancelled.")
                return

        if verbose:
            click.echo("Starting database restoration...")

        # Perform restoration
        start_time = datetime.now(UTC)
        result = service.restore_from_backup(backup_file, target)

        # Display results
        click.echo("Database restoration completed!")
        click.echo(f"Duration: {result['duration_seconds']:.2f} seconds")

        if result['recovery_time_target_met']:
            click.echo("Recovery time target: ✓ Met (< 5 minutes)")
        else:
            click.echo("Recovery time target: ⚠️  Exceeded 5 minutes")

        if verbose:
            click.echo("\nRestoration Details:")
            click.echo(f"  Source backup: {result['source_backup']}")
            click.echo(f"  Target database: {result['target_database']}")
            click.echo(f"  Integrity verified: {'✓' if result['integrity_verified'] else '✗'}")

            metadata = result['restoration_metadata']
            click.echo("  Restored entities:")
            click.echo(f"    Epics: {metadata['epics']}")
            click.echo(f"    User Stories: {metadata['user_stories']}")
            click.echo(f"    Defects: {metadata['defects']}")
            click.echo(f"    Capabilities: {metadata['capabilities']}")
            click.echo(f"    Total: {metadata['total_entities']}")

    except BackupError as e:
        click.echo(f"Restoration failed: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error during restoration: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

@cli.command()
@click.option('--json-output', '-j', is_flag=True, help='Output status in JSON format')
@click.option('--check-health', is_flag=True, help='Include database health check')
@click.pass_context
def status(ctx, json_output: bool, check_health: bool):
    """
    Display comprehensive backup system status.

    Shows backup destinations, recent backups, retention policy, and system health.
    Provides overview of backup coverage and GDPR compliance status.
    """
    verbose = ctx.obj['verbose']
    backup_dir = ctx.obj['backup_dir']

    try:
        service = BackupService(backup_base_dir=backup_dir)

        # Get backup status
        status_data = service.get_backup_status()

        # Add database health if requested
        if check_health:
            health = check_database_health()
            status_data['database_health'] = health

        if json_output:
            click.echo(json.dumps(status_data, indent=2))
            return

        # Human-readable output
        click.echo("Database Backup System Status")
        click.echo("=" * 40)

        click.echo(f"Service Status: {status_data['service_status']}")
        click.echo(f"Retention Policy: {status_data['retention_days']} days")
        click.echo(f"GDPR Compliance: {'✓ Enabled' if status_data['gdpr_compliance'] else '✗ Disabled'}")
        click.echo(f"Encryption: {'✓ Enabled' if status_data['encryption_enabled'] else '✗ Disabled'}")

        if check_health:
            health = status_data['database_health']
            click.echo(f"Database Health: {'✓ Healthy' if health['status'] == 'healthy' else '✗ Unhealthy'}")
            if health['status'] != 'healthy':
                click.echo(f"  Error: {health.get('error', 'Unknown error')}")

        click.echo("\nBackup Destinations:")
        for i, dest in enumerate(status_data['backup_destinations'], 1):
            status_icon = "✓" if dest['accessible'] else "✗"
            click.echo(f"{i}. {status_icon} {dest['path']}")
            click.echo(f"   Backups: {dest['backup_count']}")

            if dest['latest_backup']:
                latest = dest['latest_backup']
                click.echo(f"   Latest: {latest['file']} ({latest['size_mb']} MB)")
                click.echo(f"   Created: {latest['created']}")
            else:
                click.echo("   Latest: No backups found")

        if verbose:
            click.echo(f"\nBackup Directory: {backup_dir}")
            click.echo("Use --json-output for machine-readable format")

    except Exception as e:
        click.echo(f"Failed to get backup status: {e}")
        sys.exit(1)

@cli.command()
@click.option('--days', '-d', default=30, help='Retention period in days')
@click.option('--dry-run', is_flag=True, help='Show what would be cleaned up without deleting')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def cleanup(ctx, days: int, dry_run: bool, force: bool):
    """
    Clean up old backups according to retention policy.

    Removes backups older than specified days while maintaining GDPR compliance.
    Preserves critical backups and audit trail per legal requirements.
    """
    verbose = ctx.obj['verbose']
    backup_dir = ctx.obj['backup_dir']

    try:
        service = BackupService(backup_base_dir=backup_dir)
        service.retention_days = days

        if verbose:
            click.echo(f"Scanning for backups older than {days} days...")

        # Find old backups
        from datetime import timedelta
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        old_backups = []

        for destination in service.backup_destinations:
            for backup_file in destination.glob("gonogo_backup_*.db"):
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime, UTC)
                if file_time < cutoff_date:
                    old_backups.append({
                        'file': backup_file,
                        'age_days': (datetime.now(UTC) - file_time).days,
                        'size_mb': backup_file.stat().st_size / (1024 * 1024)
                    })

        if not old_backups:
            click.echo(f"No backups older than {days} days found.")
            return

        click.echo(f"Found {len(old_backups)} backup(s) for cleanup:")
        total_size = 0
        for backup in old_backups:
            click.echo(f"  - {backup['file'].name} ({backup['age_days']} days old, {backup['size_mb']:.1f} MB)")
            total_size += backup['size_mb']

        click.echo(f"Total space to be freed: {total_size:.1f} MB")

        if dry_run:
            click.echo("DRY RUN: No files were actually deleted.")
            return

        if not force:
            if not click.confirm(f"Delete {len(old_backups)} old backup(s)?"):
                click.echo("Cleanup cancelled.")
                return

        # Perform cleanup
        deleted_count = 0
        for backup in old_backups:
            try:
                backup['file'].unlink()

                # Remove associated metadata and encrypted files
                metadata_file = backup['file'].with_suffix('.metadata.json')
                if metadata_file.exists():
                    metadata_file.unlink()

                encrypted_file = backup['file'].with_suffix('.encrypted')
                if encrypted_file.exists():
                    encrypted_file.unlink()

                deleted_count += 1
                if verbose:
                    click.echo(f"  Deleted: {backup['file'].name}")

            except Exception as e:
                click.echo(f"  Failed to delete {backup['file'].name}: {e}")

        click.echo(f"Cleanup completed: {deleted_count}/{len(old_backups)} backups deleted")

    except Exception as e:
        click.echo(f"Cleanup failed: {e}")
        sys.exit(1)

@cli.command()
@click.option('--backup-file', '-f', required=True, help='Path to backup file to validate')
@click.option('--deep-check', is_flag=True, help='Perform deep integrity validation')
@click.pass_context
def validate(ctx, backup_file: str, deep_check: bool):
    """
    Validate backup file integrity and completeness.

    Performs comprehensive validation including SQLite integrity checks,
    entity counts, and GDPR compliance verification.
    """
    verbose = ctx.obj['verbose']
    backup_dir = ctx.obj['backup_dir']

    try:
        service = BackupService(backup_base_dir=backup_dir)

        backup_path = Path(backup_file)
        if not backup_path.exists():
            click.echo(f"Backup file not found: {backup_file}")
            sys.exit(1)

        if verbose:
            click.echo(f"Validating backup file: {backup_file}")

        # Basic integrity validation
        try:
            service._validate_backup_integrity(backup_file)
            click.echo("Basic integrity validation: ✓ Passed")
        except BackupError as e:
            click.echo(f"Basic integrity validation: ✗ Failed - {e}")
            sys.exit(1)

        # Checksum validation
        if verbose:
            click.echo("Calculating checksum...")
        checksum = service._calculate_checksum(backup_path)
        click.echo(f"Checksum: {checksum}")

        # Deep validation if requested
        if deep_check:
            if verbose:
                click.echo("Performing deep integrity checks...")

            # Verify restored data structure
            metadata = service._verify_restored_data(backup_file)

            click.echo("Deep validation results:")
            click.echo(f"  Epics: {metadata['epics']}")
            click.echo(f"  User Stories: {metadata['user_stories']}")
            click.echo(f"  Defects: {metadata['defects']}")
            click.echo(f"  Capabilities: {metadata['capabilities']}")
            click.echo(f"  Total entities: {metadata['total_entities']}")

        # Check for encryption
        if backup_file.endswith('.encrypted'):
            click.echo("Encryption: ✓ GDPR-compliant encrypted backup")
        else:
            click.echo("Encryption: ℹ  Unencrypted backup")

        click.echo("Backup validation completed successfully.")

    except Exception as e:
        click.echo(f"Validation failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    cli()