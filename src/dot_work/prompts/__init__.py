"""Prompt management utilities for dot-work."""

from __future__ import annotations

from pathlib import Path

from dot_work.prompts.agent_orchestrator import (
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
from dot_work.prompts.canonical import (
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


def get_bundled_prompts_dir() -> Path:
    """Get the directory containing bundled prompt assets.

    Returns:
        Path to the bundled prompts directory (assets/prompts/).
    """
    # __file__ is src/dot_work/prompts/__init__.py
    # Go up to src/dot_work/ then down to assets/prompts/
    return Path(__file__).parent.parent / "assets" / "prompts"
