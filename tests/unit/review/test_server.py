"""Tests for dot_work.review.server module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dot_work.review.server import (
    AddCommentIn,
    _check_rate_limit,
    _free_port,
    _get_auth_token,
    _verify_path_safe,
    create_app,
    pick_port,
)


class TestVerifyPathSafe:
    """Tests for _verify_path_safe function."""

    def test_verify_path_safe_accepts_valid_path(self, tmp_path: Path) -> None:
        """Test that valid paths within root are accepted.

        Args:
            tmp_path: Fixture providing temporary directory
        """
        # Valid relative paths should not raise
        _verify_path_safe(tmp_path, "file.py")
        _verify_path_safe(tmp_path, "subdir/file.py")
        _verify_path_safe(tmp_path, "a/b/c/d/file.py")

    def test_verify_path_safe_accepts_empty_path(self, tmp_path: Path) -> None:
        """Test that empty path is accepted (returns without error).

        Args:
            tmp_path: Fixture providing temporary directory
        """
        # Empty path should not raise
        _verify_path_safe(tmp_path, "")

    def test_verify_path_safe_rejects_parent_traversal(self, tmp_path: Path) -> None:
        """Test that paths with parent traversal are rejected.

        Args:
            tmp_path: Fixture providing temporary directory
        """
        with pytest.raises(Exception):  # HTTPException
            _verify_path_safe(tmp_path, "../etc/passwd")

    def test_verify_path_safe_rejects_absolute_path(self, tmp_path: Path) -> None:
        """Test that absolute paths outside root are rejected.

        Args:
            tmp_path: Fixture providing temporary directory
        """
        with pytest.raises(Exception):  # HTTPException
            _verify_path_safe(tmp_path, "/etc/passwd")


class TestCheckRateLimit:
    """Tests for _check_rate_limit function."""

    def test_check_rate_limit_allows_first_request(self) -> None:
        """Test that first request from a client is allowed."""
        assert _check_rate_limit("client1") is True

    def test_check_rate_limit_allows_under_threshold(self) -> None:
        """Test that requests under threshold are allowed."""
        client = "client2"
        for _ in range(50):
            assert _check_rate_limit(client) is True

    def test_check_rate_limit_blocks_over_threshold(self) -> None:
        """Test that requests over threshold are blocked."""
        client = "client3"
        # Fill up to limit
        for _ in range(60):
            _check_rate_limit(client)
        # Next request should be blocked
        assert _check_rate_limit(client) is False

    def test_check_rate_limit_custom_window(self) -> None:
        """Test rate limit with custom window."""
        client = "client4"
        # Fill up to custom limit
        for _ in range(10):
            assert _check_rate_limit(client, max_requests=10, window=60) is True
        # Next request should be blocked
        assert _check_rate_limit(client, max_requests=10, window=60) is False

    def test_check_rate_limit_cleanup_old(self) -> None:
        """Test that old entries are cleaned up."""
        client = "client5"
        # Add old timestamps (simulate by directly manipulating store)
        import time

        from dot_work.review import server

        old_time = time.time() - 120  # 2 minutes ago
        server._rate_limit_store[client] = [old_time] * 100

        # Should clean old entries and allow new request
        assert _check_rate_limit(client) is True


class TestFreePort:
    """Tests for _free_port function."""

    def test_free_port_returns_int(self) -> None:
        """Test that _free_port returns an integer port."""
        port = _free_port()
        assert isinstance(port, int)
        assert 1024 <= port <= 65535

    def test_free_port_returns_different_ports(self) -> None:
        """Test that _free_port can return different ports."""
        ports = {_free_port() for _ in range(10)}
        assert len(ports) > 1  # Should get variety


class TestPickPort:
    """Tests for pick_port function."""

    def test_pick_port_returns_provided_port(self) -> None:
        """Test that pick_port returns provided port when given."""
        assert pick_port(8080) == 8080

    def test_pick_port_zero_returns_free_port(self) -> None:
        """Test that pick_port(0) returns a free port."""
        port = pick_port(0)
        assert isinstance(port, int)
        assert 1024 <= port <= 65535

    def test_pick_port_none_returns_free_port(self) -> None:
        """Test that pick_port(None) returns a free port."""
        port = pick_port(None)
        assert isinstance(port, int)
        assert 1024 <= port <= 65535


class TestGetAuthToken:
    """Tests for _get_auth_token function."""

    def test_get_auth_token_returns_none_by_default(self) -> None:
        """Test that _get_auth_token returns None when env var not set."""
        # Clear the env var if set
        import os

        token = os.getenv("REVIEW_AUTH_TOKEN")
        if token:
            del os.environ["REVIEW_AUTH_TOKEN"]
        result = _get_auth_token()
        assert result is None

    @patch.dict("os.environ", {"REVIEW_AUTH_TOKEN": "test-token"})
    def test_get_auth_token_returns_env_value(self) -> None:
        """Test that _get_auth_token returns env var value when set."""
        result = _get_auth_token()
        assert result == "test-token"


class TestAddCommentIn:
    """Tests for AddCommentIn model."""

    def test_add_comment_in_creation(self) -> None:
        """Test creating AddCommentIn with required fields."""
        comment = AddCommentIn(path="test.py", line=10, message="Fix this")
        assert comment.path == "test.py"
        assert comment.line == 10
        assert comment.message == "Fix this"
        assert comment.side == "new"  # default
        assert comment.suggestion is None  # default

    def test_add_comment_in_with_suggestion(self) -> None:
        """Test creating AddCommentIn with suggestion."""
        comment = AddCommentIn(
            path="test.py", line=10, message="Fix this", suggestion="Use X instead"
        )
        assert comment.suggestion == "Use X instead"

    def test_add_comment_in_old_side(self) -> None:
        """Test creating AddCommentIn with old side."""
        comment = AddCommentIn(path="test.py", line=10, message="Fix this", side="old")
        assert comment.side == "old"


class TestCreateApp:
    """Tests for create_app function."""

    @patch("dot_work.review.server.list_tracked_files")
    @patch("dot_work.review.server.list_all_files")
    @patch("dot_work.review.server.changed_files")
    @patch("dot_work.review.server.ensure_git_repo")
    @patch("dot_work.review.server.repo_root")
    def test_create_app_returns_fastapi_app(
        self,
        mock_repo_root: MagicMock,
        mock_ensure: MagicMock,
        mock_changed: MagicMock,
        mock_all_files: MagicMock,
        mock_tracked: MagicMock,
    ) -> None:
        """Test that create_app returns a FastAPI app instance.

        Args:
            mock_repo_root: Mocked repo_root function
            mock_ensure: Mocked ensure_git_repo function
            mock_changed: Mocked changed_files function
            mock_all_files: Mocked list_all_files function
            mock_tracked: Mocked list_tracked_files function
        """
        mock_repo_root.return_value = Path("/fake/repo")
        mock_all_files.return_value = ["file1.py", "file2.py"]
        mock_tracked.return_value = ["file1.py"]
        mock_changed.return_value = set()
        app, review_id = create_app("/fake/repo", base_ref="HEAD")

        from fastapi import FastAPI

        assert isinstance(app, FastAPI)
        assert isinstance(review_id, str)
        assert len(review_id) > 0

    @patch("dot_work.review.server.list_tracked_files")
    @patch("dot_work.review.server.list_all_files")
    @patch("dot_work.review.server.changed_files")
    @patch("dot_work.review.server.ensure_git_repo")
    @patch("dot_work.review.server.repo_root")
    def test_create_app_generates_unique_review_ids(
        self,
        mock_repo_root: MagicMock,
        mock_ensure: MagicMock,
        mock_changed: MagicMock,
        mock_all_files: MagicMock,
        mock_tracked: MagicMock,
    ) -> None:
        """Test that create_app generates unique review IDs.

        Args:
            mock_repo_root: Mocked repo_root function
            mock_ensure: Mocked ensure_git_repo function
            mock_changed: Mocked changed_files function
            mock_all_files: Mocked list_all_files function
            mock_tracked: Mocked list_tracked_files function
        """
        mock_repo_root.return_value = Path("/fake/repo")
        mock_all_files.return_value = ["file1.py"]
        mock_tracked.return_value = ["file1.py"]
        mock_changed.return_value = set()
        _, review_id1 = create_app("/fake/repo", base_ref="HEAD")
        _, review_id2 = create_app("/fake/repo", base_ref="HEAD")

        assert review_id1 != review_id2
