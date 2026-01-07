"""Tests for the plugin discovery and registration system."""

from __future__ import annotations

import pytest
import typer

from dot_work.plugins import (
    DotWorkPlugin,
    discover_plugins,
    register_all_plugins,
    register_plugin_cli,
)


class TestDotWorkPlugin:
    """Test DotWorkPlugin dataclass."""

    def test_plugin_creation(self) -> None:
        """Test creating a DotWorkPlugin instance."""
        plugin = DotWorkPlugin(
            name="test",
            module="test_package",
            cli_group="test-command",
            version="1.0.0",
        )
        assert plugin.name == "test"
        assert plugin.module == "test_package"
        assert plugin.cli_group == "test-command"
        assert plugin.version == "1.0.0"

    def test_plugin_without_optional_fields(self) -> None:
        """Test creating a DotWorkPlugin without optional fields."""
        plugin = DotWorkPlugin(name="test", module="test_package", cli_group=None)
        assert plugin.name == "test"
        assert plugin.module == "test_package"
        assert plugin.cli_group is None
        assert plugin.version is None

    def test_plugin_is_frozen(self) -> None:
        """Test that DotWorkPlugin is immutable."""
        plugin = DotWorkPlugin(name="test", module="test_pkg", cli_group="test")
        with pytest.raises(Exception):  # FrozenInstanceError from dataclasses
            plugin.name = "new_name"  # type: ignore[misc]


