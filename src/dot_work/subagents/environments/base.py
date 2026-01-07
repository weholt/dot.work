"""Base environment adapter for subagent handling.

This module provides the abstract base class for environment-specific
subagent adapters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from dot_work.subagents.models import SubagentConfig


class SubagentEnvironmentAdapter(ABC):
    """Base class for environment-specific subagent handling.

    Each environment (Claude Code, OpenCode, GitHub Copilot) has
    its own file format, tool names, and configuration options.
    Adapters handle conversion between canonical and native formats.
    """

    # Tool name mapping: canonical -> environment-specific
    TOOL_MAP: dict[str, str] = {}

    # Default target directory for subagent files
    DEFAULT_TARGET: str = ""

    @abstractmethod
    def get_target_path(self, project_root: Path) -> Path:
        """Get the target directory for subagent files.

        Args:
            project_root: Project root directory.

        Returns:
            Path to the target directory.
        """

    @abstractmethod
    def generate_native(self, config: SubagentConfig) -> str:
        """Generate native subagent file content.

        Args:
            config: SubagentConfig with full configuration.

        Returns:
            Native subagent file content as string.
        """

    @abstractmethod
    def parse_native(self, content: str) -> SubagentConfig:
        """Parse native subagent file content.

        Args:
            content: Native subagent file content.

        Returns:
            SubagentConfig object.
        """

    def map_tools(self, tools: list[str] | None) -> list[str] | dict[str, bool] | None:
        """Map canonical tool names to environment-specific format.

        Args:
            tools: List of canonical tool names.

        Returns:
            Environment-specific tool format (list, dict, or None).
        """
        if tools is None:
            return None

        return [self.TOOL_MAP.get(t, t) for t in tools]

    def generate_filename(self, config: SubagentConfig) -> str:
        """Generate filename for subagent file.

        Args:
            config: SubagentConfig object.

        Returns:
            Filename (without extension).
        """
        return config.name


class SimpleAdapter(SubagentEnvironmentAdapter):
    """Simple adapter for environments with minimal configuration.

    This is a basic implementation for environments that don't need
    complex tool mapping or configuration transformation.
    """

    TOOL_MAP: dict[str, str] = {}
    DEFAULT_TARGET: str = "."

    def get_target_path(self, project_root: Path) -> Path:
        """Get the target directory for subagent files."""
        return project_root / self.DEFAULT_TARGET

    def generate_native(self, config: SubagentConfig) -> str:
        """Generate native subagent file content.

        Default implementation generates basic YAML frontmatter.
        """
        lines = ["---"]

        # Basic fields
        lines.append(f"name: {config.name}")
        lines.append(f"description: {config.description}")

        # Tools
        if config.tools:
            lines.append("tools:")
            for tool in config.tools:
                mapped_tool = self.TOOL_MAP.get(tool, tool)
                lines.append(f"  - {mapped_tool}")

        lines.append("---")
        lines.append("")
        lines.append(config.prompt)

        return "\n".join(lines)

    def parse_native(self, content: str) -> SubagentConfig:
        """Parse native subagent file content.

        Default implementation delegates to SubagentParser.
        """
        from dot_work.subagents.parser import SUBAGENT_PARSER

        # Create a temporary file path for parsing
        # The actual file doesn't matter, we just need the parser to work
        return SUBAGENT_PARSER._parse_native_content(content, "generic", Path("<native>"))
