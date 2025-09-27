"""
Structured Logger for GoNoGo Test System

Core logging functionality with JSON formatting, environment awareness,
and GDPR-compliant sanitization.
"""

import json
import logging
import logging.handlers
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from .config import EnvironmentMode, LoggingConfig, LogLevel
from .sanitizer import LogSanitizer, SanitizationLevel


@dataclass
class LogEntry:
    """Structured log entry with required fields."""

    # Core fields (always present)
    timestamp: str
    level: str
    message: str

    # Test execution fields
    test_id: Optional[str] = None
    test_name: Optional[str] = None
    test_status: Optional[str] = None  # started, passed, failed, skipped
    duration_ms: Optional[float] = None

    # Environment context
    environment: Optional[str] = None
    session_id: Optional[str] = None

    # Metadata (optional)
    metadata: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    tags: Optional[List[str]] = None

    @classmethod
    def create(
        cls,
        level: LogLevel,
        message: str,
        test_id: Optional[str] = None,
        test_name: Optional[str] = None,
        test_status: Optional[str] = None,
        duration_ms: Optional[float] = None,
        environment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> "LogEntry":
        """Create a new log entry with current timestamp."""
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level.value,
            message=message,
            test_id=test_id,
            test_name=test_name,
            test_status=test_status,
            duration_ms=duration_ms,
            environment=environment,
            session_id=str(uuid.uuid4())[:8],  # Short session ID
            metadata=metadata,
            stack_trace=stack_trace,
            tags=tags or [],
        )


