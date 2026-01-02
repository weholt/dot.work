"""
Tests for complexity metrics.
"""

from pathlib import Path

from dot_python.scan.metrics import (
    annotate_with_metrics,
    compute_function_complexity,
    compute_metrics,
)


def test_compute_metrics_simple_file(sample_python_file: Path) -> None:
    """Test computing metrics for a simple file.

    Args:
        sample_python_file: Fixture providing sample Python file.
    """
    metrics = compute_metrics(sample_python_file)

    assert "avg_complexity" in metrics
    assert "max_complexity" in metrics
    assert "rank" in metrics
    assert metrics["max_complexity"] >= 1


def test_compute_metrics_complex_file(complex_python_file: Path) -> None:
    """Test computing metrics for a complex file.

    Args:
        complex_python_file: Fixture providing complex Python file.
    """
    metrics = compute_metrics(complex_python_file)

    # Complex function should have higher complexity
    assert metrics["max_complexity"] > 1


def test_compute_function_complexity(sample_python_file: Path) -> None:
    """Test computing complexity for a specific function.

    Args:
        sample_python_file: Fixture providing sample Python file.
    """
    source = sample_python_file.read_text()

    complexity = compute_function_complexity(source, "simple_function")
    assert complexity >= 1


def test_annotate_with_metrics(sample_python_file: Path) -> None:
    """Test annotating file entities with metrics.

    Args:
        sample_python_file: Fixture providing sample Python file.
    """
    from dot_python.scan.models import FileEntity

    file_entity = FileEntity(
        path=sample_python_file,
        line_count=30,
        functions=[],
        classes=[],
        imports=[],
    )

    annotated = annotate_with_metrics(file_entity)

    # The file itself should be returned
    assert annotated.path == sample_python_file
