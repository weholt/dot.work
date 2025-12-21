"""Configuration for database and settings."""

import os
from pathlib import Path

# Default storage location: per-project in .work/kg/
DEFAULT_DB_PATH = Path(".work") / "kg" / "db.sqlite"


def get_db_path() -> Path:
    """Return the path to the sqlite database.

    Respects DOT_WORK_KG_DB_PATH environment variable if set,
    otherwise uses .work/kg/db.sqlite (per-project storage).

    Users who want a global knowledge base can set:
        DOT_WORK_KG_DB_PATH=~/.kg/db.sqlite
    """
    if env_path := os.environ.get("DOT_WORK_KG_DB_PATH"):
        return Path(env_path).expanduser()
    return DEFAULT_DB_PATH
