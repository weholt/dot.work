"""Tests for file scanner."""

from pathlib import Path

from dot_overview.scanner import (
    ScannerConfig,
    _normalize_extension,
    iter_project_files,
    load_scanner_config,
)


def test_normalize_extension_with_dot() -> None:
    assert _normalize_extension(".py") == ".py"
    assert _normalize_extension(".md") == ".md"


def test_normalize_extension_without_dot() -> None:
    assert _normalize_extension("py") == ".py"
    assert _normalize_extension("md") == ".md"


def test_normalize_extension_case_insensitive() -> None:
    assert _normalize_extension("PY") == ".py"
    assert _normalize_extension("MD") == ".md"


def test_scanner_config_defaults() -> None:
    config = ScannerConfig(include_ext=set(), exclude_dirs=set())
    assert config.include_ext == set()
    assert config.exclude_dirs == set()


def test_iter_project_files_finds_python_files(sample_project_dir: Path) -> None:
    files = list(iter_project_files(sample_project_dir))
    assert len(files) >= 1
    python_files = [f for f in files if f.suffix == ".py"]
    assert len(python_files) == 1
    assert python_files[0].path.name == "example.py"


def test_iter_project_files_finds_markdown_files(sample_project_dir: Path) -> None:
    files = list(iter_project_files(sample_project_dir))
    markdown_files = [f for f in files if f.suffix == ".md"]
    assert len(markdown_files) == 1
    assert markdown_files[0].path.name == "README.md"


def test_iter_project_files_default_extensions(sample_project_dir: Path) -> None:
    files = list(iter_project_files(sample_project_dir))
    # Should find .py and .md files (DEFAULT_INCLUDE_EXT)
    extensions = {f.suffix for f in files}
    assert ".py" in extensions
    assert ".md" in extensions


def test_iter_project_files_custom_include_ext(sample_project_dir: Path) -> None:
    # Create a .txt file
    (sample_project_dir / "test.txt").write_text("test content")

    files = list(iter_project_files(sample_project_dir, include_ext=[".txt"]))
    assert len(files) == 1
    assert files[0].suffix == ".txt"


def test_iter_project_files_excludes_default_dirs(tmp_path: Path) -> None:
    # Create directories that should be excluded
    for exclude_dir in [".git", "__pycache__", ".venv", "venv", "build", "dist"]:
        excluded = tmp_path / exclude_dir
        excluded.mkdir()
        (excluded / "test.py").write_text("# This should be excluded")

    # Create a file that should be included
    (tmp_path / "main.py").write_text("# This should be included")

    files = list(iter_project_files(tmp_path))
    assert len(files) == 1
    assert files[0].path.name == "main.py"


def test_iter_project_files_custom_exclude_dirs(tmp_path: Path) -> None:
    # Create directories
    (tmp_path / "include_this").mkdir()
    (tmp_path / "exclude_this").mkdir()
    (tmp_path / "include_this" / "test.py").write_text("# Include")
    (tmp_path / "exclude_this" / "test.py").write_text("# Exclude")

    files = list(iter_project_files(tmp_path, exclude_dirs=["exclude_this"]))
    assert len(files) == 1
    assert "include_this" in str(files[0].path)


def test_project_file_read_text(sample_project_dir: Path) -> None:
    files = list(iter_project_files(sample_project_dir))
    python_file = [f for f in files if f.suffix == ".py"][0]
    content = python_file.read_text()
    assert '"""Example module for testing."""' in content


def test_load_scanner_config_default(sample_project_dir: Path) -> None:
    config = load_scanner_config(sample_project_dir)
    assert ".py" in config.include_ext
    assert ".md" in config.include_ext
    assert ".git" in config.exclude_dirs


def test_load_scanner_config_with_pyproject(sample_project_dir: Path) -> None:
    # Create a pyproject.toml with custom scanner config
    (sample_project_dir / "pyproject.toml").write_text(
        """
[tool.birdseye.scanner]
include_ext = [".py", ".md", ".txt"]
exclude_dirs = [".git", "node_modules"]
"""
    )

    config = load_scanner_config(sample_project_dir)
    assert ".txt" in config.include_ext
    assert "node_modules" in config.exclude_dirs
