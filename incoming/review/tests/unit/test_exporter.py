"""Unit tests for agent_review.exporter module."""

from __future__ import annotations

from pathlib import Path

from agent_review.exporter import export_agent_md
from agent_review.models import ReviewComment
from agent_review.storage import append_comment, review_dir


class TestExportAgentMd:
    """Tests for export_agent_md function."""

    def test_empty_export(self, temp_dir: Path) -> None:
        """Test exporting empty review."""
        review_dir(str(temp_dir), "empty-review")
        out = export_agent_md(str(temp_dir), "empty-review")

        assert out.exists()
        content = out.read_text()
        assert "# agent-review bundle" in content
        assert "empty-review" in content

    def test_export_with_comments(self, temp_dir: Path) -> None:
        """Test exporting review with comments."""
        append_comment(
            str(temp_dir),
            ReviewComment(
                review_id="test-review",
                path="src/main.py",
                line=42,
                message="This needs refactoring",
            ),
        )

        out = export_agent_md(str(temp_dir), "test-review")
        content = out.read_text()

        assert "## src/main.py" in content
        assert "L42" in content
        assert "This needs refactoring" in content

    def test_export_with_suggestion(self, temp_dir: Path) -> None:
        """Test exporting comment with code suggestion."""
        append_comment(
            str(temp_dir),
            ReviewComment(
                review_id="test-review",
                path="test.py",
                line=10,
                message="Use pathlib",
                suggestion="path = Path(base) / filename",
            ),
        )

        out = export_agent_md(str(temp_dir), "test-review")
        content = out.read_text()

        assert "**Suggested change**" in content
        assert "```suggestion" in content
        assert "Path(base) / filename" in content

    def test_export_with_context(self, temp_dir: Path) -> None:
        """Test exporting comment with context."""
        append_comment(
            str(temp_dir),
            ReviewComment(
                review_id="test-review",
                path="test.py",
                line=5,
                message="Fix",
                context_before=["line3", "line4"],
                context_after=["line5", "line6"],
            ),
        )

        out = export_agent_md(str(temp_dir), "test-review")
        content = out.read_text()

        assert "**Context**" in content
        assert ">>> TARGET LINE: 5" in content

    def test_export_groups_by_file(self, temp_dir: Path) -> None:
        """Test that export groups comments by file."""
        append_comment(
            str(temp_dir),
            ReviewComment(review_id="test", path="file1.py", line=1, message="Comment 1"),
        )
        append_comment(
            str(temp_dir),
            ReviewComment(review_id="test", path="file2.py", line=1, message="Comment 2"),
        )
        append_comment(
            str(temp_dir),
            ReviewComment(review_id="test", path="file1.py", line=10, message="Comment 3"),
        )

        out = export_agent_md(str(temp_dir), "test")
        content = out.read_text()

        # Both files should have sections
        assert "## file1.py" in content
        assert "## file2.py" in content

        # Comments for same file should be together
        file1_pos = content.index("## file1.py")
        file2_pos = content.index("## file2.py")
        comment1_pos = content.index("Comment 1")
        comment3_pos = content.index("Comment 3")

        # Both file1 comments should be before file2 section
        assert file1_pos < comment1_pos < file2_pos
        assert file1_pos < comment3_pos < file2_pos

    def test_export_sorts_by_line(self, temp_dir: Path) -> None:
        """Test that comments are sorted by line number."""
        append_comment(
            str(temp_dir),
            ReviewComment(review_id="test", path="test.py", line=50, message="Later"),
        )
        append_comment(
            str(temp_dir),
            ReviewComment(review_id="test", path="test.py", line=10, message="Earlier"),
        )

        out = export_agent_md(str(temp_dir), "test")
        content = out.read_text()

        # Earlier line should come first
        assert content.index("L10") < content.index("L50")
        assert content.index("Earlier") < content.index("Later")
