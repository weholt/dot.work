"""Command line interface for birdseye."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import typer

from .pipeline import analyze_project, write_outputs

app = typer.Typer(help="Generate a birdseye overview of a codebase.")


def _version_callback(value: bool) -> None:
    if value:
        try:
            current_version = version("birdseye")
        except PackageNotFoundError:
            current_version = "unknown"
        typer.echo(f"birdseye version {current_version}")
        raise typer.Exit()


@app.command()
def analyze(
    input_dir: Path = typer.Argument(
        ..., exists=True, resolve_path=True, help="Folder containing the project to scan."
    ),
    output_dir: Path = typer.Argument(
        ...,
        exists=False,
        resolve_path=False,
        help="Where to store the generated markdown and JSON files.",
    ),
    _version: bool | None = typer.Option(
        None, "--version", callback=_version_callback, is_flag=True, help="Show version and exit."
    ),
) -> None:
    """Scan the given project and emit human and machine readable summaries."""

    bundle = analyze_project(input_dir)
    destinations = write_outputs(bundle, output_dir)

    typer.echo("Scan complete. Deliverables:")
    for label, path in destinations.items():
        typer.echo(f"- {label}: {path}")


def main() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
