"""Unit tests for agent_review.git module."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agent_review.git import (
    GitError,
    changed_files,
    ensure_git_repo,
    get_unified_diff,
    list_tracked_files,
    parse_unified_diff,
    read_file_text,
    repo_root,
)


class TestEnsureGitRepo:
    """Tests for ensure_git_repo function."""

    def test_valid_repo(self, git_repo: Path) -> None:
        """Test with a valid git repository."""
        # Should not raise
        ensure_git_repo(str(git_repo))

    def test_not_a_repo(self, temp_dir: Path) -> None:
        """Test with a non-git directory."""
        with pytest.raises(GitError):
            ensure_git_repo(str(temp_dir))


class TestRepoRoot:
    """Tests for repo_root function."""

    def test_get_root(self, git_repo: Path) -> None:
        """Test getting repository root."""
        root = repo_root(str(git_repo))
        assert Path(root).resolve() == git_repo.resolve()

    def test_from_subdirectory(self, git_repo: Path) -> None:
        """Test getting root from a subdirectory."""
        subdir = git_repo / "subdir"
        subdir.mkdir()
        root = repo_root(str(subdir))
        assert Path(root).resolve() == git_repo.resolve()


class TestListTrackedFiles:
    """Tests for list_tracked_files function."""

    def test_list_files(self, git_repo: Path) -> None:
        """Test listing tracked files."""
        files = list_tracked_files(str(git_repo))
        assert "test.txt" in files

    def test_new_tracked_file(self, git_repo: Path) -> None:
        """Test that newly added files appear in list."""
        new_file = git_repo / "new.py"
        new_file.write_text("# new file\n")
        subprocess.run(["git", "add", "new.py"], cwd=git_repo, check=True)

        files = list_tracked_files(str(git_repo))
        assert "new.py" in files
        assert "test.txt" in files


class TestChangedFiles:
    """Tests for changed_files function."""

    def test_no_changes(self, git_repo: Path) -> None:
        """Test with no uncommitted changes."""
        changes = changed_files(str(git_repo))
        assert len(changes) == 0

    def test_with_changes(self, git_repo: Path) -> None:
        """Test with uncommitted changes."""
        test_file = git_repo / "test.txt"
        test_file.write_text("modified content\n")

        changes = changed_files(str(git_repo))
        assert "test.txt" in changes


class TestReadFileText:
    """Tests for read_file_text function."""

    def test_read_existing_file(self, git_repo: Path) -> None:
        """Test reading an existing file."""
        content = read_file_text(str(git_repo), "test.txt")
        assert content == "initial content\n"

    def test_read_nonexistent_file(self, git_repo: Path) -> None:
        """Test reading a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            read_file_text(str(git_repo), "nonexistent.txt")

    def test_path_traversal_blocked(self, git_repo: Path) -> None:
        """Test that path traversal is blocked."""
        with pytest.raises(GitError):
            read_file_text(str(git_repo), "../../../etc/passwd")


class TestGetUnifiedDiff:
    """Tests for get_unified_diff function."""

    def test_no_diff(self, git_repo: Path) -> None:
        """Test with no changes."""
        diff = get_unified_diff(str(git_repo), "test.txt")
        assert diff.strip() == ""

    def test_with_diff(self, git_repo: Path) -> None:
        """Test with changes."""
        test_file = git_repo / "test.txt"
        test_file.write_text("modified content\n")

        diff = get_unified_diff(str(git_repo), "test.txt")
        assert "-initial content" in diff
        assert "+modified content" in diff


class TestParseUnifiedDiff:
    """Tests for parse_unified_diff function."""

    def test_empty_diff(self) -> None:
        """Test parsing empty diff."""
        result = parse_unified_diff("test.py", "")
        assert result.path == "test.py"
        assert result.hunks == []
        assert result.is_binary is False

    def test_binary_diff(self) -> None:
        """Test parsing binary file diff."""
        diff_text = "Binary files a/image.png and b/image.png differ"
        result = parse_unified_diff("image.png", diff_text)
        assert result.is_binary is True
        assert result.hunks == []

    def test_simple_diff(self) -> None:
        """Test parsing a simple diff."""
        diff_text = """diff --git a/test.py b/test.py
index abc123..def456 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 line1
-old line
+new line
+added line
 line3
"""
        result = parse_unified_diff("test.py", diff_text)
        assert result.path == "test.py"
        assert len(result.hunks) == 1

        hunk = result.hunks[0]
        assert hunk.old_start == 1
        assert hunk.old_len == 3
        assert hunk.new_start == 1
        assert hunk.new_len == 4

        # Check line types
        kinds = [line.kind for line in hunk.lines]
        assert "context" in kinds
        assert "add" in kinds
        assert "del" in kinds

    def test_multiple_hunks(self) -> None:
        """Test parsing diff with multiple hunks."""
        diff_text = """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1,2 +1,2 @@
-old1
+new1
 same
@@ -10,2 +10,2 @@
-old2
+new2
 same2
"""
        result = parse_unified_diff("test.py", diff_text)
        assert len(result.hunks) == 2
        assert result.hunks[0].old_start == 1
        assert result.hunks[1].old_start == 10

    def test_line_numbers(self) -> None:
        """Test that line numbers are tracked correctly."""
        diff_text = """@@ -5,3 +5,4 @@
 context
+added
 more context
 end
"""
        result = parse_unified_diff("test.py", diff_text)
        hunk = result.hunks[0]

        # Context line at old=5, new=5
        assert hunk.lines[0].old_lineno == 5
        assert hunk.lines[0].new_lineno == 5

        # Added line at new=6
        assert hunk.lines[1].old_lineno is None
        assert hunk.lines[1].new_lineno == 6
