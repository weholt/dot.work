"""Canonical prompt file structure parsing and validation.

This module implements the canonical prompt file format that eliminates
prompt drift across environments through enforced structure and frontmatter.

Canonical format:
---
meta:
  title: "Prompt Title"
  description: "Purpose of this prompt"
  version: "1.0"

environments:
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"

  claude:
    target: ".claude/"
    filename: "prompt.md"

---

Canonical prompt body content...
"""

from __future__ import annotations


import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml
import copy

# Path to global defaults file
GLOBAL_DEFAULTS_PATH = Path(__file__).parent / "global.yml"

def _deep_merge(a: dict, b: dict) -> dict:
    """Recursively merge dict b into dict a (a is not mutated, returns new dict)."""
    result = copy.deepcopy(a)
    for k, v in b.items():
        if (
            k in result
            and isinstance(result[k], dict)
            and isinstance(v, dict)
        ):
            result[k] = _deep_merge(result[k], v)
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


class CanonicalPromptError(Exception):
    """Error in canonical prompt structure or validation."""


@dataclass
class EnvironmentConfig:
    """Configuration for a specific target environment."""

    target: str
    filename: str | None = None
    filename_suffix: str | None = None

    def __post_init__(self) -> None:
        """Validate environment configuration."""
        # Check if both are provided
        if self.filename is not None and self.filename_suffix is not None:
            raise ValueError("Environment cannot specify both 'filename' and 'filename_suffix'")

        # Check for empty strings (distinct from None)
        if self.filename == "":
            raise ValueError("Environment filename cannot be empty")

        if self.filename_suffix == "":
            raise ValueError("Environment filename_suffix cannot be empty")

        # Check if neither is provided (after checking for empty strings)
        if self.filename is None and self.filename_suffix is None:
            raise ValueError("Environment must specify either 'filename' or 'filename_suffix'")


@dataclass
class ValidationError:
    """Represents a validation error in a canonical prompt file."""

    line: int
    message: str
    severity: str = "error"  # error, warning

    def __str__(self) -> str:
        return f"Line {self.line}: {self.message}"


@dataclass
class CanonicalPrompt:
    """Parsed canonical prompt with metadata, environments, and content."""

    meta: dict[str, Any]
    environments: dict[str, EnvironmentConfig]
    content: str
    source_file: Path | None = None

    def get_environment(self, name: str) -> EnvironmentConfig:
        """Get environment configuration by name.

        Args:
            name: Name of the environment to retrieve.

        Returns:
            EnvironmentConfig for the specified environment.

        Raises:
            CanonicalPromptError: If the environment is not found in the prompt.
        """
        if name not in self.environments:
            available = ", ".join(sorted(self.environments.keys()))
            raise CanonicalPromptError(
                f"Environment '{name}' not found in canonical prompt. "
                f"Available environments: {available}"
            )
        return self.environments[name]

    def list_environments(self) -> list[str]:
        """Get list of available environment names."""
        return list(self.environments.keys())