class StructuredLogger:
    """Main structured logger for test execution."""

    def __init__(self, config: Optional[LoggingConfig] = None):
        """Initialize the structured logger."""
        self.config = config or LoggingConfig.from_environment()
        self.sanitizer = self._create_sanitizer()
        self._lock = Lock()
        self._session_id = str(uuid.uuid4())

        # Set up file logging
        self._setup_file_logging()

        # Set up in-memory buffer for testing
        self._log_buffer: List[LogEntry] = []
        self._max_buffer_size = self.config.buffer_size

    def _create_sanitizer(self) -> LogSanitizer:
        """Create sanitizer based on configuration."""
        if not self.config.sanitize_personal_data:
            return LogSanitizer(SanitizationLevel.NONE)
        elif self.config.environment == EnvironmentMode.DEVELOPMENT:
            return LogSanitizer(SanitizationLevel.BASIC)
        elif self.config.environment == EnvironmentMode.TESTING:
            return LogSanitizer(SanitizationLevel.STRICT)
        else:  # PRODUCTION
            return LogSanitizer(SanitizationLevel.PARANOID)

    def _setup_file_logging(self) -> None:
        """Set up file-based logging with rotation."""
        # Ensure log directory exists
        self.config.ensure_log_directory_exists()

        # Create rotating file handler
        log_file_path = self.config.get_log_file_path()
        self._file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file_path,
            maxBytes=self.config.max_file_size_mb * 1024 * 1024,
            backupCount=self.config.max_files,
            encoding="utf-8",
        )

        # Set up formatter
        formatter = logging.Formatter("%(message)s")  # We'll format JSON ourselves
        self._file_handler.setFormatter(formatter)

        # Create logger
        self._file_logger = logging.getLogger(f"gonogo_structured_{self._session_id}")
        self._file_logger.setLevel(
            getattr(logging, self.config.log_level.value.upper())
        )
        self._file_logger.addHandler(self._file_handler)
        self._file_logger.propagate = False

    def log(
        self,
        level: LogLevel,
        message: str,
        test_id: Optional[str] = None,
        test_name: Optional[str] = None,
        test_status: Optional[str] = None,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> LogEntry:
        """Log a structured entry."""

        # Create log entry
        entry = LogEntry.create(
            level=level,
            message=message,
            test_id=test_id,
            test_name=test_name,
            test_status=test_status,
            duration_ms=duration_ms,
            environment=self.config.environment.value,
            metadata=metadata,
            stack_trace=stack_trace if self.config.include_stack_traces else None,
            tags=tags,
        )

        # Convert to dictionary
        entry_dict = asdict(entry)

        # Remove None values for cleaner JSON
        entry_dict = {k: v for k, v in entry_dict.items() if v is not None}

        # Apply sanitization
        entry_dict = self.sanitizer.sanitize_log_entry(entry_dict)

        # Create sanitized entry for buffer (GDPR compliance)
        sanitized_entry = LogEntry(
            timestamp=entry.timestamp,
            level=entry.level,
            message=self.sanitizer.sanitize_text(entry.message),
            test_id=entry.test_id,
            test_name=entry.test_name,
            test_status=entry.test_status,
            duration_ms=entry.duration_ms,
            environment=entry.environment,
            session_id=entry.session_id,
            metadata=(
                self.sanitizer.sanitize_log_entry(entry.metadata or {})
                if entry.metadata
                else None
            ),
            stack_trace=entry.stack_trace,
            tags=entry.tags,
        )

        # Add sanitized entry to buffer
        with self._lock:
            self._log_buffer.append(sanitized_entry)
            if len(self._log_buffer) > self._max_buffer_size:
                self._log_buffer.pop(0)  # Remove oldest entry

        # Write to file
        json_line = json.dumps(entry_dict, separators=(",", ":"))
        self._file_logger.log(getattr(logging, level.value.upper()), json_line)

        return entry

    def debug(self, message: str, **kwargs) -> LogEntry:
        """Log debug message."""
        return self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> LogEntry:
        """Log info message."""
        return self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> LogEntry:
        """Log warning message."""
        return self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> LogEntry:
        """Log error message."""
        return self.log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> LogEntry:
        """Log critical message."""
        return self.log(LogLevel.CRITICAL, message, **kwargs)

    # Test-specific convenience methods
    def test_started(self, test_id: str, test_name: str, **kwargs) -> LogEntry:
        """Log test start."""
        return self.info(
            f"Test started: {test_name}",
            test_id=test_id,
            test_name=test_name,
            test_status="started",
            tags=["test_lifecycle"],
            **kwargs,
        )

    def test_passed(
        self, test_id: str, test_name: str, duration_ms: float, **kwargs
    ) -> LogEntry:
        """Log test pass."""
        return self.info(
            f"Test passed: {test_name}",
            test_id=test_id,
            test_name=test_name,
            test_status="passed",
            duration_ms=duration_ms,
            tags=["test_lifecycle", "success"],
            **kwargs,
        )

    def test_failed(
        self,
        test_id: str,
        test_name: str,
        duration_ms: float,
        error_message: str,
        stack_trace: Optional[str] = None,
        **kwargs,
    ) -> LogEntry:
        """Log test failure."""
        return self.error(
            f"Test failed: {test_name} - {error_message}",
            test_id=test_id,
            test_name=test_name,
            test_status="failed",
            duration_ms=duration_ms,
            stack_trace=stack_trace,
            tags=["test_lifecycle", "failure"],
            **kwargs,
        )

    def test_skipped(
        self, test_id: str, test_name: str, reason: str, **kwargs
    ) -> LogEntry:
        """Log test skip."""
        return self.warning(
            f"Test skipped: {test_name} - {reason}",
            test_id=test_id,
            test_name=test_name,
            test_status="skipped",
            metadata={"skip_reason": reason},
            tags=["test_lifecycle", "skipped"],
            **kwargs,
        )

    # Buffer and query methods
    def get_recent_logs(self, count: int = 100) -> List[LogEntry]:
        """Get recent log entries from buffer."""
        with self._lock:
            return (
                self._log_buffer[-count:]
                if count < len(self._log_buffer)
                else self._log_buffer.copy()
            )

    def get_logs_for_test(self, test_id: str) -> List[LogEntry]:
        """Get all log entries for a specific test."""
        with self._lock:
            return [entry for entry in self._log_buffer if entry.test_id == test_id]

    def get_failed_test_logs(self) -> List[LogEntry]:
        """Get log entries for failed tests."""
        with self._lock:
            return [
                entry for entry in self._log_buffer if entry.test_status == "failed"
            ]

    def clear_buffer(self) -> None:
        """Clear the in-memory log buffer."""
        with self._lock:
            self._log_buffer.clear()

    def flush(self) -> None:
        """Flush any pending log entries to file."""
        if hasattr(self._file_handler, "flush"):
            self._file_handler.flush()

    def close(self) -> None:
        """Close the logger and clean up resources."""
        self.flush()
        if self._file_handler:
            self._file_handler.close()
            self._file_logger.removeHandler(self._file_handler)

    def get_config_info(self) -> Dict[str, Any]:
        """Get current configuration information."""
        return {
            "config": self.config.to_dict(),
            "sanitizer": self.sanitizer.get_sanitization_info(),
            "session_id": self._session_id,
            "buffer_size": len(self._log_buffer),
            "log_file": str(self.config.get_log_file_path()),
        }


# Global logger instance
_global_logger: Optional[StructuredLogger] = None


def get_logger(config: Optional[LoggingConfig] = None) -> StructuredLogger:
    """Get the global structured logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = StructuredLogger(config)
    return _global_logger


def setup_logging(config: Optional[LoggingConfig] = None) -> StructuredLogger:
    """Set up logging and return the logger instance."""
    global _global_logger
    _global_logger = StructuredLogger(config)
    return _global_logger
