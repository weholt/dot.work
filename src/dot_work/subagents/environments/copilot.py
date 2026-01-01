"""GitHub Copilot environment adapter for subagents.

This module provides the adapter for GitHub Copilot custom agents,
which use .github/agents/ directory with YAML frontmatter.
"""

from __future__ import annotations

from pathlib import Path

from dot_work.subagents.environments.base import SubagentEnvironmentAdapter
from dot_work.subagents.models import SubagentConfig


class CopilotAdapter(SubagentEnvironmentAdapter):
    """Adapter for GitHub Copilot custom agents.

    GitHub Copilot agents are defined in .github/agents/ directory
    with YAML frontmatter containing:
    - name, description (required)
    - target (vscode, github-copilot)
    - infer (boolean for auto-selection)
    - tools (list with optional aliases)
    - mcpServers (MCP server config, org/enterprise only)

    Reference: GitHub Copilot documentation
    """

    # Tool name mapping: canonical -> GitHub Copilot
    # Copilot uses lowercase tool names with some differences
    TOOL_MAP: dict[str, str] = {
        "Read": "read",
        "Write": "edit",
        "Edit": "edit",
        "Bash": "execute",
        "Grep": "search",
        "Glob": "search",
        "WebFetch": "web",
        "WebSearch": "web",
    }

    DEFAULT_TARGET: str = ".github/agents"

    def get_target_path(self, project_root: Path) -> Path:
        """Get the target directory for GitHub Copilot agents.

        Args:
            project_root: Project root directory.

        Returns:
            Path to .github/agents/ directory.
        """
        return project_root / ".github" / "agents"

    def generate_native(self, config: SubagentConfig) -> str:
        """Generate GitHub Copilot native agent file content.

        Args:
            config: SubagentConfig with full configuration.

        Returns:
            GitHub Copilot agent file content as string.
        """
        lines = ["---"]

        # Required fields
        lines.append(f"name: {config.name}")
        lines.append(f"description: {config.description}")

        # Target (optional)
        if config.target:
            lines.append(f"target: {config.target}")

        # Infer (optional)
        if config.infer is not None:
            lines.append(f"infer: {str(config.infer).lower()}")

        # Tools (optional)
        if config.tools:
            lines.append("tools:")
            for tool in config.tools:
                mapped_tool = self.TOOL_MAP.get(tool, tool.lower())
                lines.append(f"  - {mapped_tool}")

        # MCP servers (optional, org/enterprise only)
        if config.mcp_servers:
            lines.append("mcpServers:")
            for server_name, server_config in config.mcp_servers.items():
                lines.append(f"  {server_name}:")
                if isinstance(server_config, dict):
                    for key, value in server_config.items():
                        lines.append(f"    {key}: {value}")
                else:
                    lines.append(f"    {server_config}")

        lines.append("---")
        lines.append("")
        lines.append(config.prompt)

        return "\n".join(lines)

    def parse_native(self, content: str) -> SubagentConfig:
        """Parse GitHub Copilot native agent file content.

        Args:
            content: GitHub Copilot agent file content.

        Returns:
            SubagentConfig object.
        """
        from dot_work.subagents.parser import SUBAGENT_PARSER

        return SUBAGENT_PARSER._parse_native_content(content, "copilot", Path("<copilot>"))

    def map_tools(self, tools: list[str] | None) -> list[str] | None:
        """Map canonical tool names to GitHub Copilot format.

        Args:
            tools: List of canonical tool names.

        Returns:
            List of GitHub Copilot tool names (lowercase).
        """
        if tools is None:
            return None

        return [self.TOOL_MAP.get(t, t.lower()) for t in tools]

    def generate_filename(self, config: SubagentConfig) -> str:
        """Generate filename for GitHub Copilot agent file.

        Args:
            config: SubagentConfig object.

        Returns:
            Filename with .md extension.
        """
        return f"{config.name}.md"
