"""Fixtures for version module tests."""

import tempfile
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from git import Repo


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing.

    Yields:
        Path to the temporary directory (cleaned up after test)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_git_repo(temp_dir: Path) -> Generator[Mock, None, None]:
    """Create a mock git repository.

    This fixture provides a mock git.Repo object for testing
    version management functionality without needing a real git repo.

    Args:
        temp_dir: Temporary directory fixture

    Yields:
        Mock git.Repo object
    """
    # Create mock repo
    mock_repo = Mock(spec=Repo)
    mock_repo.working_dir = temp_dir
    mock_repo.git_dir = temp_dir / ".git"

    # Mock common git operations
    mock_repo.is_dirty.return_value = False
    mock_repo.active_branch.name = "main"
    mock_repo.head.commit.hexsha = "abc123def456"
    mock_repo.head.commit.message = "Initial commit"
    mock_repo.head.commit.author.name = "Test Author"
    mock_repo.head.commit.author.email = "test@example.com"
    mock_repo.head.commit.committed_datetime = "2025-01-01T00:00:00Z"

    # Mock tags
    mock_tag1 = Mock()
    mock_tag1.name = "version-2025.01.001"
    mock_tag1.commit.hexsha = "abc123"
    mock_tag1.commit.author.name = "Test Author"
    mock_tag1.commit.committed_datetime = datetime(2025, 1, 1, 0, 0, 0)

    mock_tag2 = Mock()
    mock_tag2.name = "version-2025.01.002"
    mock_tag2.commit.hexsha = "def456"
    mock_tag2.commit.author.name = "Test Author"
    mock_tag2.commit.committed_datetime = datetime(2025, 1, 2, 0, 0, 0)

    mock_repo.tags = [mock_tag1, mock_tag2]

    # Mock iter_commits
    mock_commit1 = Mock()
    mock_commit1.hexsha = "commit1"
    mock_commit1.message = "feat: add new feature"
    mock_commit1.author.name = "Test Author"
    mock_commit1.summary = "feat: add new feature"

    mock_commit2 = Mock()
    mock_commit2.hexsha = "commit2"
    mock_commit2.message = "fix: fix bug"
    mock_commit2.author.name = "Test Author"
    mock_commit2.summary = "fix: fix bug"

    mock_repo.iter_commits.return_value = [mock_commit1, mock_commit2]

    yield mock_repo


@pytest.fixture
def project_with_pyproject(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary project with pyproject.toml.

    Args:
        temp_dir: Temporary directory fixture

    Yields:
        Path to the temporary project directory
    """
    # Create pyproject.toml
    pyproject_content = """
[project]
name = "test-project"
version = "0.1.0"
description = "A test project for version management"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
    (temp_dir / "pyproject.toml").write_text(pyproject_content)

    yield temp_dir


@pytest.fixture
def version_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary version file.

    Args:
        temp_dir: Temporary directory fixture

    Yields:
        Path to the version file
    """
    version_content = """{
  "version": "2025.01.001",
  "build_date": "2025-01-01",
  "git_commit": "abc123",
  "git_tag": "version-2025.01.001",
  "previous_version": null,
  "changelog_generated": false
}"""
    version_file = temp_dir / "version.json"
    version_file.write_text(version_content)

    yield version_file


@pytest.fixture
def mock_commit_info():
    """Create a mock CommitInfo object."""
    from dot_work.version.commit_parser import CommitInfo

    return CommitInfo(
        commit_hash="abc123",
        short_hash="abc123",
        commit_type="feat",
        scope=None,
        subject="add new feature",
        body="",
        author="Test Author",
        date="2025-01-01",
        is_breaking=False,
    )