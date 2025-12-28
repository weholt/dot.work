"""Tests for directory traversal vulnerability in DbIssuesConfig (CR-074)."""

from __future__ import annotations

from pathlib import Path

import pytest

from dot_work.db_issues.config import DbIssuesConfig, _is_subpath, get_db_url


class TestDbIssuesConfigPathTraversal:
    """Tests for path traversal vulnerability in DbIssuesConfig."""

    def test_from_env_rejects_parent_traversal(self, monkeypatch) -> None:
        """Test that parent directory traversal (../) is rejected."""
        monkeypatch.setenv("DOT_WORK_DB_ISSUES_PATH", "../../../etc/passwd")

        with pytest.raises(ValueError, match="path|outside|invalid"):
            DbIssuesConfig.from_env()

    def test_from_env_rejects_absolute_path_outside_work(self, monkeypatch) -> None:
        """Test that absolute paths outside the working directory are rejected."""
        monkeypatch.setenv("DOT_WORK_DB_ISSUES_PATH", "/tmp/sensitive-dir")

        with pytest.raises(ValueError, match="path|outside|invalid"):
            DbIssuesConfig.from_env()

    def test_from_env_allows_relative_path_within_work(self, monkeypatch) -> None:
        """Test that relative paths within .work are allowed."""
        monkeypatch.setenv("DOT_WORK_DB_ISSUES_PATH", ".work/custom-db")

        config = DbIssuesConfig.from_env()
        assert config.base_path == Path(".work/custom-db").resolve()

    def test_from_env_allows_explicit_current_directory(self, monkeypatch) -> None:
        """Test that explicit current directory reference is allowed."""
        monkeypatch.setenv("DOT_WORK_DB_ISSUES_PATH", "./my-db")

        config = DbIssuesConfig.from_env()
        assert config.base_path == Path("./my-db").resolve()

    def test_from_env_rejects_nested_parent_traversal(self, monkeypatch) -> None:
        """Test that nested parent directory traversal is rejected."""
        monkeypatch.setenv("DOT_WORK_DB_ISSUES_PATH", "subdir/../../../etc")

        with pytest.raises(ValueError, match="path|outside|invalid"):
            DbIssuesConfig.from_env()

    def test_from_env_allows_home_expansion(self, monkeypatch) -> None:
        """Test that home directory (~) expansion is allowed."""
        # Test with ~ prefix (home directory expansion)
        monkeypatch.setenv("DOT_WORK_DB_ISSUES_PATH", "~/.work-db-test")

        config = DbIssuesConfig.from_env()
        # The path should resolve to a subdirectory of home
        home = Path.home()
        assert _is_subpath(config.base_path, home)
        # Should be under home directory
        assert str(config.base_path).startswith(str(home))

    def test_ensure_directory_rejects_traversed_path(self, monkeypatch) -> None:
        """Test that ensure_directory fails with traversed paths."""
        monkeypatch.setenv("DOT_WORK_DB_ISSUES_PATH", "../../../tmp")

        with pytest.raises(ValueError, match="path|outside|invalid"):
            config = DbIssuesConfig.from_env()
            config.ensure_directory()

    def test_db_path_property_with_valid_config(self) -> None:
        """Test that db_path property works with valid configuration."""
        config = DbIssuesConfig(base_path=Path(".work/test-db").resolve())
        expected = Path(".work/test-db/issues.db").resolve()
        assert config.db_path == expected

    def test_db_url_with_valid_config(self) -> None:
        """Test that db_url generation works with valid configuration."""
        config = DbIssuesConfig(base_path=Path(".work/test-db"))
        url = config.db_url
        assert url.startswith("sqlite:///")
        assert "test-db" in url or "Test" in url  # Path may vary by OS

    def test_from_env_with_empty_string_uses_default(self, monkeypatch) -> None:
        """Test that empty environment variable uses default path."""
        monkeypatch.setenv("DOT_WORK_DB_ISSUES_PATH", "")

        config = DbIssuesConfig.from_env()
        assert config.base_path == Path(".work/db-issues").resolve()

    def test_from_env_without_env_var_uses_default(self, monkeypatch) -> None:
        """Test that missing environment variable uses default path."""
        monkeypatch.delenv("DOT_WORK_DB_ISSUES_PATH", raising=False)

        config = DbIssuesConfig.from_env()
        assert config.base_path == Path(".work/db-issues").resolve()

    def test_get_db_url_with_traversed_path_fails(self, monkeypatch) -> None:
        """Test that get_db_url fails with directory traversal in env var."""
        monkeypatch.setenv("DOT_WORK_DB_ISSUES_PATH", "../../../etc")

        with pytest.raises(ValueError, match="path|outside|invalid"):
            get_db_url()
