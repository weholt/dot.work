"""
Python development utilities for dot-work.

This package provides Python-specific tools and utilities integrated
into the dot-work CLI framework.
"""

from pathlib import Path

import typer

from dot_work.python.build.cli import run_build
from dot_work.python.scan.cli import scan_app

# Python subcommand app
python_app = typer.Typer(help="Python development utilities.", no_args_is_help=True)

# Register scan as subcommand
python_app.add_typer(scan_app, name="scan")


@python_app.command()
def build(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    fix: bool = typer.Option(
        False, "--fix", help="Automatically fix formatting and linting issues"
    ),
    clean: bool = typer.Option(False, "--clean", help="Clean build artifacts and exit"),
    use_uv: bool = typer.Option(False, "--use-uv", help="Use 'uv run' prefix for commands"),
    project_root: Path = typer.Option(
        None,
        "--project-root",
        help="Project root directory (default: current directory)",
    ),
    source_dirs: list[str] = typer.Option(
        None,
        "--source-dirs",
        help="Source directories to check (default: auto-detect)",
    ),
    test_dirs: list[str] = typer.Option(
        ["tests"],
        "--test-dirs",
        help="Test directories (default: tests)",
    ),
    coverage_threshold: int = typer.Option(
        70,
        "--coverage-threshold",
        help="Minimum coverage percentage required (default: 70)",
    ),
) -> None:
    """
    Run comprehensive Python build pipeline.

    Performs quality checks including:
    - Code formatting (ruff format)
    - Linting (ruff check)
    - Type checking (mypy)
    - Testing with coverage (pytest)
    - Security scanning (ruff security)
    - Static analysis (if tools available)

    Examples:
        dot-work python build
        dot-work python build --verbose
        dot-work python build --fix
        dot-work python build --coverage-threshold 80
    """
    import sys

    success = run_build(
        verbose=verbose,
        fix=fix,
        clean=clean,
        use_uv=use_uv,
        project_root=project_root,
        source_dirs=source_dirs,
        test_dirs=test_dirs,
        coverage_threshold=coverage_threshold,
    )

    sys.exit(0 if success else 1)


__all__ = ["python_app", "build", "scan_app"]
