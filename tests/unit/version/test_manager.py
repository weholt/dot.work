"""Tests for version manager module."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from dot_work.version.manager import VersionInfo, VersionManager


def test_version_manager_init(mock_git_repo):
    """Test VersionManager initialization."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=Path("/test"))

        assert manager.project_root == Path("/test")
        assert manager.version_file == Path("/test/version.json")
        assert manager.repo == mock_git_repo


def test_init_version_new(mock_git_repo, temp_dir: Path):
    """Test initializing a new version."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        # Initialize with default version
        result = manager.init_version()

        assert result.version is not None
        assert result.version.startswith("2025.")  # Should start with current year
        assert result.build_date is not None
        # git_commit is set by actual Repo, which may be None in test
        assert result.git_commit is not None

        # Check version file was created
        version_file = temp_dir / "version.json"
        assert version_file.exists()


def test_init_version_with_custom(mock_git_repo, temp_dir: Path):
    """Test initializing with a custom version."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        result = manager.init_version(version="2024.12.001")

        assert result.version == "2024.12.001"
        assert result.build_date is not None
        # git_commit is set by actual Repo, which may be None in test
        assert result.git_commit is not None


def test_read_version_existing(version_file: Path, mock_git_repo):
    """Test reading an existing version.

    Note: The version_file fixture creates a .version file, but the
    VersionManager expects version.json. We need to adapt the test.
    """
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=version_file.parent)

        # The manager looks for version.json, not .version
        # So we need to create that file
        version_json = version_file.parent / "version.json"
        version_json.write_text(
            '{"version": "2025.01.001", "build_date": "2025-01-01", '
            '"git_commit": "abc123", "git_tag": "version-2025.01.001", '
            '"previous_version": null, "changelog_generated": false}'
        )

        version_info = manager.read_version()

        assert version_info is not None
        assert version_info.version == "2025.01.001"
        assert version_info.build_date == "2025-01-01"
        assert version_info.git_commit == "abc123"
        assert version_info.git_tag == "version-2025.01.001"
        assert version_info.previous_version is None


def test_read_version_missing(mock_git_repo, temp_dir: Path):
    """Test reading version when file doesn't exist."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        version_info = manager.read_version()

        assert version_info is None


def test_get_version_history(mock_git_repo, temp_dir: Path):
    """Test getting version history from git tags."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        history = manager.get_version_history(limit=5)

        # Tags start with "version-", not "v"
        assert len(history) == 2
        assert history[0]["version"] == "2025.01.002"
        assert history[1]["version"] == "2025.01.001"


def test_get_commits_since(mock_git_repo, temp_dir: Path):
    """Test getting commits since a tag."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        commits = manager.get_commits_since("version-2025.01.001")

        assert len(commits) == 2
        assert commits[0].commit_type == "feat"
        assert commits[1].commit_type == "fix"


def test_get_commits_since_no_tag(mock_git_repo, temp_dir: Path):
    """Test getting commits when no tag is specified."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        commits = manager.get_commits_since(None)

        assert len(commits) == 2


def test_get_latest_tag(mock_git_repo, temp_dir: Path):
    """Test getting the latest tag."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        latest_tag = manager.get_latest_tag()

        # Tags start with "version-", not "v"
        assert latest_tag == "version-2025.01.002"


def test_get_latest_tag_no_tags(mock_git_repo, temp_dir: Path):
    """Test getting latest tag when no tags exist."""
    mock_git_repo.tags = []

    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        latest_tag = manager.get_latest_tag()

        assert latest_tag is None


def test_freeze_version(mock_git_repo, temp_dir: Path):
    """Test freezing a new version."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        # First initialize a version
        manager.init_version("2025.01.001")

        # Freeze a new version (dry run)
        result = manager.freeze_version(dry_run=True)

        assert result is not None
        assert result.version is not None
        assert result.build_date is not None


def test_project_info(mock_git_repo, temp_dir: Path):
    """Test getting project info."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        project_info = manager.project_info

        # Should have name from directory
        assert project_info.name is not None
        # Version might be None if no pyproject.toml
        assert project_info.version is None
        # Description might be None if no pyproject.toml
        assert project_info.description is None


def test_init_version_fails_if_exists(mock_git_repo, temp_dir: Path):
    """Test that init_version raises if version file already exists."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        # First init should succeed
        manager.init_version("2025.01.001")

        # Second init should fail
        try:
            manager.init_version("2025.01.002")
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "already exists" in str(e)


