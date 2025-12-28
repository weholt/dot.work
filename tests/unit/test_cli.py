"""Unit tests for CLI commands using CliRunner.

Tests all 8 CLI commands with smoke tests, --help tests, and error paths.
Regression guard for TEST-002@d8c4e1.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from dot_work.cli import app

if TYPE_CHECKING:
    pass


runner = CliRunner()


# =============================================================================
# Version and Help Tests (Regression Guards)
# =============================================================================


class TestVersionCommand:
    """Tests for --version flag - regression guard for BUG-001."""

    def test_version_flag_exits_zero(self) -> None:
        """--version should exit successfully."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0

    def test_version_flag_shows_version(self) -> None:
        """--version should display the package version."""
        result = runner.invoke(app, ["--version"])
        assert "dot-work version" in result.stdout

    def test_version_short_flag(self) -> None:
        """-v should work as short form of --version."""
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "dot-work version" in result.stdout

    def test_version_is_valid_semver(self) -> None:
        """Version string should be valid semver format."""
        import re

        result = runner.invoke(app, ["--version"])
        # Extract version from output like "dot-work version 0.1.1"
        match = re.search(r"version\s+(\d+\.\d+\.\d+)", result.stdout)
        assert match is not None, f"No semver found in: {result.stdout}"


class TestHelpCommand:
    """Tests for --help across all commands."""

    def test_main_help(self) -> None:
        """Main help should list all commands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "install" in result.stdout
        assert "list" in result.stdout
        assert "detect" in result.stdout
        assert "init" in result.stdout
        assert "init-work" in result.stdout
        assert "validate" in result.stdout

    def test_no_args_shows_help(self) -> None:
        """Running with no args should show help (exit code 2 due to no_args_is_help)."""
        result = runner.invoke(app, [])
        # typer exits with code 2 for no_args_is_help, but still shows help
        assert result.exit_code in (0, 2)
        # Help might be in stdout or output depending on typer version
        output = result.stdout + (result.output or "")
        assert "install" in output.lower() or "usage" in output.lower()

    def test_install_help(self) -> None:
        """install --help should show options."""
        result = runner.invoke(app, ["install", "--help"])
        assert result.exit_code == 0
        assert "--env" in result.stdout
        assert "--target" in result.stdout
        assert "--force" in result.stdout

    def test_list_help(self) -> None:
        """list --help should describe the command."""
        result = runner.invoke(app, ["list", "--help"])
        assert result.exit_code == 0
        assert "environment" in result.stdout.lower()

    def test_detect_help(self) -> None:
        """detect --help should show target option."""
        result = runner.invoke(app, ["detect", "--help"])
        assert result.exit_code == 0
        assert "--target" in result.stdout

    def test_init_help(self) -> None:
        """init --help should show options."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "--env" in result.stdout

    def test_init_work_help(self) -> None:
        """init-work --help should show options."""
        result = runner.invoke(app, ["init-work", "--help"])
        assert result.exit_code == 0
        assert "--target" in result.stdout
        assert "--force" in result.stdout

    def test_validate_help(self) -> None:
        """validate --help should list subcommands."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "json" in result.stdout
        assert "yaml" in result.stdout

    def test_validate_json_help(self) -> None:
        """validate json --help should show file argument."""
        result = runner.invoke(app, ["validate", "json", "--help"])
        assert result.exit_code == 0
        assert "FILE" in result.stdout
        assert "--schema" in result.stdout

    def test_validate_yaml_help(self) -> None:
        """validate yaml --help should show options."""
        result = runner.invoke(app, ["validate", "yaml", "--help"])
        assert result.exit_code == 0
        assert "FILE" in result.stdout
        assert "--frontmatter" in result.stdout


# =============================================================================
# List Command Tests
# =============================================================================


class TestListCommand:
    """Tests for the 'list' command."""

    def test_list_exits_zero(self) -> None:
        """list command should exit successfully."""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

    def test_list_shows_environments(self) -> None:
        """list should display known environments."""
        result = runner.invoke(app, ["list"])
        assert "copilot" in result.stdout.lower()
        assert "cursor" in result.stdout.lower()
        assert "claude" in result.stdout.lower()

    def test_list_shows_table_header(self) -> None:
        """list should show table with headers."""
        result = runner.invoke(app, ["list"])
        assert "Key" in result.stdout or "key" in result.stdout.lower()
        assert "Name" in result.stdout or "name" in result.stdout.lower()


# =============================================================================
# Detect Command Tests
# =============================================================================


class TestDetectCommand:
    """Tests for the 'detect' command."""

    def test_detect_no_environment(self, tmp_path: Path) -> None:
        """detect should report when no environment is found."""
        result = runner.invoke(app, ["detect", "--target", str(tmp_path)])
        assert result.exit_code == 0
        assert "No AI environment detected" in result.stdout

    def test_detect_copilot_environment(self, tmp_path: Path) -> None:
        """detect should find .github/prompts directory."""
        # Copilot detection marker is .github/prompts or .vscode
        prompts_dir = tmp_path / ".github" / "prompts"
        prompts_dir.mkdir(parents=True)

        result = runner.invoke(app, ["detect", "--target", str(tmp_path)])
        assert result.exit_code == 0
        assert "Detected" in result.stdout

    def test_detect_cursor_environment(self, tmp_path: Path) -> None:
        """detect should find .cursor directory."""
        cursor_dir = tmp_path / ".cursor"
        cursor_dir.mkdir()

        result = runner.invoke(app, ["detect", "--target", str(tmp_path)])
        assert result.exit_code == 0
        assert "Detected" in result.stdout

    def test_detect_nonexistent_directory(self, tmp_path: Path) -> None:
        """detect should error on nonexistent directory."""
        fake_path = tmp_path / "nonexistent"
        result = runner.invoke(app, ["detect", "--target", str(fake_path)])
        assert result.exit_code == 1
        assert "does not exist" in result.stdout


# =============================================================================
# Init-Work Command Tests
# =============================================================================


class TestInitWorkCommand:
    """Tests for the 'init-work' command."""

    def test_init_work_creates_structure(self, tmp_path: Path) -> None:
        """init-work should create .work directory structure."""
        result = runner.invoke(app, ["init-work", "--target", str(tmp_path)])
        assert result.exit_code == 0
        assert "initialized" in result.stdout.lower()
        assert (tmp_path / ".work").exists()
        assert (tmp_path / ".work" / "agent").exists()
        assert (tmp_path / ".work" / "agent" / "issues").exists()

    def test_init_work_creates_issue_files(self, tmp_path: Path) -> None:
        """init-work should create priority issue files."""
        runner.invoke(app, ["init-work", "--target", str(tmp_path)])
        issues_dir = tmp_path / ".work" / "agent" / "issues"
        assert (issues_dir / "critical.md").exists()
        assert (issues_dir / "high.md").exists()
        assert (issues_dir / "medium.md").exists()
        assert (issues_dir / "low.md").exists()

    def test_init_work_creates_focus_and_memory(self, tmp_path: Path) -> None:
        """init-work should create focus.md and memory.md."""
        runner.invoke(app, ["init-work", "--target", str(tmp_path)])
        agent_dir = tmp_path / ".work" / "agent"
        assert (agent_dir / "focus.md").exists()
        assert (agent_dir / "memory.md").exists()

    def test_init_work_nonexistent_directory(self, tmp_path: Path) -> None:
        """init-work should error on nonexistent directory."""
        fake_path = tmp_path / "nonexistent"
        result = runner.invoke(app, ["init-work", "--target", str(fake_path)])
        assert result.exit_code == 1
        assert "does not exist" in result.stdout

    def test_init_work_with_force(self, tmp_path: Path) -> None:
        """init-work --force should work on existing structure."""
        # First init
        runner.invoke(app, ["init-work", "--target", str(tmp_path)])
        # Second init with force
        result = runner.invoke(app, ["init-work", "--target", str(tmp_path), "--force"])
        assert result.exit_code == 0


# =============================================================================
# Install Command Tests
# =============================================================================


class TestInstallCommand:
    """Tests for the 'install' command."""

    def test_install_nonexistent_target(self, tmp_path: Path) -> None:
        """install should error on nonexistent target."""
        fake_path = tmp_path / "nonexistent"
        result = runner.invoke(app, ["install", "--target", str(fake_path), "--env", "copilot"])
        assert result.exit_code == 1
        assert "does not exist" in result.stdout

    def test_install_unknown_environment(self, tmp_path: Path) -> None:
        """install should error on unknown environment."""
        result = runner.invoke(app, ["install", "--target", str(tmp_path), "--env", "unknown_env"])
        assert result.exit_code == 1
        assert "Unknown environment" in result.stdout

    def test_install_with_force_succeeds(self, tmp_path: Path) -> None:
        """install with --force should complete successfully."""
        result = runner.invoke(
            app, ["install", "--target", str(tmp_path), "--env", "copilot", "--force"]
        )
        assert result.exit_code == 0
        assert "complete" in result.stdout.lower()

    def test_install_creates_prompt_directory(self, tmp_path: Path) -> None:
        """install should create the prompt directory for the environment."""
        runner.invoke(app, ["install", "--target", str(tmp_path), "--env", "copilot", "--force"])
        assert (tmp_path / ".github" / "prompts").exists()

    def test_install_creates_prompt_files(self, tmp_path: Path) -> None:
        """install for copilot should create prompt files in .github/prompts."""
        runner.invoke(app, ["install", "--target", str(tmp_path), "--env", "copilot", "--force"])
        prompts_dir = tmp_path / ".github" / "prompts"
        assert prompts_dir.exists()
        # Should have at least one prompt file
        prompt_files = list(prompts_dir.glob("*.prompt.md"))
        assert len(prompt_files) > 0


# =============================================================================
# Init Command Tests
# =============================================================================


class TestInitCommand:
    """Tests for the 'init' command (alias for install)."""

    def test_init_nonexistent_target(self, tmp_path: Path) -> None:
        """init should error on nonexistent target."""
        fake_path = tmp_path / "nonexistent"
        result = runner.invoke(app, ["init", "--target", str(fake_path), "--env", "copilot"])
        assert result.exit_code == 1
        assert "does not exist" in result.stdout

    def test_init_with_env_succeeds(self, tmp_path: Path) -> None:
        """init with env should complete successfully."""
        result = runner.invoke(
            app, ["init", "--target", str(tmp_path), "--env", "copilot"], input="y\n"
        )
        # May prompt for confirmation, handle that
        assert result.exit_code == 0 or "complete" in result.stdout.lower()


# =============================================================================
# Validate JSON Command Tests
# =============================================================================


class TestValidateJsonCommand:
    """Tests for 'validate json' command."""

    def test_validate_json_valid_file(self, tmp_path: Path) -> None:
        """validate json should pass for valid JSON."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value"}')

        result = runner.invoke(app, ["validate", "json", str(json_file)])
        assert result.exit_code == 0
        assert "valid" in result.stdout.lower()

    def test_validate_json_invalid_file(self, tmp_path: Path) -> None:
        """validate json should fail for invalid JSON."""
        json_file = tmp_path / "test.json"
        json_file.write_text("{key: value}")  # Invalid JSON

        result = runner.invoke(app, ["validate", "json", str(json_file)])
        assert result.exit_code == 1
        assert "error" in result.stdout.lower()

    def test_validate_json_nonexistent_file(self, tmp_path: Path) -> None:
        """validate json should error on nonexistent file."""
        fake_file = tmp_path / "nonexistent.json"
        result = runner.invoke(app, ["validate", "json", str(fake_file)])
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_validate_json_with_schema(self, tmp_path: Path) -> None:
        """validate json with schema should validate structure."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"name": "test"}')

        schema_file = tmp_path / "schema.json"
        schema_file.write_text('{"type": "object", "required": ["name"]}')

        result = runner.invoke(
            app, ["validate", "json", str(json_file), "--schema", str(schema_file)]
        )
        assert result.exit_code == 0
        assert "valid" in result.stdout.lower()

    def test_validate_json_with_invalid_schema_file(self, tmp_path: Path) -> None:
        """validate json with invalid schema file should error."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"name": "test"}')

        schema_file = tmp_path / "schema.json"
        schema_file.write_text("not valid json")

        result = runner.invoke(
            app, ["validate", "json", str(json_file), "--schema", str(schema_file)]
        )
        assert result.exit_code == 1
        assert "Invalid schema file" in result.stdout

    def test_validate_json_schema_validation_fails(self, tmp_path: Path) -> None:
        """validate json should fail when data doesn't match schema."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"other": "field"}')

        schema_file = tmp_path / "schema.json"
        schema_file.write_text('{"type": "object", "required": ["name"]}')

        result = runner.invoke(
            app, ["validate", "json", str(json_file), "--schema", str(schema_file)]
        )
        assert result.exit_code == 1
        assert "Schema validation errors" in result.stdout

    def test_validate_json_with_nonexistent_schema(self, tmp_path: Path) -> None:
        """validate json should error if schema file doesn't exist."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"name": "test"}')

        fake_schema = tmp_path / "nonexistent.json"

        result = runner.invoke(
            app, ["validate", "json", str(json_file), "--schema", str(fake_schema)]
        )
        assert result.exit_code == 1
        assert "Schema file not found" in result.stdout


