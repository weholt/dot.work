"""Domain entities for issue tracking.

Consolidates all domain entities, value objects, exceptions, and utilities
from the issue-tracker project into a single module for dot-work.

Source: /home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/src/issue_tracker/
"""

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import Enum, IntEnum
from typing import Protocol, runtime_checkable

# =============================================================================
# Domain Utilities
# =============================================================================


def utcnow_naive() -> datetime:
    """Return current UTC time as naive datetime.

    SQLAlchemy/SQLModel stores datetime as naive by default.
    This centralizes the conversion to avoid DRY violations.
    """
    return datetime.now(UTC).replace(tzinfo=None)


# =============================================================================
# Domain Exceptions
# =============================================================================


class DomainError(Exception):
    """Base exception for all domain errors."""

    pass


class InvariantViolationError(DomainError):
    """Raised when a domain invariant is violated."""

    def __init__(self, message: str, entity_id: str | None = None):
        super().__init__(message)
        self.entity_id = entity_id


class InvalidTransitionError(DomainError):
    """Raised when an invalid state transition is attempted."""

    def __init__(
        self,
        message: str,
        entity_id: str,
        current_state: str,
        target_state: str,
    ):
        super().__init__(message)
        self.entity_id = entity_id
        self.current_state = current_state
        self.target_state = target_state


class NotFoundError(DomainError):
    """Raised when an entity is not found."""

    def __init__(self, message: str, entity_id: str | None = None):
        super().__init__(message)
        self.entity_id = entity_id


