"""Adapters layer for db-issues module.

Provides database adapters including SQLModel models, repositories,
and Unit of Work for SQLite persistence.
"""

from dot_issues.adapters.sqlite import (
    CommentModel,
    CommentRepository,
    DependencyModel,
    EpicModel,
    EpicRepository,
    IssueGraphRepository,
    IssueLabelModel,
    IssueModel,
    IssueRepository,
    LabelModel,
    LabelRepository,
    UnitOfWork,
    create_db_engine,
    get_database_path,
)

__all__ = [
    # Models
    "IssueModel",
    "LabelModel",
    "IssueLabelModel",
    "CommentModel",
    "DependencyModel",
    "EpicModel",
    # Engine
    "create_db_engine",
    "get_database_path",
    # Repositories
    "IssueRepository",
    "CommentRepository",
    "IssueGraphRepository",
    "EpicRepository",
    "LabelRepository",
    # Unit of Work
    "UnitOfWork",
]
