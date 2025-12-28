"""Unit tests for StatsService statistics and analytics (CR-020)."""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlmodel import Session, text

from dot_work.db_issues.adapters import UnitOfWork
from dot_work.db_issues.adapters.sqlite import IssueModel
from dot_work.db_issues.services.stats_service import (
    IssueMetrics,
    Statistics,
    StatsService,
)


@pytest.fixture
def db_session_with_stats_data(
    in_memory_db: Session,
) -> Generator[Session, None, None]:
    """Create a database session with sample statistics data.

    Args:
        in_memory_db: In-memory database session

    Yields:
        Session with sample issues for statistics testing
    """
    session = in_memory_db

    # Fixed timestamp for consistent test data
    now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

    # Create sample issues with various statuses, priorities, and types
    sample_issues = [
        # Proposed issues (3)
        IssueModel(
            id="issue-0001",
            project_id="test-project",
            title="Proposed bug",
            description="Bug to fix",
            status="proposed",
            priority="high",
            type="bug",
            assignees=[],
            labels=["bug"],
            created_at=now,
            updated_at=now,
            closed_at=None,
        ),
        IssueModel(
            id="issue-0002",
            project_id="test-project",
            title="Proposed feature",
            description="Feature to add",
            status="proposed",
            priority="medium",
            type="feature",
            assignees=[],
            labels=["enhancement"],
            created_at=now,
            updated_at=now,
            closed_at=None,
        ),
        IssueModel(
            id="issue-0003",
            project_id="test-project",
            title="Proposed task",
            description="Task to do",
            status="proposed",
            priority="low",
            type="task",
            assignees=[],
            labels=["todo"],
            created_at=now,
            updated_at=now,
            closed_at=None,
        ),
        # In-progress issues (2)
        IssueModel(
            id="issue-0004",
            project_id="test-project",
            title="In progress bug",
            description="Bug being fixed",
            status="in_progress",
            priority="high",
            type="bug",
            assignees=["user1"],
            labels=["active"],
            created_at=now,
            updated_at=now,
            closed_at=None,
        ),
        IssueModel(
            id="issue-0005",
            project_id="test-project",
            title="In progress feature",
            description="Feature being added",
            status="in_progress",
            priority="medium",
            type="feature",
            assignees=["user2"],
            labels=["active"],
            created_at=now,
            updated_at=now,
            closed_at=None,
        ),
        # Blocked issues (2)
        IssueModel(
            id="issue-0006",
            project_id="test-project",
            title="Blocked task",
            description="Task blocked by dependency",
            status="blocked",
            priority="high",
            type="task",
            assignees=[],
            labels=["blocked"],
            created_at=now,
            updated_at=now,
            closed_at=None,
        ),
        IssueModel(
            id="issue-0007",
            project_id="test-project",
            title="Blocked bug",
            description="Bug blocked by external factor",
            status="blocked",
            priority="medium",
            type="bug",
            assignees=[],
            labels=["blocked"],
            created_at=now,
            updated_at=now,
            closed_at=None,
        ),
        # Completed issues (3) - for resolution time calculation
        IssueModel(
            id="issue-0008",
            project_id="test-project",
            title="Completed bug 1",
            description="Bug fixed quickly",
            status="completed",
            priority="high",
            type="bug",
            assignees=[],
            labels=["done"],
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(days=1),
            closed_at=now - timedelta(days=1),
        ),
        IssueModel(
            id="issue-0009",
            project_id="test-project",
            title="Completed feature 1",
            description="Feature added in 5 days",
            status="completed",
            priority="medium",
            type="feature",
            assignees=[],
            labels=["done"],
            created_at=now - timedelta(days=5),
            updated_at=now,
            closed_at=now,
        ),
        IssueModel(
            id="issue-0010",
            project_id="test-project",
            title="Completed task 1",
            description="Task done in 3 days",
            status="completed",
            priority="low",
            type="task",
            assignees=[],
            labels=["done"],
            created_at=now - timedelta(days=3),
            updated_at=now,
            closed_at=now,
        ),
    ]

    for issue in sample_issues:
        session.add(issue)

    session.commit()
    yield session


