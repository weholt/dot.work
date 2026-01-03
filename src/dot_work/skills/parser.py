"""Parser for SKILL.md files with YAML frontmatter.

This module implements the SkillParser class which extracts and parses
SKILL.md files following the Agent Skills specification format.

The parser mirrors the pattern of CanonicalPromptParser for consistency.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from dot_work.skills.models import Skill, SkillEnvironmentConfig, SkillMetadata

# Path to global defaults file
GLOBAL_DEFAULTS_PATH = Path(__file__).parent / "global.yml"


def _deep_merge(a: dict, b: dict) -> dict:
    """Recursively merge dict b into dict a (a is not mutated, returns new dict).

    Special handling for environment configs: if local (b) specifies 'filename',
    any 'filename_suffix' from global (a) is removed, and vice versa.

    Empty local dict {} does NOT override global defaults - global values are used.
    This allows skills to explicitly declare environments section while relying
    on global defaults.
    """
    result = copy.deepcopy(a)
    for k, v in b.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            # Recursively merge non-empty dicts (empty local dict preserves global defaults)
            if v:
                result[k] = _deep_merge(result[k], v)
                # Handle filename/filename_suffix mutual exclusion for environment configs
                if "filename" in v or "filename_suffix" in v:
                    if "filename" in v:
                        result[k].pop("filename_suffix", None)
                    elif "filename_suffix" in v:
                        result[k].pop("filename", None)
        else:
            result[k] = copy.deepcopy(v)
    return result


def _load_global_defaults() -> dict:
    """Load global.yml defaults if present, else return empty dict."""
    if GLOBAL_DEFAULTS_PATH.exists():
        with GLOBAL_DEFAULTS_PATH.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("defaults", {}) if isinstance(data, dict) else {}
    return {}


class SkillParserError(Exception):
    """Error in skill file parsing or validation."""


@dataclass
class ValidationError:
    """Represents a validation error in a skill file."""

    field: str
    message: str
    severity: str = "error"  # error, warning

    def __str__(self) -> str:
        return f"{self.field}: {self.message}"


class SkillParser:
    """Parser for SKILL.md files with YAML frontmatter.

    This class has no state - all methods are pure functions.
    Use the SKILL_PARSER singleton for efficiency.

    The frontmatter format:
    ---
    name: my-skill
    description: A brief description of what this skill does
    license: MIT
    compatibility: Compatible with Claude Code 1.0+
    metadata:
      author: Your Name
      version: 1.0.0
    allowed_tools:
      - read
      - write
    ---

    Skill content here in markdown format...
    """

    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)

    def parse(self, skill_dir: str | Path) -> Skill:
        """Parse a skill directory containing SKILL.md.

        Args:
            skill_dir: Path to the skill directory.

        Returns:
            Skill object with metadata, content, and optional resources.

        Raises:
            FileNotFoundError: If SKILL.md not found in directory.
            SkillParserError: If parsing or validation fails.
        """
        skill_dir = Path(skill_dir)
        skill_file = skill_dir / "SKILL.md"

        if not skill_file.exists():
            raise FileNotFoundError(f"SKILL.md not found in skill directory: {skill_dir}")

        content = skill_file.read_text(encoding="utf-8").strip()
        return self._parse_content(content, skill_dir=skill_dir)

    def parse_metadata_only(self, skill_dir: str | Path) -> SkillMetadata:
        """Parse only frontmatter for lightweight discovery.

        This is useful for scanning multiple skills without loading full content.

        Args:
            skill_dir: Path to the skill directory.

        Returns:
            SkillMetadata object with name, description, and other metadata.

        Raises:
            FileNotFoundError: If SKILL.md not found in directory.
            SkillParserError: If parsing or validation fails.
        """
        skill_dir = Path(skill_dir)
        skill_file = skill_dir / "SKILL.md"

        if not skill_file.exists():
            raise FileNotFoundError(f"SKILL.md not found in skill directory: {skill_dir}")

        content = skill_file.read_text(encoding="utf-8").strip()
        return self._parse_metadata(content, skill_dir=skill_dir)

    def _parse_content(self, content: str, skill_dir: Path) -> Skill:
        """Parse content string into Skill object.

        Args:
            content: Full SKILL.md file content.
            skill_dir: Path to the skill directory.

        Returns:
            Skill object.

        Raises:
            ValueError: If frontmatter format is invalid.
            SkillParserError: If YAML parsing fails or validation fails.
        """
        # Extract frontmatter and content
        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            raise ValueError("Invalid skill format: missing frontmatter markers")

        frontmatter_text, skill_content = match.groups()

        # Parse YAML frontmatter
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
            if not isinstance(frontmatter, dict):
                raise ValueError("Frontmatter must be a dictionary")
        except yaml.YAMLError as e:
            raise SkillParserError(f"Invalid YAML in frontmatter: {e}") from e

        # Load and merge global defaults (deep merge, local overrides global)
        global_defaults = _load_global_defaults()
        merged_frontmatter = _deep_merge(global_defaults, frontmatter)

        # Extract metadata
        metadata = self._extract_metadata(merged_frontmatter, skill_dir)

        return Skill(
            meta=metadata,
            content=skill_content,
            path=skill_dir,
        )

    def _parse_metadata(self, content: str, skill_dir: Path) -> SkillMetadata:
        """Parse only metadata from frontmatter (lightweight discovery).

        Args:
            content: Full SKILL.md file content.
            skill_dir: Path to the skill directory.

        Returns:
            SkillMetadata object.

        Raises:
            ValueError: If frontmatter format is invalid.
            SkillParserError: If YAML parsing fails or validation fails.
        """
        # Extract frontmatter (ignore content body)
        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            raise ValueError("Invalid skill format: missing frontmatter markers")

        frontmatter_text = match.group(1)

        # Parse YAML frontmatter
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
            if not isinstance(frontmatter, dict):
                raise ValueError("Frontmatter must be a dictionary")
        except yaml.YAMLError as e:
            raise SkillParserError(f"Invalid YAML in frontmatter: {e}") from e

        # Load and merge global defaults (deep merge, local overrides global)
        global_defaults = _load_global_defaults()
        merged_frontmatter = _deep_merge(global_defaults, frontmatter)

        return self._extract_metadata(merged_frontmatter, skill_dir)

    def _extract_metadata(self, frontmatter: dict[str, Any], skill_dir: Path) -> SkillMetadata:
        """Extract and validate metadata from frontmatter dictionary.

        Args:
            frontmatter: Parsed YAML frontmatter dictionary.
            skill_dir: Path to the skill directory (for error messages).

        Returns:
            SkillMetadata object.

        Raises:
            SkillParserError: If required fields are missing.
        """
        # Check for required fields
        if "name" not in frontmatter:
            raise SkillParserError(f"Missing required field 'name' in {skill_dir / 'SKILL.md'}")

        if "description" not in frontmatter:
            raise SkillParserError(
                f"Missing required field 'description' in {skill_dir / 'SKILL.md'}"
            )

        # Extract fields
        name = frontmatter["name"]
        description = frontmatter["description"]
        license_str = frontmatter.get("license")
        compatibility = frontmatter.get("compatibility")
        metadata = frontmatter.get("metadata")
        allowed_tools = frontmatter.get("allowed_tools")
        environments = self._parse_environments(frontmatter.get("environments"), skill_dir)

        # Validate metadata dict if provided
        if metadata is not None and not isinstance(metadata, dict):
            raise SkillParserError(
                f"Field 'metadata' must be a dictionary in {skill_dir / 'SKILL.md'}"
            )

        # Validate allowed_tools list if provided
        if allowed_tools is not None and not isinstance(allowed_tools, list):
            raise SkillParserError(
                f"Field 'allowed_tools' must be a list in {skill_dir / 'SKILL.md'}"
            )

        return SkillMetadata(
            name=name,
            description=description,
            license=license_str,
            compatibility=compatibility,
            metadata=metadata,
            allowed_tools=allowed_tools,
            environments=environments,
        )

    def _parse_environments(
        self, environments_raw: Any, skill_dir: Path
    ) -> dict[str, SkillEnvironmentConfig] | None:
        """Parse environment configurations from raw dict.

        Args:
            environments_raw: Raw environments section from frontmatter.
            skill_dir: Path to the skill directory (for error messages).

        Returns:
            Dict of environment name to SkillEnvironmentConfig, or None if no environments.

        Raises:
            SkillParserError: If environment configuration is invalid.
        """
        if not isinstance(environments_raw, dict):
            return None

        environments: dict[str, SkillEnvironmentConfig] = {}

        for env_name, env_config in environments_raw.items():
            if not isinstance(env_config, dict):
                raise SkillParserError(
                    f"Environment '{env_name}' must be a dictionary in {skill_dir / 'SKILL.md'}"
                )

            if "target" not in env_config:
                raise SkillParserError(
                    f"Environment '{env_name}' must specify 'target' in {skill_dir / 'SKILL.md'}"
                )

            # Create SkillEnvironmentConfig
            environments[env_name] = SkillEnvironmentConfig(
                target=env_config["target"],
                filename=env_config.get("filename"),
                filename_suffix=env_config.get("filename_suffix"),
            )

        return environments if environments else None


# Singleton instance for efficiency
SKILL_PARSER = SkillParser()
