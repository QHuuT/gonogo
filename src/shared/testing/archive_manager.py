#!/usr/bin/env python3
"""
Test Report and Log Archive Management

Automated archiving, compression, and retention management for test reports,
logs, and generated content with configurable policies and search capabilities.

Related to: US-00028 Test report archiving and retention management
Parent Epic: EP-00006 Test Logging and Reporting
"""

import os
import gzip
import json
import shutil
import zipfile
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import sqlite3


@dataclass
class RetentionPolicy:
    """Retention policy configuration for different file types."""
    file_pattern: str
    retention_days: int
    compress_after_days: int
    archive_location: str
    max_size_mb: Optional[int] = None
    enabled: bool = True


@dataclass
class ArchiveItem:
    """Metadata for an archived item."""
    original_path: str
    archive_path: str
    file_type: str
    original_size: int
    compressed_size: int
    created_date: datetime
    archived_date: datetime
    compression_ratio: float
    metadata: Dict[str, Any]


@dataclass
class StorageMetrics:
    """Storage metrics and optimization data."""
    total_files: int
    total_size_mb: float
    compressed_files: int
    compression_savings_mb: float
    old_files_count: int
    old_files_size_mb: float
    recommendations: List[str]


class TestArchiveManager:
    """Manages archiving, compression, and retention of test artifacts."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize the archive manager."""
        self.base_path = base_path or Path("quality")
        self.archive_base = self.base_path / "archives"
        self.metadata_db = self.archive_base / "archive_metadata.db"

        # Ensure directories exist
        self.archive_base.mkdir(parents=True, exist_ok=True)
        self._init_metadata_db()

        # Default retention policies
        self.policies = self._get_default_policies()

    def _init_metadata_db(self):
        """Initialize the archive metadata database."""
        with sqlite3.connect(self.metadata_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS archived_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_path TEXT NOT NULL,
                    archive_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    original_size INTEGER NOT NULL,
                    compressed_size INTEGER NOT NULL,
                    created_date TEXT NOT NULL,
                    archived_date TEXT NOT NULL,
                    compression_ratio REAL NOT NULL,
                    metadata TEXT NOT NULL
                )
            """)

    def _get_default_policies(self) -> List[RetentionPolicy]:
        """Get default retention policies for different file types."""
        return [
            RetentionPolicy(
                file_pattern="*.html",
                retention_days=90,
                compress_after_days=14,
                archive_location="reports/html",
                max_size_mb=50
            ),
            RetentionPolicy(
                file_pattern="*.json",
                retention_days=180,
                compress_after_days=30,
                archive_location="reports/json",
                max_size_mb=100
            ),
            RetentionPolicy(
                file_pattern="*.log",
                retention_days=60,
                compress_after_days=7,
                archive_location="logs",
                max_size_mb=200
            ),
            RetentionPolicy(
                file_pattern="*.db",
                retention_days=365,
                compress_after_days=90,
                archive_location="databases",
                max_size_mb=500
            ),
            RetentionPolicy(
                file_pattern="*.py",
                retention_days=30,
                compress_after_days=7,
                archive_location="scripts",
                max_size_mb=10
            ),
            RetentionPolicy(
                file_pattern="*.md",
                retention_days=120,
                compress_after_days=21,
                archive_location="reports/markdown",
                max_size_mb=20
            )
        ]

    def apply_retention_policies(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Apply retention policies to all configured directories.

        Args:
            dry_run: If True, only simulate actions without making changes

        Returns:
            Summary of actions taken or would be taken
        """
        results = {
            "processed_files": 0,
            "compressed_files": 0,
            "archived_files": 0,
            "deleted_files": 0,
            "space_saved_mb": 0,
            "actions": [],
            "errors": []
        }

        # Process each directory with files
        for directory in ["reports", "logs"]:
            dir_path = self.base_path / directory
            if not dir_path.exists():
                continue

            # Get all files in directory
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    try:
                        action = self._process_file(file_path, dry_run)
                        if action:
                            results["actions"].append(action)
                            results["processed_files"] += 1

                            if action["type"] == "compress":
                                results["compressed_files"] += 1
                                results["space_saved_mb"] += action.get("space_saved_mb", 0)
                            elif action["type"] == "archive":
                                results["archived_files"] += 1
                            elif action["type"] == "delete":
                                results["deleted_files"] += 1

                    except Exception as e:
                        error_msg = f"Error processing {file_path}: {str(e)}"
                        results["errors"].append(error_msg)

        return results

    def _process_file(self, file_path: Path, dry_run: bool = True) -> Optional[Dict[str, Any]]:
        """Process a single file according to retention policies."""
        # Find matching policy
        policy = self._find_matching_policy(file_path)
        if not policy or not policy.enabled:
            return None

        # Get file info
        file_stat = file_path.stat()
        file_age_days = (datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)).days
        file_size_mb = file_stat.st_size / (1024 * 1024)

        # Check if file should be deleted
        if file_age_days > policy.retention_days:
            if not dry_run:
                file_path.unlink()
            return {
                "type": "delete",
                "file": str(file_path),
                "reason": f"Exceeded retention period ({policy.retention_days} days)",
                "age_days": file_age_days
            }

        # Check if file should be compressed
        if (file_age_days > policy.compress_after_days and
            not self._is_compressed(file_path) and
            file_size_mb > 1):  # Only compress files > 1MB

            if not dry_run:
                compressed_path = self._compress_file(file_path)
                space_saved = file_size_mb - (compressed_path.stat().st_size / (1024 * 1024))
            else:
                space_saved = file_size_mb * 0.7  # Estimated 70% compression

            return {
                "type": "compress",
                "file": str(file_path),
                "reason": f"File older than {policy.compress_after_days} days",
                "age_days": file_age_days,
                "space_saved_mb": space_saved
            }

        # Check if file should be archived (moved to archive directory)
        if (file_age_days > policy.compress_after_days * 2 and
            not str(file_path).startswith(str(self.archive_base))):

            if not dry_run:
                archive_path = self._archive_file(file_path, policy)
            else:
                archive_path = self.archive_base / policy.archive_location / file_path.name

            return {
                "type": "archive",
                "file": str(file_path),
                "archive_path": str(archive_path),
                "reason": f"File older than {policy.compress_after_days * 2} days",
                "age_days": file_age_days
            }

        return None

    def _find_matching_policy(self, file_path: Path) -> Optional[RetentionPolicy]:
        """Find the retention policy that matches a file."""
        import fnmatch

        for policy in self.policies:
            if fnmatch.fnmatch(file_path.name, policy.file_pattern):
                return policy
        return None

    def _is_compressed(self, file_path: Path) -> bool:
        """Check if a file is already compressed."""
        return file_path.suffix.lower() in ['.gz', '.zip', '.bz2']

    def _compress_file(self, file_path: Path) -> Path:
        """Compress a file using gzip compression."""
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')

        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Remove original file
        file_path.unlink()

        return compressed_path

    def _archive_file(self, file_path: Path, policy: RetentionPolicy) -> Path:
        """Move a file to the archive directory."""
        # Create archive subdirectory
        archive_dir = self.archive_base / policy.archive_location
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped archive path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = archive_dir / f"{timestamp}_{file_path.name}"

        # Move file to archive
        shutil.move(str(file_path), str(archive_path))

        # Store metadata
        self._store_archive_metadata(file_path, archive_path, policy)

        return archive_path

    def _store_archive_metadata(self, original_path: Path, archive_path: Path, policy: RetentionPolicy):
        """Store metadata about an archived file."""
        original_size = 0
        try:
            original_stat = original_path.stat()
            original_size = original_stat.st_size
            created_date = datetime.fromtimestamp(original_stat.st_ctime)
        except:
            created_date = datetime.now()

        archive_stat = archive_path.stat()
        compressed_size = archive_stat.st_size

        metadata = {
            "policy": policy.file_pattern,
            "retention_days": policy.retention_days,
            "archive_reason": "automatic_policy"
        }

        archive_item = ArchiveItem(
            original_path=str(original_path),
            archive_path=str(archive_path),
            file_type=original_path.suffix,
            original_size=original_size,
            compressed_size=compressed_size,
            created_date=created_date,
            archived_date=datetime.now(),
            compression_ratio=compressed_size / original_size if original_size > 0 else 1.0,
            metadata=metadata
        )

        with sqlite3.connect(self.metadata_db) as conn:
            conn.execute("""
                INSERT INTO archived_items
                (original_path, archive_path, file_type, original_size, compressed_size,
                 created_date, archived_date, compression_ratio, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                archive_item.original_path,
                archive_item.archive_path,
                archive_item.file_type,
                archive_item.original_size,
                archive_item.compressed_size,
                archive_item.created_date.isoformat(),
                archive_item.archived_date.isoformat(),
                archive_item.compression_ratio,
                json.dumps(archive_item.metadata)
            ))

    def search_archives(self,
                       query: Optional[str] = None,
                       file_type: Optional[str] = None,
                       date_from: Optional[datetime] = None,
                       date_to: Optional[datetime] = None,
                       limit: int = 50) -> List[ArchiveItem]:
        """
        Search archived items with various filters.

        Args:
            query: Text to search in file paths
            file_type: File extension to filter by
            date_from: Minimum creation date
            date_to: Maximum creation date
            limit: Maximum number of results

        Returns:
            List of matching archive items
        """
        sql = "SELECT * FROM archived_items WHERE 1=1"
        params = []

        if query:
            sql += " AND (original_path LIKE ? OR archive_path LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])

        if file_type:
            sql += " AND file_type = ?"
            params.append(file_type)

        if date_from:
            sql += " AND created_date >= ?"
            params.append(date_from.isoformat())

        if date_to:
            sql += " AND created_date <= ?"
            params.append(date_to.isoformat())

        sql += " ORDER BY archived_date DESC LIMIT ?"
        params.append(limit)

        results = []
        with sqlite3.connect(self.metadata_db) as conn:
            conn.row_factory = sqlite3.Row
            for row in conn.execute(sql, params):
                results.append(ArchiveItem(
                    original_path=row['original_path'],
                    archive_path=row['archive_path'],
                    file_type=row['file_type'],
                    original_size=row['original_size'],
                    compressed_size=row['compressed_size'],
                    created_date=datetime.fromisoformat(row['created_date']),
                    archived_date=datetime.fromisoformat(row['archived_date']),
                    compression_ratio=row['compression_ratio'],
                    metadata=json.loads(row['metadata'])
                ))

        return results

    def retrieve_from_archive(self, archive_path: str, destination: Optional[Path] = None) -> Path:
        """
        Retrieve a file from the archive.

        Args:
            archive_path: Path to the archived file
            destination: Where to restore the file (defaults to original location)

        Returns:
            Path where the file was restored
        """
        archive_file = Path(archive_path)
        if not archive_file.exists():
            raise FileNotFoundError(f"Archive file not found: {archive_path}")

        if destination is None:
            # Restore to a 'restored' directory to avoid conflicts
            destination = self.base_path / "restored" / archive_file.name

        destination.parent.mkdir(parents=True, exist_ok=True)

        # Handle compressed files
        if archive_file.suffix == '.gz':
            with gzip.open(archive_file, 'rb') as f_in:
                with open(destination, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(archive_file, destination)

        return destination

    def generate_storage_metrics(self) -> StorageMetrics:
        """Generate comprehensive storage metrics and recommendations."""
        total_files = 0
        total_size = 0
        compressed_files = 0
        compression_savings = 0
        old_files_count = 0
        old_files_size = 0

        cutoff_date = datetime.now() - timedelta(days=30)

        # Analyze active files
        for directory in ["reports", "logs"]:
            dir_path = self.base_path / directory
            if not dir_path.exists():
                continue

            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    file_stat = file_path.stat()
                    file_size = file_stat.st_size
                    file_date = datetime.fromtimestamp(file_stat.st_mtime)

                    total_files += 1
                    total_size += file_size

                    if self._is_compressed(file_path):
                        compressed_files += 1
                        # Estimate original size (assume 70% compression)
                        estimated_original = file_size / 0.3
                        compression_savings += estimated_original - file_size

                    if file_date < cutoff_date:
                        old_files_count += 1
                        old_files_size += file_size

        # Generate recommendations
        recommendations = []

        if old_files_count > 10:
            recommendations.append(f"Consider archiving {old_files_count} old files to save {old_files_size/(1024*1024):.1f} MB")

        if compression_savings < total_size * 0.1:
            recommendations.append("Enable compression for older files to save storage space")

        if total_size > 1024*1024*1024:  # > 1GB
            recommendations.append("Large storage usage detected - consider more aggressive retention policies")

        if compressed_files / total_files < 0.2 and total_files > 50:
            recommendations.append("Low compression rate - review file types and compression policies")

        return StorageMetrics(
            total_files=total_files,
            total_size_mb=total_size / (1024 * 1024),
            compressed_files=compressed_files,
            compression_savings_mb=compression_savings / (1024 * 1024),
            old_files_count=old_files_count,
            old_files_size_mb=old_files_size / (1024 * 1024),
            recommendations=recommendations
        )

    def create_archive_bundle(self, file_patterns: List[str], bundle_name: str) -> Path:
        """
        Create a compressed bundle of files matching patterns.

        Args:
            file_patterns: List of glob patterns to match
            bundle_name: Name for the archive bundle

        Returns:
            Path to the created bundle
        """
        bundle_path = self.archive_base / f"{bundle_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

        with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            files_added = 0

            for pattern in file_patterns:
                for file_path in self.base_path.rglob(pattern):
                    if file_path.is_file():
                        # Add file to zip with relative path
                        arcname = file_path.relative_to(self.base_path)
                        zipf.write(file_path, arcname)
                        files_added += 1

        if files_added == 0:
            bundle_path.unlink()  # Remove empty archive
            raise ValueError(f"No files found matching patterns: {file_patterns}")

        return bundle_path

    def schedule_cleanup(self, cron_schedule: str = "0 2 * * *") -> str:
        """
        Generate a cron job configuration for automated cleanup.

        Args:
            cron_schedule: Cron schedule expression (default: daily at 2 AM)

        Returns:
            Cron job configuration string
        """
        script_path = Path(__file__).parent.parent.parent.parent / "tools" / "archive_cleanup.py"

        cron_command = f"{cron_schedule} cd {self.base_path.parent} && python {script_path} --apply 2>&1 | logger -t archive_cleanup"

        return cron_command

    def export_configuration(self, output_path: Optional[Path] = None) -> str:
        """Export archive configuration to JSON file."""
        if output_path is None:
            output_path = self.base_path / "archive_config.json"

        config = {
            "base_path": str(self.base_path),
            "archive_base": str(self.archive_base),
            "policies": [asdict(policy) for policy in self.policies],
            "generated_at": datetime.now().isoformat()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        return str(output_path)

    def import_configuration(self, config_path: Path):
        """Import archive configuration from JSON file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.policies = [
            RetentionPolicy(**policy_data)
            for policy_data in config.get('policies', [])
        ]