#!/usr/bin/env python3
"""
CLI interface for Python Project Builder.
"""

import argparse
import sys
from pathlib import Path

from builder.runner import BuildRunner


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Comprehensive build pipeline for Python projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full build pipeline
  pybuilder

  # Run with verbose output
  pybuilder --verbose

  # Auto-fix formatting and linting issues
  pybuilder --fix

  # Use with uv package manager
  pybuilder --use-uv

  # Clean build artifacts
  pybuilder --clean

  # Set custom coverage threshold
  pybuilder --coverage-threshold 80

  # Specify source directories
  pybuilder --source-dirs src mypackage

For more information, see: https://github.com/your-username/python-project-builder
        """,
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix formatting and linting issues",
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts and exit",
    )

    parser.add_argument(
        "--use-uv",
        action="store_true",
        help="Use 'uv run' prefix for commands (requires uv package manager)",
    )

    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)",
    )

    parser.add_argument(
        "--source-dirs",
        nargs="+",
        help="Source directories to check (default: auto-detect)",
    )

    parser.add_argument(
        "--test-dirs",
        nargs="+",
        default=["tests"],
        help="Test directories (default: tests)",
    )

    parser.add_argument(
        "--coverage-threshold",
        type=int,
        default=70,
        help="Minimum coverage percentage required (default: 70)",
    )

    args = parser.parse_args()

    # Create builder instance
    builder = BuildRunner(
        project_root=args.project_root,
        verbose=args.verbose,
        fix=args.fix,
        source_dirs=args.source_dirs,
        test_dirs=args.test_dirs,
        coverage_threshold=args.coverage_threshold,
        use_uv=args.use_uv,
    )

    # Handle clean command
    if args.clean:
        builder.clean_artifacts()
        return 0

    # Run full build
    success = builder.run_full_build()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
