"""Data models for Agent Skills.

This module defines the data structures for Agent Skills per the
Agent Skills specification (https://agentskills.io/specification).

Skills are reusable agent capability packages with structured metadata,
progressive disclosure, and optional bundled resources.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SkillMetadata:
    """Lightweight metadata loaded at startup (~100 tokens per skill).

    Attributes:
        name: Required skill name, 1-64 chars, lowercase + hyphens only.
            No leading/trailing/consecutive hyphens.
        description: Required description, 1-1024 chars, non-empty.
        license: Optional license identifier.
        compatibility: Optional compatibility notes, max 500 chars.
        metadata: Optional string->string metadata dictionary.
        allowed_tools: Optional list of allowed tool names (experimental).

    Raises:
        ValueError: If validation constraints are violated in __post_init__.
    """

    name: str
    description: str
    license: str | None = None
    compatibility: str | None = None
    metadata: dict[str, str] | None = None
    allowed_tools: list[str] | None = None

    # Compiled regex for name validation
    NAME_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")

    def __post_init__(self) -> None:
        """Validate skill metadata constraints."""
        # Validate name
        if not isinstance(self.name, str):
            raise ValueError("Skill name must be a string")

        if not (1 <= len(self.name) <= 64):
            raise ValueError(
                f"Skill name must be 1-64 characters, got {len(self.name)} chars"
            )

        if not self.NAME_PATTERN.match(self.name):
            raise ValueError(
                f"Skill name must contain only lowercase letters, numbers, and hyphens; "
                f"cannot start/end with hyphen or have consecutive hyphens. Got: {self.name!r}"
            )

        # Validate description
        if not isinstance(self.description, str):
            raise ValueError("Skill description must be a string")

        stripped_description = self.description.strip()
        if not stripped_description:
            raise ValueError("Skill description cannot be empty")

        if not (1 <= len(self.description) <= 1024):
            raise ValueError(
                f"Skill description must be 1-1024 characters, got {len(self.description)} chars"
            )

        # Validate compatibility length if provided
        if self.compatibility is not None:
            if not isinstance(self.compatibility, str):
                raise ValueError("Skill compatibility must be a string")
            if len(self.compatibility) > 500:
                raise ValueError(
                    f"Skill compatibility must be <= 500 characters, got {len(self.compatibility)} chars"
                )

        # Validate metadata dict if provided
        if self.metadata is not None:
            if not isinstance(self.metadata, dict):
                raise ValueError("Skill metadata must be a dictionary")
            for key, value in self.metadata.items():
                if not isinstance(key, str):
                    raise ValueError(f"Skill metadata key must be string, got {type(key).__name__}")
                if not isinstance(value, str):
                    raise ValueError(f"Skill metadata value must be string, got {type(value).__name__} for key {key!r}")

        # Validate allowed_tools list if provided
        if self.allowed_tools is not None:
            if not isinstance(self.allowed_tools, list):
                raise ValueError("Skill allowed_tools must be a list")
            for i, tool in enumerate(self.allowed_tools):
                if not isinstance(tool, str):
                    raise ValueError(f"Skill allowed_tools[{i}] must be string, got {type(tool).__name__}")


@dataclass
class Skill:
    """Full skill with content and optional resource directories.

    Attributes:
        meta: SkillMetadata with name, description, and other metadata.
        content: Markdown body content (< 5000 tokens recommended).
        path: Skill directory path.
        scripts: Optional list of paths to scripts/ directory contents.
        references: Optional list of paths to references/ directory contents.
        assets: Optional list of paths to assets/ directory contents.
    """

    meta: SkillMetadata
    content: str
    path: Path
    scripts: list[Path] | None = None
    references: list[Path] | None = None
    assets: list[Path] | None = None

    def __post_init__(self) -> None:
        """Validate skill content and resolve directory paths."""
        # Ensure path is a Path object
        if not isinstance(self.path, Path):
            self.path = Path(self.path)

        # Validate content is a string
        if not isinstance(self.content, str):
            raise ValueError("Skill content must be a string")

        # Verify skill name matches directory name
        if self.path.name != self.meta.name:
            raise ValueError(
                f"Skill directory name {self.path.name!r} must match metadata name {self.meta.name!r}"
            )

        # Resolve optional resource directories
        self._resolve_resource_directories()

    def _resolve_resource_directories(self) -> None:  # pragma: no cover (type checking issue)
        """Resolve paths to optional resource directories (scripts, references, assets).

        This method is called during __post_init__ to populate the optional
        resource lists based on what exists in the skill directory.

        Note: Uses object.__setattr__ to avoid frozen dataclass issues if class
        is made frozen in the future.
        """
        scripts_dir = self.path / "scripts"
        if scripts_dir.is_dir():
            object.__setattr__(self, "scripts", sorted(scripts_dir.iterdir()))

        refs_dir = self.path / "references"
        if refs_dir.is_dir():
            object.__setattr__(self, "references", sorted(refs_dir.iterdir()))

        assets_dir = self.path / "assets"
        if assets_dir.is_dir():
            object.__setattr__(self, "assets", sorted(assets_dir.iterdir()))


# Note: The _resolve_resource_directories method is defined on Skill but cannot
# reference self during type checking. The actual implementation populates
# self.scripts, self.references, and self.assets based on directory contents.
