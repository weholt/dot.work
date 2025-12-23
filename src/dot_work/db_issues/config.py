"""Configuration management for db-issues module.

Handles database path configuration and environment-based settings.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DbIssuesConfig:
    """Configuration for db-issues storage.

    Attributes:
        base_path: Base directory for db-issues storage
        db_file: Name of the SQLite database file
    """

    base_path: Path = field(default_factory=lambda: Path(".work/db-issues"))
    db_file: str = "issues.db"

    @classmethod
    def from_env(cls) -> "DbIssuesConfig":
        """Create configuration from environment variable.

        Reads DOT_WORK_DB_ISSUES_PATH environment variable to override
        the default base path.

        Returns:
            DbIssuesConfig instance with environment overrides applied
        """
        base = os.getenv("DOT_WORK_DB_ISSUES_PATH")
        return cls(base_path=Path(base) if base else Path(".work/db-issues"))

    @property
    def db_path(self) -> Path:
        """Get the full path to the database file.

        Returns:
            Path to the SQLite database file
        """
        return self.base_path / self.db_file

    @property
    def db_url(self) -> str:
        """Get the SQLAlchemy database URL.

        Returns:
            Database URL string for SQLAlchemy/sqlmodel
        """
        path_str = str(self.db_path)
        # For absolute paths, strip the leading slash to avoid 4 slashes
        # sqlite:///path -> sqlite:///path (not sqlite:////path)
        if path_str.startswith("/"):
            path_str = path_str[1:]
        return f"sqlite:///{path_str}"

    def ensure_directory(self) -> None:
        """Ensure the base directory exists.

        Creates the base directory and any necessary parent directories.
        """
        self.base_path.mkdir(parents=True, exist_ok=True)


def get_default_db_path() -> Path:
    """Get the default database file path.

    Returns:
        Path to the default database file in .work directory
    """
    config = DbIssuesConfig()
    return config.db_path


def get_db_url() -> str:
    """Get the database URL from environment or default.

    Checks DOT_WORK_DB_ISSUES_PATH environment variable first.
    If not set, returns the default SQLite database URL.

    Returns:
        Database URL string
    """
    config = DbIssuesConfig.from_env()
    # Ensure parent directory exists
    config.ensure_directory()
    return config.db_url


def is_debug_mode() -> bool:
    """Check if debug mode is enabled.

    Returns:
        True if DB_ISSUES_DEBUG is set to a truthy value
    """
    return os.environ.get("DB_ISSUES_DEBUG", "").lower() in ("1", "true", "yes", "on")


__all__ = [
    "DbIssuesConfig",
    "get_default_db_path",
    "get_db_url",
    "is_debug_mode",
]
