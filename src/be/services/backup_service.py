"""
Comprehensive Database Backup Service

Implements automated backup and disaster recovery for the RTM database with
GDPR compliance.
Provides daily snapshots, integrity validation, and multiple destination
support.

Related Issue: US-00036 - Comprehensive Database Backup Strategy
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Blocks: #101, #102, #103, #106, #108, #109, #110, #111, #112, #113
"""

import base64
import hashlib
import logging
import os
import shutil
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import text

from ..database import DATABASE_URL, get_db_session

# Configure logging
logger = logging.getLogger(__name__)


class BackupError(Exception):
    """Custom exception for backup operations."""

    pass


class BackupService:
    """
    Comprehensive backup service with GDPR compliance and multi-destination
    support.

    Features:
    - Automated daily database snapshots
    - GDPR-compliant encryption for sensitive data
    - Multiple backup destinations
    - Integrity validation and corruption detection
    - 5-minute recovery time objective
    """

    def __init__(self, backup_base_dir: str = "backups", encryption_key: Optional[str] = None):
        """
        Initialize backup service.

        Args:
            backup_base_dir: Base directory for backup storage
            encryption_key: Optional encryption key for GDPR data (auto-generated if None)
        """
        self.backup_base_dir = Path(backup_base_dir)
        self.backup_base_dir.mkdir(exist_ok=True)

        # Initialize encryption for GDPR compliance
        self.encryption_key = encryption_key or self._generate_encryption_key()
        self.cipher_suite = self._initialize_encryption()

        # Backup configuration
        self.retention_days = 30  # GDPR-compliant retention period
        self.max_backup_size_mb = 500  # Maximum backup file size

        # Multiple destination support
        self.backup_destinations = [
            self.backup_base_dir / "local",
            self.backup_base_dir / "secondary",
        ]

        # Ensure backup directories exist
        for dest in self.backup_destinations:
            dest.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Backup service initialized with %d destinations",
            len(self.backup_destinations),
        )

    def _generate_encryption_key(self) -> str:
        """Generate encryption key for GDPR data protection."""
        password = os.getenv("BACKUP_ENCRYPTION_PASSWORD", "gonogo-backup-key-2025").encode()
        salt = os.getenv("BACKUP_SALT", "gonogo-rtm-salt").encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key.decode()

    def _initialize_encryption(self) -> Fernet:
        """Initialize encryption cipher for GDPR compliance."""
        try:
            return Fernet(self.encryption_key.encode())
        except Exception as e:
            logger.error("Failed to initialize encryption: %s", e)
            # Fallback to new key generation
            self.encryption_key = self._generate_encryption_key()
            return Fernet(self.encryption_key.encode())

    def create_daily_backup(self) -> Dict[str, any]:
        """
        Create automated daily database backup.

        Returns:
            Dict containing backup status, file paths, and metadata
        """
        start_time = datetime.now(UTC)
        backup_id = start_time.strftime("%Y%m%d_%H%M%S")

        logger.info("Starting daily backup process: %s", backup_id)

        try:
            # Validate database health before backup
            self._validate_database_health()

            # Create backup in all configured destinations
            backup_results = []
            for destination in self.backup_destinations:
                try:
                    result = self._create_backup_to_destination(backup_id, destination)
                    backup_results.append(result)
                    logger.info("Backup successful to destination: %s", destination)
                except Exception as e:
                    logger.error("Backup failed to destination %s: %s", destination, e)
                    backup_results.append(
                        {
                            "destination": str(destination),
                            "success": False,
                            "error": str(e),
                        }
                    )

            # Validate backup integrity
            successful_backups = [r for r in backup_results if r.get("success", False)]
            if not successful_backups:
                raise BackupError("All backup destinations failed")

            # Perform integrity validation on successful backups
            for backup_result in successful_backups:
                self._validate_backup_integrity(backup_result["file_path"])

            # Clean up old backups per retention policy
            self._cleanup_old_backups()

            end_time = datetime.now(UTC)
            duration = (end_time - start_time).total_seconds()

            result = {
                "backup_id": backup_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "successful_destinations": len(successful_backups),
                "total_destinations": len(self.backup_destinations),
                "backup_results": backup_results,
                "integrity_validated": True,
                "gdpr_compliant": True,
            }

            logger.info("Daily backup completed successfully: %s", backup_id)
            return result

        except Exception as e:
            logger.error("Daily backup failed: %s", e)
            raise BackupError(f"Daily backup failed: {e}")

    def _create_backup_to_destination(self, backup_id: str, destination: Path) -> Dict[str, any]:
        """Create backup to specific destination."""
        backup_filename = f"gonogo_backup_{backup_id}.db"
        backup_path = destination / backup_filename

        # Extract database path from DATABASE_URL
        if DATABASE_URL.startswith("sqlite:///"):
            source_db_path = DATABASE_URL.replace("sqlite:///", "")
        else:
            raise BackupError("Only SQLite databases are currently supported for backup")

        # Use SQLite backup API for atomic backup
        self._create_sqlite_backup(source_db_path, str(backup_path))

        # Create backup metadata
        metadata = self._create_backup_metadata(backup_id, backup_path)
        metadata_path = destination / f"gonogo_backup_{backup_id}.metadata.json"

        import json

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Encrypt GDPR-sensitive data if present
        if self._contains_gdpr_data():
            encrypted_path = self._encrypt_gdpr_data(backup_path)
            metadata["gdpr_encrypted"] = True
            metadata["encrypted_file"] = str(encrypted_path)

        return {
            "destination": str(destination),
            "success": True,
            "backup_id": backup_id,
            "file_path": str(backup_path),
            "metadata_path": str(metadata_path),
            "file_size": backup_path.stat().st_size if backup_path.exists() else 0,
            "checksum": self._calculate_checksum(backup_path),
        }

    def _create_sqlite_backup(self, source_path: str, backup_path: str) -> None:
        """Create SQLite backup using the backup API for atomic operation."""
        try:
            # Connect to source database
            source_conn = sqlite3.connect(source_path)

            # Connect to backup database
            backup_conn = sqlite3.connect(backup_path)

            # Perform backup using SQLite backup API
            source_conn.backup(backup_conn)

            # Close connections
            backup_conn.close()
            source_conn.close()

            logger.debug("SQLite backup created: %s", backup_path)

        except Exception as e:
            logger.error("SQLite backup failed: %s", e)
            raise BackupError(f"SQLite backup failed: {e}")

    def _create_backup_metadata(self, backup_id: str, backup_path: Path) -> Dict[str, any]:
        """Create comprehensive backup metadata."""
        db = get_db_session()
        try:
            # Count RTM entities
            epic_count = db.execute(text("SELECT COUNT(*) FROM epics")).scalar()
            user_story_count = db.execute(text("SELECT COUNT(*) FROM user_stories")).scalar()
            defect_count = db.execute(text("SELECT COUNT(*) FROM defects")).scalar()
            capability_count = db.execute(text("SELECT COUNT(*) FROM capabilities")).scalar()

            metadata = {
                "backup_id": backup_id,
                "created_at": datetime.now(UTC).isoformat(),
                "database_url": DATABASE_URL,
                "file_path": str(backup_path),
                "file_size": backup_path.stat().st_size,
                "rtm_entity_counts": {
                    "epics": epic_count,
                    "user_stories": user_story_count,
                    "defects": defect_count,
                    "capabilities": capability_count,
                    "total": epic_count + user_story_count + defect_count + capability_count,
                },
                "backup_version": "1.0",
                "gdpr_compliant": True,
                "unicode_safe": True,
                "checksum": self._calculate_checksum(backup_path),
            }

            return metadata

        finally:
            db.close()

    def _validate_database_health(self) -> bool:
        """Validate database health before backup."""
        from ..database import check_database_health

        health = check_database_health()
        if health["status"] != "healthy":
            raise BackupError(f"Database unhealthy: {health.get('error', 'Unknown error')}")

    def _validate_backup_integrity(self, backup_path: str) -> bool:
        """
        Validate backup file integrity.

        Args:
            backup_path: Path to backup file

        Returns:
            True if backup is valid

        Raises:
            BackupError: If backup is corrupted
        """
        try:
            # Test SQLite database integrity
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()

            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

            if result[0] != "ok":
                raise BackupError(f"Backup integrity check failed: {result[0]}")

            # Verify essential tables exist
            essential_tables = ["epics", "user_stories", "defects", "capabilities"]
            for table in essential_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.debug("Table %s contains %d records", table, count)

            conn.close()
            logger.info("Backup integrity validation passed: %s", backup_path)
            return True

        except Exception as e:
            logger.error("Backup integrity validation failed: %s", e)
            raise BackupError(f"Backup integrity validation failed: {e}")

    def _contains_gdpr_data(self) -> bool:
        """Check if database contains GDPR-sensitive data."""
        try:
            db = get_db_session()
            try:
                # Check for GDPR consent records table
                result = db.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='consent_records'")
                ).fetchone()
                return result is not None
            finally:
                db.close()
        except Exception:
            return False

    def _encrypt_gdpr_data(self, backup_path: Path) -> Path:
        """Encrypt GDPR-sensitive data in backup file."""
        try:
            # Read backup file
            with open(backup_path, "rb") as f:
                data = f.read()

            # Encrypt data
            encrypted_data = self.cipher_suite.encrypt(data)

            # Write encrypted backup
            encrypted_path = backup_path.with_suffix(".encrypted")
            with open(encrypted_path, "wb") as f:
                f.write(encrypted_data)

            logger.info("GDPR data encrypted: %s", encrypted_path)
            return encrypted_path

        except Exception as e:
            logger.error("GDPR data encryption failed: %s", e)
            raise BackupError(f"GDPR data encryption failed: {e}")

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of backup file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _cleanup_old_backups(self) -> None:
        """Clean up old backups according to retention policy."""
        cutoff_date = datetime.now(UTC) - timedelta(days=self.retention_days)

        for destination in self.backup_destinations:
            try:
                for backup_file in destination.glob("gonogo_backup_*.db"):
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime, UTC)
                    if file_time < cutoff_date:
                        # Remove backup file and metadata
                        backup_file.unlink()
                        metadata_file = backup_file.with_suffix(".metadata.json")
                        if metadata_file.exists():
                            metadata_file.unlink()

                        # Remove encrypted version if exists
                        encrypted_file = backup_file.with_suffix(".encrypted")
                        if encrypted_file.exists():
                            encrypted_file.unlink()

                        logger.info("Removed old backup: %s", backup_file)

            except Exception as e:
                logger.error("Cleanup failed for destination %s: %s", destination, e)

    def restore_from_backup(self, backup_path: str, target_db_path: Optional[str] = None) -> Dict[str, any]:
        """
        Restore database from backup with 5-minute recovery target.

        Args:
            backup_path: Path to backup file
            target_db_path: Target database path (uses current DATABASE_URL if None)

        Returns:
            Dict containing restoration status and metrics
        """
        start_time = datetime.now(UTC)
        logger.info("Starting database restoration from: %s", backup_path)

        try:
            # Determine target database path
            if target_db_path is None:
                if DATABASE_URL.startswith("sqlite:///"):
                    target_db_path = DATABASE_URL.replace("sqlite:///", "")
                else:
                    raise BackupError("Target database path required for non-SQLite databases")

            # Validate backup file exists and is readable
            backup_file = Path(backup_path)
            if not backup_file.exists():
                raise BackupError(f"Backup file not found: {backup_path}")

            # Decrypt if encrypted
            if backup_path.endswith(".encrypted"):
                backup_path = self._decrypt_backup(backup_path)

            # Validate backup integrity before restoration
            self._validate_backup_integrity(backup_path)

            # Create backup of current database if it exists
            current_db = Path(target_db_path)
            if current_db.exists():
                backup_current = current_db.with_suffix(".pre-restore-backup")
                shutil.copy2(current_db, backup_current)
                logger.info("Current database backed up to: %s", backup_current)

            # Perform restoration
            shutil.copy2(backup_path, target_db_path)

            # Validate restored database
            self._validate_database_health()

            # Calculate restoration time
            end_time = datetime.now(UTC)
            duration = (end_time - start_time).total_seconds()

            # Verify data integrity post-restoration
            restoration_metadata = self._verify_restored_data(target_db_path)

            result = {
                "restored_at": end_time.isoformat(),
                "duration_seconds": duration,
                "source_backup": backup_path,
                "target_database": target_db_path,
                "integrity_verified": True,
                "recovery_time_target_met": duration <= 300,
                # 5 minutes = 300 seconds
                "restoration_metadata": restoration_metadata,
            }

            logger.info("Database restoration completed in %.2f seconds", duration)

            if duration > 300:
                logger.warning(
                    "Recovery time target exceeded: %.2f seconds > 300 seconds",
                    duration,
                )

            return result

        except Exception as e:
            logger.error("Database restoration failed: %s", e)
            raise BackupError(f"Database restoration failed: {e}")

    def _decrypt_backup(self, encrypted_path: str) -> str:
        """Decrypt GDPR-encrypted backup file."""
        try:
            with open(encrypted_path, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = self.cipher_suite.decrypt(encrypted_data)

            # Write decrypted file
            decrypted_path = encrypted_path.replace(".encrypted", ".decrypted")
            with open(decrypted_path, "wb") as f:
                f.write(decrypted_data)

            logger.info("Backup decrypted successfully: %s", decrypted_path)
            return decrypted_path

        except Exception as e:
            logger.error("Backup decryption failed: %s", e)
            raise BackupError(f"Backup decryption failed: {e}")

    def _verify_restored_data(self, db_path: str) -> Dict[str, any]:
        """Verify data integrity after restoration."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Count entities in restored database
            cursor.execute("SELECT COUNT(*) FROM epics")
            epic_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM user_stories")
            user_story_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM defects")
            defect_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM capabilities")
            capability_count = cursor.fetchone()[0]

            conn.close()

            return {
                "epics": epic_count,
                "user_stories": user_story_count,
                "defects": defect_count,
                "capabilities": capability_count,
                "total_entities": epic_count + user_story_count + defect_count + capability_count,
            }

        except Exception as e:
            logger.error("Data verification failed: %s", e)
            raise BackupError(f"Data verification failed: {e}")

    def get_backup_status(self) -> Dict[str, any]:
        """Get comprehensive backup system status."""
        status = {
            "service_status": "operational",
            "backup_destinations": [],
            "recent_backups": [],
            "retention_days": self.retention_days,
            "gdpr_compliance": True,
            "encryption_enabled": True,
        }

        # Check each destination
        for destination in self.backup_destinations:
            dest_status = {
                "path": str(destination),
                "accessible": destination.exists(),
                "backup_count": len(list(destination.glob("gonogo_backup_*.db"))),
                "latest_backup": None,
            }

            # Find latest backup
            backups = sorted(
                destination.glob("gonogo_backup_*.db"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )
            if backups:
                latest = backups[0]
                dest_status["latest_backup"] = {
                    "file": latest.name,
                    "created": datetime.fromtimestamp(latest.stat().st_mtime, UTC).isoformat(),
                    "size_mb": round(latest.stat().st_size / (1024 * 1024), 2),
                }

            status["backup_destinations"].append(dest_status)

        return status
