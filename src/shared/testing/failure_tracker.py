"""
Test Failure Tracking and Pattern Analysis System

This module provides comprehensive test failure tracking, categorization,
and pattern analysis to improve test reliability and debugging efficiency.

Related to: US-00025 Test failure tracking and reporting
Parent Epic: EP-00006 Test Logging and Reporting
"""

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class FailureCategory(Enum):
    """Categories for test failure classification."""

    ASSERTION_ERROR = "assertion_error"
    IMPORT_ERROR = "import_error"
    TIMEOUT_ERROR = "timeout_error"
    NETWORK_ERROR = "network_error"
    DATABASE_ERROR = "database_error"
    CONFIGURATION_ERROR = "configuration_error"
    ENVIRONMENT_ERROR = "environment_error"
    DEPENDENCY_ERROR = "dependency_error"
    UNICODE_ERROR = "unicode_error"
    PERMISSION_ERROR = "permission_error"
    UNKNOWN_ERROR = "unknown_error"


class FailureSeverity(Enum):
    """Severity levels for test failures."""

    CRITICAL = "critical"  # Blocks release
    HIGH = "high"  # Affects core functionality
    MEDIUM = "medium"  # Affects secondary features
    LOW = "low"  # Minor issues
    FLAKY = "flaky"  # Intermittent failures


