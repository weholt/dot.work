"""Pytest fixtures for db-issues tests."""

from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

import pytest
import sqlmodel
from sqlalchemy import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from dot_issues.adapters.sqlite import UnitOfWork
from dot_issues.domain.entities import (
    Clock,
    Epic,
    EpicStatus,
    IdentifierService,
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
)
from dot_issues.services import DependencyService, EpicService, IssueService, LabelService

# =============================================================================
# Session-Scoped Database Engine
# =============================================================================


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine, None, None]:
    """Create a single SQLAlchemy engine shared across all tests.

    This fixture is session-scoped (runs once per test session) to prevent
    memory leaks from creating multiple engines. Each engine creation with
    SQLModel.metadata.create_all() accumulates metadata in the global singleton.

    The engine uses StaticPool which keeps a single connection alive for
    :memory: databases so the database persists across tests.

    Yields:
        SQLAlchemy Engine backed by in-memory SQLite
    """
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables once for the entire test session
    SQLModel.metadata.create_all(engine)

    try:
        yield engine
    finally:
        # CRITICAL: Clear global metadata to prevent memory leaks
        SQLModel.metadata.clear()

        # Dispose engine to close all connections
        try:
            engine.dispose()
        except Exception:
            pass


@pytest.fixture(autouse=True)
def _reset_database_state(db_engine: Engine) -> None:
    """Automatically reset database state between tests.

    This fixture is autouse=True so it runs before and after every test.
    It deletes all data from the database to ensure test isolation.

    For in-memory SQLite with StaticPool, we can't rely on transaction
    rollback alone because the database persists across tests. We need
    to explicitly delete all data.

    Args:
        db_engine: The session-scoped database engine
    """

    def _delete_all_data(session: Session) -> None:
        """Delete all data from all tables, ignoring errors for missing tables."""
        tables = [
            "epic_issues",
            "dependencies",  # Correct table name for IssueModel dependencies
            "comments",
            "issues",
            "epics",
            "projects",
            "issue_labels",  # Added for label associations
            "labels",  # Added for labels
        ]
        for table in tables:
            try:
                session.exec(sqlmodel.text(f"DELETE FROM {table}"))
            except Exception:
                # Table doesn't exist or other error - ignore
                pass
        try:
            session.commit()
        except Exception:
            pass

    # Before test: ensure we're starting fresh
    with Session(db_engine) as session:
        _delete_all_data(session)

    yield

    # After test: clean up again for next test
    with Session(db_engine) as session:
        _delete_all_data(session)


# =============================================================================
# Test Fixtures
# =============================================================================


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
def in_memory_db(db_engine: Engine) -> Generator[Session, None, None]:
    """Create an in-memory SQLite database session for testing.

    This fixture uses the shared db_engine (session-scoped) and provides
    a fresh session for each test. The database schema is already created
    by the db_engine fixture, so we only need to create a new session.

    Using a single engine across all tests prevents memory leaks from
    SQLModel.metadata accumulation that occurs with multiple create_all() calls.

    Args:
        db_engine: The session-scoped database engine

    Returns:
        SQLModel Session backed by in-memory SQLite
    """
    # Create a new session for this test
    session = Session(db_engine)

    try:
        yield session
    finally:
        # Rollback any changes made during the test
        try:
            session.rollback()
        except Exception:
            pass

        # Close the session
        try:
            session.close()
        except Exception:
            pass


@pytest.fixture
def uow(
    in_memory_db: Session,
) -> Generator[UnitOfWork, None, None]:
    """Create a shared UnitOfWork for all service fixtures.

    Sharing a single UnitOfWork across services prevents memory leaks from
    multiple repository instances caching the same data. The UnitOfWork
    is properly closed after each test.

    Args:
        in_memory_db: In-memory database session

    Returns:
        UnitOfWork instance for test services to share
    """
    from dot_issues.adapters import UnitOfWork

    uow = UnitOfWork(in_memory_db)
    try:
        yield uow
    finally:
        # CRITICAL: Close UnitOfWork to release repository cache references
        try:
            uow.close()
        except Exception:
            pass
        del uow


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
    uow: UnitOfWork,
    fixed_id_service: IdentifierService,
    fixed_clock: Clock,
) -> IssueService:
    """Create an IssueService with test dependencies.

    Uses the shared uow fixture to prevent memory leaks from multiple
    UnitOfWork instances.

    Args:
        uow: Shared UnitOfWork fixture
        fixed_id_service: Fixed identifier service
        fixed_clock: Fixed clock

    Returns:
        IssueService instance configured for testing
    """
    return IssueService(uow, fixed_id_service, fixed_clock)


@pytest.fixture
def epic_service(
    uow: UnitOfWork,
    fixed_id_service: IdentifierService,
    fixed_clock: Clock,
) -> EpicService:
    """Create an EpicService with test dependencies.

    Uses the shared uow fixture to prevent memory leaks from multiple
    UnitOfWork instances.

    Args:
        uow: Shared UnitOfWork fixture
        fixed_id_service: Fixed identifier service
        fixed_clock: Fixed clock

    Returns:
        EpicService instance configured for testing
    """
    return EpicService(uow, fixed_id_service, fixed_clock)


@pytest.fixture
def dependency_service(
    uow: UnitOfWork,
) -> DependencyService:
    """Create a DependencyService with test dependencies.

    Uses the shared uow fixture to prevent memory leaks from multiple
    UnitOfWork instances.

    Args:
        uow: Shared UnitOfWork fixture

    Returns:
        DependencyService instance configured for testing
    """
    from dot_issues.services.dependency_service import DependencyService

    return DependencyService(uow)


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


@pytest.fixture
def label_service(
    uow: UnitOfWork,
    fixed_id_service: IdentifierService,
    fixed_clock: Clock,
) -> LabelService:
    """Create a LabelService for testing.

    Uses the shared uow fixture to prevent memory leaks from multiple
    UnitOfWork instances.

    Args:
        uow: Shared UnitOfWork fixture
        fixed_id_service: Fixed identifier service
        fixed_clock: Fixed clock

    Returns:
        LabelService instance configured for testing
    """
    from dot_issues.services import LabelService

    return LabelService(uow, fixed_id_service, fixed_clock)
