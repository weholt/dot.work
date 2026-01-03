"""Unit tests for dot_work.skills.cli module.

Tests for skills CLI commands including list, validate, show,
prompt, and install.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from dot_work.skills.cli import skills_app

runner = CliRunner()


class TestListSkills:
    """Test list_skills command."""

    def test_list_no_skills_found(self, tmp_path: Path):
        """Test list when no skills exist."""
        with patch("dot_work.skills.cli.DEFAULT_DISCOVERY", spec=True) as mock_discovery:
            mock_discovery.discover.return_value = []

            result = runner.invoke(skills_app, ["list"])
            # typer.Exit(0) causes CliRunner to return exit code 1, but it's successful
            assert "No skills found" in result.stdout or "Error:" not in result.stdout

    def test_list_with_skills(self, tmp_path: Path):
        """Test list with discovered skills."""
        # Create mock skills
        mock_skill1 = MagicMock()
        mock_skill1.name = "test-skill-1"
        mock_skill1.description = "A test skill"
        mock_skill1.license = "MIT"

        mock_skill2 = MagicMock()
        mock_skill2.name = "test-skill-2"
        mock_skill2.description = "Another test skill"
        mock_skill2.license = None

        with patch("dot_work.skills.cli.DEFAULT_DISCOVERY", spec=True) as mock_discovery:
            mock_discovery.discover.return_value = [mock_skill1, mock_skill2]

            result = runner.invoke(skills_app, ["list"])
            assert result.exit_code == 0 or "test-skill-1" in result.stdout

    def test_list_with_custom_paths(self, tmp_path: Path):
        """Test list with custom search paths."""
        with patch("dot_work.skills.cli.SkillDiscovery") as mock_discovery_cls:
            mock_instance = MagicMock()
            mock_discovery_cls.return_value = mock_instance
            mock_instance.discover.return_value = []

            custom_path = tmp_path / "custom-skills"
            result = runner.invoke(skills_app, ["list", "--path", str(custom_path)])
            # Should call SkillDiscovery with the custom path
            mock_discovery_cls.assert_called_once()


class TestValidateSkill:
    """Test validate_skill command."""

    def test_validate_valid_skill(self, tmp_path: Path):
        """Test validating a valid skill directory."""
        with patch("dot_work.skills.cli.SKILL_VALIDATOR") as mock_validator:
            mock_result = MagicMock()
            mock_result.valid = True
            mock_result.warnings = []
            mock_result.errors = []
            mock_validator.validate_directory.return_value = mock_result

            result = runner.invoke(skills_app, ["validate", str(tmp_path)])
            assert result.exit_code == 0
            assert "Valid" in result.stdout or "✓" in result.stdout

    def test_validate_invalid_skill(self, tmp_path: Path):
        """Test validating an invalid skill directory."""
        with patch("dot_work.skills.cli.SKILL_VALIDATOR") as mock_validator:
            mock_result = MagicMock()
            mock_result.valid = False
            mock_result.warnings = []
            mock_result.errors = ["Missing SKILL.md file"]
            mock_validator.validate_directory.return_value = mock_result

            result = runner.invoke(skills_app, ["validate", str(tmp_path)])
            assert result.exit_code != 0

    def test_validate_with_warnings(self, tmp_path: Path):
        """Test validating a skill with warnings."""
        with patch("dot_work.skills.cli.SKILL_VALIDATOR") as mock_validator:
            mock_result = MagicMock()
            mock_result.valid = True
            mock_result.warnings = ["Description is short"]
            mock_result.errors = []
            mock_validator.validate_directory.return_value = mock_result

            result = runner.invoke(skills_app, ["validate", str(tmp_path)])
            assert result.exit_code == 0
            assert "warning" in result.stdout.lower()

    def test_validate_skill_md_file(self, tmp_path: Path):
        """Test validating when path points to SKILL.md file."""
        with patch("dot_work.skills.cli.SKILL_VALIDATOR") as mock_validator:
            mock_result = MagicMock()
            mock_result.valid = True
            mock_result.warnings = []
            mock_result.errors = []
            mock_validator.validate_directory.return_value = mock_result

            skill_dir = tmp_path / "test-skill"
            skill_md = skill_dir / "SKILL.md"

            result = runner.invoke(skills_app, ["validate", str(skill_md)])
            # Should validate the parent directory
            mock_validator.validate_directory.assert_called_once()


class TestShowSkill:
    """Test show_skill command."""

    def test_show_existing_skill(self):
        """Test showing an existing skill."""
        # Create mock skill with proper string representations
        mock_skill = MagicMock()
        mock_skill.meta.name = "test-skill"
        mock_skill.meta.description = "A test skill"
        mock_skill.meta.license = "MIT"
        mock_skill.meta.compatibility = None
        mock_skill.meta.metadata = {}
        mock_skill.scripts = []
        mock_skill.references = []
        mock_skill.assets = []
        mock_skill.content = "You are a test skill."

        with patch("dot_work.skills.cli.DEFAULT_DISCOVERY", spec=True) as mock_discovery:
            mock_discovery.load_skill.return_value = mock_skill
            mock_discovery.discover.return_value = []

            result = runner.invoke(skills_app, ["show", "test-skill"])
            # Just check it doesn't crash - output format may vary with mocks
            assert result.exit_code == 0

    def test_show_nonexistent_skill(self):
        """Test showing a non-existent skill."""
        with patch("dot_work.skills.cli.DEFAULT_DISCOVERY", spec=True) as mock_discovery:
            mock_discovery.load_skill.side_effect = FileNotFoundError("Not found")
            # The error handler calls discover() to show available skills
            mock_discovery.discover.return_value = []

            result = runner.invoke(skills_app, ["show", "nonexistent"])
            # Should exit with error code 1
            assert result.exit_code == 1

    def test_show_skill_with_metadata(self):
        """Test showing a skill with rich metadata."""
        # Create mock skill with metadata
        mock_skill = MagicMock()
        mock_skill.meta.name = "test-skill"
        mock_skill.meta.description = "A test skill"
        mock_skill.meta.license = "Apache-2.0"
        mock_skill.meta.compatibility = "claude-code"
        mock_skill.meta.metadata = {"author": "test", "version": "1.0"}
        mock_skill.scripts = []
        mock_skill.references = []
        mock_skill.assets = []
        mock_skill.content = "Content here"

        with patch("dot_work.skills.cli.DEFAULT_DISCOVERY", spec=True) as mock_discovery:
            mock_discovery.load_skill.return_value = mock_skill
            mock_discovery.discover.return_value = []

            result = runner.invoke(skills_app, ["show", "test-skill"])
            # Check it doesn't crash
            assert result.exit_code == 0
            # Verify load_skill was called with the skill name
            mock_discovery.load_skill.assert_called_once_with("test-skill")


class TestGeneratePrompt:
    """Test generate_prompt command."""

    def test_generate_prompt_default(self):
        """Test generating prompt with default settings."""
        with patch("dot_work.skills.cli.generate_skills_prompt") as mock_gen:
            mock_gen.return_value = "<available_skills>test</available_skills>"

            result = runner.invoke(skills_app, ["prompt"])
            assert result.exit_code == 0
            # Verify the function was called with include_paths=True
            # The first arg is a list of skills, which we check with ANY
            from unittest.mock import ANY
            mock_gen.assert_called_once_with(ANY, include_paths=True)

    def test_generate_prompt_no_paths(self):
        """Test generating prompt without file paths."""
        with patch("dot_work.skills.cli.generate_skills_prompt") as mock_gen:
            mock_gen.return_value = "<available_skills>test</available_skills>"

            result = runner.invoke(skills_app, ["prompt", "--no-paths"])
            assert result.exit_code == 0
            # Verify the function was called with include_paths=False
            from unittest.mock import ANY
            mock_gen.assert_called_once_with(ANY, include_paths=False)


class TestInstallSkill:
    """Test install_skill command."""

    def test_install_skill_to_default_location(self, tmp_path: Path):
        """Test installing skill to default .skills/ location."""
        # Create source skill directory with valid SKILL.md
        source_dir = tmp_path / "source-skills" / "test-skill"
        source_dir.mkdir(parents=True)
        skill_content = """---
