"""Unit tests for the installer module."""

from pathlib import Path

from dot_work.environments import ENVIRONMENTS
from dot_work.installer import create_jinja_env, render_prompt


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
