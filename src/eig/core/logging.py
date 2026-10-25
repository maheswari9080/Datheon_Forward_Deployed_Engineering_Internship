"""Structured JSON logging with request correlation IDs and secret scrubbing."""

import json
import logging
import re
import sys
import contextvars
from typing import Any, Dict

# Context variable for tracking request correlation IDs across async tasks
correlation_id_ctx = contextvars.ContextVar("correlation_id", default="SYSTEM")

# Redaction patterns for sensitive enterprise tokens and passwords
SENSITIVE_PATTERNS = [
    (re.compile(r'(?i)(bearer\s+)[a-zA-Z0-9\._\-]+'), r'\1***REDACTED***'),
    (re.compile(r'(?i)(password["\']?\s*[:=]\s*["\'])([^"\']+)'), r'\1***REDACTED***'),
    (re.compile(r'(?i)(secret["\']?\s*[:=]\s*["\'])([^"\']+)'), r'\1***REDACTED***'),
    (re.compile(r'(?i)(api[_-]?key["\']?\s*[:=]\s*["\'])([^"\']+)'), r'\1***REDACTED***'),
]


def scrub_sensitive_data(message: str) -> str:
    """Sanitize secrets, tokens, and credentials from log strings."""
    sanitized = message
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


class StructuredJSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON with correlation IDs and sanitized payloads."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "correlation_id": correlation_id_ctx.get(),
            "message": scrub_sensitive_data(record.getMessage()),
        }

        if record.exc_info:
            log_entry["exception"] = scrub_sensitive_data(self.formatException(record.exc_info))

        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_entry["extra"] = {
                k: scrub_sensitive_data(str(v)) if isinstance(v, str) else v
                for k, v in record.extra.items()
            }

        return json.dumps(log_entry)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure platform-wide structured logging to stdout."""
    logger = logging.getLogger("eig")
    logger.setLevel(level)

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJSONFormatter())
        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = setup_logging()