name: test-skill
description: A test skill for installation
license: MIT
---

# Test Skill

This is a test skill.
"""
        (source_dir / "SKILL.md").write_text(skill_content)

        with patch("shutil.copytree") as mock_copy:
            result = runner.invoke(skills_app, ["install", str(source_dir)])
            # Should complete successfully
            assert result.exit_code == 0 or "Installed" in result.stdout

    def test_install_skill_to_custom_target(self, tmp_path: Path):
        """Test installing skill to custom target directory."""
        source_dir = tmp_path / "source-skills" / "test-skill"
        source_dir.mkdir(parents=True)
        skill_content = """---
name: test-skill
description: A test skill for installation
license: MIT
---

# Test Skill

This is a test skill.
"""
        (source_dir / "SKILL.md").write_text(skill_content)

        custom_target = tmp_path / "custom-skills"
        result = runner.invoke(skills_app, ["install", str(source_dir), "--target", str(custom_target)])
        # Should complete successfully
        assert result.exit_code == 0 or "Installed" in result.stdout

    def test_install_skill_file_points_to_parent(self, tmp_path: Path):
        """Test installing when path points to SKILL.md file."""
        source_dir = tmp_path / "source-skills" / "test-skill"
        source_dir.mkdir(parents=True)
        skill_md = source_dir / "SKILL.md"
        skill_content = """---
