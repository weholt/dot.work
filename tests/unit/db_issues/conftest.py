"""Pytest fixtures for db-issues tests."""

import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

from dot_work.db_issues.config import DbIssuesConfig
from dot_work.db_issues.domain.entities import (
    Clock,
    Comment,
    Dependency,
    DependencyType,
    Epic,
    EpicStatus,
    IdentifierService,
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
)
from dot_work.db_issues.services import EpicService, IssueService


class FixedClock(Clock):
    """Clock that returns a fixed time for testing."""

    def __init__(self, fixed_time: datetime) -> None:
        """Initialize with a fixed time.

        Args:
            fixed_time: The fixed datetime to return
        """
        self._fixed_time = fixed_time.replace(tzinfo=None)

    def now(self) -> datetime:
        """Return the fixed time.

        Returns:
            The fixed datetime (naive, as expected by domain)
        """
        return self._fixed_time


class FixedIdentifierService(IdentifierService):
    """Identifier service that returns predictable IDs for testing."""

    def __init__(self, prefix_map: dict[str, str] | None = None) -> None:
        """Initialize with optional prefix map.

        Args:
            prefix_map: Optional dict mapping prefixes to specific IDs
        """
        self._prefix_map = prefix_map or {}
        self._counter = 0

    def generate(self, prefix: str = "issue") -> str:
        """Generate a predictable identifier.

        Args:
            prefix: Entity type prefix

        Returns:
            Predictable identifier for testing
        """
        if prefix in self._prefix_map:
            return self._prefix_map[prefix]
        self._counter += 1
        suffix = format(self._counter, "04x")
        return f"{prefix}-{suffix}"


@pytest.fixture
def fixed_clock() -> Clock:
    """Return a clock fixed to a specific test time.

    Returns:
        FixedClock instance set to 2024-01-15 12:00:00 UTC
    """
    return FixedClock(datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC))


@pytest.fixture
def fixed_id_service() -> IdentifierService:
    """Return an identifier service that generates predictable IDs.

    Returns:
        FixedIdentifierService instance
    """
    # Don't fix "issue" prefix so sequential IDs are generated
    return FixedIdentifierService({"comment": "comment-0001"})


@pytest.fixture
def in_memory_db() -> Session:
    """Create an in-memory SQLite database for testing.

    Returns:
        SQLModel Session backed by in-memory SQLite
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture
def sample_issue(fixed_clock: Clock) -> Issue:
    """Create a sample issue for testing.

    Args:
        fixed_clock: Clock fixture

    Returns:
        Sample Issue entity
    """
    return Issue(
        id="issue-0001",
        project_id="test-project",
        title="Test Issue",
        description="A test issue for unit testing",
        status=IssueStatus.PROPOSED,
        priority=IssuePriority.MEDIUM,
        type=IssueType.TASK,
        assignee=None,
        labels=["bug", "test"],
        created_at=fixed_clock.now(),
        updated_at=fixed_clock.now(),
        closed_at=None,
    )


@pytest.fixture
def issue_service(
    in_memory_db: Session, fixed_id_service: IdentifierService, fixed_clock: Clock
) -> IssueService:
    """Create an IssueService with test dependencies.

    Args:
        in_memory_db: In-memory database session
        fixed_id_service: Fixed identifier service
        fixed_clock: Fixed clock

    Returns:
        IssueService instance configured for testing
    """
    from dot_work.db_issues.adapters import UnitOfWork

    uow = UnitOfWork(in_memory_db)
    return IssueService(uow, fixed_id_service, fixed_clock)


@pytest.fixture
def epic_service(
    in_memory_db: Session, fixed_id_service: IdentifierService, fixed_clock: Clock
) -> EpicService:
    """Create an EpicService with test dependencies.

    Args:
        in_memory_db: In-memory database session
        fixed_id_service: Fixed identifier service
        fixed_clock: Fixed clock

    Returns:
        EpicService instance configured for testing
    """
    from dot_work.db_issues.adapters import UnitOfWork

    uow = UnitOfWork(in_memory_db)
    return EpicService(uow, fixed_id_service, fixed_clock)


@pytest.fixture
def sample_epic(fixed_clock: Clock) -> Epic:
    """Create a sample epic for testing.

    Args:
        fixed_clock: Clock fixture

    Returns:
        Sample Epic entity
    """
    return Epic(
        id="epic-0001",
        title="Test Epic",
        description="A test epic for unit testing",
        status=EpicStatus.OPEN,
        parent_epic_id=None,
        created_at=fixed_clock.now(),
        updated_at=fixed_clock.now(),
        closed_at=None,
    )


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Create a temporary path for database testing.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        Path to temporary db-issues directory
    """
    return tmp_path / "db-issues"
