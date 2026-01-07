"""Windsurf AI editor environment adapter for subagents.

This module provides the adapter for Windsurf (Codeium) Cascade agents,
which use AGENTS.md files with plain markdown format (no frontmatter).
"""

from __future__ import annotations

from pathlib import Path

from dot_work.subagents.environments.base import SubagentEnvironmentAdapter
from dot_work.subagents.models import SubagentConfig


class WindsurfAdapter(SubagentEnvironmentAdapter):
    """Adapter for Windsurf Cascade AGENTS.md files.

    Windsurf uses plain markdown AGENTS.md files with NO frontmatter.
    The files are automatically discovered based on their location:
    - Root AGENTS.md: Global instructions for entire project
    - Subdirectory AGENTS.md: Directory-specific instructions

    The file name is case-insensitive (AGENTS.md or agents.md).

    Reference: https://docs.windsurf.com/windsurf/cascade/agents-md
    """

    # Tool name mapping: canonical -> Windsurf
    # Windsurf Cascade uses standard tool names
    TOOL_MAP: dict[str, str] = {
        "Read": "Read",
        "Write": "Write",
        "Edit": "Edit",
        "Bash": "Bash",
        "Grep": "Grep",
        "Glob": "Glob",
        "WebFetch": "WebFetch",
        "WebSearch": "WebSearch",
    }

    DEFAULT_TARGET: str = "AGENTS.md"

    def get_target_path(self, project_root: Path) -> Path:
        """Get the target path for Windsurf AGENTS.md file.

        Note: For Windsurf, AGENTS.md can be placed at any directory level.
        This returns the root project path where AGENTS.md would be placed.

        Args:
            project_root: Project root directory.

        Returns:
            Path to AGENTS.md in project root.
        """
        return project_root / "AGENTS.md"

    def generate_native(self, config: SubagentConfig) -> str:
        """Generate Windsurf AGENTS.md file content.

        Windsurf uses PLAIN MARKDOWN with NO frontmatter.
        The content is just the prompt/instructions.

        Args:
            config: SubagentConfig with full configuration.

        Returns:
            AGENTS.md file content as plain markdown string.
        """
        # Windsurf AGENTS.md has no frontmatter, just plain markdown
        # We can add a header if description is available
        content = []

        # Optional: Add title/description as header
        if config.description:
            content.append(f"# {config.description}")
            content.append("")

        # Add the prompt/instructions
        if config.prompt:
            content.append(config.prompt)

        return "\n".join(content)

    def parse_native(self, content: str) -> SubagentConfig:
        """Parse Windsurf AGENTS.md file content.

        Since AGENTS.md has no frontmatter, we extract content
        and create a SubagentConfig with reasonable defaults.

        Args:
            content: AGENTS.md file content (plain markdown).

        Returns:
            SubagentConfig object.
        """
        from dot_work.subagents.parser import SUBAGENT_PARSER

        return SUBAGENT_PARSER._parse_native_content(content, "windsurf", Path("<windsurf>"))

    def generate_filename(self, config: SubagentConfig) -> str:
        """Generate filename for Windsurf AGENTS.md file.

        Note: Windsurf AGENTS.md has a fixed name, not based on config.

        Args:
            config: SubagentConfig object (ignored).

        Returns:
            Always returns "AGENTS.md".
        """
        return "AGENTS.md"

    def map_tools(self, tools: list[str] | None) -> list[str] | dict[str, bool] | None:
        """Map canonical tool names to Windsurf format.

        Windsurf uses standard tool names, so we pass through as-is.

        Args:
            tools: List of canonical tool names.

        Returns:
            List of tool names (unchanged).
        """
        if tools is None:
            return None

        # Windsurf uses standard names, return as-is
        return tools
