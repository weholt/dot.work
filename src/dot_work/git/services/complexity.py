"""Complexity calculation for git commits and changes."""

import re
from typing import Any

from dot_work.git.models import ChangeAnalysis, ChangeType, FileCategory, FileChange


class ComplexityCalculator:
    """Calculates complexity scores for commits and file changes."""

    # Risky path patterns for security/sensitive file detection
    _RISKY_PATH_PATTERNS = [
        "migration",
        "schema",
        "database",
        "auth",
        "security",
        "permission",
        "role",
        "cert",
        "key",
        "secret",
    ]

    def __init__(self):
        # Complexity weights for different factors
        #
        # Rationale for weight values:
        # - Line changes: Deletions weighted higher (0.015) than additions (0.01) because
        #   removing code can have subtle ripple effects that are harder to review than
        #   new code which is typically more straightforward.
        # - Message indicators: Breaking changes (25.0) and security (20.0) weighted highest
        #   as they represent highest risk. Refactor (15.0) and migration (18.0) are high
        #   complexity due to broad impact. Performance (12.0) and hotfix (12.0) indicate
        #   urgency and complexity. Feature work (10.0) is standard complexity, bugs (8.0)
        #   are typically localized. WIP (5.0) and draft (3.0) are lower as they may be
        #   incomplete.
        # - File types: Deployment (1.5x) and config (1.2x) weighted higher due to risk.
        #   Tests (0.7x) and docs (0.3x via patterns) weighted lower as they're safer.
        # - Change types: New files (1.2x) require more review than modifications (1.0x).
        #   Deletions (0.8x) are simpler than additions. Renames (0.6x) are simplest.
        self.weights = {
            "files_changed": 5.0,  # Per file - each file adds context switching overhead
            "lines_added": 0.01,  # Per line added - baseline complexity
            "lines_deleted": 0.015,  # Per line deleted - higher cost due to ripple effects
            "file_types": {  # Multipliers for different file types
                FileCategory.CODE: 1.0,  # Baseline for code changes
                FileCategory.TESTS: 0.7,  # Tests are lower risk than production code
                FileCategory.CONFIG: 1.2,  # Config changes can have broad impact
                FileCategory.DOCUMENTATION: 0.3,  # Docs are very low risk
                FileCategory.DATA: 0.5,  # Data changes are moderate risk
                FileCategory.BUILD: 0.8,  # Build changes are moderate complexity
                FileCategory.DEPLOYMENT: 1.5,  # Deployment changes are high risk
                FileCategory.UNKNOWN: 0.6,  # Unknown files get moderate weight
            },
            "change_types": {
                ChangeType.ADDED: 1.2,  # New files require understanding from scratch
                ChangeType.DELETED: 0.8,  # Deletions simplify the codebase
                ChangeType.MODIFIED: 1.0,  # Baseline for modifications
                ChangeType.RENAMED: 0.6,  # Renames are typically straightforward
                ChangeType.COPIED: 0.7,  # Copies add some duplication
            },
            "message_indicators": {
                "breaking": 25.0,  # Breaking changes have highest impact/risk
                "security": 20.0,  # Security issues are critical
                "migration": 18.0,  # Migrations affect entire data model
                "refactor": 15.0,  # Refactors touch many files
                "performance": 12.0,  # Perf changes require careful analysis
                "hotfix": 12.0,  # Hotfixes are urgent and risky
                "feature": 10.0,  # New features are standard complexity
                "bug": 8.0,  # Bug fixes are typically localized
                "wip": 5.0,  # Work in progress - may be incomplete
                "draft": 3.0,  # Drafts are not final
            },
            "file_complexity_patterns": [
                # High complexity patterns
                (r"\.(json|yaml|yml|toml|xml)$", 1.5),  # Config files
                (r"\.(sql|migration)$", 1.8),  # Database changes
                (r"(Dockerfile|docker-compose)", 2.0),  # Container changes
                (r"\.(proto|graphql|schema)$", 2.5),  # Schema changes
                (r"\.(env|config|ini)$", 1.3),  # Environment config
                (r"(package\.json|requirements|poetry)", 1.4),  # Dependencies
                (r"\.(lock|hash)$", 0.5),  # Lock files (low complexity)
                (r"\.(md|rst|txt)$", 0.2),  # Documentation
                (r"\.(test|spec)_.*\.py$", 0.8),  # Test files
            ],
        }

        # Maximum score for each component
        self.max_scores = {
            "files_changed": 30.0,
            "lines_changed": 40.0,
            "message_indicators": 30.0,
            "base_score": 10.0,
        }

        # Pre-compile file complexity patterns for performance
        self._compiled_complexity_patterns = [
            (re.compile(pattern, re.IGNORECASE), weight)
            for pattern, weight in self.weights["file_complexity_patterns"]
        ]

    def calculate_complexity(self, commit: ChangeAnalysis) -> float:
        """
        Calculate complexity score (0-100) for a commit.

        Args:
            commit: ChangeAnalysis object with commit information

        Returns:
            Complexity score between 0 and 100
        """
        score = 0.0

        # Base score
        score += self.max_scores["base_score"]

        # Files changed component
        files_score = min(
            len(commit.files_changed) * self.weights["files_changed"],
            self.max_scores["files_changed"],
        )
        score += files_score

        # Lines changed component
        lines_score = min(
            (commit.lines_added + commit.lines_deleted) * self.weights["lines_added"],
            self.max_scores["lines_changed"],
        )
        score += lines_score

        # File type and change type adjustments
        file_multiplier = self._calculate_file_type_multiplier(commit.files_changed)
        score *= file_multiplier

        # Message indicators
        message_score = self._calculate_message_score(commit.message)
        message_score = min(message_score, self.max_scores["message_indicators"])
        score += message_score

        # Special adjustments
        score = self._apply_special_adjustments(commit, score)

        return min(score, 100.0)

    def _calculate_file_type_multiplier(self, files: list[FileChange]) -> float:
        """Calculate multiplier based on file types and change types."""
        if not files:
            return 1.0

        total_weight = 0.0
        total_files = len(files)

        for file_change in files:
            # File category weight
            category_weight = self.weights["file_types"].get(file_change.category, 1.0)

            # Change type weight
            change_type_weight = self.weights["change_types"].get(file_change.change_type, 1.0)

            # File pattern multipliers
            pattern_weight = self._get_pattern_weight(file_change.path)

            total_weight += category_weight * change_type_weight * pattern_weight

        # Average weight
        average_weight = total_weight / total_files if total_files > 0 else 1.0

        # Clamp to reasonable range
        return max(0.3, min(average_weight, 3.0))

    def _get_pattern_weight(self, file_path: str) -> float:
        """Get weight multiplier based on file path patterns using pre-compiled regex."""
        for pattern, weight in self._compiled_complexity_patterns:
            if pattern.search(file_path):
                return weight
        return 1.0

    def _calculate_message_score(self, message: str) -> float:
        """Calculate complexity score based on commit message indicators."""
        message_lower = message.lower()
        score = 0.0

        for indicator, weight in self.weights["message_indicators"].items():
            if indicator in message_lower:
                score += weight

        # Length factor (longer messages might indicate more complex changes)
        words = len(message.split())
        if words > 50:
            score += 5.0
        elif words > 20:
            score += 2.0

        # Exclamation points or urgency indicators
        if any(char in message for char in ["!", "URGENT", "IMPORTANT"]):
            score += 3.0

        return score

    def _apply_special_adjustments(self, commit: ChangeAnalysis, score: float) -> float:
        """Apply special adjustments to the complexity score."""
        adjusted_score = score

        # Breaking change penalty
        if commit.breaking_change:
            adjusted_score *= 1.5

        # Security relevance
        if commit.security_relevant:
            adjusted_score *= 1.3

        # Large number of files (might indicate refactoring or bulk changes)
        if len(commit.files_changed) > 20:
            adjusted_score *= 1.2
        elif len(commit.files_changed) > 50:
            adjusted_score *= 1.4

        # High test coverage change (might indicate extensive refactoring)
        if abs(commit.test_coverage_change) > 20:
            adjusted_score *= 1.1

        # Performance impact adjustments
        if commit.performance_impact:
            if "critical" in commit.performance_impact.lower():
                adjusted_score *= 1.3
            elif "significant" in commit.performance_impact.lower():
                adjusted_score *= 1.15

        return adjusted_score

    def calculate_file_complexity(self, file_change: FileChange) -> dict[str, Any]:
        """
        Calculate detailed complexity for a single file change.

        Args:
            file_change: FileChange object

        Returns:
            Dictionary with complexity details
        """
        base_score = 10.0

        # Lines changed score
        lines_score = (file_change.lines_added + file_change.lines_deleted) * 0.1

        # File type multiplier
        file_type_score = base_score * self.weights["file_types"].get(file_change.category, 1.0)

        # Change type multiplier
        change_type_score = file_type_score * self.weights["change_types"].get(
            file_change.change_type, 1.0
        )

        # Pattern multiplier
        pattern_score = change_type_score * self._get_pattern_weight(file_change.path)

        # Binary files
        if file_change.binary_file:
            pattern_score *= 1.5

        return {
            "base_score": base_score,
            "lines_score": lines_score,
            "file_type_multiplier": self.weights["file_types"].get(file_change.category, 1.0),
            "change_type_multiplier": self.weights["change_types"].get(
                file_change.change_type, 1.0
            ),
            "pattern_multiplier": self._get_pattern_weight(file_change.path),
            "total_score": pattern_score + lines_score,
            "complexity_level": self._get_complexity_level(pattern_score + lines_score),
        }

    def _get_complexity_level(self, score: float) -> str:
        """Get complexity level description based on score."""
        if score < 20:
            return "low"
        elif score < 40:
            return "medium"
        elif score < 60:
            return "high"
        elif score < 80:
            return "very_high"
        else:
            return "critical"

    def analyze_commit_complexity_distribution(
        self, commits: list[ChangeAnalysis]
    ) -> dict[str, int]:
        """
        Analyze distribution of complexity scores across commits.

        Args:
            commits: List of ChangeAnalysis objects

        Returns:
            Dictionary with complexity ranges and counts
        """
        ranges = {
            "0-20": 0,  # Low complexity
            "20-40": 0,  # Medium complexity
            "40-60": 0,  # High complexity
            "60-80": 0,  # Very high complexity
            "80-100": 0,  # Critical complexity
        }

        for commit in commits:
            score = commit.complexity_score
            if score < 20:
                ranges["0-20"] += 1
            elif score < 40:
                ranges["20-40"] += 1
            elif score < 60:
                ranges["40-60"] += 1
            elif score < 80:
                ranges["60-80"] += 1
            else:
                ranges["80-100"] += 1

        return ranges

    def get_top_complex_files(
        self, commits: list[ChangeAnalysis], limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get the most complex files across all commits.

        Args:
            commits: List of ChangeAnalysis objects
            limit: Maximum number of files to return

        Returns:
            List of file complexity information sorted by complexity
        """
        file_complexities: dict[str, dict[str, Any]] = {}

        for commit in commits:
            for file_change in commit.files_changed:
                file_path = file_change.path
                if file_path not in file_complexities:
                    file_complexities[file_path] = {
                        "path": file_path,
                        "category": file_change.category,
                        "total_lines_added": 0,
                        "total_lines_deleted": 0,
                        "commits": 0,
                        "complexity_score": 0.0,
                    }

                # Update file info
                file_info = file_complexities[file_path]
                file_info["total_lines_added"] += file_change.lines_added
                file_info["total_lines_deleted"] += file_change.lines_deleted
                file_info["commits"] += 1

                # Calculate complexity for this file change
                file_complexity = self.calculate_file_complexity(file_change)
                file_info["complexity_score"] += file_complexity["total_score"]

        # Sort by complexity score
        sorted_files = sorted(
            file_complexities.values(), key=lambda x: x["complexity_score"], reverse=True
        )

        return sorted_files[:limit]

    def identify_risk_factors(self, commit: ChangeAnalysis) -> list[str]:
        """Identify risk factors for a commit based on complexity analysis."""
        risk_factors = []

        if commit.complexity_score > 70:
            risk_factors.append("Very high complexity score")

        if len(commit.files_changed) > 30:
            risk_factors.append("Large number of files changed")

        if commit.lines_added + commit.lines_deleted > 1000:
            risk_factors.append("Large volume of code changes")

        if any(f.category == FileCategory.CONFIG for f in commit.files_changed):
            risk_factors.append("Configuration files modified")

        if any(f.category == FileCategory.DEPLOYMENT for f in commit.files_changed):
            risk_factors.append("Deployment configuration changed")

        if commit.breaking_change:
            risk_factors.append("Breaking change detected")

        if commit.security_relevant:
            risk_factors.append("Security-related changes")

        # Check for risky file patterns
        for file_change in commit.files_changed:
            path_lower = file_change.path.lower()
            if any(pattern in path_lower for pattern in self._RISKY_PATH_PATTERNS):
                risk_factors.append(f"High-risk file modified: {file_change.path}")

        return risk_factors