# =============================================================================
# Validate YAML Command Tests
# =============================================================================


class TestValidateYamlCommand:
    """Tests for 'validate yaml' command."""

    def test_validate_yaml_valid_file(self, tmp_path: Path) -> None:
        """validate yaml should pass for valid YAML."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("key: value\nlist:\n  - item1\n  - item2")

        result = runner.invoke(app, ["validate", "yaml", str(yaml_file)])
        assert result.exit_code == 0
        assert "valid" in result.stdout.lower()

    def test_validate_yaml_invalid_file(self, tmp_path: Path) -> None:
        """validate yaml should fail for invalid YAML."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("key: value\n  indentation: wrong")

        result = runner.invoke(app, ["validate", "yaml", str(yaml_file)])
        assert result.exit_code == 1
        assert "error" in result.stdout.lower()

    def test_validate_yaml_nonexistent_file(self, tmp_path: Path) -> None:
        """validate yaml should error on nonexistent file."""
        fake_file = tmp_path / "nonexistent.yaml"
        result = runner.invoke(app, ["validate", "yaml", str(fake_file)])
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_validate_yaml_frontmatter_mode(self, tmp_path: Path) -> None:
        """validate yaml --frontmatter should validate markdown frontmatter."""
        md_file = tmp_path / "test.md"
        md_file.write_text("---\ntitle: Test\nauthor: Me\n---\n\n# Content here")

        result = runner.invoke(app, ["validate", "yaml", str(md_file), "--frontmatter"])
        assert result.exit_code == 0
        assert "frontmatter" in result.stdout.lower()

    def test_validate_yaml_invalid_frontmatter(self, tmp_path: Path) -> None:
        """validate yaml --frontmatter should fail on invalid frontmatter."""
        md_file = tmp_path / "test.md"
        md_file.write_text("---\ntitle: [unclosed\n---\n\n# Content")

        result = runner.invoke(app, ["validate", "yaml", str(md_file), "--frontmatter"])
        assert result.exit_code == 1
        assert "error" in result.stdout.lower()


