"""SQLite adapter for db-issues module.

Consolidates database models, engine factory, repositories, and UnitOfWork
from the issue-tracker project into a single module for dot-work.

Source: /home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/src/issue_tracker/adapters/db/

SQL Injection Safety:
---------------------
This module uses SQLAlchemy/SQLModel which provides protection against SQL injection
through parameterized queries. When using raw SQL with `text()`, ALWAYS follow these
safe patterns:

1. **USE NAMED PARAMETERS**: Never concatenate user input into SQL strings.
   ❌ BAD:  text(f"DELETE FROM table WHERE id = {user_input}")
   ✅ GOOD: text("DELETE FROM table WHERE id = :id"), {"id": user_input}

2. **VALIDATE INPUT FIRST**: Ensure user input meets expected format before using it.

3. **USE ORM METHODS**: When possible, use SQLModel's built-in methods (select, delete, etc.)
   instead of raw SQL.

4. **AUDIT REGULARLY**: Any new `text()` usage must be reviewed for SQL injection risks.

Current `text()` usages (all safe):
- Lines 374, 393, 412: DELETE with :issue_id parameter (junction table cleanup)
- Line 604: Static GROUP BY query with no user input (epic counts)

All text() calls are audited in tests/unit/db_issues/test_sqlite.py::TestSQLInjectionSafety.
"""

import logging
import os
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from types import TracebackType

from sqlalchemy import Engine, TypeDecorator, cast, create_engine, text
from sqlalchemy.pool import StaticPool
from sqlmodel import Column, Field, Index, Session, SQLModel, String, select

