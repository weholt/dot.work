"""Tests for SQLite adapter (models, repositories)."""

from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, text

from dot_work.db_issues.adapters import (
    IssueRepository,
    UnitOfWork,
    create_db_engine,
)
from dot_work.db_issues.domain.entities import (
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
)


class TestCreateDbEngine:
    """Tests for create_db_engine function."""

    def test_create_db_engine_returns_engine(self) -> None:
        """Test create_db_engine returns a SQLAlchemy Engine."""
        engine = create_db_engine("sqlite:///:memory:")
        assert engine is not None

    def test_create_db_engine_with_echo(self) -> None:
        """Test create_db_engine with echo=True."""
        engine = create_db_engine("sqlite:///:memory:", echo=True)
        assert engine is not None


class TestDatabaseInitialization:
    """Tests for database table creation."""

    def test_init_creates_tables(self, tmp_path: Path) -> None:
        """Test that database initialization creates all tables."""
        db_path = tmp_path / "test.db"
        engine = create_db_engine(f"sqlite:///{db_path}")

        # Create tables using SQLAlchemy

        SQLModel.metadata.create_all(engine)

        # Verify tables exist by querying sqlite_master
        with Session(engine) as session:
            result = session.exec(
                text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            )
            table_names = [row[0] for row in result]

        assert "issues" in table_names
        assert "comments" in table_names
        assert "dependencies" in table_names
        assert "labels" in table_names
        assert "issue_labels" in table_names
        assert "epics" in table_names


class TestIssueRepository:
    """Tests for IssueRepository."""

    @pytest.fixture
    def repo(self, in_memory_db: Session) -> IssueRepository:
        """Create an IssueRepository with test database.

        Args:
            in_memory_db: In-memory database session

        Returns:
            IssueRepository instance
        """
        return IssueRepository(in_memory_db)

    def test_repository_persists_issue(self, repo: IssueRepository) -> None:
        """Test that repository persists an issue to database."""
        issue = Issue(
            id="issue-001",
            project_id="test-project",
            title="Test Issue",
            description="Test description",
            status=IssueStatus.PROPOSED,
            priority=IssuePriority.MEDIUM,
            type=IssueType.TASK,
        )

        created = repo.save(issue)
        assert created.id == "issue-001"

        # Retrieve and verify
        retrieved = repo.get("issue-001")
        assert retrieved is not None
        assert retrieved.title == "Test Issue"

    def test_repository_get_returns_none_for_nonexistent(self, repo: IssueRepository) -> None:
        """Test that get returns None for non-existent issue."""
        result = repo.get("nonexistent-id")
        assert result is None

    def test_repository_list_returns_all_issues(self, repo: IssueRepository) -> None:
        """Test that list returns all persisted issues."""
        repo.save(
            Issue(
                id="issue-001",
                project_id="test",
                title="Issue 1",
                description="Test",
                status=IssueStatus.PROPOSED,
                priority=IssuePriority.MEDIUM,
                type=IssueType.TASK,
            )
        )
        repo.save(
            Issue(
                id="issue-002",
                project_id="test",
                title="Issue 2",
                description="Test",
                status=IssueStatus.PROPOSED,
                priority=IssuePriority.HIGH,
                type=IssueType.BUG,
            )
        )

        issues = repo.list_all()
        assert len(issues) == 2

    def test_repository_update_modifies_issue(self, repo: IssueRepository) -> None:
        """Test that update modifies an existing issue."""
        created = repo.save(
            Issue(
                id="issue-001",
                project_id="test",
                title="Original",
                description="Test",
                status=IssueStatus.PROPOSED,
                priority=IssuePriority.MEDIUM,
                type=IssueType.TASK,
            )
        )

        # Modify the issue
        modified = created.transition(IssueStatus.IN_PROGRESS)
        updated = repo.save(modified)

        assert updated.status == IssueStatus.IN_PROGRESS

    def test_repository_delete_removes_issue(self, repo: IssueRepository) -> None:
        """Test that delete removes an issue."""
        created = repo.save(
            Issue(
                id="issue-001",
                project_id="test",
                title="To Delete",
                description="Test",
                status=IssueStatus.PROPOSED,
                priority=IssuePriority.MEDIUM,
                type=IssueType.TASK,
            )
        )

        result = repo.delete("issue-001")
        assert result is True

        # Verify gone
        retrieved = repo.get("issue-001")
        assert retrieved is None

    def test_repository_delete_nonexistent_returns_false(self, repo: IssueRepository) -> None:
        """Test deleting non-existent issue returns False."""
        result = repo.delete("nonexistent-id")
        assert result is False


class TestUnitOfWork:
    """Tests for UnitOfWork."""

    @pytest.fixture
    def uow(self, in_memory_db: Session) -> UnitOfWork:
        """Create a UnitOfWork with test database.

        Args:
            in_memory_db: In-memory database session

        Returns:
            UnitOfWork instance
        """
        return UnitOfWork(in_memory_db)

    def test_uow_provides_issue_repository(self, uow: UnitOfWork) -> None:
        """Test that UnitOfWork provides access to IssueRepository."""
        repo = uow.issues
        assert isinstance(repo, IssueRepository)

    def test_uow_commits_transaction(self, uow: UnitOfWork) -> None:
        """Test that UnitOfWork commits changes on exit."""
        with uow:
            issue = Issue(
                id="issue-001",
                project_id="test",
                title="Test",
                description="Test",
                status=IssueStatus.PROPOSED,
                priority=IssuePriority.MEDIUM,
                type=IssueType.TASK,
            )
            uow.issues.save(issue)

        # After context exit, check if issue persists
        retrieved = uow.issues.get("issue-001")
        assert retrieved is not None

    def test_uow_rolls_back_on_exception(self, uow: UnitOfWork) -> None:
        """Test that UnitOfWork rolls back on exception."""
        try:
            with uow:
                issue = Issue(
                    id="issue-001",
                    project_id="test",
                    title="Test",
                    description="Test",
                    status=IssueStatus.PROPOSED,
                    priority=IssuePriority.MEDIUM,
                    type=IssueType.TASK,
                )
                uow.issues.save(issue)
                raise RuntimeError("Test error")
        except RuntimeError:
            pass

        # Issue should not be persisted due to rollback
        retrieved = uow.issues.get("issue-001")
        assert retrieved is None
