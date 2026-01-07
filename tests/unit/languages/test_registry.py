"""Tests for the language adapter registry."""

import pytest
from pathlib import Path

from dot_work.languages.registry import LanguageRegistry, detect_language, get_global_registry


class MockAdapter:
    """Mock adapter for testing."""

    def __init__(self, can_handle_value=False):
        self.can_handle_value = can_handle_value

    def can_handle(self, project_path):  # type: ignore[override]
        return self.can_handle_value


class TestLanguageRegistry:
    """Tests for LanguageRegistry class."""

    def test_register_adapter(self):
        """Test registering an adapter."""
        registry = LanguageRegistry()
        adapter = MockAdapter()

        initial_count = len(registry.get_all_adapters())
        registry.register(adapter)

        assert len(registry.get_all_adapters()) == initial_count + 1
        assert adapter in registry.get_all_adapters()

    def test_detect_returns_matching_adapter(self):
        """Test detect returns the first adapter that can handle the project."""
        registry = LanguageRegistry()
        adapter1 = MockAdapter(can_handle_value=False)
        adapter2 = MockAdapter(can_handle_value=True)
        adapter3 = MockAdapter(can_handle_value=True)

        registry.register(adapter1)
        registry.register(adapter2)
        registry.register(adapter3)

        project_path = Path("/tmp/test")
        result = registry.detect(project_path)

        assert result is adapter2

    def test_detect_returns_none_when_no_match(self):
        """Test detect returns None when no adapter can handle the project."""
        registry = LanguageRegistry()
        adapter = MockAdapter(can_handle_value=False)

        registry.register(adapter)

        project_path = Path("/tmp/test")
        result = registry.detect(project_path)

        assert result is None

    def test_default_adapters_registered(self):
        """Test that default adapters are registered on init."""
        registry = LanguageRegistry()

        # Should have at least the Python adapter
        adapters = registry.get_all_adapters()
        assert len(adapters) >= 1

        # Check for Python adapter by class name
        from dot_work.languages.python import PythonAdapter
        has_python = any(isinstance(a, PythonAdapter) for a in adapters)
        assert has_python


class TestGlobalRegistry:
    """Tests for the global registry singleton."""

    def test_get_global_registry_returns_instance(self):
        """Test that get_global_registry returns a registry instance."""
        registry = get_global_registry()

        assert isinstance(registry, LanguageRegistry)

    def test_get_global_registry_returns_same_instance(self):
        """Test that get_global_registry returns the same instance each time."""
        registry1 = get_global_registry()
        registry2 = get_global_registry()

        assert registry1 is registry2


class TestDetectLanguage:
    """Tests for the detect_language convenience function."""

    def test_detect_language_returns_adapter(self):
        """Test that detect_language returns an adapter for Python projects."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "pyproject.toml").touch()

            adapter = detect_language(project_path)

            assert adapter is not None
            from dot_work.languages.python import PythonAdapter
            assert isinstance(adapter, PythonAdapter)

    def test_detect_language_returns_none_for_unknown(self):
        """Test that detect_language returns None for unknown projects."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            # No language markers

            adapter = detect_language(project_path)

            assert adapter is None
