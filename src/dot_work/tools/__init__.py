"""Validation tools for dot-work.

This package provides zero-dependency validation tools using only Python 3.11+ stdlib.
"""

from dot_work.tools.json_validator import (
    JSONError,
    JSONWarning,
    ValidationResult,
    validate_against_schema,
    validate_json,
    validate_json_file,
)
from dot_work.tools.yaml_validator import (
    FrontmatterResult,
    YAMLError,
    YAMLValidationResult,
    YAMLWarning,
    extract_frontmatter,
    parse_yaml,
    validate_yaml,
    validate_yaml_file,
)

__all__ = [
    # JSON validation
    "JSONError",
    "JSONWarning",
    "ValidationResult",
    "validate_json",
    "validate_json_file",
    "validate_against_schema",
    # YAML validation
    "YAMLError",
    "YAMLWarning",
    "YAMLValidationResult",
    "FrontmatterResult",
    "validate_yaml",
    "validate_yaml_file",
    "parse_yaml",
    "extract_frontmatter",
]
