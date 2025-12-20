"""JSON validation using Python's built-in json module.

Validates JSON syntax, reports errors with line/column info, and provides
optional JSON Schema validation for a useful subset of the spec.

Example:
    >>> from dot_work.tools.json_validator import validate_json
    >>> result = validate_json('{"name": "test"}')
    >>> result.valid
    True
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class JSONError:
    """A JSON validation error with location info."""

    message: str
    line: int = 0
    column: int = 0
    context: str = ""

    def __str__(self) -> str:
        """Format error with location."""
        if self.line:
            return f"Line {self.line}, col {self.column}: {self.message}"
        return self.message


@dataclass
class JSONWarning:
    """A JSON validation warning."""

    message: str
    line: int = 0
    column: int = 0

    def __str__(self) -> str:
        """Format warning with location."""
        if self.line:
            return f"Line {self.line}, col {self.column}: {self.message}"
        return self.message


@dataclass
class ValidationResult:
    """Result of JSON validation."""

    valid: bool
    errors: list[JSONError] = field(default_factory=list)
    warnings: list[JSONWarning] = field(default_factory=list)
    data: Any = None

    def __bool__(self) -> bool:
        """True if valid."""
        return self.valid


def _pos_to_line_col(content: str, pos: int) -> tuple[int, int]:
    """Convert character position to (line, column)."""
    lines = content[:pos].split("\n")
    return (len(lines), len(lines[-1]) + 1)


def _get_context(content: str, pos: int, chars: int = 20) -> str:
    """Extract context around error position."""
    start = max(0, pos - chars)
    end = min(len(content), pos + chars)
    return content[start:end].replace("\n", "↵")


def validate_json(content: str) -> ValidationResult:
    """Validate JSON string.

    Args:
        content: JSON string to validate.

    Returns:
        ValidationResult with parsed data if valid, errors if not.
    """
    if not content or not content.strip():
        return ValidationResult(
            valid=False,
            errors=[JSONError("Empty content", line=1, column=1)],
        )

    try:
        data = json.loads(content)
        return ValidationResult(valid=True, data=data)
    except json.JSONDecodeError as e:
        line, col = _pos_to_line_col(content, e.pos)
        return ValidationResult(
            valid=False,
            errors=[
                JSONError(
                    message=e.msg,
                    line=line,
                    column=col,
                    context=_get_context(content, e.pos),
                )
            ],
        )


def validate_json_file(path: Path) -> ValidationResult:
    """Validate a JSON file.

    Args:
        path: Path to JSON file.

    Returns:
        ValidationResult with parsed data or errors.
    """
    if not path.exists():
        return ValidationResult(
            valid=False,
            errors=[JSONError(f"File not found: {path}")],
        )

    try:
        content = path.read_text(encoding="utf-8")
    except PermissionError:
        return ValidationResult(
            valid=False,
            errors=[JSONError(f"Permission denied: {path}")],
        )
    except UnicodeDecodeError as e:
        return ValidationResult(
            valid=False,
            errors=[JSONError(f"Encoding error: {e}")],
        )

    return validate_json(content)


# =============================================================================
# JSON Schema Validation (subset)
# =============================================================================


def _get_type(value: Any) -> str:
    """Get JSON type name for a Python value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


def _validate_node(data: Any, schema: dict[str, Any], path: str = "$") -> list[JSONError]:
    """Validate a data node against schema."""
    errors: list[JSONError] = []

    # Type check
    if "type" in schema:
        expected = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        actual = _get_type(data)
        # integer is also a number
        if actual == "integer" and "number" in expected:
            pass
        elif actual not in expected:
            errors.append(JSONError(f"{path}: expected {expected}, got {actual}"))
            return errors

    # Enum check
    if "enum" in schema and data not in schema["enum"]:
        errors.append(JSONError(f"{path}: must be one of {schema['enum']}"))

    # Pattern check (strings)
    if "pattern" in schema and isinstance(data, str):
        try:
            if not re.search(schema["pattern"], data):
                errors.append(JSONError(f"{path}: does not match pattern '{schema['pattern']}'"))
        except re.error:
            errors.append(JSONError(f"{path}: invalid regex in schema"))

    # Object checks
    if isinstance(data, dict):
        if "required" in schema:
            for prop in schema["required"]:
                if prop not in data:
                    errors.append(JSONError(f"{path}: missing required property '{prop}'"))

        if "properties" in schema:
            for prop, prop_schema in schema["properties"].items():
                if prop in data:
                    errors.extend(_validate_node(data[prop], prop_schema, f"{path}.{prop}"))

    # Array checks
    if isinstance(data, list) and "items" in schema:
        for i, item in enumerate(data):
            errors.extend(_validate_node(item, schema["items"], f"{path}[{i}]"))

    return errors


def validate_against_schema(data: Any, schema: dict[str, Any]) -> ValidationResult:
    """Validate data against JSON Schema (subset).

    Supports: type, required, enum, pattern, properties, items.

    Args:
        data: Parsed JSON data.
        schema: JSON Schema dict.

    Returns:
        ValidationResult with errors if any.
    """
    errors = _validate_node(data, schema)
    return ValidationResult(valid=len(errors) == 0, errors=errors, data=data)
