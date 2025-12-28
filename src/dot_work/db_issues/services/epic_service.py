"""Epic service for business logic operations.

Provides high-level operations for epic management, coordinating
between repositories and enforcing business rules.
"""

import logging
from dataclasses import dataclass

from dot_work.db_issues.adapters import UnitOfWork
from dot_work.db_issues.domain.entities import (
    Clock,
    Epic,
    EpicStatus,
    IdentifierService,
    Issue,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EpicInfo:
    """Summary information about an epic.

    Attributes:
        epic_id: The epic identifier
        title: Epic title
        total_count: Total number of issues in the epic
        proposed_count: Number of issues with proposed status
        in_progress_count: Number of issues in progress
        completed_count: Number of completed issues
    """

    epic_id: str
    title: str
    total_count: int
    proposed_count: int
    in_progress_count: int
    completed_count: int


@dataclass(frozen=True)
class EpicTreeItem:
    """An item in the epic tree.

    Attributes:
        issue_id: The issue ID
        title: Issue title
        status: Issue status
        indent_level: Indentation level for tree display
    """

    issue_id: str
    title: str
    status: str
    indent_level: int


class EpicService:
    """Service for epic management operations.

    Coordinates between repositories and enforces business rules.
    All operations use UnitOfWork for transaction management.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        id_service: IdentifierService,
        clock: Clock,
    ) -> None:
        """Initialize epic service.

        Args:
            uow: Unit of work for transaction management
            id_service: Service for generating unique identifiers
            clock: Time provider for timestamps
        """
        self.uow = uow
        self.id_service = id_service
        self.clock = clock

    def create_epic(
        self,
        title: str,
        description: str | None = None,
        parent_epic_id: str | None = None,
        project_id: str = "default",
        custom_id: str | None = None,
    ) -> Epic:
        """Create a new epic.

        Args:
            title: Epic title
            description: Optional epic description
            parent_epic_id: Optional parent epic ID for hierarchy
            project_id: Project identifier (default: "default")
            custom_id: Optional custom epic ID (auto-generated if not provided)

        Returns:
            Created epic entity

        Examples:
            >>> service.create_epic("User Authentication Epic")
            Epic(id='epic-abc123', title='User Authentication Epic', ...)

            >>> service.create_epic("Custom", custom_id="PROJECT-EPIC-1")
            Epic(id='PROJECT-EPIC-1', title='Custom', ...)
        """
        logger.debug("Creating epic: title=%s, parent=%s", title, parent_epic_id)

        # Use custom ID if provided, otherwise generate one
        if custom_id:
            existing = self.uow.epics.get(custom_id)
            if existing:
                logger.warning("Cannot create epic with custom_id=%s: already exists", custom_id)
                raise ValueError(f"Epic with ID {custom_id} already exists")
            epic_id = custom_id
        else:
            epic_id = self.id_service.generate("epic")

        # Validate parent epic exists if specified
        if parent_epic_id:
            parent = self.uow.epics.get(parent_epic_id)
            if not parent:
                raise ValueError(f"Parent epic {parent_epic_id} not found")
            # Check for cycles
            if self._would_create_cycle(parent_epic_id, epic_id):
                raise ValueError("Cannot add epic: would create a cycle in hierarchy")

        epic = Epic(
            id=epic_id,
            title=title,
            description=description,
            status=EpicStatus.OPEN,
            parent_epic_id=parent_epic_id,
            created_at=self.clock.now(),
            updated_at=self.clock.now(),
        )

        with self.uow:
            saved = self.uow.epics.save(epic)
            logger.info("Created epic: id=%s, title=%s", epic_id, title)
            return saved

    def get_epic(self, epic_id: str) -> Epic | None:
        """Get epic by ID.

        Args:
            epic_id: Epic identifier

        Returns:
            Epic entity if found, None otherwise
        """
        logger.debug("Getting epic: id=%s", epic_id)
        return self.uow.epics.get(epic_id)

    def list_epics(self, status: EpicStatus | None = None) -> list[Epic]:
        """List all epics, optionally filtered by status.

        Args:
            status: Optional status filter

        Returns:
            List of epic entities
        """
        logger.debug("Listing epics: status=%s", status)
        if status:
            return self.uow.epics.get_by_status(status)
        return self.uow.epics.list_all()

    def update_epic(
        self,
        epic_id: str,
        title: str | None = None,
        description: str | None = None,
        status: EpicStatus | None = None,
    ) -> Epic | None:
        """Update an epic.

        Args:
            epic_id: Epic identifier
            title: New title (optional)
            description: New description (optional)
            status: New status (optional)

        Returns:
            Updated epic entity if found, None otherwise
        """
        logger.debug("Updating epic: id=%s", epic_id)
        epic = self.uow.epics.get(epic_id)
        if not epic:
            logger.warning("Cannot update epic %s: not found", epic_id)
            return None

        if title:
            epic.title = title
        if description is not None:
            epic.description = description
        if status:
            epic.status = status
            # Set closed_at if status is COMPLETED or CLOSED
            if status in (EpicStatus.COMPLETED, EpicStatus.CLOSED) and not epic.closed_at:
                epic.closed_at = self.clock.now()
        epic.updated_at = self.clock.now()

        with self.uow:
            updated = self.uow.epics.save(epic)
            logger.info("Updated epic: id=%s", epic_id)
            return updated

    def delete_epic(self, epic_id: str) -> bool:
        """Delete an epic.

        Args:
            epic_id: Epic identifier

        Returns:
            True if epic was deleted, False if not found

        Note:
            This will NOT delete child epics or issues associated with this epic.
            Child epics will have their parent_epic_id set to None.
        """
        logger.debug("Deleting epic: id=%s", epic_id)

        # Check for child epics and clear their parent references
        child_epics = self.uow.epics.get_child_epics(epic_id)
        with self.uow:
            for child in child_epics:
                child.parent_epic_id = None
                child.updated_at = self.clock.now()
                self.uow.epics.save(child)
                logger.debug("Cleared parent for child epic: %s", child.id)

            # Also need to clear epic_id from any issues that reference this epic
            # Use SQL-level filtering to only load issues that reference this epic
            epic_issues = self.uow.issues.list_by_epic(epic_id)
            for issue in epic_issues:
                # Update issue epic_id to None
                # This requires using IssueRepository which doesn't have this method
                # We'll need to handle this in IssueService
                logger.debug("Issue %s references deleted epic %s", issue.id, epic_id)

            deleted = self.uow.epics.delete(epic_id)
            if deleted:
                logger.info("Deleted epic: id=%s", epic_id)
            else:
                logger.warning("Cannot delete epic %s: not found", epic_id)
            return deleted

    def add_child_epic(self, parent_epic_id: str, child_epic_id: str) -> bool:
        """Add a child epic to a parent epic.

        Args:
            parent_epic_id: Parent epic identifier
            child_epic_id: Child epic identifier

        Returns:
            True if child was added, False otherwise

        Raises:
            ValueError: If operation would create a cycle
        """
        logger.debug("Adding child epic: parent=%s, child=%s", parent_epic_id, child_epic_id)

        # Check for cycle before making changes
        if self._would_create_cycle(parent_epic_id, child_epic_id):
            raise ValueError("Cannot add child epic: would create a cycle in hierarchy")

        parent = self.uow.epics.get(parent_epic_id)
        child = self.uow.epics.get(child_epic_id)

        if not parent:
            logger.warning("Parent epic %s not found", parent_epic_id)
            return False
        if not child:
            logger.warning("Child epic %s not found", child_epic_id)
            return False

        child.parent_epic_id = parent_epic_id
        child.updated_at = self.clock.now()

        with self.uow:
            self.uow.epics.save(child)
            logger.info("Added child epic: parent=%s, child=%s", parent_epic_id, child_epic_id)
            return True

    def remove_child_epic(self, child_epic_id: str) -> bool:
        """Remove a child epic from its parent.

        Args:
            child_epic_id: Child epic identifier

        Returns:
            True if child was removed, False otherwise
        """
        logger.debug("Removing child epic: child=%s", child_epic_id)

        child = self.uow.epics.get(child_epic_id)
        if not child:
            logger.warning("Child epic %s not found", child_epic_id)
            return False

        if child.parent_epic_id is None:
            logger.warning("Child epic %s has no parent", child_epic_id)
            return False

        parent_id = child.parent_epic_id
        child.parent_epic_id = None
        child.updated_at = self.clock.now()

        with self.uow:
            self.uow.epics.save(child)
            logger.info("Removed child epic: former_parent=%s, child=%s", parent_id, child_epic_id)
            return True

    def list_child_epics(self, parent_epic_id: str) -> list[Epic]:
        """List all child epics of a parent epic.

        Args:
            parent_epic_id: Parent epic identifier

        Returns:
            List of child epic entities
        """
        logger.debug("Listing child epics: parent=%s", parent_epic_id)
        return self.uow.epics.get_child_epics(parent_epic_id)

    def get_all_epics_with_counts(self) -> list[EpicInfo]:
        """Get all epics with issue count summaries.

        Returns:
            List of EpicInfo objects with counts by status

        Examples:
            >>> infos = service.get_all_epics_with_counts()
            >>> for info in infos:
            ...     print(f"{info.epic_id}: {info.total_count} issues")
        """
        logger.debug("Getting all epics with counts")

        # Get all epics
        epics = self.uow.epics.list_all()

        # Get counts using SQL-level aggregation (no memory issues)
        epic_counts = self.uow.issues.get_epic_counts()

        results: list[EpicInfo] = []

        for epic in epics:
            counts = epic_counts.get(epic.id, {"total": 0, "proposed": 0, "in_progress": 0, "completed": 0})

            results.append(
                EpicInfo(
                    epic_id=epic.id,
                    title=epic.title,
                    total_count=counts["total"],
                    proposed_count=counts["proposed"],
                    in_progress_count=counts["in_progress"],
                    completed_count=counts["completed"],
                )
            )

        return results

    def get_epic_issues(self, epic_id: str) -> list[Issue]:
        """Get all issues in an epic.

        Args:
            epic_id: Epic identifier

        Returns:
            List of issues in the epic

        Examples:
            >>> issues = service.get_epic_issues("EPIC-001")
            >>> for issue in issues:
            ...     print(f"{issue.id}: {issue.title}")
        """
        logger.debug("Getting issues for epic: id=%s", epic_id)

        # Verify epic exists
        epic = self.uow.epics.get(epic_id)
        if not epic:
            logger.warning("Epic not found: id=%s", epic_id)
            return []

        # Use SQL-level filtering instead of loading all issues
        return self.uow.issues.list_by_epic(epic_id)

    def get_epic_tree(self, epic_id: str) -> list[EpicTreeItem]:
        """Get hierarchical tree of issues in an epic.

        Builds a tree structure showing issues and their children
        (issues that have this issue as their parent_id).

        Args:
            epic_id: Epic identifier

        Returns:
            List of EpicTreeItem objects representing the tree

        Examples:
            >>> tree = service.get_epic_tree("EPIC-001")
            >>> for item in tree:
            ...     indent = "  " * item.indent_level
            ...     print(f"{indent}{item.issue_id}: {item.title}")
        """
        logger.debug("Getting epic tree: epic_id=%s", epic_id)

        # Verify epic exists
        epic = self.uow.epics.get(epic_id)
        if not epic:
            logger.warning("Epic not found: id=%s", epic_id)
            return []

        # Use SQL-level filtering instead of loading all issues
        epic_issues = self.uow.issues.list_by_epic(epic_id)

        # Build a parent -> children map
        children_map: dict[str, list[Issue]] = {}
        root_issues: list[Issue] = []

        for issue in epic_issues:
            # Check if this issue has a parent_id (assuming parent_id field exists on Issue)
            # If not, treat it as a root issue
            parent_id = getattr(issue, "parent_id", None)
            if parent_id and parent_id in [i.id for i in epic_issues]:
                if parent_id not in children_map:
                    children_map[parent_id] = []
                children_map[parent_id].append(issue)
            else:
                root_issues.append(issue)

        # Build tree using DFS
        results: list[EpicTreeItem] = []

        def build_tree(issues: list[Issue], level: int) -> None:
            """Recursively build tree from issues."""
            for issue in issues:
                results.append(
                    EpicTreeItem(
                        issue_id=issue.id,
                        title=issue.title,
                        status=issue.status.value,
                        indent_level=level,
                    )
                )

                # Add children
                children = children_map.get(issue.id, [])
                if children:
                    build_tree(children, level + 1)

        build_tree(root_issues, 0)

        return results

    def get_all_epic_trees(self) -> dict[str, list[EpicTreeItem]]:
        """Get trees for all epics.

        Returns:
            Dictionary mapping epic IDs to their tree items

        Examples:
            >>> trees = service.get_all_epic_trees()
            >>> for epic_id, items in trees.items():
            ...     print(f"{epic_id}: {len(items)} issues")
        """
        logger.debug("Getting trees for all epics")

        epics = self.uow.epics.list_all()
        results: dict[str, list[EpicTreeItem]] = {}

        for epic in epics:
            results[epic.id] = self.get_epic_tree(epic.id)

        return results

    def _would_create_cycle(self, parent_id: str, child_id: str) -> bool:
        """Check if adding a child would create a cycle.

        Args:
            parent_id: Prospective parent epic ID
            child_id: Child epic ID to add

        Returns:
            True if adding would create a cycle, False otherwise
        """
        # If we're adding child_id as a child of parent_id,
        # we need to check if child_id is already an ancestor of parent_id
        visited: set[str] = set()

        def dfs(current_id: str) -> bool:
            """Depth-first search to detect cycles."""
            if current_id == child_id:
                return True  # Found the child_id in ancestors - cycle!
            if current_id in visited:
                return False
            visited.add(current_id)

            current = self.uow.epics.get(current_id)
            if current and current.parent_epic_id:
                return dfs(current.parent_epic_id)
            return False

        return dfs(parent_id)


__all__ = [
    "EpicService",
    "EpicInfo",
    "EpicTreeItem",
]
