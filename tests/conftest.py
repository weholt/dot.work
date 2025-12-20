"""Pytest configuration and fixtures for dot-work tests."""

from collections.abc import Generator
from pathlib import Path

import pytest


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
