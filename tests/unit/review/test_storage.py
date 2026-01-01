"""Tests for dot_work.review.storage module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dot_work.review.models import ReviewComment
from dot_work.review.storage import (
    append_comment,
    ensure_store,
    latest_review_id,
    load_comments,
    new_review_id,
    review_dir,
)


class TestNewReviewId:
    """Tests for new_review_id function."""

    def test_new_review_id_returns_string(self) -> None:
        """Test that new_review_id returns a string."""
        review_id = new_review_id()
        assert isinstance(review_id, str)

    def test_new_review_id_format(self) -> None:
        """Test that review ID has expected format."""
        review_id = new_review_id()
        # Format: YYYYMMDD-HHMMSS-XXX
        parts = review_id.split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 8  # YYYYMMDD
        assert len(parts[1]) == 6  # HHMMSS
        assert len(parts[2]) == 3  # XXX

    def test_new_review_id_unique(self) -> None:
        """Test that review IDs are unique."""
        import time

        id1 = new_review_id()
        time.sleep(0.002)  # Small delay to ensure different millisecond
        id2 = new_review_id()
        assert id1 != id2


class TestEnsureStore:
    """Tests for ensure_store function."""

    @patch("dot_work.review.storage.get_config")
    def test_ensure_store_creates_directories(self, mock_config: MagicMock, tmp_path: Path) -> None:
        """Test that ensure_store creates required directories.

        Args:
            mock_config: Mocked get_config function
            tmp_path: Fixture providing temporary directory
        """
        mock_cfg = MagicMock()
        mock_cfg.storage_dir = ".review"
        mock_config.return_value = mock_cfg

        result = ensure_store(str(tmp_path))

        assert result == tmp_path / ".review"
        assert (tmp_path / ".review").exists()
        assert (tmp_path / ".review" / "reviews").exists()
        assert (tmp_path / ".review" / "exports").exists()

    @patch("dot_work.review.storage.get_config")
    def test_ensure_store_idempotent(self, mock_config: MagicMock, tmp_path: Path) -> None:
        """Test that ensure_store can be called multiple times.

        Args:
            mock_config: Mocked get_config function
            tmp_path: Fixture providing temporary directory
        """
        mock_cfg = MagicMock()
        mock_cfg.storage_dir = ".review"
        mock_config.return_value = mock_cfg

        # Call twice
        ensure_store(str(tmp_path))
        result2 = ensure_store(str(tmp_path))

        assert result2.exists()


class TestReviewDir:
    """Tests for review_dir function."""

    @patch("dot_work.review.storage.get_config")
    def test_review_dir_creates_directory(self, mock_config: MagicMock, tmp_path: Path) -> None:
        """Test that review_dir creates the review directory.

        Args:
            mock_config: Mocked get_config function
            tmp_path: Fixture providing temporary directory
        """
        mock_cfg = MagicMock()
        mock_cfg.storage_dir = ".review"
        mock_config.return_value = mock_cfg

        rd = review_dir(str(tmp_path), "test-review-123")

        assert rd == tmp_path / ".review" / "reviews" / "test-review-123"
        assert rd.exists()


class TestAppendComment:
    """Tests for append_comment function."""

    @patch("dot_work.review.storage.get_config")
    def test_append_comment_writes_file(self, mock_config: MagicMock, tmp_path: Path) -> None:
        """Test that append_comment writes to file.

        Args:
            mock_config: Mocked get_config function
            tmp_path: Fixture providing temporary directory
        """
        mock_cfg = MagicMock()
        mock_cfg.storage_dir = ".review"
        mock_config.return_value = mock_cfg

        comment = ReviewComment(
            id="comment-1",
            review_id="review-123",
            path="test.py",
            side="new",
            line=10,
            message="Fix this",
            context_before=[],
            context_after=[],
        )

        append_comment(str(tmp_path), comment)

        comment_file = tmp_path / ".review" / "reviews" / "review-123" / "comments.jsonl"
        assert comment_file.exists()

        content = comment_file.read_text()
        assert "Fix this" in content


class TestLoadComments:
    """Tests for load_comments function."""

    @patch("dot_work.review.storage.get_config")
    def test_load_comments_empty_when_no_file(self, mock_config: MagicMock, tmp_path: Path) -> None:
        """Test that load_comments returns empty list when file doesn't exist.

        Args:
            mock_config: Mocked get_config function
            tmp_path: Fixture providing temporary directory
        """
        mock_cfg = MagicMock()
        mock_cfg.storage_dir = ".review"
        mock_config.return_value = mock_cfg

        comments = load_comments(str(tmp_path), "review-123")
        assert comments == []

    @patch("dot_work.review.storage.get_config")
    def test_load_comments_filters_by_path(self, mock_config: MagicMock, tmp_path: Path) -> None:
        """Test that load_comments filters by file path.

        Args:
            mock_config: Mocked get_config function
            tmp_path: Fixture providing temporary directory
        """
        mock_cfg = MagicMock()
        mock_cfg.storage_dir = ".review"
        mock_config.return_value = mock_cfg

        # Create two comments for different files
        comment1 = ReviewComment(
            id="c1",
            review_id="review-123",
            path="file1.py",
            side="new",
            line=10,
            message="Comment 1",
            context_before=[],
            context_after=[],
        )
        comment2 = ReviewComment(
            id="c2",
            review_id="review-123",
            path="file2.py",
            side="new",
            line=20,
            message="Comment 2",
            context_before=[],
            context_after=[],
        )

        append_comment(str(tmp_path), comment1)
        append_comment(str(tmp_path), comment2)

        # Load comments for file1.py only
        comments = load_comments(str(tmp_path), "review-123", path="file1.py")
        assert len(comments) == 1
        assert comments[0].path == "file1.py"

    @patch("dot_work.review.storage.get_config")
    def test_load_comments_returns_all_when_no_filter(self, mock_config: MagicMock, tmp_path: Path) -> None:
        """Test that load_comments returns all comments when no path filter.

        Args:
            mock_config: Mocked get_config function
            tmp_path: Fixture providing temporary directory
        """
        mock_cfg = MagicMock()
        mock_cfg.storage_dir = ".review"
        mock_config.return_value = mock_cfg

        comment1 = ReviewComment(
            id="c1",
            review_id="review-123",
            path="file1.py",
            side="new",
            line=10,
            message="Comment 1",
            context_before=[],
            context_after=[],
        )
        comment2 = ReviewComment(
            id="c2",
            review_id="review-123",
            path="file2.py",
            side="new",
            line=20,
            message="Comment 2",
            context_before=[],
            context_after=[],
        )

        append_comment(str(tmp_path), comment1)
        append_comment(str(tmp_path), comment2)

        comments = load_comments(str(tmp_path), "review-123")
        assert len(comments) == 2


class TestLatestReviewId:
    """Tests for latest_review_id function."""

    @patch("dot_work.review.storage.get_config")
    def test_latest_review_id_returns_none_when_empty(self, mock_config: MagicMock, tmp_path: Path) -> None:
        """Test that latest_review_id returns None when no reviews exist.

        Args:
            mock_config: Mocked get_config function
            tmp_path: Fixture providing temporary directory
        """
        mock_cfg = MagicMock()
        mock_cfg.storage_dir = ".review"
        mock_config.return_value = mock_cfg

        review_id = latest_review_id(str(tmp_path))
        assert review_id is None

    @patch("dot_work.review.storage.get_config")
    def test_latest_review_id_returns_most_recent(self, mock_config: MagicMock, tmp_path: Path) -> None:
        """Test that latest_review_id returns the most recent review.

        Args:
            mock_config: Mocked get_config function
            tmp_path: Fixture providing temporary directory
        """
        mock_cfg = MagicMock()
        mock_cfg.storage_dir = ".review"
        mock_config.return_value = mock_cfg

        # Create multiple review directories
        review_dir(str(tmp_path), "review-001")
        review_dir(str(tmp_path), "review-002")
        review_dir(str(tmp_path), "review-003")

        latest = latest_review_id(str(tmp_path))
        assert latest == "review-003"
