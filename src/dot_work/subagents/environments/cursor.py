"""Cursor AI editor environment adapter for subagents.

This module provides the adapter for Cursor AI custom agents,
which use .cursor/rules/ directory with .mdc files and YAML frontmatter.
"""

from __future__ import annotations

from pathlib import Path

from dot_work.subagents.environments.base import SubagentEnvironmentAdapter
from dot_work.subagents.models import SubagentConfig


class CursorAdapter(SubagentEnvironmentAdapter):
    """Adapter for Cursor AI custom agents.

    Cursor agents are defined in .cursor/rules/ directory
    with .mdc files using YAML frontmatter:
    - description (required, under 120 chars)
    - globs (optional, file pattern matching)

    The body contains markdown instructions for the AI.

    Reference: https://cursor.com/docs/context/rules
    """

    # Tool name mapping: canonical -> Cursor
    # Cursor uses similar tool names to Claude Code
    TOOL_MAP: dict[str, str] = {
        "Read": "read",
        "Write": "write",
        "Edit": "edit",
        "Bash": "bash",
        "Grep": "grep",
        "Glob": "glob",
        "WebFetch": "web_fetch",
        "WebSearch": "web_search",
    }

    DEFAULT_TARGET: str = ".cursor/rules"

    def get_target_path(self, project_root: Path) -> Path:
        """Get the target directory for Cursor agent files.

        Args:
            project_root: Project root directory.

        Returns:
            Path to .cursor/rules/ directory.
        """
        return project_root / ".cursor" / "rules"

    def generate_native(self, config: SubagentConfig) -> str:
        """Generate Cursor .mdc agent file content.

        Args:
            config: SubagentConfig with full configuration.

        Returns:
            Cursor .mdc file content as string.
        """
        lines = ["---"]

        # Required: description (under 120 chars for AI clarity)
        # Truncate if necessary
        description = config.description or ""
        if len(description) > 120:
            description = description[:117] + "..."
        lines.append(f"description: {description}")

        # Optional: globs for file pattern matching
        # Default to ["**/*"] for global application if not specified
        globs = getattr(config, "globs", None) or ["**/*"]
        if globs:
            lines.append("globs:")
            for glob_pattern in globs:
                lines.append(f"  - {glob_pattern}")

        lines.append("---")
        lines.append("")
        lines.append(config.prompt)

        return "\n".join(lines)

    def parse_native(self, content: str) -> SubagentConfig:
        """Parse Cursor .mdc native agent file content.

        Args:
            content: Cursor .mdc agent file content.

        Returns:
            SubagentConfig object.
        """
        from dot_work.subagents.parser import SUBAGENT_PARSER

        return SUBAGENT_PARSER._parse_native_content(content, "cursor", Path("<cursor>"))

    def generate_filename(self, config: SubagentConfig) -> str:
        """Generate filename for Cursor agent file.

        Args:
            config: SubagentConfig object.

        Returns:
            Filename with .mdc extension.
        """
        return f"{config.name}.mdc"
