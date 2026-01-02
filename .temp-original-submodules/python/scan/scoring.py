"""
Quality scoring for Python codebases.
"""

from typing import Any

from dot_work.python.scan.models import CodeIndex


class QualityScorer:
    """Calculate quality scores for Python code."""

    def __init__(self) -> None:
        """Initialize the quality scorer."""
        self.weights = {
            "complexity": 0.3,
            "documentation": 0.2,
            "test_coverage": 0.2,
            "code_duplication": 0.15,
            "naming_convention": 0.15,
        }

    def score(self, index: CodeIndex) -> dict[str, Any]:
        """Calculate overall quality score for a codebase.

        Args:
            index: CodeIndex to score.

        Returns:
            Dictionary with overall score and component scores.
        """
        complexity_score = self._score_complexity(index)
        documentation_score = self._score_documentation(index)
        test_score = self._score_tests(index)

        overall = (
            complexity_score * self.weights["complexity"]
            + documentation_score * self.weights["documentation"]
            + test_score * self.weights["test_coverage"]
            + 1.0 * self.weights["code_duplication"]
            + 1.0 * self.weights["naming_convention"]
        )

        return {
            "overall": round(overall, 2),
            "complexity": round(complexity_score, 2),
            "documentation": round(documentation_score, 2),
            "tests": round(test_score, 2),
            "grade": self._get_grade(overall),
        }

    def _score_complexity(self, index: CodeIndex) -> float:
        """Score based on cyclomatic complexity.

        Args:
            index: CodeIndex to score.

        Returns:
            Score from 0.0 to 1.0.
        """
        avg_complexity = index.metrics.avg_complexity

        if avg_complexity <= 3:
            return 1.0
        elif avg_complexity <= 5:
            return 0.8
        elif avg_complexity <= 10:
            return 0.6
        elif avg_complexity <= 20:
            return 0.4
        else:
            return 0.2

    def _score_documentation(self, index: CodeIndex) -> float:
        """Score based on docstring coverage.

        Args:
            index: CodeIndex to score.

        Returns:
            Score from 0.0 to 1.0.
        """
        total_functions = 0
        documented_functions = 0
        total_classes = 0
        documented_classes = 0

        for file_entity in index.files.values():
            for func in file_entity.functions:
                total_functions += 1
                if func.docstring:
                    documented_functions += 1

            for cls in file_entity.classes:
                total_classes += 1
                if cls.docstring:
                    documented_classes += 1

        if total_functions + total_classes == 0:
            return 1.0

        doc_ratio = (documented_functions + documented_classes) / (total_functions + total_classes)
        return doc_ratio

    def _score_tests(self, index: CodeIndex) -> float:
        """Score based on test file presence.

        Args:
            index: CodeIndex to score.

        Returns:
            Score from 0.0 to 1.0.
        """
        test_files = 0
        for path in index.files.keys():
            if "test" in path.lower():
                test_files += 1

        if len(index.files) == 0:
            return 1.0

        ratio = test_files / len(index.files)
        return min(ratio * 10, 1.0)

    def _get_grade(self, score: float) -> str:
        """Convert numeric score to letter grade.

        Args:
            score: Numeric score from 0.0 to 1.0.

        Returns:
            Letter grade (A-F).
        """
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"
