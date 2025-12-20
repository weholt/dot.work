"""Unit tests for the installer module."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from dot_work.environments import ENVIRONMENTS
from dot_work.installer import (
    create_jinja_env,
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
