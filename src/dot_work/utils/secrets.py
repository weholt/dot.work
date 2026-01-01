"""Secrets management and validation utilities.

This module provides functions for validating and managing API keys and tokens
to prevent secrets leakage and ensure proper handling of sensitive credentials.

## Design Rationale

API keys and tokens require special handling to prevent security breaches:
- Format validation catches configuration errors early
- Logging interception prevents accidental secrets exposure
- Clear error messages help developers fix configuration issues
- Integration with sanitization ensures secrets never appear in user output

Reference: Issue SEC-007@security-review-2026
"""

import os
import logging
import re
from typing import Literal

from dot_work.utils.sanitization import sanitize_log_message

logger = logging.getLogger(__name__)

# Secret type identifiers
SecretType = Literal["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GITHUB_TOKEN"]


class SecretValidationError(ValueError):
    """Raised when a secret fails validation."""

    def __init__(self, secret_type: SecretType, reason: str) -> None:
        self.secret_type = secret_type
        self.reason = reason
        message = f"Invalid {secret_type}: {reason}"
        super().__init__(message)


# Format patterns for API key validation
SECRET_PATTERNS: dict[SecretType, re.Pattern[str]] = {
    "OPENAI_API_KEY": re.compile(r"^sk-[a-zA-Z0-9]{48,}$"),  # sk- followed by 48+ alphanumeric chars
    "ANTHROPIC_API_KEY": re.compile(r"^sk-ant-[a-zA-Z0-9_-]{95,}$"),  # sk-ant-api03- followed by 95+ chars
    "GITHUB_TOKEN": re.compile(r"^(ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36}|ghu_[a-zA-Z0-9]{36}|ghs_[a-zA-Z0-9]{36}|ghr_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})$"),  # Various GitHub token formats
}


def get_secret(secret_type: SecretType, env_var: str | None = None) -> str:
    """
    Retrieve and validate a secret from environment variables.

    This function validates the secret format and ensures it's not accidentally
    logged. Raises SecretValidationError if the secret is missing or invalid.

    Args:
        secret_type: Type of secret (e.g., "OPENAI_API_KEY")
        env_var: Environment variable name (defaults to secret_type)

    Returns:
        The validated secret value

    Raises:
        SecretValidationError: If the secret is missing, empty, or invalid format

    Examples:
        >>> get_secret("OPENAI_API_KEY")
        'sk-abc123...'

        >>> get_secret("GITHUB_TOKEN", "CUSTOM_GITHUB_TOKEN")
        'ghp_xyz123...'
    """
    if env_var is None:
        env_var = secret_type

    value = os.environ.get(env_var)

    if not value:
        raise SecretValidationError(
            secret_type, f"Environment variable {env_var} is not set or empty"
        )

    # Validate format
    validate_secret_format(secret_type, value)

    logger.debug(f"Successfully loaded and validated {secret_type} from {env_var}")

    return value


def validate_secret_format(secret_type: SecretType, value: str) -> None:
    """
    Validate the format of a secret value.

    Checks if the secret matches the expected pattern for its type.
    This catches configuration errors early (e.g., using a GitHub token
    as an OpenAI API key).

    Args:
        secret_type: Type of secret to validate
        value: The secret value to validate

    Raises:
        SecretValidationError: If the format doesn't match the expected pattern

    Examples:
        >>> validate_secret_format("OPENAI_API_KEY", "sk-abc123...")
        # Passes silently

        >>> validate_secret_format("OPENAI_API_KEY", "invalid")
        # Raises SecretValidationError
    """
    pattern = SECRET_PATTERNS.get(secret_type)

    if pattern is None:
        logger.warning(f"No validation pattern for secret type: {secret_type}")
        return

    if not pattern.match(value):
        # Don't log the actual value - only whether it matches
        logger.warning(f"Secret format validation failed for {secret_type}")

        raise SecretValidationError(
            secret_type,
            f"Invalid format. Expected format: {pattern.pattern}",
        )


def get_safe_log_message(message: str) -> str:
    """
    Sanitize a log message to remove secrets.

    Wrapper around sanitize_log_message() that specifically targets API keys
    and tokens. Use this when logging anything that might contain secrets.

    Args:
        message: The log message to sanitize

    Returns:
        Sanitized log message with secrets redacted

    Examples:
        >>> get_safe_log_message("API key: sk-abc123...")
        'API key: [key]'
    """
    return sanitize_log_message(message)


def require_secrets(*secret_types: SecretType) -> dict[str, str]:
    """
    Require multiple secrets to be present and valid.

    Convenience function for validating multiple secrets at once.

    Args:
        *secret_types: One or more secret type names

    Returns:
        Dictionary mapping secret types to their validated values

    Raises:
        SecretValidationError: If any secret is missing or invalid

    Examples:
        >>> require_secrets("OPENAI_API_KEY", "ANTHROPIC_API_KEY")
        {'OPENAI_API_KEY': 'sk-...', 'ANTHROPIC_API_KEY': 'sk-ant-...'}
    """
    result: dict[str, str] = {}
    errors: list[str] = []

    for secret_type in secret_types:
        try:
            result[secret_type] = get_secret(secret_type)
        except SecretValidationError as e:
            errors.append(str(e))

    if errors:
        raise SecretValidationError(
            secret_types[0], f"Multiple secret errors: {'; '.join(errors)}"
        )

    return result


def mask_secret(value: str, reveal_last: int = 4) -> str:
    """
    Mask a secret value for display purposes.

    Shows only the last N characters of the secret, useful for confirmation
    prompts or debugging (never use in production logs).

    Args:
        value: The secret value to mask
        reveal_last: Number of characters to reveal at the end

    Returns:
        Masked secret with asterisks

    Examples:
        >>> mask_secret("sk-abc123xyz")
        'sk-*********xyz'
    """
    if len(value) <= reveal_last:
        return "*" * len(value)

    return value[:-reveal_last] + "*" * reveal_last + value[-reveal_last:]
