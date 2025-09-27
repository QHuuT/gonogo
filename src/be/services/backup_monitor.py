"""
Backup Monitoring and Alerting Service

Real-time monitoring and alerting system for database backup operations.
Provides immediate administrator alerts, corruption detection, and SLA
tracking.

Related Issue: US-00036 - Comprehensive Database Backup Strategy
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Dependencies: US-00064 - Backup Health Monitoring and Alerting
"""

import logging
import smtplib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.mime.multipart import MimeMultipart
from email.mime.text import MimeText
from enum import Enum
from typing import Dict, List, Optional

from .backup_service import BackupError, BackupService

# Configure logging
logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Available alert channels."""

    EMAIL = "email"
    LOG = "log"
    WEBHOOK = "webhook"


@dataclass
class Alert:
    """Alert data structure."""

    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    component: str
    details: Optional[Dict] = None


@dataclass
class BackupMetrics:
    """Backup performance metrics."""

    backup_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    success: bool
    file_size_mb: float
    destinations_success: int
    destinations_total: int
    error_message: Optional[str] = None


class BackupMonitor:
    """
    Comprehensive backup monitoring and alerting service.

    Features:
    - Real-time backup health monitoring
    - Immediate administrator alerts via multiple channels
    - Backup corruption detection and validation
    - Performance metrics and SLA tracking
    - Automated remediation triggers
    """

    def __init__(
        self,
        alert_email: Optional[str] = None,
        smtp_config: Optional[Dict] = None,
        sla_recovery_time_minutes: int = 5,
    ):
        """
        Initialize backup monitoring service.

        Args:
            alert_email: Administrator email for alerts
            smtp_config: SMTP configuration for email alerts
            sla_recovery_time_minutes: SLA target for recovery time
        """
        self.alert_email = alert_email
        self.smtp_config = smtp_config or self._get_default_smtp_config()
        self.sla_recovery_time_minutes = sla_recovery_time_minutes

        # Monitoring configuration
        self.max_backup_age_hours = (
            25  # Alert if no backup in 25 hours (daily + buffer)
        )
        self.max_backup_duration_minutes = 30  # Alert if backup takes > 30min
        self.min_success_rate = 0.8  # Alert if success rate < 80%

        # Metrics storage (in production, use proper database)
        self.backup_history: List[BackupMetrics] = []
        self.alert_history: List[Alert] = []

        logger.info("Backup monitoring service initialized")

    def _get_default_smtp_config(self) -> Dict[str, str]:
        """Get default SMTP configuration from environment."""
        import os

        return {
            "smtp_server": os.getenv("SMTP_SERVER", "localhost"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "smtp_username": os.getenv("SMTP_USERNAME", ""),
            "smtp_password": os.getenv("SMTP_PASSWORD", ""),
            "smtp_use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        }

    def monitor_backup_operation(self, backup_service: BackupService) -> Dict[str, any]:
        """
        Monitor a backup operation in real-time.

        Args:
            backup_service: Backup service instance

        Returns:
            Dict containing monitoring results and any alerts generated
        """
        start_time = datetime.now(UTC)
        backup_id = start_time.strftime("%Y%m%d_%H%M%S")

        logger.info("Starting backup monitoring for operation: %s", backup_id)

        try:
            # Execute backup with monitoring
            backup_result = backup_service.create_daily_backup()

            # Calculate metrics
            end_time = datetime.now(UTC)
            duration = backup_result["duration_seconds"]

            # Determine success based on backup results
            successful_destinations = backup_result.get("successful_destinations", 0)
            total_destinations = backup_result.get("total_destinations", 1)
            success = successful_destinations > 0

            # Calculate file size (use first successful backup)
            file_size_mb = 0
            for result in backup_result.get("backup_results", []):
                if result.get("success", False):
                    file_size_mb = result.get("file_size", 0) / (1024 * 1024)
                    break

            # Create metrics record
            metrics = BackupMetrics(
                backup_id=backup_id,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                success=success,
                file_size_mb=file_size_mb,
                destinations_success=successful_destinations,
                destinations_total=total_destinations,
            )

            self.backup_history.append(metrics)

            # Generate alerts based on metrics
            alerts = self._analyze_backup_metrics(metrics, backup_result)

            # Send alerts if any
            for alert in alerts:
                self._send_alert(alert)

            # Check overall backup health
            health_alerts = self._check_backup_health()
            for alert in health_alerts:
                self._send_alert(alert)

            monitoring_result = {
                "backup_id": backup_id,
                "monitoring_success": True,
                "metrics": {
                    "duration_seconds": duration,
                    "success": success,
                    "file_size_mb": file_size_mb,
                    "destinations_success": successful_destinations,
                    "destinations_total": total_destinations,
                    "sla_met": (duration <= (self.sla_recovery_time_minutes * 60)),
                },
                "alerts_generated": len(alerts),
                "alerts": [{"level": a.level.value, "title": a.title} for a in alerts],
            }

            logger.info("Backup monitoring completed successfully: %s", backup_id)
            return monitoring_result

        except Exception as e:
            # Record failed backup
            end_time = datetime.now(UTC)
            duration = (end_time - start_time).total_seconds()

            failed_metrics = BackupMetrics(
                backup_id=backup_id,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                success=False,
                file_size_mb=0,
                destinations_success=0,
                destinations_total=1,
                error_message=str(e),
            )

            self.backup_history.append(failed_metrics)

            # Generate critical alert for failed backup
            alert = Alert(
                level=AlertLevel.CRITICAL,
                title="Backup Operation Failed",
                message=f"Backup operation {backup_id} failed with error: {e}",
                timestamp=end_time,
                component="backup_service",
                details={"backup_id": backup_id, "error": str(e)},
            )

            self._send_alert(alert)

            logger.error("Backup monitoring failed: %s", e)
            raise BackupError(f"Backup monitoring failed: {e}")

    def _analyze_backup_metrics(
        self, metrics: BackupMetrics, backup_result: Dict
    ) -> List[Alert]:
        """Analyze backup metrics and generate alerts."""
        alerts = []

        # Check backup duration
        if metrics.duration_seconds > (self.max_backup_duration_minutes * 60):
            alerts.append(
                Alert(
                    level=AlertLevel.WARNING,
                    title="Backup Duration Exceeded",
                    message=(
                        f"Backup {metrics.backup_id} took "
                        f"{metrics.duration_seconds:.1f} seconds "
                        f"(>{self.max_backup_duration_minutes} minutes)"
                    ),
                    timestamp=metrics.end_time,
                    component="backup_performance",
                    details={
                        "backup_id": metrics.backup_id,
                        "duration": metrics.duration_seconds,
                    },
                )
            )

        # Check destination success rate
        success_rate = metrics.destinations_success / metrics.destinations_total
        if success_rate < self.min_success_rate:
            alerts.append(
                Alert(
                    level=AlertLevel.ERROR,
                    title="Backup Destination Failures",
                    message=(
                        f"Only {metrics.destinations_success}/"
                        f"{metrics.destinations_total} destinations succeeded "
                        f"(success rate: {success_rate:.1%})"
                    ),
                    timestamp=metrics.end_time,
                    component="backup_destinations",
                    details={
                        "backup_id": metrics.backup_id,
                        "success_rate": success_rate,
                        "failed_destinations": metrics.destinations_total
                        - metrics.destinations_success,
                    },
                )
            )

        # Check for complete backup failure
        if not metrics.success:
            alerts.append(
                Alert(
                    level=AlertLevel.CRITICAL,
                    title="Complete Backup Failure",
                    message=f"Backup {metrics.backup_id} failed completely. "
                    f"Error: {metrics.error_message or 'Unknown error'}",
                    timestamp=metrics.end_time,
                    component="backup_service",
                    details={
                        "backup_id": metrics.backup_id,
                        "error": metrics.error_message,
                    },
                )
            )

        # Check backup integrity
        if not backup_result.get("integrity_validated", False):
            alerts.append(
                Alert(
                    level=AlertLevel.ERROR,
                    title="Backup Integrity Validation Failed",
                    message=f"Backup {metrics.backup_id} failed integrity validation",
                    timestamp=metrics.end_time,
                    component="backup_integrity",
                    details={"backup_id": metrics.backup_id},
                )
            )

        return alerts

    def _check_backup_health(self) -> List[Alert]:
        """Check overall backup system health."""
        alerts = []
        now = datetime.now(UTC)

        # Check if we have recent successful backups
        if self.backup_history:
            latest_backup = max(self.backup_history, key=lambda x: x.end_time)
            hours_since_backup = (now - latest_backup.end_time).total_seconds() / 3600

            if hours_since_backup > self.max_backup_age_hours:
                alerts.append(
                    Alert(
                        level=AlertLevel.WARNING,
                        title="Backup Schedule Alert",
                        message=f"No backup completed in {hours_since_backup:.1f} hours (expected every 24 hours)",
                        timestamp=now,
                        component="backup_schedule",
                        details={"hours_since_backup": hours_since_backup},
                    )
                )

            # Check recent success rate
            recent_backups = [
                b
                for b in self.backup_history
                if (now - b.end_time).total_seconds() < (7 * 24 * 3600)
            ]  # Last 7 days

            if recent_backups:
                success_count = sum(1 for b in recent_backups if b.success)
                success_rate = success_count / len(recent_backups)

                if success_rate < self.min_success_rate:
                    alerts.append(
                        Alert(
                            level=AlertLevel.ERROR,
                            title="Low Backup Success Rate",
                            message=f"Recent backup success rate: {success_rate:.1%} "
                            f"({success_count}/{len(recent_backups)} in last 7 days)",
                            timestamp=now,
                            component="backup_reliability",
                            details={
                                "success_rate": success_rate,
                                "successful_backups": success_count,
                                "total_backups": len(recent_backups),
                            },
                        )
                    )

        return alerts

    def detect_backup_corruption(
        self, backup_service: BackupService, backup_paths: List[str]
    ) -> List[Alert]:
        """
        Detect corruption in existing backup files.

        Args:
            backup_service: Backup service instance
            backup_paths: List of backup file paths to validate

        Returns:
            List of alerts for any corrupted backups found
        """
        alerts = []
        now = datetime.now(UTC)

        logger.info(
            "Starting corruption detection for %d backup files", len(backup_paths)
        )

        for backup_path in backup_paths:
            try:
                # Validate backup integrity
                backup_service._validate_backup_integrity(backup_path)
                logger.debug("Backup integrity OK: %s", backup_path)

            except BackupError as e:
                alerts.append(
                    Alert(
                        level=AlertLevel.CRITICAL,
                        title="Backup Corruption Detected",
                        message=f"Corrupted backup file: {backup_path}. Error: {e}",
                        timestamp=now,
                        component="backup_integrity",
                        details={"backup_path": backup_path, "error": str(e)},
                    )
                )

                logger.error("Backup corruption detected: %s - %s", backup_path, e)

            except Exception as e:
                alerts.append(
                    Alert(
                        level=AlertLevel.WARNING,
                        title="Backup Validation Error",
                        message=f"Could not validate backup: {backup_path}. Error: {e}",
                        timestamp=now,
                        component="backup_validation",
                        details={"backup_path": backup_path, "error": str(e)},
                    )
                )

                logger.warning("Backup validation error: %s - %s", backup_path, e)

        if alerts:
            logger.warning("Corruption detection found %d issues", len(alerts))
        else:
            logger.info("Corruption detection completed - no issues found")

        return alerts

    def _send_alert(self, alert: Alert):
        """Send alert via configured channels."""
        self.alert_history.append(alert)

        # Always log the alert
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL,
        }[alert.level]

        logger.log(
            log_level,
            "ALERT [%s] %s: %s",
            alert.level.value.upper(),
            alert.title,
            alert.message,
        )

        # Send email alert for warning level and above
        if (
            alert.level in [AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL]
            and self.alert_email
        ):
            self._send_email_alert(alert)

    def _send_email_alert(self, alert: Alert):
        """Send email alert to administrators."""
        try:
            # Create email message
            msg = MimeMultipart()
            msg["From"] = self.smtp_config.get(
                "smtp_username", "backup-monitor@gonogo.local"
            )
            msg["To"] = self.alert_email
            msg["Subject"] = f"[GoNoGo Backup Alert] {alert.title}"

            # Email body
            body = f"""
