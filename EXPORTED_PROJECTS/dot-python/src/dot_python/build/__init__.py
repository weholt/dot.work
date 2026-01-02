"""
Python build pipeline for dot-work.

This module provides comprehensive build automation including:
- Code formatting (ruff format)
- Linting (ruff check)
- Type checking (mypy)
- Testing (pytest with coverage)
- Security scanning
- Static analysis
- Memory monitoring and enforcement (default: 4GB limit for pytest)

Can be used via `dot-work python build` or standalone `pybuilder` command.
"""

from dot_python.build.runner import BuildRunner, MemoryStats

__all__ = ["BuildRunner", "MemoryStats"]
