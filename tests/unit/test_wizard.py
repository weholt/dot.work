"""Tests for the prompt creation wizard."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from rich.console import Console

from dot_work.prompts.canonical import CanonicalPromptParser
from dot_work.prompts.wizard import (
    ENVIRONMENT_TARGETS,
    PROMPT_TYPES,
    PromptWizard,
    create_prompt_interactive,
)


@pytest.fixture
def mock_console() -> Mock:
    """Create a mock console that doesn't output."""
    console = Mock(spec=Console)
    return console


@pytest.fixture
def temp_prompts_dir(tmp_path: Path) -> Path:
    """Create a temporary prompts directory."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(parents=True)
    return prompts_dir


@pytest.fixture
def wizard(mock_console: Mock) -> PromptWizard:
    """Create a PromptWizard instance with mocked console."""
    return PromptWizard(console=mock_console)


class TestPromptWizard:
    """Tests for PromptWizard class."""

    def test_init_creates_wizard(self, wizard: PromptWizard) -> None:
        """Test wizard initialization."""
        assert wizard is not None
        assert wizard.console is not None

    def test_generate_filename_from_title(self, wizard: PromptWizard) -> None:
        """Test filename generation from title."""
        filename = wizard._generate_filename("My Cool Prompt", ".md")
        assert filename == "my-cool-prompt.md"

    def test_generate_filename_with_special_chars(self, wizard: PromptWizard) -> None:
        """Test filename generation with special characters."""
        filename = wizard._generate_filename("Hello@World! Test", ".md")
        assert filename == "hello-world-test.md"

    def test_generate_filename_with_spaces(self, wizard: PromptWizard) -> None:
        """Test filename generation with spaces."""
        filename = wizard._generate_filename("  Spaces Everywhere  ", ".md")
        assert filename == "spaces-everywhere.md"

    @patch("dot_work.installer.get_prompts_dir")
    def test_create_prompt_file_creates_valid_canonical_prompt(
        self,
        mock_get_prompts_dir: Mock,
        temp_prompts_dir: Path,
        wizard: PromptWizard,
    ) -> None:
        """Test that created prompt file has valid canonical frontmatter."""
        mock_get_prompts_dir.return_value = temp_prompts_dir

        prompt_path = wizard._create_prompt_file(
            title="Test Prompt",
            description="A test prompt for unit testing",
            version="0.1.0",
            environments=["claude", "copilot"],
        )

        # Verify file was created
        assert prompt_path.exists()
        assert prompt_path.name == "test-prompt.md"

        # Verify it parses as valid canonical prompt
        parser = CanonicalPromptParser()
        prompt = parser.parse(prompt_path)

        # Verify meta section
        assert prompt.meta["title"] == "Test Prompt"
        assert prompt.meta["description"] == "A test prompt for unit testing"
        assert prompt.meta["version"] == "0.1.0"

        # Verify environments
        assert "claude" in prompt.environments
        assert "copilot" in prompt.environments
        assert prompt.environments["claude"].target == ".claude/commands/"
        assert prompt.environments["copilot"].target == ".github/prompts/"

    @patch("dot_work.installer.get_prompts_dir")
    def test_create_prompt_file_overwrites_existing(
        self,
        mock_get_prompts_dir: Mock,
        temp_prompts_dir: Path,
        wizard: PromptWizard,
    ) -> None:
        """Test that existing file is overwritten when confirmed."""
        mock_get_prompts_dir.return_value = temp_prompts_dir

        # Create initial file
        wizard._create_prompt_file(
            title="Test Prompt",
            description="Initial content",
            version="0.1.0",
            environments=["claude"],
        )

        # Create new wizard that will overwrite
        new_wizard = PromptWizard(console=wizard.console)

        with patch.object(wizard.console, "print"):  # Mock console output
            with patch("dot_work.prompts.wizard.Confirm") as mock_confirm:
                mock_confirm.ask.return_value = True  # User confirms overwrite

                # Overwrite with new content
                new_path = new_wizard._create_prompt_file(
                    title="Test Prompt",
                    description="Updated content",
                    version="0.2.0",
                    environments=["copilot"],
                )

                # Verify file was updated
                content = new_path.read_text()
                assert "Updated content" in content
                assert "0.2.0" in content


class TestPromptWizardIntegration:
    """Integration tests for prompt wizard with mocked interactions."""

    @patch("dot_work.installer.get_prompts_dir")
    @patch("dot_work.prompts.wizard.subprocess.call")
    @patch("dot_work.prompts.wizard.Confirm")
    @patch("dot_work.prompts.wizard.Prompt")
    def test_create_prompt_interactive_non_blocking(
        self,
        mock_prompt_cls: Mock,
        mock_confirm: Mock,
        mock_subprocess: Mock,
        mock_get_prompts_dir: Mock,
        temp_prompts_dir: Path,
        mock_console: Mock,
    ) -> None:
        """Test non-interactive prompt creation with all parameters provided."""
        mock_get_prompts_dir.return_value = temp_prompts_dir

        # Mock confirmation (create file)
        mock_confirm.ask.return_value = True

        # Mock editor open
        mock_subprocess.call.return_value = 0

        # Run wizard non-interactively
        result = create_prompt_interactive(
            title="Non-Interactive Test",
            description="Testing non-interactive mode",
            prompt_type="review",
            environments=["claude", "cursor"],
            console=mock_console,
        )

        # Verify file was created
        assert result.exists()
        assert result.name == "non-interactive-test.md"

        # Verify content
        parser = CanonicalPromptParser()
        prompt = parser.parse(result)
        assert prompt.meta["title"] == "Non-Interactive Test"
        assert "claude" in prompt.environments
        assert "cursor" in prompt.environments


class TestPromptTypeSuggestions:
    """Tests for prompt type environment suggestions."""

    def test_agent_type_suggests_claude_and_opencode(self) -> None:
        """Test that agent type suggests claude and opencode."""
        agent_type = PROMPT_TYPES["agent"]
        assert "claude" in agent_type.suggested_environments
        assert "opencode" in agent_type.suggested_environments

    def test_command_type_suggests_claude_and_copilot(self) -> None:
        """Test that command type suggests claude and copilot."""
        command_type = PROMPT_TYPES["command"]
        assert "claude" in command_type.suggested_environments
        assert "copilot" in command_type.suggested_environments

    def test_review_type_suggests_all_environments(self) -> None:
        """Test that review type suggests all environments."""
        review_type = PROMPT_TYPES["review"]
        assert len(review_type.suggested_environments) > 5
        # Check for key environments
        assert "claude" in review_type.suggested_environments
        assert "copilot" in review_type.suggested_environments
        assert "cursor" in review_type.suggested_environments


class TestEnvironmentTargets:
    """Tests for environment target configurations."""

    def test_claude_target_configuration(self) -> None:
        """Test Claude environment target configuration."""
        target, suffix = ENVIRONMENT_TARGETS["claude"]
        assert target == ".claude/commands/"
        assert suffix == ".md"

    def test_copilot_target_configuration(self) -> None:
        """Test Copilot environment target configuration."""
        target, suffix = ENVIRONMENT_TARGETS["copilot"]
        assert target == ".github/prompts/"
        assert suffix == ".md"

    def test_cursor_target_configuration(self) -> None:
        """Test Cursor environment target configuration."""
        target, suffix = ENVIRONMENT_TARGETS["cursor"]
        assert target == ".cursor/rules/"
        assert suffix == ".mdc"

    def test_all_environments_have_valid_targets(self) -> None:
        """Test that all environments have valid target configurations."""
        for env, (target, suffix) in ENVIRONMENT_TARGETS.items():
            assert target.startswith(".") or target.startswith("/"), f"Invalid target for {env}"
            assert suffix.startswith("."), f"Invalid suffix for {env}"
            assert "/" in target, f"Target path for {env} should contain /"


class TestWizardValidation:
    """Tests for wizard validation of created prompts."""

    @patch("dot_work.installer.get_prompts_dir")
    def test_created_prompt_passes_validation(
        self,
        mock_get_prompts_dir: Mock,
        temp_prompts_dir: Path,
    ) -> None:
        """Test that prompts created by wizard pass validation."""
        mock_get_prompts_dir.return_value = temp_prompts_dir

        wizard = PromptWizard()

        # Create a prompt
        prompt_path = wizard._create_prompt_file(
            title="Validation Test",
            description="Testing wizard validation",
            version="0.1.0",
            environments=["claude"],
        )

        # Validate the created prompt
        from dot_work.prompts.canonical import CanonicalPromptValidator

        parser = CanonicalPromptParser()
        validator = CanonicalPromptValidator()

        prompt = parser.parse(prompt_path)
        errors = validator.validate(prompt, strict=False)

        # Should have no errors (only warnings at most)
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0, f"Validation errors: {error_errors}"


class TestWizardErrorHandling:
    """Tests for wizard error handling."""

    def test_create_prompt_interactive_handles_keyboard_interrupt(
        self,
        mock_console: Mock,
    ) -> None:
        """Test that keyboard interrupt is handled gracefully."""
        wizard = PromptWizard(console=mock_console)

        with patch.object(wizard, "_prompt_title", side_effect=KeyboardInterrupt):
            with pytest.raises(KeyboardInterrupt):
                wizard.run()

    @patch("dot_work.installer.get_prompts_dir")
    def test_create_prompt_file_handles_write_error(
        self,
        mock_get_prompts_dir: Mock,
        wizard: PromptWizard,
    ) -> None:
        """Test that write errors are handled gracefully."""
        # Use a directory that doesn't exist and can't be created
        mock_get_prompts_dir.return_value = Path("/nonexistent/path/that/does/not/exist")

        with pytest.raises(OSError):
            wizard._create_prompt_file(
                title="Error Test",
                description="Testing error handling",
                version="0.1.0",
                environments=["claude"],
            )