@pytest.fixture
def db_uow_with_stats_data(
    db_session_with_stats_data: Session,
) -> Generator[UnitOfWork, None, None]:
    """Create a UnitOfWork with statistics data for testing.

    Args:
        db_session_with_stats_data: Session with sample data

    Yields:
        UnitOfWork wrapping the session
    """
    uow = UnitOfWork(db_session_with_stats_data)
    yield uow


class TestStatsService:
    """Tests for StatsService statistics generation."""

    def test_get_statistics_returns_complete_snapshot(
        self, db_uow_with_stats_data: UnitOfWork
    ) -> None:
        """Test that get_statistics returns all required components."""
        service = StatsService(db_uow_with_stats_data.session)
        stats = service.get_statistics()

        assert isinstance(stats, Statistics)
        assert stats.total == 10
        assert len(stats.by_status) > 0
        assert len(stats.by_priority) > 0
        assert len(stats.by_type) > 0
        assert isinstance(stats.metrics, IssueMetrics)

    def test_by_status_grouping(self, db_uow_with_stats_data: UnitOfWork) -> None:
        """Test statistics grouped by status."""
        service = StatsService(db_uow_with_stats_data.session)
        stats = service.get_statistics()

        # Should have 4 status groups: proposed (3), in_progress (2), blocked (2), completed (3)
        status_dict = {s.status: s.count for s in stats.by_status}
        assert status_dict.get("proposed") == 3
        assert status_dict.get("in_progress") == 2
        assert status_dict.get("blocked") == 2
        assert status_dict.get("completed") == 3

        # Verify percentages sum to approximately 100%
        total_percentage = sum(s.percentage for s in stats.by_status)
        assert 99.0 <= total_percentage <= 101.0  # Allow for rounding

    def test_by_priority_grouping(self, db_uow_with_stats_data: UnitOfWork) -> None:
        """Test statistics grouped by priority."""
        service = StatsService(db_uow_with_stats_data.session)
        stats = service.get_statistics()

        # Should have 3 priority groups: high (4), medium (4), low (2)
        priority_dict = {p.priority: p.count for p in stats.by_priority}
        assert priority_dict.get("high") == 4
        assert priority_dict.get("medium") == 4
        assert priority_dict.get("low") == 2

        # Verify percentages sum to approximately 100%
        total_percentage = sum(p.percentage for p in stats.by_priority)
        assert 99.0 <= total_percentage <= 101.0  # Allow for rounding

    def test_by_type_grouping(self, db_uow_with_stats_data: UnitOfWork) -> None:
        """Test statistics grouped by type."""
        service = StatsService(db_uow_with_stats_data.session)
        stats = service.get_statistics()

        # Should have 3 type groups: bug (4), feature (3), task (3)
        type_dict = {t.type: t.count for t in stats.by_type}
        assert type_dict.get("bug") == 4
        assert type_dict.get("feature") == 3
        assert type_dict.get("task") == 3

        # Verify percentages sum to approximately 100%
        total_percentage = sum(t.percentage for t in stats.by_type)
        assert 99.0 <= total_percentage <= 101.0  # Allow for rounding

    def test_metrics_total_issues(self, db_uow_with_stats_data: UnitOfWork) -> None:
        """Test that metrics total_issues matches overall total."""
        service = StatsService(db_uow_with_stats_data.session)
        stats = service.get_statistics()

        assert stats.metrics.total_issues == stats.total

    def test_metrics_blocked_count(self, db_uow_with_stats_data: UnitOfWork) -> None:
        """Test that blocked_count is calculated correctly."""
        service = StatsService(db_uow_with_stats_data.session)
        stats = service.get_statistics()

        # We created 2 blocked issues
        assert stats.metrics.blocked_count == 2

    def test_metrics_ready_to_work_count(self, db_uow_with_stats_data: UnitOfWork) -> None:
        """Test that ready_to_work_count includes proposed and in_progress."""
        service = StatsService(db_uow_with_stats_data.session)
        stats = service.get_statistics()

        # Should be proposed (3) + in_progress (2) = 5
        assert stats.metrics.ready_to_work_count == 5

    def test_metrics_avg_resolution_time(self, db_uow_with_stats_data: UnitOfWork) -> None:
        """Test that average resolution time is calculated correctly."""
        service = StatsService(db_uow_with_stats_data.session)
        stats = service.get_statistics()

        # We have 3 completed issues: 2 days, 5 days, 3 days
        # Average should be (2 + 5 + 3) / 3 = 3.33 days (approximately)
        assert stats.metrics.avg_resolution_time_days is not None
        assert 3.0 <= stats.metrics.avg_resolution_time_days <= 3.5

    def test_empty_database_returns_zero_stats(
        self, in_memory_db: Session
    ) -> None:
        """Test statistics on empty database."""
        service = StatsService(in_memory_db)
        stats = service.get_statistics()

        assert stats.total == 0
        assert stats.by_status == []
        assert stats.by_priority == []
        assert stats.by_type == []
        assert stats.metrics.total_issues == 0
        assert stats.metrics.blocked_count == 0
        assert stats.metrics.ready_to_work_count == 0
        assert stats.metrics.avg_resolution_time_days is None

    def test_percentage_calculations_with_zero_total(self, in_memory_db: Session) -> None:
        """Test that percentage calculations handle zero total gracefully."""
        service = StatsService(in_memory_db)
        stats = service.get_statistics()

        # Should not divide by zero
        assert stats.total == 0

    def test_deleted_issues_excluded_from_stats(
        self, db_session_with_stats_data: Session
    ) -> None:
        """Test that soft-deleted issues are excluded from statistics."""
        # Soft-delete one issue
        session = db_session_with_stats_data
        session.exec(  # type: ignore[call-overload]
            text("UPDATE issues SET deleted_at = '2024-01-15 12:00:00' WHERE id = 'issue-0001';")
        )
        session.commit()

        service = StatsService(session)
        stats = service.get_statistics()

        # Total should be 9 (10 - 1 deleted)
        assert stats.total == 9

        # Status counts should exclude deleted issue
        status_dict = {s.status: s.count for s in stats.by_status}
        assert status_dict.get("proposed") == 2  # Was 3, now 2


