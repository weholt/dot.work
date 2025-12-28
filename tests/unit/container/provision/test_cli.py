"""Tests for container provision CLI module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer

from dot_work.container.provision.cli import init


class TestCLICommands:
    """Test the CLI commands."""

    def test_init_creates_template(self, tmp_path: Path) -> None:
        """Test that init command creates a template file."""
        output_file = tmp_path / "test-instructions.md"

        # Run init command
        init(output_file, force=False)

        # Check file was created
        assert output_file.exists(), "Template file was not created"

        # Check content has frontmatter
        content = output_file.read_text()
        assert "---" in content, "Template missing frontmatter"
        assert "repo_url:" in content, "Template missing repo_url field"

    def test_init_overwrites_with_force(self, tmp_path: Path) -> None:
        """Test that init with force overwrites existing file."""
        output_file = tmp_path / "test-instructions.md"

        # Create existing file
        output_file.write_text("existing content")

        # Run init with force
        init(output_file, force=True)

        # Check content was replaced
        content = output_file.read_text()
        assert "existing content" not in content, "File was not overwritten"
        assert "repo_url:" in content, "Template not created"

    def test_init_fails_without_force(self, tmp_path: Path) -> None:
        """Test that init fails when file exists without force."""
        output_file = tmp_path / "test-instructions.md"

        # Create existing file
        output_file.write_text("existing content")

        # Should raise typer.Exit
        with pytest.raises(typer.Exit):
            init(output_file, force=False)

    @patch("dot_work.container.provision.validation.validate_instructions")
    def test_validate_command(self, mock_validate: MagicMock, tmp_path: Path) -> None:
        """Test that validate command calls validate_instructions."""
        # Create test file
        test_file = tmp_path / "instructions.md"
        test_file.write_text("---\nrepo_url: test\n---\n")

        # Import and run validate
        from dot_work.container.provision.cli import validate

        # Run validate (should not raise if mock doesn't raise)
        validate(test_file)

        # Check validate_instructions was called
        mock_validate.assert_called_once_with(test_file)

    @patch("dot_work.container.provision.validation.validate_instructions")
    def test_validate_command_handles_error(self, mock_validate: MagicMock, tmp_path: Path) -> None:
        """Test that validate command handles RepoAgentError."""
        from dot_work.container.provision.core import RepoAgentError

        # Create test file
        test_file = tmp_path / "instructions.md"
        test_file.write_text("---\nrepo_url: test\n---\n")

        # Import and run validate
        from dot_work.container.provision.cli import validate

        # Mock validate to raise error
        mock_validate.side_effect = RepoAgentError("Test error")

        # Should raise typer.Exit
        with pytest.raises(typer.Exit):
            validate(test_file)
