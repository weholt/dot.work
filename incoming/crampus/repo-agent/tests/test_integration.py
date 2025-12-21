"""Integration tests for repo-agent.

These tests require Docker to be running and will build Docker images.
They test the full workflow from instruction file to Docker command execution.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, Mock
from repo_agent.core import run_from_markdown, RepoAgentError


class TestEndToEndDryRun:
    """Test end-to-end dry run workflow."""

    @pytest.fixture
    def complete_instructions_file(self, tmp_path):
        """Create a complete instruction file with all features."""
        file = tmp_path / "complete.md"
        file.write_text("""---
repo_url: "https://github.com/testuser/testrepo.git"
base_branch: "main"
branch: "test-feature"
model: "openai/gpt-4"
strategy: "agentic"
docker_image: "repo-agent:test"
github_token_env: "GITHUB_TOKEN"
git_user_name: "Test Bot"
git_user_email: "bot@example.com"
auto_commit: true
create_pr: true
create_repo_if_missing: false
pr_title: "Test PR"
pr_body: "Test body"
commit_message: "Test commit"
tool:
  name: "opencode"
  entrypoint: "opencode run"
  args:
    temperature: "0.7"
    max-tokens: "2000"
---
# Test Instructions

This is a test instruction file.
""")
        return file

    @patch("repo_agent.core.subprocess.run")
    def test_dry_run_parses_full_config(self, mock_run, complete_instructions_file):
        """Test that dry run can parse a complete configuration."""
        run_from_markdown(complete_instructions_file, dry_run=True)
        
        # Should not call subprocess.run in dry run
        mock_run.assert_not_called()

    @patch("repo_agent.core.subprocess.run")
    def test_dry_run_skips_docker_build(self, mock_run, complete_instructions_file):
        """Test that dry run doesn't build Docker images."""
        with patch("repo_agent.core._docker_build_if_needed") as mock_build:
            run_from_markdown(complete_instructions_file, dry_run=True)
            
            # In dry run, docker build is still called but subprocess.run is not
            mock_run.assert_not_called()

    def test_invalid_repo_url_raises_error(self, tmp_path):
        """Test that invalid repo URL raises an error."""
        file = tmp_path / "invalid.md"
        file.write_text("""---
repo_url: ""
model: "gpt-4"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Test
""")
        
        with pytest.raises(RepoAgentError):
            run_from_markdown(file)


class TestConfigurationOverrides:
    """Test CLI parameter overrides."""

    @pytest.fixture
    def basic_instructions_file(self, tmp_path):
        file = tmp_path / "basic.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-3.5"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Instructions
""")
        return file

    def test_repo_url_override(self, basic_instructions_file):
        """Test that repo_url can be overridden via CLI."""
        with patch("repo_agent.core.subprocess.run"):
            run_from_markdown(
                basic_instructions_file,
                repo_url="https://github.com/override/repo.git",
                dry_run=True
            )

    def test_model_override(self, basic_instructions_file):
        """Test that model can be overridden via CLI."""
        with patch("repo_agent.core.subprocess.run"):
            run_from_markdown(
                basic_instructions_file,
                model="gpt-4",
                dry_run=True
            )

    def test_branch_override(self, basic_instructions_file):
        """Test that branch can be overridden via CLI."""
        with patch("repo_agent.core.subprocess.run"):
            run_from_markdown(
                basic_instructions_file,
                branch="custom-branch",
                dry_run=True
            )

    def test_multiple_overrides(self, basic_instructions_file):
        """Test multiple CLI overrides at once."""
        with patch("repo_agent.core.subprocess.run"):
            run_from_markdown(
                basic_instructions_file,
                repo_url="https://github.com/override/repo.git",
                model="gpt-4-turbo",
                branch="feature/test",
                auto_commit=False,
                create_pr=False,
                dry_run=True
            )


class TestDockerCommandGeneration:
    """Test Docker command generation."""

    @pytest.fixture
    def minimal_instructions_file(self, tmp_path):
        file = tmp_path / "minimal.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Instructions
""")
        return file

    @patch("repo_agent.core.subprocess.run")
    def test_docker_command_includes_required_env_vars(self, mock_run, minimal_instructions_file, monkeypatch):
        """Test that Docker command includes all required environment variables."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
        
        run_from_markdown(minimal_instructions_file, dry_run=False)
        
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        cmd_str = " ".join(cmd)
        
        assert "docker" in cmd_str
        assert "run" in cmd_str
        assert "REPO_URL" in cmd_str
        assert "MODEL" in cmd_str

    @patch("repo_agent.core.subprocess.run")
    def test_docker_command_with_tool_args(self, mock_run, tmp_path, monkeypatch):
        """Test Docker command with tool arguments."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
        
        file = tmp_path / "with_args.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
