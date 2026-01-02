"""Tests for python build CLI."""

from pathlib import Path

from typer.testing import CliRunner

from dot_python.build.cli import build_app, run_build

app_runner = CliRunner()


class TestBuildCLI:
    """Tests for build CLI commands."""

    def test_build_app_exists(self) -> None:
        """Test build app is accessible."""
        assert build_app is not None

    def test_run_build_function_exists(self) -> None:
        """Test run_build function is accessible."""
        assert run_build is not None

    def test_run_build_default_parameters(self, tmp_path: Path) -> None:
        """Test run_build with default parameters."""
        # Mock the build process since we don't want to run actual build
        result = run_build(
            verbose=False,
            fix=False,
            clean=True,  # Use clean to avoid actual build
            use_uv=False,
            project_root=tmp_path,
            source_dirs=None,
            test_dirs=None,
            coverage_threshold=70,
        )
        # clean always returns True
        assert result is True

    def test_build_help(self) -> None:
        """Test build help command works."""
        result = app_runner.invoke(build_app, ["--help"])
        assert result.exit_code == 0
        assert "build pipeline" in result.stdout.lower()

    def test_build_run_help(self) -> None:
        """Test build run help command works."""
        result = app_runner.invoke(build_app, ["run", "--help"])
        assert result.exit_code == 0
        assert "verbose" in result.stdout.lower()

    def test_build_verbose_flag_in_help(self) -> None:
        """Test verbose flag is in help."""
        result = app_runner.invoke(build_app, ["run", "--help"])
        assert result.exit_code == 0
        assert "--verbose" in result.stdout
        assert "-v" in result.stdout

    def test_build_fix_flag_in_help(self) -> None:
        """Test fix flag is in help."""
        result = app_runner.invoke(build_app, ["run", "--help"])
        assert result.exit_code == 0
        assert "--fix" in result.stdout

    def test_build_clean_flag_in_help(self) -> None:
        """Test clean flag is in help."""
        result = app_runner.invoke(build_app, ["run", "--help"])
        assert result.exit_code == 0
        assert "--clean" in result.stdout

    def test_build_use_uv_flag_in_help(self) -> None:
        """Test use-uv flag is in help."""
        result = app_runner.invoke(build_app, ["run", "--help"])
        assert result.exit_code == 0
        assert "--use-uv" in result.stdout

    def test_build_coverage_threshold_in_help(self) -> None:
        """Test coverage-threshold option is in help."""
        result = app_runner.invoke(build_app, ["run", "--help"])
        assert result.exit_code == 0
        assert "--coverage-threshold" in result.stdout

    def test_clean_option_works(self, tmp_path: Path) -> None:
        """Test clean option doesn't require actual build."""
        result = run_build(
            clean=True,
            project_root=tmp_path,
        )
        assert result is True
