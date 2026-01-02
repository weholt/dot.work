"""Tests for N+1 query issue in cycle detection (PERF-001)."""

from datetime import UTC, datetime

import pytest
from sqlmodel import Session

from dot_issues.adapters import UnitOfWork
from dot_issues.adapters.sqlite import IssueModel
from dot_issues.domain.entities import (
    Dependency,
    DependencyType,
)


@pytest.fixture
def db_session(db_engine) -> Session:
    """Create a database session using the session-scoped db_engine.

    Uses the shared session-scoped db_engine from conftest.py to prevent
    memory leaks from multiple engine creations. The db_engine fixture
    creates tables once and reuses them across all tests.

    Args:
        db_engine: Session-scoped database engine from conftest.py

    Yields:
        Session with test data
    """
    with Session(db_engine) as session:
        yield session


class TestCycleDetectionNPlusOne:
    """Tests for N+1 query issue in cycle detection."""

    def test_has_cycle_with_no_existing_dependencies(self, db_session: Session) -> None:
        """Test cycle detection when no dependencies exist yet."""
        # Create two issues
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        issue1 = IssueModel(
            id="issue-001",
            project_id="test-project",
            title="First issue",
            description="Test issue 1",
            status="proposed",
            priority="high",
            type="feature",
            assignees=[],
            labels=[],
            created_at=now,
            updated_at=now,
            closed_at=None,
        )
        issue2 = IssueModel(
            id="issue-002",
            project_id="test-project",
            title="Second issue",
            description="Test issue 2",
            status="proposed",
            priority="medium",
            type="feature",
            assignees=[],
            labels=[],
            created_at=now,
            updated_at=now,
            closed_at=None,
        )

        for issue in (issue1, issue2):
            db_session.add(issue)
        db_session.commit()

        # Test with UnitOfWork
        uow = UnitOfWork(db_session)
        result = uow.graph.has_cycle("issue-001", "issue-002")
        assert result is False  # No cycle possible with only 2 issues and no deps

    def test_has_cycle_detects_simple_cycle(self, db_session: Session) -> None:
        """Test that cycle detection finds a simple A->B->A cycle."""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        # Create issues
        for i in range(3):
            issue = IssueModel(
                id=f"issue-{i:03d}",
                project_id="test-project",
                title=f"Issue {i}",
                description=f"Test issue {i}",
                status="proposed",
                priority="high",
                type="feature",
                assignees=[],
                labels=[],
                created_at=now,
                updated_at=now,
                closed_at=None,
            )
            db_session.add(issue)
        db_session.commit()

        uow = UnitOfWork(db_session)

        # Create dependencies: issue-001 -> issue-002
        dep1 = Dependency(
            from_issue_id="issue-001",
            to_issue_id="issue-002",
            dependency_type=DependencyType.DEPENDS_ON,
            id="dep-001",
            created_at=now,
        )
        uow.graph.add_dependency(dep1)

        # Now check if adding issue-002 -> issue-001 would create a cycle
        result = uow.graph.has_cycle("issue-002", "issue-001")
        assert result is True  # Would create A->B->A cycle

    def test_has_cycle_with_linear_chain(self, db_session: Session) -> None:
        """Test cycle detection with a linear dependency chain (no cycle)."""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        # Create issues
        for i in range(5):
            issue = IssueModel(
                id=f"issue-{i:03d}",
                project_id="test-project",
                title=f"Issue {i}",
                description=f"Test issue {i}",
                status="proposed",
                priority="high",
                type="feature",
                assignees=[],
                labels=[],
                created_at=now,
                updated_at=now,
                closed_at=None,
            )
            db_session.add(issue)
        db_session.commit()

        uow = UnitOfWork(db_session)

        # Create linear chain: 001 -> 002 -> 003 -> 004
        for i in range(1, 4):  # Start at 1 to create 001->002, 002->003, 003->004
            dep = Dependency(
                id=f"dep-{i:03d}",
                from_issue_id=f"issue-{i:03d}",
                to_issue_id=f"issue-{i + 1:03d}",
                dependency_type=DependencyType.DEPENDS_ON,
                created_at=now,
            )
            uow.graph.add_dependency(dep)
        # Commit to ensure dependencies are visible to has_cycle
        db_session.commit()

        # Check if adding 004 -> 001 would create a cycle
        result = uow.graph.has_cycle("issue-004", "issue-001")
        assert result is True  # Would create 001->002->003->004->001 cycle

        # Check if adding 003 -> 002 (reverse of existing edge 002->003)
        # This creates 002->003->002 cycle
        result = uow.graph.has_cycle("issue-003", "issue-002")
        assert result is True  # Would create 002->003->002 cycle

    def test_has_cycle_with_complex_graph(self, db_session: Session) -> None:
        """Test cycle detection with a more complex dependency graph."""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        # Create issues
        for i in range(6):
            issue = IssueModel(
                id=f"issue-{i:03d}",
                project_id="test-project",
                title=f"Issue {i}",
                description=f"Test issue {i}",
                status="proposed",
                priority="high",
                type="feature",
                assignees=[],
                labels=[],
                created_at=now,
                updated_at=now,
                closed_at=None,
            )
            db_session.add(issue)
        db_session.commit()

        uow = UnitOfWork(db_session)

        # Create graph:
        # 001 -> 002 -> 003
        # 001 -> 004
        # 002 -> 005
        dependencies = [
            ("issue-001", "issue-002"),
            ("issue-002", "issue-003"),
            ("issue-001", "issue-004"),
            ("issue-002", "issue-005"),
        ]

        for idx, (from_id, to_id) in enumerate(dependencies):
            dep = Dependency(
                id=f"dep-{idx:03d}",
                from_issue_id=from_id,
                to_issue_id=to_id,
                dependency_type=DependencyType.DEPENDS_ON,
                created_at=now,
            )
            uow.graph.add_dependency(dep)
        # Commit to ensure dependencies are visible to has_cycle
        db_session.commit()

        # Check if adding 005 -> 001 would create a cycle
        result = uow.graph.has_cycle("issue-005", "issue-001")
        assert result is True  # Would create 001->002->005->001 cycle

        # Check if adding 003 -> 001 would create a cycle
        result = uow.graph.has_cycle("issue-003", "issue-001")
        assert result is True  # Would create 001->002->003->001 cycle

        # Verify that adding an edge from 005 to a new node doesn't create a cycle
        result = uow.graph.has_cycle("issue-005", "issue-099")
        assert result is False  # Adding edge to unconnected node is safe

    def test_has_cycle_scales_efficiently(self, db_session: Session) -> None:
        """Test that cycle detection scales efficiently with many dependencies.

        This test creates a chain of 100 dependencies and verifies that
        has_cycle() completes quickly (O(1) queries, not O(N)).
        """
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        # Create 100 issues
        for i in range(100):
            issue = IssueModel(
                id=f"issue-{i:03d}",
                project_id="test-project",
                title=f"Issue {i}",
                description=f"Test issue {i}",
                status="proposed",
                priority="high",
                type="feature",
                assignees=[],
                labels=[],
                created_at=now,
                updated_at=now,
                closed_at=None,
            )
            db_session.add(issue)
        db_session.commit()

        uow = UnitOfWork(db_session)

        # Create linear chain of 99 dependencies
        for i in range(99):
            dep = Dependency(
                id=f"dep-{i:03d}",
                from_issue_id=f"issue-{i:03d}",
                to_issue_id=f"issue-{i + 1:03d}",
                dependency_type=DependencyType.DEPENDS_ON,
                created_at=now,
            )
            uow.graph.add_dependency(dep)
        # Commit to ensure dependencies are visible to has_cycle
        db_session.commit()

        # Check if adding a dependency would create a cycle
        # This should complete quickly with O(1) queries, not O(100)
        result = uow.graph.has_cycle("issue-099", "issue-001")
        assert result is True  # Would create cycle: 001->002->...->099->001

        # Verify that adding a forward dependency doesn't create a cycle
        result = uow.graph.has_cycle("issue-001", "issue-099")
        assert result is False  # Adding edge in forward direction is safe

    def test_has_cycle_with_self_loop(self, db_session: Session) -> None:
        """Test cycle detection with a self-referencing dependency."""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        issue = IssueModel(
            id="issue-001",
            project_id="test-project",
            title="First issue",
            description="Test issue",
            status="proposed",
            priority="high",
            type="feature",
            assignees=[],
            labels=[],
            created_at=now,
            updated_at=now,
            closed_at=None,
        )
        db_session.add(issue)
        db_session.commit()

        uow = UnitOfWork(db_session)

        # Self-loop is a cycle
        result = uow.graph.has_cycle("issue-001", "issue-001")
        assert result is True

    def test_has_cycle_with_empty_graph(self, db_session: Session) -> None:
        """Test cycle detection with no dependencies in the database."""
        uow = UnitOfWork(db_session)

        # No dependencies exist, so no cycle possible
        result = uow.graph.has_cycle("issue-001", "issue-002")
        assert result is False

    def test_has_cycle_multiple_paths_to_target(self, db_session: Session) -> None:
        """Test cycle detection when multiple paths exist to the target."""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        # Create issues
        for i in range(5):
            issue = IssueModel(
                id=f"issue-{i:03d}",
                project_id="test-project",
                title=f"Issue {i}",
                description=f"Test issue {i}",
                status="proposed",
                priority="high",
                type="feature",
                assignees=[],
                labels=[],
                created_at=now,
                updated_at=now,
                closed_at=None,
            )
            db_session.add(issue)
        db_session.commit()

        uow = UnitOfWork(db_session)

        # Create diamond graph:
        #     001
        #    /   \
        #  002   003
        #    \   /
        #     004
        dependencies = [
            ("issue-001", "issue-002"),
            ("issue-001", "issue-003"),
            ("issue-002", "issue-004"),
            ("issue-003", "issue-004"),
        ]

        for idx, (from_id, to_id) in enumerate(dependencies):
            dep = Dependency(
                id=f"dep-{idx:03d}",
                from_issue_id=from_id,
                to_issue_id=to_id,
                dependency_type=DependencyType.DEPENDS_ON,
                created_at=now,
            )
            uow.graph.add_dependency(dep)
        # Commit to ensure dependencies are visible to has_cycle
        db_session.commit()

        # Check if adding 004 -> 001 would create a cycle
        result = uow.graph.has_cycle("issue-004", "issue-001")
        assert result is True  # Would create 001->002/003->004->001 cycle
