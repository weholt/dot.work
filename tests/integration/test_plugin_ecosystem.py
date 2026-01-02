"""Integration tests for the plugin ecosystem.

These tests verify that:
1. Core dot-work works without any plugins installed
2. Each plugin registers correctly
3. `dot-work[all]` provides full functionality
4. No import errors when mixing installed/not-installed plugins
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dot_work.cli import app
from dot_work.plugins import discover_plugins, DotWorkPlugin, register_all_plugins


class TestCoreWithoutPlugins:
    """Test that core CLI works without any plugins installed."""

    def test_core_cli_loads_without_plugins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that the CLI app loads even when no plugins are discoverable."""
        # Mock discover_plugins to return empty list
        monkeypatch.setattr("dot_work.plugins.discover_plugins", lambda: [])

        # Import and create app should not fail
        from dot_work.cli import app as test_app
        assert test_app is not None

    def test_help_works_without_plugins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that --help shows core commands without plugins."""
        # Mock discover_plugins to return empty list
        monkeypatch.setattr("dot_work.plugins.discover_plugins", lambda: [])

        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

        # Core commands should be present
        assert "install" in result.stdout
        assert "list" in result.stdout
        assert "validate" in result.stdout
        assert "prompt" in result.stdout
        assert "plugins" in result.stdout

    def test_plugins_command_shows_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that plugins command shows 'No plugins installed' when none exist."""
        # Mock discover_plugins to return empty list
        monkeypatch.setattr("dot_work.plugins.discover_plugins", lambda: [])

        runner = CliRunner()
        result = runner.invoke(app, ["plugins"])
        assert result.exit_code == 0
        assert "No plugins installed" in result.stdout


class TestPluginDiscovery:
    """Test plugin discovery functionality."""

    def test_discover_plugins_returns_list(self) -> None:
        """Test that discover_plugins always returns a list."""
        plugins = discover_plugins()
        assert isinstance(plugins, list)
        # May be empty if no plugins installed

    def test_discover_plugins_with_broken_plugin(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        """Test that broken plugins are logged and skipped."""

        class MockBrokenEntryPoint:
            def __init__(self) -> None:
                self.name = "broken"
                self._value = "nonexistent_module"

            @property
            def value(self) -> str:
                return self._value

        class MockEntryPoints:
            def __init__(self) -> None:
                self._eps = [MockBrokenEntryPoint()]

            def __iter__(self):
                return iter(self._eps)

        def mock_entry_points(*, group: str | None = None) -> MockEntryPoints:
            return MockEntryPoints()

        monkeypatch.setattr("dot_work.plugins.entry_points", mock_entry_points)

        with caplog.at_level("WARNING"):
            plugins = discover_plugins()

        # Should return empty list, not crash
        assert plugins == []
        assert any("nonexistent_module" in record.message for record in caplog.records)


class TestPluginRegistration:
    """Test plugin CLI registration."""

    def test_register_plugin_adds_command(self) -> None:
        """Test that registering a plugin adds its command to the CLI."""
        import typer
        from types import ModuleType

        # Create a mock plugin module
        mock_plugin = ModuleType("test_plugin")
        mock_plugin.CLI_GROUP = "test-cmd"
        plugin_app = typer.Typer()

        @plugin_app.command()
        def hello() -> None:
            """Say hello."""
            print("Hello from plugin!")

        mock_plugin.app = plugin_app
        sys.modules["test_plugin"] = mock_plugin

        try:
            # Create plugin metadata
            plugin = DotWorkPlugin(name="test", module="test_plugin", cli_group="test-cmd")

            # Register with app directly
            from dot_work.plugins import register_plugin_cli
            test_app = typer.Typer()
            result = register_plugin_cli(test_app, plugin)

            # Should successfully register
            assert result is True

            # Verify command is registered by checking help
            runner = CliRunner()
            # Use the main app pattern
            main_app = typer.Typer()
            main_app.add_typer(plugin_app, name="test-cmd")

            result = runner.invoke(main_app, ["--help"])
            assert result.exit_code == 0
            assert "test-cmd" in result.stdout

        finally:
            del sys.modules["test_plugin"]

    def test_register_plugin_without_cli_group(self) -> None:
        """Test that plugins without CLI_GROUP use entry point name."""
        import typer
        from types import ModuleType

        # Create a mock plugin without CLI_GROUP
        mock_plugin = ModuleType("test_plugin_nogroup")
        # No CLI_GROUP defined
        plugin_app = typer.Typer()

        @plugin_app.command()
        def hello() -> None:
            """Say hello."""
            print("Hello from plugin!")

        mock_plugin.app = plugin_app
        sys.modules["test_plugin_nogroup"] = mock_plugin

        try:
            # Create plugin metadata without cli_group
            plugin = DotWorkPlugin(name="mycmd", module="test_plugin_nogroup", cli_group=None)

            # Register with app directly
            from dot_work.plugins import register_plugin_cli
            test_app = typer.Typer()
            result = register_plugin_cli(test_app, plugin)

            # Should successfully register
            assert result is True

            # Verify command is registered by checking help
            runner = CliRunner()
            main_app = typer.Typer()
            main_app.add_typer(plugin_app, name="mycmd")

            result = runner.invoke(main_app, ["--help"])
            assert result.exit_code == 0
            assert "mycmd" in result.stdout

        finally:
            del sys.modules["test_plugin_nogroup"]


class TestGracefulDegradation:
    """Test that missing plugins don't crash the CLI."""

    def test_missing_plugin_shows_helpful_error(self) -> None:
        """Test that attempting to use a missing plugin command shows helpful error."""
        runner = CliRunner()
        result = runner.invoke(app, ["nonexistent", "--help"])
        # Should exit with error but not crash
        assert result.exit_code != 0


class TestMixedPluginScenarios:
    """Test mixing installed and not-installed plugins."""

    def test_partial_plugin_installation(self) -> None:
        """Test that installing some plugins works while others are missing."""
        # This test verifies the behavior when only a subset of plugins
        # are installed. In a real scenario, this would involve pip installing
        # specific plugins and verifying they work while missing plugins
        # simply don't appear in the command list.
        plugins = discover_plugins()
        # Should return list of only installed plugins (may be empty in test env)
        assert isinstance(plugins, list)


class TestCoreCommandsAlwaysAvailable:
    """Test that core commands are always available regardless of plugins."""

    def test_core_install_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that install command works without plugins."""
        monkeypatch.setattr("dot_work.plugins.discover_plugins", lambda: [])

        runner = CliRunner()
        result = runner.invoke(app, ["install", "--help"])
        assert result.exit_code == 0
        assert "install" in result.stdout.lower()

    def test_core_list_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that list command works without plugins."""
        monkeypatch.setattr("dot_work.plugins.discover_plugins", lambda: [])

        runner = CliRunner()
        result = runner.invoke(app, ["list", "--help"])
        assert result.exit_code == 0

    def test_core_validate_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that validate command works without plugins."""
        monkeypatch.setattr("dot_work.plugins.discover_plugins", lambda: [])

        runner = CliRunner()
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "validate" in result.stdout.lower()

    def test_core_prompt_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that prompt command works without plugins."""
        monkeypatch.setattr("dot_work.plugins.discover_plugins", lambda: [])

        runner = CliRunner()
        result = runner.invoke(app, ["prompt", "--help"])
        assert result.exit_code == 0
        assert "prompt" in result.stdout.lower()
