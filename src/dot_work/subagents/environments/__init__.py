"""Environment adapters for subagent deployment.

This module provides environment-specific adapters for generating
and parsing subagent files across different AI coding platforms.
"""

from dot_work.subagents.environments.base import SubagentEnvironmentAdapter
from dot_work.subagents.environments.claude_code import ClaudeCodeAdapter
from dot_work.subagents.environments.copilot import CopilotAdapter
from dot_work.subagents.environments.opencode import OpenCodeAdapter

__all__ = [
    "SubagentEnvironmentAdapter",
    "ClaudeCodeAdapter",
    "OpenCodeAdapter",
    "CopilotAdapter",
]


# Environment registry
_ADAPTERS: dict[str, type[SubagentEnvironmentAdapter]] = {
    "claude": ClaudeCodeAdapter,
    "opencode": OpenCodeAdapter,
    "copilot": CopilotAdapter,
}


def get_adapter(environment: str) -> SubagentEnvironmentAdapter:
    """Get an environment adapter instance.

    Args:
        environment: Environment name (claude, opencode, copilot).

    Returns:
        SubagentEnvironmentAdapter instance.

    Raises:
        ValueError: If environment is not supported.
    """
    adapter_cls = _ADAPTERS.get(environment)
    if not adapter_cls:
        raise ValueError(
            f"Unsupported environment: {environment}. "
            f"Supported: {', '.join(sorted(_ADAPTERS))}"
        )
    return adapter_cls()


def get_supported_environments() -> list[str]:
    """Get list of supported environment names.

    Returns:
        List of environment names.
    """
    return sorted(_ADAPTERS.keys())
