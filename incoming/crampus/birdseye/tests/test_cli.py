"""CLI coverage for birdseye."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from birdseye.cli import app


def test_cli_analyze_generates_output(sample_project: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    output_dir = tmp_path / "output"

    result = runner.invoke(app, [str(sample_project), str(output_dir)], catch_exceptions=False)

    assert result.exit_code == 0, result.stdout
    assert (output_dir / "birdseye_overview.md").exists()
    assert (output_dir / "features.json").exists()
    assert "Scan complete" in result.stdout
