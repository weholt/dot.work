"""Prompt management utilities for dot-work."""

from .canonical import (
    CANONICAL_PARSER,
    CANONICAL_VALIDATOR,
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
    "CANONICAL_PARSER",
    "CANONICAL_VALIDATOR",
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
