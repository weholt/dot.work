"""
Complexity metrics for Python code using radon.
"""

from pathlib import Path
from typing import Any

from dot_work.python.scan.models import FileEntity


def compute_metrics(file_path: Path) -> dict[str, Any]:
    """Compute complexity metrics for a Python file.

    Uses radon library for cyclomatic complexity analysis.

    Args:
        file_path: Path to the Python file.

    Returns:
        Dictionary containing complexity metrics.
    """
    try:
        from radon.complexity import cc_rank, cc_visit  # type: ignore[import-untyped]
    except ImportError:
        # Radon not available, return defaults
        return {
            "avg_complexity": 1.0,
            "max_complexity": 1,
            "total_complexity": 1,
            "rank": "A",
        }

    try:
        source = file_path.read_text(encoding="utf-8")
        results = cc_visit(source)

        if not results:
            return {
                "avg_complexity": 1.0,
                "max_complexity": 1,
                "total_complexity": 1,
                "rank": "A",
            }

        complexities = [result.complexity for result in results]
        avg_complexity = sum(complexities) / len(complexities)
        max_complexity = max(complexities)
        total_complexity = sum(complexities)

        return {
            "avg_complexity": avg_complexity,
            "max_complexity": max_complexity,
            "total_complexity": total_complexity,
            "rank": cc_rank(max_complexity),
        }

    except (OSError, SyntaxError):
        return {
            "avg_complexity": 1.0,
            "max_complexity": 1,
            "total_complexity": 1,
            "rank": "A",
        }


def compute_function_complexity(source: str, function_name: str) -> int:
    """Compute cyclomatic complexity for a specific function.

    Args:
        source: Python source code.
        function_name: Name of the function to analyze.

    Returns:
        Cyclomatic complexity value.
    """
    try:
        from radon.complexity import cc_visit
    except ImportError:
        return 1

    try:
        results = cc_visit(source)
        for result in results:
            if result.name == function_name:
                return result.complexity
    except (SyntaxError, OSError):
        pass

    return 1


def annotate_with_metrics(file_entity: FileEntity) -> FileEntity:
    """Annotate functions in a file with complexity metrics.

    Args:
        file_entity: FileEntity to annotate.

    Returns:
        FileEntity with complexity values set.
    """
    try:
        source = file_entity.path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return file_entity

    for func in file_entity.functions:
        func.complexity = compute_function_complexity(source, func.name)

    for cls in file_entity.classes:
        for method in cls.methods:
            method.complexity = compute_function_complexity(source, method.name)

    return file_entity
