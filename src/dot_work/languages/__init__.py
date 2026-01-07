"""Language adapter system for multi-language build support.

This module provides a pluggable architecture for supporting different
programming languages with their own build, test, and lint workflows.
"""

from dot_work.languages.base import (
    BuildResult,
    LanguageAdapter,
    TestResult,
)

__all__ = ["LanguageAdapter", "BuildResult", "TestResult"]
