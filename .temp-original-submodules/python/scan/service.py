"""
Service layer for the Python code scanner.

High-level API for scanning, querying, and analyzing Python code.
"""

from pathlib import Path
from typing import Any

from dot_work.python.scan.cache import ScanCache
from dot_work.python.scan.config import ScanConfig
from dot_work.python.scan.metrics import annotate_with_metrics
from dot_work.python.scan.models import CodeIndex
from dot_work.python.scan.repository import IndexRepository
from dot_work.python.scan.scanner import ASTScanner


class ScanService:
    """High-level service for scanning Python code."""

    def __init__(self, config: ScanConfig | None = None) -> None:
        """Initialize the scan service.

        Args:
            config: Scan configuration. Uses default if None.
        """
        self.config = config or ScanConfig()
        self.cache = ScanCache(self.config)
        self.repository = IndexRepository(self.config)

    def scan(
        self,
        root_path: Path,
        incremental: bool = False,
        annotate_metrics: bool = True,
    ) -> CodeIndex:
        """Scan a Python codebase.

        Args:
            root_path: Root directory to scan.
            incremental: Use incremental scanning if True.
            annotate_metrics: Add complexity metrics to entities.

        Returns:
            CodeIndex containing all scanned entities.

        Raises:
            FileNotFoundError: If root_path does not exist.
            NotADirectoryError: If root_path is not a directory.
        """
        # Validate path before scanning to provide clear error messages
        if not root_path.exists():
            raise FileNotFoundError(f"Scan path does not exist: {root_path}")
        if not root_path.is_dir():
            raise NotADirectoryError(f"Scan path is not a directory: {root_path}")

        scanner = ASTScanner(root_path)
        index = scanner.scan(incremental=incremental)

        if annotate_metrics:
            for file_entity in index.files.values():
                annotated = annotate_with_metrics(file_entity)
                index.files[str(file_entity.path)] = annotated

        self._update_metrics(index)
        self.repository.save(index)
        self.cache.save()

        return index

    def load_index(self) -> CodeIndex | None:
        """Load the existing code index.

        Returns:
            CodeIndex if it exists, None otherwise.
        """
        return self.repository.load()

    def query_index(self, index: CodeIndex, name: str) -> dict[str, Any] | None:
        """Query the index for an entity by name.

        Args:
            index: CodeIndex to query.
            name: Entity name to find.

        Returns:
            Dictionary with query results or None.
        """
        functions = index.find_function(name)
        classes = index.find_class(name)

        if not functions and not classes:
            return None

        return {
            "functions": [
                {
                    "name": f.name,
                    "file": str(f.file_path),
                    "line": f.line_no,
                    "complexity": f.complexity,
                }
                for f in (functions or [])
            ],
            "classes": [
                {
                    "name": c.name,
                    "file": str(c.file_path),
                    "line": c.line_no,
                    "methods": [m.name for m in c.methods],
                }
                for c in (classes or [])
            ],
        }

    def get_complex_functions(self, index: CodeIndex, threshold: int) -> list[dict[str, Any]]:
        """Get functions exceeding complexity threshold.

        Args:
            index: CodeIndex to query.
            threshold: Minimum complexity.

        Returns:
            List of complex function descriptions.
        """
        functions = index.get_complex_functions(threshold)
        return [
            {
                "name": f.name,
                "file": str(f.file_path),
                "line": f.line_no,
                "complexity": f.complexity,
            }
            for f in functions
        ]

    def get_metrics(self, index: CodeIndex) -> dict[str, Any]:
        """Get summary metrics for the codebase.

        Args:
            index: CodeIndex to summarize.

        Returns:
            Dictionary with metrics.
        """
        return {
            "total_files": index.metrics.total_files,
            "total_functions": index.metrics.total_functions,
            "total_classes": index.metrics.total_classes,
            "total_lines": index.metrics.total_lines,
            "avg_complexity": index.metrics.avg_complexity,
            "max_complexity": index.metrics.max_complexity,
        }

    def _update_metrics(self, index: CodeIndex) -> None:
        """Update metrics in the index.

        Calculates metrics incrementally to avoid O(N) memory usage
        from storing all functions in an intermediate list.

        Args:
            index: CodeIndex to update.
        """
        index.metrics.total_files = len(index.files)
        index.metrics.total_functions = sum(len(f.functions) for f in index.files.values())
        index.metrics.total_classes = sum(len(f.classes) for f in index.files.values())
        index.metrics.total_lines = sum(f.line_count for f in index.files.values())

        # Calculate complexity metrics incrementally (O(1) additional memory)
        sum_complexity = 0
        max_complexity = 0
        high_complexity_functions: list[str] = []

        for file_entity in index.files.values():
            for func in file_entity.functions:
                sum_complexity += func.complexity
                max_complexity = max(max_complexity, func.complexity)
                if func.complexity > 10:
                    high_complexity_functions.append(
                        f"{func.name} ({func.file_path}:{func.line_no})"
                    )
            for cls in file_entity.classes:
                for method in cls.methods:
                    sum_complexity += method.complexity
                    max_complexity = max(max_complexity, method.complexity)
                    if method.complexity > 10:
                        high_complexity_functions.append(
                            f"{method.name} ({method.file_path}:{method.line_no})"
                        )

        if index.metrics.total_functions > 0:
            index.metrics.avg_complexity = sum_complexity / index.metrics.total_functions
            index.metrics.max_complexity = max_complexity
            index.metrics.high_complexity_functions = high_complexity_functions
