"""
Structured Logging Module for GoNoGo

Provides structured JSON logging for test execution with environment-aware
configuration and GDPR-compliant sanitization.

Related to: EP-00006 Test Logging and Reporting
User Story: US-00022 Structured logging system for test execution
"""

from .logger import StructuredLogger, LogLevel, LogEntry, get_logger, setup_logging
from .config import LoggingConfig, EnvironmentMode
from .sanitizer import LogSanitizer, SanitizationLevel
from .formatters import JSONFormatter, TestFormatter, TableFormatter, SummaryFormatter
from .pytest_integration import PytestLoggingPlugin, setup_pytest_logging

__all__ = [
    "StructuredLogger",
    "LogLevel",
    "LogEntry",
    "get_logger",
    "setup_logging",
    "LoggingConfig",
    "EnvironmentMode",
    "LogSanitizer",
    "SanitizationLevel",
    "JSONFormatter",
    "TestFormatter",
    "TableFormatter",
    "SummaryFormatter",
    "PytestLoggingPlugin",
    "setup_pytest_logging"
]

# Version and metadata
__version__ = "1.0.0"
__author__ = "GoNoGo Team"
__description__ = "Structured logging system for test execution and development workflow"