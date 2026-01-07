"""Tests for the TypeScript/JavaScript language adapter."""

import json
import pytest
from pathlib import Path

from dot_work.languages.typescript import TypeScriptAdapter


@pytest.fixture
def ts_adapter():
    """Fixture providing a TypeScriptAdapter instance."""
    return TypeScriptAdapter()


@pytest.fixture
def temp_project_dir(tmp_path):
    """Fixture providing a temporary project directory."""
    return tmp_path


class TestTypeScriptAdapterCanHandle:
    """Tests for TypeScriptAdapter.can_handle()."""

    def test_detects_package_json(self, ts_adapter, temp_project_dir):
        """Test detection via package.json."""
        (temp_project_dir / "package.json").touch()
        assert ts_adapter.can_handle(temp_project_dir) is True

    def test_detects_tsconfig_json(self, ts_adapter, temp_project_dir):
        """Test detection via tsconfig.json."""
        (temp_project_dir / "tsconfig.json").touch()
        assert ts_adapter.can_handle(temp_project_dir) is True

    def test_detects_jsconfig_json(self, ts_adapter, temp_project_dir):
        """Test detection via jsconfig.json."""
        (temp_project_dir / "jsconfig.json").touch()
        assert ts_adapter.can_handle(temp_project_dir) is True

    def test_rejects_non_js_project(self, ts_adapter, temp_project_dir):
        """Test rejection of project without JS markers."""
        assert ts_adapter.can_handle(temp_project_dir) is False


class TestTypeScriptAdapterPackageManagerDetection:
    """Tests for TypeScriptAdapter._detect_package_manager()."""

    def test_detects_npm(self, ts_adapter, temp_project_dir):
        """Test detection via package-lock.json."""
        (temp_project_dir / "package-lock.json").touch()
        assert ts_adapter._detect_package_manager(temp_project_dir) == "npm"

    def test_detects_yarn(self, ts_adapter, temp_project_dir):
        """Test detection via yarn.lock."""
        (temp_project_dir / "yarn.lock").touch()
        assert ts_adapter._detect_package_manager(temp_project_dir) == "yarn"

    def test_detects_pnpm(self, ts_adapter, temp_project_dir):
        """Test detection via pnpm-lock.yaml."""
        (temp_project_dir / "pnpm-lock.yaml").touch()
        assert ts_adapter._detect_package_manager(temp_project_dir) == "pnpm"

    def test_detects_bun(self, ts_adapter, temp_project_dir):
        """Test detection via bun.lockb."""
        (temp_project_dir / "bun.lockb").touch()
        assert ts_adapter._detect_package_manager(temp_project_dir) == "bun"

    def test_defaults_to_npm(self, ts_adapter, temp_project_dir):
        """Test default to npm when no lockfile found."""
        assert ts_adapter._detect_package_manager(temp_project_dir) == "npm"