# =============================================================================
# Edge Cases and Integration
# =============================================================================


class TestEdgeCases:
    """Edge case and integration tests."""

    def test_install_then_detect(self, tmp_path: Path) -> None:
        """After install, detect should find the environment."""
        # Install copilot
        runner.invoke(app, ["install", "--target", str(tmp_path), "--env", "copilot", "--force"])
        # Detect should find it
        result = runner.invoke(app, ["detect", "--target", str(tmp_path)])
        assert result.exit_code == 0
        assert "Detected" in result.stdout

    def test_init_work_then_validate_structure(self, tmp_path: Path) -> None:
        """After init-work, the full structure should exist."""
        runner.invoke(app, ["init-work", "--target", str(tmp_path)])

        # Check all expected files
        work_dir = tmp_path / ".work"
        assert work_dir.exists()
        assert (work_dir / "agent" / "focus.md").exists()
        assert (work_dir / "agent" / "memory.md").exists()
        assert (work_dir / "agent" / "issues" / "critical.md").exists()
        assert (work_dir / "agent" / "issues" / "high.md").exists()
        assert (work_dir / "agent" / "issues" / "medium.md").exists()
        assert (work_dir / "agent" / "issues" / "low.md").exists()
        assert (work_dir / "agent" / "notes").exists()

    def test_validate_subcommand_no_args(self) -> None:
        """validate with no subcommand should show help or error."""
        result = runner.invoke(app, ["validate"])
        # May exit with code 2 (missing required arg) or 0 (showing help)
        # Check output for subcommands in either stdout or full output
        output = (result.stdout + (result.output or "")).lower()
        assert "json" in output or "yaml" in output or result.exit_code == 2

    def test_multiple_environments_in_list(self) -> None:
        """list should show multiple environments."""
        result = runner.invoke(app, ["list"])
        environments = ["copilot", "cursor", "claude", "windsurf", "aider"]
        found = sum(1 for env in environments if env in result.stdout.lower())
        assert found >= 3, f"Expected at least 3 environments in output: {result.stdout}"


