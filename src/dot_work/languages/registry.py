"""Language adapter registry and auto-detection.

This module provides a central registry for language adapters and
functionality to automatically detect the appropriate adapter for a project.
"""

from pathlib import Path

from dot_work.languages.base import LanguageAdapter
from dot_work.languages.dotnet import DotNetAdapter
from dot_work.languages.python import PythonAdapter
from dot_work.languages.typescript import TypeScriptAdapter


class LanguageRegistry:
    """Registry for language adapters.

    Maintains a collection of available language adapters and provides
    methods to register new adapters and detect the appropriate adapter
    for a given project.
    """

    def __init__(self) -> None:
        """Initialize the registry with default adapters."""
        self._adapters: list[LanguageAdapter] = []
        self._register_default_adapters()

    def _register_default_adapters(self) -> None:
        """Register the default set of language adapters."""
        self.register(PythonAdapter())
        self.register(DotNetAdapter())
        self.register(TypeScriptAdapter())

    def register(self, adapter: LanguageAdapter) -> None:
        """Register a new language adapter.

        Args:
            adapter: The language adapter to register.
        """
        self._adapters.append(adapter)

    def detect(self, project_path: Path) -> LanguageAdapter | None:
        """Detect the appropriate language adapter for a project.

        Checks each registered adapter to see if it can handle the project.
        Returns the first adapter that claims to handle the project.

        Args:
            project_path: Path to the project directory.

        Returns:
            The first adapter that can handle the project, or None if no
            adapter is found.
        """
        for adapter in self._adapters:
            if adapter.can_handle(project_path):
                return adapter
        return None

    def get_all_adapters(self) -> list[LanguageAdapter]:
        """Get all registered adapters.

        Returns:
            List of all registered language adapters.
        """
        return self._adapters.copy()


# Global registry instance
_global_registry: LanguageRegistry | None = None


def get_global_registry() -> LanguageRegistry:
    """Get the global language registry instance.

    Creates the registry on first call.

    Returns:
        The global LanguageRegistry instance.
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = LanguageRegistry()
    return _global_registry


def detect_language(project_path: Path) -> LanguageAdapter | None:
    """Detect the appropriate language adapter for a project.

    Convenience function that uses the global registry.

    Args:
        project_path: Path to the project directory.

    Returns:
        The first adapter that can handle the project, or None if no
        adapter is found.
    """
    return get_global_registry().detect(project_path)
