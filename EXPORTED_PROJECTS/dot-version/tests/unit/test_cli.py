"""Tests for version CLI module."""

from pathlib import Path
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from dot_version.cli import app

runner = CliRunner()


def test_version_init_command():
    """Test version init command."""
    with patch("dot_work.version.cli.VersionManager") as mock_manager_class:
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        mock_result = Mock()
        mock_result.version = "2025.01.001"
        mock_manager.init_version.return_value = mock_result
        mock_manager.version_file = Path.cwd() / ".work" / "version" / "version.json"

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert "2025.01.001" in result.output
        mock_manager.init_version.assert_called_once()


def test_version_init_with_version():
    """Test version init command with custom version."""
    with patch("dot_work.version.cli.VersionManager") as mock_manager_class:
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        mock_result = Mock()
        mock_result.version = "2024.12.001"
        mock_manager.init_version.return_value = mock_result
        mock_manager.version_file = Path.cwd() / ".work" / "version" / "version.json"

        result = runner.invoke(app, ["init", "--version", "2024.12.001"])

        assert result.exit_code == 0
        assert "2024.12.001" in result.output
        mock_manager.init_version.assert_called_once_with(version="2024.12.001")


def test_version_show_command():
    """Test version show command."""
    with patch("dot_work.version.cli.VersionManager") as mock_manager_class:
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        mock_current = Mock()
        mock_current.version = "2025.01.001"
        mock_current.build_date = "2025-01-01"
        mock_current.git_commit = "abc123def456"
        mock_current.git_tag = "version-2025.01.001"
        mock_current.previous_version = None

        mock_project_info = Mock()
        mock_project_info.name = "test-project"
        mock_project_info.description = "Test project"

        mock_manager.read_version.return_value = mock_current
        mock_manager.project_info = mock_project_info

        result = runner.invoke(app, ["show"])

        assert result.exit_code == 0
        assert "2025.01.001" in result.output
        assert "test-project" in result.output


def test_version_show_no_version():
    """Test version show command when no version exists."""
    with patch("dot_work.version.cli.VersionManager") as mock_manager_class:
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.read_version.return_value = None

        result = runner.invoke(app, ["show"])

        assert result.exit_code == 1
        assert "No version found" in result.output


def test_version_history_command():
    """Test version history command."""
    with patch("dot_work.version.cli.VersionManager") as mock_manager_class:
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        mock_versions = [
            {
                "version": "2025.01.002",
                "date": "2025-01-02",
                "commit": "def456",
                "author": "Test Author",
            },
            {
                "version": "2025.01.001",
                "date": "2025-01-01",
                "commit": "abc123",
                "author": "Test Author",
            },
        ]

        mock_manager.get_version_history.return_value = mock_versions

        result = runner.invoke(app, ["history"])

        assert result.exit_code == 0
        assert "2025.01.002" in result.output
        assert "2025.01.001" in result.output


def test_version_history_empty():
    """Test version history command when no history."""
    with patch("dot_work.version.cli.VersionManager") as mock_manager_class:
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.get_version_history.return_value = []

        result = runner.invoke(app, ["history"])

        assert result.exit_code == 0
        assert "No version history found" in result.output


def test_version_commits_command():
    """Test version commits command."""
    with patch("dot_work.version.cli.VersionManager") as mock_manager_class:
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        mock_commits = [
            Mock(
                commit_type="feat",
                subject="add new feature",
                author="Test Author",
                short_hash="abc123",
            ),
            Mock(commit_type="fix", subject="fix bug", author="Test Author", short_hash="def456"),
        ]

        mock_manager.get_commits_since.return_value = mock_commits
        mock_manager.get_latest_tag.return_value = "version-2025.01.001"

        result = runner.invoke(app, ["commits"])

        assert result.exit_code == 0
        assert "add new feature" in result.output
        assert "fix bug" in result.output


def test_version_commits_no_tag():
    """Test version commits command when no tag exists."""
    with patch("dot_work.version.cli.VersionManager") as mock_manager_class:
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        mock_commits = [
            Mock(
                commit_type="feat",
                subject="add new feature",
                author="Test Author",
                short_hash="abc123",
            ),
        ]

        mock_manager.get_commits_since.return_value = mock_commits
        mock_manager.get_latest_tag.return_value = None

        result = runner.invoke(app, ["commits"])

        assert result.exit_code == 0
        assert "Showing all commits" in result.output
        assert "add new feature" in result.output


def test_version_config_command():
    """Test version config command."""
    with patch("dot_work.version.cli.VersionManager") as mock_manager_class:
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        config_data = {
            "format": "YYYY.MM.build-number",
            "tag_prefix": "version-",
            "changelog": {"file": "CHANGELOG.md", "include_authors": True, "group_by_type": True},
        }

        mock_manager.load_config.return_value = config_data

        result = runner.invoke(app, ["config", "--show"])

        assert result.exit_code == 0
        # Should display JSON config
        assert "tag_prefix" in result.output
        assert "version-" in result.output


def test_version_config_without_show():
    """Test version config command without --show flag."""
    result = runner.invoke(app, ["config"])

    assert result.exit_code == 0
    assert "Use --show to display configuration" in result.output


def test_version_freeze_command():
    """Test version freeze command."""
    with patch("dot_work.version.cli.VersionManager") as mock_manager_class:
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        mock_result = Mock()
        mock_result.version = "2025.01.002"
        mock_result.git_tag = "version-2025.01.002"
        mock_result.changelog_generated = True

        mock_manager.freeze_version.return_value = mock_result

        result = runner.invoke(app, ["freeze"])

        assert result.exit_code == 0
        assert "2025.01.002" in result.output
        assert "version-2025.01.002" in result.output
        mock_manager.freeze_version.assert_called_once_with(use_llm=False, dry_run=False)


def test_version_freeze_dry_run():
    """Test version freeze command with dry run."""
    with patch("dot_work.version.cli.VersionManager") as mock_manager_class:
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        mock_result = Mock()
        mock_result.version = "2025.01.002"
        mock_result.git_tag = "version-2025.01.002"
        mock_result.changelog_generated = True

        mock_manager.freeze_version.return_value = mock_result

        result = runner.invoke(app, ["freeze", "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "2025.01.002" in result.output
        mock_manager.freeze_version.assert_called_once_with(use_llm=False, dry_run=True)


def test_version_freeze_with_llm():
    """Test version freeze command with LLM."""
    with patch("dot_work.version.cli.VersionManager") as mock_manager_class:
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        mock_result = Mock()
        mock_result.version = "2025.01.002"
        mock_result.git_tag = "version-2025.01.002"
        mock_result.changelog_generated = True

        mock_manager.freeze_version.return_value = mock_result

        result = runner.invoke(app, ["freeze", "--llm"])

        assert result.exit_code == 0
        mock_manager.freeze_version.assert_called_once_with(use_llm=True, dry_run=False)


def test_version_freeze_push():
    """Test version freeze command with push."""
    with patch("dot_work.version.cli.VersionManager") as mock_manager_class:
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        mock_result = Mock()
        mock_result.version = "2025.01.002"
        mock_result.git_tag = "version-2025.01.002"
        mock_result.changelog_generated = True

        mock_manager.freeze_version.return_value = mock_result

        result = runner.invoke(app, ["freeze", "--push"])

        assert result.exit_code == 0
        mock_manager.freeze_version.assert_called_once_with(use_llm=False, dry_run=False)
        mock_manager.push_tags.assert_called_once()
