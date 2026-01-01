"""Validation logic for Agent Skills.

This module implements validation for Agent Skills per the specification,
including error collection and detailed validation reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from dot_work.skills.models import Skill, SkillMetadata


@dataclass
class ValidationResult:
    """Result of skill validation with collected errors and warnings.

    Attributes:
        valid: True if skill is valid (no errors), False otherwise.
        errors: List of validation errors.
        warnings: List of validation warnings.
        skill_path: Path to the skill directory.
    """

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skill_path: Path | None = None

    def add_error(self, message: str) -> None:
        """Add an error message and mark validation as failed."""
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def __str__(self) -> str:
        """Return formatted validation result."""
        if self.valid:
            if self.warnings:
                return f"Valid with {len(self.warnings)} warning(s)"
            return "Valid"
        return f"Invalid: {len(self.errors)} error(s)"


class SkillValidator:
    """Validator for Agent Skills per the specification.

    This class validates Skill and SkillMetadata objects against
    the Agent Skills specification requirements.

    Validation rules:
    - name: 1-64 chars, [a-z0-9-], no leading/trailing/consecutive hyphens
    - description: 1-1024 chars, non-empty
    - compatibility: 1-500 chars if provided
    - metadata: string keys -> string values
    - SKILL.md must exist in skill directory
    - Directory name must match metadata name
    """

    def validate(self, skill: Skill) -> ValidationResult:
        """Validate a full Skill object.

        Args:
            skill: Skill object to validate.

        Returns:
            ValidationResult with errors and warnings.
        """
        result = ValidationResult(valid=True, skill_path=skill.path)

        # Validate metadata first
        metadata_result = self.validate_metadata(skill.meta)
        result.errors.extend(metadata_result.errors)
        result.warnings.extend(metadata_result.warnings)

        # Additional skill-level validations
        if not skill.path.exists():
            result.add_error(f"Skill directory does not exist: {skill.path}")

        if skill.path.name != skill.meta.name:
            result.add_error(
                f"Skill directory name {skill.path.name!r} does not match "
                f"metadata name {skill.meta.name!r}"
            )

        skill_file = skill.path / "SKILL.md"
        if not skill_file.exists():
            result.add_error(f"SKILL.md not found in skill directory: {skill.path}")

        # Check content length (warning only, > 5000 tokens is ~20k chars)
        if len(skill.content) > 20000:
            result.add_warning(
                f"Skill content is very long ({len(skill.content)} chars), "
                f"consider splitting into multiple skills"
            )

        return result

    def validate_metadata(self, metadata: SkillMetadata) -> ValidationResult:
        """Validate SkillMetadata object.

        Args:
            metadata: SkillMetadata to validate.

        Returns:
            ValidationResult with errors and warnings.
        """
        result = ValidationResult(valid=True)

        # Name validation is already done in SkillMetadata.__post_init__
        # but we can add additional checks here

        # Check for reserved names (warning)
        if metadata.name in ("test", "example", "sample"):
            result.add_warning(
                f"Skill name {metadata.name!r} is reserved for examples, "
                f"consider a more specific name"
            )

        # Description validation
        if not metadata.description.strip():
            result.add_error("Skill description cannot be empty or whitespace only")

        # Content quality checks (warnings)
        words = metadata.description.split()
        if len(words) < 3:
            result.add_warning("Skill description is very short, consider adding more detail")

        return result

    def validate_directory(self, skill_dir: Path) -> ValidationResult:
        """Validate a skill directory by parsing and validating its SKILL.md.

        Args:
            skill_dir: Path to the skill directory.

        Returns:
            ValidationResult with errors and warnings.
        """
        from dot_work.skills.parser import SKILL_PARSER

        result = ValidationResult(valid=True, skill_path=skill_dir)

        # Check directory exists
        if not skill_dir.exists():
            result.add_error(f"Skill directory does not exist: {skill_dir}")
            return result

        if not skill_dir.is_dir():
            result.add_error(f"Skill path is not a directory: {skill_dir}")
            return result

        # Try to parse the skill
        try:
            skill = SKILL_PARSER.parse(skill_dir)
            # Merge with full validation
            skill_result = self.validate(skill)
            result.errors.extend(skill_result.errors)
            result.warnings.extend(skill_result.warnings)
            result.valid = result.valid and skill_result.valid
        except FileNotFoundError as e:
            result.add_error(str(e))
        except Exception as e:
            result.add_error(f"Failed to parse skill: {e}")

        return result


# Singleton instance for efficiency
SKILL_VALIDATOR = SkillValidator()