class TestStatsServiceEdgeCases:
    """Tests for StatsService edge cases and corner cases."""

    def test_single_issue_statistics(self, in_memory_db: Session) -> None:
        """Test statistics with only one issue."""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        issue = IssueModel(
            id="issue-0001",
            project_id="test-project",
            title="Single issue",
            description="Only issue",
            status="proposed",
            priority="high",
            type="bug",
            assignees=[],
            labels=[],
            created_at=now,
            updated_at=now,
            closed_at=None,
        )
        in_memory_db.add(issue)
        in_memory_db.commit()

        service = StatsService(in_memory_db)
        stats = service.get_statistics()

        assert stats.total == 1
        assert len(stats.by_status) == 1
        assert stats.by_status[0].percentage == 100.0

    def test_all_completed_issues(self, in_memory_db: Session) -> None:
        """Test statistics when all issues are completed."""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        for i in range(5):
            issue = IssueModel(
                id=f"issue-{i:04d}",
                project_id="test-project",
                title=f"Completed issue {i}",
                description=f"Description {i}",
                status="completed",
                priority="medium",
                type="task",
                assignees=[],
                labels=[],
                created_at=now - timedelta(days=i + 1),
                updated_at=now,
                closed_at=now,
            )
            in_memory_db.add(issue)
        in_memory_db.commit()

        service = StatsService(in_memory_db)
        stats = service.get_statistics()

        assert stats.total == 5
        assert stats.metrics.blocked_count == 0
        assert stats.metrics.ready_to_work_count == 0
        assert stats.metrics.avg_resolution_time_days is not None

    def test_all_blocked_issues(self, in_memory_db: Session) -> None:
        """Test statistics when all issues are blocked."""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        for i in range(5):
            issue = IssueModel(
                id=f"issue-{i:04d}",
                project_id="test-project",
                title=f"Blocked issue {i}",
                description=f"Description {i}",
                status="blocked",
                priority="high",
                type="bug",
                assignees=[],
                labels=["blocked"],
                created_at=now,
                updated_at=now,
                closed_at=None,
            )
            in_memory_db.add(issue)
        in_memory_db.commit()

        service = StatsService(in_memory_db)
        stats = service.get_statistics()

        assert stats.total == 5
        assert stats.metrics.blocked_count == 5
        assert stats.metrics.ready_to_work_count == 0
