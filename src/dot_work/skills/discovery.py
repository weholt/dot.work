"""Filesystem skill discovery for Agent Skills.

This module implements skill discovery from configured search paths,
supporting project-local, user-global, and bundled skills.
"""

from __future__ import annotations

from pathlib import Path

from dot_work.skills.models import Skill, SkillMetadata
from dot_work.skills.parser import SKILL_PARSER


class SkillDiscovery:
    """Discover skills from configured directories.

    Default search paths:
    - .skills/ (project-local)
    - ~/.config/dot-work/skills/ (user-global)
    - Bundled skills in package (not yet implemented)

    Example usage:
        discovery = SkillDiscovery()
        skills = discovery.discover()
        for skill_meta in skills:
            print(f"{skill_meta.name}: {skill_meta.description}")
    """

    def __init__(self, search_paths: list[Path] | None = None) -> None:
        """Initialize skill discovery with custom search paths.

        Args:
            search_paths: Optional list of directories to search for skills.
                If None, uses default paths (.skills/ and ~/.config/dot-work/skills/).
        """
        if search_paths is None:
            self.search_paths = self._get_default_search_paths()
        else:
            self.search_paths = search_paths

    def _get_default_search_paths(self) -> list[Path]:
        """Get default search paths for skills.

        Returns:
            List of Paths to search for skills.
        """
        paths: list[Path] = []

        # Project-local .skills/ directory
        cwd = Path.cwd()
        project_skills = cwd / ".skills"
        if project_skills.is_dir():
            paths.append(project_skills)

        # User-global ~/.config/dot-work/skills/ directory
        user_config = Path.home() / ".config" / "dot-work" / "skills"
        if user_config.is_dir():
            paths.append(user_config)

        # Bundled skills (not yet implemented)
        # TODO: Add bundled package skills

        return paths

    def discover(self) -> list[SkillMetadata]:
        """Scan paths for valid skill directories.

        Returns:
            List of SkillMetadata objects from all discovered skills.

        Raises:
            OSError: If a search path cannot be accessed.
        """
        discovered: list[SkillMetadata] = []

        for search_path in self.search_paths:
            if not search_path.exists():
                continue

            if not search_path.is_dir():
                continue

            # Scan for skill subdirectories (containing SKILL.md)
            for entry in search_path.iterdir():
                if not entry.is_dir():
                    continue

                skill_file = entry / "SKILL.md"
                if not skill_file.exists():
                    continue

                # Parse metadata only (lightweight)
                try:
                    metadata = SKILL_PARSER.parse_metadata_only(entry)
                    discovered.append(metadata)
                except Exception:
                    # Skip invalid skills during discovery
                    # Use validate() for detailed error reporting
                    continue

        # Sort by name for deterministic output
        discovered.sort(key=lambda m: m.name)

        return discovered

    def load_skill(self, name: str) -> Skill:
        """Load full skill content by name.

        Args:
            name: Name of the skill to load.

        Returns:
            Skill object with full content and resources.

        Raises:
            FileNotFoundError: If skill is not found in any search path.
            Exception: If skill parsing fails.
        """
        for search_path in self.search_paths:
            skill_dir = search_path / name
            if skill_dir.exists() and skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    return SKILL_PARSER.parse(skill_dir)

        raise FileNotFoundError(
            f"Skill {name!r} not found in search paths: "
            + ", ".join(str(p) for p in self.search_paths)
        )

    def find_skill(self, name: str) -> Path | None:
        """Find skill directory by name without loading full content.

        Args:
            name: Name of the skill to find.

        Returns:
            Path to skill directory if found, None otherwise.
        """
        for search_path in self.search_paths:
            skill_dir = search_path / name
            if skill_dir.exists() and skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    return skill_dir

        return None


# Singleton instance for convenience
DEFAULT_DISCOVERY = SkillDiscovery()
