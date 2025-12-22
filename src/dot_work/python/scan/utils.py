"""
Utility functions for the Python code scanner.
"""

import hashlib
import os
from pathlib import Path


def is_python_file(path: Path) -> bool:
    """Check if a path is a Python source file.

    Args:
        path: Path to check.

    Returns:
        True if path is a .py file.
    """
    return path.suffix == ".py"


def should_ignore(path: Path, ignore_patterns: list[str] | None = None) -> bool:
    """Check if a path should be ignored during scanning.

    Args:
        path: Path to check.
        ignore_patterns: List of glob patterns to ignore.

    Returns:
        True if path should be ignored.
    """
    default_ignore = [
        "__pycache__",
        ".venv",
        "venv",
        ".virtualenv",
        ".git",
        ".tox",
        ".eggs",
        "*.egg-info",
        "build",
        "dist",
    ]

    patterns = ignore_patterns or default_ignore

    for part in path.parts:
        if part in patterns:
            return True

    for pattern in patterns:
        if path.match(pattern):
            return True

    return False


def compute_file_hash(path: Path) -> str:
    """Compute MD5 hash of a file's contents.

    Args:
        path: Path to file.

    Returns:
        Hex digest of MD5 hash.
    """
    hasher = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_file_mtime(path: Path) -> float:
    """Get file modification time.

    Args:
        path: Path to file.

    Returns:
        Modification time as float.
    """
    return os.path.getmtime(path)


def get_file_size(path: Path) -> int:
    """Get file size in bytes.

    Args:
        path: Path to file.

    Returns:
        File size in bytes.
    """
    return os.path.getsize(path)
