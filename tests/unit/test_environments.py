"""Tests for Environment configuration validation."""

import pytest

from dot_work.environments import Environment


class TestEnvironmentValidation:
    """Test Environment __post_init__ validation."""

    def test_valid_environment_with_prompt_dir(self) -> None:
        """Test that valid Environment with prompt_dir can be created."""
        env = Environment(
            key="test",
            name="Test Environment",
            prompt_dir=".test/prompts",
            prompt_extension=".md",
            instructions_file=None,
            rules_file=None,
        )
        assert env.prompt_dir == ".test/prompts"

    def test_valid_environment_without_prompt_dir(self) -> None:
        """Test that valid Environment without prompt_dir can be created."""
        env = Environment(
            key="test",
            name="Test Environment",
            prompt_dir=None,
            prompt_extension=None,
            instructions_file=None,
            rules_file=None,
        )
        assert env.prompt_dir is None

    def test_rejects_empty_prompt_dir(self) -> None:
        """Test that empty prompt_dir raises ValueError."""
        with pytest.raises(ValueError, match="prompt_dir cannot be empty"):
            Environment(
                key="test",
                name="Test Environment",
                prompt_dir="",  # Empty string
                prompt_extension=None,
                instructions_file=None,
                rules_file=None,
            )

    def test_rejects_whitespace_only_prompt_dir(self) -> None:
        """Test that whitespace-only prompt_dir raises ValueError."""
        with pytest.raises(ValueError, match="prompt_dir cannot be empty"):
            Environment(
                key="test",
                name="Test Environment",
                prompt_dir="   ",  # Whitespace only
                prompt_extension=None,
                instructions_file=None,
                rules_file=None,
            )

    def test_rejects_path_traversal(self) -> None:
        """Test that path traversal in prompt_dir raises ValueError."""
        with pytest.raises(ValueError, match="path traversal not allowed"):
            Environment(
                key="test",
                name="Test Environment",
                prompt_dir="../../../etc",  # Path traversal
                prompt_extension=None,
                instructions_file=None,
                rules_file=None,
            )

    def test_rejects_dotdot_slash(self) -> None:
        """Test that ../ prefix in prompt_dir raises ValueError."""
        with pytest.raises(ValueError, match="path traversal not allowed"):
            Environment(
                key="test",
                name="Test Environment",
                prompt_dir="../prompts",
                prompt_extension=None,
                instructions_file=None,
                rules_file=None,
            )

    def test_allows_relative_path(self) -> None:
        """Test that valid relative paths are allowed."""
        env = Environment(
            key="test",
            name="Test Environment",
            prompt_dir=".mydir/prompts",
            prompt_extension=None,
            instructions_file=None,
            rules_file=None,
        )
        assert env.prompt_dir == ".mydir/prompts"

    def test_allows_absolute_path_with_warning(self, caplog) -> None:
        """Test that absolute paths are allowed but trigger a warning."""
        import logging

        with caplog.at_level(logging.WARNING):
            env = Environment(
                key="test",
                name="Test Environment",
                prompt_dir="/absolute/path/prompts",
                prompt_extension=None,
                instructions_file=None,
                rules_file=None,
            )
        assert env.prompt_dir == "/absolute/path/prompts"
        assert "Relative paths are recommended" in caplog.text

    def test_error_message_includes_environment_info(self) -> None:
        """Test that error messages include environment name and key."""
        with pytest.raises(ValueError, match="Environment 'My Env' \\(key: my-key\\)"):
            Environment(
                key="my-key",
                name="My Env",
                prompt_dir="",
                prompt_extension=None,
                instructions_file=None,
                rules_file=None,
            )
