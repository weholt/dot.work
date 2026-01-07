"""Fixtures for zip module tests."""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing.

    Yields:
        Path to the temporary directory (cleaned up after test)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_folder_structure(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a test folder structure with various files.

    Structure:
        test_folder/
        ├── file1.txt
        ├── file2.py
        ├── subdir/
        │   ├── nested_file.txt
        │   └── nested_code.py
        └── build/
            └── output.o

    Args:
        temp_dir: Temporary directory fixture

    Yields:
        Path to the test folder
    """
    test_folder = temp_dir / "test_folder"
    test_folder.mkdir()

    # Create root level files
    (test_folder / "file1.txt").write_text("content1")
    (test_folder / "file2.py").write_text("print('hello')")

    # Create nested directory
    subdir = test_folder / "subdir"
    subdir.mkdir()
    (subdir / "nested_file.txt").write_text("nested content")
    (subdir / "nested_code.py").write_text("def foo(): pass")

    # Create build directory
    build_dir = test_folder / "build"
    build_dir.mkdir()
    (build_dir / "output.o").write_text("binary content")

    yield test_folder


@pytest.fixture
def gitignore_folder(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a test folder with .gitignore patterns.

    Structure:
        gitignore_test/
        ├── .gitignore (ignores *.log, debug/, build/)
        ├── main.py
        ├── debug.log (should be ignored)
        ├── app.log (should be ignored)
        ├── debug/
        │   └── debug_info.txt (should be ignored)
        ├── build/
        │   └── artifact.o (should be ignored)
        └── src/
            └── code.py

    Args:
        temp_dir: Temporary directory fixture

    Yields:
        Path to the folder with .gitignore
    """
    folder = temp_dir / "gitignore_test"
    folder.mkdir()

    # Create .gitignore
    (folder / ".gitignore").write_text("*.log\ndebug/\nbuild/\n__pycache__/\n")

    # Create files
    (folder / "main.py").write_text("import sys")
    (folder / "debug.log").write_text("debug output")
    (folder / "app.log").write_text("app output")

    # Create ignored directories
    debug_dir = folder / "debug"
    debug_dir.mkdir()
    (debug_dir / "debug_info.txt").write_text("debug info")

    build_dir = folder / "build"
    build_dir.mkdir()
    (build_dir / "artifact.o").write_text("compiled")

    # Create tracked directory
    src_dir = folder / "src"
    src_dir.mkdir()
    (src_dir / "code.py").write_text("def main(): pass")

    yield folder


@pytest.fixture
def empty_folder(temp_dir: Path) -> Generator[Path, None, None]:
    """Create an empty test folder.

    Args:
        temp_dir: Temporary directory fixture

    Yields:
        Path to the empty folder
    """
    empty = temp_dir / "empty"
    empty.mkdir()
    yield empty


@pytest.fixture
def zip_output_dir(temp_dir: Path) -> Generator[Path, None, None]:
    """Provide a directory for zip output files.

    Args:
        temp_dir: Temporary directory fixture

    Yields:
        Path to directory for zip output
    """
    output_dir = temp_dir / "zips"
    output_dir.mkdir()
    yield output_dir


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Clean environment variables related to zip module.

    Saves and restores the environment to prevent test pollution.

    Yields:
        None
    """
    # Save original values
    original_url = os.environ.get("DOT_WORK_ZIP_UPLOAD_URL")

    # Ensure clean state
    os.environ.pop("DOT_WORK_ZIP_UPLOAD_URL", None)

    yield

    # Restore original values
    if original_url is not None:
        os.environ["DOT_WORK_ZIP_UPLOAD_URL"] = original_url
    else:
        os.environ.pop("DOT_WORK_ZIP_UPLOAD_URL", None)
