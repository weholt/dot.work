Database-backed issue tracking for dot-work.

This module provides a complete issue tracking system with:
- Domain entities (Issue, Comment, Dependency, Epic, Label)
- SQLite persistence with SQLModel
- Business logic services
- Full-text search with FTS5
- Typer-based CLI

Source: Migrated from glorious issue-tracker project.
"""

CLI_GROUP = "db-issues"

__version__ = "0.1.0"

# Public API exports
from dot_issues.adapters import (
    CommentRepository,
    IssueGraphRepository,
    IssueRepository,
    UnitOfWork,
    create_db_engine,
    get_database_path,
)
from dot_issues.config import (
    DbIssuesConfig,
    get_db_url,
    get_default_db_path,
    is_debug_mode,
)
from dot_issues.domain import (
    Clock,
    Comment,
    CycleDetectedError,
    DatabaseError,
    Dependency,
    DependencyType,
    DomainError,
    Epic,
    EpicStatus,
    IdentifierService,
    InvalidTransitionError,
    InvariantViolationError,
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
    Label,
    NotFoundError,
    ValidationError,
    utcnow_naive,
)
from dot_issues.services import (
    IssueService,
    SearchResult,
    SearchService,
)

__all__ = [
    # Domain layer
    "Clock",
    "Comment",
    "CycleDetectedError",
    "DatabaseError",
    "Dependency",
    "DependencyType",
    "DomainError",
    "Epic",
    "EpicStatus",
    "IdentifierService",
    "InvariantViolationError",
    "InvalidTransitionError",
    "Issue",
    "IssuePriority",
    "IssueStatus",
    "IssueType",
    "Label",
    "NotFoundError",
    "ValidationError",
    "utcnow_naive",
    # Adapter layer
    "CommentRepository",
    "IssueGraphRepository",
    "IssueRepository",
    "UnitOfWork",
    "create_db_engine",
    "get_database_path",
    # Service layer
    "IssueService",
    "SearchService",
    "SearchResult",
    # Configuration
    "DbIssuesConfig",
    "get_db_url",
    "get_default_db_path",
    "is_debug_mode",
]
