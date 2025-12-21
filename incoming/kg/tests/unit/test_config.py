"""Unit tests for configuration management."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from kgshred.config import ConfigError, ensure_db_directory, get_db_path, validate_path


class TestGetDbPath:
    """Tests for get_db_path function."""

    def test_default_db_path_returns_home_directory(self, clean_env: None) -> None:
        """Default DB path should be in user's home directory."""
        result = get_db_path()
        expected = Path.home() / ".kgshred" / "db.sqlite"
        assert result == expected

    def test_custom_db_path_from_env_variable(self, clean_env: None, temp_dir: Path) -> None:
        """DB path can be overridden via environment variable."""
        custom_path = temp_dir / "custom.sqlite"
        os.environ["KG_DB_PATH"] = str(custom_path)

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
        # This exercises line 51 (db_path = get_db_path())
        result = ensure_db_directory(None)
        expected = Path.home() / ".kgshred" / "db.sqlite"
        assert result == expected

    def test_raises_config_error_on_permission_error(self, temp_dir: Path) -> None:
        """Should raise ConfigError when directory cannot be created."""
        # Mock mkdir to raise OSError
        db_path = temp_dir / "subdir" / "db.sqlite"
        with patch.object(Path, "mkdir", side_effect=OSError("Permission denied")):
            with pytest.raises(ConfigError, match="Cannot create database directory"):
                ensure_db_directory(db_path)


class TestValidatePath:
    """Tests for validate_path function."""

    def test_valid_path_returns_path(self, temp_dir: Path) -> None:
        """Valid paths should be returned unchanged."""
        valid_path = temp_dir / "test.sqlite"
        result = validate_path(valid_path)
        assert result == valid_path

    def test_invalid_path_no_extension_raises_error(self, temp_dir: Path) -> None:
        """Invalid paths should raise ConfigError."""
        invalid_path = temp_dir / "no_extension"
        with pytest.raises(ConfigError, match="no file extension"):
            validate_path(invalid_path)

    def test_path_with_nonexistent_parent_validates(self, temp_dir: Path) -> None:
        """Path with nonexistent parent should still validate (can be created)."""
        # This exercises lines 82-90 (the while loop)
        deep_path = temp_dir / "a" / "b" / "c" / "d" / "test.sqlite"
        result = validate_path(deep_path)
        assert result == deep_path

    def test_path_resolve_oserror_raises_config_error(self, temp_dir: Path) -> None:
        """OSError during resolve should raise ConfigError."""
        with patch.object(Path, "resolve", side_effect=OSError("Invalid path")):
            with pytest.raises(ConfigError, match="Invalid path"):
                validate_path(temp_dir / "test.sqlite")

    def test_path_resolve_value_error_raises_config_error(self, temp_dir: Path) -> None:
        """ValueError during resolve should raise ConfigError."""
        with patch.object(Path, "resolve", side_effect=ValueError("Bad path")):
            with pytest.raises(ConfigError, match="Invalid path"):
                validate_path(temp_dir / "test.sqlite")