class CanonicalPromptParser:
    """Parser for canonical prompt files with frontmatter validation.

    This class has no state - all methods are pure functions.
    Use the CANONICAL_PARSER singleton for efficiency.
    """

    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


    def parse(self, file_path: str | Path) -> CanonicalPrompt:
        """Parse a canonical prompt file, merging with global defaults if present."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Canonical prompt file not found: {file_path}")
        content = file_path.read_text(encoding="utf-8").strip()
        return self._parse_content(content, source_file=file_path)

    def parse_content(self, content: str) -> CanonicalPrompt:
        """Parse canonical prompt content directly, merging with global defaults if present."""
        return self._parse_content(content.strip())

    def _parse_content(self, content: str, source_file: Path | None = None) -> CanonicalPrompt:
        """Parse content string into CanonicalPrompt, merging with global defaults."""
        # Extract frontmatter and content
        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            raise ValueError("Invalid canonical prompt format: missing frontmatter markers")

        frontmatter_text, prompt_content = match.groups()

        # Parse YAML frontmatter
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
            if not isinstance(frontmatter, dict):
                raise ValueError("Frontmatter must be a dictionary")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in frontmatter: {e}") from e

        # Load and merge global defaults (deep merge, local overrides global)
        global_defaults = _load_global_defaults()
        merged_frontmatter = _deep_merge(global_defaults, frontmatter)

        # Validate frontmatter structure
        self._validate_frontmatter(merged_frontmatter)

        # Extract and parse environments
        meta = merged_frontmatter.get("meta", {})
        environments_raw = merged_frontmatter.get("environments", {})
        environments = self._parse_environments(environments_raw)

        return CanonicalPrompt(
            meta=meta, environments=environments, content=prompt_content, source_file=source_file
        )

    def _validate_frontmatter(self, frontmatter: dict[str, Any]) -> None:
        """Validate frontmatter structure."""
        if "environments" not in frontmatter:
            raise ValueError("Frontmatter must contain 'environments' section")

        if not isinstance(frontmatter["environments"], dict):
            raise ValueError("'environments' must be a dictionary")

        if not frontmatter["environments"]:
            raise ValueError("'environments' cannot be empty")

    def _parse_environments(self, environments_raw: dict[str, Any]) -> dict[str, EnvironmentConfig]:
        """Parse environment configurations from raw dict."""
        environments: dict[str, EnvironmentConfig] = {}

        for env_name, env_config in environments_raw.items():
            if not isinstance(env_config, dict):
                raise ValueError(f"Environment '{env_name}' must be a dictionary")

            if "target" not in env_config:
                raise ValueError(f"Environment '{env_name}' must specify 'target'")

            # Create EnvironmentConfig
            environments[env_name] = EnvironmentConfig(
                target=env_config["target"],
                filename=env_config.get("filename"),
                filename_suffix=env_config.get("filename_suffix"),
            )

        return environments


class CanonicalPromptValidator:
    """Validator for canonical prompt structure and content.

    This class has no state - all methods are pure functions.
    Use the CANONICAL_VALIDATOR singleton for efficiency.
    """

    def validate(self, prompt: CanonicalPrompt, strict: bool = False) -> list[ValidationError]:
        """Validate a canonical prompt and return any errors."""
        errors: list[ValidationError] = []

        # Validate meta section
        errors.extend(self._validate_meta(prompt))

        # Validate environments
        errors.extend(self._validate_environments(prompt))

        # Validate content
        errors.extend(self._validate_content(prompt))

        # Strict validation (additional checks)
        if strict:
            errors.extend(self._validate_strict(prompt))

        return errors

    def _validate_meta(self, prompt: CanonicalPrompt) -> list[ValidationError]:
        """Validate the meta section."""
        errors: list[ValidationError] = []

        if prompt.meta is None:
            errors.append(ValidationError(0, "Meta section is empty or missing"))
            return errors

        # If meta is empty dict, don't treat as fatal error, just generate warnings
        if prompt.meta == {}:
            # Check recommended meta fields
            recommended_fields = ["title", "description", "version"]
            for field in recommended_fields:
                errors.append(
                    ValidationError(0, f"Recommended meta field '{field}' is missing", "warning")
                )
            return errors

        # Check recommended meta fields
        recommended_fields = ["title", "description", "version"]
        for field in recommended_fields:
            if field not in prompt.meta:
                errors.append(
                    ValidationError(0, f"Recommended meta field '{field}' is missing", "warning")
                )

        return errors

    def _validate_environments(self, prompt: CanonicalPrompt) -> list[ValidationError]:
        """Validate the environments section."""
        errors: list[ValidationError] = []

        if not prompt.environments:
            errors.append(ValidationError(0, "At least one environment must be defined"))
            return errors

        # Check for duplicate targets
        targets: dict[str, str] = {}
        for name, config in prompt.environments.items():
            target = config.target

            if target in targets:
                errors.append(
                    ValidationError(
                        0,
                        f"Environment '{name}' has duplicate target '{target}' (also used by '{targets[target]}')",
                        "warning",
                    )
                )
            else:
                targets[target] = name

        # Check target paths are absolute or relative but not empty
        for name, config in prompt.environments.items():
            if not config.target.strip():
                errors.append(ValidationError(0, f"Environment '{name}' target cannot be empty"))

        return errors

    def _validate_content(self, prompt: CanonicalPrompt) -> list[ValidationError]:
        """Validate the prompt content."""
        errors: list[ValidationError] = []

        if not prompt.content.strip():
            errors.append(ValidationError(0, "Prompt content is empty"))

        return errors

    def _validate_strict(self, prompt: CanonicalPrompt) -> list[ValidationError]:
        """Strict validation with additional requirements."""
        errors: list[ValidationError] = []

        # Require specific meta fields in strict mode
        required_meta = ["title", "description"]
        for field in required_meta:
            if field not in prompt.meta or not str(prompt.meta[field]).strip():
                errors.append(ValidationError(0, f"Strict mode: 'meta.{field}' is required"))

        # Check that all targets end with /
        for name, config in prompt.environments.items():
            if not config.target.endswith("/"):
                errors.append(
                    ValidationError(
                        0,
                        f"Strict mode: Environment '{name}' target '{config.target}' should end with '/'",
                        "warning",
                    )
                )

        return errors

    def is_valid(self, prompt: CanonicalPrompt, strict: bool = False) -> bool:
        """Check if prompt passes validation."""
        errors = self.validate(prompt, strict)
        return not any(error.severity == "error" for error in errors)


def parse_canonical_prompt(file_path: str | Path) -> CanonicalPrompt:
    """Convenience function to parse a canonical prompt file."""
    parser = CanonicalPromptParser()
    return parser.parse(file_path)


def validate_canonical_prompt(
    prompt: CanonicalPrompt, strict: bool = False
) -> list[ValidationError]:
    """Convenience function to validate a canonical prompt."""
    validator = CanonicalPromptValidator()
    return validator.validate(prompt, strict)


# Module-level singletons for efficient reuse (classes have no state)
CANONICAL_PARSER = CanonicalPromptParser()
CANONICAL_VALIDATOR = CanonicalPromptValidator()


def generate_environment_prompt(prompt: CanonicalPrompt, env_name: str) -> tuple[str, str]:
    """Generate environment-specific prompt file.

    Args:
        prompt: CanonicalPrompt object
        env_name: Target environment name

    Returns:
        Tuple of (filename, content) for the environment-specific prompt

    Raises:
        CanonicalPromptError: If environment not found or configuration is invalid
    """
    try:
        env_config = prompt.get_environment(env_name)
    except CanonicalPromptError:
        raise

    # Validate target path is not empty
    if not env_config.target or not env_config.target.strip():
        raise CanonicalPromptError(
            f"Environment '{env_name}' has an empty or missing 'target' path. "
            f"The target path must be specified and non-empty."
        )

    # Generate filename
    if env_config.filename:
        filename = env_config.filename
    elif env_config.filename_suffix:
        # Use meta title or fallback to environment name
        base_name = prompt.meta.get("title", env_name).lower()
        base_name = re.sub(r"[^a-z0-9_-]", "-", base_name)
        filename = base_name + env_config.filename_suffix
    else:
        # Default to environment name + .prompt.md
        filename = f"{env_name}.prompt.md"

    # Generate frontmatter for this environment
    env_frontmatter = {
        "meta": prompt.meta,
    }

    # Include environment-specific config (excluding target)
    env_config_dict = {
        k: v
        for k, v in {
            "filename": env_config.filename,
            "filename_suffix": env_config.filename_suffix,
        }.items()
        if v is not None
    }

    if env_config_dict:
        env_frontmatter["environment"] = env_config_dict

    # Generate final content
    output = io.StringIO()
    output.write("---\n")
    yaml.dump(env_frontmatter, output, default_flow_style=False)
    output.write("---\n")
    output.write(prompt.content)

    return filename, output.getvalue()


def extract_environment_file(
    prompt_file: Path, env_name: str, output_dir: Path | None = None
) -> Path:
    """Extract environment-specific prompt file from canonical prompt.

    Args:
        prompt_file: Path to canonical prompt file
        env_name: Target environment name
        output_dir: Optional output directory. If None, the environment's `target` is used
        (relative targets are resolved against the current working directory).

    Returns:
        Path to generated environment file (under the environment target or specified output_dir)

    Raises:
        CanonicalPromptError: If extraction fails
    """
    prompt = parse_canonical_prompt(prompt_file)
    # Retrieve environment config (raises if missing)
    env_config = prompt.get_environment(env_name)

    # Determine output path: prefer explicit output_dir parameter; otherwise use env target
    if output_dir is None:
        target = env_config.target
        if not target or not str(target).strip():
            raise CanonicalPromptError(
                f"Environment '{env_name}' has an empty or missing 'target' path."
            )
        target_path = Path(target)
        # Resolve relative targets against CWD (repository root)
        if not target_path.is_absolute():
            output_dir = Path.cwd() / target_path
        else:
            output_dir = target_path
    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    filename, content = generate_environment_prompt(prompt, env_name)
    output_path = output_dir / filename

    # Write file
    try:
        output_path.write_text(content, encoding="utf-8")
    except OSError as e:
        raise CanonicalPromptError(f"Failed to write {output_path}: {e}") from e

    return output_path
