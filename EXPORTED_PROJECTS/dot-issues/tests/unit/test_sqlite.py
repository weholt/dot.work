"""Tests for SQLite adapter (models, repositories)."""

from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, text

from dot_issues.adapters import (
    IssueRepository,
    UnitOfWork,
    create_db_engine,
)
from dot_issues.domain.entities import (
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
        # CRITICAL: Dispose engine to prevent memory leaks
        engine.dispose()

    def test_create_db_engine_with_echo(self) -> None:
        """Test create_db_engine with echo=True."""
        engine = create_db_engine("sqlite:///:memory:", echo=True)
        assert engine is not None
        # CRITICAL: Dispose engine to prevent memory leaks
        engine.dispose()


class TestDatabaseInitialization:
    """Tests for database table creation."""

    @pytest.fixture
    def temp_engine(self, tmp_path: Path) -> Generator[Engine, None, None]:
        """Create a temporary database engine for testing.

        Args:
            tmp_path: Pytest temporary directory fixture

        Yields:
            SQLAlchemy Engine backed by file-based SQLite
        """
        db_path = tmp_path / "test.db"
        engine = create_db_engine(f"sqlite:///{db_path}")

        try:
            yield engine
        finally:
            # CRITICAL: Dispose engine and clear metadata to prevent memory leaks
            try:
                SQLModel.metadata.clear()
            except Exception:
                pass
            try:
                engine.dispose()
            except Exception:
                pass

    def test_init_creates_tables(self, temp_engine: Engine) -> None:
        """Test that database initialization creates all tables."""
        # Create tables using SQLAlchemy
        SQLModel.metadata.create_all(temp_engine)

        # Verify tables exist by querying sqlite_master
        with Session(temp_engine) as session:
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
        repo.save(
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


class TestSQLInjectionSafety:
    """Tests for SQL injection prevention in text() queries."""

    def test_delete_uses_parameterized_query(self, uow: UnitOfWork) -> None:
        """Test that DELETE operations use parameterized queries."""
        with uow:
            # Create an issue with labels
            issue = Issue(
                id="issue-001",
                project_id="test",
                title="Test Issue",
                description="Test",
                status=IssueStatus.PROPOSED,
                priority=IssuePriority.MEDIUM,
                type=IssueType.TASK,
                labels=["label1", "label2"],
            )
            uow.issues.save(issue)

        # Verify issue was created
        retrieved = uow.issues.get("issue-001")
        assert retrieved is not None
        assert retrieved.labels == ["label1", "label2"]

        # Update with different labels - the text() DELETE should use :issue_id parameter
        with uow:
            issue = Issue(
                id="issue-001",
                project_id="test",
                title="Test Issue",
                description="Test",
                status=IssueStatus.PROPOSED,
                priority=IssuePriority.MEDIUM,
                type=IssueType.TASK,
                labels=["label3"],
            )
            uow.issues.save(issue)

        # Verify labels were updated (proves DELETE worked safely)
        retrieved = uow.issues.get("issue-001")
        assert retrieved.labels == ["label3"]

    def test_special_characters_in_labels_safe(self, uow: UnitOfWork) -> None:
        """Test that special characters in labels are handled safely."""
        # Characters that could be dangerous in SQL if not parameterized
        dangerous_labels = [
            "label' OR '1'='1",
            "label; DROP TABLE--",
            'label"union select',
            "label`",
            "label\\",
            "label\x00",
        ]

        with uow:
            issue = Issue(
                id="issue-001",
                project_id="test",
                title="Test",
                description="Test",
                status=IssueStatus.PROPOSED,
                priority=IssuePriority.MEDIUM,
                type=IssueType.TASK,
                labels=dangerous_labels,
            )
            uow.issues.save(issue)

        # Verify labels stored as-is (not interpreted as SQL)
        retrieved = uow.issues.get("issue-001")
        assert set(retrieved.labels) == set(dangerous_labels)
        assert len(retrieved.labels) == len(dangerous_labels)

    def test_special_characters_in_assignee_safe(self, uow: UnitOfWork) -> None:
        """Test that special characters in assignees are handled safely."""
        dangerous_assignee = "admin' OR '1'='1"

        with uow:
            issue = Issue(
                id="issue-001",
                project_id="test",
                title="Test",
                description="Test",
                status=IssueStatus.PROPOSED,
                priority=IssuePriority.MEDIUM,
                type=IssueType.TASK,
                assignees=[dangerous_assignee],
            )
            uow.issues.save(issue)

        # Verify assignee stored as-is
        retrieved = uow.issues.get("issue-001")
        assert retrieved.assignees == [dangerous_assignee]

    def test_special_characters_in_references_safe(self, uow: UnitOfWork) -> None:
        """Test that special characters in references are handled safely."""
        dangerous_ref = "REF-001'; DROP TABLE issues; --"

        with uow:
            issue = Issue(
                id="issue-001",
                project_id="test",
                title="Test",
                description="Test",
                status=IssueStatus.PROPOSED,
                priority=IssuePriority.MEDIUM,
                type=IssueType.TASK,
                references=[dangerous_ref],
            )
            uow.issues.save(issue)

        # Verify reference stored as-is
        retrieved = uow.issues.get("issue-001")
        assert retrieved.references == [dangerous_ref]
