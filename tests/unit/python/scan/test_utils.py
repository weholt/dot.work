"""
Tests for utility functions.
"""

from pathlib import Path

from dot_work.python.scan.utils import (
    compute_file_hash,
    get_file_mtime,
    get_file_size,
    is_python_file,
    should_ignore,
)


def test_is_python_file(tmp_path: Path) -> None:
    """Test identifying Python files.

    Args:
        tmp_path: Pytest temporary path fixture.
    """
    py_file = tmp_path / "module.py"
    txt_file = tmp_path / "readme.txt"

    assert is_python_file(py_file) is True
    assert is_python_file(txt_file) is False


def test_should_ignore_default_patterns() -> None:
    """Test default ignore patterns."""
    # __pycache__ should be ignored
    assert should_ignore(Path("__pycache__")) is True
    assert should_ignore(Path(".venv")) is True
    assert should_ignore(Path("venv")) is True
    assert should_ignore(Path(".git")) is True

    # Regular paths should not be ignored
    assert should_ignore(Path("src")) is False
    assert should_ignore(Path("module.py")) is False


def test_should_ignore_custom_patterns() -> None:
    """Test custom ignore patterns."""
    assert should_ignore(Path("test_foo.py"), ["test_*.py"]) is True
    assert should_ignore(Path("module.py"), ["test_*.py"]) is False


def test_get_file_size(tmp_path: Path) -> None:
    """Test getting file size.

    Args:
        tmp_path: Pytest temporary path fixture.
    """
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello, World!")

    size = get_file_size(file_path)
    assert size == 13


def test_get_file_mtime(tmp_path: Path) -> None:
    """Test getting file modification time.

    Args:
        tmp_path: Pytest temporary path fixture.
    """
    file_path = tmp_path / "test.txt"
    file_path.write_text("test")

    mtime = get_file_mtime(file_path)
    assert mtime > 0


def test_compute_file_hash(tmp_path: Path) -> None:
    """Test computing file hash.

    Args:
        tmp_path: Pytest temporary path fixture.
    """
    file_path = tmp_path / "test.txt"
    file_path.write_text("test content")

    hash1 = compute_file_hash(file_path)
    hash2 = compute_file_hash(file_path)

    assert hash1 == hash2
    assert len(hash1) == 32  # MD5 hex digest
