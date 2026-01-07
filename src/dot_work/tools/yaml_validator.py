"""YAML validation using PyYAML.

Validates YAML syntax, reports errors with line/column info, and provides
frontmatter extraction for markdown files.

Example:
    >>> from dot_work.tools.yaml_validator import validate_yaml
    >>> result = validate_yaml("name: test\\ncount: 42")
    >>> result.valid
    True
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class YAMLError:
    """A YAML validation error with location info."""

    message: str
    line: int = 0
    column: int = 0

    def __str__(self) -> str:
        """Format error with location."""
        if self.line:
            return f"Line {self.line}, col {self.column}: {self.message}"
        return self.message


@dataclass
class YAMLWarning:
    """A YAML validation warning."""

    message: str
    line: int = 0
    column: int = 0

    def __str__(self) -> str:
        """Format warning with location."""
        if self.line:
            return f"Line {self.line}, col {self.column}: {self.message}"
        return self.message


@dataclass
class YAMLValidationResult:
    """Result of YAML validation."""

    valid: bool
    errors: list[YAMLError] = field(default_factory=list)
    warnings: list[YAMLWarning] = field(default_factory=list)
    data: dict[str, Any] | list[Any] | None = None

    def __bool__(self) -> bool:
        """True if valid."""
        return self.valid


@dataclass
class FrontmatterResult:
    """Result of frontmatter extraction."""

    valid: bool
    frontmatter: dict[str, Any] | None = None
    content: str = ""
    errors: list[YAMLError] = field(default_factory=list)


def _check_tabs(content: str) -> list[YAMLWarning]:
    """Check for tab characters (discouraged in YAML)."""
    warnings: list[YAMLWarning] = []
    for i, line in enumerate(content.split("\n"), 1):
        if "\t" in line:
            warnings.append(
                YAMLWarning("Tab character (use spaces)", line=i, column=line.index("\t") + 1)
            )
    return warnings


def validate_yaml(content: str) -> YAMLValidationResult:
    """Validate YAML string.

    Args:
        content: YAML string to validate.

    Returns:
        YAMLValidationResult with parsed data if valid, errors if not.
    """
    if not content or not content.strip():
        return YAMLValidationResult(
            valid=False,
            errors=[YAMLError("Empty content", line=1, column=1)],
        )

    warnings = _check_tabs(content)

    try:
        data = yaml.safe_load(content)
        return YAMLValidationResult(valid=True, data=data, warnings=warnings)
    except yaml.YAMLError as e:
        error = YAMLError(str(e))
        # Extract line/column from PyYAML error if available
        if hasattr(e, "problem_mark") and e.problem_mark:
            error.line = e.problem_mark.line + 1
            error.column = e.problem_mark.column + 1
            error.message = getattr(e, "problem", str(e)) or str(e)
        return YAMLValidationResult(valid=False, errors=[error], warnings=warnings)


def validate_yaml_file(path: Path) -> YAMLValidationResult:
    """Validate a YAML file.

    Args:
        path: Path to YAML file.

    Returns:
        YAMLValidationResult with parsed data or errors.
    """
    if not path.exists():
        return YAMLValidationResult(
            valid=False,
            errors=[YAMLError(f"File not found: {path}")],
        )

    try:
        content = path.read_text(encoding="utf-8")
    except PermissionError:
        return YAMLValidationResult(
            valid=False,
            errors=[YAMLError(f"Permission denied: {path}")],
        )
    except UnicodeDecodeError as e:
        return YAMLValidationResult(
            valid=False,
            errors=[YAMLError(f"Encoding error: {e}")],
        )

    return validate_yaml(content)


def extract_frontmatter(content: str) -> FrontmatterResult:
    """Extract YAML frontmatter from markdown content.

    Frontmatter must be delimited by --- at the start of the file.

    Args:
        content: Full file content.

    Returns:
        FrontmatterResult with parsed frontmatter and remaining content.
    """
    lines = content.split("\n")

    # Check for opening ---
    if not lines or lines[0].strip() != "---":
        return FrontmatterResult(
            valid=False,
            content=content,
            errors=[YAMLError("No frontmatter (missing opening ---)", line=1)],
        )

    # Find closing ---
    end_idx = -1
    for i, line in enumerate(lines[1:], 2):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return FrontmatterResult(
            valid=False,
            content=content,
            errors=[YAMLError("Unclosed frontmatter (missing closing ---)", line=1)],
        )

    # Parse frontmatter
    # Note: enumerate starts at 2, so end_idx is the actual line index
    # lines[0] is opening "---", lines[end_idx] is closing "---"
    # Content is everything between (exclusive of delimiters)
    fm_content = "\n".join(lines[1 : end_idx - 1])
    remaining = "\n".join(lines[end_idx:]).lstrip("\n")

    if not fm_content.strip():
        return FrontmatterResult(
            valid=False,
            content=remaining,
            errors=[YAMLError("Empty frontmatter", line=1)],
        )

    result = validate_yaml(fm_content)
    if not result.valid:
        return FrontmatterResult(valid=False, content=remaining, errors=result.errors)

    if not isinstance(result.data, dict):
        return FrontmatterResult(
            valid=False,
            content=remaining,
            errors=[YAMLError("Frontmatter must be a mapping", line=1)],
        )

    return FrontmatterResult(valid=True, frontmatter=result.data, content=remaining)


def parse_yaml(content: str) -> dict[str, Any] | list[Any]:
    """Parse YAML content directly.

    Args:
        content: YAML string.

    Returns:
        Parsed data.

    Raises:
        yaml.YAMLError: If parsing fails.
    """
    return yaml.safe_load(content)
