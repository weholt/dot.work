"""Configuration for database and settings."""

import os
from pathlib import Path


# Custom exception for configuration errors
class ConfigError(Exception):
    """Configuration-related errors."""

    pass


# Default storage location: per-project in .work/kg/
DEFAULT_DB_PATH = Path(".work") / "kg" / "db.sqlite"


def get_db_path() -> Path:
    """Return path to sqlite database.

    Respects DOT_WORK_KG_DB_PATH environment variable if set,
    otherwise uses .work/kg/db.sqlite (per-project storage).

    Users who want a global knowledge base can set:
        DOT_WORK_KG_DB_PATH=~/.kg/db.sqlite
    """
    if env_path := os.environ.get("DOT_WORK_KG_DB_PATH"):
        return Path(env_path).expanduser()
    return DEFAULT_DB_PATH


def ensure_db_directory(db_path: Path | None = None) -> Path:
    """Ensure database directory exists, creating if necessary.

    Args:
        db_path: Path to database file. If None, uses get_db_path().

    Returns:
        Path to the database file.

    Raises:
        ConfigError: If directory cannot be created.
    """
    if db_path is None:
        db_path = get_db_path()

    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return db_path
    except OSError as e:
        raise ConfigError(f"Cannot create database directory: {e}") from e