def test_calculate_next_version(mock_git_repo, temp_dir: Path):
    """Test version calculation."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        # First version should be 00001
        next_version = manager.calculate_next_version(None)
        assert next_version.endswith("00001")

        # Create a current version info with current month/year
        now = datetime.now()
        current_year = now.year
        current_month = now.month

        current = VersionInfo(
            version=f"{current_year}.{current_month:02d}.00001",
            build_date=datetime.now().isoformat(),
            git_commit="abc123",
            git_tag=f"version-{current_year}.{current_month:02d}.00001",
        )

        # Same month should increment build number
        next_version = manager.calculate_next_version(current)
        assert next_version == f"{current_year}.{current_month:02d}.00002"


def test_calculate_next_version_invalid_format_too_few_parts(
    mock_git_repo, temp_dir: Path
) -> None:
    """Test that malformed version with too few parts raises helpful error."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        # Version with only 2 parts instead of 3
        current = VersionInfo(
            version="1.2",  # Missing build number
            build_date=datetime.now().isoformat(),
            git_commit="abc123",
            git_tag="version-1.2",
        )

        with pytest.raises(ValueError, match="Invalid version format.*Got 2 parts instead of 3"):
            manager.calculate_next_version(current)


def test_calculate_next_version_invalid_format_too_many_parts(
    mock_git_repo, temp_dir: Path
) -> None:
    """Test that malformed version with too many parts raises helpful error."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        # Version with 4 parts instead of 3
        current = VersionInfo(
            version="1.2.3.4",
            build_date=datetime.now().isoformat(),
            git_commit="abc123",
            git_tag="version-1.2.3.4",
        )

        with pytest.raises(ValueError, match="Invalid version format.*Got 4 parts instead of 3"):
            manager.calculate_next_version(current)


def test_calculate_next_version_invalid_format_non_integer(
    mock_git_repo, temp_dir: Path
) -> None:
    """Test that version with non-integer parts raises helpful error."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        # Version with non-integer parts
        current = VersionInfo(
            version="abc.def.ghi",
            build_date=datetime.now().isoformat(),
            git_commit="abc123",
            git_tag="version-abc.def.ghi",
        )

        with pytest.raises(ValueError, match="Invalid version format.*all parts are integers"):
            manager.calculate_next_version(current)


def test_calculate_next_version_invalid_year(mock_git_repo, temp_dir: Path) -> None:
    """Test that version with invalid year raises helpful error."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        # Version with year out of range
        current = VersionInfo(
            version="1999.01.00001",  # Year too low
            build_date=datetime.now().isoformat(),
            git_commit="abc123",
            git_tag="version-1999.01.00001",
        )

        with pytest.raises(ValueError, match="Invalid year.*between 2000 and 2100"):
            manager.calculate_next_version(current)


def test_calculate_next_version_invalid_month(mock_git_repo, temp_dir: Path) -> None:
    """Test that version with invalid month raises helpful error."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        # Version with month out of range
        current = VersionInfo(
            version="2025.13.00001",  # Month too high
            build_date=datetime.now().isoformat(),
            git_commit="abc123",
            git_tag="version-2025.13.00001",
        )

        with pytest.raises(ValueError, match="Invalid month.*between 1 and 12"):
            manager.calculate_next_version(current)


def test_calculate_next_version_invalid_build(mock_git_repo, temp_dir: Path) -> None:
    """Test that version with invalid build number raises helpful error."""
    with patch("dot_work.version.manager.Repo", return_value=mock_git_repo):
        manager = VersionManager(project_root=temp_dir)

        # Version with build number out of range
        current = VersionInfo(
            version="2025.01.100000",  # Build too high
            build_date=datetime.now().isoformat(),
            git_commit="abc123",
            git_tag="version-2025.01.100000",
        )

        with pytest.raises(ValueError, match="Invalid build number.*between 1 and 99999"):
            manager.calculate_next_version(current)
