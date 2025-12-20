"""Unit tests for agent_review.models module."""

from __future__ import annotations

import time

from agent_review.models import DiffHunk, DiffLine, FileDiff, ReviewComment


class TestDiffLine:
    """Tests for DiffLine model."""

    def test_create_add_line(self) -> None:
        """Test creating an add line."""
        line = DiffLine(kind="add", text="new content", new_lineno=10)
        assert line.kind == "add"
        assert line.text == "new content"
        assert line.new_lineno == 10
        assert line.old_lineno is None

    def test_create_del_line(self) -> None:
        """Test creating a delete line."""
        line = DiffLine(kind="del", text="old content", old_lineno=5)
        assert line.kind == "del"
        assert line.text == "old content"
        assert line.old_lineno == 5
        assert line.new_lineno is None

    def test_create_context_line(self) -> None:
        """Test creating a context line."""
        line = DiffLine(kind="context", text="unchanged", old_lineno=3, new_lineno=3)
        assert line.kind == "context"
        assert line.old_lineno == 3
        assert line.new_lineno == 3

    def test_serialization(self) -> None:
        """Test JSON serialization roundtrip."""
        line = DiffLine(kind="add", text="test", new_lineno=1)
        json_str = line.model_dump_json()
        restored = DiffLine.model_validate_json(json_str)
        assert restored == line


class TestDiffHunk:
    """Tests for DiffHunk model."""

    def test_create_hunk(self) -> None:
        """Test creating a hunk with lines."""
        hunk = DiffHunk(
            header="@@ -1,3 +1,4 @@",
            old_start=1,
            old_len=3,
            new_start=1,
            new_len=4,
            lines=[
                DiffLine(kind="context", text="line1", old_lineno=1, new_lineno=1),
                DiffLine(kind="add", text="new line", new_lineno=2),
            ],
        )
        assert len(hunk.lines) == 2
        assert hunk.old_start == 1
        assert hunk.new_len == 4

    def test_empty_lines_default(self) -> None:
        """Test that lines defaults to empty list."""
        hunk = DiffHunk(header="@@", old_start=1, old_len=1, new_start=1, new_len=1)
        assert hunk.lines == []


class TestFileDiff:
    """Tests for FileDiff model."""

    def test_create_file_diff(self) -> None:
        """Test creating a file diff."""
        diff = FileDiff(path="src/test.py", hunks=[])
        assert diff.path == "src/test.py"
        assert diff.is_binary is False
        assert diff.hunks == []

    def test_binary_file(self) -> None:
        """Test binary file flag."""
        diff = FileDiff(path="image.png", is_binary=True)
        assert diff.is_binary is True


class TestReviewComment:
    """Tests for ReviewComment model."""

    def test_create_comment(self) -> None:
        """Test creating a review comment."""
        comment = ReviewComment(
            review_id="20241220-120000",
            path="src/test.py",
            line=42,
            message="Fix this bug",
        )
        assert comment.review_id == "20241220-120000"
        assert comment.path == "src/test.py"
        assert comment.line == 42
        assert comment.message == "Fix this bug"
        assert comment.side == "new"
        assert comment.suggestion is None

    def test_auto_generated_id(self) -> None:
        """Test that ID is auto-generated."""
        comment = ReviewComment(
            review_id="test",
            path="test.py",
            line=1,
            message="test",
        )
        assert len(comment.id) == 12
        assert comment.id.isalnum()

    def test_unique_ids(self) -> None:
        """Test that generated IDs are unique."""
        ids = set()
        for _ in range(100):
            comment = ReviewComment(review_id="test", path="test.py", line=1, message="test")
            ids.add(comment.id)
        assert len(ids) == 100

    def test_created_timestamp(self) -> None:
        """Test that created timestamp is set."""
        before = time.time()
        comment = ReviewComment(review_id="test", path="test.py", line=1, message="test")
        after = time.time()
        assert before <= comment.created_unix <= after

    def test_with_suggestion(self) -> None:
        """Test comment with code suggestion."""
        comment = ReviewComment(
            review_id="test",
            path="test.py",
            line=10,
            message="Use pathlib",
            suggestion="path = Path(base) / filename",
        )
        assert comment.suggestion == "path = Path(base) / filename"

    def test_with_context(self) -> None:
        """Test comment with context lines."""
        comment = ReviewComment(
            review_id="test",
            path="test.py",
            line=10,
            message="test",
            context_before=["line8", "line9"],
            context_after=["line10", "line11"],
        )
        assert len(comment.context_before) == 2
        assert len(comment.context_after) == 2

    def test_serialization_roundtrip(self) -> None:
        """Test JSON serialization roundtrip."""
        comment = ReviewComment(
            review_id="test",
            path="test.py",
            line=5,
            message="Fix this",
            suggestion="fixed code",
            context_before=["before"],
            context_after=["after"],
        )
        json_str = comment.model_dump_json()
        restored = ReviewComment.model_validate_json(json_str)
        assert restored.review_id == comment.review_id
        assert restored.path == comment.path
        assert restored.message == comment.message
        assert restored.suggestion == comment.suggestion
