"""Domain entities for issue tracking.

Consolidates all domain entities, value objects, exceptions, and utilities
from the issue-tracker project into a single module for dot-work.

Source: /home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/src/issue_tracker/
"""

from dataclasses import dataclass, field
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
    """Issue priority levels (0=highest, 3=lowest).

    Compatible with issue-tracker project priority system.
    """

    CRITICAL = 0  # P0 - Drop everything
    HIGH = 1  # P1 - Next sprint
    MEDIUM = 2  # P2 - Normal priority (default)
    LOW = 3  # P3 - When convenient


# =============================================================================
# Enums
# =============================================================================


class IssueStatus(str, Enum):
    """Issue status values."""

    PROPOSED = "proposed"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    WONT_FIX = "wont_fix"

    def can_transition_to(self, target: "IssueStatus") -> bool:
        """Check if transition to target status is valid.

        Valid transitions:
        - proposed → in_progress, blocked, wont_fix
        - in_progress → completed, blocked, proposed
        - blocked → in_progress, proposed
        - completed → proposed (reopen)
        - wont_fix → (no transitions allowed)

        Args:
            target: Target status to transition to

        Returns:
            True if transition is valid, False otherwise
        """
        # Valid transitions map: current_status -> {valid next status values}
        _TRANSITIONS_MAP: dict[str, set[str]] = {
            "proposed": {"in_progress", "blocked", "wont_fix"},
            "in_progress": {"completed", "blocked", "proposed"},
            "blocked": {"in_progress", "proposed"},
            "completed": {"proposed"},  # Reopen completed issues
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
        assignee: Assigned user
        epic_id: Parent epic ID
        labels: List of label names
        created_at: Creation timestamp
        updated_at: Last modification timestamp
        closed_at: Closure timestamp
    """

    id: str
    project_id: str
    title: str
    description: str
    status: IssueStatus = IssueStatus.PROPOSED
    priority: IssuePriority = IssuePriority.MEDIUM
    type: IssueType = IssueType.TASK
    assignee: str | None = None
    epic_id: str | None = None
    labels: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utcnow_naive)
    updated_at: datetime = field(default_factory=utcnow_naive)
    closed_at: datetime | None = None

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

        # Create new instance with updated status
        new_issue = Issue(
            id=self.id,
            project_id=self.project_id,
            title=self.title,
            description=self.description,
            status=new_status,
            priority=self.priority,
            type=self.type,
            assignee=self.assignee,
            epic_id=self.epic_id,
            labels=self.labels.copy(),
            created_at=self.created_at,
            updated_at=utcnow_naive(),
            closed_at=self.closed_at,
        )

        # Update closed_at when transitioning to closed
        if new_status == IssueStatus.COMPLETED and self.closed_at is None:
            new_issue.closed_at = utcnow_naive()

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
            return Issue(
                id=self.id,
                project_id=self.project_id,
                title=self.title,
                description=self.description,
                status=self.status,
                priority=self.priority,
                type=self.type,
                assignee=self.assignee,
                epic_id=self.epic_id,
                labels=new_labels,
                created_at=self.created_at,
                updated_at=utcnow_naive(),
                closed_at=self.closed_at,
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
            return Issue(
                id=self.id,
                project_id=self.project_id,
                title=self.title,
                description=self.description,
                status=self.status,
                priority=self.priority,
                type=self.type,
                assignee=self.assignee,
                epic_id=self.epic_id,
                labels=new_labels,
                created_at=self.created_at,
                updated_at=utcnow_naive(),
                closed_at=self.closed_at,
            )
        return self

    def assign_to(self, assignee: str) -> "Issue":
        """Assign the issue to a user.

        Args:
            assignee: Username to assign to

        Returns:
            New Issue instance with updated assignee
        """
        return Issue(
            id=self.id,
            project_id=self.project_id,
            title=self.title,
            description=self.description,
            status=self.status,
            priority=self.priority,
            type=self.type,
            assignee=assignee,
            epic_id=self.epic_id,
            labels=self.labels.copy(),
            created_at=self.created_at,
            updated_at=utcnow_naive(),
            closed_at=self.closed_at,
        )

    def assign_to_epic(self, epic_id: str) -> "Issue":
        """Assign the issue to an epic.

        Args:
            epic_id: Epic ID

        Returns:
            New Issue instance with epic assignment
        """
        return Issue(
            id=self.id,
            project_id=self.project_id,
            title=self.title,
            description=self.description,
            status=self.status,
            priority=self.priority,
            type=self.type,
            assignee=self.assignee,
            epic_id=epic_id,
            labels=self.labels.copy(),
            created_at=self.created_at,
            updated_at=utcnow_naive(),
            closed_at=self.closed_at,
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
