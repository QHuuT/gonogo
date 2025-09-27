"""
Backup Management API Endpoints

RESTful API for database backup and disaster recovery operations.
Integrates with the backup service and monitoring system for comprehensive
management.

Related Issue: US-00036 - Comprehensive Database Backup Strategy
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Integration: FastAPI backend architecture
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.backup_monitor import BackupMonitor
from ..services.backup_service import BackupError, BackupService

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/backup", tags=["backup"])


# Pydantic models for API requests/responses
class BackupRequest(BaseModel):
    """Request model for backup creation."""

    destinations: Optional[List[str]] = Field(None, description="Specific backup destinations")
    encrypt_gdpr: Optional[bool] = Field(True, description="Force GDPR encryption")
    validate_integrity: Optional[bool] = Field(True, description="Validate backup integrity")


class BackupResponse(BaseModel):
    """Response model for backup operations."""

    backup_id: str
    status: str  # success, partial, failed
    start_time: str
    end_time: str
    duration_seconds: float
    successful_destinations: int
    total_destinations: int
    file_paths: List[str]
    integrity_validated: bool
    gdpr_compliant: bool
    message: str


class RestoreRequest(BaseModel):
    """Request model for database restoration."""

    backup_file: str = Field(..., description="Path to backup file")
    target_database: Optional[str] = Field(None, description="Target database path")
    verify_only: Optional[bool] = Field(False, description="Only verify backup without restoring")
    force: Optional[bool] = Field(False, description="Force restoration without confirmation")


class RestoreResponse(BaseModel):
    """Response model for restore operations."""

    restored_at: str
    duration_seconds: float
    source_backup: str
    target_database: str
    integrity_verified: bool
    recovery_time_target_met: bool
    restored_entities: Dict[str, int]
    message: str


class BackupStatusResponse(BaseModel):
    """Response model for backup system status."""

    service_status: str
    backup_destinations: List[Dict]
    retention_days: int
    gdpr_compliance: bool
    encryption_enabled: bool
    recent_backups: List[Dict]
    system_health: Optional[Dict] = None


class MonitoringDashboardResponse(BaseModel):
    """Response model for monitoring dashboard."""

    system_status: str
    monitoring_summary: Dict
    recent_performance: Dict
    alert_summary: Dict
    latest_backup: Dict
    configuration: Dict


# Dependency to get backup service
def get_backup_service() -> BackupService:
    """Get backup service instance."""
    return BackupService()


# Dependency to get backup monitor
def get_backup_monitor() -> BackupMonitor:
    """Get backup monitor instance."""
    return BackupMonitor(
        alert_email="admin@gonogo.local",  # Config from env
        sla_recovery_time_minutes=5,
    )


# API Endpoints
@router.post("/create", response_model=BackupResponse)
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    backup_service: BackupService = Depends(get_backup_service),
    monitor: BackupMonitor = Depends(get_backup_monitor),
):
    """
    Create comprehensive database backup.

    Creates backup with integrity validation, GDPR compliance,
    and multi-destination support. Supports both automated and manual
    backup triggers with real-time monitoring.
    """
    try:
        logger.info("API backup request received")

        # Start monitoring
        background_tasks.add_task(monitor.monitor_backup_operation, backup_service)

        # Create backup
        result = backup_service.create_daily_backup()

        # Prepare response
        file_paths = []
        for backup_result in result.get("backup_results", []):
            if backup_result.get("success", False):
                file_paths.append(backup_result["file_path"])

        response = BackupResponse(
            backup_id=result["backup_id"],
            status=("success" if result["successful_destinations"] > 0 else "failed"),
            start_time=result["start_time"],
            end_time=result["end_time"],
            duration_seconds=result["duration_seconds"],
            successful_destinations=result["successful_destinations"],
            total_destinations=result["total_destinations"],
            file_paths=file_paths,
            integrity_validated=result.get("integrity_validated", False),
            gdpr_compliant=result.get("gdpr_compliant", False),
            message=(
                f"Backup completed with {result['successful_destinations']}/"
                f"{result['total_destinations']} destinations successful"
            ),
        )

        logger.info("API backup completed successfully: %s", result["backup_id"])
        return response

    except BackupError as e:
        logger.error("API backup failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Backup operation failed: {e}")

    except Exception as e:
        logger.error("API backup unexpected error: %s", e)
        raise HTTPException(status_code=500, detail=f"Unexpected error during backup: {e}")


@router.post("/restore", response_model=RestoreResponse)
async def restore_database(
    request: RestoreRequest,
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    Restore database from backup with 5-minute recovery target.

    Performs fast database restoration with integrity validation
    and data verification. Supports encrypted backups and maintains
    GDPR compliance during recovery.
    """
    try:
        logger.info("API restore request received for backup: %s", request.backup_file)

        # Verify backup file exists
        backup_path = Path(request.backup_file)
        if not backup_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Backup file not found: {request.backup_file}",
            )

        # Verify only mode
        if request.verify_only:
            try:
                backup_service._validate_backup_integrity(request.backup_file)
                return RestoreResponse(
                    restored_at=datetime.now(UTC).isoformat(),
                    duration_seconds=0,
                    source_backup=request.backup_file,
                    target_database="verification_only",
                    integrity_verified=True,
                    recovery_time_target_met=True,
                    restored_entities={},
                    message="Backup verification completed successfully",
                )
            except BackupError as e:
                raise HTTPException(status_code=400, detail=f"Backup verification failed: {e}")

        # Perform restoration
        result = backup_service.restore_from_backup(
            backup_path=request.backup_file,
            target_db_path=request.target_database,
        )

        response = RestoreResponse(
            restored_at=result["restored_at"],
            duration_seconds=result["duration_seconds"],
            source_backup=result["source_backup"],
            target_database=result["target_database"],
            integrity_verified=result["integrity_verified"],
            recovery_time_target_met=result["recovery_time_target_met"],
            restored_entities=result["restoration_metadata"],
            message=(f"Database restored successfully in {result['duration_seconds']:.2f} seconds"),
        )

        logger.info("API restore completed successfully")
        return response

    except BackupError as e:
        logger.error("API restore failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Restore operation failed: {e}")

    except Exception as e:
        logger.error("API restore unexpected error: %s", e)
        raise HTTPException(status_code=500, detail=f"Unexpected error during restore: {e}")