class ValidationError(DomainError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field


class DatabaseError(DomainError):
    """Raised when database operations fail."""

    pass


class CycleDetectedError(DomainError):
    """Raised when a dependency cycle is detected."""

    def __init__(self, message: str, cycle_path: list[str] | None = None):
        super().__init__(message)
        self.cycle_path = cycle_path or []


# =============================================================================
# Authorization & Audit Types
# =============================================================================


@dataclass(frozen=True)
class User:
    """User context for operations.

    Lightweight value object representing the user performing an operation.
    Used for audit logging and optional authorization checks.

    Attributes:
        username: User identifier (typically from git config or system user)
        email: Optional user email
    """

    username: str
    email: str | None = None

    @classmethod
    def from_git_config(cls) -> "User | None":
        """Create User from git configuration.

        Returns:
            User from git config, or None if git unavailable
        """
        try:
            import subprocess

            try:
                username = (
                    subprocess.check_output(
                        ["git", "config", "user.name"], stderr=subprocess.DEVNULL  # noqa: S607
                    )
                    .decode()
                    .strip()
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                return None

            try:
                email = (
                    subprocess.check_output(
                        ["git", "config", "user.email"], stderr=subprocess.DEVNULL  # noqa: S607
                    )
                    .decode()
                    .strip()
                    or None
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                email = None

            return cls(username=username, email=email)
        except Exception:
            return None

    @classmethod
    def from_system(cls) -> "User":
        """Create User from system environment.

        Returns:
            User with system username
        """
        import getpass
        import os

        username = os.environ.get("USER") or os.environ.get("USERNAME") or getpass.getuser()
        return cls(username=username)


@dataclass
class AuditEntry:
    """Audit log entry for tracking operations.

    Records who did what, when, and to which entity.
    Used for accountability and debugging.

    Attributes:
        id: Unique entry identifier
        action: Action performed (create, update, delete, etc.)
        entity_type: Type of entity affected (issue, comment, project, etc.)
        entity_id: ID of affected entity
        user: User who performed the action
        timestamp: When the action occurred
        details: Optional additional details (JSON string)
    """

    id: str
    action: str
    entity_type: str
    entity_id: str
    user: User
    timestamp: datetime
    details: str | None = None


# =============================================================================
# Service Protocols (Dependency Injection)
# =============================================================================


@runtime_checkable
class Clock(Protocol):
    """Protocol for time provider services.

    Allows injection of different time sources (real time, frozen time for tests, etc.)
    """

    def now(self) -> datetime:
        """Get current UTC datetime.

        Returns:
            Current datetime in UTC timezone (naive datetime)
        """
        ...


@runtime_checkable
class IdentifierService(Protocol):
    """Protocol for generating unique identifiers.

    Used for creating IDs for issues, comments, dependencies, etc.
    """

    def generate(self, prefix: str = "issue") -> str:
        """Generate a new unique identifier.

        Args:
            prefix: Entity type prefix (e.g., "issue", "comment", "epic")

        Returns:
            New identifier with format prefix-XXXXXX (6 hex chars)

        Examples:
            >>> service.generate("issue")
            'issue-a3f8e9'
            >>> service.generate("comment")
            'comment-7b2d4c'
        """
        ...


# =============================================================================
# Value Objects
# =============================================================================


class IssuePriority(IntEnum):
    """Issue priority levels (0=highest, 4=lowest).

    Compatible with issue-tracker project priority system.
    """

    CRITICAL = 0  # P0 - Drop everything
    HIGH = 1  # P1 - Next sprint
    MEDIUM = 2  # P2 - Normal priority (default)
    LOW = 3  # P3 - When convenient
    BACKLOG = 4  # P4 - Not actively considering


# =============================================================================
# Enums
# =============================================================================


class IssueStatus(str, Enum):
    """Issue status values."""

    PROPOSED = "proposed"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    RESOLVED = "resolved"
    COMPLETED = "completed"
    STALE = "stale"
    WONT_FIX = "wont_fix"

    def can_transition_to(self, target: "IssueStatus") -> bool:
        """Check if transition to target status is valid.

        Valid transitions:
        - proposed → in_progress, blocked, resolved, stale, wont_fix
        - in_progress → resolved, completed, blocked, proposed, stale
        - blocked → in_progress, proposed, stale
        - resolved → completed, proposed, stale
        - completed → proposed, stale (reopen)
        - stale → in_progress, proposed
        - wont_fix → (no transitions allowed)

        Args:
            target: Target status to transition to

        Returns:
            True if transition is valid, False otherwise
        """
        # Valid transitions map: current_status -> {valid next status values}
        _TRANSITIONS_MAP: dict[str, set[str]] = {
            "proposed": {"in_progress", "blocked", "resolved", "stale", "wont_fix"},
            "in_progress": {"resolved", "completed", "blocked", "proposed", "stale"},
            "blocked": {"in_progress", "proposed", "stale"},
            "resolved": {"completed", "proposed", "stale"},
            "completed": {"proposed", "stale"},  # Reopen completed issues
            "stale": {"in_progress", "proposed"},
            "wont_fix": set(),  # No transitions allowed from won't-fix
        }

        valid_targets = _TRANSITIONS_MAP.get(self.value, set())
        return target.value in valid_targets


class IssueType(str, Enum):
    """Issue types."""

    BUG = "bug"
    FEATURE = "feature"
    TASK = "task"
    ENHANCEMENT = "enhancement"
    REFACTOR = "refactor"
    DOCS = "docs"
    TEST = "test"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STORY = "story"
    EPIC = "epic"


class EpicStatus(str, Enum):
    """Epic status."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"


class DependencyType(str, Enum):
    """Dependency types between issues.

    Compatible with issue-tracker project dependency types.
    """

    BLOCKS = "blocks"  # Issue A blocks Issue B
    DEPENDS_ON = "depends-on"  # Issue A depends on Issue B
    RELATED_TO = "related-to"  # Issues are related
    DUPLICATES = "duplicates"  # Issue A duplicates Issue B
    PARENT_OF = "parent-of"  # Issue A is parent of Issue B
    CHILD_OF = "child-of"  # Issue A is child of Issue B
    DISCOVERED_FROM = "discovered-from"  # Issue A was discovered while working on Issue B


# =============================================================================
# Entities
# =============================================================================


@dataclass
class Issue:
    """Issue entity for tracking work items.

    Attributes:
        id: Unique issue identifier
        project_id: Project identifier
        title: Issue title
        description: Detailed description
        status: Current status
        priority: Priority level
        type: Issue type
        assignees: List of assigned users (multi-assignee support)
        epic_id: Parent epic ID
        labels: List of label names
        blocked_reason: Reason for blocked status
        source_url: Original source URL (e.g., from external issue tracker)
        references: List of reference URLs or identifiers
        created_at: Creation timestamp
        updated_at: Last modification timestamp
        closed_at: Closure timestamp
        deleted_at: Soft delete timestamp (None if not deleted)
    """

    id: str
    project_id: str
    title: str
    description: str
    status: IssueStatus = IssueStatus.PROPOSED
    priority: IssuePriority = IssuePriority.MEDIUM
    type: IssueType = IssueType.TASK
    assignees: list[str] = field(default_factory=list)
    epic_id: str | None = None
    labels: list[str] = field(default_factory=list)
    blocked_reason: str | None = None
    source_url: str | None = None
    references: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utcnow_naive)
    updated_at: datetime = field(default_factory=utcnow_naive)
    closed_at: datetime | None = None
    deleted_at: datetime | None = None

    def transition(self, new_status: IssueStatus) -> "Issue":
        """Transition to a new status.

        Args:
            new_status: Target status

        Returns:
            New Issue instance with updated status

        Raises:
            InvalidTransitionError: If transition is not valid
        """
        if not self.status.can_transition_to(new_status):
            raise InvalidTransitionError(
                f"Cannot transition from {self.status.value} to {new_status.value}",
                entity_id=self.id,
                current_state=self.status.value,
                target_state=new_status.value,
            )

        # Create new instance with updated status using dataclasses.replace
        new_issue = replace(
            self,
            status=new_status,
            updated_at=utcnow_naive(),
        )

        # Update closed_at when transitioning to completed
        if new_status == IssueStatus.COMPLETED and self.closed_at is None:
            # replace() returns a new instance, so we need another replace for closed_at
            new_issue = replace(new_issue, closed_at=utcnow_naive())

        return new_issue

    def add_label(self, label: str) -> "Issue":
        """Add a label to the issue.

        Args:
            label: Label name to add

        Returns:
            New Issue instance with added label
        """
        if label not in self.labels:
            new_labels = self.labels.copy()
            new_labels.append(label)
            return replace(
                self,
                labels=new_labels,
                updated_at=utcnow_naive(),
            )
        return self

    def remove_label(self, label: str) -> "Issue":
        """Remove a label from the issue.

        Args:
            label: Label name to remove

        Returns:
            New Issue instance with label removed
        """
        if label in self.labels:
            new_labels = [
                existing_label for existing_label in self.labels if existing_label != label
            ]
            return replace(
                self,
                labels=new_labels,
                updated_at=utcnow_naive(),
            )
        return self

    def assign_to(self, assignee: str) -> "Issue":
        """Assign the issue to a user (adds to assignees list).

        Args:
            assignee: Username to assign to

        Returns:
            New Issue instance with added assignee
        """
        if assignee not in self.assignees:
            new_assignees = self.assignees.copy()
            new_assignees.append(assignee)
            return replace(
                self,
                assignees=new_assignees,
                updated_at=utcnow_naive(),
            )
        return self

    def unassign(self, assignee: str) -> "Issue":
        """Unassign a user from the issue.

        Args:
            assignee: Username to unassign

        Returns:
            New Issue instance with assignee removed
        """
        if assignee in self.assignees:
            new_assignees = [a for a in self.assignees if a != assignee]
            return replace(
                self,
                assignees=new_assignees,
                updated_at=utcnow_naive(),
            )
        return self

    def assign_to_epic(self, epic_id: str) -> "Issue":
        """Assign the issue to an epic.

        Args:
            epic_id: Epic ID

        Returns:
            New Issue instance with epic assignment
        """
        return replace(
            self,
            epic_id=epic_id,
            updated_at=utcnow_naive(),
        )


@dataclass
class Comment:
    """Comment entity for issue discussions.

    Attributes:
        id: Unique comment identifier
        issue_id: Parent issue identifier
        author: Comment author username
        text: Comment text content
        created_at: Creation timestamp
        updated_at: Last modification timestamp
    """

    id: str
    issue_id: str
    author: str
    text: str
    created_at: datetime = field(default_factory=utcnow_naive)
    updated_at: datetime = field(default_factory=utcnow_naive)


@dataclass
class Dependency:
    """Dependency entity for issue relationships.

    Represents a directed edge between two issues.

    Attributes:
        from_issue_id: Source issue identifier
        to_issue_id: Target issue identifier
        dependency_type: Type of relationship
        id: Unique dependency identifier (auto-increment)
        description: Optional context about the dependency
        created_at: Creation timestamp
    """

    from_issue_id: str
    to_issue_id: str
    dependency_type: DependencyType
    id: int | None = None
    description: str | None = None
    created_at: datetime = field(default_factory=utcnow_naive)

    def __post_init__(self) -> None:
        """Validate invariants after initialization."""
        # Validate from != to (self-dependency)
        if self.from_issue_id == self.to_issue_id:
            raise InvariantViolationError(f"Issue cannot depend on itself: {self.from_issue_id}")

        # Trim description if provided
        if self.description is not None:
            trimmed = self.description.strip()
            object.__setattr__(self, "description", trimmed if trimmed else None)


@dataclass
class Epic:
    """Epic entity for grouping related issues.

    Attributes:
        id: Unique epic identifier
        title: Epic title
        description: Optional epic description
        status: Epic status
        parent_epic_id: Parent epic for hierarchical organization
        created_at: Creation timestamp
        updated_at: Last modification timestamp
        closed_at: Closure timestamp (if applicable)
    """

    id: str
    title: str
    description: str | None = None
    status: EpicStatus = EpicStatus.OPEN
    parent_epic_id: str | None = None
    created_at: datetime = field(default_factory=utcnow_naive)
    updated_at: datetime = field(default_factory=utcnow_naive)
    closed_at: datetime | None = None


class ProjectStatus(str, Enum):
    """Project status values."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    ON_HOLD = "on_hold"


@dataclass
class Project:
    """Project entity for organizing issues.

    Attributes:
        id: Unique project identifier
        name: Project name
        description: Optional project description
        status: Project status
        is_default: Whether this is the default project
        created_at: Creation timestamp
        updated_at: Last modification timestamp
    """

    id: str
    name: str
    description: str | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    is_default: bool = False
    created_at: datetime = field(default_factory=utcnow_naive)
    updated_at: datetime = field(default_factory=utcnow_naive)


@dataclass
class Label:
    """Label entity for categorizing issues.

    Attributes:
        id: Unique label identifier
        name: Label name (unique)
        color: Optional hex color code
        description: Optional label description
        created_at: Creation timestamp
        updated_at: Last modification timestamp
    """

    id: str
    name: str
    color: str | None = None
    description: str | None = None
    created_at: datetime = field(default_factory=utcnow_naive)
    updated_at: datetime = field(default_factory=utcnow_naive)


# =============================================================================
# Public Exports
# =============================================================================

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
    # Authorization & Audit
    "User",
    "AuditEntry",
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
    "ProjectStatus",
    # Entities
    "Issue",
    "Comment",
    "Dependency",
    "Epic",
    "Label",
    "Project",
]
