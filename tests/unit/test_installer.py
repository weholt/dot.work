"""Unit tests for the installer module."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from dot_work.environments import ENVIRONMENTS
from dot_work.installer import (
    create_jinja_env,
    detect_project_context,
    initialize_work_directory,
    install_for_copilot,
    install_prompts,
    render_prompt,
    should_write_file,
)


class TestShouldWriteFile:
    """Tests for should_write_file helper function."""

    def test_returns_true_if_file_does_not_exist(self, tmp_path: Path) -> None:
        """Test that new files are always written."""
        dest_path = tmp_path / "new_file.md"
        console = MagicMock()

        result = should_write_file(dest_path, force=False, console=console)

        assert result is True
        console.input.assert_not_called()

    def test_returns_true_if_force_is_true(self, tmp_path: Path) -> None:
        """Test that force=True overwrites without prompting."""
        dest_path = tmp_path / "existing.md"
        dest_path.write_text("existing content", encoding="utf-8")
        console = MagicMock()

        result = should_write_file(dest_path, force=True, console=console)

        assert result is True
        console.input.assert_not_called()

    def test_prompts_user_when_file_exists_no_force(self, tmp_path: Path) -> None:
        """Test that user is prompted when file exists and force=False."""
        dest_path = tmp_path / "existing.md"
        dest_path.write_text("existing content", encoding="utf-8")
        console = MagicMock()
        console.input.return_value = "y"

        result = should_write_file(dest_path, force=False, console=console)

        assert result is True
        console.input.assert_called_once()

    def test_returns_false_when_user_declines(self, tmp_path: Path) -> None:
        """Test that user can decline overwriting."""
        dest_path = tmp_path / "existing.md"
        dest_path.write_text("existing content", encoding="utf-8")
        console = MagicMock()
        console.input.return_value = "n"

        result = should_write_file(dest_path, force=False, console=console)

        assert result is False

    def test_accepts_yes_lowercase(self, tmp_path: Path) -> None:
        """Test that 'yes' is accepted as confirmation."""
        dest_path = tmp_path / "existing.md"
        dest_path.write_text("existing content", encoding="utf-8")
        console = MagicMock()
        console.input.return_value = "yes"

        result = should_write_file(dest_path, force=False, console=console)

        assert result is True


class TestInstallPrompts:
    """Tests for install_prompts function."""

    def test_passes_force_to_installer(
        self, temp_project_dir: Path, sample_prompts_dir: Path
    ) -> None:
        """Test that force parameter is passed through to environment installer."""
        console = MagicMock()

        # Install once
        install_prompts("copilot", temp_project_dir, sample_prompts_dir, console)

        # Install again with force
        install_prompts(
            "copilot", temp_project_dir, sample_prompts_dir, console, force=True
        )

        # Files should exist and be overwritten
        dest_dir = temp_project_dir / ".github" / "prompts"
        assert (dest_dir / "test.prompt.md").exists()

    def test_raises_for_unknown_environment(
        self, temp_project_dir: Path, sample_prompts_dir: Path
    ) -> None:
        """Test that unknown environment raises ValueError."""
        console = MagicMock()

        with pytest.raises(ValueError, match="Unknown environment"):
            install_prompts(
                "nonexistent", temp_project_dir, sample_prompts_dir, console
            )


class TestInstallForCopilotWithForce:
    """Tests for install_for_copilot with force parameter."""

    def test_skips_existing_files_without_force(
        self, temp_project_dir: Path, sample_prompts_dir: Path
    ) -> None:
        """Test that existing files are skipped when force=False and user declines."""
        console = MagicMock()
        console.input.return_value = "n"

        # Create existing file
        dest_dir = temp_project_dir / ".github" / "prompts"
        dest_dir.mkdir(parents=True)
        existing_file = dest_dir / "test.prompt.md"
        existing_file.write_text("original content", encoding="utf-8")

        install_for_copilot(temp_project_dir, sample_prompts_dir, console, force=False)

        # File should remain unchanged
        assert existing_file.read_text(encoding="utf-8") == "original content"

    def test_overwrites_with_force(
        self, temp_project_dir: Path, sample_prompts_dir: Path
    ) -> None:
        """Test that force=True overwrites existing files."""
        console = MagicMock()

        # Create existing file
        dest_dir = temp_project_dir / ".github" / "prompts"
        dest_dir.mkdir(parents=True)
        existing_file = dest_dir / "test.prompt.md"
        existing_file.write_text("original content", encoding="utf-8")

        install_for_copilot(temp_project_dir, sample_prompts_dir, console, force=True)

        # File should be overwritten with new content
        new_content = existing_file.read_text(encoding="utf-8")
        assert new_content != "original content"
        assert "Test Prompt" in new_content


class TestCreateJinjaEnv:
    """Tests for create_jinja_env function."""

    def test_creates_environment_with_loader(self, sample_prompts_dir: Path) -> None:
        """Test that Jinja environment is created with FileSystemLoader."""
        env = create_jinja_env(sample_prompts_dir)
        assert env is not None
        assert env.loader is not None

    def test_keeps_trailing_newline(self, sample_prompts_dir: Path) -> None:
        """Test that trailing newlines are preserved."""
        env = create_jinja_env(sample_prompts_dir)
        assert env.keep_trailing_newline is True


class TestRenderPrompt:
    """Tests for render_prompt function."""

    def test_renders_template_with_copilot_values(self, sample_prompts_dir: Path) -> None:
        """Test that template variables are substituted correctly for Copilot."""
        prompt_file = sample_prompts_dir / "test.prompt.md"
        env_config = ENVIRONMENTS["copilot"]

        result = render_prompt(sample_prompts_dir, prompt_file, env_config)

        assert ".github/prompts" in result
        assert "copilot" in result

    def test_renders_template_with_cursor_values(self, sample_prompts_dir: Path) -> None:
        """Test that template variables are substituted correctly for Cursor."""
        prompt_file = sample_prompts_dir / "another.prompt.md"
        env_config = ENVIRONMENTS["cursor"]

        result = render_prompt(sample_prompts_dir, prompt_file, env_config)

        assert ".mdc" in result

    def test_renders_template_with_generic_values(self, sample_prompts_dir: Path) -> None:
        """Test that template variables are substituted correctly for generic."""
        prompt_file = sample_prompts_dir / "test.prompt.md"
        env_config = ENVIRONMENTS["generic"]

        result = render_prompt(sample_prompts_dir, prompt_file, env_config)

        assert "prompts" in result
        assert "generic" in result


class TestDetectProjectContext:
    """Tests for detect_project_context function."""

    def test_detects_python_with_pyproject(self, tmp_path: Path) -> None:
        """Test detection of Python project with pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\n', encoding="utf-8")

        result = detect_project_context(tmp_path)

        assert result["language"] == "Python"
        assert "uv" in result["package_manager"] or "pip" in result["package_manager"]

    def test_detects_pytest(self, tmp_path: Path) -> None:
        """Test detection of pytest from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\nname = "test"\n[tool.pytest]\n', encoding="utf-8"
        )

        result = detect_project_context(tmp_path)

        assert result["test_framework"] == "pytest"

    def test_detects_typer_framework(self, tmp_path: Path) -> None:
        """Test detection of Typer framework from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\ndependencies = ["typer"]\n', encoding="utf-8"
        )

        result = detect_project_context(tmp_path)

        assert result["framework"] == "Typer (CLI)"

    def test_detects_nodejs(self, tmp_path: Path) -> None:
        """Test detection of Node.js project."""
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test"}', encoding="utf-8")

        result = detect_project_context(tmp_path)

        assert result["language"] == "JavaScript/TypeScript"
        assert "npm" in result["package_manager"]

    def test_detects_rust(self, tmp_path: Path) -> None:
        """Test detection of Rust project."""
        cargo = tmp_path / "Cargo.toml"
        cargo.write_text('[package]\nname = "test"\n', encoding="utf-8")

        result = detect_project_context(tmp_path)

        assert result["language"] == "Rust"
        assert result["package_manager"] == "cargo"

    def test_detects_go(self, tmp_path: Path) -> None:
        """Test detection of Go project."""
        gomod = tmp_path / "go.mod"
        gomod.write_text("module test\n", encoding="utf-8")

        result = detect_project_context(tmp_path)

        assert result["language"] == "Go"

    def test_returns_unknown_for_empty_dir(self, tmp_path: Path) -> None:
        """Test that empty directory returns unknown values."""
        result = detect_project_context(tmp_path)

        assert result["language"] == "unknown"
        assert result["framework"] == "unknown"


