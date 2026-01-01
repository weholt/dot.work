"""OpenCode environment adapter for subagents.

This module provides the adapter for OpenCode agents,
which use .opencode/agent/ directory with YAML frontmatter.
"""

from __future__ import annotations

from pathlib import Path

from dot_work.subagents.environments.base import SubagentEnvironmentAdapter
from dot_work.subagents.models import SubagentConfig


class OpenCodeAdapter(SubagentEnvironmentAdapter):
    """Adapter for OpenCode agents.

    OpenCode agents are defined in .opencode/agent/ directory
    with YAML frontmatter containing:
    - name, description (required)
    - mode (primary, subagent, all)
    - model (provider/model-id format)
    - temperature (0.0-2.0)
    - maxSteps
    - tools (boolean map or wildcards)
    - permissions (granular bash rules)

    Reference: OpenCode documentation
    """

    # Tool name mapping: canonical -> OpenCode
    # OpenCode uses lowercase tool names
    TOOL_MAP: dict[str, str] = {
        "Read": "read",
        "Write": "write",
        "Edit": "edit",
        "Bash": "bash",
        "Grep": "grep",
        "Glob": "glob",
        "WebFetch": "webfetch",
        "WebSearch": "websearch",
    }

    DEFAULT_TARGET: str = ".opencode/agent"

    def get_target_path(self, project_root: Path) -> Path:
        """Get the target directory for OpenCode agents.

        Args:
            project_root: Project root directory.

        Returns:
            Path to .opencode/agent/ directory.
        """
        return project_root / ".opencode" / "agent"

    def generate_native(self, config: SubagentConfig) -> str:
        """Generate OpenCode native agent file content.

        Args:
            config: SubagentConfig with full configuration.

        Returns:
            OpenCode agent file content as string.
        """
        lines = ["---"]

        # Required fields
        lines.append(f"name: {config.name}")
        lines.append(f"description: {config.description}")

        # Mode (optional)
        if config.mode:
            lines.append(f"mode: {config.mode}")

        # Model (optional)
        if config.model:
            lines.append(f"model: {config.model}")

        # Temperature (optional)
        if config.temperature is not None:
            lines.append(f"temperature: {config.temperature}")

        # Max steps (optional)
        if config.max_steps is not None:
            lines.append(f"maxSteps: {config.max_steps}")

        # Tools (optional) - OpenCode uses boolean map
        if config.tools:
            lines.append("tools:")
            for tool in config.tools:
                mapped_tool = self.TOOL_MAP.get(tool, tool)
                lines.append(f"  {mapped_tool}: true")

        # Permissions (optional)
        if config.permissions:
            lines.append("permissions:")
            for key, value in config.permissions.items():
                if isinstance(value, bool):
                    lines.append(f"  {key}: {str(value).lower()}")
                elif isinstance(value, dict):
                    lines.append(f"  {key}:")
                    for k, v in value.items():
                        lines.append(f"    {k}: {v}")
                else:
                    lines.append(f"  {key}: {value}")

        lines.append("---")
        lines.append("")
        lines.append(config.prompt)

        return "\n".join(lines)

    def parse_native(self, content: str) -> SubagentConfig:
        """Parse OpenCode native agent file content.

        Args:
            content: OpenCode agent file content.

        Returns:
            SubagentConfig object.
        """
        from dot_work.subagents.parser import SUBAGENT_PARSER

        return SUBAGENT_PARSER._parse_native_content(content, "opencode", Path("<opencode>"))

    def map_tools(self, tools: list[str] | None) -> dict[str, bool] | None:
        """Map canonical tool names to OpenCode format.

        OpenCode uses a boolean map for tools.

        Args:
            tools: List of canonical tool names.

        Returns:
            Dict of tool name to boolean, or None.
        """
        if tools is None:
            return None

        return {self.TOOL_MAP.get(t, t.lower()): True for t in tools}

    def generate_filename(self, config: SubagentConfig) -> str:
        """Generate filename for OpenCode agent file.

        Args:
            config: SubagentConfig object.

        Returns:
            Filename with .md extension.
        """
        return f"{config.name}.md"
