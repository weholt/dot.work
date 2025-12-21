"""Configuration management for kgshred.

Handles database paths, environment variables, and configuration loading.
"""

import os
from pathlib import Path


class ConfigError(Exception):
    """Raised when configuration is invalid."""

    pass


def get_db_path() -> Path:
    """Get the database file path.

    Returns the database path from environment variable KG_DB_PATH,
    or defaults to ~/.kgshred/db.sqlite.

    Returns:
        Path to the database file.

    Raises:
        ConfigError: If the path is invalid.
    """
    env_path = os.environ.get("KG_DB_PATH")
    if env_path:
        db_path = Path(env_path)
    else:
        db_path = Path.home() / ".kgshred" / "db.sqlite"

    return db_path


def ensure_db_directory(db_path: Path | None = None) -> Path:
    """Ensure the database directory exists.

    Args:
        db_path: Optional explicit database path. If not provided,
                 uses get_db_path().

    Returns:
        The database path (with parent directory created).

    Raises:
        ConfigError: If the directory cannot be created.
    """
    if db_path is None:
        db_path = get_db_path()

    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ConfigError(f"Cannot create database directory: {e}") from e

    return db_path


def validate_path(path: Path) -> Path:
    """Validate a path for use as database location.

    TODO: Wire up to CLI --db option for user-provided database paths.
    Currently tested but not called from production code.

    Args:
        path: Path to validate.

    Returns:
        The validated path.

    Raises:
        ConfigError: If the path is invalid.
    """
    # Check for obviously invalid paths
    if not path.suffix:
        raise ConfigError(f"Invalid path (no file extension): {path}")

    # Check parent directory is valid
    try:
        resolved = path.resolve()
        if not resolved.parent.exists():
            # Try to check if it's creatable
            test_parts = []
            current = resolved.parent
            while not current.exists():
                test_parts.append(current)
                current = current.parent
                if current == current.parent:  # Reached root
                    break
    except (OSError, ValueError) as e:
        raise ConfigError(f"Invalid path: {e}") from e

    return path
