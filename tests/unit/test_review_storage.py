"""Unit tests for dot_work.review.storage module."""

from __future__ import annotations

from pathlib import Path

from dot_work.review.models import ReviewComment
from dot_work.review.storage import (
    append_comment,
    ensure_store,
    latest_review_id,
    load_comments,
    new_review_id,
    review_dir,
)


class TestEnsureStore:
    """Tests for ensure_store function."""

    def test_creates_structure(self, tmp_path: Path) -> None:
        """Test that storage structure is created."""
        base = ensure_store(str(tmp_path))
        assert base.exists()
        assert (base / "reviews").exists()
        assert (base / "exports").exists()

    def test_idempotent(self, tmp_path: Path) -> None:
        """Test that calling multiple times is safe."""
        base1 = ensure_store(str(tmp_path))
        base2 = ensure_store(str(tmp_path))
        assert base1 == base2


class TestNewReviewId:
    """Tests for new_review_id function."""

    def test_format(self) -> None:
        """Test review ID format."""
        rid = new_review_id()
        # Format: YYYYMMDD-HHMMSS
        assert len(rid) == 15
        assert rid[8] == "-"

    def test_sortable(self) -> None:
        """Test that IDs are sortable."""
        import time

        id1 = new_review_id()
        time.sleep(0.01)  # Small delay
        id2 = new_review_id()
        # IDs should be sortable chronologically
        assert id1 <= id2


class TestReviewDir:
    """Tests for review_dir function."""

    def test_creates_directory(self, tmp_path: Path) -> None:
        """Test that review directory is created."""
        rd = review_dir(str(tmp_path), "test-review")
        assert rd.exists()
        assert rd.name == "test-review"


class TestAppendAndLoadComments:
    """Tests for append_comment and load_comments functions."""

    def test_append_and_load(self, tmp_path: Path) -> None:
        """Test appending and loading comments."""
        comment = ReviewComment(
            review_id="test-review",
            path="src/test.py",
            line=10,
            message="Fix this",
        )
        append_comment(str(tmp_path), comment)

        comments = load_comments(str(tmp_path), "test-review")
        assert len(comments) == 1
        assert comments[0].path == "src/test.py"
        assert comments[0].message == "Fix this"

    def test_multiple_comments(self, tmp_path: Path) -> None:
        """Test appending multiple comments."""
        for i in range(3):
            comment = ReviewComment(
                review_id="test-review",
                path="test.py",
                line=i + 1,
                message=f"Comment {i}",
            )
            append_comment(str(tmp_path), comment)

        comments = load_comments(str(tmp_path), "test-review")
        assert len(comments) == 3

    def test_filter_by_path(self, tmp_path: Path) -> None:
        """Test filtering comments by path."""
        append_comment(
            str(tmp_path),
            ReviewComment(review_id="test", path="file1.py", line=1, message="msg1"),
        )
        append_comment(
            str(tmp_path),
            ReviewComment(review_id="test", path="file2.py", line=1, message="msg2"),
        )

        comments = load_comments(str(tmp_path), "test", path="file1.py")
        assert len(comments) == 1
        assert comments[0].path == "file1.py"

    def test_load_empty_review(self, tmp_path: Path) -> None:
        """Test loading from non-existent review."""
        comments = load_comments(str(tmp_path), "nonexistent")
        assert comments == []


class TestLatestReviewId:
    """Tests for latest_review_id function."""

    def test_no_reviews(self, tmp_path: Path) -> None:
        """Test with no reviews."""
        result = latest_review_id(str(tmp_path))
        assert result is None

    def test_single_review(self, tmp_path: Path) -> None:
        """Test with single review."""
        review_dir(str(tmp_path), "20241220-120000")
        result = latest_review_id(str(tmp_path))
        assert result == "20241220-120000"

    def test_multiple_reviews(self, tmp_path: Path) -> None:
        """Test with multiple reviews - returns latest."""
        review_dir(str(tmp_path), "20241219-100000")
        review_dir(str(tmp_path), "20241220-150000")
        review_dir(str(tmp_path), "20241220-120000")

        result = latest_review_id(str(tmp_path))
        # Should return the lexicographically last (most recent)
        assert result == "20241220-150000"
