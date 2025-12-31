"""Unit tests for configuration management."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from dot_work.knowledge_graph.config import (
    ConfigError,
    ensure_db_directory,
    get_db_path,
)


class TestGetDbPath:
    """Tests for get_db_path function."""

    def test_default_db_path_returns_work_directory(self, clean_env: None) -> None:
        """Default DB path should be in .work/kg directory."""
        result = get_db_path()
        expected = Path(".work/kg/db.sqlite")
        assert result == expected

    def test_custom_db_path_from_env_variable(self, clean_env: None, temp_dir: Path) -> None:
        """DB path can be overridden via environment variable."""
        custom_path = temp_dir / "custom.sqlite"
        os.environ["DOT_WORK_KG_DB_PATH"] = str(custom_path)

        result = get_db_path()
        assert result == custom_path


class TestEnsureDbDirectory:
    """Tests for ensure_db_directory function."""

    def test_create_db_directory_if_not_exists(self, temp_dir: Path) -> None:
        """Config should create parent directories for DB path."""
        nested_path = temp_dir / "subdir1" / "subdir2" / "db.sqlite"
        result = ensure_db_directory(nested_path)

        assert result == nested_path
        assert nested_path.parent.exists()

    def test_returns_path_when_directory_exists(self, temp_dir: Path) -> None:
        """Should return path when directory already exists."""
        db_path = temp_dir / "db.sqlite"
        result = ensure_db_directory(db_path)
        assert result == db_path

    def test_uses_default_path_when_none(self, clean_env: None) -> None:
        """Should use get_db_path() when no path provided."""
        result = ensure_db_directory(None)
        expected = Path(".work/kg/db.sqlite")
        assert result == expected

    def test_raises_config_error_on_permission_error(self, temp_dir: Path) -> None:
        """Should raise ConfigError when directory cannot be created."""
        db_path = temp_dir / "subdir" / "db.sqlite"
        with patch.object(Path, "mkdir", side_effect=OSError("Permission denied")):
            with pytest.raises(ConfigError, match="Cannot create database directory"):
                ensure_db_directory(db_path)
