"""Tests for version manager module."""

from pathlib import Path
from unittest.mock import Mock, patch

from dot_work.version.manager import VersionManager, VersionInfo


def test_version_manager_init(mock_git_repo):
    """Test VersionManager initialization."""
    with patch("git.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=Path("/test"))

        assert manager.project_root == Path("/test")
        assert manager.version_file == Path("/test/.version")
        assert manager.changelog_file == Path("/test/CHANGELOG.md")


def test_init_version_new(mock_git_repo, temp_dir: Path):
    """Test initializing a new version."""
    with patch("git.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        # Initialize with default version
        result = manager.init_version()

        assert result.version is not None
        assert result.version.startswith("2025.")  # Should start with current year
        assert result.build_date is not None
        assert result.git_commit == mock_git_repo.head.commit.hexsha

        # Check version file was created
        version_file = temp_dir / ".version"
        assert version_file.exists()


def test_init_version_with_custom(mock_git_repo, temp_dir: Path):
    """Test initializing with a custom version."""
    with patch("git.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        result = manager.init_version(version="2024.12.001")

        assert result.version == "2024.12.001"
        assert result.build_date is not None
        assert result.git_commit == mock_git_repo.head.commit.hexsha


def test_read_version_existing(version_file: Path, mock_git_repo):
    """Test reading an existing version."""
    with patch("git.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=version_file.parent)

        version_info = manager.read_version()

        assert version_info is not None
        assert version_info.version == "2025.01.001"
        assert version_info.build_date == "2025-01-01"
        assert version_info.git_commit == "abc123"
        assert version_info.git_tag == "v2025.01.001"
        assert version_info.previous_version is None


def test_read_version_missing(mock_git_repo, temp_dir: Path):
    """Test reading version when file doesn't exist."""
    with patch("git.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        version_info = manager.read_version()

        assert version_info is None


def test_get_version_history(mock_git_repo, temp_dir: Path):
    """Test getting version history from git tags."""
    with patch("git.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        history = manager.get_version_history(limit=5)

        assert len(history) == 2
        assert history[0]["version"] == "v2025.01.001"
        assert history[1]["version"] == "v2025.01.002"


def test_get_commits_since(mock_git_repo, temp_dir: Path):
    """Test getting commits since a tag."""
    with patch("git.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        commits = manager.get_commits_since("v2025.01.001")

        assert len(commits) == 2
        assert commits[0].commit_type == "feat"
        assert commits[1].commit_type == "fix"


def test_get_commits_since_no_tag(mock_git_repo, temp_dir: Path):
    """Test getting commits when no tag is specified."""
    with patch("git.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        commits = manager.get_commits_since(None)

        assert len(commits) == 2


def test_get_latest_tag(mock_git_repo, temp_dir: Path):
    """Test getting the latest tag."""
    with patch("git.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        latest_tag = manager.get_latest_tag()

        # Should return the last tag in the list
        assert latest_tag == "v2025.01.002"


def test_get_latest_tag_no_tags(mock_git_repo, temp_dir: Path):
    """Test getting latest tag when no tags exist."""
    mock_git_repo.tags = []

    with patch("git.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        latest_tag = manager.get_latest_tag()

        assert latest_tag is None


def test_freeze_version(mock_git_repo, temp_dir: Path):
    """Test freezing a new version."""
    with patch("git.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        # First initialize a version
        manager.init_version("2025.01.001")

        # Freeze a new version
        result = manager.freeze_version(dry_run=True)

        assert result is not None
        assert result.version is not None
        assert result.build_date is not None


def test_project_info(mock_git_repo, temp_dir: Path):
    """Test getting project info."""
    with patch("git.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        project_info = manager.project_info

        # Should have name from directory
        assert project_info.name is not None
        # Version might be None if no pyproject.toml
        assert project_info.version is None
        # Description might be None if no pyproject.toml
        assert project_info.description is None