class TestInitializeWorkDirectory:
    """Tests for initialize_work_directory function."""

    def test_creates_work_directory_structure(self, tmp_path: Path) -> None:
        """Test that all directories are created."""
        console = MagicMock()

        initialize_work_directory(tmp_path, console, force=True)

        assert (tmp_path / ".work").is_dir()
        assert (tmp_path / ".work" / "agent").is_dir()
        assert (tmp_path / ".work" / "agent" / "issues").is_dir()
        assert (tmp_path / ".work" / "agent" / "notes").is_dir()
        assert (tmp_path / ".work" / "agent" / "issues" / "references").is_dir()

    def test_creates_all_issue_files(self, tmp_path: Path) -> None:
        """Test that all issue priority files are created."""
        console = MagicMock()

        initialize_work_directory(tmp_path, console, force=True)

        issues_dir = tmp_path / ".work" / "agent" / "issues"
        assert (issues_dir / "critical.md").exists()
        assert (issues_dir / "high.md").exists()
        assert (issues_dir / "medium.md").exists()
        assert (issues_dir / "low.md").exists()
        assert (issues_dir / "backlog.md").exists()
        assert (issues_dir / "shortlist.md").exists()
        assert (issues_dir / "history.md").exists()

    def test_creates_focus_and_memory_files(self, tmp_path: Path) -> None:
        """Test that focus.md and memory.md are created."""
        console = MagicMock()

        initialize_work_directory(tmp_path, console, force=True)

        agent_dir = tmp_path / ".work" / "agent"
        assert (agent_dir / "focus.md").exists()
        assert (agent_dir / "memory.md").exists()

    def test_creates_baseline_placeholder(self, tmp_path: Path) -> None:
        """Test that baseline.md placeholder is created."""
        console = MagicMock()

        initialize_work_directory(tmp_path, console, force=True)

        baseline = tmp_path / ".work" / "baseline.md"
        assert baseline.exists()
        assert "Not yet generated" in baseline.read_text(encoding="utf-8")

    def test_creates_gitkeep_files(self, tmp_path: Path) -> None:
        """Test that .gitkeep files are created in empty directories."""
        console = MagicMock()

        initialize_work_directory(tmp_path, console, force=True)

        assert (tmp_path / ".work" / "agent" / "notes" / ".gitkeep").exists()
        assert (
            tmp_path / ".work" / "agent" / "issues" / "references" / ".gitkeep"
        ).exists()

    def test_skips_existing_files_without_force(self, tmp_path: Path) -> None:
        """Test that existing files are skipped when force=False."""
        console = MagicMock()
        console.input.return_value = "n"  # Decline overwrite

        # Create the structure first
        initialize_work_directory(tmp_path, console, force=True)

        # Modify a file
        focus_file = tmp_path / ".work" / "agent" / "focus.md"
        original_content = focus_file.read_text(encoding="utf-8")
        focus_file.write_text("Modified content", encoding="utf-8")

        # Run again without force
        initialize_work_directory(tmp_path, console, force=False)

        # File should still have modified content
        assert focus_file.read_text(encoding="utf-8") == "Modified content"

    def test_overwrites_with_force(self, tmp_path: Path) -> None:
        """Test that existing files are overwritten when force=True."""
        console = MagicMock()

        # Create the structure first
        initialize_work_directory(tmp_path, console, force=True)

        # Modify a file
        focus_file = tmp_path / ".work" / "agent" / "focus.md"
        focus_file.write_text("Modified content", encoding="utf-8")

        # Run again with force
        initialize_work_directory(tmp_path, console, force=True)

        # File should be reset
        assert "Modified content" not in focus_file.read_text(encoding="utf-8")
        assert "Agent Focus" in focus_file.read_text(encoding="utf-8")

    def test_memory_has_detected_context(self, tmp_path: Path) -> None:
        """Test that memory.md contains detected project context."""
        console = MagicMock()

        # Create a Python project marker
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\n', encoding="utf-8")

        initialize_work_directory(tmp_path, console, force=True)

        memory_content = (tmp_path / ".work" / "agent" / "memory.md").read_text(
            encoding="utf-8"
        )
        assert "Python" in memory_content
