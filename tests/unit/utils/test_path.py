"""Tests for path validation utilities."""

import pytest
from pathlib import Path
import tempfile
import os

from dot_work.utils.path import (
    safe_path_join,
    validate_path_safe,
    safe_write_path,
    PathTraversalError,
)


class TestSafePathJoin:
    """Tests for safe_path_join function."""

    def test_joins_simple_relative_path(self, tmp_path: Path) -> None:
        """Test joining a simple relative path."""
        result = safe_path_join(tmp_path, "config.yaml")
        assert result == tmp_path / "config.yaml"
        assert result.is_absolute()

    def test_joins_nested_relative_path(self, tmp_path: Path) -> None:
        """Test joining a nested relative path."""
        (tmp_path / "subdir").mkdir()
        result = safe_path_join(tmp_path, "subdir/file.txt")
        assert result == tmp_path / "subdir" / "file.txt"

    def test_resolves_symlinks_within_target(self, tmp_path: Path) -> None:
        """Test that symlinks within target are resolved correctly."""
        # Create a file and a symlink to it
        target_file = tmp_path / "target.txt"
        target_file.write_text("content")

        link_dir = tmp_path / "links"
        link_dir.mkdir()
        link_path = link_dir / "link.txt"
        link_path.symlink_to(target_file)

        result = safe_path_join(tmp_path, "links/link.txt")
        # Should resolve to actual file path
        assert result.exists()
        assert result == target_file

    def test_rejects_symlink_escape(self, tmp_path: Path) -> None:
        """Test that symlinks escaping target are rejected."""
        # Create a file outside target
        outside_file = tmp_path.parent / "outside.txt"
        outside_file.write_text("outside content")

        # Create symlink within target pointing outside
        link_path = tmp_path / "escape_link"
        link_path.symlink_to(outside_file)

        with pytest.raises(PathTraversalError, match="escapes target directory"):
            safe_path_join(tmp_path, "escape_link")

    def test_rejects_double_dot_escape(self, tmp_path: Path) -> None:
        """Test that '..' traversal is rejected."""
        with pytest.raises(PathTraversalError, match="escapes target directory"):
            safe_path_join(tmp_path, "../../etc/passwd")

    def test_rejects_absolute_path(self, tmp_path: Path) -> None:
        """Test that absolute paths are rejected."""
        with pytest.raises(PathTraversalError, match="Absolute path not allowed"):
            safe_path_join(tmp_path, "/etc/passwd")

    def test_requires_absolute_target(self) -> None:
        """Test that target must be an absolute path."""
        with pytest.raises(ValueError, match="Target directory must be absolute"):
            safe_path_join(Path("relative"), "file.txt")

    def test_requires_existing_target(self) -> None:
        """Test that target directory must exist."""
        with pytest.raises(ValueError, match="does not exist"):
            safe_path_join(Path("/nonexistent/path/12345"), "file.txt")

    def test_normalizes_dot_components(self, tmp_path: Path) -> None:
        """Test that '.' components are normalized."""
        result = safe_path_join(tmp_path, "./subdir/./file.txt")
        # Should normalize the './' components
        assert "subdir/file.txt" in str(result) or "subdir\\file.txt" in str(result)


class TestValidatePathSafe:
    """Tests for validate_path_safe function."""

    def test_returns_true_for_safe_path(self, tmp_path: Path) -> None:
        """Test that safe paths return True."""
        assert validate_path_safe(tmp_path, "config.yaml") is True

    def test_returns_false_for_traversal(self, tmp_path: Path) -> None:
        """Test that traversal attempts return False."""
        assert validate_path_safe(tmp_path, "../../etc/passwd") is False

    def test_returns_false_for_absolute_path(self, tmp_path: Path) -> None:
        """Test that absolute paths return False."""
        assert validate_path_safe(tmp_path, "/etc/passwd") is False


class TestSafeWritePath:
    """Tests for safe_write_path function."""

    def test_returns_safe_path_for_simple_filename(self, tmp_path: Path) -> None:
        """Test getting safe write path for simple filename."""
        result = safe_write_path(tmp_path, "output.txt")
        assert result == tmp_path / "output.txt"

    def test_rejects_empty_filename(self, tmp_path: Path) -> None:
        """Test that empty filename is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            safe_write_path(tmp_path, "")

    def test_rejects_path_with_slash(self, tmp_path: Path) -> None:
        """Test that filenames with separators are rejected."""
        with pytest.raises(PathTraversalError, match="path separators"):
            safe_write_path(tmp_path, "subdir/file.txt")

    def test_rejects_path_with_backslash(self, tmp_path: Path) -> None:
        """Test that filenames with backslash are rejected."""
        with pytest.raises(PathTraversalError, match="path separators"):
            safe_write_path(tmp_path, "subdir\\file.txt")

    def test_rejects_double_dot_in_filename(self, tmp_path: Path) -> None:
        """Test that filenames with '..' are rejected."""
        with pytest.raises(PathTraversalError, match="traversal pattern"):
            safe_write_path(tmp_path, "..hidden")

    def test_rejects_dot_start_filename(self, tmp_path: Path) -> None:
        """Test that filenames starting with '.' are rejected."""
        with pytest.raises(PathTraversalError, match="traversal pattern"):
            safe_write_path(tmp_path, ".hidden")