class TestTypeScriptAdapterCommands:
    """Tests for TypeScriptAdapter command methods."""

    def test_get_build_command_npm(self, ts_adapter, temp_project_dir):
        """Test build command with npm."""
        (temp_project_dir / "package-lock.json").touch()
        cmd = ts_adapter.get_build_command(temp_project_dir)
        assert cmd == ["npm", "run", "build"]

    def test_get_build_command_yarn(self, ts_adapter, temp_project_dir):
        """Test build command with yarn."""
        (temp_project_dir / "yarn.lock").touch()
        cmd = ts_adapter.get_build_command(temp_project_dir)
        assert cmd == ["yarn", "build"]

    def test_get_build_command_pnpm(self, ts_adapter, temp_project_dir):
        """Test build command with pnpm."""
        (temp_project_dir / "pnpm-lock.yaml").touch()
        cmd = ts_adapter.get_build_command(temp_project_dir)
        assert cmd == ["pnpm", "run", "build"]

    def test_get_build_command_bun(self, ts_adapter, temp_project_dir):
        """Test build command with bun."""
        (temp_project_dir / "bun.lockb").touch()
        cmd = ts_adapter.get_build_command(temp_project_dir)
        assert cmd == ["bun", "run", "build"]

    def test_get_test_command(self, ts_adapter, temp_project_dir):
        """Test test command."""
        cmd = ts_adapter.get_test_command(temp_project_dir)
        assert "npm" in cmd or "yarn" in cmd or "pnpm" in cmd or "bun" in cmd
        assert "test" in cmd

    def test_get_lint_command_with_script(self, ts_adapter, temp_project_dir):
        """Test lint command when lint script exists."""
        package_json = temp_project_dir / "package.json"
        package_json.write_text(json.dumps({"scripts": {"lint": "eslint ."}}))
        cmd = ts_adapter.get_lint_command(temp_project_dir)
        assert "lint" in cmd

    def test_get_lint_command_fallback(self, ts_adapter, temp_project_dir):
        """Test lint command fallback to direct eslint."""
        cmd = ts_adapter.get_lint_command(temp_project_dir)
        assert "npx" in cmd and "eslint" in cmd

    def test_get_type_check_command_ts(self, ts_adapter, temp_project_dir):
        """Test type check command for TypeScript."""
        (temp_project_dir / "tsconfig.json").touch()
        cmd = ts_adapter.get_type_check_command(temp_project_dir)
        assert cmd == ["npx", "tsc", "--noEmit"]

    def test_get_type_check_command_js(self, ts_adapter, temp_project_dir):
        """Test type check command for JavaScript (no tsconfig.json)."""
        (temp_project_dir / "package.json").touch()
        cmd = ts_adapter.get_type_check_command(temp_project_dir)
        assert cmd == []

    def test_get_format_command(self, ts_adapter, temp_project_dir):
        """Test format check command."""
        cmd = ts_adapter.get_format_command(temp_project_dir)
        assert len(cmd) > 0

    def test_get_format_fix_command(self, ts_adapter, temp_project_dir):
        """Test format fix command."""
        cmd = ts_adapter.get_format_fix_command(temp_project_dir)
        assert len(cmd) > 0


class TestTypeScriptAdapterParseBuildResult:
    """Tests for TypeScriptAdapter.parse_build_result()."""

    def test_parse_success(self, ts_adapter):
        """Test parsing a successful build."""
        result = ts_adapter.parse_build_result(0, "Build success.", "", 1.5)
        assert result.success is True
        assert result.exit_code == 0

    def test_parse_failure(self, ts_adapter):
        """Test parsing a failed build."""
        result = ts_adapter.parse_build_result(1, "", "Build failed.", 2.5)
        assert result.success is False
        assert result.exit_code == 1


class TestTypeScriptAdapterParseTestResult:
    """Tests for TypeScriptAdapter.parse_test_result()."""

    def test_parse_success_with_counts(self, ts_adapter):
        """Test parsing successful test output with counts."""
        stdout = "Tests: 10 passed, 0 failed, 0 skipped"
        result = ts_adapter.parse_test_result(0, stdout, "", 2.5)
        assert result.success is True
        assert result.tests_run == 10
        assert result.tests_failed == 0

    def test_parse_failure_with_counts(self, ts_adapter):
        """Test parsing failed test output with counts."""
        stdout = "Tests: 8 passed, 2 failed, 1 skipped"
        result = ts_adapter.parse_test_result(1, stdout, "", 3.0)
        assert result.success is False
        assert result.tests_run == 11  # 8 + 2 + 1
        assert result.tests_failed == 2

    def test_parse_vitest_style(self, ts_adapter):
        """Test parsing vitest-style output."""
        stdout = "Test Files: 5 passed, 2 failed"
        result = ts_adapter.parse_test_result(1, stdout, "", 2.0)
        assert result.success is False
        assert result.tests_failed == 2

    def test_parse_no_counts(self, ts_adapter):
        """Test parsing output without test counts."""
        stdout = "Tests completed"
        result = ts_adapter.parse_test_result(0, stdout, "", 1.0)
        assert result.success is True
        assert result.tests_run is None