@dataclass
class TestFailure:
    """Represents a single test failure with full context."""

    __test__ = False  # Tell pytest this is not a test class

    id: Optional[int] = None
    test_id: str = ""
    test_name: str = ""
    test_file: str = ""
    failure_message: str = ""
    stack_trace: str = ""
    category: FailureCategory = FailureCategory.UNKNOWN_ERROR
    severity: FailureSeverity = FailureSeverity.MEDIUM
    error_hash: str = ""
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    occurrence_count: int = 1
    environment_info: str = ""
    coverage_info: str = ""
    execution_mode: str = ""
    session_id: str = ""
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Generate error hash and set timestamps."""
        if not self.error_hash:
            self.error_hash = self._generate_error_hash()
        if not self.first_seen:
            self.first_seen = datetime.now(UTC)
        if not self.last_seen:
            self.last_seen = datetime.now(UTC)
        if self.metadata is None:
            self.metadata = {}

    def _generate_error_hash(self) -> str:
        """Generate unique hash for error pattern matching."""
        # Normalize error message for consistent hashing
        normalized_msg = re.sub(r"\d+", "<NUM>", self.failure_message)
        normalized_msg = re.sub(r"0x[0-9a-fA-F]+", "<HEX>", normalized_msg)
        normalized_msg = re.sub(r"/[^/\s]+/", "<PATH>/", normalized_msg)

        hash_content = f"{self.test_name}:{normalized_msg}:{self.category.value}"
        return hashlib.sha256(hash_content.encode()).hexdigest()[:12]


@dataclass
class FailurePattern:
    """Represents a pattern in test failures for analysis."""

    pattern_id: str
    description: str
    occurrences: int
    affected_tests: List[str]
    category: FailureCategory
    severity: FailureSeverity
    first_occurrence: datetime
    last_occurrence: datetime
    trend: str  # "increasing", "decreasing", "stable"
    impact_score: float


@dataclass
class FailureStatistics:
    """Statistical analysis of test failures."""

    total_failures: int
    unique_failures: int
    failure_rate: float
    most_common_category: FailureCategory
    flaky_test_count: int
    critical_failure_count: int
    time_period: str
    trend_analysis: Dict[str, Any]


class FailureTracker:
    """Main class for tracking and analyzing test failures."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize failure tracker with SQLite database."""
        if db_path is None:
            db_path = Path("quality/logs/test_failures.db")

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS test_failures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    test_file TEXT NOT NULL,
                    failure_message TEXT NOT NULL,
                    stack_trace TEXT,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    error_hash TEXT NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    occurrence_count INTEGER DEFAULT 1,
                    environment_info TEXT,
                    coverage_info TEXT,
                    execution_mode TEXT,
                    session_id TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_error_hash ON test_failures(error_hash);
                CREATE INDEX IF NOT EXISTS idx_test_name ON test_failures(test_name);
                CREATE INDEX IF NOT EXISTS idx_category ON test_failures(category);
                CREATE INDEX IF NOT EXISTS idx_last_seen ON test_failures(last_seen);

                CREATE TABLE IF NOT EXISTS failure_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    occurrences INTEGER DEFAULT 1,
                    affected_tests TEXT NOT NULL,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    first_occurrence TEXT NOT NULL,
                    last_occurrence TEXT NOT NULL,
                    trend TEXT DEFAULT 'stable',
                    impact_score REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_pattern_id ON failure_patterns(pattern_id);
                CREATE INDEX IF NOT EXISTS idx_impact_score ON failure_patterns(impact_score);
            """
            )

    def record_failure(self, failure: TestFailure) -> int:
        """Record a test failure in the database."""
        with sqlite3.connect(self.db_path) as conn:
            # Check if this error pattern already exists
            existing = conn.execute(
                "SELECT id, occurrence_count FROM test_failures WHERE error_hash = ?",
                (failure.error_hash,),
            ).fetchone()

            if existing:
                # Update existing failure record
                failure_id, count = existing
                new_count = count + 1
                conn.execute(
                    """
                    UPDATE test_failures
                    SET occurrence_count = ?, last_seen = ?, session_id = ?,
                        execution_mode = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (
                        new_count,
                        failure.last_seen.isoformat(),
                        failure.session_id,
                        failure.execution_mode,
                        failure_id,
                    ),
                )
                return failure_id
            else:
                # Insert new failure record
                result = conn.execute(
                    """
                    INSERT INTO test_failures (
                        test_id, test_name, test_file, failure_message, stack_trace,
                        category, severity, error_hash, first_seen, last_seen,
                        occurrence_count, environment_info, coverage_info,
                        execution_mode, session_id, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        failure.test_id,
                        failure.test_name,
                        failure.test_file,
                        failure.failure_message,
                        failure.stack_trace,
                        failure.category.value,
                        failure.severity.value,
                        failure.error_hash,
                        failure.first_seen.isoformat(),
                        failure.last_seen.isoformat(),
                        failure.occurrence_count,
                        failure.environment_info,
                        failure.coverage_info,
                        failure.execution_mode,
                        failure.session_id,
                        json.dumps(failure.metadata),
                    ),
                )
                return result.lastrowid

    def categorize_failure(self, error_message: str, stack_trace: str) -> FailureCategory:
        """Automatically categorize failure based on error patterns."""
        error_text = f"{error_message} {stack_trace}".lower()

        # Pattern matching for automatic categorization
        patterns = {
            FailureCategory.ASSERTION_ERROR: [
                "assertionerror",
                "assert",
                "expected",
                "actual",
            ],
            FailureCategory.IMPORT_ERROR: [
                "importerror",
                "modulenotfounderror",
                "no module named",
            ],
            FailureCategory.TIMEOUT_ERROR: ["timeout", "timed out", "timeouterror"],
            FailureCategory.NETWORK_ERROR: [
                "connectionerror",
                "network",
                "socket",
                "dns",
            ],
            FailureCategory.DATABASE_ERROR: [
                "database",
                "sql",
                "sqlite",
                "postgresql",
                "connection refused",
            ],
            FailureCategory.CONFIGURATION_ERROR: [
                "config",
                "configuration",
                "setting",
                "environment variable",
            ],
            FailureCategory.UNICODE_ERROR: [
                "unicodeencodeerror",
                "unicodedecodeerror",
                "charmap",
                "codec",
            ],
            FailureCategory.PERMISSION_ERROR: [
                "permissionerror",
                "access denied",
                "permission denied",
            ],
            FailureCategory.DEPENDENCY_ERROR: [
                "dependency",
                "version",
                "compatibility",
                "requirement",
            ],
        }

        for category, keywords in patterns.items():
            if any(keyword in error_text for keyword in keywords):
                return category

        return FailureCategory.UNKNOWN_ERROR

    def determine_severity(self, failure: TestFailure) -> FailureSeverity:
        """Determine failure severity based on various factors."""
        # Critical indicators
        critical_patterns = [
            "segmentation fault",
            "core dumped",
            "fatal error",
            "system exit",
            "abort",
            "critical",
        ]

        # High severity indicators
        high_patterns = [
            "database",
            "security",
            "authentication",
            "authorization",
            "gdpr",
            "privacy",
            "data loss",
        ]

        error_text = f"{failure.failure_message} {failure.stack_trace}".lower()

        if any(pattern in error_text for pattern in critical_patterns):
            return FailureSeverity.CRITICAL

        if any(pattern in error_text for pattern in high_patterns):
            return FailureSeverity.HIGH

        # Check for flaky tests (multiple occurrences with intermittent success)
        if failure.occurrence_count > 3:
            return FailureSeverity.FLAKY

        return FailureSeverity.MEDIUM

    def get_failure_statistics(self, days: int = 30) -> FailureStatistics:
        """Get statistical analysis of failures over specified period."""
        since_date = (datetime.now(UTC) - timedelta(days=days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # Total and unique failures
            total_failures = (
                conn.execute(
                    "SELECT SUM(occurrence_count) FROM test_failures WHERE last_seen >= ?",
                    (since_date,),
                ).fetchone()[0]
                or 0
            )

            unique_failures = (
                conn.execute(
                    "SELECT COUNT(*) FROM test_failures WHERE last_seen >= ?",
                    (since_date,),
                ).fetchone()[0]
                or 0
            )

            # Most common category
            category_result = conn.execute(
                """
                SELECT category, SUM(occurrence_count) as count
                FROM test_failures WHERE last_seen >= ?
                GROUP BY category ORDER BY count DESC LIMIT 1
            """,
                (since_date,),
            ).fetchone()

            most_common_category = FailureCategory.UNKNOWN_ERROR
            if category_result:
                most_common_category = FailureCategory(category_result[0])

            # Flaky and critical counts
            flaky_count = (
                conn.execute(
                    "SELECT COUNT(*) FROM test_failures WHERE severity = 'flaky' AND last_seen >= ?",
                    (since_date,),
                ).fetchone()[0]
                or 0
            )

            critical_count = (
                conn.execute(
                    "SELECT COUNT(*) FROM test_failures WHERE severity = 'critical' AND last_seen >= ?",
                    (since_date,),
                ).fetchone()[0]
                or 0
            )

            # Calculate failure rate (simplified)
            total_tests = (
                conn.execute(
                    "SELECT COUNT(DISTINCT test_name) FROM test_failures WHERE last_seen >= ?",
                    (since_date,),
                ).fetchone()[0]
                or 1
            )

            failure_rate = (unique_failures / total_tests) * 100 if total_tests > 0 else 0

        return FailureStatistics(
            total_failures=total_failures,
            unique_failures=unique_failures,
            failure_rate=failure_rate,
            most_common_category=most_common_category,
            flaky_test_count=flaky_count,
            critical_failure_count=critical_count,
            time_period=f"{days} days",
            trend_analysis=self._analyze_trends(days),
        )

    def _analyze_trends(self, days: int) -> Dict[str, Any]:
        """Analyze failure trends over time."""
        with sqlite3.connect(self.db_path) as conn:
            # Weekly failure counts
            weekly_data = conn.execute(
                """
                SELECT
                    date(last_seen, 'weekday 0', '-6 days') as week_start,
                    SUM(occurrence_count) as failures
                FROM test_failures
                WHERE last_seen >= date('now', '-{} days')
                GROUP BY week_start
                ORDER BY week_start
            """.format(days)
            ).fetchall()

        return {
            "weekly_failures": [{"week": w[0], "count": w[1]} for w in weekly_data],
            "trend_direction": self._calculate_trend_direction(weekly_data),
        }

    def _calculate_trend_direction(self, weekly_data: List[Tuple]) -> str:
        """Calculate if failures are trending up, down, or stable."""
        if len(weekly_data) < 2:
            return "insufficient_data"

        recent_avg = sum(w[1] for w in weekly_data[-2:]) / 2
        earlier_avg = (
            sum(w[1] for w in weekly_data[:-2]) / len(weekly_data[:-2]) if len(weekly_data) > 2 else weekly_data[0][1]
        )

        if recent_avg > earlier_avg * 1.2:
            return "increasing"
        elif recent_avg < earlier_avg * 0.8:
            return "decreasing"
        else:
            return "stable"

    def get_top_failing_tests(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get tests with highest failure counts."""
        with sqlite3.connect(self.db_path) as conn:
            results = conn.execute(
                """
                SELECT test_name, test_file, SUM(occurrence_count) as total_failures,
                       category, severity, MAX(last_seen) as last_failure
                FROM test_failures
                GROUP BY test_name
                ORDER BY total_failures DESC
                LIMIT ?
            """,
                (limit,),
            ).fetchall()

        return [
            {
                "test_name": r[0],
                "test_file": r[1],
                "total_failures": r[2],
                "category": r[3],
                "severity": r[4],
                "last_failure": r[5],
            }
            for r in results
        ]

    def detect_patterns(self) -> List[FailurePattern]:
        """Detect patterns in test failures for proactive analysis."""
        patterns = []

        with sqlite3.connect(self.db_path) as conn:
            # Group by error category and analyze patterns
            category_patterns = conn.execute(
                """
                SELECT category, COUNT(*) as occurrences,
                       GROUP_CONCAT(test_name) as affected_tests,
                       MIN(first_seen) as first_occurrence,
                       MAX(last_seen) as last_occurrence
                FROM test_failures
                GROUP BY category
                HAVING occurrences > 1
                ORDER BY occurrences DESC
            """
            ).fetchall()

            for pattern_data in category_patterns:
                category = FailureCategory(pattern_data[0])
                pattern = FailurePattern(
                    pattern_id=f"CAT_{category.value.upper()}",
                    description=f"Multiple {category.value.replace('_', ' ')} failures",
                    occurrences=pattern_data[1],
                    affected_tests=(pattern_data[2].split(",") if pattern_data[2] else []),
                    category=category,
                    severity=FailureSeverity.MEDIUM,
                    first_occurrence=datetime.fromisoformat(pattern_data[3]),
                    last_occurrence=datetime.fromisoformat(pattern_data[4]),
                    trend="stable",
                    impact_score=pattern_data[1] * 0.1,
                )
                patterns.append(pattern)

        return patterns

    def cleanup_old_failures(self, days: int = 90):
        """Clean up old failure records to manage database size."""
        cutoff_date = (datetime.now(UTC) - timedelta(days=days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            deleted_count = conn.execute("DELETE FROM test_failures WHERE last_seen < ?", (cutoff_date,)).rowcount
            conn.execute("DELETE FROM failure_patterns WHERE last_occurrence < ?", (cutoff_date,))

        return deleted_count
