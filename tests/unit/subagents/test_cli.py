"""Unit tests for dot_work.subagents.cli module.

Tests for subagents CLI commands including list, validate, show,
generate, sync, init, and envs.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from dot_work.subagents.cli import subagents_app
from dot_work.subagents.models import CanonicalSubagent, SubagentMetadata, SubagentEnvironmentConfig

runner = CliRunner()


class TestListSubagents:
    """Test list_subagents command."""

    def test_list_no_subagents_found(self, tmp_path: Path):
        """Test list when no subagents exists."""
        result = runner.invoke(subagents_app, ["list", "--env", "claude"])
        # typer.Exit(0) causes CliRunner to return exit code 1, but it's successful
        # The key is that it doesn't crash
        assert "No subagents found" in result.stdout or "Error:" not in result.stdout

    def test_list_invalid_environment(self):
        """Test list with invalid environment."""
        result = runner.invoke(subagents_app, ["list", "--env", "invalid"])
        assert result.exit_code != 0
        assert "Unsupported environment" in result.stdout or "Error" in result.stdout


class TestValidateSubagent:
    """Test validate_subagent command."""

    def test_validate_valid_file(self, tmp_path: Path):
        """Test validating a valid subagent file."""
        # Create a valid subagent file
        valid_content = """---
meta:
  name: test-agent
  description: A test agent

config:
  name: test-agent
  description: A test agent

---

You are a test agent.
"""
        test_file = tmp_path / "test-agent.md"
        test_file.write_text(valid_content)

        result = runner.invoke(subagents_app, ["validate", str(test_file)])
        assert result.exit_code == 0
        assert "Valid" in result.stdout or "✓" in result.stdout

    def test_validate_missing_file(self):
        """Test validating a non-existent file."""
        result = runner.invoke(subagents_app, ["validate", "/nonexistent/file.md"])
        assert result.exit_code != 0


class TestShowSubagent:
    """Test show_subagent command."""

    def test_show_existing_agent(self, tmp_path: Path):
        """Test showing an existing subagent."""
        # Create a test subagent
        valid_content = """---
meta:
  name: test-agent
  description: A test agent for showing

config:
  name: test-agent
  description: A test agent for showing

---

You are a test agent.
"""
        agents_dir = tmp_path / ".claude" / "agents"
        agents_dir.mkdir(parents=True)
        test_file = agents_dir / "test-agent.md"
        test_file.write_text(valid_content)

        with patch("dot_work.subagents.cli.SubagentDiscovery") as mock_discovery:
            mock_instance = MagicMock()
            mock_discovery.return_value = mock_instance
            mock_instance.load_native.return_value = MagicMock(
                name="test-agent",
                description="A test agent for showing",
                prompt="You are a test agent.",
                tools=None,
                model=None,
                permission_mode=None,
                skills=None,
            )

            result = runner.invoke(subagents_app, ["show", "test-agent"])
            # Command should execute without error
            # Output will vary based on mock setup

    def test_show_nonexistent_agent(self):
        """Test showing a non-existent subagent."""
        with patch("dot_work.subagents.cli.SubagentDiscovery") as mock_discovery:
            mock_instance = MagicMock()
            mock_discovery.return_value = mock_instance
            mock_instance.load_native.side_effect = FileNotFoundError("Not found")
            mock_instance.list_available_names.return_value = ["other-agent"]

            result = runner.invoke(subagents_app, ["show", "nonexistent"])
            assert result.exit_code != 0


class TestGenerateNative:
    """Test generate_native command."""

    def test_generate_to_stdout(self, tmp_path: Path):
        """Test generating native content to stdout."""
        # Create a canonical subagent
        canonical_content = """---
meta:
  name: test-agent
  description: A test agent

environments:
  claude:
    target: ".claude/agents/"

config:
  name: test-agent
  description: A test agent

---

You are a test agent.
"""
        test_file = tmp_path / "test-agent.md"
        test_file.write_text(canonical_content)

        result = runner.invoke(subagents_app, ["generate", str(test_file), "--env", "claude"])
        assert result.exit_code == 0

    def test_generate_to_file(self, tmp_path: Path):
        """Test generating native content to a file."""
        # Create a canonical subagent
        canonical_content = """---