# =============================================================================
# Review Command Tests (MIGRATE-011)
# =============================================================================


class TestReviewHelpCommands:
    """Tests for review command help output."""

    def test_review_help(self) -> None:
        """review --help should show subcommands."""
        result = runner.invoke(app, ["review", "--help"])
        assert result.exit_code == 0
        assert "start" in result.stdout
        assert "export" in result.stdout
        assert "clear" in result.stdout

    def test_review_start_help(self) -> None:
        """review start --help should show options."""
        result = runner.invoke(app, ["review", "start", "--help"])
        assert result.exit_code == 0
        assert "--port" in result.stdout
        assert "--base" in result.stdout
        assert "--head" in result.stdout

    def test_review_export_help(self) -> None:
        """review export --help should show options."""
        result = runner.invoke(app, ["review", "export", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.stdout
        assert "--review-id" in result.stdout

    def test_review_clear_help(self) -> None:
        """review clear --help should show options."""
        result = runner.invoke(app, ["review", "clear", "--help"])
        assert result.exit_code == 0
        assert "--review-id" in result.stdout
        assert "--force" in result.stdout


class TestReviewExportCommand:
    """Tests for review export command."""

    def test_review_export_no_git_repo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """review export should fail when not in a git repo."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["review", "export"])
        # Should fail - not in a git repo
        assert result.exit_code == 1
        output = result.stdout.lower()
        assert "git" in output or "repository" in output or "no review" in output

    def test_review_export_no_reviews(
        self, git_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """review export should fail when no reviews exist."""
        monkeypatch.chdir(git_repo)

        result = runner.invoke(app, ["review", "export"])
        # Should exit with code 1 - no reviews found
        assert result.exit_code == 1
        output = result.stdout.lower()
        assert "no review" in output or "not found" in output


class TestReviewClearCommand:
    """Tests for review clear command."""

    def test_review_clear_no_reviews_dir(
        self, git_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """review clear should handle missing reviews directory."""
        monkeypatch.chdir(git_repo)

        result = runner.invoke(app, ["review", "clear", "--force"])
        # Should succeed or warn - no reviews to clear
        assert result.exit_code == 0
        output = result.stdout.lower()
        assert "no review" in output or "warning" in output or "⚠" in result.stdout

    def test_review_clear_specific_review_not_found(
        self, git_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """review clear with non-existent review ID should fail."""
        monkeypatch.chdir(git_repo)

        # Create the reviews directory but no reviews
        reviews_dir = git_repo / ".work" / "reviews" / "reviews"
        reviews_dir.mkdir(parents=True, exist_ok=True)

        result = runner.invoke(
            app, ["review", "clear", "--review-id", "nonexistent-review", "--force"]
        )
        # Should exit with code 1 - review not found
        assert result.exit_code == 1
        output = result.stdout.lower()
        assert "not found" in output or "nonexistent" in output
