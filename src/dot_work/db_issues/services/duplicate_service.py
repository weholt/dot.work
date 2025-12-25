"""Duplicate detection service for db-issues module.

Provides functionality to detect potential duplicate issues based on
title similarity and common attributes.
"""

import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from dot_work.db_issues.domain.entities import Clock, Issue

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class DuplicateGroup:
    """A group of potentially duplicate issues.

    Attributes:
        issues: List of duplicate issue IDs
        similarity: Similarity score (0-1)
        representative_issue: The issue that best represents the group
    """

    issues: list[str]
    similarity: float
    representative_issue: str | None = None


@dataclass
class DuplicateDetectionResult:
    """Result of duplicate detection.

    Attributes:
        groups: List of duplicate groups found
        total_issues: Total number of issues scanned
        duplicates_found: Number of issues that have duplicates
        scan_time: Time taken to scan
    """

    groups: list[DuplicateGroup]
    total_issues: int
    duplicates_found: int
    scan_time: float = 0.0


# =============================================================================
# Service Protocols
# =============================================================================


@runtime_checkable
class DuplicateDetector(Protocol):
    """Protocol for duplicate detection algorithms."""

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings.

        Args:
            text1: First text string
            text2: Second text string

        Returns:
            Similarity score between 0 and 1
        """
        ...

    def find_duplicates(
        self, issues: Sequence[Issue], threshold: float
    ) -> list[DuplicateGroup]:
        """Find duplicate groups from a list of issues.

        Args:
            issues: List of issues to scan
            threshold: Minimum similarity to consider as duplicate

        Returns:
            List of duplicate groups
        """
        ...


# =============================================================================
# Service Implementation
# =============================================================================


class JaccardDuplicateDetector:
    """Duplicate detector using Jaccard similarity on normalized titles.

    Jaccard similarity = (intersection / union) of word sets.
    """

    def __init__(self) -> None:
        """Initialize the Jaccard duplicate detector."""
        self._word_pattern = re.compile(r"\b\w+\b")

    def _normalize_title(self, title: str) -> set[str]:
        """Normalize title to a set of words.

        Args:
            title: Title string to normalize

        Returns:
            Set of lowercase words
        """
        # Extract words, convert to lowercase
        words = self._word_pattern.findall(title.lower())
        return set(words)

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two text strings.

        Args:
            text1: First text string
            text2: Second text string

        Returns:
            Similarity score between 0 and 1
        """
        words1 = self._normalize_title(text1)
        words2 = self._normalize_title(text2)

        if not words1 and not words2:
            return 1.0  # Both empty
        if not words1 or not words2:
            return 0.0  # One empty

        # Jaccard similarity = intersection / union
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def find_duplicates(
        self, issues: Sequence[Issue], threshold: float
    ) -> list[DuplicateGroup]:
        """Find duplicate groups from a list of issues.

        Args:
            issues: List of issues to scan
            threshold: Minimum similarity to consider as duplicate (0-1)

        Returns:
            List of duplicate groups, sorted by similarity (highest first)
        """
        # Track which issues have been grouped
        grouped: set[str] = set()
        groups: list[DuplicateGroup] = []

        for i, issue1 in enumerate(issues):
            if issue1.id in grouped:
                continue

            # Find similar issues
            similar_issues: list[tuple[str, float]] = []

            for j, issue2 in enumerate(issues):
                if i == j or issue2.id in grouped:
                    continue

                similarity = self.calculate_similarity(issue1.title, issue2.title)

                if similarity >= threshold:
                    similar_issues.append((issue2.id, similarity))

            if similar_issues:
                # Create a duplicate group
                all_similar = [issue1.id] + [sid for sid, _ in similar_issues]
                avg_similarity = sum(sim for _, sim in similar_issues) / len(
                    similar_issues
                )

                # Choose representative (shortest ID = likely oldest)
                representative = min(all_similar, key=lambda x: (len(x), x))

                group = DuplicateGroup(
                    issues=all_similar,
                    similarity=avg_similarity,
                    representative_issue=representative,
                )
                groups.append(group)

                # Mark all as grouped
                grouped.update(all_similar)

        # Sort by similarity (highest first)
        groups.sort(key=lambda g: g.similarity, reverse=True)
        return groups


class DuplicateService:
    """Service for detecting potential duplicate issues.

    Provides functionality to scan issues and find potential duplicates
    based on title similarity using configurable detection algorithms.
    """

    def __init__(
        self,
        detector: DuplicateDetector | None = None,
        clock: Clock | None = None,
    ) -> None:
        """Initialize the duplicate service.

        Args:
            detector: Duplicate detection algorithm (uses Jaccard if None)
            clock: Time provider (uses system time if None)
        """
        self.detector = detector or JaccardDuplicateDetector()
        self.clock = clock

    def find_duplicates(
        self,
        issues: Sequence[Issue],
        threshold: float = 0.7,
    ) -> DuplicateDetectionResult:
        """Find potential duplicate issues.

        Args:
            issues: List of issues to scan
            threshold: Minimum similarity to consider as duplicate (default: 0.7)

        Returns:
            Duplicate detection result with groups and statistics
        """
        start_time = datetime.now(UTC).timestamp()

        logger.debug(
            "Finding duplicates: issues=%d, threshold=%s", len(issues), threshold
        )

        # Use detector to find duplicate groups
        groups = self.detector.find_duplicates(issues, threshold)

        # Count duplicates
        duplicates_count = sum(len(g.issues) for g in groups)

        end_time = datetime.now(UTC).timestamp()
        scan_time = end_time - start_time

        result = DuplicateDetectionResult(
            groups=groups,
            total_issues=len(issues),
            duplicates_found=duplicates_count,
            scan_time=scan_time,
        )

        logger.info(
            "Duplicate detection complete: groups=%d, duplicates=%d, time=%.3fs",
            len(groups),
            duplicates_count,
            scan_time,
        )

        return result


__all__ = [
    "DuplicateGroup",
    "DuplicateDetectionResult",
    "DuplicateDetector",
    "JaccardDuplicateDetector",
    "DuplicateService",
]
