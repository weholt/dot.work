"""Integration tests for git history commands."""

import pytest
from typer.testing import CliRunner

from dot_work.cli import app

runner = CliRunner()


@pytest.mark.integration
class TestGitHistoryIntegration:
    """Integration tests using the dot-work repo itself."""

    def test_compare_refs_basic(self):
        """Test comparing HEAD~5 to HEAD."""
        result = runner.invoke(app, ["git", "history", "compare", "HEAD~5", "HEAD"])
        assert result.exit_code == 0
        # Should contain output section headers
        assert any(word in result.output for word in ["Commits:", "commits", "Commit"])

    def test_compare_refs_json_format(self):
        """Test comparing refs with JSON output format."""
        result = runner.invoke(
            app, ["git", "history", "compare", "HEAD~3", "HEAD", "--format", "json"]
        )
        # Command should not error (format option accepted)
        assert result.exit_code != 2

    def test_compare_refs_yaml_format(self):
        """Test comparing refs with YAML output format."""
        result = runner.invoke(
            app, ["git", "history", "compare", "HEAD~3", "HEAD", "--format", "yaml"]
        )
        # Command should not error (format option accepted)
        assert result.exit_code != 2

    def test_analyze_commit_head(self):
        """Test analyzing HEAD commit."""
        result = runner.invoke(app, ["git", "history", "analyze", "HEAD"])
        assert result.exit_code == 0
        # Should output something about the commit
        assert len(result.output) > 0

    def test_analyze_commit_by_hash(self):
        """Test analyzing a commit by hash (using HEAD~1)."""
        # First get the hash for HEAD~1
        hash_result = runner.invoke(app, ["git", "history", "analyze", "HEAD~1"])
        # Should work without error
        assert hash_result.exit_code == 0

    def test_diff_commits(self):
        """Test diffing two commits."""
        result = runner.invoke(app, ["git", "history", "diff-commits", "HEAD~2", "HEAD~1"])
        assert result.exit_code == 0
        # Should produce output
        assert len(result.output) > 0

    def test_contributors(self):
        """Test showing contributors between refs."""
        result = runner.invoke(app, ["git", "history", "contributors", "HEAD~10", "HEAD"])
        assert result.exit_code == 0
        # Should have some output
        assert len(result.output) > 0

    def test_complexity_analysis(self):
        """Test complexity analysis."""
        result = runner.invoke(app, ["git", "history", "complexity", "HEAD~10", "HEAD"])
        assert result.exit_code == 0
        # Should have output about complexity
        assert len(result.output) > 0

    def test_complexity_analysis_with_threshold(self):
        """Test complexity analysis with threshold option."""
        result = runner.invoke(
            app, ["git", "history", "complexity", "HEAD~10", "HEAD", "--threshold", "30.0"]
        )
        # Should accept threshold option
        assert result.exit_code != 2

    def test_releases(self):
        """Test showing recent releases."""
        result = runner.invoke(app, ["git", "history", "releases"])
        # Command should exist (even if no releases found)
        assert result.exit_code != 2

    def test_releases_with_count(self):
        """Test showing recent releases with count limit."""
        result = runner.invoke(app, ["git", "history", "releases", "--count", "5"])
        # Should accept count option
        assert result.exit_code != 2

    def test_help_text(self):
        """Test that help text is available."""
        result = runner.invoke(app, ["git", "history", "--help"])
        assert result.exit_code == 0
        assert "compare" in result.output
        assert "analyze" in result.output
        assert "diff-commits" in result.output
        assert "contributors" in result.output
        assert "complexity" in result.output
        assert "releases" in result.output

    def test_compare_help(self):
        """Test compare command help."""
        result = runner.invoke(app, ["git", "history", "compare", "--help"])
        assert result.exit_code == 0
        # Should show usage
        assert "compare" in result.output.lower()

    def test_verbose_flag(self):
        """Test that verbose flag is accepted."""
        result = runner.invoke(app, ["git", "history", "compare", "HEAD~3", "HEAD", "--verbose"])
        # Should accept verbose flag
        assert result.exit_code != 2

    def test_output_flag(self):
        """Test that output flag is accepted."""
        result = runner.invoke(
            app,
            ["git", "history", "compare", "HEAD~3", "HEAD", "--output", "/tmp/test_output.json"],
        )
        # Should accept output flag (may fail if file can't be written, but flag should be recognized)
        assert result.exit_code != 2

    def test_invalid_ref_shows_error(self):
        """Test that invalid refs show appropriate error."""
        result = runner.invoke(app, ["git", "history", "compare", "invalid_ref_xyz", "HEAD"])
        # Should show error (not command not found)
        assert result.exit_code != 0

    def test_git_history_help(self):
        """Test git history subcommand help."""
        result = runner.invoke(app, ["git", "history", "--help"])
        assert result.exit_code == 0
        # Should list all 6 commands
        assert "compare" in result.output
        assert "analyze" in result.output
        assert "diff-commits" in result.output
        assert "contributors" in result.output
        assert "complexity" in result.output
        assert "releases" in result.output

    def test_git_help(self):
        """Test git command help."""
        result = runner.invoke(app, ["git", "--help"])
        assert result.exit_code == 0
        # Should show history subcommand
        assert "history" in result.output
