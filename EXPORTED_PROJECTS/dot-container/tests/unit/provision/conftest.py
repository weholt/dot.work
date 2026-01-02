"""Pytest fixtures for container provision tests."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest


@pytest.fixture
def valid_instructions_content() -> str:
    """Return a valid instruction file content."""
    return dedent("""\
        ---
        repo_url: "https://github.com/test/repo.git"
        model: "openai/gpt-4"
        base_branch: "main"
        branch: "test/feature"
        docker_image: "test:latest"
        use_ssh: false
        github_token_env: "GITHUB_TOKEN"
        strategy: "agentic"
        tool:
          name: "opencode"
          entrypoint: "opencode run"
          args:
            strategy: "agentic"
        git_user_name: "Test User"
        git_user_email: "test@example.com"
        auto_commit: true
        create_pr: true
        ---

        Make some changes to the codebase.
        """)


@pytest.fixture
def valid_instructions_file(tmp_path: Path, valid_instructions_content: str) -> Path:
    """Create a valid instruction file."""
    test_file = tmp_path / "valid_instructions.md"
    test_file.write_text(valid_instructions_content)
    return test_file


@pytest.fixture
def minimal_dockerfile(tmp_path: Path) -> Path:
    """Create a minimal Dockerfile for testing."""
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM python:3.11-slim\nWORKDIR /app\n")
    return dockerfile
