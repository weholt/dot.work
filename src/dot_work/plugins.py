"""Plugin discovery and registration for dot-work.

This module provides the plugin system that allows external packages to register
their CLI commands with the main dot-work application via Python entry points.

Example:
    For a plugin to register itself, it should define an entry point in pyproject.toml:

    [project.entry-points."dot_work.plugins"]
    myplugin = "my_package"

    And in my_package/__init__.py:
        CLI_GROUP = "my-command"
        app = typer.Typer()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import typer

logger = logging.getLogger(__name__)

# Entry point group for dot-work plugins
PLUGIN_ENTRY_POINT = "dot_work.plugins"


@dataclass(frozen=True)
class DotWorkPlugin:
    """Metadata about a discovered dot-work plugin.

    Attributes:
        name: The plugin name (entry point name)
        module: The Python module path (e.g., "my_package")
        cli_group: The CLI command group (e.g., "db-issues") if defined
        version: Plugin version string if available
    """

    name: str
    module: str
    cli_group: str | None
    version: str | None = None


def discover_plugins() -> list[DotWorkPlugin]:
    """Discover all installed dot-work plugins via entry points.

    Returns:
        A list of DotWorkPlugin instances for all discovered plugins.
        Returns an empty list if no plugins are installed.

    Examples:
        >>> plugins = discover_plugins()
        >>> len(plugins)
        3
        >>> plugins[0].name
        'issues'
    """
    plugins: list[DotWorkPlugin] = []

    try:
        eps = entry_points(group=PLUGIN_ENTRY_POINT)
    except TypeError:
        # Python < 3.10 compatibility: entry_points() doesn't accept group parameter
        try:
            eps_data = entry_points()
            eps = eps_data.select(group=PLUGIN_ENTRY_POINT) if hasattr(eps_data, "select") else []  # type: ignore[assignment]
        except Exception as e:
            logger.warning("Failed to discover plugins: %s", e)
            return []

    for ep in eps:
        try:
            module_path = str(ep.value)

            # Try to import the module to get metadata
            cli_group: str | None = None
            version: str | None = None

            try:
                module = __import__(module_path, fromlist=[""])
                cli_group = getattr(module, "CLI_GROUP", None)
                version = getattr(module, "__version__", None)
            except ImportError as import_error:
                logger.warning(
                    "Plugin '%s' module '%s' not importable: %s",
                    ep.name,
                    module_path,
                    import_error,
                )
                continue
            except Exception as e:
                logger.warning(
                    "Plugin '%s' metadata loading failed: %s",
                    ep.name,
                    e,
                )
                # Continue anyway - we'll create plugin without metadata

            plugins.append(
                DotWorkPlugin(
                    name=ep.name,
                    module=module_path,
                    cli_group=cli_group,
                    version=version,
                )
            )
            logger.debug("Discovered plugin: %s (%s)", ep.name, module_path)

        except Exception as e:
            logger.warning("Failed to load plugin entry point '%s': %s", ep.name, e)
            continue

    return plugins


def register_plugin_cli(app: typer.Typer, plugin: DotWorkPlugin) -> bool:
    """Register a plugin's CLI with the main typer application.

    Args:
        app: The main typer.Typer application instance.
        plugin: The DotWorkPlugin metadata.

    Returns:
        True if the plugin was registered successfully, False otherwise.

    Examples:
        >>> import typer
        >>> app = typer.Typer()
        >>> plugin = DotWorkPlugin(name="test", module="test_pkg", cli_group="test")
        >>> register_plugin_cli(app, plugin)
        True
    """
    try:
        module = __import__(plugin.module, fromlist=[""])
        plugin_app = getattr(module, "app", None)

        if plugin_app is None:
            logger.warning(
                "Plugin '%s' has no 'app' attribute (Typer instance)",
                plugin.name,
            )
            return False

        # Use cli_group if defined, otherwise use entry point name
        command_name = plugin.cli_group if plugin.cli_group else plugin.name

        app.add_typer(plugin_app, name=command_name)
        logger.info("Registered plugin '%s' as command '%s'", plugin.name, command_name)
        return True

    except ImportError as e:
        logger.warning(
            "Failed to import plugin '%s' module '%s': %s",
            plugin.name,
            plugin.module,
            e,
        )
        return False
    except AttributeError as e:
        logger.warning(
            "Plugin '%s' missing required attribute: %s",
            plugin.name,
            e,
        )
        return False
    except Exception as e:
        logger.warning(
            "Failed to register plugin '%s': %s",
            plugin.name,
            e,
        )
        return False


def register_all_plugins(app: typer.Typer) -> int:
    """Discover and register all installed plugins.

    This is a convenience function that combines discover_plugins() and
    register_plugin_cli() for typical usage.

    Args:
        app: The main typer.Typer application instance.

    Returns:
        The number of plugins successfully registered.

    Examples:
        >>> import typer
        >>> app = typer.Typer()
        >>> count = register_all_plugins(app)
        >>> print(f"Registered {count} plugins")
        Registered 3 plugins
    """
    plugins = discover_plugins()
    registered = 0

    for plugin in plugins:
        if register_plugin_cli(app, plugin):
            registered += 1

    if registered > 0:
        logger.info("Registered %d plugin(s)", registered)
    else:
        logger.debug("No plugins registered")

    return registered
