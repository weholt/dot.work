"""Error message sanitization utilities.

This module provides functions for sanitizing error messages to prevent
information disclosure in user-facing output.

## Design Rationale

Error messages often contain sensitive information like:
- File paths (revealing directory structure)
- API keys, tokens, passwords
- Internal implementation details
- Database schemas or queries

For non-verbose user output, we sanitize these details while logging
the full error server-side for debugging.

Reference: Issue SEC-004@security-review-2026
"""

import logging
import re

logger = logging.getLogger(__name__)

# Patterns that should be redacted from user-facing error messages
# Order matters: more specific patterns should come before general ones
SENSITIVE_PATTERNS = [
    # Database connection strings (most specific - check first)
    r"(postgresql|mysql|sqlite)://[^\s]+",
    # API keys with sk- prefix (OpenAI, Stripe, etc.)
    r"sk-[a-zA-Z0-9_-]{20,}",
    r"sk-ant-[a-zA-Z0-9_-]{20,}",
    # GitHub tokens (all variants) - more permissive pattern
    r"gh[pou]_[a-zA-Z0-9]{36}",
    r"github_pat_[a-zA-Z0-9_]{82}",
    # AWS keys
    r"AKIA[0-9A-Z]{16}",
    # Email addresses (before general path matching)
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    # Credentials and secrets - match with optional space after separator
    r"password[=:]\s*\S+",
    r"token[=:]\s*\S+",
    r"secret[=:]\s*\S+",
    r"api[_-]?key[=:]\s*\S+",
    r"auth[=:]\s*\S+",
    r"key[=:]\s*\S+",
    # Generic GitHub token prefix followed by many characters
    r"gh[pou]_[a-zA-Z0-9_-]{10,}",
    # File paths (absolute and relative) - check last as they match many things
    r"[A-Z]:\\[\w\\\-._]+",  # Windows paths
    r"/[\w/\-._]+",  # Unix paths
    # Internal implementation details
    r"File .+? line \d+",
    r"at 0x[0-9a-fA-F]+",  # Memory addresses
]


def sanitize_error_message(error: Exception | str) -> str:
    """
    Sanitize an exception or error message for user-facing output.

    Removes sensitive information like file paths, credentials, and
    implementation details while preserving the core error semantics.

    Args:
        error: Exception object or error message string

    Returns:
        Sanitized error message safe for user display

    Examples:
        >>> sanitize_error_message("Failed to open /home/user/.ssh/id_rsa")
        'Failed to open [path]'
        >>> sanitize_error_message("DB connection failed: postgresql://user:pass@host/db")
        'DB connection failed: [connection string]'
    """
    if isinstance(error, Exception):
        message = str(error)
    else:
        message = error

    # Log the full error server-side for debugging
    logger.debug(f"Full error (sanitized for user): {message}")

    sanitized = message

    # Apply sanitization patterns
    for pattern in SENSITIVE_PATTERNS:
        sanitized = re.sub(
            pattern,
            _replacement_for_pattern(pattern),
            sanitized,
            flags=re.IGNORECASE,
        )

    # Fallback for any remaining sensitive-looking content
    if _looks_sensitive(sanitized):
        sanitized = _generic_message(sanitized)

    return sanitized


def _replacement_for_pattern(pattern: str) -> str:
    """Generate appropriate replacement text for a pattern."""
    pattern_lower = pattern.lower()

    # Match pattern ordering from SENSITIVE_PATTERNS
    if "postgresql" in pattern_lower or "mysql" in pattern_lower or "sqlite" in pattern_lower:
        return "[connection string]"
    elif "sk-" in pattern or "sk-ant" in pattern:
        return "[api key]"
    elif (
        "ghp_" in pattern_lower
        or "gho_" in pattern_lower
        or "ghu_" in pattern_lower
        or "ghs_" in pattern_lower
        or "ghr_" in pattern_lower
        or "github_pat_" in pattern_lower
    ):
        return "[token]"
    elif "AKIA" in pattern:
        return "[key]"
    elif "@" in pattern and "." in pattern:  # Email
        return "[email]"
    elif "password" in pattern_lower:
        return "[password]"
    elif "secret" in pattern_lower:
        return "[secret]"
    elif "token" in pattern_lower:
        return "[token]"
    elif "api" in pattern_lower:
        return "[key]"
    elif "auth" in pattern_lower:
        return "[auth]"
    elif "key" in pattern_lower:
        return "[key]"
    elif "/" in pattern or "\\" in pattern:  # File path
        return "[path]"
    else:
        return "[redacted]"


def _looks_sensitive(message: str) -> bool:
    """Check if message still looks like it contains sensitive info."""
    sensitive_indicators = [
        "/" in message and len(message.split("/")) > 2,  # Likely a file path
        "\\" in message and len(message.split("\\")) > 2,  # Windows path
        ":=" in message or "=" in message,  # Might be key=value
        "0x" in message.lower(),  # Memory address
        message.count(".") > 2 and "@" in message,  # Email-like
    ]
    return any(sensitive_indicators)


def _generic_message(message: str) -> str:
    """Generate a generic error message preserving error type."""
    # Extract common error types
    if "not found" in message.lower():
        return "Resource not found"
    elif "permission" in message.lower() or "denied" in message.lower():
        return "Permission denied"
    elif "connection" in message.lower():
        return "Connection failed"
    elif "invalid" in message.lower():
        return "Invalid input"
    else:
        return "An error occurred"


def sanitize_log_message(message: str) -> str:
    """
    Sanitize log message by removing sensitive information.

    This is the original function from git/utils.py, maintained here
    for backward compatibility. New code should use sanitize_error_message().

    Args:
        message: Log message to sanitize

    Returns:
        Sanitized log message
    """
    sanitized = message
    # Use all patterns for comprehensive sanitization
    for pattern in SENSITIVE_PATTERNS:
        # For patterns with = or :, replace the value portion
        if "=" in pattern or ":" in pattern:
            sanitized = re.sub(
                pattern,
                lambda m: m.group(0).split("=")[0].split(":")[0] + "=***",
                sanitized,
                flags=re.IGNORECASE,
            )
        else:
            # For patterns without separator (GitHub tokens, API keys, etc.)
            sanitized = re.sub(
                pattern,
                "***",
                sanitized,
                flags=re.IGNORECASE,
            )

    return sanitized
