import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from repo_agent.cli import app
from repo_agent.validation import validate_instructions
from typer.testing import CliRunner


runner = CliRunner()


class TestInitCommand:
    """Test init command."""

    def test_creates_new_template_file(self, tmp_path):
        output_file = tmp_path / "test.md"
        result = runner.invoke(app, ["init", str(output_file)])
        
        assert result.exit_code == 0
        assert output_file.exists()
        assert "Created template" in result.stdout

    def test_refuses_to_overwrite_without_force(self, tmp_path):
        output_file = tmp_path / "test.md"
        output_file.write_text("existing content")
        
        result = runner.invoke(app, ["init", str(output_file)])
        
        assert result.exit_code != 0
        output = (result.stdout + result.stderr).lower()
        assert "already exists" in output

    def test_overwrites_with_force_flag(self, tmp_path):
        output_file = tmp_path / "test.md"
        output_file.write_text("existing content")
        
        result = runner.invoke(app, ["init", str(output_file), "--force"])
        
        assert result.exit_code == 0
        assert "Created template" in result.stdout

    def test_template_contains_required_fields(self, tmp_path):
        output_file = tmp_path / "test.md"
        result = runner.invoke(app, ["init", str(output_file)])
        
        content = output_file.read_text()
        assert "repo_url:" in content
        assert "model:" in content
        assert "tool:" in content
        assert "name:" in content
        assert "entrypoint:" in content


class TestValidateCommand:
    """Test validate command."""

    def test_validates_correct_file(self, tmp_path):
        instructions = tmp_path / "test.md"
        instructions.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
github_token_env: "GITHUB_TOKEN"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Test instructions
""")
        
        result = runner.invoke(app, ["validate", str(instructions)])
        
        assert result.exit_code == 0
        assert "valid" in result.stdout.lower()

    def test_fails_for_missing_file(self, tmp_path):
        nonexistent = tmp_path / "nonexistent.md"
        
        result = runner.invoke(app, ["validate", str(nonexistent)])
        
        assert result.exit_code != 0

    def test_fails_for_invalid_frontmatter(self, tmp_path):
        instructions = tmp_path / "test.md"
        instructions.write_text("""---
model: "gpt-4"
---
Missing repo_url
""")
        
        result = runner.invoke(app, ["validate", str(instructions)])
        
        assert result.exit_code != 0


class TestRunCommand:
    """Test run command."""

    @patch("repo_agent.cli.run_from_markdown")
    def test_calls_run_from_markdown(self, mock_run, tmp_path):
        instructions = tmp_path / "test.md"
        instructions.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Test
""")
        
        result = runner.invoke(app, ["run", str(instructions)])
        
        mock_run.assert_called_once()
        assert result.exit_code == 0

    @patch("repo_agent.cli.run_from_markdown")
    def test_passes_overrides_to_run_from_markdown(self, mock_run, tmp_path):
        instructions = tmp_path / "test.md"
        instructions.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Test
""")
        
        result = runner.invoke(app, [
            "run", str(instructions),
            "--repo-url", "https://github.com/override/repo.git",
            "--model", "gpt-3.5",
            "--branch", "custom-branch"
        ])
        
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["repo_url"] == "https://github.com/override/repo.git"
        assert call_kwargs["model"] == "gpt-3.5"
        assert call_kwargs["branch"] == "custom-branch"

    @patch("repo_agent.cli.run_from_markdown")
    def test_dry_run_flag(self, mock_run, tmp_path):
        instructions = tmp_path / "test.md"
        instructions.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Test
""")
        
        result = runner.invoke(app, ["run", str(instructions), "--dry-run"])
        
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["dry_run"] is True

    @patch("repo_agent.cli.run_from_markdown")
    def test_boolean_flags(self, mock_run, tmp_path):
        instructions = tmp_path / "test.md"
        instructions.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
github_token_env: "GITHUB_TOKEN"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Test
""")
        
        result = runner.invoke(app, [
            "run", str(instructions),
            "--no-auto-commit",
            "--no-create-pr",
            "--create-repo",
            "--ssh"
        ])
        
        # Debug: print result if test fails
        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.stdout}")
            print(f"Exception: {result.exception}")
        
        # Verify the mock was called and received the boolean flags
        assert mock_run.called, f"Mock not called. Exit code: {result.exit_code}, Output: {result.stdout}"
        # Check the call happened with expected keyword arguments
        _, kwargs = mock_run.call_args
        assert kwargs.get("auto_commit") is False
        assert kwargs.get("create_pr") is False
        assert kwargs.get("create_repo_if_missing") is True
        assert kwargs.get("use_ssh") is True


class TestCLIHelp:
    """Test CLI help messages."""

    def test_main_help_shows_commands(self):
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "run" in result.stdout
        assert "init" in result.stdout
        assert "validate" in result.stdout

    def test_run_help_shows_options(self):
        result = runner.invoke(app, ["run", "--help"])
        
        assert result.exit_code == 0
        assert "--repo-url" in result.stdout
        assert "--model" in result.stdout
        assert "--dry-run" in result.stdout

    def test_init_help_shows_options(self):
        result = runner.invoke(app, ["init", "--help"])
        
        assert result.exit_code == 0
        assert "--force" in result.stdout


class TestCLIErrorHandling:
    """Test CLI error handling."""

    @patch("repo_agent.cli.run_from_markdown")
    def test_handles_repo_agent_error(self, mock_run, tmp_path):
        from repo_agent.core import RepoAgentError
        
        instructions = tmp_path / "test.md"
        instructions.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Test
""")
        
        mock_run.side_effect = RepoAgentError("Test error")
        
        result = runner.invoke(app, ["run", str(instructions)])
        
        assert result.exit_code != 0
        output = result.stdout + result.stderr
        assert "Test error" in output
