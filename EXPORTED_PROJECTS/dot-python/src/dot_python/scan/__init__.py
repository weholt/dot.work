"""
Python codebase scanner for dot-work.

This module provides AST-based code analysis for Python projects,
including structure parsing, complexity metrics, and dependency analysis.
"""

from dot_python.scan.models import (
    ClassEntity,
    CodeIndex,
    Dependency,
    FileEntity,
    FunctionEntity,
    ImportInfo,
)
from dot_python.scan.scanner import ASTScanner

__all__ = [
    "ASTScanner",
    "CodeIndex",
    "ClassEntity",
    "FileEntity",
    "FunctionEntity",
    "ImportInfo",
    "Dependency",
]
