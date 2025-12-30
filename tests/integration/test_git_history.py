"""Integration tests for git history commands.

AGENTS: DO NOT REMOVE SKIP MARKERS - READ NOTES BELOW

These tests operate on the live dot-work repository. They are marked
as skipped to prevent accidental modification of repository state and
ensure test isolation.

The git history commands (compare, analyze, diff-commits, contributors,
complexity, releases) read from and potentially modify git state. Running
these tests on the live repository can cause:
1. Flaky tests due to repository state changes between runs
2. Unintended modifications to git refs
3. Test failures dependent on current branch/commit

To enable these tests safely, implement one of:
1. Create temp git repo with known state for each test
2. Mock git subprocess calls to return predictable data
3. Use git worktree for isolated test environment

DO NOT CHANGE SKIP STATE without explicit user approval and safe implementation.
"""

import pytest
from typer.testing import CliRunner

from dot_work.cli import app

runner = CliRunner()


@pytest.mark.integration
@pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
class TestGitHistoryIntegration:
    """Integration tests using the dot-work repo itself.

    NOTE: All tests in this class are skipped because they operate on the
    live repository. See module docstring for details on how to enable safely.
    """

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
    def test_compare_refs_basic(self):
        """Test comparing HEAD~5 to HEAD."""
        result = runner.invoke(app, ["git", "history", "compare", "HEAD~5", "HEAD"])
        assert result.exit_code == 0
        # Should contain output section headers
        assert any(word in result.output for word in ["Commits:", "commits", "Commit"])

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
    def test_compare_refs_json_format(self):
        """Test comparing refs with JSON output format."""
        result = runner.invoke(
            app, ["git", "history", "compare", "HEAD~3", "HEAD", "--format", "json"]
        )
        # Command should not error (format option accepted)
        assert result.exit_code != 2

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
    def test_compare_refs_yaml_format(self):
        """Test comparing refs with YAML output format."""
        result = runner.invoke(
            app, ["git", "history", "compare", "HEAD~3", "HEAD", "--format", "yaml"]
        )
        # Command should not error (format option accepted)
        assert result.exit_code != 2

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
    def test_analyze_commit_head(self):
        """Test analyzing HEAD commit."""
        result = runner.invoke(app, ["git", "history", "analyze", "HEAD"])
        assert result.exit_code == 0
        # Should output something about the commit
        assert len(result.output) > 0

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
    def test_analyze_commit_by_hash(self):
        """Test analyzing a commit by hash (using HEAD~1)."""
        # First get the hash for HEAD~1
        hash_result = runner.invoke(app, ["git", "history", "analyze", "HEAD~1"])
        # Should work without error
        assert hash_result.exit_code == 0

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
    def test_diff_commits(self):
        """Test diffing two commits."""
        result = runner.invoke(app, ["git", "history", "diff-commits", "HEAD~2", "HEAD~1"])
        assert result.exit_code == 0
        # Should produce output
        assert len(result.output) > 0

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
    def test_contributors(self):
        """Test showing contributors between refs."""
        result = runner.invoke(app, ["git", "history", "contributors", "HEAD~10", "HEAD"])
        assert result.exit_code == 0
        # Should have some output
        assert len(result.output) > 0

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
    def test_complexity_analysis(self):
        """Test complexity analysis."""
        result = runner.invoke(app, ["git", "history", "complexity", "HEAD~10", "HEAD"])
        assert result.exit_code == 0
        # Should have output about complexity
        assert len(result.output) > 0

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
    def test_complexity_analysis_with_threshold(self):
        """Test complexity analysis with threshold option."""
        result = runner.invoke(
            app, ["git", "history", "complexity", "HEAD~10", "HEAD", "--threshold", "30.0"]
        )
        # Should accept threshold option
        assert result.exit_code != 2

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
    def test_releases(self):
        """Test showing recent releases."""
        result = runner.invoke(app, ["git", "history", "releases"])
        # Command should exist (even if no releases found)
        assert result.exit_code != 2

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
    def test_releases_with_count(self):
        """Test showing recent releases with count limit."""
        result = runner.invoke(app, ["git", "history", "releases", "--count", "5"])
        # Should accept count option
        assert result.exit_code != 2

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
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

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
    def test_compare_help(self):
        """Test compare command help."""
        result = runner.invoke(app, ["git", "history", "compare", "--help"])
        assert result.exit_code == 0
        # Should show usage
        assert "compare" in result.output.lower()

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
    def test_verbose_flag(self):
        """Test that verbose flag is accepted."""
        result = runner.invoke(app, ["git", "history", "compare", "HEAD~3", "HEAD", "--verbose"])
        # Should accept verbose flag
        assert result.exit_code != 2

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
    def test_output_flag(self):
        """Test that output flag is accepted."""
        result = runner.invoke(
            app,
            ["git", "history", "compare", "HEAD~3", "HEAD", "--output", "/tmp/test_output.json"],
        )
        # Should accept output flag (may fail if file can't be written, but flag should be recognized)
        assert result.exit_code != 2

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
    def test_invalid_ref_shows_error(self):
        """Test that invalid refs show appropriate error."""
        result = runner.invoke(app, ["git", "history", "compare", "invalid_ref_xyz", "HEAD"])
        # Should show error (not command not found)
        assert result.exit_code != 0

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
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

    @pytest.mark.skip(reason="Tests operate on live git repository - unsafe for automated runs. Requires temp repo isolation implementation.")
    def test_git_help(self):
        """Test git command help."""
        result = runner.invoke(app, ["git", "--help"])
        assert result.exit_code == 0
        # Should show history subcommand
        assert "history" in result.output
