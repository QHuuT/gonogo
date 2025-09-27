"""
Logging Configuration for GoNoGo Test System

Provides environment-aware configuration for structured logging with GDPR
compliance.
"""

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class EnvironmentMode(Enum):
    """Environment modes for logging configuration."""

    DEVELOPMENT = "dev"
    TESTING = "test"
    PRODUCTION = "prod"


class LogLevel(Enum):
    """Log levels for structured logging."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LoggingConfig:
    """Configuration class for structured logging."""

    # Environment settings
    environment: EnvironmentMode
    log_level: LogLevel

    # File settings
    log_directory: Path
    log_filename: str
    max_file_size_mb: int
    max_files: int

    # Format settings
    include_metadata: bool
    include_stack_traces: bool
    sanitize_personal_data: bool

    # Performance settings
    buffer_size: int
    flush_interval_seconds: float

    # GDPR settings
    data_retention_days: int
    anonymize_ips: bool
    exclude_user_data: bool

    @classmethod
    def from_environment(cls, env: Optional[str] = None) -> "LoggingConfig":
        """Create configuration based on environment."""
        if env is None:
            env = os.getenv("ENVIRONMENT", "development").lower()

        # Determine environment mode
        if env in ["dev", "development"]:
            environment = EnvironmentMode.DEVELOPMENT
        elif env in ["test", "testing"]:
            environment = EnvironmentMode.TESTING
        elif env in ["prod", "production"]:
            environment = EnvironmentMode.PRODUCTION
        else:
            environment = EnvironmentMode.DEVELOPMENT

        # Base configuration
        base_config = {
            "environment": environment,
            "log_directory": Path("quality/logs"),
            "log_filename": "test_execution.log",
            "max_file_size_mb": 10,
            "max_files": 5,
            "buffer_size": 1000,
            "flush_interval_seconds": 5.0,
            "data_retention_days": 30,
        }

        # Environment-specific configurations
        if environment == EnvironmentMode.DEVELOPMENT:
            return cls(
                **base_config,
                log_level=LogLevel.DEBUG,
                include_metadata=True,
                include_stack_traces=True,
                sanitize_personal_data=False,
                # Full logging for debugging
                anonymize_ips=False,
                exclude_user_data=False,
            )

        elif environment == EnvironmentMode.TESTING:
            return cls(
                **base_config,
                log_level=LogLevel.INFO,
                include_metadata=True,
                include_stack_traces=True,
                sanitize_personal_data=True,
                # Basic sanitization
                anonymize_ips=True,
                exclude_user_data=False,
                log_filename="test_execution_test.log",
            )

        else:  # PRODUCTION
            return cls(
                **base_config,
                log_level=LogLevel.WARNING,
                include_metadata=False,
                include_stack_traces=False,
                sanitize_personal_data=True,
                # Full GDPR compliance
                anonymize_ips=True,
                exclude_user_data=True,
                data_retention_days=7,
                # Shorter retention in prod
                log_filename="test_execution_prod.log",
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "environment": self.environment.value,
            "log_level": self.log_level.value,
            "log_directory": str(self.log_directory),
            "log_filename": self.log_filename,
            "max_file_size_mb": self.max_file_size_mb,
            "max_files": self.max_files,
            "include_metadata": self.include_metadata,
            "include_stack_traces": self.include_stack_traces,
            "sanitize_personal_data": self.sanitize_personal_data,
            "buffer_size": self.buffer_size,
            "flush_interval_seconds": self.flush_interval_seconds,
            "data_retention_days": self.data_retention_days,
            "anonymize_ips": self.anonymize_ips,
            "exclude_user_data": self.exclude_user_data,
        }

    def get_log_file_path(self) -> Path:
        """Get the full path to the log file."""
        return self.log_directory / self.log_filename

    def ensure_log_directory_exists(self) -> None:
        """Ensure the log directory exists."""
        self.log_directory.mkdir(parents=True, exist_ok=True)
