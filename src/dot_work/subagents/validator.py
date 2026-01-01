"""Validator for subagent definitions.

This module provides validation functionality for subagent definitions
following the subagent specification.
"""

from __future__ import annotations

import string
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ValidationResult:
    """Result of subagent validation.

    Attributes:
        valid: Whether the subagent passed validation.
        errors: List of error messages.
        warnings: List of warning messages.
    """

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        """Return string representation of validation result."""
        if self.valid:
            if self.warnings:
                return f"Valid with {len(self.warnings)} warning(s)"
            return "Valid"
        return f"Invalid ({len(self.errors)} error(s), {len(self.warnings)} warning(s))"


class SubagentValidator:
    """Validator for subagent definitions.

    This class provides validation methods for subagent files and
    configurations following the subagent specification.
    """

    # Valid environment names
    VALID_ENVIRONMENTS = {"claude", "opencode", "copilot"}

    # Valid permission modes for Claude Code
    VALID_CLAUDE_PERMISSION_MODES = {"default", "acceptEdits", "bypassPermissions", "plan"}

    # Valid modes for OpenCode
    VALID_OPENCODE_MODES = {"primary", "subagent", "all"}

    # Valid models for Claude Code
    VALID_CLAUDE_MODELS = {"sonnet", "opus", "haiku", "inherit"}

    # Valid targets for GitHub Copilot
    VALID_COPILOT_TARGETS = {"vscode", "github-copilot"}

    def validate(self, subagent_path: Path) -> ValidationResult:
        """Validate a subagent file.

        Args:
            subagent_path: Path to the subagent .md file or directory.

        Returns:
            ValidationResult with errors and warnings.
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Resolve path
        if subagent_path.is_dir():
            subagent_file = subagent_path / "SUBAGENT.md"
        else:
            subagent_file = subagent_path

        # Check file exists
        if not subagent_file.exists():
            errors.append(f"Subagent file not found: {subagent_file}")
            return ValidationResult(valid=False, errors=errors)

        # Check file extension
        if subagent_file.suffix not in {".md", ".markdown"}:
            warnings.append(
                f"Subagent file has non-standard extension: {subagent_file.suffix}"
            )

        # Try to parse the file
        from dot_work.subagents.parser import SUBAGENT_PARSER

        try:
            canonical_subagent = SUBAGENT_PARSER.parse(subagent_file)
        except FileNotFoundError as e:
            errors.append(str(e))
            return ValidationResult(valid=False, errors=errors)
        except Exception as e:
            errors.append(f"Failed to parse subagent: {e}")
            return ValidationResult(valid=False, errors=errors)

        # Validate metadata
        self._validate_metadata(canonical_subagent, errors, warnings)

        # Validate configuration
        self._validate_config(canonical_subagent.config, errors, warnings)

        # Validate environments
        self._validate_environments(canonical_subagent.environments, errors, warnings)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_directory(self, subagent_dir: Path) -> ValidationResult:
        """Validate a subagent directory.

        This is an alias for validate() for compatibility.

        Args:
            subagent_dir: Path to the subagent directory.

        Returns:
            ValidationResult with errors and warnings.
        """
        return self.validate(subagent_dir)

    def _validate_metadata(
        self,
        subagent: Any,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate subagent metadata.

        Args:
            subagent: CanonicalSubagent object.
            errors: Error list to append to.
            warnings: Warning list to append to.
        """
        # Metadata is already validated by SubagentMetadata.__post_init__
        # This method checks for additional best practices

        # Check description quality
        description = subagent.meta.description
        if len(description) < 20:
            warnings.append("Description is very short (< 20 characters)")

        if description[0] in string.ascii_lowercase:
            warnings.append("Description should start with a capital letter")

        if not description.endswith("."):
            warnings.append("Description should end with a period")

    def _validate_config(
        self,
        config: Any,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate subagent configuration.

        Args:
            config: SubagentConfig object.
            errors: Error list to append to.
            warnings: Warning list to append to.
        """
        # Validate prompt
        if not config.prompt or not config.prompt.strip():
            errors.append("Prompt cannot be empty")
        elif len(config.prompt.strip()) < 50:
            warnings.append("Prompt is very short (< 50 characters)")

        # Validate tools
        if config.tools is not None:
            if not isinstance(config.tools, list):
                errors.append("Tools must be a list")
            elif len(config.tools) == 0:
                warnings.append("Tools list is empty")
            else:
                for i, tool in enumerate(config.tools):
                    if not isinstance(tool, str):
                        errors.append(f"Tool [{i}] must be a string, got {type(tool).__name__}")

        # Validate model
        if config.model is not None:
            if not isinstance(config.model, str):
                errors.append("Model must be a string")

        # Validate permission_mode
        if config.permission_mode is not None:
            if not isinstance(config.permission_mode, str):
                errors.append("permission_mode must be a string")
            elif config.permission_mode not in self.VALID_CLAUDE_PERMISSION_MODES:
                warnings.append(
                    f"Unknown permission_mode: {config.permission_mode}. "
                    f"Valid options: {', '.join(sorted(self.VALID_CLAUDE_PERMISSION_MODES))}"
                )

        # Validate mode
        if config.mode is not None:
            if not isinstance(config.mode, str):
                errors.append("mode must be a string")
            elif config.mode not in self.VALID_OPENCODE_MODES:
                warnings.append(
                    f"Unknown mode: {config.mode}. "
                    f"Valid options: {', '.join(sorted(self.VALID_OPENCODE_MODES))}"
                )

        # Validate temperature
        if config.temperature is not None:
            if not isinstance(config.temperature, (int, float)):
                errors.append("temperature must be a number")
            elif not (0.0 <= config.temperature <= 2.0):
                errors.append("temperature must be between 0.0 and 2.0")

        # Validate max_steps
        if config.max_steps is not None:
            if not isinstance(config.max_steps, int):
                errors.append("max_steps must be an integer")
            elif config.max_steps < 1:
                errors.append("max_steps must be at least 1")

        # Validate skills
        if config.skills is not None:
            if not isinstance(config.skills, list):
                errors.append("skills must be a list")
            elif len(config.skills) == 0:
                warnings.append("Skills list is empty")

        # Validate infer
        if config.infer is not None and not isinstance(config.infer, bool):
            errors.append("infer must be a boolean")

    def _validate_environments(
        self,
        environments: dict[str, Any],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate environment-specific configurations.

        Args:
            environments: Dict of environment name to SubagentEnvironmentConfig.
            errors: Error list to append to.
            warnings: Warning list to append to.
        """
        if not environments:
            # No environments defined is fine
            return

        for env_name, env_config in environments.items():
            # Validate environment name
            if env_name not in self.VALID_ENVIRONMENTS:
                warnings.append(
                    f"Unknown environment: {env_name}. "
                    f"Valid options: {', '.join(sorted(self.VALID_ENVIRONMENTS))}"
                )

            # Validate target
            if not env_config.target:
                errors.append(f"Environment '{env_name}' missing target")
            elif not env_config.target.startswith("."):
                warnings.append(
                    f"Environment '{env_name}' target should be a relative path starting with '.'"
                )

            # Validate environment-specific fields
            if env_name == "claude":
                self._validate_claude_environment(env_config, errors, warnings)
            elif env_name == "opencode":
                self._validate_opencode_environment(env_config, errors, warnings)
            elif env_name == "copilot":
                self._validate_copilot_environment(env_config, errors, warnings)

    def _validate_claude_environment(
        self,
        env_config: Any,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate Claude Code-specific environment configuration."""
        if env_config.model and env_config.model not in self.VALID_CLAUDE_MODELS:
            warnings.append(
                f"Claude environment: Unknown model '{env_config.model}'. "
                f"Valid options: {', '.join(sorted(self.VALID_CLAUDE_MODELS))}"
            )

        if env_config.permission_mode and env_config.permission_mode not in self.VALID_CLAUDE_PERMISSION_MODES:
            warnings.append(
                f"Claude environment: Unknown permission_mode '{env_config.permission_mode}'"
            )

    def _validate_opencode_environment(
        self,
        env_config: Any,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate OpenCode-specific environment configuration."""
        if env_config.mode and env_config.mode not in self.VALID_OPENCODE_MODES:
            warnings.append(
                f"OpenCode environment: Unknown mode '{env_config.mode}'"
            )

        if env_config.temperature is not None and not (0.0 <= env_config.temperature <= 2.0):
            errors.append("OpenCode environment: temperature must be between 0.0 and 2.0")

    def _validate_copilot_environment(
        self,
        env_config: Any,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate GitHub Copilot-specific environment configuration."""
        if env_config.target and env_config.target not in self.VALID_COPILOT_TARGETS:
            warnings.append(
                f"Copilot environment: Unknown target '{env_config.target}'. "
                f"Valid options: {', '.join(sorted(self.VALID_COPILOT_TARGETS))}"
            )


# Singleton instance for efficiency
SUBAGENT_VALIDATOR = SubagentValidator()