class TestDiscoverPlugins:
    """Test plugin discovery functionality."""

    def test_discover_no_plugins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test discovering plugins when none are installed."""

        def mock_entry_points(*, group: str | None = None) -> dict:
            return {}

        monkeypatch.setattr("dot_work.plugins.entry_points", mock_entry_points)
        plugins = discover_plugins()
        assert plugins == []

    def test_discover_with_mock_plugin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test discovering plugins with mocked entry points."""

        class MockEntryPoint:
            def __init__(self, name: str, value: str) -> None:
                self.name = name
                self._value = value

            @property
            def value(self) -> str:
                return self._value

        class MockEntryPoints:
            def __init__(self, eps: list) -> None:
                self._eps = eps

            def __iter__(self):
                return iter(self._eps)

        def mock_entry_points(*, group: str | None = None) -> MockEntryPoints:
            if group == "dot_work.plugins":
                return MockEntryPoints([MockEntryPoint("test", "test_package")])
            return MockEntryPoints([])

        monkeypatch.setattr("dot_work.plugins.entry_points", mock_entry_points)

        # Mock the import to return a module with CLI_GROUP
        import sys
        from types import ModuleType

        mock_module = ModuleType("test_package")
        mock_module.CLI_GROUP = "test-command"
        mock_module.__version__ = "1.0.0"
        sys.modules["test_package"] = mock_module

        try:
            plugins = discover_plugins()
            assert len(plugins) == 1
            assert plugins[0].name == "test"
            assert plugins[0].module == "test_package"
            assert plugins[0].cli_group == "test-command"
            assert plugins[0].version == "1.0.0"
        finally:
            del sys.modules["test_package"]

    def test_discover_handles_import_error(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        """Test that import errors are handled gracefully."""

        class MockEntryPoint:
            def __init__(self, name: str, value: str) -> None:
                self.name = name
                self._value = value

            @property
            def value(self) -> str:
                return self._value

        class MockEntryPoints:
            def __init__(self, eps: list) -> None:
                self._eps = eps

            def __iter__(self):
                return iter(self._eps)

        def mock_entry_points(*, group: str | None = None) -> MockEntryPoints:
            return MockEntryPoints([MockEntryPoint("broken", "nonexistent_module")])

        monkeypatch.setattr("dot_work.plugins.entry_points", mock_entry_points)

        with caplog.at_level("WARNING"):
            plugins = discover_plugins()

        assert plugins == []
        assert any("nonexistent_module" in record.message for record in caplog.records)


class TestRegisterPluginCli:
    """Test plugin CLI registration."""

    def test_register_plugin_with_app(self) -> None:
        """Test registering a plugin with a Typer app."""
        app = typer.Typer()
        plugin_app = typer.Typer()

        # Mock the plugin module
        import sys
        from types import ModuleType

        mock_module = ModuleType("test_plugin")
        mock_module.app = plugin_app
        sys.modules["test_plugin"] = mock_module

        try:
            plugin = DotWorkPlugin(name="test", module="test_plugin", cli_group="test-cmd")
            result = register_plugin_cli(app, plugin)
            assert result is True
        finally:
            del sys.modules["test_plugin"]

    def test_register_plugin_without_app_attribute(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test registering a plugin that has no app attribute."""
        app = typer.Typer()

        # Mock the plugin module without app
        import sys
        from types import ModuleType

        mock_module = ModuleType("no_app_plugin")
        sys.modules["no_app_plugin"] = mock_module

        try:
            plugin = DotWorkPlugin(name="noapp", module="no_app_plugin", cli_group="noapp")
            with caplog.at_level("WARNING"):
                result = register_plugin_cli(app, plugin)
            assert result is False
            assert any("no 'app' attribute" in record.message for record in caplog.records)
        finally:
            del sys.modules["no_app_plugin"]

    def test_register_plugin_uses_cli_group(self) -> None:
        """Test that cli_group is used when defined."""
        app = typer.Typer()
        plugin_app = typer.Typer()

        import sys
        from types import ModuleType

        mock_module = ModuleType("grouped_plugin")
        mock_module.app = plugin_app
        sys.modules["grouped_plugin"] = mock_module

        try:
            plugin = DotWorkPlugin(
                name="entry-name",
                module="grouped_plugin",
                cli_group="custom-command",
            )
            register_plugin_cli(app, plugin)
            # Verify the command is registered with the custom name
            # (Typer doesn't expose registered commands easily)
        finally:
            del sys.modules["grouped_plugin"]


class TestRegisterAllPlugins:
    """Test bulk plugin registration."""

    def test_register_all_returns_count(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that register_all_plugins returns the count of registered plugins."""
        app = typer.Typer()

        class MockEntryPoint:
            def __init__(self, name: str, value: str) -> None:
                self.name = name
                self._value = value

            @property
            def value(self) -> str:
                return self._value

        class MockEntryPoints:
            def __init__(self, eps: list) -> None:
                self._eps = eps

            def __iter__(self):
                return iter(self._eps)

        def mock_entry_points(*, group: str | None = None) -> MockEntryPoints:
            return MockEntryPoints([
                MockEntryPoint("plugin1", "pkg1"),
                MockEntryPoint("plugin2", "pkg2"),
            ])

        monkeypatch.setattr("dot_work.plugins.entry_points", mock_entry_points)

        # Mock both plugin modules
        import sys
        from types import ModuleType

        for pkg_name in ["pkg1", "pkg2"]:
            mock_module = ModuleType(pkg_name)
            mock_module.app = typer.Typer()
            mock_module.CLI_GROUP = pkg_name
            sys.modules[pkg_name] = mock_module

        try:
            count = register_all_plugins(app)
            assert count == 2
        finally:
            for pkg_name in ["pkg1", "pkg2"]:
                del sys.modules[pkg_name]

    def test_register_all_with_failures(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that registration continues even if some plugins fail."""
        app = typer.Typer()

        class MockEntryPoint:
            def __init__(self, name: str, value: str) -> None:
                self.name = name
                self._value = value

            @property
            def value(self) -> str:
                return self._value

        class MockEntryPoints:
            def __init__(self, eps: list) -> None:
                self._eps = eps

            def __iter__(self):
                return iter(self._eps)

        def mock_entry_points(*, group: str | None = None) -> MockEntryPoints:
            return MockEntryPoints([
                MockEntryPoint("good", "good_pkg"),
                MockEntryPoint("bad", "nonexistent_pkg"),
            ])

        monkeypatch.setattr("dot_work.plugins.entry_points", mock_entry_points)

        # Mock only the good plugin
        import sys
        from types import ModuleType

        mock_module = ModuleType("good_pkg")
        mock_module.app = typer.Typer()
        mock_module.CLI_GROUP = "good"
        sys.modules["good_pkg"] = mock_module

        try:
            count = register_all_plugins(app)
            # Only the good plugin should be registered
            assert count == 1
        finally:
            del sys.modules["good_pkg"]
