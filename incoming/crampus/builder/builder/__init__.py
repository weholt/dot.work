"""
Python Project Builder - Comprehensive build pipeline for Python projects.

A standalone build tool that provides comprehensive quality checks including:
- Code formatting (ruff)
- Linting (ruff)
- Type checking (mypy)
- Testing with coverage (pytest)
- Static analysis (radon, vulture, jscpd, import-linter, bandit)
- Security checks
- Documentation building (mkdocs)
"""

__version__ = "0.1.0"

from builder.runner import BuildRunner

__all__ = ["BuildRunner"]