@router.get("/status", response_model=BackupStatusResponse)
async def get_backup_status(
    include_health: bool = Query(False, description="Include database health check"),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    Get comprehensive backup system status.

    Returns backup destinations, recent backups, retention policy,
    and system health. Provides overview of backup coverage
    and GDPR compliance status.
    """
    try:
        logger.debug("API status request received")

        # Get backup status
        status = backup_service.get_backup_status()

        # Add database health if requested
        system_health = None
        if include_health:
            from ..database import check_database_health

            system_health = check_database_health()

        # Get recent backups info
        recent_backups = []
        for dest in status["backup_destinations"]:
            if dest.get("latest_backup"):
                recent_backups.append(
                    {
                        "destination": dest["path"],
                        "backup_info": dest["latest_backup"],
                    }
                )

        response = BackupStatusResponse(
            service_status=status["service_status"],
            backup_destinations=status["backup_destinations"],
            retention_days=status["retention_days"],
            gdpr_compliance=status["gdpr_compliance"],
            encryption_enabled=status["encryption_enabled"],
            recent_backups=recent_backups,
            system_health=system_health,
        )

        return response

    except Exception as e:
        logger.error("API status request failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get backup status: {e}")


@router.get("/monitor/dashboard", response_model=MonitoringDashboardResponse)
async def get_monitoring_dashboard(
    monitor: BackupMonitor = Depends(get_backup_monitor),
):
    """
    Get comprehensive monitoring dashboard data.

    Returns system performance metrics, alert summaries, SLA compliance,
    and recent backup statistics for administrative oversight.
    """
    try:
        logger.debug("API monitoring dashboard request received")

        dashboard_data = monitor.get_monitoring_dashboard()
        return MonitoringDashboardResponse(**dashboard_data)

    except Exception as e:
        logger.error("API monitoring dashboard failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring dashboard: {e}")


@router.get("/monitor/health")
async def get_health_check(
    backup_service: BackupService = Depends(get_backup_service),
    monitor: BackupMonitor = Depends(get_backup_monitor),
):
    """
    Run comprehensive backup system health check.

    Performs system validation including backup service status,
    recent backup availability, alert system functionality,
    and overall system health assessment.
    """
    try:
        logger.debug("API health check request received")

        health_results = monitor.run_health_check(backup_service)
        return health_results

    except Exception as e:
        logger.error("API health check failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")


@router.post("/validate/{backup_id}")
async def validate_backup(
    backup_id: str,
    deep_check: bool = Query(False, description="Perform deep integrity validation"),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    Validate specific backup file integrity.

    Performs comprehensive validation including SQLite integrity checks,
    entity counts, and GDPR compliance verification for the specified backup.
    """
    try:
        logger.info("API validation request for backup: %s", backup_id)

        # Find backup file by ID
        backup_found = False
        validation_results = []

        for destination in backup_service.backup_destinations:
            backup_file = destination / f"gonogo_backup_{backup_id}.db"
            if backup_file.exists():
                backup_found = True

                try:
                    # Basic integrity validation
                    backup_service._validate_backup_integrity(str(backup_file))

                    # Calculate checksum
                    checksum = backup_service._calculate_checksum(backup_file)

                    result = {
                        "destination": str(destination),
                        "file_path": str(backup_file),
                        "integrity_valid": True,
                        "checksum": checksum,
                        "file_size": backup_file.stat().st_size,
                        "validation_time": datetime.now(UTC).isoformat(),
                    }

                    # Deep validation if requested
                    if deep_check:
                        metadata = backup_service._verify_restored_data(str(backup_file))
                        result["entity_counts"] = metadata

                    validation_results.append(result)

                except BackupError as e:
                    validation_results.append(
                        {
                            "destination": str(destination),
                            "file_path": str(backup_file),
                            "integrity_valid": False,
                            "error": str(e),
                            "validation_time": datetime.now(UTC).isoformat(),
                        }
                    )

        if not backup_found:
            raise HTTPException(
                status_code=404,
                detail=f"Backup {backup_id} not found in any destination",
            )

        return {
            "backup_id": backup_id,
            "validation_time": datetime.now(UTC).isoformat(),
            "destinations_checked": len(validation_results),
            "valid_backups": sum(1 for r in validation_results if r.get("integrity_valid", False)),
            "validation_results": validation_results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("API validation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Validation failed: {e}")


@router.delete("/cleanup")
async def cleanup_old_backups(
    days: int = Query(30, description="Retention period in days"),
    dry_run: bool = Query(True, description="Show what would be cleaned without deleting"),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    Clean up old backups according to retention policy.

    Removes backups older than specified days while maintaining
    GDPR compliance. Supports dry-run mode to preview cleanup
    actions before execution.
    """
    try:
        logger.info("API cleanup request: %d days, dry_run=%s", days, dry_run)

        from datetime import timedelta

        # Set retention policy
        backup_service.retention_days = days

        # Find old backups
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        cleanup_summary = {
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": days,
            "dry_run": dry_run,
            "destinations": [],
        }

        total_files = 0
        total_size_mb = 0

        for destination in backup_service.backup_destinations:
            dest_summary = {
                "path": str(destination),
                "old_backups": [],
                "files_to_delete": 0,
                "size_to_free_mb": 0,
            }

            for backup_file in destination.glob("gonogo_backup_*.db"):
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime, UTC)
                if file_time < cutoff_date:
                    age_days = (datetime.now(UTC) - file_time).days
                    size_mb = backup_file.stat().st_size / (1024 * 1024)

                    backup_info = {
                        "file": backup_file.name,
                        "age_days": age_days,
                        "size_mb": round(size_mb, 2),
                        "created": file_time.isoformat(),
                    }

                    dest_summary["old_backups"].append(backup_info)
                    dest_summary["files_to_delete"] += 1
                    dest_summary["size_to_free_mb"] += size_mb

                    total_files += 1
                    total_size_mb += size_mb

                    # Actually delete if not dry run
                    if not dry_run:
                        try:
                            backup_file.unlink()

                            # Remove associated files
                            metadata_file = backup_file.with_suffix(".metadata.json")
                            if metadata_file.exists():
                                metadata_file.unlink()

                            encrypted_file = backup_file.with_suffix(".encrypted")
                            if encrypted_file.exists():
                                encrypted_file.unlink()

                            backup_info["deleted"] = True

                        except Exception as e:
                            backup_info["deleted"] = False
                            backup_info["error"] = str(e)

            cleanup_summary["destinations"].append(dest_summary)

        cleanup_summary.update(
            {
                "total_files_identified": total_files,
                "total_size_mb": round(total_size_mb, 2),
                "cleanup_time": datetime.now(UTC).isoformat(),
                "message": (
                    f"{'Would delete' if dry_run else 'Deleted'} {total_files} backup files ({total_size_mb:.1f} MB)"
                ),
            }
        )

        logger.info(
            "API cleanup completed: %d files, %.1f MB",
            total_files,
            total_size_mb,
        )
        return cleanup_summary

    except Exception as e:
        logger.error("API cleanup failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Cleanup operation failed: {e}")


@router.get("/destinations")
async def list_backup_destinations(
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    List all configured backup destinations with accessibility status.

    Returns information about each backup destination including accessibility,
    backup counts, and latest backup information.
    """
    try:
        logger.debug("API destinations list request received")

        destinations_info = []

        for destination in backup_service.backup_destinations:
            # Count backups in destination
            backup_files = list(destination.glob("gonogo_backup_*.db"))
            backup_count = len(backup_files)

            # Find latest backup
            latest_backup = None
            if backup_files:
                latest_file = max(backup_files, key=lambda x: x.stat().st_mtime)
                latest_backup = {
                    "file": latest_file.name,
                    "created": datetime.fromtimestamp(latest_file.stat().st_mtime, UTC).isoformat(),
                    "size_mb": round(latest_file.stat().st_size / (1024 * 1024), 2),
                }

            dest_info = {
                "path": str(destination),
                "accessible": destination.exists() and destination.is_dir(),
                "backup_count": backup_count,
                "latest_backup": latest_backup,
                "free_space_mb": None,  # shutil.disk_usage
            }

            # Calculate free space if accessible
            if dest_info["accessible"]:
                try:
                    import shutil

                    total, used, free = shutil.disk_usage(destination)
                    dest_info["free_space_mb"] = round(free / (1024 * 1024), 2)
                except Exception:
                    pass

            destinations_info.append(dest_info)

        return {
            "destinations": destinations_info,
            "total_destinations": len(destinations_info),
            "accessible_destinations": sum(1 for d in destinations_info if d["accessible"]),
            "total_backups": sum(d["backup_count"] for d in destinations_info),
        }

    except Exception as e:
        logger.error("API destinations list failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to list destinations: {e}")


# Error handlers
@router.exception_handler(BackupError)
async def backup_error_handler(request, exc) -> dict[str, str]:
    """Handle backup-specific errors."""
    logger.error("Backup error in API: %s", exc)
    return HTTPException(status_code=500, detail=str(exc))


# Health check endpoint for the backup API itself
@router.get("/api-health")
async def api_health_check() -> dict[str, str]:
    """Simple health check for the backup API endpoints."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "api_version": "1.0",
        "endpoints": [
            "/api/backup/create",
            "/api/backup/restore",
            "/api/backup/status",
            "/api/backup/monitor/dashboard",
            "/api/backup/monitor/health",
            "/api/backup/validate/{backup_id}",
            "/api/backup/cleanup",
            "/api/backup/destinations",
        ],
    }
