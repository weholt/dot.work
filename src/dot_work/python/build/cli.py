#!/usr/bin/env python3
"""
CLI interface for Python build pipeline in dot-work.
"""

import sys
from pathlib import Path

import typer

from dot_work.python.build.runner import BuildRunner

# Create the build app for standalone use
build_app = typer.Typer(
    help="Comprehensive build pipeline for Python projects.",
    add_completion=False,
)


def run_build(
    verbose: bool = False,
    fix: bool = False,
    clean: bool = False,
    use_uv: bool = False,
    project_root: Path | None = None,
    source_dirs: list[str] | None = None,
    test_dirs: list[str] | None = None,
    coverage_threshold: int = 70,
    memory_limit_mb: int | None = None,
    enforce_memory_limit: bool = True,
) -> bool:
    """
    Run the build pipeline with the given parameters.

    Returns True if build succeeded, False otherwise.
    """
    root = project_root or Path.cwd()

    # Create builder instance
    builder = BuildRunner(
        project_root=root,
        verbose=verbose,
        fix=fix,
        source_dirs=source_dirs,
        test_dirs=test_dirs or ["tests"],
        coverage_threshold=coverage_threshold,
        use_uv=use_uv,
        memory_limit_mb=memory_limit_mb,
        enforce_memory_limit=enforce_memory_limit,
    )

    # Handle clean command
    if clean:
        builder.clean_artifacts()
        return True

    # Run full build
    return builder.run_full_build()


@build_app.command()
def run(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    fix: bool = typer.Option(False, "--fix", help="Automatically fix formatting and linting issues"),
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
    memory_limit: int = typer.Option(
        4096,
        "--memory-limit",
        help="Memory limit in MB for test execution (default: 4096 = 4GB)",
    ),
    no_memory_enforce: bool = typer.Option(
        False,
        "--no-memory-enforce",
        help="Disable memory enforcement (monitoring only)",
    ),
) -> None:
    """
    Run the Python build pipeline.

    This command performs comprehensive quality checks including:
    - Code formatting (ruff format)
    - Linting (ruff check)
    - Type checking (mypy)
    - Testing with coverage (pytest)
    - Security scanning (ruff security)
    - Static analysis (if tools available)
    - Memory monitoring and enforcement (default: 4GB limit for pytest)

    Examples:
        pybuilder
        pybuilder --verbose
        pybuilder --fix
        pybuilder --coverage-threshold 80
        pybuilder --memory-limit 8192
        pybuilder --no-memory-enforce

    Memory Management:
        --memory-limit MB     Set memory limit in MB (default: 4096 = 4GB)
        --no-memory-enforce   Monitor memory without enforcing limits

    The build system automatically enforces memory limits during pytest runs
    to prevent system freezes. Tests exceeding the limit will be terminated.
    Uses cgroup v2 (systemd-run) when available, otherwise falls back to ulimit.
    """
    success = run_build(
        verbose=verbose,
        fix=fix,
        clean=clean,
        use_uv=use_uv,
        project_root=project_root,
        source_dirs=source_dirs,
        test_dirs=test_dirs,
        coverage_threshold=coverage_threshold,
        memory_limit_mb=memory_limit,
        enforce_memory_limit=not no_memory_enforce,
    )

    sys.exit(0 if success else 1)


# Main entry point for standalone use
def main() -> None:
    """Main entry point for the standalone pybuilder command."""
    build_app()
