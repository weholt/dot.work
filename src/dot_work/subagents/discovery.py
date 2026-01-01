"""Discovery of subagent definitions.

This module provides functionality for discovering subagents
from multiple sources (native and canonical).
"""

from __future__ import annotations

from pathlib import Path

from dot_work.subagents.environments import get_adapter
from dot_work.subagents.models import (
    CanonicalSubagent,
    SubagentConfig,
    SubagentMetadata,
)
from dot_work.subagents.parser import SUBAGENT_PARSER


class SubagentDiscovery:
    """Discover subagents from multiple sources.

    This class handles discovery of both native subagents (from
    environment-specific directories) and canonical subagents
    (from .work/subagents/).
    """

    # Default search paths for canonical subagents
    DEFAULT_CANONICAL_PATHS: list[Path] = [
        Path(".work/subagents"),
        Path("~/.config/dot-work/subagents").expanduser(),
    ]

    def __init__(
        self,
        project_root: Path | str = ".",
        environment: str = "claude",
        canonical_paths: list[Path] | None = None,
    ) -> None:
        """Initialize the discovery instance.

        Args:
            project_root: Project root directory.
            environment: Environment name (claude, opencode, copilot).
            canonical_paths: Additional search paths for canonical subagents.
        """
        self.project_root = Path(project_root).resolve()
        self.environment = environment
        self.adapter = get_adapter(environment)

        # Build canonical search paths
        self.canonical_paths: list[Path] = []
        if canonical_paths:
            self.canonical_paths.extend(canonical_paths)
        self.canonical_paths.extend(self.DEFAULT_CANONICAL_PATHS)

    def discover_native(self) -> list[SubagentConfig]:
        """Discover native subagents for the current environment.

        Searches the environment-specific directory (e.g., .claude/agents/)
        for subagent definitions.

        Returns:
            List of SubagentConfig objects.
        """
        target_path = self.adapter.get_target_path(self.project_root)

        if not target_path.exists() or not target_path.is_dir():
            return []

        subagents: list[SubagentConfig] = []

        for file_path in target_path.glob("*.md"):
            try:
                config = self.adapter.parse_native(file_path.read_text(encoding="utf-8"))
                subagents.append(config)
            except Exception:
                # Skip files that fail to parse
                continue

        return subagents

    def discover_canonical(self) -> list[CanonicalSubagent]:
        """Discover canonical subagents in configured paths.

        Searches for .md files in canonical subagent directories.

        Returns:
            List of CanonicalSubagent objects.
        """
        subagents: list[CanonicalSubagent] = []

        for search_path in self.canonical_paths:
            # Expand user and resolve
            search_path = search_path.expanduser().resolve()

            if not search_path.exists() or not search_path.is_dir():
                continue

            for file_path in search_path.glob("*.md"):
                try:
                    subagent = SUBAGENT_PARSER.parse(file_path)
                    subagents.append(subagent)
                except Exception:
                    # Skip files that fail to parse
                    continue

        return subagents

    def discover_metadata(self) -> list[SubagentMetadata]:
        """Discover lightweight metadata for native subagents.

        This is faster than discover_native() as it only reads frontmatter.

        Returns:
            List of SubagentMetadata objects.
        """
        configs = self.discover_native()
        return [
            SubagentMetadata(name=config.name, description=config.description)
            for config in configs
        ]

    def load_native(self, name: str) -> SubagentConfig:
        """Load a native subagent by name.

        Args:
            name: Subagent name.

        Returns:
            SubagentConfig object.

        Raises:
            FileNotFoundError: If subagent not found.
        """
        configs = self.discover_native()

        for config in configs:
            if config.name == name:
                return config

        raise FileNotFoundError(f"Subagent {name!r} not found")

    def load_canonical(self, name: str) -> CanonicalSubagent:
        """Load a canonical subagent by name.

        Args:
            name: Subagent name.

        Returns:
            CanonicalSubagent object.

        Raises:
            FileNotFoundError: If subagent not found.
        """
        subagents = self.discover_canonical()

        for subagent in subagents:
            if subagent.meta.name == name:
                return subagent

        raise FileNotFoundError(f"Canonical subagent {name!r} not found")

    def list_available_names(self) -> list[str]:
        """List names of all available native subagents.

        Returns:
            List of subagent names.
        """
        configs = self.discover_native()
        return [config.name for config in configs]

    def list_canonical_names(self) -> list[str]:
        """List names of all available canonical subagents.

        Returns:
            List of canonical subagent names.
        """
        subagents = self.discover_canonical()
        return [subagent.meta.name for subagent in subagents]


# Default discovery instance for current environment
DEFAULT_DISCOVERY = SubagentDiscovery()
