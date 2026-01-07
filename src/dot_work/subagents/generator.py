"""Generator for subagent deployment.

This module provides functionality for generating environment-specific
subagent files from canonical subagent definitions.
"""

from __future__ import annotations

import logging
from pathlib import Path

from dot_work.subagents.environments import get_adapter
from dot_work.subagents.models import (
    CanonicalSubagent,
    SubagentConfig,
)

logger = logging.getLogger(__name__)


class SubagentGenerator:
    """Generator for subagent deployment across environments.

    This class handles conversion of canonical subagents to
    environment-specific native formats.
    """

    def __init__(self) -> None:
        """Initialize the generator."""

    def generate_native(
        self,
        subagent: CanonicalSubagent,
        environment: str,
        project_root: Path | None = None,
    ) -> str:
        """Generate native subagent file content for an environment.

        Args:
            subagent: CanonicalSubagent object.
            environment: Environment name (claude, opencode, copilot).
            project_root: Optional project root for path resolution.

        Returns:
            Native subagent file content as string.

        Raises:
            ValueError: If environment is not supported.
        """
        adapter = get_adapter(environment)

        # Merge base config with environment overrides
        config = self._merge_config(subagent, environment)

        return adapter.generate_native(config)

    def generate_native_file(
        self,
        subagent: CanonicalSubagent,
        environment: str,
        project_root: Path,
        output_path: Path | None = None,
    ) -> Path:
        """Generate and write native subagent file.

        Args:
            subagent: CanonicalSubagent object.
            environment: Environment name (claude, opencode, copilot).
            project_root: Project root directory.
            output_path: Optional output file path. If not provided,
                uses default target path from environment adapter.

        Returns:
            Path to the generated file.

        Raises:
            ValueError: If environment is not supported.
        """
        adapter = get_adapter(environment)

        # Determine output path
        if output_path is None:
            target_dir = adapter.get_target_path(project_root)
            filename = adapter.generate_filename(subagent.config)
            output_path = target_dir / filename

        # Generate content
        content = self.generate_native(subagent, environment, project_root)

        # Create parent directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        output_path.write_text(content, encoding="utf-8")

        return output_path

    def generate_all(
        self,
        subagent: CanonicalSubagent,
        project_root: Path,
    ) -> dict[str, Path]:
        """Generate native files for all configured environments.

        Args:
            subagent: CanonicalSubagent object.
            project_root: Project root directory.

        Returns:
            Dict of environment name to generated file path.
        """
        generated: dict[str, Path] = {}

        for env_name in subagent.environments:
            try:
                path = self.generate_native_file(subagent, env_name, project_root)
                generated[env_name] = path
            except Exception as e:
                # Skip environments that fail to generate
                logger.debug(f"Skipping environment {env_name} for {subagent.meta.name}: {e}")
                continue

        return generated

    def _merge_config(
        self,
        subagent: CanonicalSubagent,
        environment: str,
    ) -> SubagentConfig:
        """Merge base config with environment-specific overrides.

        Args:
            subagent: CanonicalSubagent object.
            environment: Environment name.

        Returns:
            Merged SubagentConfig object.
        """
        base = subagent.config
        env_config = subagent.environments.get(environment)

        if env_config is None:
            return base

        # Create merged config with environment overrides
        return SubagentConfig(
            name=base.name,
            description=base.description,
            prompt=base.prompt,
            tools=env_config.tools if env_config.tools is not None else base.tools,
            model=env_config.model if env_config.model is not None else base.model,
            permission_mode=(
                env_config.permission_mode
                if env_config.permission_mode is not None
                else base.permission_mode
            ),
            permissions=base.permissions,  # Not overridable per env
            mode=env_config.mode if env_config.mode is not None else base.mode,
            temperature=(
                env_config.temperature if env_config.temperature is not None else base.temperature
            ),
            max_steps=env_config.max_steps if env_config.max_steps is not None else base.max_steps,
            skills=env_config.skills if env_config.skills is not None else base.skills,
            target=base.target,  # Not overridable per env (stored in env_config.target)
            infer=env_config.infer if env_config.infer is not None else base.infer,
            mcp_servers=base.mcp_servers,  # Not overridable per env
            source_file=base.source_file,
        )

    def generate_canonical_template(
        self,
        name: str,
        description: str,
        environments: list[str] | None = None,
    ) -> str:
        """Generate a canonical subagent template file.

        Args:
            name: Subagent name.
            description: Subagent description.
            environments: List of environments to include in template.

        Returns:
            Canonical subagent template content.
        """
        if environments is None:
            environments = ["claude", "opencode", "copilot"]

        lines = ["---"]
        lines.append("meta:")
        lines.append(f"  name: {name}")
        lines.append(f"  description: {description}")
        lines.append("")
        lines.append("environments:")

        for env in environments:
            if env == "claude":
                lines.append("  claude:")
                lines.append('    target: ".claude/agents/"')
                lines.append("    model: sonnet")
                lines.append("    permissionMode: default")
            elif env == "opencode":
                lines.append("  opencode:")
                lines.append('    target: ".opencode/agent/"')
                lines.append("    mode: subagent")
                lines.append("    temperature: 0.1")
            elif env == "copilot":
                lines.append("  copilot:")
                lines.append('    target: ".github/agents/"')
                lines.append("    infer: true")
                lines.append("    tools:")
                lines.append("      - read")
                lines.append("      - edit")
                lines.append("      - search")

        lines.append("")
        lines.append("# Common configuration (can be overridden per-environment)")
        lines.append("tools:")
        lines.append("  - Read")
        lines.append("  - Write")
        lines.append("  - Edit")
        lines.append("  - Bash")
        lines.append("  - Grep")
        lines.append("---")
        lines.append("")
        lines.append(f"# {name}")
        lines.append("")
        lines.append(description)
        lines.append("")
        lines.append("## Instructions")
        lines.append("")
        lines.append("Add your subagent instructions here...")

        return "\n".join(lines)


# Singleton instance for efficiency
SUBAGENT_GENERATOR = SubagentGenerator()
