"""Validation utilities for repo-agent instruction files.

This module provides functions to validate instruction markdown files,
ensuring they contain required frontmatter fields and valid configuration
before running the agent.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import frontmatter

from .core import RepoAgentError

# Required top-level frontmatter fields
REQUIRED_FIELDS = {
    "repo_url",
    "model",
}

# Required fields in the tool configuration block
TOOL_REQUIRED_FIELDS = {
    "name",
    "entrypoint",
}


def validate_instructions(path: Path) -> None:
    """Validate an instruction file's frontmatter configuration.

    Checks that all required fields are present, tool configuration is valid,
    strategy is a recognized value, and authentication is configured.

    Args:
        path: Path to the markdown instruction file to validate.

    Raises:
        RepoAgentError: If validation fails due to missing required fields,
            invalid configuration, or other validation errors.
    """
    post = frontmatter.load(str(path))
    meta: Mapping[str, Any] = post.metadata or {}

    # Required top-level keys
    missing = [k for k in REQUIRED_FIELDS if k not in meta]
    if missing:
        raise RepoAgentError(f"Missing required fields in frontmatter: {missing}")

    # Tool block
    if "tool" not in meta:
        raise RepoAgentError("tool block is missing from frontmatter")

    tool_meta = meta.get("tool", {})
    if not isinstance(tool_meta, dict):
        raise RepoAgentError("tool must be a mapping in frontmatter")

    missing_tool = [k for k in TOOL_REQUIRED_FIELDS if k not in tool_meta]
    if missing_tool:
        raise RepoAgentError(f"Missing required tool fields: {missing_tool}")

    # Strategy
    strategy = meta.get("strategy") or meta.get("opencode_strategy") or "agentic"
    if strategy not in {"agentic", "direct"}:
        raise RepoAgentError("strategy must be 'agentic' or 'direct'")

    # Dockerfile existence (optional check)
    dockerfile = meta.get("dockerfile")
    if dockerfile:
        if not (path.parent / dockerfile).exists():
            raise RepoAgentError(f"Dockerfile not found at: {dockerfile}")

    # Authentication check (soft)
    if "github_token" not in meta and "github_token_env" not in meta and not meta.get("use_ssh"):
        # Not a fatal error but warn
        raise RepoAgentError(
            "Authentication not configured: provide github_token, github_token_env, or set use_ssh: true"
        )
