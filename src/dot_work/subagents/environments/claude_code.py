"""Claude Code environment adapter for subagents.

This module provides the adapter for Claude Code subagents,
which use .claude/agents/ directory with YAML frontmatter.
"""

from __future__ import annotations

from pathlib import Path

from dot_work.subagents.environments.base import SubagentEnvironmentAdapter
from dot_work.subagents.models import SubagentConfig


class ClaudeCodeAdapter(SubagentEnvironmentAdapter):
    """Adapter for Claude Code subagents.

    Claude Code subagents are defined in .claude/agents/ directory
    with YAML frontmatter containing:
    - name, description (required)
    - model (sonnet, opus, haiku, inherit)
    - permissionMode (default, acceptEdits, bypassPermissions, plan)
    - tools (comma-separated or list)
    - skills (list of skill names to auto-load)

    Reference: https://github.com/anthropics/claude-code
    """

    # Tool name mapping: canonical -> Claude Code
    # Claude Code uses capitalized tool names
    TOOL_MAP: dict[str, str] = {
        "read": "Read",
        "write": "Write",
        "edit": "Edit",
        "bash": "Bash",
        "grep": "Grep",
        "glob": "Glob",
        "webfetch": "WebFetch",
        "websearch": "WebSearch",
    }

    DEFAULT_TARGET: str = ".claude/agents"

    def get_target_path(self, project_root: Path) -> Path:
        """Get the target directory for Claude Code subagents.

        Args:
            project_root: Project root directory.

        Returns:
            Path to .claude/agents/ directory.
        """
        return project_root / ".claude" / "agents"

    def generate_native(self, config: SubagentConfig) -> str:
        """Generate Claude Code native subagent file content.

        Args:
            config: SubagentConfig with full configuration.

        Returns:
            Claude Code subagent file content as string.
        """
        lines = ["---"]

        # Required fields
        lines.append(f"name: {config.name}")
        lines.append(f"description: {config.description}")

        # Model (optional)
        if config.model:
            lines.append(f"model: {config.model}")

        # Permission mode (optional)
        if config.permission_mode:
            lines.append(f"permissionMode: {config.permission_mode}")

        # Tools (optional)
        if config.tools:
            lines.append("tools:")
            for tool in config.tools:
                mapped_tool = self.TOOL_MAP.get(tool.lower(), tool)
                lines.append(f"  - {mapped_tool}")

        # Skills (optional, Claude Code specific)
        if config.skills:
            lines.append("skills:")
            for skill in config.skills:
                lines.append(f"  - {skill}")

        lines.append("---")
        lines.append("")
        lines.append(config.prompt)

        return "\n".join(lines)

    def parse_native(self, content: str) -> SubagentConfig:
        """Parse Claude Code native subagent file content.

        Args:
            content: Claude Code subagent file content.

        Returns:
            SubagentConfig object.
        """
        from dot_work.subagents.parser import SUBAGENT_PARSER

        return SUBAGENT_PARSER._parse_native_content(content, "claude", Path("<claude>"))

    def map_tools(self, tools: list[str] | None) -> list[str] | None:
        """Map canonical tool names to Claude Code format.

        Args:
            tools: List of canonical tool names.

        Returns:
            List of Claude Code tool names (capitalized).
        """
        if tools is None:
            return None

        return [self.TOOL_MAP.get(t.lower(), t) for t in tools]

    def generate_filename(self, config: SubagentConfig) -> str:
        """Generate filename for Claude Code subagent file.

        Args:
            config: SubagentConfig object.

        Returns:
            Filename with .md extension.
        """
        return f"{config.name}.md"
