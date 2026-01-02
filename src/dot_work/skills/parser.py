"""Parser for SKILL.md files with YAML frontmatter.

This module implements the SkillParser class which extracts and parses
SKILL.md files following the Agent Skills specification format.

The parser mirrors the pattern of CanonicalPromptParser for consistency.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from dot_work.skills.models import Skill, SkillMetadata


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

        # Extract metadata
        metadata = self._extract_metadata(frontmatter, skill_dir)

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

        return self._extract_metadata(frontmatter, skill_dir)

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
        )


# Singleton instance for efficiency
SKILL_PARSER = SkillParser()
