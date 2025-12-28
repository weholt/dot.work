"""Tests for db-issues configuration."""

import os
from pathlib import Path

import pytest

from dot_work.db_issues.config import DbIssuesConfig, get_db_url, is_debug_mode


class TestDbIssuesConfig:
    """Tests for DbIssuesConfig dataclass."""

    def test_default_config_values(self) -> None:
        """Test default configuration values."""
        config = DbIssuesConfig()
        assert config.base_path == Path(".work/db-issues")
        assert config.db_file == "issues.db"

    def test_db_path_property(self) -> None:
        """Test db_path property returns correct path."""
        config = DbIssuesConfig()
        assert config.db_path == Path(".work/db-issues/issues.db")

    def test_db_url_property(self) -> None:
        """Test db_url property returns correct URL."""
        config = DbIssuesConfig()
        assert config.db_url == "sqlite:///.work/db-issues/issues.db"

    def test_custom_base_path(self) -> None:
        """Test configuration with custom base path."""
        config = DbIssuesConfig(base_path=Path("/custom/location"))
        assert config.base_path == Path("/custom/location")
        assert config.db_path == Path("/custom/location/issues.db")

    def test_custom_db_file(self) -> None:
        """Test configuration with custom database file name."""
        config = DbIssuesConfig(db_file="custom.db")
        assert config.db_file == "custom.db"
        assert config.db_path == Path(".work/db-issues/custom.db")


class TestDbIssuesConfigFromEnv:
    """Tests for DbIssuesConfig.from_env class method."""

    def test_from_env_without_override(self) -> None:
        """Test from_env without environment variable uses default."""
        # Ensure env var is not set
        if "DOT_WORK_DB_ISSUES_PATH" in os.environ:
            del os.environ["DOT_WORK_DB_ISSUES_PATH"]

        config = DbIssuesConfig.from_env()
        # from_env() calls resolve() for security, so we compare resolved paths
        assert config.base_path == Path(".work/db-issues").resolve()

    def test_from_env_with_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test from_env with environment variable override."""
        # Use a relative path within CWD (allowed by security validation)
        monkeypatch.setenv("DOT_WORK_DB_ISSUES_PATH", "custom/db-issues")
        config = DbIssuesConfig.from_env()
        # from_env() resolves paths for security, so compare resolved paths
        assert config.base_path == Path("custom/db-issues").resolve()

    def test_from_env_db_url_with_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test db_url with environment variable override."""
        # Use a relative path within CWD (allowed by security validation)
        monkeypatch.setenv("DOT_WORK_DB_ISSUES_PATH", "custom/db-issues")
        config = DbIssuesConfig.from_env()
        expected_path = Path("custom/db-issues").resolve() / "issues.db"
        # db_url strips leading slash from absolute paths
        assert config.db_url == f"sqlite:///{str(expected_path)[1:]}"


class TestEnsureDirectory:
    """Tests for ensure_directory method."""

    def test_ensure_directory_creates_path(self, tmp_path: Path) -> None:
        """Test ensure_directory creates the directory."""
        config = DbIssuesConfig(base_path=tmp_path / "new-dir")
        assert not config.base_path.exists()

        config.ensure_directory()
        assert config.base_path.exists()
        assert config.base_path.is_dir()

    def test_ensure_directory_idempotent(self, tmp_path: Path) -> None:
        """Test ensure_directory is safe to call multiple times."""
        config = DbIssuesConfig(base_path=tmp_path / "test-dir")
        config.ensure_directory()
        config.ensure_directory()  # Should not raise
        assert config.base_path.exists()


class TestGetDbUrl:
    """Tests for get_db_url function."""

    def test_get_db_url_returns_valid_url(self) -> None:
        """Test get_db_url returns a valid SQLite URL."""
        url = get_db_url()
        assert url.startswith("sqlite:///")
        assert "issues.db" in url


class TestIsDebugMode:
    """Tests for is_debug_mode function."""

    def test_is_debug_mode_default_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test is_debug_mode returns False by default."""
        monkeypatch.delenv("DB_ISSUES_DEBUG", raising=False)
        assert is_debug_mode() is False

    def test_is_debug_mode_with_true_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test is_debug_mode returns True for truthy values."""
        for value in ["1", "true", "TRUE", "yes", "YES", "on", "ON"]:
            monkeypatch.setenv("DB_ISSUES_DEBUG", value)
            assert is_debug_mode() is True

    def test_is_debug_mode_with_false_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test is_debug_mode returns False for falsy values."""
        for value in ["0", "false", "FALSE", "no", "NO", "off", "OFF"]:
            monkeypatch.setenv("DB_ISSUES_DEBUG", value)
            assert is_debug_mode() is False