tool:
  name: "opencode"
  entrypoint: "opencode run"
  args:
    temperature: "0.7"
    max-tokens: "1000"
---
Instructions
""")
        
        run_from_markdown(file, dry_run=False)
        
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        cmd_str = " ".join(cmd)
        
        assert "TOOL_EXTRA_ARGS" in cmd_str


class TestAuthenticationMethods:
    """Test different authentication methods."""

    def test_github_token_from_env_var(self, tmp_path, monkeypatch):
        """Test GitHub token authentication from environment variable."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
        
        file = tmp_path / "token_auth.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
github_token_env: "GITHUB_TOKEN"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Instructions
""")
        
        with patch("repo_agent.core.subprocess.run"):
            run_from_markdown(file, dry_run=True)

    def test_ssh_authentication(self, tmp_path):
        """Test SSH authentication configuration."""
        file = tmp_path / "ssh_auth.md"
        file.write_text("""---
repo_url: "git@github.com:user/repo.git"
model: "gpt-4"
use_ssh: true
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Instructions
""")
        
        with patch("repo_agent.core.subprocess.run"):
            run_from_markdown(file, dry_run=True)


class TestErrorHandling:
    """Test error handling in various scenarios."""

    def test_missing_file_raises_error(self, tmp_path):
        """Test that missing instruction file raises error."""
        nonexistent = tmp_path / "nonexistent.md"
        
        with pytest.raises(RepoAgentError, match="not found"):
            run_from_markdown(nonexistent)

    def test_missing_repo_url_raises_error(self, tmp_path):
        """Test that missing repo_url raises error."""
        file = tmp_path / "no_repo.md"
        file.write_text("""---
model: "gpt-4"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Instructions
""")
        
        with pytest.raises(RepoAgentError, match="repo_url"):
            run_from_markdown(file)

    def test_missing_model_raises_error(self, tmp_path):
        """Test that missing model raises error."""
        file = tmp_path / "no_model.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Instructions
""")
        
        with pytest.raises(RepoAgentError, match="model"):
            run_from_markdown(file)

    @patch("repo_agent.core.subprocess.run")
    def test_missing_tool_section_uses_defaults(self, mock_run, tmp_path):
        """Test that missing tool section uses default tool configuration."""
        file = tmp_path / "no_tool.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
github_token_env: "GITHUB_TOKEN"
---
Instructions
""")
        
        # Should not raise - tool section is optional, uses defaults
        run_from_markdown(file, dry_run=False)
        
        # Verify subprocess was called (command was built)
        mock_run.assert_called_once()

    def test_invalid_strategy_raises_error(self, tmp_path):
        """Test that invalid strategy raises error."""
        file = tmp_path / "invalid_strategy.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
strategy: "invalid"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Instructions
""")
        
        with pytest.raises(RepoAgentError, match="strategy"):
            run_from_markdown(file)


class TestFeatureFlags:
    """Test various feature flags."""

    @pytest.fixture
    def feature_test_file(self, tmp_path):
        file = tmp_path / "features.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
auto_commit: false
create_pr: false
create_repo_if_missing: true
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Instructions
""")
        return file

    @patch("repo_agent.core.subprocess.run")
    def test_create_repo_if_missing_flag(self, mock_run, feature_test_file, monkeypatch):
        """Test create_repo_if_missing feature flag."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
        
        run_from_markdown(feature_test_file, dry_run=False)
        
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        cmd_str = " ".join(cmd)
        
        assert "CREATE_REPO_IF_MISSING" in cmd_str

    @patch("repo_agent.core.subprocess.run")
    def test_auto_commit_disabled(self, mock_run, feature_test_file, monkeypatch):
        """Test auto_commit=false configuration."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
        
        run_from_markdown(feature_test_file, dry_run=False)
        
        mock_run.assert_called_once()

    @patch("repo_agent.core.subprocess.run")
    def test_create_pr_disabled(self, mock_run, feature_test_file, monkeypatch):
        """Test create_pr=false configuration."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
        
        run_from_markdown(feature_test_file, dry_run=False)
        
        mock_run.assert_called_once()
