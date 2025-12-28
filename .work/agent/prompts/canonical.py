"""Canonical prompt data classes and parsing logic."""

from dataclasses import dataclass
from typing import Any

import yaml


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment."""

    target: str
    filename_suffix: str | None
    keys: dict[str, Any]


@dataclass
class ValidationError:
    """Represents a validation error in a canonical prompt file."""

    line: int
    message: str
    path: str | None


class CanonicalPrompt:
    """Represents a canonical prompt file with multi-environment frontmatter."""

    meta: dict[str, Any]
    environments: dict[str, EnvironmentConfig]
    content: str


def parse_canonical_prompt(file_path: str) -> CanonicalPrompt:
    """Parse a canonical prompt file with YAML frontmatter and content.

    Args:
        file_path: Path to the README or markdown file

    Returns:
        CanonicalPrompt object
    """
    # Parse YAML frontmatter
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Split YAML frontmatter from content
        if content.startswith("---\n"):
            parts = content.split("---\n", 1)
            if len(parts) >= 2:
                yaml_content = parts[0].strip()
                prompt_content = "---\n".join(parts[1:])
                frontmatter = yaml.safe_load(yaml_content)
            else:
                frontmatter = {}
                prompt_content = content
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {file_path}: {e}")

    # Validate required fields
    errors = []

    # Meta validation
    meta = frontmatter.get("meta", {})
    required_meta_fields = ["title", "description", "version"]
    for field in required_meta_fields:
        if field not in meta:
            errors.append(ValidationError(line=1, message=f"Missing required meta field: {field}"))

    # Environments validation
    environments = frontmatter.get("environments", {})
    if not environments:
        errors.append(ValidationError(line=1, message="Missing environments block"))

    # Environment validation
    for env_name, env_config in environments.items():
        if "target" not in env_config:
            errors.append(
                ValidationError(
                    line=1, message=f"Environment '{env_name}' missing required 'target' field"
                )
            )

        # Validate target path format
        target = env_config.get("target", "")
        if not (target.startswith(".") and "/" in target):
            errors.append(
                ValidationError(
                    line=1,
                    message=f"Environment '{env_name}' target must be a directory path ending with '/'",
                )
            )

    if errors:
        # Join all error details
        error_messages = [f"Line {err.line}: {err.message}" for err in errors]
        raise ValueError("Canonical prompt validation failed:\n" + "\n".join(error_messages))

    return CanonicalPrompt(meta=meta, environments=environments, content=prompt_content.strip())


def validate_canonical_structure(prompt: CanonicalPrompt) -> list[ValidationError]:
    """Validate canonical prompt structure and content.

    Returns:
        List of validation errors
    """
    errors = []

    # Validate structure
    if not prompt.content.strip():
        errors.append(ValidationError(line=1, message="Prompt content cannot be empty"))

    # Environment-specific validation
    for env_name, env_config in prompt.environments.items():
        # Check for reserved keys that should be inherited from meta
        reserved_keys = {"title", "description", "version"}
        reserved_in_env = set()

        for key in env_config.keys():
            if key in reserved_keys:
                reserved_in_env.add(key)
                errors.append(
                    ValidationError(
                        line=1,
                        message=f"Environment '{env_name}' contains reserved meta field '{key} (should inherit from meta)",
                    )
                )

        # Validate environment-specific keys
        if "keys" in env_config:
            keys = env_config["keys"]
            if not isinstance(keys, dict):
                errors.append(
                    ValidationError(
                        line=1, message=f"Environment '{env_name}' 'keys' must be a dictionary"
                    )
                )

    return errors


def generate_sequential_id(existing_ids: list[str]) -> str:
    """Generate a sequential ID avoiding collisions."""
    import time

    # Simple hash-based approach
    timestamp = str(int(time.time()))
    base_id = f"{timestamp[-8:]}"  # Last 8 chars of timestamp

    # Ensure uniqueness
    counter = 1
    while f"{base_id}-{counter:03d}" in existing_ids:
        counter += 1
        if counter > 99:
            # Fallback to timestamp + increment to prevent infinite loop
            base_id = f"{timestamp}-{time.time() % 1000:03d}"
            break

    return f"{base_id}-{counter:03d}"
