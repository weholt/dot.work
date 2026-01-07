"""Tests for the .NET language adapter."""

import pytest
from pathlib import Path

from dot_work.languages.dotnet import DotNetAdapter


@pytest.fixture
def dotnet_adapter():
    """Fixture providing a DotNetAdapter instance."""
    return DotNetAdapter()


@pytest.fixture
def temp_project_dir(tmp_path):
    """Fixture providing a temporary project directory."""
    return tmp_path


class TestDotNetAdapterCanHandle:
    """Tests for DotNetAdapter.can_handle()."""

    def test_detects_sln_file(self, dotnet_adapter, temp_project_dir):
        """Test detection via .sln file."""
        (temp_project_dir / "solution.sln").touch()
        assert dotnet_adapter.can_handle(temp_project_dir) is True

    def test_detects_csproj_file(self, dotnet_adapter, temp_project_dir):
        """Test detection via .csproj file."""
        (temp_project_dir / "project.csproj").touch()
        assert dotnet_adapter.can_handle(temp_project_dir) is True

    def test_detects_fsproj_file(self, dotnet_adapter, temp_project_dir):
        """Test detection via .fsproj file."""
        (temp_project_dir / "project.fsproj").touch()
        assert dotnet_adapter.can_handle(temp_project_dir) is True

    def test_detects_vbproj_file(self, dotnet_adapter, temp_project_dir):
        """Test detection via .vbproj file."""
        (temp_project_dir / "project.vbproj").touch()
        assert dotnet_adapter.can_handle(temp_project_dir) is True

    def test_detects_nested_csproj(self, dotnet_adapter, temp_project_dir):
        """Test detection of nested .csproj file."""
        src_dir = temp_project_dir / "src"
        src_dir.mkdir()
        (src_dir / "project.csproj").touch()
        assert dotnet_adapter.can_handle(temp_project_dir) is True

    def test_rejects_non_dotnet_project(self, dotnet_adapter, temp_project_dir):
        """Test rejection of project without .NET markers."""
        assert dotnet_adapter.can_handle(temp_project_dir) is False


class TestDotNetAdapterCommands:
    """Tests for DotNetAdapter command methods."""

    def test_get_build_command_default(self, dotnet_adapter, temp_project_dir):
        """Test build command without solution file."""
        cmd = dotnet_adapter.get_build_command(temp_project_dir)
        assert cmd == ["dotnet", "build"]

    def test_get_build_command_with_sln(self, dotnet_adapter, temp_project_dir):
        """Test build command when solution file exists."""
        (temp_project_dir / "MySolution.sln").touch()
        cmd = dotnet_adapter.get_build_command(temp_project_dir)
        assert cmd == ["dotnet", "build", str(temp_project_dir / "MySolution.sln")]

    def test_get_test_command(self, dotnet_adapter, temp_project_dir):
        """Test test command."""
        cmd = dotnet_adapter.get_test_command(temp_project_dir)
        assert "dotnet" in cmd
        assert "test" in cmd
        assert "--no-build" in cmd

    def test_get_lint_command(self, dotnet_adapter, temp_project_dir):
        """Test lint command."""
        cmd = dotnet_adapter.get_lint_command(temp_project_dir)
        # For .NET, linting uses the compiler (build)
        assert cmd == dotnet_adapter.get_build_command(temp_project_dir)

    def test_get_type_check_command(self, dotnet_adapter, temp_project_dir):
        """Test type check command."""
        cmd = dotnet_adapter.get_type_check_command(temp_project_dir)
        # For .NET, type checking is done by the compiler (build)
        assert cmd == dotnet_adapter.get_build_command(temp_project_dir)

    def test_get_format_command(self, dotnet_adapter, temp_project_dir):
        """Test format check command."""
        cmd = dotnet_adapter.get_format_command(temp_project_dir)
        assert "dotnet" in cmd
        assert "format" in cmd
        assert "--verify-no-changes" in cmd

    def test_get_format_fix_command(self, dotnet_adapter, temp_project_dir):
        """Test format fix command."""
        cmd = dotnet_adapter.get_format_fix_command(temp_project_dir)
        assert cmd == ["dotnet", "format"]


class TestDotNetAdapterParseBuildResult:
    """Tests for DotNetAdapter.parse_build_result()."""

    def test_parse_success(self, dotnet_adapter):
        """Test parsing a successful build."""
        result = dotnet_adapter.parse_build_result(0, "Build succeeded.", "", 1.5)

        assert result.success is True
        assert result.exit_code == 0
        assert result.duration_seconds == 1.5

    def test_parse_failure(self, dotnet_adapter):
        """Test parsing a failed build."""
        result = dotnet_adapter.parse_build_result(1, "", "Build failed.", 2.5)

        assert result.success is False
        assert result.exit_code == 1

    def test_parse_with_errors(self, dotnet_adapter):
        """Test parsing build with error count."""
        stdout = "Build FAILED. 2 Error(s), 5 Warning(s)"
        result = dotnet_adapter.parse_build_result(1, stdout, "", 1.0)

        assert result.success is False


class TestDotNetAdapterParseTestResult:
    """Tests for DotNetAdapter.parse_test_result()."""

    def test_parse_success_with_passed(self, dotnet_adapter):
        """Test parsing successful test output with Passed count."""
        stdout = "Passed: 10, Failed: 0, Skipped: 0"
        result = dotnet_adapter.parse_test_result(0, stdout, "", 2.5)

        assert result.success is True
        assert result.tests_run == 10
        assert result.tests_failed == 0

    def test_parse_failure_with_counts(self, dotnet_adapter):
        """Test parsing failed test output with counts."""
        stdout = "Passed: 8, Failed: 2, Skipped: 1"
        result = dotnet_adapter.parse_test_result(1, stdout, "", 3.0)

        assert result.success is False
        assert result.tests_run == 11  # 8 + 2 + 1
        assert result.tests_failed == 2
        assert result.tests_skipped == 1

    def test_parse_total_style(self, dotnet_adapter):
        """Test parsing 'Total:' style output."""
        stdout = "Total: 15 tests"
        result = dotnet_adapter.parse_test_result(0, stdout, "", 2.0)

        assert result.success is True
        assert result.tests_run == 15

    def test_parse_no_counts(self, dotnet_adapter):
        """Test parsing output without test counts."""
        stdout = "Tests completed"
        result = dotnet_adapter.parse_test_result(0, stdout, "", 1.0)

        assert result.success is True
        assert result.tests_run is None
