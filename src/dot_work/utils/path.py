"""Path validation utilities for secure file operations.

This module provides functions for validating file paths to prevent
directory traversal attacks (OWASP A01:2021).

## Design Rationale

Path traversal attacks allow malicious users to access files outside
the intended directory by using sequences like "../" or absolute paths.
This module provides safe path joining that validates the result stays
within the target directory.

Reference: Issue SEC-005@security-review-2026
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PathTraversalError(ValueError):
    """Raised when a path traversal attempt is detected."""

    pass


def safe_path_join(target: Path, path: str | Path) -> Path:
    """
    Safely join a target directory with a relative path.

    Validates that the resulting path stays within the target directory
    and resolves any symlinks to prevent symlink attacks.

    Args:
        target: The base directory (must be absolute or resolved)
        path: The relative path to join (can contain multiple components)

    Returns:
        Absolute, resolved path that is guaranteed to be within target

    Raises:
        PathTraversalError: If the path would escape the target directory
        ValueError: If target is not an absolute path

    Examples:
        >>> target = Path("/home/user/project")
        >>> safe_path_join(target, "config.yaml")
        Path('/home/user/project/config.yaml')
        >>> safe_path_join(target, "../etc/passwd")  # Raises PathTraversalError
        PathTraversalError: Path escapes target directory

    Security:
        - Resolves all symlinks before validation
        - Normalizes "." and ".." components
        - Rejects absolute paths that escape target
        - Rejects relative paths with ".." that escape target
    """
    if not target.is_absolute():
        raise ValueError(f"Target directory must be absolute: {target}")

    # Ensure target exists and is a directory
    if not target.exists():
        raise ValueError(f"Target directory does not exist: {target}")
    if not target.is_dir():
        raise ValueError(f"Target is not a directory: {target}")

    # Convert path to Path object if string
    path_obj = Path(path) if isinstance(path, str) else path

    # Reject absolute paths - they could escape the target
    if path_obj.is_absolute():
        logger.warning(f"Rejected absolute path: {path}")
        raise PathTraversalError(f"Absolute path not allowed: {path}")

    # Join with target
    joined = target / path_obj

    # Resolve to absolute path (follows symlinks)
    try:
        resolved = joined.resolve(strict=False)
    except OSError as e:
        logger.error(f"Failed to resolve path {joined}: {e}")
        raise PathTraversalError(f"Cannot resolve path: {path}") from e

    # Validate the resolved path is within target
    # Use resolve() on target to handle symlinks consistently
    target_resolved = target.resolve()

    # Check if resolved path starts with target path
    try:
        resolved.relative_to(target_resolved)
    except ValueError:
        logger.warning(f"Path traversal detected: {path} -> {resolved}")
        raise PathTraversalError(
            f"Path escapes target directory: {path} (resolved to {resolved})"
        )

    return resolved


def validate_path_safe(target: Path, path: str | Path) -> bool:
    """
    Check if a path is safe (within target directory) without raising exceptions.

    This is a non-throwing variant of safe_path_join() for validation checks.

    Args:
        target: The base directory (must be absolute or resolved)
        path: The path to validate

    Returns:
        True if path is safe, False otherwise
    """
    try:
        safe_path_join(target, path)
        return True
    except (PathTraversalError, ValueError):
        return False


def safe_write_path(target: Path, filename: str) -> Path:
    """
    Get a safe path for writing a file within target directory.

    Convenience function for common write operations.

    Args:
        target: The base directory
        filename: The filename (must not contain path separators)

    Returns:
        Safe absolute path for writing

    Raises:
        PathTraversalError: If filename contains path traversal attempts
        ValueError: If filename is invalid
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    # Reject paths with separators (directory components)
    if "/" in filename or "\\" in filename:
        raise PathTraversalError(f"Filename cannot contain path separators: {filename}")

    # Reject obvious traversal attempts
    if ".." in filename or filename.startswith("."):
        raise PathTraversalError(f"Filename contains traversal pattern: {filename}")

    return safe_path_join(target, filename)
