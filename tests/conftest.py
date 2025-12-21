"""Pytest configuration and fixtures for dot-work tests."""

from __future__ import annotations

import subprocess
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for tests.

    This is an alias for pytest's tmp_path for compatibility.
    """
    return tmp_path


@pytest.fixture
def git_repo(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary git repository for tests."""
    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    # Create an initial commit
    test_file = tmp_path / "test.txt"
    test_file.write_text("initial content\n")
    subprocess.run(
        ["git", "add", "."],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    yield tmp_path


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory for testing installations."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def sample_prompts_dir(tmp_path: Path) -> Path:
    """Create a sample prompts directory with test prompt files."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()

    # Create sample prompt files
    (prompts_dir / "test.prompt.md").write_text(
        "# Test Prompt\n\nPath: {{ prompt_path }}\nTool: {{ ai_tool }}\n",
        encoding="utf-8",
    )
    (prompts_dir / "another.prompt.md").write_text(
        "# Another Prompt\n\nExtension: {{ prompt_extension }}\n",
        encoding="utf-8",
    )

    return prompts_dir


@pytest.fixture
def mock_console() -> Generator:
    """Create a mock Rich console for testing output."""
    from unittest.mock import MagicMock

    console = MagicMock()
    yield console
