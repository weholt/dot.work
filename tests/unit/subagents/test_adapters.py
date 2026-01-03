"""Unit tests for environment adapters.

Tests for CursorAdapter and WindsurfAdapter, ensuring they correctly
generate and parse native subagent file formats.
"""

import pytest
from pathlib import Path

from dot_work.subagents.environments import get_adapter, get_supported_environments
from dot_work.subagents.environments.cursor import CursorAdapter
from dot_work.subagents.environments.windsurf import WindsurfAdapter
from dot_work.subagents.models import SubagentConfig


class TestCursorAdapter:
    """Test CursorAdapter for Cursor AI .mdc format."""

    def test_adapter_in_registry(self):
        """Cursor adapter should be registered in environment registry."""
        adapter = get_adapter("cursor")
        assert isinstance(adapter, CursorAdapter)

    def test_supported_environments_includes_cursor(self):
        """cursor should be in supported environments list."""
        envs = get_supported_environments()
        assert "cursor" in envs

    def test_get_target_path(self):
        """Target path should be .cursor/rules/."""
        adapter = CursorAdapter()
        project_root = Path("/test/project")
        target = adapter.get_target_path(project_root)
        assert target == project_root / ".cursor" / "rules"

    def test_generate_filename(self):
        """Filename should use .mdc extension."""
        adapter = CursorAdapter()
        config = SubagentConfig(
            name="test-agent",
            description="A test agent",
            prompt="Test prompt"
        )
        filename = adapter.generate_filename(config)
        assert filename == "test-agent.mdc"

    def test_generate_native_minimal(self):
        """Generate minimal .mdc file content."""
        adapter = CursorAdapter()
        config = SubagentConfig(
            name="test-agent",
            description="A test agent",
            prompt="You are a test agent."
        )

        result = adapter.generate_native(config)
        assert result.startswith("---")
        assert "description: A test agent" in result
        assert "globs:" in result
        assert "- **/*" in result  # Default glob pattern
        assert "---\n\nYou are a test agent." in result

    def test_generate_native_with_globs(self):
        """Generate .mdc file content with custom globs."""
        adapter = CursorAdapter()
        config = SubagentConfig(
            name="test-agent",
            description="A test agent",
            prompt="Test prompt"
        )
        # Add custom globs attribute
        config.globs = ["**/*.py", "**/*.ts"]

        result = adapter.generate_native(config)
        assert "description: A test agent" in result
        assert "globs:" in result
        assert "- **/*.py" in result
        assert "- **/*.ts" in result

    def test_generate_native_truncates_long_description(self):
        """Description over 120 chars should be truncated."""
        adapter = CursorAdapter()
        long_desc = "x" * 150  # 150 characters
        config = SubagentConfig(
            name="test-agent",
            description=long_desc,
            prompt="Test prompt"
        )

        result = adapter.generate_native(config)
        # Should be truncated to 117 chars + "..."
        assert "description: " in result
        # Extract the description line
        for line in result.split("\n"):
            if line.startswith("description: "):
                desc_value = line.split("description: ", 1)[1]
                assert len(desc_value) <= 120


class TestWindsurfAdapter:
    """Test WindsurfAdapter for Windsurf AGENTS.md format."""

    def test_adapter_in_registry(self):
        """Windsurf adapter should be registered in environment registry."""
        adapter = get_adapter("windsurf")
        assert isinstance(adapter, WindsurfAdapter)

    def test_supported_environments_includes_windsurf(self):
        """windsurf should be in supported environments list."""
        envs = get_supported_environments()
        assert "windsurf" in envs

    def test_get_target_path(self):
        """Target path should be AGENTS.md in project root."""
        adapter = WindsurfAdapter()
        project_root = Path("/test/project")
        target = adapter.get_target_path(project_root)
        assert target == project_root / "AGENTS.md"

    def test_generate_filename(self):
        """Filename should always be AGENTS.md."""
        adapter = WindsurfAdapter()
        config = SubagentConfig(
            name="test-agent",
            description="A test agent",
            prompt="Test prompt"
        )
        filename = adapter.generate_filename(config)
        assert filename == "AGENTS.md"

    def test_generate_native_minimal(self):
        """Generate plain markdown AGENTS.md content."""
        adapter = WindsurfAdapter()
        config = SubagentConfig(
            name="test-agent",
            description="A test agent",
            prompt="You are a test agent."
        )

        result = adapter.generate_native(config)
        # Should have NO frontmatter (no "---")
        assert not result.startswith("---")
        assert "# A test agent" in result
        assert "You are a test agent." in result

    def test_generate_native_no_description(self):
        """Generate AGENTS.md without description header."""
        adapter = WindsurfAdapter()
        config = SubagentConfig(
            name="test-agent",
            description="",
            prompt="Just the prompt."
        )

        result = adapter.generate_native(config)
        # Should just be the prompt, no header
        assert result.strip() == "Just the prompt."

    def test_map_tools_passthrough(self):
        """Windsurf should pass tools through unchanged."""
        adapter = WindsurfAdapter()
        tools = ["Read", "Write", "Edit", "Bash"]
        result = adapter.map_tools(tools)
        assert result == tools  # No modification

    def test_map_tools_none(self):
        """None tools should return None."""
        adapter = WindsurfAdapter()
        result = adapter.map_tools(None)
        assert result is None


class TestEnvironmentRegistry:
    """Test environment registry functionality."""

    def test_all_expected_environments(self):
        """All expected environments should be registered."""
        envs = get_supported_environments()
        expected = {"claude", "opencode", "copilot", "cursor", "windsurf"}
        assert set(envs) == expected

    def test_get_adapter_raises_on_invalid(self):
        """get_adapter should raise ValueError for invalid environment."""
        with pytest.raises(ValueError, match="Unsupported environment"):
            get_adapter("nonexistent")

    def test_cursor_and_windsurf_in_adapters(self):
        """Cursor and Windsorf adapters should be importable."""
        from dot_work.subagents.environments import (  # noqa: F401
            CursorAdapter,
            WindsurfAdapter,
        )
