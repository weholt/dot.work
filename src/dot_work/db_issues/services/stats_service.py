"""Statistics and analytics service for issue tracking.

Provides metrics, grouping, and trend analysis for issues.

Source: /home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/src/issue_tracker/services/
"""

from dataclasses import dataclass

from sqlmodel import Session, text


@dataclass
class StatusStats:
    """Statistics grouped by status."""

    status: str
    count: int
    percentage: float


@dataclass
class PriorityStats:
    """Statistics grouped by priority."""

    priority: str
    count: int
    percentage: float


@dataclass
class TypeStats:
    """Statistics grouped by type."""

    type: str
    count: int
    percentage: float


@dataclass
class IssueMetrics:
    """Calculated metrics for issues."""

    total_issues: int
    avg_resolution_time_days: float | None
    longest_dependency_chain: int
    blocked_count: int
    ready_to_work_count: int


@dataclass
class Statistics:
    """Complete statistics snapshot."""

    total: int
    by_status: list[StatusStats]
    by_priority: list[PriorityStats]
    by_type: list[TypeStats]
    metrics: IssueMetrics


class StatsService:
    """Service for generating statistics and analytics."""

    def __init__(self, session: Session) -> None:
        """Initialize stats service.

        Args:
            session: SQLModel session for database access
        """
        self.session = session

    def get_statistics(self) -> Statistics:
        """Get complete statistics snapshot.

        Returns:
            Statistics object with all metrics and groupings
        """
        # Get total count
        total = self._get_total_count()

        # Get groupings
        by_status = self._get_by_status(total)
        by_priority = self._get_by_priority(total)
        by_type = self._get_by_type(total)

        # Get metrics
        metrics = self._get_metrics()

        return Statistics(
            total=total,
            by_status=by_status,
            by_priority=by_priority,
            by_type=by_type,
            metrics=metrics,
        )

    def _get_total_count(self) -> int:
        """Get total issue count."""
        result = self.session.exec(
            text("SELECT COUNT(*) as cnt FROM issues WHERE deleted_at IS NULL;")
        )  # type: ignore[call-overload]
        row = result.first()
        return row.cnt if row else 0

    def _get_by_status(self, total: int) -> list[StatusStats]:
        """Get statistics grouped by status."""
        result = self.session.exec(
            text("""
            SELECT status, COUNT(*) as cnt
            FROM issues
            WHERE deleted_at IS NULL
            GROUP BY status
            ORDER BY cnt DESC;
        """)
        )  # type: ignore[call-overload]

        return [
            StatusStats(
                status=row.status,
                count=row.cnt,
                percentage=round(row.cnt / total * 100, 1) if total > 0 else 0.0,
            )
            for row in result
        ]

    def _get_by_priority(self, total: int) -> list[PriorityStats]:
        """Get statistics grouped by priority."""
        result = self.session.exec(
            text("""
            SELECT priority, COUNT(*) as cnt
            FROM issues
            WHERE deleted_at IS NULL
            GROUP BY priority
            ORDER BY priority ASC;
        """)
        )  # type: ignore[call-overload]

        return [
            PriorityStats(
                priority=str(row.priority),
                count=row.cnt,
                percentage=round(row.cnt / total * 100, 1) if total > 0 else 0.0,
            )
            for row in result
        ]

    def _get_by_type(self, total: int) -> list[TypeStats]:
        """Get statistics grouped by type."""
        result = self.session.exec(
            text("""
            SELECT type, COUNT(*) as cnt
            FROM issues
            WHERE deleted_at IS NULL
            GROUP BY type
            ORDER BY cnt DESC;
        """)
        )  # type: ignore[call-overload]

        return [
            TypeStats(
                type=str(row.type),
                count=row.cnt,
                percentage=round(row.cnt / total * 100, 1) if total > 0 else 0.0,
            )
            for row in result
        ]

    def _get_metrics(self) -> IssueMetrics:
        """Get calculated metrics."""
        total = self._get_total_count()

        # Average resolution time (for completed issues)
        avg_result = self.session.exec(
            text("""
            SELECT AVG(julianday(closed_at) - julianday(created_at)) as avg_days
            FROM issues
            WHERE closed_at IS NOT NULL AND deleted_at IS NULL;
        """)
        )  # type: ignore[call-overload]
        avg_row = avg_result.first()
        avg_resolution = round(avg_row.avg_days, 1) if avg_row and avg_row.avg_days else None

        # Longest dependency chain (simplified - just count dependencies for now)
        # A proper implementation would use graph traversal
        chain_result = self.session.exec(
            text("""
            SELECT MAX(deps.chain_length) as max_chain
            FROM (
                SELECT COUNT(*) as chain_length
                FROM dependencies
                GROUP BY from_issue_id
            ) deps;
        """)
        )  # type: ignore[call-overload]
        chain_row = chain_result.first()
        longest_chain = chain_row.max_chain if chain_row and chain_row.max_chain else 0

        # Blocked issues count
        blocked_result = self.session.exec(
            text("""
            SELECT COUNT(*) as cnt
            FROM issues
            WHERE status = 'blocked' AND deleted_at IS NULL;
        """)
        )  # type: ignore[call-overload]
        blocked_row = blocked_result.first()
        blocked_count = blocked_row.cnt if blocked_row else 0

        # Ready to work count (proposed or in-progress, not blocked)
        ready_result = self.session.exec(
            text("""
            SELECT COUNT(*) as cnt
            FROM issues
            WHERE status IN ('proposed', 'in_progress')
            AND deleted_at IS NULL;
        """)
        )  # type: ignore[call-overload]
        ready_row = ready_result.first()
        ready_count = ready_row.cnt if ready_row else 0

        return IssueMetrics(
            total_issues=total,
            avg_resolution_time_days=avg_resolution,
            longest_dependency_chain=longest_chain,
            blocked_count=blocked_count,
            ready_to_work_count=ready_count,
        )


__all__ = [
    "StatsService",
    "Statistics",
    "StatusStats",
    "PriorityStats",
    "TypeStats",
    "IssueMetrics",
]
