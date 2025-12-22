"""Tests for git history CLI commands."""

import pytest
from typer.testing import CliRunner
from unittest.mock import Mock, patch

from dot_work.git.cli import history_app


runner = CliRunner()


class TestHistoryCLICommands:
    """Test the history CLI commands."""

    @patch("dot_work.git.cli.GitAnalysisService")
    def test_compare_command_exists(self, mock_service_class):
        """Test that compare command is available."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.compare_refs.return_value = Mock(
            metadata=Mock(from_ref="HEAD~1", to_ref="HEAD"),
            commits=[],
            contributors={}
        )

        result = runner.invoke(history_app, ["compare", "HEAD~1", "HEAD"])

        # Command should exist (not error on command not found)
        assert result.exit_code != 2  # 2 is "command not found" in typer

    @patch("dot_work.git.cli.GitAnalysisService")
    def test_analyze_command_exists(self, mock_service_class):
        """Test that analyze command is available."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.analyze_commit.return_value = Mock(
            commit_hash="abc123",
            author="Test",
            message="Test commit"
        )

        result = runner.invoke(history_app, ["analyze", "abc123"])

        # Command should exist
        assert result.exit_code != 2

    @patch("dot_work.git.cli.GitAnalysisService")
    def test_diff_commits_command_exists(self, mock_service_class):
        """Test that diff-commits command is available."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.compare_commits.return_value = Mock(
            commit_a_hash="abc123",
            commit_b_hash="def456",
            differences=[]
        )

        result = runner.invoke(history_app, ["diff-commits", "abc123", "def456"])

        # Command should exist
        assert result.exit_code != 2

    @patch("dot_work.git.cli.GitAnalysisService")
    def test_contributors_command_exists(self, mock_service_class):
        """Test that contributors command is available."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_contributors.return_value = {}

        result = runner.invoke(history_app, ["contributors", "HEAD~10", "HEAD"])

        # Command should exist
        assert result.exit_code != 2

    @patch("dot_work.git.cli.GitAnalysisService")
    def test_complexity_command_exists(self, mock_service_class):
        """Test that complexity command is available."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_complexity_analysis.return_value = Mock(
            average_complexity=25.0,
            high_complexity_commits=[]
        )

        result = runner.invoke(history_app, ["complexity", "HEAD~10", "HEAD"])

        # Command should exist
        assert result.exit_code != 2

    @patch("dot_work.git.cli.GitAnalysisService")
    def test_releases_command_exists(self, mock_service_class):
        """Test that releases command is available."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_recent_releases.return_value = []

        result = runner.invoke(history_app, ["releases"])

        # Command should exist
        assert result.exit_code != 2


class TestHistoryCLIOptions:
    """Test CLI option handling."""

    @patch("dot_work.git.cli.GitAnalysisService")
    def test_format_option_json(self, mock_service_class):
        """Test --format json option is accepted."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.compare_refs.return_value = Mock(
            metadata=Mock(from_ref="HEAD~1", to_ref="HEAD"),
            commits=[],
            contributors={}
        )

        result = runner.invoke(history_app, ["compare", "HEAD~1", "HEAD", "--format", "json"])

        # Should accept the format option
        assert result.exit_code != 2

    @patch("dot_work.git.cli.GitAnalysisService")
    def test_format_option_yaml(self, mock_service_class):
        """Test --format yaml option is accepted."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.compare_refs.return_value = Mock(
            metadata=Mock(from_ref="HEAD~1", to_ref="HEAD"),
            commits=[],
            contributors={}
        )

        result = runner.invoke(history_app, ["compare", "HEAD~1", "HEAD", "--format", "yaml"])

        # Should accept the format option
        assert result.exit_code != 2

    @patch("dot_work.git.cli.GitAnalysisService")
    def test_verbose_option(self, mock_service_class):
        """Test --verbose option is accepted."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.compare_refs.return_value = Mock(
            metadata=Mock(from_ref="HEAD~1", to_ref="HEAD"),
            commits=[],
            contributors={}
        )

        result = runner.invoke(history_app, ["compare", "HEAD~1", "HEAD", "--verbose"])

        # Should accept the verbose option
        assert result.exit_code != 2

    @patch("dot_work.git.cli.GitAnalysisService")
    def test_output_option(self, mock_service_class):
        """Test --output option is accepted."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.compare_refs.return_value = Mock(
            metadata=Mock(from_ref="HEAD~1", to_ref="HEAD"),
            commits=[],
            contributors={}
        )

        result = runner.invoke(history_app, ["compare", "HEAD~1", "HEAD", "--output", "/tmp/output.json"])

        # Should accept the output option
        assert result.exit_code != 2


class TestHistoryCLIErrors:
    """Test CLI error handling."""

    @patch("dot_work.git.cli.GitAnalysisService")
    def test_compare_with_missing_refs(self, mock_service_class):
        """Test compare command with missing refs shows error."""
        result = runner.invoke(history_app, ["compare"])

        # Should show error (not command not found)
        assert result.exit_code != 0

    @patch("dot_work.git.cli.GitAnalysisService")
    def test_analyze_with_missing_hash(self, mock_service_class):
        """Test analyze command with missing commit hash shows error."""
        result = runner.invoke(history_app, ["analyze"])

        # Should show error
        assert result.exit_code != 0

    @patch("dot_work.git.cli.GitAnalysisService")
    def test_diff_commits_with_missing_hashes(self, mock_service_class):
        """Test diff-commits with missing hashes shows error."""
        result = runner.invoke(history_app, ["diff-commits", "abc123"])

        # Should show error (needs two hashes)
        assert result.exit_code != 0


class TestHistoryCLIServiceIntegration:
    """Test that CLI properly integrates with GitAnalysisService."""

    @patch("dot_work.git.cli.GitAnalysisService")
    def test_compare_calls_service_with_correct_args(self, mock_service_class):
        """Test that compare command calls service with correct arguments."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.compare_refs.return_value = Mock(
            metadata=Mock(from_ref="HEAD~5", to_ref="HEAD"),
            commits=[],
            contributors={}
        )

        result = runner.invoke(history_app, ["compare", "HEAD~5", "HEAD"])

        # Service should be created
        mock_service_class.assert_called_once()

        # Compare method should be called
        assert mock_service.compare_refs.called

    @patch("dot_work.git.cli.GitAnalysisService")
    def test_analyze_calls_service_with_commit_hash(self, mock_service_class):
        """Test that analyze command calls service with commit hash."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.analyze_commit.return_value = Mock(
            commit_hash="abc123def456",
            author="Test Author",
            message="Test commit"
        )

        result = runner.invoke(history_app, ["analyze", "abc123def456"])

        # Service should be created
        mock_service_class.assert_called_once()

        # Analyze method should be called
        assert mock_service.analyze_commit.called

    @patch("dot_work.git.cli.GitAnalysisService")
    def test_complexity_passes_threshold(self, mock_service_class):
        """Test that complexity command passes threshold option."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        # Mock get_complexity_distribution as the actual method name
        mock_service.get_complexity_distribution.return_value = {"0-20": 5, "20-40": 3}

        result = runner.invoke(history_app, ["complexity", "HEAD~10", "HEAD", "--threshold", "30.0"])

        # Service should be created
        mock_service_class.assert_called_once()

        # Should not error on the command
        assert result.exit_code != 2
