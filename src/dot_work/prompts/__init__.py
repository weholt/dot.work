"""Prompt management utilities for dot-work."""

from .canonical import (
    CanonicalPrompt,
    CanonicalPromptError,
    CanonicalPromptParser,
    CanonicalPromptValidator,
    EnvironmentConfig,
    ValidationError,
    extract_environment_file,
    generate_environment_prompt,
    parse_canonical_prompt,
    validate_canonical_prompt,
)

__all__ = [
    "CanonicalPrompt",
    "CanonicalPromptError",
    "CanonicalPromptParser",
    "CanonicalPromptValidator",
    "EnvironmentConfig",
    "ValidationError",
    "extract_environment_file",
    "generate_environment_prompt",
    "parse_canonical_prompt",
    "validate_canonical_prompt",
]