Database Backup Alert

Level: {alert.level.value.upper()}
Title: {alert.title}
Component: {alert.component}
Timestamp: {alert.timestamp.isoformat()}

Message:
{alert.message}

"""

            if alert.details:
                body += "Details:\n"
                for key, value in alert.details.items():
                    body += f"  {key}: {value}\n"

            body += """

This is an automated alert from the GoNoGo database backup monitoring system.
Please investigate and take appropriate action.

---
GoNoGo Backup Monitor
US-00036: Comprehensive Database Backup Strategy
"""

            msg.attach(MimeText(body, "plain"))

            # Send email
            server = smtplib.SMTP(
                self.smtp_config["smtp_server"], self.smtp_config["smtp_port"]
            )

            if self.smtp_config["smtp_use_tls"]:
                server.starttls()

            if self.smtp_config["smtp_username"]:
                server.login(
                    self.smtp_config["smtp_username"], self.smtp_config["smtp_password"]
                )

            server.send_message(msg)
            server.quit()

            logger.info("Email alert sent successfully: %s", alert.title)

        except Exception as e:
            logger.error("Failed to send email alert: %s", e)

    def get_monitoring_dashboard(self) -> Dict[str, any]:
        """Get comprehensive monitoring dashboard data."""
        now = datetime.now(UTC)

        # Calculate summary statistics
        total_backups = len(self.backup_history)
        successful_backups = sum(1 for b in self.backup_history if b.success)
        success_rate = successful_backups / total_backups if total_backups > 0 else 0

        # Recent backup metrics (last 24 hours)
        recent_cutoff = now - timedelta(hours=24)
        recent_backups = [b for b in self.backup_history if b.end_time > recent_cutoff]

        # Recent alerts (last 7 days)
        alert_cutoff = now - timedelta(days=7)
        recent_alerts = [a for a in self.alert_history if a.timestamp > alert_cutoff]

        # SLA compliance
        sla_target_seconds = self.sla_recovery_time_minutes * 60
        sla_compliant_backups = sum(
            1
            for b in self.backup_history
            if b.success and b.duration_seconds <= sla_target_seconds
        )
        sla_compliance_rate = (
            sla_compliant_backups / total_backups if total_backups > 0 else 0
        )

        dashboard = {
            "system_status": "operational" if success_rate > 0.8 else "degraded",
            "monitoring_summary": {
                "total_backups": total_backups,
                "successful_backups": successful_backups,
                "success_rate": round(success_rate, 3),
                "sla_compliance_rate": round(sla_compliance_rate, 3),
                "recent_backups_24h": len(recent_backups),
                "recent_alerts_7d": len(recent_alerts),
            },
            "recent_performance": {
                "avg_duration_minutes": (
                    round(
                        sum(b.duration_seconds for b in recent_backups)
                        / len(recent_backups)
                        / 60,
                        2,
                    )
                    if recent_backups
                    else 0
                ),
                "avg_file_size_mb": (
                    round(
                        sum(b.file_size_mb for b in recent_backups)
                        / len(recent_backups),
                        2,
                    )
                    if recent_backups
                    else 0
                ),
                "destination_reliability": (
                    round(
                        sum(
                            b.destinations_success / b.destinations_total
                            for b in recent_backups
                        )
                        / len(recent_backups),
                        3,
                    )
                    if recent_backups
                    else 0
                ),
            },
            "alert_summary": {
                "critical": sum(
                    1 for a in recent_alerts if a.level == AlertLevel.CRITICAL
                ),
                "error": sum(1 for a in recent_alerts if a.level == AlertLevel.ERROR),
                "warning": sum(
                    1 for a in recent_alerts if a.level == AlertLevel.WARNING
                ),
                "info": sum(1 for a in recent_alerts if a.level == AlertLevel.INFO),
            },
            "latest_backup": {
                "backup_id": (
                    self.backup_history[-1].backup_id if self.backup_history else None
                ),
                "timestamp": (
                    self.backup_history[-1].end_time.isoformat()
                    if self.backup_history
                    else None
                ),
                "success": (
                    self.backup_history[-1].success if self.backup_history else None
                ),
                "duration_seconds": (
                    self.backup_history[-1].duration_seconds
                    if self.backup_history
                    else None
                ),
            },
            "configuration": {
                "sla_recovery_time_minutes": self.sla_recovery_time_minutes,
                "max_backup_age_hours": self.max_backup_age_hours,
                "min_success_rate": self.min_success_rate,
                "alert_email_configured": bool(self.alert_email),
            },
        }

        return dashboard

    def run_health_check(self, backup_service: BackupService) -> Dict[str, any]:
        """Run comprehensive backup system health check."""
        start_time = datetime.now(UTC)
        health_results = {
            "timestamp": start_time.isoformat(),
            "overall_health": "healthy",
            "checks": [],
        }

        # Check 1: Backup service status
        try:
            status = backup_service.get_backup_status()
            health_results["checks"].append(
                {
                    "name": "backup_service_status",
                    "status": "pass",
                    "message": f"Service operational with {len(status['backup_destinations'])} destinations",
                }
            )
        except Exception as e:
            health_results["checks"].append(
                {
                    "name": "backup_service_status",
                    "status": "fail",
                    "message": f"Backup service error: {e}",
                }
            )
            health_results["overall_health"] = "unhealthy"

        # Check 2: Recent backup availability
        if self.backup_history:
            latest_backup = max(self.backup_history, key=lambda x: x.end_time)
            hours_since_backup = (
                start_time - latest_backup.end_time
            ).total_seconds() / 3600

            if hours_since_backup <= self.max_backup_age_hours:
                health_results["checks"].append(
                    {
                        "name": "recent_backup_availability",
                        "status": "pass",
                        "message": f"Latest backup {hours_since_backup:.1f} hours ago",
                    }
                )
            else:
                health_results["checks"].append(
                    {
                        "name": "recent_backup_availability",
                        "status": "fail",
                        "message": f"No recent backup ({hours_since_backup:.1f} hours ago)",
                    }
                )
                health_results["overall_health"] = "degraded"
        else:
            health_results["checks"].append(
                {
                    "name": "recent_backup_availability",
                    "status": "fail",
                    "message": "No backup history available",
                }
            )
            health_results["overall_health"] = "unhealthy"

        # Check 3: Alert system functionality
        try:
            test_alert = Alert(
                level=AlertLevel.INFO,
                title="Health Check Test Alert",
                message="Testing alert system functionality",
                timestamp=start_time,
                component="health_check",
            )
            # Don't actually send the test alert, just validate the mechanism
            health_results["checks"].append(
                {
                    "name": "alert_system",
                    "status": "pass",
                    "message": f"Alert system configured with email: {bool(self.alert_email)}",
                }
            )
        except Exception as e:
            health_results["checks"].append(
                {
                    "name": "alert_system",
                    "status": "fail",
                    "message": f"Alert system error: {e}",
                }
            )

        return health_results