from dot_work.db_issues.domain.entities import (
    Comment,
    Dependency,
    DependencyType,
    Epic,
    EpicStatus,
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
    Label,
    Project,
    ProjectStatus,
    utcnow_naive,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Types
# =============================================================================


class DateTimeAsISOString(TypeDecorator[datetime]):
    """Custom DateTime type that stores as ISO string and converts transparently.

    This type provides:
    - Automatic conversion from Python datetime to ISO string on write
    - Automatic conversion from ISO string to Python datetime on read
    - Type safety (mypy validates datetime usage)
    - Backward compatibility with existing string-based data

    SQLite doesn't have a native DATETIME type, so we store as ISO 8601 strings
    but provide automatic conversion to maintain type safety throughout the codebase.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: datetime | str | None, dialect) -> str | None:
        """Convert Python datetime to ISO string for database storage.

        Handles both datetime objects and pre-formatted ISO strings for compatibility.
        """
        if value is None:
            return None
        if isinstance(value, str):
            # Already a string (likely from test fixtures or legacy data)
            return value
        return value.isoformat()

    def process_result_value(self, value: str | None, dialect) -> datetime | None:
        """Convert ISO string from database to Python datetime."""
        return datetime.fromisoformat(value) if value else None


# =============================================================================
# Database Models (SQLModel)
# =============================================================================


class IssueModel(SQLModel, table=True):
    """Issue table model.

    Maps to Issue domain entity.
    """

    __tablename__ = "issues"
    __table_args__ = (
        # Composite index for common queries
        Index("ix_issues_status_priority", "status", "priority"),
        Index("ix_issues_project_status", "project_id", "status"),
        Index("ix_issues_created_status", "created_at", "status"),
    )

    id: str = Field(primary_key=True, max_length=50)
    project_id: str = Field(index=True, max_length=50)
    title: str = Field(max_length=500)
    description: str = Field(default="", sa_column=Column(String))
    status: str = Field(max_length=20, index=True)
    priority: int = Field(default=2, index=True)
    type: str = Field(max_length=20, index=True)
    epic_id: str | None = Field(default=None, max_length=50, index=True)
    blocked_reason: str | None = Field(default=None, max_length=1000)
    source_url: str | None = Field(default=None, max_length=2048)
    created_at: datetime = Field(sa_type=DateTimeAsISOString, index=True)
    updated_at: datetime = Field(sa_type=DateTimeAsISOString, index=True)
    closed_at: datetime | None = Field(default=None, sa_type=DateTimeAsISOString, index=True)
    deleted_at: datetime | None = Field(default=None, sa_type=DateTimeAsISOString, index=True)


class LabelModel(SQLModel, table=True):
    """Label table model.

    Maps to Label domain entity.
    """

    __tablename__ = "labels"

    id: str = Field(primary_key=True, max_length=50)
    project_id: str = Field(index=True, max_length=50)
    name: str = Field(max_length=100, index=True)
    color: str | None = Field(default=None, max_length=7)  # Hex color
    created_at: datetime = Field(sa_type=DateTimeAsISOString)


class IssueLabelModel(SQLModel, table=True):
    """Junction table for issue-label many-to-many relationship."""

    __tablename__ = "issue_labels"

    issue_id: str = Field(foreign_key="issues.id", primary_key=True, max_length=50)
    label_name: str = Field(primary_key=True, max_length=100)
    created_at: datetime = Field(sa_type=DateTimeAsISOString)


class IssueAssigneeModel(SQLModel, table=True):
    """Junction table for issue-assignee many-to-many relationship."""

    __tablename__ = "issue_assignees"

    issue_id: str = Field(foreign_key="issues.id", primary_key=True, max_length=50)
    assignee: str = Field(primary_key=True, max_length=100)
    created_at: datetime = Field(sa_type=DateTimeAsISOString)


class IssueReferenceModel(SQLModel, table=True):
    """Junction table for issue-reference many-to-many relationship."""

    __tablename__ = "issue_references"

    issue_id: str = Field(foreign_key="issues.id", primary_key=True, max_length=50)
    reference: str = Field(primary_key=True, max_length=2048)
    created_at: datetime = Field(sa_type=DateTimeAsISOString)


class CommentModel(SQLModel, table=True):
    """Comment table model.

    Maps to Comment domain entity.
    """

    __tablename__ = "comments"

    id: str = Field(primary_key=True, max_length=50)
    issue_id: str = Field(foreign_key="issues.id", index=True, max_length=50)
    author: str = Field(max_length=100, index=True)
    content: str = Field(sa_column=Column(String))
    created_at: datetime = Field(sa_type=DateTimeAsISOString, index=True)
    updated_at: datetime = Field(sa_type=DateTimeAsISOString)


class DependencyModel(SQLModel, table=True):
    """Dependency edge table for issue relationships.

    Maps to Dependency domain entity.
    """

    __tablename__ = "dependencies"
    __table_args__ = (
        # Composite index for dependency graph traversal
        Index("ix_dependencies_from_to", "from_issue_id", "to_issue_id"),
        Index("ix_dependencies_to_type", "to_issue_id", "type"),
    )

    id: str = Field(primary_key=True, max_length=50)
    from_issue_id: str = Field(foreign_key="issues.id", index=True, max_length=50)
    to_issue_id: str = Field(foreign_key="issues.id", index=True, max_length=50)
    type: str = Field(max_length=20, index=True)  # blocks, depends-on, related-to
    created_at: datetime = Field(sa_type=DateTimeAsISOString)


class EpicModel(SQLModel, table=True):
    """Epic table model.

    Maps to Epic domain entity.
    Note: Epics are also stored in issues table with type='epic'
    This table stores epic-specific metadata.
    """

    __tablename__ = "epics"

    id: str = Field(foreign_key="issues.id", primary_key=True, max_length=50)
    project_id: str = Field(index=True, max_length=50)
    status: str = Field(max_length=20, index=True)
    progress: int = Field(default=0)  # 0-100
    parent_epic_id: str | None = Field(default=None, max_length=50, index=True)
    start_date: datetime | None = Field(default=None, sa_type=DateTimeAsISOString)
    target_date: datetime | None = Field(default=None, sa_type=DateTimeAsISOString)
    completed_date: datetime | None = Field(default=None, sa_type=DateTimeAsISOString)


class ProjectModel(SQLModel, table=True):
    """Project table model.

    Maps to Project domain entity.
    """

    __tablename__ = "projects"

    id: str = Field(primary_key=True, max_length=50)
    name: str = Field(max_length=200)
    description: str | None = None
    status: str = Field(default="active", max_length=20, index=True)
    is_default: bool = Field(default=False)
    created_at: datetime = Field(sa_type=DateTimeAsISOString)
    updated_at: datetime = Field(sa_type=DateTimeAsISOString)


# =============================================================================
# Database Engine Factory
# =============================================================================


def _get_default_db_url() -> str:
    """Get default database URL from dot-work config."""
    db_path = Path.cwd() / ".work" / "db-issues.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"


def create_db_engine(db_url: str | None = None, echo: bool = False) -> Engine:
    """Create SQLAlchemy engine for db-issues.

    Args:
        db_url: Database URL. If None, uses default .work/db-issues.db
        echo: Whether to log SQL statements (default: False)

    Returns:
        Configured SQLAlchemy engine

    Examples:
        >>> # Use default database
        >>> engine = create_db_engine()

        >>> # Use custom database
        >>> engine = create_db_engine("sqlite:///./test.db")

        >>> # Use PostgreSQL
        >>> engine = create_db_engine("postgresql://user:pass@localhost/issues")
    """
    if db_url is None:
        db_url = os.environ.get("DB_ISSUES_DB_URL", _get_default_db_url())

    # Use StaticPool for SQLite in-memory databases
    if db_url == "sqlite:///:memory:" or db_url == "sqlite://":
        return create_engine(
            db_url,
            echo=echo,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    # Use default pooling for file-based SQLite and other databases
    if db_url.startswith("sqlite:///"):
        return create_engine(
            db_url,
            echo=echo,
            connect_args={
                "check_same_thread": False,
                "timeout": 30.0,  # Wait up to 30 seconds for database lock
            },
        )

    # PostgreSQL, MySQL, etc.
    return create_engine(db_url, echo=echo)


def get_database_path() -> Path:
    """Get the path to the database file.

    Returns:
        Path to database file, or Path("memory") for in-memory databases

    Raises:
        ValueError: If database URL is not SQLite-based
    """
    db_url = os.environ.get("DB_ISSUES_DB_URL", _get_default_db_url())

    if db_url == "sqlite:///:memory:" or db_url == "sqlite://":
        return Path("memory")

    if db_url.startswith("sqlite:///"):
        # Extract path after sqlite:///
        path_str = db_url[len("sqlite:///") :]
        return Path(path_str)

    raise ValueError(f"Only SQLite databases supported for path extraction: {db_url}")


# =============================================================================
# Repository: Issue
# =============================================================================


class IssueRepository:
    """Repository for Issue entities using SQLModel.

    Provides CRUD operations and advanced querying for issues.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLModel database session for queries
        """
        self.session = session

    def get(self, issue_id: str) -> Issue | None:
        """Retrieve issue by ID.

        Args:
            issue_id: Unique issue identifier

        Returns:
            Issue entity if found and not deleted, None otherwise
        """
        logger.debug("Repository: fetching issue: id=%s", issue_id)
        model = self.session.get(IssueModel, issue_id)
        if model and model.deleted_at is None:
            logger.debug("Repository: issue found: id=%s, title=%s", model.id, model.title)
            return self._model_to_entity(model)
        elif model and model.deleted_at is not None:
            logger.debug("Repository: issue is deleted: id=%s", issue_id)
            return None
        else:
            logger.debug("Repository: issue not found: id=%s", issue_id)
            return None

    def save(self, issue: Issue) -> Issue:
        """Save or update issue.

        Args:
            issue: Issue entity to persist

        Returns:
            Saved issue with updated timestamps
        """
        logger.debug(
            "Repository: saving issue: id=%s, title=%s, labels=%d, assignees=%d",
            issue.id,
            issue.title,
            len(issue.labels),
            len(issue.assignees),
        )
        model = self._entity_to_model(issue)
        merged = self.session.merge(model)
        self.session.flush()

        # Handle labels via junction table
        # Bulk delete existing labels for this issue
        self.session.execute(
            text("DELETE FROM issue_labels WHERE issue_id = :issue_id"), {"issue_id": issue.id}
        )

        # Bulk add new labels
        now = utcnow_naive()
        if issue.labels:
            label_models = [
                IssueLabelModel(
                    issue_id=issue.id,
                    label_name=label_name,
                    created_at=now,
                )
                for label_name in issue.labels
            ]
            self.session.add_all(label_models)

        # Handle assignees via junction table
        # Bulk delete existing assignees for this issue
        self.session.execute(
            text("DELETE FROM issue_assignees WHERE issue_id = :issue_id"), {"issue_id": issue.id}
        )

        # Bulk add new assignees
        if issue.assignees:
            assignee_models = [
                IssueAssigneeModel(
                    issue_id=issue.id,
                    assignee=assignee,
                    created_at=now,
                )
                for assignee in issue.assignees
            ]
            self.session.add_all(assignee_models)

        # Handle references via junction table
        refs = getattr(issue, "references", [])
        # Bulk delete existing references for this issue
        self.session.execute(
            text("DELETE FROM issue_references WHERE issue_id = :issue_id"), {"issue_id": issue.id}
        )

        # Bulk add new references
        if refs:
            ref_models = [
                IssueReferenceModel(
                    issue_id=issue.id,
                    reference=reference,
                    created_at=now,
                )
                for reference in refs
            ]
            self.session.add_all(ref_models)

        self.session.flush()

        self.session.refresh(merged)
        saved_issue = self._model_to_entity(merged)
        logger.debug("Repository: issue saved: id=%s", saved_issue.id)
        return saved_issue

    def delete(self, issue_id: str) -> bool:
        """Soft-delete issue by ID (sets deleted_at timestamp).

        Args:
            issue_id: Unique issue identifier

        Returns:
            True if issue was soft-deleted, False if not found
        """
        logger.debug("Repository: soft-deleting issue: id=%s", issue_id)
        model = self.session.get(IssueModel, issue_id)
        if model:
            model.deleted_at = utcnow_naive()
            self.session.flush()
            logger.info("Repository: issue soft-deleted: id=%s", issue_id)
            return True
        logger.warning("Repository: issue not found for deletion: id=%s", issue_id)
        return False

    def restore(self, issue_id: str) -> bool:
        """Restore soft-deleted issue by clearing deleted_at timestamp.

        Args:
            issue_id: Unique issue identifier

        Returns:
            True if issue was restored, False if not found or not deleted
        """
        logger.debug("Repository: restoring issue: id=%s", issue_id)
        model = self.session.get(IssueModel, issue_id)
        if model and model.deleted_at is not None:
            model.deleted_at = None
            self.session.flush()
            logger.info("Repository: issue restored: id=%s", issue_id)
            return True
        elif model and model.deleted_at is None:
            logger.debug("Repository: issue not deleted, cannot restore: id=%s", issue_id)
            return False
        else:
            logger.warning("Repository: issue not found for restore: id=%s", issue_id)
            return False

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Issue]:
        """List all issues with pagination.

        Args:
            limit: Maximum number of issues to return
            offset: Number of issues to skip

        Returns:
            List of issue entities (excluding soft-deleted)
        """
        statement = (
            select(IssueModel)
            .where(IssueModel.deleted_at.is_(None))  # type: ignore[union-attr]
            .limit(limit)
            .offset(offset)
        )
        models = self.session.exec(statement).all()
        return self._models_to_entities(models)

    def list_deleted(self, limit: int = 100, offset: int = 0) -> list[Issue]:
        """List soft-deleted issues with pagination.

        Args:
            limit: Maximum number of issues to return
            offset: Number of issues to skip

        Returns:
            List of soft-deleted issue entities
        """
        statement = (
            select(IssueModel)
            .where(IssueModel.deleted_at.is_not(None))  # type: ignore[union-attr]
            .limit(limit)
            .offset(offset)
        )
        models = self.session.exec(statement).all()
        return self._models_to_entities(models)

    def list_by_status(self, status: IssueStatus, limit: int = 100, offset: int = 0) -> list[Issue]:
        """List issues filtered by status.

        Args:
            status: Issue status to filter by
            limit: Maximum number of issues to return
            offset: Number of issues to skip

        Returns:
            List of issues matching status (excluding soft-deleted)
        """
        statement = (
            select(IssueModel)
            .where(IssueModel.status == status.value)
            .where(IssueModel.deleted_at.is_(None))  # type: ignore[union-attr]
            .limit(limit)
            .offset(offset)
        )
        models = self.session.exec(statement).all()
        return self._models_to_entities(models)

    def list_by_priority(
        self, priority: IssuePriority, limit: int = 100, offset: int = 0
    ) -> list[Issue]:
        """List issues filtered by priority.

        Args:
            priority: Issue priority to filter by
            limit: Maximum number of issues to return
            offset: Number of issues to skip

        Returns:
            List of issues matching priority
        """
        statement = (
            select(IssueModel)
            .where(IssueModel.priority == priority.value)
            .limit(limit)
            .offset(offset)
        )
        models = self.session.exec(statement).all()
        return self._models_to_entities(models)

    def list_by_assignee(self, assignee: str, limit: int = 100, offset: int = 0) -> list[Issue]:
        """List issues filtered by assignee.

        Args:
            assignee: Username to filter by
            limit: Maximum number of issues to return
            offset: Number of issues to skip

        Returns:
            List of issues assigned to user
        """
        statement = (
            select(IssueModel).where(IssueModel.assignee == assignee).limit(limit).offset(offset)  # type: ignore[attr-defined]
        )
        models = self.session.exec(statement).all()
        return self._models_to_entities(models)

    def list_by_epic(self, epic_id: str, limit: int = 100, offset: int = 0) -> list[Issue]:
        """List issues belonging to an epic.

        Args:
            epic_id: Epic identifier to filter by
            limit: Maximum number of issues to return
            offset: Number of issues to skip

        Returns:
            List of issues in epic
        """
        statement = (
            select(IssueModel).where(IssueModel.epic_id == epic_id).limit(limit).offset(offset)
        )
        models = self.session.exec(statement).all()
        return self._models_to_entities(models)

    def get_epic_counts(self) -> dict[str, dict[str, int]]:
        """Get issue counts grouped by epic_id and status using SQL aggregation.

        Returns a dict like: {
            "EPIC-001": {"total": 10, "proposed": 3, "in_progress": 4, "completed": 3},
            ...
        }

        This uses SQL GROUP BY for efficient counting without loading all issues.
        """
        from sqlmodel import text

        result = self.session.exec(
            text("""
            SELECT
                epic_id,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'proposed' THEN 1 ELSE 0 END) as proposed,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM issues
            WHERE epic_id IS NOT NULL AND deleted_at IS NULL
            GROUP BY epic_id
        """)  # type: ignore[call-overload]
        )

        epic_counts: dict[str, dict[str, int]] = {}
        for row in result:
            epic_counts[row.epic_id] = {
                "total": row.total,
                "proposed": row.proposed,
                "in_progress": row.in_progress,
                "completed": row.completed,
            }
        return epic_counts

    def list_by_type(self, issue_type: IssueType, limit: int = 100, offset: int = 0) -> list[Issue]:
        """List issues filtered by type.

        Args:
            issue_type: Issue type to filter by
            limit: Maximum number of issues to return
            offset: Number of issues to skip

        Returns:
            List of issues matching type
        """
        statement = (
            select(IssueModel)
            .where(IssueModel.type == issue_type.value)
            .limit(limit)
            .offset(offset)
        )
        models = self.session.exec(statement).all()
        return self._models_to_entities(models)

    def list_by_project(self, project_id: str, limit: int = 100, offset: int = 0) -> list[Issue]:
        """List issues filtered by project.

        Args:
            project_id: Project identifier to filter by
            limit: Maximum number of issues to return
            offset: Number of issues to skip

        Returns:
            List of issues in the project
        """
        statement = (
            select(IssueModel)
            .where(IssueModel.project_id == project_id)
            .where(IssueModel.deleted_at.is_(None))  # type: ignore[union-attr]
            .limit(limit)
            .offset(offset)
        )
        models = self.session.exec(statement).all()
        return self._models_to_entities(models)

    def list_updated_before(
        self, cutoff: datetime, limit: int = 100, offset: int = 0
    ) -> list[Issue]:
        """List issues updated before a cutoff date.

        Args:
            cutoff: Cutoff datetime - only return issues updated before this time
            limit: Maximum number of issues to return
            offset: Number of issues to skip

        Returns:
            List of issues updated before cutoff, sorted by updated_at ascending
        """
        statement = (
            select(IssueModel)
            .where(IssueModel.updated_at < cutoff)
            .where(IssueModel.deleted_at.is_(None))  # type: ignore[union-attr]
            .order_by(cast(IssueModel.updated_at, String))
            .limit(limit)
            .offset(offset)
        )
        models = self.session.exec(statement).all()
        return self._models_to_entities(models)

    def _entity_to_model(self, issue: Issue) -> IssueModel:
        """Convert Issue entity to database model.

        Args:
            issue: Issue entity to convert

        Returns:
            IssueModel for database persistence
        """
        return IssueModel(
            id=issue.id,
            project_id=getattr(issue, "project_id", "default"),
            title=issue.title,
            description=issue.description or "",
            status=issue.status.value,
            priority=issue.priority.value,
            type=issue.type.value,
            epic_id=issue.epic_id,
            blocked_reason=issue.blocked_reason,
            source_url=getattr(issue, "source_url", None),
            created_at=str(issue.created_at),
            updated_at=str(issue.updated_at),
            closed_at=str(issue.closed_at) if issue.closed_at else None,
            deleted_at=str(issue.deleted_at) if issue.deleted_at else None,
        )

    def _model_to_entity(self, model: IssueModel) -> Issue:
        """Convert database model to Issue entity.

        Args:
            model: IssueModel from database

        Returns:
            Issue domain entity
        """
        # Load labels from junction table
        statement = select(IssueLabelModel).where(IssueLabelModel.issue_id == model.id)
        label_models = self.session.exec(statement).all()
        labels = [label_model.label_name for label_model in label_models]

        # Load assignees from junction table
        assignee_statement = select(IssueAssigneeModel).where(
            IssueAssigneeModel.issue_id == model.id
        )
        assignee_models = self.session.exec(assignee_statement).all()
        assignees = [assignee_model.assignee for assignee_model in assignee_models]

        # Load references from junction table
        ref_statement = select(IssueReferenceModel).where(IssueReferenceModel.issue_id == model.id)
        ref_models = self.session.exec(ref_statement).all()
        references = [ref_model.reference for ref_model in ref_models]

        return Issue(
            id=model.id,
            project_id=model.project_id,
            title=model.title,
            description=model.description or "",
            status=IssueStatus(model.status),
            priority=IssuePriority(model.priority),
            type=IssueType(model.type),
            assignees=assignees,
            epic_id=model.epic_id,
            labels=labels,
            blocked_reason=model.blocked_reason,
            source_url=model.source_url,
            references=references,
            created_at=model.created_at or utcnow_naive(),
            updated_at=model.updated_at or utcnow_naive(),
            closed_at=model.closed_at,
            deleted_at=model.deleted_at,
        )

    def _models_to_entities(self, models: Sequence[IssueModel]) -> list[Issue]:
        """Convert multiple database models to Issue entities efficiently.

        Batch-loads labels and assignees to avoid N+1 queries.

        Args:
            models: Sequence of IssueModels from database

        Returns:
            List of Issue domain entities
        """
        if not models:
            return []

        issue_ids: list[str] = [model.id for model in models]

        # Batch-load all labels for these issues
        issue_id_col = IssueLabelModel.issue_id
        statement = select(IssueLabelModel).where(issue_id_col.in_(issue_ids))  # type: ignore[attr-defined]
        label_models = self.session.exec(statement).all()

        # Group labels by issue_id
        labels_by_issue: dict[str, list[str]] = {}
        for label_model in label_models:
            if label_model.issue_id not in labels_by_issue:
                labels_by_issue[label_model.issue_id] = []
            labels_by_issue[label_model.issue_id].append(label_model.label_name)

        # Batch-load all assignees for these issues
        issue_id_col = IssueAssigneeModel.issue_id
        assignee_statement = select(IssueAssigneeModel).where(issue_id_col.in_(issue_ids))  # type: ignore[attr-defined]
        assignee_models = self.session.exec(assignee_statement).all()

        # Group assignees by issue_id
        assignees_by_issue: dict[str, list[str]] = {}
        for assignee_model in assignee_models:
            if assignee_model.issue_id not in assignees_by_issue:
                assignees_by_issue[assignee_model.issue_id] = []
            assignees_by_issue[assignee_model.issue_id].append(assignee_model.assignee)

        # Batch-load all references for these issues
        issue_id_col = IssueReferenceModel.issue_id
        ref_statement = select(IssueReferenceModel).where(issue_id_col.in_(issue_ids))  # type: ignore[attr-defined]
        ref_models = self.session.exec(ref_statement).all()

        # Group references by issue_id
        refs_by_issue: dict[str, list[str]] = {}
        for ref_model in ref_models:
            if ref_model.issue_id not in refs_by_issue:
                refs_by_issue[ref_model.issue_id] = []
            refs_by_issue[ref_model.issue_id].append(ref_model.reference)

        # Convert models to entities with batched labels, assignees, and references
        entities = []
        for model in models:
            labels = labels_by_issue.get(model.id, [])
            assignees = assignees_by_issue.get(model.id, [])
            references = refs_by_issue.get(model.id, [])

            entity = Issue(
                id=model.id,
                project_id=model.project_id,
                title=model.title,
                description=model.description or "",
                status=IssueStatus(model.status),
                priority=IssuePriority(model.priority),
                type=IssueType(model.type),
                assignees=assignees,
                epic_id=model.epic_id,
                labels=labels,
                blocked_reason=model.blocked_reason,
                source_url=model.source_url,
                references=references,
                created_at=model.created_at or utcnow_naive(),
                updated_at=model.updated_at or utcnow_naive(),
                closed_at=model.closed_at,
                deleted_at=model.deleted_at,
            )
            entities.append(entity)

        return entities


# =============================================================================
# Repository: Comment
# =============================================================================


class CommentRepository:
    """Repository for Comment entities using SQLModel.

    Provides CRUD operations for issue comments.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLModel database session for queries
        """
        self.session = session

    def get(self, comment_id: str) -> Comment | None:
        """Retrieve comment by ID.

        Args:
            comment_id: Unique comment identifier

        Returns:
            Comment entity if found, None otherwise
        """
        model = self.session.get(CommentModel, comment_id)
        return self._model_to_entity(model) if model else None

    def save(self, comment: Comment) -> Comment:
        """Save or update comment.

        Args:
            comment: Comment entity to persist

        Returns:
            Saved comment with updated timestamps
        """
        logger.debug(
            "Repository: saving comment: id=%s, issue_id=%s, author=%s",
            comment.id,
            comment.issue_id,
            comment.author,
        )
        model = self._entity_to_model(comment)
        merged = self.session.merge(model)
        self.session.flush()
        self.session.refresh(merged)
        saved_comment = self._model_to_entity(merged)
        logger.debug("Repository: comment saved: id=%s", saved_comment.id)
        return saved_comment

    def delete(self, comment_id: str) -> bool:
        """Delete comment by ID.

        Args:
            comment_id: Unique comment identifier

        Returns:
            True if comment was deleted, False if not found
        """
        logger.debug("Repository: deleting comment: id=%s", comment_id)
        model = self.session.get(CommentModel, comment_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            logger.info("Repository: comment deleted: id=%s", comment_id)
            return True
        logger.warning("Repository: comment not found for deletion: id=%s", comment_id)
        return False

    def list_by_issue(self, issue_id: str) -> list[Comment]:
        """List all comments for an issue.

        Args:
            issue_id: Issue identifier to get comments for

        Returns:
            List of comments ordered by creation time
        """
        logger.debug("Repository: listing comments for issue: id=%s", issue_id)
        statement = (
            select(CommentModel)
            .where(CommentModel.issue_id == issue_id)
            .order_by(CommentModel.created_at)  # type: ignore[arg-type]
        )
        models = self.session.exec(statement).all()
        logger.debug("Repository: found %d comments for issue: id=%s", len(models), issue_id)
        return [self._model_to_entity(model) for model in models]

    def list_by_author(self, author: str, limit: int = 100, offset: int = 0) -> list[Comment]:
        """List comments by author.

        Args:
            author: Author username to filter by
            limit: Maximum number of comments to return
            offset: Number of comments to skip

        Returns:
            List of comments by author
        """
        statement = (
            select(CommentModel)
            .where(CommentModel.author == author)
            .order_by(CommentModel.created_at.desc())  # type: ignore
            .limit(limit)
            .offset(offset)
        )
        models = self.session.exec(statement).all()
        return [self._model_to_entity(model) for model in models]

    def _entity_to_model(self, comment: Comment) -> CommentModel:
        """Convert Comment entity to database model.

        Args:
            comment: Comment entity to convert

        Returns:
            CommentModel for database persistence
        """
        return CommentModel(
            id=comment.id,
            issue_id=comment.issue_id,
            author=comment.author,
            content=comment.text,
            created_at=str(comment.created_at),
            updated_at=str(comment.updated_at),
        )

    def _model_to_entity(self, model: CommentModel) -> Comment:
        """Convert database model to Comment entity.

        Args:
            model: CommentModel from database

        Returns:
            Comment domain entity
        """
        return Comment(
            id=model.id,
            issue_id=model.issue_id,
            author=model.author,
            text=model.content,
            created_at=model.created_at or utcnow_naive(),
            updated_at=model.updated_at or utcnow_naive(),
        )


# =============================================================================
# Repository: Issue Graph (Dependencies)
# =============================================================================


class IssueGraphRepository:
    """Repository for issue dependency graph operations.

    Manages dependency edges between issues with cycle detection.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLModel database session for queries
        """
        self.session = session

    def add_dependency(self, dependency: Dependency) -> Dependency:
        """Add a dependency edge.

        Args:
            dependency: Dependency entity to persist

        Returns:
            Saved dependency with generated ID
        """
        model = self._entity_to_model(dependency)
        self.session.add(model)
        self.session.flush()
        self.session.refresh(model)
        return self._model_to_entity(model)

    def remove_dependency(
        self, from_issue_id: str, to_issue_id: str, dependency_type: DependencyType
    ) -> bool:
        """Remove a dependency edge.

        Args:
            from_issue_id: Source issue identifier
            to_issue_id: Target issue identifier
            dependency_type: Type of dependency relationship

        Returns:
            True if dependency was removed, False if not found
        """
        statement = select(DependencyModel).where(
            DependencyModel.from_issue_id == from_issue_id,
            DependencyModel.to_issue_id == to_issue_id,
            DependencyModel.type == dependency_type.value,
        )
        model = self.session.exec(statement).first()
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def get_dependencies(self, issue_id: str) -> list[Dependency]:
        """Get all outgoing dependencies (this issue depends on...).

        Args:
            issue_id: Issue identifier

        Returns:
            List of outgoing dependency edges
        """
        statement = select(DependencyModel).where(DependencyModel.from_issue_id == issue_id)
        models = self.session.exec(statement).all()
        return [self._model_to_entity(model) for model in models]

    def get_dependents(self, issue_id: str) -> list[Dependency]:
        """Get all incoming dependencies (...depend on this issue).

        Args:
            issue_id: Issue identifier

        Returns:
            List of incoming dependency edges
        """
        statement = select(DependencyModel).where(DependencyModel.to_issue_id == issue_id)
        models = self.session.exec(statement).all()
        return [self._model_to_entity(model) for model in models]

    def get_blockers(self, issue_id: str) -> list[str]:
        """Get all issue IDs that block this issue.

        Args:
            issue_id: Issue identifier

        Returns:
            List of issue IDs blocking this issue
        """
        statement = select(DependencyModel).where(
            DependencyModel.to_issue_id == issue_id,
            DependencyModel.type == DependencyType.BLOCKS.value,
        )
        models = self.session.exec(statement).all()
        return [model.from_issue_id for model in models]

    def get_blocked_by(self, issue_id: str) -> list[str]:
        """Get all issue IDs blocked by this issue.

        Args:
            issue_id: Issue identifier

        Returns:
            List of issue IDs blocked by this issue
        """
        statement = select(DependencyModel).where(
            DependencyModel.from_issue_id == issue_id,
            DependencyModel.type == DependencyType.BLOCKS.value,
        )
        models = self.session.exec(statement).all()
        return [model.to_issue_id for model in models]

    def has_cycle(self, from_issue_id: str, to_issue_id: str) -> bool:
        """Check if adding edge would create cycle using DFS.

        Args:
            from_issue_id: Source issue identifier
            to_issue_id: Target issue identifier

        Returns:
            True if adding edge creates cycle, False otherwise
        """
        # Special case: self-loop is always a cycle
        if from_issue_id == to_issue_id:
            return True

        # Load ALL dependencies in a single query to avoid N+1 problem
        # This is O(1) queries instead of O(N) queries
        statement = select(DependencyModel)
        models = self.session.exec(statement).all()

        # Build in-memory adjacency list for O(1) lookup
        from collections import defaultdict

        adjacency = defaultdict(list)
        for model in models:
            adjacency[model.from_issue_id].append(model.to_issue_id)

        # DFS in-memory (no database queries)
        visited: set[str] = set()

        def dfs(current: str) -> bool:
            """Depth-first search to detect cycles.

            Runs entirely in-memory using the pre-built adjacency list.
            """
            if current == from_issue_id:
                return True
            if current in visited:
                return False
            visited.add(current)

            # Check all neighbors in-memory
            for neighbor in adjacency.get(current, []):
                if dfs(neighbor):
                    return True

            return False

        return dfs(to_issue_id)

    def get_all_dependencies(self) -> list[Dependency]:
        """Get all dependencies in the system.

        Returns:
            List of all dependency relationships
        """
        statement = select(DependencyModel)
        models = self.session.exec(statement).all()
        return [self._model_to_entity(model) for model in models]

    def _entity_to_model(self, dependency: Dependency) -> DependencyModel:
        """Convert Dependency entity to database model.

        Args:
            dependency: Dependency entity to convert

        Returns:
            DependencyModel for database persistence
        """
        # Generate ID from issue IDs + type
        dep_id = (
            str(dependency.id)
            if dependency.id
            else f"{dependency.from_issue_id[:8]}{dependency.to_issue_id[:8]}{dependency.dependency_type.value[:5]}"
        )
        return DependencyModel(
            id=dep_id,
            from_issue_id=dependency.from_issue_id,
            to_issue_id=dependency.to_issue_id,
            type=dependency.dependency_type.value,
            created_at=str(dependency.created_at),
        )

    def _model_to_entity(self, model: DependencyModel) -> Dependency:
        """Convert database model to Dependency entity.

        Args:
            model: DependencyModel from database

        Returns:
            Dependency domain entity
        """
        return Dependency(
            from_issue_id=model.from_issue_id,
            to_issue_id=model.to_issue_id,
            dependency_type=DependencyType(model.type),
            id=None,  # Entity uses int, model uses string
            description=None,  # Not stored in DB currently
            created_at=utcnow_naive(),
        )


# =============================================================================
# Repository: Epic
# =============================================================================


class EpicRepository:
    """Repository for Epic entity operations.

    Manages epics which span both issues and epics tables.
    The issues table stores core epic data (title, description).
    The epics table stores epic-specific metadata (status, parent, dates).
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLModel database session for queries
        """
        self.session = session

    def get(self, epic_id: str) -> Epic | None:
        """Get epic by ID.

        Args:
            epic_id: Epic identifier

        Returns:
            Epic entity if found, None otherwise
        """
        # Join issues and epics tables
        statement = (
            select(IssueModel, EpicModel)
            .join(EpicModel, IssueModel.id == EpicModel.id)  # type: ignore[arg-type]
            .where(IssueModel.id == epic_id)
        )
        result = self.session.exec(statement).first()
        if not result:
            return None
        issue_model, epic_model = result
        return self._models_to_entity(issue_model, epic_model)

    def save(self, epic: Epic) -> Epic:
        """Save epic to database.

        Updates or creates records in both issues and epics tables.

        Args:
            epic: Epic entity to persist

        Returns:
            Saved epic entity
        """
        # Check if issue exists
        issue_model = self.session.get(IssueModel, epic.id)
        epic_model = self.session.get(EpicModel, epic.id)

        if issue_model and epic_model:
            # Update existing
            issue_model.title = epic.title
            issue_model.description = epic.description or ""
            issue_model.updated_at = epic.updated_at
            if epic.closed_at:
                issue_model.closed_at = epic.closed_at

            epic_model.status = epic.status.value
            epic_model.parent_epic_id = epic.parent_epic_id
            if epic.closed_at:
                epic_model.completed_date = epic.closed_at

            self.session.flush()
            self.session.refresh(issue_model)
            self.session.refresh(epic_model)
            return self._models_to_entity(issue_model, epic_model)
        else:
            # Create new
            # Note: Epic data spans both issues and epics tables
            # - issues table: core data (title, description) - uses valid IssueType/IssueStatus
            # - epics table: epic-specific metadata (epic status, parent, etc.)
            new_issue = IssueModel(
                id=epic.id,
                title=epic.title,
                description=epic.description or "",
                status="proposed",  # Use neutral IssueStatus for epic in issues table
                priority=3,  # MEDIUM default
                type="task",  # Use valid IssueType - epic metadata in EpicModel
                project_id="default",
                created_at=epic.created_at,
                updated_at=epic.updated_at,
                closed_at=epic.closed_at,
            )
            new_epic = EpicModel(
                id=epic.id,
                project_id="default",
                status=epic.status.value,
                parent_epic_id=epic.parent_epic_id,
                completed_date=epic.closed_at,
            )

            self.session.add(new_issue)
            self.session.add(new_epic)
            self.session.flush()
            self.session.refresh(new_issue)
            self.session.refresh(new_epic)
            return self._models_to_entity(new_issue, new_epic)

    def delete(self, epic_id: str) -> bool:
        """Delete epic by ID.

        Removes from both issues and epics tables.

        Args:
            epic_id: Epic identifier

        Returns:
            True if epic was deleted, False if not found
        """
        issue_model = self.session.get(IssueModel, epic_id)
        epic_model = self.session.get(EpicModel, epic_id)

        if not issue_model or not epic_model:
            return False

        self.session.delete(epic_model)
        self.session.delete(issue_model)
        self.session.flush()
        return True

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Epic]:
        """List all epics with pagination.

        Args:
            limit: Maximum number of epics to return
            offset: Number of epics to skip

        Returns:
            List of epic entities
        """
        # Join issues and epics tables - the join identifies epics
        statement = (
            select(IssueModel, EpicModel)
            .join(EpicModel, IssueModel.id == EpicModel.id)  # type: ignore[arg-type]
            .order_by(IssueModel.created_at.desc())  # type: ignore[attr-defined]
            .offset(offset)
            .limit(limit)
        )
        results = self.session.exec(statement).all()
        return [self._models_to_entity(im, em) for im, em in results]

    def get_by_status(self, status: EpicStatus) -> list[Epic]:
        """Get all epics with given status.

        Args:
            status: Epic status to filter by

        Returns:
            List of epic entities with matching status
        """
        statement = (
            select(IssueModel, EpicModel)
            .join(EpicModel, IssueModel.id == EpicModel.id)  # type: ignore[arg-type]
            .where(EpicModel.status == status.value)
        )
        results = self.session.exec(statement).all()
        return [self._models_to_entity(im, em) for im, em in results]

    def get_child_epics(self, parent_epic_id: str) -> list[Epic]:
        """Get all child epics of a parent epic.

        Args:
            parent_epic_id: Parent epic identifier

        Returns:
            List of child epic entities
        """
        statement = (
            select(IssueModel, EpicModel)
            .join(EpicModel, IssueModel.id == EpicModel.id)  # type: ignore[arg-type]
            .where(EpicModel.parent_epic_id == parent_epic_id)
        )
        results = self.session.exec(statement).all()
        return [self._models_to_entity(im, em) for im, em in results]

    def _models_to_entity(self, issue_model: IssueModel, epic_model: EpicModel) -> Epic:
        """Convert database models to Epic entity.

        Args:
            issue_model: IssueModel from issues table
            epic_model: EpicModel from epics table

        Returns:
            Epic domain entity
        """
        closed_at = issue_model.closed_at or epic_model.completed_date

        return Epic(
            id=issue_model.id,
            title=issue_model.title,
            description=issue_model.description if issue_model.description else None,
            status=EpicStatus(epic_model.status),
            parent_epic_id=epic_model.parent_epic_id,
            created_at=issue_model.created_at or utcnow_naive(),
            updated_at=issue_model.updated_at or utcnow_naive(),
            closed_at=closed_at,
        )


# =============================================================================
# Repository: Label
# =============================================================================


class LabelRepository:
    """Repository for Label entity operations.

    Manages predefined labels with colors for categorizing issues.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLModel database session for queries
        """
        self.session = session

    def get(self, label_id: str) -> Label | None:
        """Get label by ID.

        Args:
            label_id: Label identifier

        Returns:
            Label entity if found, None otherwise
        """
        model = self.session.get(LabelModel, label_id)
        return self._model_to_entity(model) if model else None

    def get_by_name(self, name: str, project_id: str = "default") -> Label | None:
        """Get label by name.

        Args:
            name: Label name
            project_id: Project identifier (default: "default")

        Returns:
            Label entity if found, None otherwise
        """
        statement = select(LabelModel).where(
            LabelModel.name == name,
            LabelModel.project_id == project_id,
        )
        model = self.session.exec(statement).first()
        return self._model_to_entity(model) if model else None

    def list_all(self, project_id: str = "default") -> list[Label]:
        """List all labels in project.

        Args:
            project_id: Project identifier (default: "default")

        Returns:
            List of all label entities
        """
        statement = select(LabelModel).where(LabelModel.project_id == project_id)
        models = self.session.exec(statement).all()
        return [self._model_to_entity(m) for m in models]

    def list_unused(self, project_id: str = "default") -> list[Label]:
        """List labels not used by any issue.

        Args:
            project_id: Project identifier (default: "default")

        Returns:
            List of unused label entities
        """
        # Get all labels
        statement = select(LabelModel).where(LabelModel.project_id == project_id)
        all_labels = self.session.exec(statement).all()

        # Get all used label names
        used_statement = select(IssueLabelModel.label_name).distinct()
        used_names = {row[0] for row in self.session.exec(used_statement).all()}

        # Filter unused
        unused = [self._model_to_entity(m) for m in all_labels if m.name not in used_names]
        return unused

    def save(self, label: Label) -> Label:
        """Save label to database.

        Args:
            label: Label entity to persist

        Returns:
            Saved label entity
        """
        model = self.session.get(LabelModel, label.id)

        if model:
            # Update existing
            model.name = label.name
            model.color = label.color
            model.updated_at = str(label.updated_at)
        else:
            # Create new
            model = LabelModel(
                id=label.id,
                project_id="default",  # Default project
                name=label.name,
                color=label.color,
                created_at=str(label.created_at),
            )
            self.session.add(model)

        self.session.flush()
        self.session.refresh(model)
        return self._model_to_entity(model)

    def delete(self, label_id: str) -> bool:
        """Delete label from database.

        Args:
            label_id: Label identifier

        Returns:
            True if deleted, False if not found
        """
        model = self.session.get(LabelModel, label_id)
        if model:
            self.session.delete(model)
            return True
        return False

    def rename(self, label_id: str, new_name: str) -> Label | None:
        """Rename a label.

        Args:
            label_id: Label identifier
            new_name: New label name

        Returns:
            Updated label entity, or None if not found
        """
        model = self.session.get(LabelModel, label_id)
        if model:
            model.name = new_name
            self.session.flush()
            self.session.refresh(model)
            return self._model_to_entity(model)
        return None

    def _model_to_entity(self, model: LabelModel) -> Label:
        """Convert database model to Label entity.

        Args:
            model: LabelModel from database

        Returns:
            Label domain entity
        """
        return Label(
            id=model.id,
            name=model.name,
            color=model.color,
            description=None,  # Not stored in DB currently
            created_at=model.created_at or utcnow_naive(),
            updated_at=utcnow_naive(),
        )


class ProjectRepository:
    """Repository for Project entity operations.

    Manages projects for organizing issues.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLModel database session for queries
        """
        self.session = session

    def get(self, project_id: str) -> Project | None:
        """Get project by ID.

        Args:
            project_id: Project identifier

        Returns:
            Project entity if found, None otherwise
        """
        model = self.session.get(ProjectModel, project_id)
        return self._model_to_entity(model) if model else None

    def get_default(self) -> Project | None:
        """Get the default project.

        Returns:
            Default project entity if found, None otherwise
        """
        statement = select(ProjectModel).where(ProjectModel.is_default)
        model = self.session.exec(statement).first()
        return self._model_to_entity(model) if model else None

    def list_all(self) -> list[Project]:
        """List all projects.

        Returns:
            List of all project entities
        """
        statement = select(ProjectModel).order_by(ProjectModel.name)
        models = self.session.exec(statement).all()
        return [self._model_to_entity(m) for m in models]

    def list_by_status(self, status: ProjectStatus) -> list[Project]:
        """List projects by status.

        Args:
            status: Project status to filter by

        Returns:
            List of project entities with specified status
        """
        statement = (
            select(ProjectModel)
            .where(ProjectModel.status == status.value)
            .order_by(ProjectModel.name)
        )
        models = self.session.exec(statement).all()
        return [self._model_to_entity(m) for m in models]

    def save(self, project: Project) -> Project:
        """Save project to database.

        Args:
            project: Project entity to persist

        Returns:
            Saved project entity
        """
        model = self.session.get(ProjectModel, project.id)

        if model:
            # Update existing
            model.name = project.name
            model.description = project.description
            model.status = project.status.value
            model.is_default = project.is_default
            model.updated_at = project.updated_at
        else:
            # Create new
            model = ProjectModel(
                id=project.id,
                name=project.name,
                description=project.description,
                status=project.status.value,
                is_default=project.is_default,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
            self.session.add(model)

        self.session.flush()
        self.session.refresh(model)
        return self._model_to_entity(model)

    def delete(self, project_id: str) -> bool:
        """Delete project from database.

        Args:
            project_id: Project identifier

        Returns:
            True if deleted, False if not found
        """
        model = self.session.get(ProjectModel, project_id)
        if model:
            self.session.delete(model)
            return True
        return False

    def set_default(self, project_id: str) -> Project | None:
        """Set a project as the default.

        Unsets is_default on all other projects.

        Args:
            project_id: Project identifier to set as default

        Returns:
            Updated project entity, or None if not found
        """
        # Clear default flag from all projects
        statement = select(ProjectModel).where(ProjectModel.is_default)
        default_models = self.session.exec(statement).all()
        for default_model in default_models:
            default_model.is_default = False

        # Set new default
        model = self.session.get(ProjectModel, project_id)
        if model:
            model.is_default = True
            self.session.flush()
            self.session.refresh(model)
            return self._model_to_entity(model)
        return None

    def _model_to_entity(self, model: ProjectModel) -> Project:
        """Convert database model to Project entity.

        Args:
            model: ProjectModel from database

        Returns:
            Project domain entity
        """
        return Project(
            id=model.id,
            name=model.name,
            description=model.description,
            status=ProjectStatus(model.status),
            is_default=model.is_default,
            created_at=model.created_at or utcnow_naive(),
            updated_at=model.updated_at or utcnow_naive(),
        )


# =============================================================================
# Unit of Work
# =============================================================================


class UnitOfWork:
    """Unit of Work for managing database transactions.

    Provides transaction boundaries and lazy-loaded repositories.
    Automatically commits on successful completion or rolls back on exceptions.

    Examples:
        >>> from sqlmodel import Session, create_engine
        >>> engine = create_engine("sqlite:///./issues.db")
        >>> session = Session(engine)
        >>>
        >>> # Use as context manager
        >>> with UnitOfWork(session) as uow:
        ...     issue = uow.issues.get("issue-123")
        ...     issue.status = IssueStatus.CLOSED
        ...     uow.issues.save(issue)
        ...     # Automatically commits on success

        >>> # Rollback on exception
        >>> try:
        ...     with UnitOfWork(session) as uow:
        ...         issue = uow.issues.get("issue-123")
        ...         raise ValueError("Something went wrong")
        ... except ValueError:
        ...     pass  # Transaction rolled back automatically
    """

    def __init__(self, session: Session) -> None:
        """Initialize with database session.

        Args:
            session: SQLModel database session for queries and transactions
        """
        self._session = session
        self._in_transaction = False
        self._issues: IssueRepository | None = None
        self._comments: CommentRepository | None = None
        self._graph: IssueGraphRepository | None = None
        self._epics: EpicRepository | None = None
        self._labels: LabelRepository | None = None
        self._projects: ProjectRepository | None = None

    @property
    def session(self) -> Session:
        """Get the underlying database session.

        Provides access for services that need direct SQL execution
        (e.g., SearchService with FTS5 queries).

        Returns:
            The SQLModel session.
        """
        return self._session

    def __enter__(self) -> "UnitOfWork":
        """Begin transaction.

        Returns:
            Self for context manager pattern
        """
        logger.debug("Entering transaction context")
        self._in_transaction = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """End transaction - commit on success, rollback on exception.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception instance if raised
            exc_tb: Exception traceback if raised
        """
        if exc_type is not None:
            logger.warning("Transaction error, rolling back: %s", exc_type.__name__)
            self.rollback()
        else:
            if self._in_transaction:
                logger.debug("Committing transaction")
                self.commit()
        self._in_transaction = False

    def commit(self) -> None:
        """Commit current transaction.

        Persists all changes made within the transaction to the database.
        """
        logger.debug("Committing database transaction")
        self._session.commit()
        logger.debug("Transaction committed successfully")

    def rollback(self) -> None:
        """Rollback current transaction.

        Discards all changes made within the transaction.
        """
        if self._in_transaction:
            logger.warning("Rolling back database transaction")
            self._session.rollback()
            logger.debug("Transaction rolled back")

    @property
    def issues(self) -> IssueRepository:
        """Lazy-load issue repository.

        Returns:
            Issue repository instance
        """
        if self._issues is None:
            self._issues = IssueRepository(self.session)
        return self._issues

    @property
    def comments(self) -> CommentRepository:
        """Lazy-load comment repository.

        Returns:
            Comment repository instance
        """
        if self._comments is None:
            self._comments = CommentRepository(self.session)
        return self._comments

    @property
    def graph(self) -> IssueGraphRepository:
        """Lazy-load issue graph repository.

        Returns:
            Issue graph repository instance for dependency management
        """
        if self._graph is None:
            self._graph = IssueGraphRepository(self.session)
        return self._graph

    @property
    def epics(self) -> EpicRepository:
        """Lazy-load epic repository.

        Returns:
            Epic repository instance for epic management
        """
        if self._epics is None:
            self._epics = EpicRepository(self.session)
        return self._epics

    @property
    def labels(self) -> LabelRepository:
        """Lazy-load label repository.

        Returns:
            Label repository instance for label management
        """
        if self._labels is None:
            self._labels = LabelRepository(self.session)
        return self._labels

    @property
    def projects(self) -> ProjectRepository:
        """Lazy-load project repository.

        Returns:
            Project repository instance for project management
        """
        if self._projects is None:
            self._projects = ProjectRepository(self.session)
        return self._projects

    def close(self) -> None:
        """Close the underlying session.

        CRITICAL: Must be called to prevent memory leaks when UnitOfWork
        is not used as a context manager.
        """
        try:
            self.session.close()
        except Exception as e:
            logger.warning("Failed to close session: %s", e)

        # Clear repository references to release cached data
        self._issues = None
        self._comments = None
        self._graph = None
        self._epics = None
        self._labels = None
        self._projects = None

    def __del__(self) -> None:
        """Ensure session cleanup on garbage collection."""
        self.close()


# =============================================================================
# Public Exports
# =============================================================================

__all__ = [
    # Models
    "IssueModel",
    "LabelModel",
    "IssueLabelModel",
    "CommentModel",
    "DependencyModel",
    "EpicModel",
    "ProjectModel",
    # Engine
    "create_db_engine",
    "get_database_path",
    # Repositories
    "IssueRepository",
    "CommentRepository",
    "IssueGraphRepository",
    "EpicRepository",
    "LabelRepository",
    "ProjectRepository",
    # Unit of Work
    "UnitOfWork",
]
