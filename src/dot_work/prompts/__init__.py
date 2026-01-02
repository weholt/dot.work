"""Prompt management utilities for dot-work."""

from .agent_orchestrator import (
    DEFAULT_MAX_CYCLES,
    DEFAULT_STATE_PATH,
    MAX_CYCLES_BEFORE_ABORT,
    classify_error,
    format_cycle_report,
    format_progress_report,
    log_error,
    read_state,
    write_state,
)
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
    # FEAT-029: Agent orchestrator exports
    "OrchestratorState",
    "read_state",
    "write_state",
    "format_progress_report",
    "format_cycle_report",
    "classify_error",
    "log_error",
    "DEFAULT_STATE_PATH",
    "MAX_CYCLES_BEFORE_ABORT",
    "DEFAULT_MAX_CYCLES",
]
