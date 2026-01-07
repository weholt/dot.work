"""Tests for the base language adapter module."""

import pytest

from dot_work.languages.base import BuildResult, LanguageAdapter, TestResult


class DummyAdapter(LanguageAdapter):
    """Dummy adapter for testing."""

    def can_handle(self, project_path):  # type: ignore[override]
        return True

    def get_build_command(self, project_path):  # type: ignore[override]
        return ["echo", "build"]

    def get_test_command(self, project_path):  # type: ignore[override]
        return ["echo", "test"]

    def get_lint_command(self, project_path):  # type: ignore[override]
        return ["echo", "lint"]

    def get_type_check_command(self, project_path):  # type: ignore[override]
        return ["echo", "typecheck"]

    def get_format_command(self, project_path):  # type: ignore[override]
        return ["echo", "format"]

    def parse_build_result(self, exit_code, stdout, stderr, duration_seconds):  # type: ignore[override]
        return BuildResult(
            success=exit_code == 0,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration_seconds,
        )

    def parse_test_result(self, exit_code, stdout, stderr, duration_seconds):  # type: ignore[override]
        return TestResult(
            success=exit_code == 0,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration_seconds,
        )


class TestBuildResult:
    """Tests for BuildResult dataclass."""

    def test_build_result_creation(self):
        """Test creating a BuildResult."""
        result = BuildResult(
            success=True,
            exit_code=0,
            stdout="build output",
            stderr="build errors",
            duration_seconds=1.5,
        )

        assert result.success is True
        assert result.exit_code == 0
        assert result.stdout == "build output"
        assert result.stderr == "build errors"
        assert result.duration_seconds == 1.5


class TestTestResult:
    """Tests for TestResult dataclass."""

    def test_test_result_creation_with_all_fields(self):
        """Test creating a TestResult with all fields."""
        result = TestResult(
            success=True,
            exit_code=0,
            stdout="test output",
            stderr="test errors",
            duration_seconds=2.5,
            tests_run=100,
            tests_failed=0,
            tests_skipped=5,
        )

        assert result.success is True
        assert result.exit_code == 0
        assert result.stdout == "test output"
        assert result.tests_run == 100
        assert result.tests_failed == 0
        assert result.tests_skipped == 5

    def test_test_result_creation_without_counts(self):
        """Test creating a TestResult without test counts."""
        result = TestResult(
            success=True,
            exit_code=0,
            stdout="test output",
            stderr="",
            duration_seconds=1.0,
        )

        assert result.success is True
        assert result.tests_run is None
        assert result.tests_failed is None
        assert result.tests_skipped is None


class TestLanguageAdapter:
    """Tests for LanguageAdapter ABC."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that LanguageAdapter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LanguageAdapter()  # type: ignore[abstract]

    def test_dummy_adapter_implements_interface(self):
        """Test that a concrete adapter implements all required methods."""
        adapter = DummyAdapter()

        from pathlib import Path
        project_path = Path("/tmp/test")

        # Can handle
        assert adapter.can_handle(project_path) is True

        # Commands
        assert adapter.get_build_command(project_path) == ["echo", "build"]
        assert adapter.get_test_command(project_path) == ["echo", "test"]
        assert adapter.get_lint_command(project_path) == ["echo", "lint"]
        assert adapter.get_type_check_command(project_path) == ["echo", "typecheck"]
        assert adapter.get_format_command(project_path) == ["echo", "format"]

        # Default format fix command is empty
        assert adapter.get_format_fix_command(project_path) == []

        # Parse results
        build_result = adapter.parse_build_result(0, "out", "err", 1.0)
        assert build_result.success is True

        test_result = adapter.parse_test_result(0, "out", "err", 1.0)
        assert test_result.success is True
