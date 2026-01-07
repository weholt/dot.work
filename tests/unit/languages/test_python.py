"""Tests for the Python language adapter."""

import pytest
from pathlib import Path

from dot_work.languages.python import PythonAdapter


@pytest.fixture
def python_adapter():
    """Fixture providing a PythonAdapter instance."""
    return PythonAdapter()


@pytest.fixture
def temp_project_dir(tmp_path):
    """Fixture providing a temporary project directory."""
    return tmp_path


class TestPythonAdapterCanHandle:
    """Tests for PythonAdapter.can_handle()."""

    def test_detects_pyproject_toml(self, python_adapter, temp_project_dir):
        """Test detection via pyproject.toml."""
        (temp_project_dir / "pyproject.toml").touch()
        assert python_adapter.can_handle(temp_project_dir) is True

    def test_detects_setup_py(self, python_adapter, temp_project_dir):
        """Test detection via setup.py."""
        (temp_project_dir / "setup.py").touch()
        assert python_adapter.can_handle(temp_project_dir) is True

    def test_detects_setup_cfg(self, python_adapter, temp_project_dir):
        """Test detection via setup.cfg."""
        (temp_project_dir / "setup.cfg").touch()
        assert python_adapter.can_handle(temp_project_dir) is True

    def test_detects_requirements_txt(self, python_adapter, temp_project_dir):
        """Test detection via requirements.txt."""
        (temp_project_dir / "requirements.txt").touch()
        assert python_adapter.can_handle(temp_project_dir) is True

    def test_detects_pipfile(self, python_adapter, temp_project_dir):
        """Test detection via Pipfile."""
        (temp_project_dir / "Pipfile").touch()
        assert python_adapter.can_handle(temp_project_dir) is True

    def test_detects_poetry_lock(self, python_adapter, temp_project_dir):
        """Test detection via poetry.lock."""
        (temp_project_dir / "poetry.lock").touch()
        assert python_adapter.can_handle(temp_project_dir) is True

    def test_rejects_non_python_project(self, python_adapter, temp_project_dir):
        """Test rejection of project without Python markers."""
        assert python_adapter.can_handle(temp_project_dir) is False


class TestPythonAdapterCommands:
    """Tests for PythonAdapter command methods."""

    def test_get_build_command_with_script(self, python_adapter, temp_project_dir):
        """Test build command when build.py exists."""
        scripts_dir = temp_project_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "build.py").touch()

        cmd = python_adapter.get_build_command(temp_project_dir)
        assert cmd == ["uv", "run", "python", str(scripts_dir / "build.py")]

    def test_get_build_command_without_script(self, python_adapter, temp_project_dir):
        """Test build command when build.py doesn't exist."""
        cmd = python_adapter.get_build_command(temp_project_dir)
        assert cmd == ["uv", "run", "python", "-m", "build"]

    def test_get_test_command(self, python_adapter, temp_project_dir):
        """Test test command."""
        cmd = python_adapter.get_test_command(temp_project_dir)
        assert cmd == ["uv", "run", "pytest", "tests/"]

    def test_get_lint_command(self, python_adapter, temp_project_dir):
        """Test lint command."""
        cmd = python_adapter.get_lint_command(temp_project_dir)
        assert cmd == ["uv", "run", "ruff", "check", "."]

    def test_get_type_check_command(self, python_adapter, temp_project_dir):
        """Test type check command."""
        cmd = python_adapter.get_type_check_command(temp_project_dir)
        assert cmd == ["uv", "run", "mypy", "src/"]

    def test_get_format_command(self, python_adapter, temp_project_dir):
        """Test format check command."""
        cmd = python_adapter.get_format_command(temp_project_dir)
        assert cmd == ["uv", "run", "ruff", "format", "--check", "."]

    def test_get_format_fix_command(self, python_adapter, temp_project_dir):
        """Test format fix command."""
        cmd = python_adapter.get_format_fix_command(temp_project_dir)
        assert cmd == ["uv", "run", "ruff", "format", "."]


class TestPythonAdapterParseBuildResult:
    """Tests for PythonAdapter.parse_build_result()."""

    def test_parse_success(self, python_adapter):
        """Test parsing a successful build."""
        result = python_adapter.parse_build_result(0, "out", "err", 1.5)

        assert result.success is True
        assert result.exit_code == 0
        assert result.stdout == "out"
        assert result.stderr == "err"
        assert result.duration_seconds == 1.5

    def test_parse_failure(self, python_adapter):
        """Test parsing a failed build."""
        result = python_adapter.parse_build_result(1, "out", "err", 2.5)

        assert result.success is False
        assert result.exit_code == 1


class TestPythonAdapterParseTestResult:
    """Tests for PythonAdapter.parse_test_result()."""

    def test_parse_success_with_counts(self, python_adapter):
        """Test parsing successful test output with counts."""
        stdout = "=== 10 passed in 2.5s ==="
        result = python_adapter.parse_test_result(0, stdout, "", 2.5)

        assert result.success is True
        assert result.exit_code == 0
        assert result.tests_run == 10
        assert result.tests_failed is None
        assert result.tests_skipped is None

    def test_parse_failure_with_counts(self, python_adapter):
        """Test parsing failed test output with counts."""
        stdout = "=== 8 passed, 2 failed in 3.0s ==="
        result = python_adapter.parse_test_result(1, stdout, "", 3.0)

        assert result.success is False
        assert result.tests_run == 8
        assert result.tests_failed == 2

    def test_parse_with_skipped(self, python_adapter):
        """Test parsing test output with skipped tests."""
        stdout = "=== 5 passed, 1 failed, 2 skipped in 2.0s ==="
        result = python_adapter.parse_test_result(0, stdout, "", 2.0)

        assert result.success is True
        assert result.tests_run == 5
        assert result.tests_failed == 1
        assert result.tests_skipped == 2

    def test_parse_collected_style(self, python_adapter):
        """Test parsing 'tests collected' style output."""
        stdout = "collected 15 items\n=== 15 passed in 2.0s ==="
        result = python_adapter.parse_test_result(0, stdout, "", 2.0)

        assert result.success is True
        assert result.tests_run == 15

    def test_parse_no_counts(self, python_adapter):
        """Test parsing output without test counts."""
        stdout = "tests completed"
        result = python_adapter.parse_test_result(0, stdout, "", 1.0)

        assert result.success is True
        assert result.tests_run is None
        assert result.tests_failed is None
        assert result.tests_skipped is None
