#!/usr/bin/env python3
"""
Main entry point for `python -m dot_work.python.build`.

This module enables running the Python build pipeline using:
    python -m dot_work.python.build

Instead of:
    python -m dot_work.python.build.cli

The __main__.py pattern is Python's recommended approach for package
executables and avoids the RuntimeWarning that occurs with the
`-m package.module` pattern.

Example usage:
    python -m dot_work.python.build
    python -m dot_work.python.build --verbose
    python -m dot_work.python.build --fix
    python -m dot_work.python.build --memory-limit 8192
"""

from dot_work.python.build.cli import main

if __name__ == "__main__":
    main()
