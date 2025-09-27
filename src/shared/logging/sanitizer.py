"""
GDPR-Compliant Log Sanitization for GoNoGo

Provides sanitization patterns and utilities for removing or anonymizing
personal data from log entries in compliance with GDPR requirements.
"""

import hashlib
import re
from enum import Enum
from typing import Any, Dict, Pattern


class SanitizationLevel(Enum):
    """Levels of log sanitization."""

    NONE = "none"  # No sanitization (development only)
    BASIC = "basic"  # Basic PII removal
    STRICT = "strict"  # Comprehensive sanitization
    PARANOID = "paranoid"  # Maximum sanitization


class LogSanitizer:
    """GDPR-compliant log sanitization utility."""

    def __init__(self, level: SanitizationLevel = SanitizationLevel.BASIC):
        """Initialize sanitizer with specified level."""
        self.level = level
        self._patterns = self._compile_patterns()
        self._replacements = self._get_replacements()

    def _compile_patterns(self) -> Dict[str, Pattern[str]]:
        """Compile regex patterns for different types of personal data."""
        patterns = {}

        if self.level == SanitizationLevel.NONE:
            return patterns

        # Email addresses
        patterns["email"] = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            re.IGNORECASE,
        )

        # IP addresses (IPv4 and IPv6)
        patterns["ipv4"] = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
        patterns["ipv6"] = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b")

        if self.level in [
            SanitizationLevel.STRICT,
            SanitizationLevel.PARANOID,
        ]:
            # Phone numbers (various formats)
            patterns["phone"] = re.compile(
                r"(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}",
                re.IGNORECASE,
            )

            # Social security numbers
            patterns["ssn"] = re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b")

            # Credit card numbers (basic pattern)
            patterns["credit_card"] = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")

            # User paths (containing usernames)
            patterns["user_path"] = re.compile(r"/(?:home|users?)/[^/\s]+", re.IGNORECASE)

        if self.level == SanitizationLevel.PARANOID:
            # Names (common patterns - be careful with false positives)
            patterns["names"] = re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b")

            # Session tokens and API keys
            patterns["tokens"] = re.compile(r"\b[A-Za-z0-9]{20,}\b")

            # URLs with sensitive parameters
            patterns["sensitive_urls"] = re.compile(
                r"https?://[^\s]*(?:token|key|password|auth)=[^\s&]*",
                re.IGNORECASE,
            )

        return patterns

    def _get_replacements(self) -> Dict[str, str]:
        """Get replacement strings for different data types."""
        if self.level == SanitizationLevel.NONE:
            return {}

        return {
            "email": "[EMAIL_REDACTED]",
            "ipv4": "[IP_REDACTED]",
            "ipv6": "[IP_REDACTED]",
            "phone": "[PHONE_REDACTED]",
            "ssn": "[SSN_REDACTED]",
            "credit_card": "[CARD_REDACTED]",
            "user_path": "/[USER_PATH_REDACTED]",
            "names": "[NAME_REDACTED]",
            "tokens": "[TOKEN_REDACTED]",
            "sensitive_urls": "[SENSITIVE_URL_REDACTED]",
        }

    def sanitize_text(self, text: str) -> str:
        """Sanitize a text string according to the configured level."""
        if self.level == SanitizationLevel.NONE:
            return text

        sanitized = text
        for pattern_name, pattern in self._patterns.items():
            replacement = self._replacements.get(pattern_name, "[REDACTED]")
            sanitized = pattern.sub(replacement, sanitized)

        return sanitized

    def sanitize_log_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize a complete log entry dictionary."""
        if self.level == SanitizationLevel.NONE:
            return log_entry

        sanitized_entry = {}

        for key, value in log_entry.items():
            if isinstance(value, str):
                sanitized_entry[key] = self.sanitize_text(value)
            elif isinstance(value, dict):
                sanitized_entry[key] = self.sanitize_log_entry(value)
            elif isinstance(value, list):
                sanitized_entry[key] = [self.sanitize_text(item) if isinstance(item, str) else item for item in value]
            else:
                sanitized_entry[key] = value

        return sanitized_entry

    def anonymize_ip(self, ip_address: str) -> str:
        """Anonymize an IP address by hashing."""
        if self.level == SanitizationLevel.NONE:
            return ip_address

        # Simple anonymization - hash with salt
        salt = "gonogo_logging_salt"
        return hashlib.sha256(f"{ip_address}{salt}".encode()).hexdigest()[:12]

    def should_exclude_field(self, field_name: str) -> bool:
        """Determine if a field should be completely excluded."""
        if self.level == SanitizationLevel.NONE:
            return False

        sensitive_fields = {
            "user_id",
            "email",
            "password",
            "token",
            "session_id",
            "api_key",
            "auth_header",
            "personal_data",
        }

        if self.level == SanitizationLevel.PARANOID:
            sensitive_fields.update({"user_agent", "referer", "remote_addr", "client_ip"})

        return field_name.lower() in sensitive_fields

    def get_sanitization_info(self) -> Dict[str, Any]:
        """Get information about current sanitization configuration."""
        return {
            "level": self.level.value,
            "patterns_active": list(self._patterns.keys()),
            "replacements": self._replacements,
            "description": self._get_level_description(),
        }

    def _get_level_description(self) -> str:
        """Get description of current sanitization level."""
        descriptions = {
            SanitizationLevel.NONE: ("No sanitization - full logging (development only)"),
            SanitizationLevel.BASIC: "Basic PII removal (emails, IPs)",
            SanitizationLevel.STRICT: ("Comprehensive sanitization (PII, paths, tokens)"),
            SanitizationLevel.PARANOID: ("Maximum sanitization (aggressive pattern matching)"),
        }
        return descriptions.get(self.level, "Unknown level")
