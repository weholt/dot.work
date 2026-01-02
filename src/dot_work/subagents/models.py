"""Data models for Subagents.

This module defines the data structures for subagents/custom agents
that can be deployed across multiple AI coding environments (Claude Code,
OpenCode, GitHub Copilot).

Subagents are specialized AI assistants with tool/permission configurations
that can be invoked on-demand for specific tasks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SubagentMetadata:
    """Lightweight metadata for discovery/listing.

    Attributes:
        name: Required subagent name, 1-64 chars, lowercase + hyphens only.
            No leading/trailing/consecutive hyphens.
        description: Required description, 1-1024 chars, non-empty.

    Raises:
        ValueError: If validation constraints are violated in __post_init__.
    """

    name: str
    description: str

    # Compiled regex for name validation
    NAME_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")

    def __post_init__(self) -> None:
        """Validate subagent metadata constraints."""
        # Validate name
        if not isinstance(self.name, str):
            raise ValueError("Subagent name must be a string")

        if not (1 <= len(self.name) <= 64):
            raise ValueError(f"Subagent name must be 1-64 characters, got {len(self.name)} chars")

        if not self.NAME_PATTERN.match(self.name):
            raise ValueError(
                f"Subagent name must contain only lowercase letters, numbers, and hyphens; "
                f"cannot start/end with hyphen or have consecutive hyphens. Got: {self.name!r}"
            )

        # Validate description
        if not isinstance(self.description, str):
            raise ValueError("Subagent description must be a string")

        stripped_description = self.description.strip()
        if not stripped_description:
            raise ValueError("Subagent description cannot be empty")

        if not (1 <= len(self.description) <= 1024):
            raise ValueError(
                f"Subagent description must be 1-1024 characters, got {len(self.description)} chars"
            )


@dataclass
class SubagentConfig:
    """Full subagent configuration.

    This class represents a complete subagent configuration with all
    platform-specific fields. Not all fields apply to all platforms.

    Attributes:
        name: Subagent name.
        description: Description of when to use this agent.
        prompt: System prompt (markdown body).
        tools: List of tool names (None = inherit all).
        model: Model selection (platform-specific format).
        permission_mode: Claude Code permission mode (default, acceptEdits, bypassPermissions, plan).
        permissions: OpenCode granular bash rules.
        mode: OpenCode mode (primary, subagent, all).
        temperature: OpenCode temperature setting.
        max_steps: OpenCode max steps setting.
        skills: Claude Code auto-load skills list.
        target: GitHub Copilot target (vscode, github-copilot).
        infer: GitHub Copilot auto-selection.
        mcp_servers: GitHub Copilot MCP server config (org/enterprise only).
        source_file: Source file path for this config.
    """

    name: str
    description: str
    prompt: str

    # Tool access (environment-specific interpretation)
    tools: list[str] | None = None

    # Model selection
    model: str | None = None

    # Permissions (Claude Code / OpenCode)
    permission_mode: str | None = None
    permissions: dict[str, Any] | None = None

    # OpenCode-specific
    mode: str | None = None
    temperature: float | None = None
    max_steps: int | None = None

    # Claude Code-specific
    skills: list[str] | None = None

    # GitHub Copilot-specific
    target: str | None = None
    infer: bool | None = None
    mcp_servers: dict[str, Any] | None = None

    # Metadata
    source_file: Path | None = None


@dataclass
class SubagentEnvironmentConfig:
    """Environment-specific configuration overrides.

    Attributes:
        target: Target directory for subagent files (e.g., ".claude/agents/").
        model: Model override for this environment.
        permission_mode: Permission mode override.
        tools: Tools list override.
        mode: Mode override (OpenCode).
        temperature: Temperature override (OpenCode).
        max_steps: Max steps override (OpenCode).
        skills: Skills list override (Claude Code).
        infer: Infer flag override (GitHub Copilot).
    """

    target: str
    model: str | None = None
    permission_mode: str | None = None
    tools: list[str] | None = None
    mode: str | None = None
    temperature: float | None = None
    max_steps: int | None = None
    skills: list[str] | None = None
    infer: bool | None = None


@dataclass
class CanonicalSubagent:
    """Canonical subagent with multi-environment support.

    A canonical subagent is defined once with common configuration
    and environment-specific overrides, then can be deployed to
    multiple AI coding platforms.

    Attributes:
        meta: SubagentMetadata with name and description.
        config: SubagentConfig with full configuration.
        environments: Dict of environment name to SubagentEnvironmentConfig.
        source_file: Source file path for this canonical subagent.

    Example:
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="code-reviewer",
                description="Expert code reviewer for quality and security",
            ),
            config=SubagentConfig(
                name="code-reviewer",
                description="Expert code reviewer for quality and security",
                prompt="You are a senior code reviewer...",
                tools=["Read", "Grep", "Glob", "Bash"],
            ),
            environments={
                "claude": SubagentEnvironmentConfig(
                    target=".claude/agents/",
                    model="sonnet",
                    permission_mode="default",
                ),
                "opencode": SubagentEnvironmentConfig(
                    target=".opencode/agent/",
                    mode="subagent",
                    temperature=0.1,
                ),
            },
        )
    """

    meta: SubagentMetadata
    config: SubagentConfig
    environments: dict[str, SubagentEnvironmentConfig] = field(default_factory=dict)
    source_file: Path | None = None

    def __post_init__(self) -> None:
        """Validate that metadata name matches config name."""
        if self.meta.name != self.config.name:
            raise ValueError(
                f"Subagent metadata name {self.meta.name!r} must match config name {self.config.name!r}"
            )

        # Ensure source_file is a Path object if provided
        if self.source_file is not None and not isinstance(self.source_file, Path):
            object.__setattr__(self, "source_file", Path(self.source_file))