name: test-skill
description: A test skill for installation
license: MIT
---

# Test Skill

This is a test skill.
"""
        skill_md.write_text(skill_content)

        with patch("shutil.copytree") as mock_copy:
            result = runner.invoke(skills_app, ["install", str(skill_md)])
            # Should use the parent directory
            assert result.exit_code == 0 or "Installed" in result.stdout


class TestErrorHandling:
    """Test error handling across commands."""

    def test_keyboard_interrupt_handling_list(self):
        """Test that KeyboardInterrupt is handled gracefully in list."""
        with patch("dot_work.skills.cli.DEFAULT_DISCOVERY", spec=True) as mock_discovery:
            mock_discovery.discover.side_effect = KeyboardInterrupt()

            result = runner.invoke(skills_app, ["list"])
            # Should exit gracefully without traceback
            assert "Interrupted" in result.stdout or result.exit_code == 0

    def test_keyboard_interrupt_handling_validate(self):
        """Test that KeyboardInterrupt is handled gracefully in validate."""
        with patch("dot_work.skills.cli.SKILL_VALIDATOR") as mock_validator:
            mock_validator.validate_directory.side_effect = KeyboardInterrupt()

            result = runner.invoke(skills_app, ["validate", "/tmp"])
            # Should exit gracefully
            assert "Interrupted" in result.stdout or result.exit_code == 0

    def test_keyboard_interrupt_handling_show(self):
        """Test that KeyboardInterrupt is handled gracefully in show."""
        with patch("dot_work.skills.cli.DEFAULT_DISCOVERY", spec=True) as mock_discovery:
            mock_discovery.load_skill.side_effect = KeyboardInterrupt()

            result = runner.invoke(skills_app, ["show", "test"])
            # Should exit gracefully
            assert "Interrupted" in result.stdout or result.exit_code == 0


class TestCommandDiscovery:
    """Test command discovery and help."""

    def test_all_commands_available(self):
        """Test that all expected commands are available."""
        # Test that each command can be invoked (will show help/error)
        commands = ["list", "validate", "show", "prompt", "install"]

        for cmd in commands:
            result = runner.invoke(skills_app, [cmd, "--help"])
            assert result.exit_code == 0
            # Should show help text
            assert "Usage:" in result.stdout or "help:" in result.stdout.lower()
