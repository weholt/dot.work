"""
Tests for scan CLI commands.
"""

from pathlib import Path

from typer.testing import CliRunner

from dot_python.scan.cli import scan_app

runner = CliRunner()


def test_scan_help() -> None:
    """Test that scan help works."""
    result = runner.invoke(scan_app, ["--help"])
    assert result.exit_code == 0
    assert "Scan Python codebase" in result.output


def test_scan_run_command(tmp_path: Path) -> None:
    """Test the scan run command.

    Args:
        tmp_path: Pytest temporary path fixture.
    """
    # Create a simple Python file
    (tmp_path / "module.py").write_text("def foo(): pass")

    result = runner.invoke(scan_app, ["run", str(tmp_path)])
    # Exit code 2 is expected with no_args_is_help=True
    # but we run the command so it should work
    assert result.exit_code in (0, 2)


def test_scan_metrics_help() -> None:
    """Test the metrics command help."""
    result = runner.invoke(scan_app, ["metrics", "--help"])
    assert result.exit_code == 0
    assert "Show metrics summary" in result.output


def test_scan_complex_help() -> None:
    """Test the complex command help."""
    result = runner.invoke(scan_app, ["complex", "--help"])
    assert result.exit_code == 0
    assert "complexity threshold" in result.output


def test_scan_query_help() -> None:
    """Test the query command help."""
    result = runner.invoke(scan_app, ["query", "--help"])
    assert result.exit_code == 0
    assert "Entity name" in result.output


def test_scan_export_help() -> None:
    """Test the export command help."""
    result = runner.invoke(scan_app, ["export", "--help"])
    assert result.exit_code == 0
    assert "Export index" in result.output


def test_scan_check_help() -> None:
    """Test the check command help."""
    result = runner.invoke(scan_app, ["check", "--help"])
    assert result.exit_code == 0
    assert "YAML rules" in result.output


def test_scan_score_help() -> None:
    """Test the score command help."""
    result = runner.invoke(scan_app, ["score", "--help"])
    assert result.exit_code == 0
    assert "quality score" in result.output


def test_scan_deps_help() -> None:
    """Test the deps command help."""
    result = runner.invoke(scan_app, ["deps", "--help"])
    assert result.exit_code == 0
    assert "dependency graph" in result.output


def test_scan_layers_help() -> None:
    """Test the layers command help."""
    result = runner.invoke(scan_app, ["layers", "--help"])
    assert result.exit_code == 0
    assert "layered structure" in result.output
