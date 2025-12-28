"""Configuration management for db-issues module.

Handles database path configuration and environment-based settings.

Security: Environment variable paths are validated to prevent directory
traversal attacks. Only paths within the current working directory or
home directory (~/) are allowed.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path


def _is_subpath(path: Path, base: Path) -> bool:
    """Check if a path is a subdirectory of another path.

    Args:
        path: The path to check.
        base: The base directory.

    Returns:
        True if path is a subdirectory of base, False otherwise.
    """
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


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

        The path is validated to prevent directory traversal attacks:
        - Paths with .. are resolved and must stay within allowed directories
        - Relative paths (without ~) must stay within current working directory
        - Paths starting with ~/ must stay within home directory

        Returns:
            DbIssuesConfig instance with environment overrides applied

        Raises:
            ValueError: If path escapes allowed directories.
        """
        base = os.getenv("DOT_WORK_DB_ISSUES_PATH")

        if not base:
            return cls(base_path=Path(".work/db-issues").resolve())

        # Check if path explicitly uses home directory (~)
        uses_home = base.startswith("~")

        # Expand ~ for home directory
        input_path = Path(base).expanduser()

        # Resolve to absolute path (this normalizes .. and symlinks)
        resolved_path = input_path.resolve()

        # Validate based on whether user explicitly requested home directory
        cwd = Path.cwd().resolve()

        if uses_home:
            # For ~ paths, require they stay within home directory
            home = Path.home().resolve()
            if not _is_subpath(resolved_path, home):
                raise ValueError(
                    f"Invalid DOT_WORK_DB_ISSUES_PATH: '{base}' resolves to "
                    f"'{resolved_path}' which is outside the home directory. "
                    f"Paths starting with ~/ must stay within home directory."
                )
        else:
            # For relative paths, require they stay within current working directory
            if not _is_subpath(resolved_path, cwd):
                raise ValueError(
                    f"Invalid DOT_WORK_DB_ISSUES_PATH: '{base}' resolves to "
                    f"'{resolved_path}' which is outside the current working "
                    f"directory. Use ~/ prefix for home directory paths."
                )

        return cls(base_path=resolved_path)

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