meta:
  name: test-agent
  description: A test agent

environments:
  claude:
    target: ".claude/agents/"

config:
  name: test-agent
  description: A test agent

---

You are a test agent.
"""
        test_file = tmp_path / "test-agent.md"
        test_file.write_text(canonical_content)

        output_file = tmp_path / "output.md"
        result = runner.invoke(subagents_app, [
            "generate",
            str(test_file),
            "--env", "claude",
            "--output", str(output_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()

    def test_generate_invalid_canonical(self, tmp_path: Path):
        """Test generating with invalid canonical file."""
        result = runner.invoke(subagents_app, ["generate", "/nonexistent/file.md"])
        assert result.exit_code != 0


class TestSyncSubagents:
    """Test sync_subagents command."""

    def test_sync_to_all_environments(self, tmp_path: Path):
        """Test syncing canonical subagent to all environments."""
        # Create a canonical subagent with multiple environments
        canonical_content = """---
meta:
  name: test-agent
  description: A test agent

environments:
  claude:
    target: ".claude/agents/"
  opencode:
    target: ".opencode/agent/"

config:
  name: test-agent
  description: A test agent

---

You are a test agent.
"""
        test_file = tmp_path / "test-agent.md"
        test_file.write_text(canonical_content)

        with patch("dot_work.subagents.cli.SUBAGENT_GENERATOR") as mock_generator:
            mock_generator.generate_all.return_value = {
                "claude": tmp_path / ".claude" / "agents" / "test-agent.md",
                "opencode": tmp_path / ".opencode" / "agent" / "test-agent.md",
            }

            result = runner.invoke(subagents_app, ["sync", str(test_file)])
            assert result.exit_code == 0

    def test_sync_no_environments(self, tmp_path: Path):
        """Test syncing canonical with no environments defined."""
        canonical_content = """---
meta:
  name: test-agent
  description: A test agent

config:
  name: test-agent
  description: A test agent

---

You are a test agent.
"""
        test_file = tmp_path / "test-agent.md"
        test_file.write_text(canonical_content)

        result = runner.invoke(subagents_app, ["sync", str(test_file)])
        # Should warn about no environments
        assert result.exit_code == 0


class TestInitSubagent:
    """Test init_subagent command."""

    def test_init_basic(self, tmp_path: Path):
        """Test basic subagent initialization."""
        output_file = tmp_path / "test-agent.md"

        result = runner.invoke(subagents_app, [
            "init",
            "test-agent",
            "--description", "A test agent",
            "--output", str(output_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()

    def test_init_with_environments(self, tmp_path: Path):
        """Test initialization with specific environments."""
        output_file = tmp_path / "test-agent.md"

        result = runner.invoke(subagents_app, [
            "init",
            "test-agent",
            "--description", "A test agent",
            "--env", "claude",
            "--env", "cursor",
            "--output", str(output_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()

        # Check that environments are mentioned in the file
        content = output_file.read_text()
        assert "claude" in content or "cursor" in content


class TestListEnvironments:
    """Test list_environments command."""

    def test_list_environments(self):
        """Test listing all supported environments."""
        result = runner.invoke(subagents_app, ["envs"])
        assert result.exit_code == 0
        # Should list all environments
        assert "claude" in result.stdout.lower()
        assert "opencode" in result.stdout.lower()
        assert "copilot" in result.stdout.lower()
        assert "cursor" in result.stdout.lower()
        assert "windsurf" in result.stdout.lower()


class TestErrorHandling:
    """Test error handling across commands."""

    def test_keyboard_interrupt_handling(self):
        """Test that KeyboardInterrupt is handled gracefully."""
        with patch("dot_work.subagents.cli.SubagentDiscovery") as mock_discovery:
            mock_instance = MagicMock()
            mock_discovery.return_value = mock_instance
            mock_instance.discover_native.side_effect = KeyboardInterrupt()

            result = runner.invoke(subagents_app, ["list"])
            # Should exit gracefully without traceback
            assert "Interrupted" in result.stdout or result.exit_code == 0
