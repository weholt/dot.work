"""Domain layer for db-issues module.

Provides domain entities, value objects, exceptions, and protocols
for issue tracking functionality.
"""

from dot_work.db_issues.domain.entities import (
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

__all__ = [
    # Utilities
    "utcnow_naive",
    # Exceptions
    "DomainError",
    "InvariantViolationError",
    "InvalidTransitionError",
    "NotFoundError",
    "ValidationError",
    "DatabaseError",
    "CycleDetectedError",
    # Protocols
    "Clock",
    "IdentifierService",
    # Value Objects
    "IssuePriority",
    # Enums
    "IssueStatus",
    "IssueType",
    "EpicStatus",
    "DependencyType",
    # Entities
    "Issue",
    "Comment",
    "Dependency",
    "Epic",
    "Label",
]
