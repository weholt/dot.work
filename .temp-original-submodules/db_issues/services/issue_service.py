"""Issue service for business logic operations.

Provides high-level operations for issue management, coordinating
between repositories and enforcing business rules.

Source: /home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/src/issue_tracker/services/
"""

import logging
from dataclasses import dataclass, field

from dot_work.db_issues.adapters import UnitOfWork
from dot_work.db_issues.domain.entities import (
    AuditEntry,
    Clock,
    Comment,
    Dependency,
    DependencyType,
    IdentifierService,
    InvalidTransitionError,
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
    User,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Audit Log Support
# =============================================================================


@dataclass
class AuditLog:
    """In-memory audit log for tracking operations.

    Provides thread-safe audit logging for accountability.
    Entries can be exported to persistent storage if needed.

    Attributes:
        entries: List of audit entries
    """

    entries: list[AuditEntry] = field(default_factory=list)

    def log(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user: User | None,
        timestamp_field,
        details: str | None = None,
    ) -> None:
        """Log an audit entry.

        Args:
            action: Action performed (create, update, delete, etc.)
            entity_type: Type of entity affected
            entity_id: ID of affected entity
            user: User who performed the action (None if unknown)
            timestamp_field: Callable to get current timestamp
            details: Optional additional details
        """
        if user is None:
            # Skip logging if no user context (backward compatible)
            return

        import uuid

        entry = AuditEntry(
            id=f"audit-{uuid.uuid4().hex[:8]}",
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user=user,
            timestamp=timestamp_field(),
            details=details,
        )
        self.entries.append(entry)


class IssueService:
    """Service for issue management operations.

    Coordinates between repositories and enforces business rules.
    All operations use UnitOfWork for transaction management.

    Supports optional user context for audit logging and authorization.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        id_service: IdentifierService,
        clock: Clock,
        audit_log: AuditLog | None = None,
        default_user: User | None = None,
    ) -> None:
        """Initialize issue service.

        Args:
            uow: Unit of work for transaction management
            id_service: Service for generating unique identifiers
            clock: Time provider for timestamps
            audit_log: Optional audit log for tracking operations
            default_user: Optional default user for operations (from git config)
        """
        self.uow = uow
        self.id_service = id_service
        self.clock = clock
        self.audit_log = audit_log or AuditLog()
        self.default_user = default_user

    def create_issue(
        self,
        title: str,
        description: str = "",
        priority: IssuePriority = IssuePriority.MEDIUM,
        issue_type: IssueType = IssueType.TASK,
        assignee: str | None = None,
        assignees: list[str] | None = None,
        epic_id: str | None = None,
        labels: list[str] | None = None,
        project_id: str = "default",
        custom_id: str | None = None,
        user: User | None = None,
    ) -> Issue:
        """Create a new issue.

        Args:
            title: Issue title
            description: Issue description (default: empty)
            priority: Issue priority (default: MEDIUM)
            issue_type: Issue type (default: TASK)
            assignee: Optional single assignee username (deprecated, use assignees)
            assignees: Optional list of assignee usernames
            epic_id: Optional parent epic ID
            labels: Optional list of labels
            project_id: Project identifier (default: "default")
            custom_id: Optional custom issue ID (auto-generated if not provided)
            user: Optional user context for audit logging

        Returns:
            Created issue entity

        Examples:
            >>> service.create_issue("Fix bug", priority=IssuePriority.HIGH)
            Issue(id='issue-abc123', title='Fix bug', ...)

            >>> service.create_issue("Multi-assign", assignees=["alice", "bob"])
            Issue(id='issue-def456', title='Multi-assign', ...)

            >>> service.create_issue("Custom", custom_id="PROJECT-123")
            Issue(id='PROJECT-123', title='Custom', ...)
        """
        # Handle both assignee (single) and assignees (list) for backward compatibility
        final_assignees: list[str] = []
        if assignee:
            final_assignees.append(assignee)
        if assignees:
            final_assignees.extend(assignees)

        logger.debug(
            "Creating issue: title=%s, type=%s, priority=%s, assignees=%s",
            title,
            issue_type.value,
            priority.value,
            final_assignees,
        )

        # Use custom ID if provided, otherwise generate one
        if custom_id:
            # Validate that custom ID doesn't already exist
            logger.debug("Checking if custom ID already exists: %s", custom_id)
            existing = self.uow.issues.get(custom_id)
            if existing:
                logger.warning("Cannot create issue with custom_id=%s: already exists", custom_id)
                raise ValueError(f"Issue with ID '{custom_id}' already exists")
            issue_id = custom_id
        else:
            issue_id = self.id_service.generate("issue")

        now = self.clock.now()

        issue = Issue(
            id=issue_id,
            project_id=project_id,
            title=title,
            description=description,
            status=IssueStatus.PROPOSED,
            priority=priority,
            type=issue_type,
            assignees=final_assignees,
            epic_id=epic_id,
            labels=labels or [],
            created_at=now,
            updated_at=now,
        )

        saved_issue = self.uow.issues.save(issue)
        logger.info(
            "Issue created: id=%s, title=%s, project=%s",
            saved_issue.id,
            saved_issue.title,
            project_id,
        )

        # Audit log
        effective_user = user or self.default_user
        self.audit_log.log(
            action="create",
            entity_type="issue",
            entity_id=saved_issue.id,
            user=effective_user,
            timestamp_field=self.clock.now,
            details=f"Created issue: {saved_issue.title}",
        )

        return saved_issue

    def get_issue(self, issue_id: str) -> Issue | None:
        """Get issue by ID.

        Args:
            issue_id: Issue identifier

        Returns:
            Issue if found, None otherwise
        """
        logger.debug("Retrieving issue: id=%s", issue_id)
        issue = self.uow.issues.get(issue_id)
        if issue:
            logger.debug(
                "Issue found: id=%s, title=%s, status=%s", issue.id, issue.title, issue.status.value
            )
        else:
            logger.debug("Issue not found: id=%s", issue_id)
        return issue

    def update_issue(
        self,
        issue_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: IssuePriority | None = None,
        assignee: str | None = None,
        assignees: list[str] | None = None,
        epic_id: str | None = None,
        status: IssueStatus | None = None,
        type: IssueType | None = None,
    ) -> Issue | None:
        """Update issue fields.

        Args:
            issue_id: Issue identifier
            title: New title (if provided)
            description: New description (if provided)
            priority: New priority (if provided)
            assignee: New single assignee, replaces all assignees (if provided)
            assignees: New list of assignees, replaces all assignees (if provided)
            epic_id: New epic ID (if provided)
            status: New status (if provided, uses transition validation)
            type: New issue type (if provided)

        Returns:
            Updated issue if found, None otherwise

        Raises:
            InvalidTransitionError: If status transition is not allowed
        """
        logger.debug(
            "Updating issue: id=%s, title=%s, priority=%s, assignee=%s, assignees=%s, epic_id=%s, status=%s, type=%s",
            issue_id,
            title,
            priority,
            assignee,
            assignees,
            epic_id,
            status.value if status else None,
            type.value if type else None,
        )
        issue = self.uow.issues.get(issue_id)
        if not issue:
            logger.warning("Cannot update: issue not found: id=%s", issue_id)
            return None

        if title is not None:
            issue.title = title
        if description is not None:
            issue.description = description
        if priority is not None:
            issue.priority = priority

        # Handle assignee/assignees - set the full assignees list
        if assignees is not None:
            # Replace entire assignees list
            issue.assignees = assignees.copy()
        elif assignee is not None:
            # Single assignee replaces all
            issue.assignees = [assignee]

        if epic_id is not None:
            issue.epic_id = epic_id
        if status is not None:
            # Validate status transition
            if not issue.status.can_transition_to(status):
                raise InvalidTransitionError(
                    f"Cannot transition from {issue.status.value} to {status.value}",
                    entity_id=issue.id,
                    current_state=issue.status.value,
                    target_state=status.value,
                )
            issue.status = status
        if type is not None:
            issue.type = type

        issue.updated_at = self.clock.now()
        updated_issue = self.uow.issues.save(issue)
        logger.info("Issue updated: id=%s, title=%s", updated_issue.id, updated_issue.title)
        return updated_issue

    def transition_issue(self, issue_id: str, new_status: IssueStatus) -> Issue | None:
        """Transition issue to new status.

        Args:
            issue_id: Issue identifier
            new_status: Target status

        Returns:
            Updated issue if found, None otherwise

        Raises:
            InvalidTransitionError: If transition is not allowed
        """
        logger.debug(
            "Transitioning issue: id=%s, from_status=?, to_status=%s", issue_id, new_status.value
        )
        issue = self.uow.issues.get(issue_id)
        if not issue:
            logger.warning("Cannot transition: issue not found: id=%s", issue_id)
            return None

        logger.debug(
            "Issue status transition: id=%s, from=%s, to=%s",
            issue_id,
            issue.status.value,
            new_status.value,
        )
        # transition() returns a new Issue object
        transitioned = issue.transition(new_status)
        transitioned.updated_at = self.clock.now()

        if new_status == IssueStatus.COMPLETED:
            transitioned.closed_at = self.clock.now()

        saved = self.uow.issues.save(transitioned)
        logger.info("Issue transitioned: id=%s, new_status=%s", saved.id, saved.status.value)
        return saved

    def close_issue(self, issue_id: str) -> Issue | None:
        """Close an issue.

        Transitions the issue to COMPLETED status.

        Args:
            issue_id: Issue identifier

        Returns:
            Closed issue if found, None otherwise
        """
        logger.debug("Closing issue: id=%s", issue_id)
        issue = self.uow.issues.get(issue_id)
        if not issue:
            logger.warning("Cannot close: issue not found: id=%s", issue_id)
            return None

        # Transition to completed
        closed = self.transition_issue(issue_id, IssueStatus.COMPLETED)
        if closed:
            logger.info("Issue closed: id=%s", issue_id)
        return closed

    def reopen_issue(self, issue_id: str) -> Issue | None:
        """Reopen a closed issue.

        Args:
            issue_id: Issue identifier

        Returns:
            Reopened issue if found, None otherwise
        """
        issue = self.uow.issues.get(issue_id)
        if not issue:
            return None

        issue.status = IssueStatus.PROPOSED
        issue.closed_at = None
        issue.updated_at = self.clock.now()
        return self.uow.issues.save(issue)

    def delete_issue(self, issue_id: str) -> bool:
        """Delete an issue.

        Args:
            issue_id: Issue identifier

        Returns:
            True if deleted, False if not found
        """
        logger.debug("Deleting issue: id=%s", issue_id)
        deleted = self.uow.issues.delete(issue_id)
        if deleted:
            logger.info("Issue deleted: id=%s", issue_id)
        else:
            logger.warning("Cannot delete: issue not found: id=%s", issue_id)
        return deleted

    def list_issues(
        self,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        assignee: str | None = None,
        epic_id: str | None = None,
        issue_type: IssueType | None = None,
        project_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
        exclude_backlog: bool = True,
    ) -> list[Issue]:
        """List issues with optional filtering.

        Args:
            status: Filter by status
            priority: Filter by priority
            assignee: Filter by assignee
            epic_id: Filter by epic
            issue_type: Filter by type
            project_id: Filter by project
            limit: Maximum results (default: 100)
            offset: Offset for pagination (default: 0)
            exclude_backlog: Exclude backlog priority issues (default: True)

        Returns:
            List of matching issues
        """
        if project_id:
            issues = self.uow.issues.list_by_project(project_id, limit, offset)
        elif status:
            issues = self.uow.issues.list_by_status(status, limit, offset)
        elif priority is not None:
            issues = self.uow.issues.list_by_priority(priority, limit, offset)
        elif assignee:
            issues = self.uow.issues.list_by_assignee(assignee, limit, offset)
        elif epic_id:
            issues = self.uow.issues.list_by_epic(epic_id, limit, offset)
        elif issue_type:
            issues = self.uow.issues.list_by_type(issue_type, limit, offset)
        else:
            issues = self.uow.issues.list_all(limit, offset)

        # Filter out backlog items if exclude_backlog is True
        if exclude_backlog:
            issues = [i for i in issues if i.priority != IssuePriority.BACKLOG]

        return issues

    def add_comment(self, issue_id: str, author: str, text: str) -> Comment | None:
        """Add comment to issue.

        Args:
            issue_id: Issue identifier
            author: Comment author username
            text: Comment text content

        Returns:
            Created comment if issue exists, None otherwise
        """
        logger.debug("Adding comment to issue: issue_id=%s, author=%s", issue_id, author)
        # Verify issue exists
        issue = self.uow.issues.get(issue_id)
        if not issue:
            logger.warning("Cannot add comment: issue not found: id=%s", issue_id)
            return None

        comment_id = self.id_service.generate("comment")
        now = self.clock.now()

        comment = Comment(
            id=comment_id,
            issue_id=issue_id,
            author=author,
            text=text,
            created_at=now,
            updated_at=now,
        )

        saved_comment = self.uow.comments.save(comment)
        logger.info(
            "Comment added: id=%s, issue_id=%s, author=%s", saved_comment.id, issue_id, author
        )
        return saved_comment

    def list_comments(self, issue_id: str) -> list[Comment]:
        """List all comments for an issue.

        Args:
            issue_id: Issue identifier

        Returns:
            List of comments ordered by creation time
        """
        return self.uow.comments.list_by_issue(issue_id)

    def add_dependency(
        self,
        from_issue_id: str,
        to_issue_id: str,
        dependency_type: DependencyType = DependencyType.DEPENDS_ON,
    ) -> Dependency | None:
        """Add dependency between issues.

        Args:
            from_issue_id: Source issue ID
            to_issue_id: Target issue ID
            dependency_type: Type of dependency (default: DEPENDS_ON)

        Returns:
            Created dependency if no cycle detected, None otherwise
        """
        logger.debug(
            "Adding dependency: from=%s, to=%s, type=%s",
            from_issue_id,
            to_issue_id,
            dependency_type.value,
        )
        # Check for cycles
        if self.uow.graph.has_cycle(from_issue_id, to_issue_id):
            logger.warning(
                "Cannot add dependency: would create cycle: from=%s, to=%s",
                from_issue_id,
                to_issue_id,
            )
            return None

        now = self.clock.now()
        dependency = Dependency(
            from_issue_id=from_issue_id,
            to_issue_id=to_issue_id,
            dependency_type=dependency_type,
            created_at=now,
        )

        saved_dep = self.uow.graph.add_dependency(dependency)
        logger.info(
            "Dependency added: from=%s, to=%s, type=%s",
            from_issue_id,
            to_issue_id,
            dependency_type.value,
        )
        return saved_dep

    def remove_dependency(
        self,
        from_issue_id: str,
        to_issue_id: str,
        dependency_type: DependencyType = DependencyType.DEPENDS_ON,
    ) -> bool:
        """Remove dependency between issues.

        Args:
            from_issue_id: Source issue ID
            to_issue_id: Target issue ID
            dependency_type: Type of dependency (default: DEPENDS_ON)

        Returns:
            True if removed, False if not found
        """
        return self.uow.graph.remove_dependency(from_issue_id, to_issue_id, dependency_type)

    def get_blockers(self, issue_id: str) -> list[str]:
        """Get issues blocking this issue.

        Args:
            issue_id: Issue identifier

        Returns:
            List of issue IDs that block this issue
        """
        return self.uow.graph.get_blockers(issue_id)

    def get_blocked_issues(self, issue_id: str) -> list[str]:
        """Get issues blocked by this issue.

        Args:
            issue_id: Issue identifier

        Returns:
            List of issue IDs blocked by this issue
        """
        return self.uow.graph.get_blocked_by(issue_id)

    def bulk_update_status(
        self, issue_ids: list[str], new_status: IssueStatus
    ) -> tuple[list[Issue], list[str]]:
        """Update status for multiple issues in a single transaction.

        Args:
            issue_ids: List of issue IDs to update
            new_status: New status to apply

        Returns:
            Tuple of (successfully updated issues, failed issue IDs)
        """
        logger.debug(
            "Bulk updating status for %d issues: new_status=%s", len(issue_ids), new_status.value
        )
        updated: list[Issue] = []
        failed: list[str] = []

        for issue_id in issue_ids:
            try:
                issue = self.transition_issue(issue_id, new_status)
                if issue:
                    updated.append(issue)
                else:
                    failed.append(issue_id)
            except Exception as e:
                logger.error("Failed to transition issue: id=%s, error=%s", issue_id, str(e))
                failed.append(issue_id)

        logger.info(
            "Bulk status update completed: updated=%d, failed=%d", len(updated), len(failed)
        )
        return updated, failed

    def bulk_update_priority(
        self, issue_ids: list[str], new_priority: IssuePriority
    ) -> tuple[list[Issue], list[str]]:
        """Update priority for multiple issues in a single transaction.

        Args:
            issue_ids: List of issue IDs to update
            new_priority: New priority to apply

        Returns:
            Tuple of (successfully updated issues, failed issue IDs)
        """
        updated: list[Issue] = []
        failed: list[str] = []

        for issue_id in issue_ids:
            try:
                issue = self.update_issue(issue_id, priority=new_priority)
                if issue:
                    updated.append(issue)
                else:
                    failed.append(issue_id)
            except Exception:
                failed.append(issue_id)

        return updated, failed

    def bulk_assign(self, issue_ids: list[str], assignee: str) -> tuple[list[Issue], list[str]]:
        """Assign multiple issues to a user in a single transaction.

        Args:
            issue_ids: List of issue IDs to assign
            assignee: Username to assign issues to

        Returns:
            Tuple of (successfully updated issues, failed issue IDs)
        """
        updated: list[Issue] = []
        failed: list[str] = []

        for issue_id in issue_ids:
            try:
                issue = self.update_issue(issue_id, assignee=assignee)
                if issue:
                    updated.append(issue)
                else:
                    failed.append(issue_id)
            except Exception:
                failed.append(issue_id)

        return updated, failed

    def set_epic(self, issue_id: str, epic_id: str) -> Issue | None:
        """Set the epic for an issue.

        Args:
            issue_id: ID of the issue
            epic_id: ID of the epic to assign

        Returns:
            Updated issue or None if not found
        """
        with self.uow:
            issue = self.uow.issues.get(issue_id)
            if not issue:
                return None

            issue.epic_id = epic_id
            issue.updated_at = self.clock.now()
            self.uow.issues.save(issue)
            self.uow.commit()
            return issue

    def clear_epic(self, issue_id: str) -> Issue | None:
        """Clear the epic from an issue.

        Args:
            issue_id: ID of the issue

        Returns:
            Updated issue or None if not found
        """
        with self.uow:
            issue = self.uow.issues.get(issue_id)
            if not issue:
                return None

            issue.epic_id = None
            issue.updated_at = self.clock.now()
            self.uow.issues.save(issue)
            self.uow.commit()
            return issue

    def get_epic_issues(self, epic_id: str, include_children: bool = False) -> list[Issue]:
        """Get all issues in an epic.

        Args:
            epic_id: ID of the epic
            include_children: If True, include issues from child epics
                (Note: include_children not supported with new enum schema)

        Returns:
            List of issues in the epic
        """
        with self.uow:
            # Use repository method that filters at SQL level
            epic_issues = self.uow.issues.list_by_epic(epic_id, limit=100000)

            # Note: include_children functionality removed as IssueType.EPIC
            # no longer exists in the issue-tracker enum schema.
            # Hierarchical epic handling to be addressed in reconciliation.

            return epic_issues

    def set_labels(self, issue_id: str, labels: list[str]) -> Issue | None:
        """Replace all labels on an issue.

        Args:
            issue_id: Issue identifier
            labels: New list of labels (replaces all existing labels)

        Returns:
            Updated issue if found, None otherwise

        Examples:
            >>> service.set_labels("issue-123", ["bug", "urgent"])
            Issue(id='issue-123', labels=["bug", "urgent"], ...)
        """
        logger.debug("Setting labels for issue: id=%s, labels=%s", issue_id, labels)

        issue = self.uow.issues.get(issue_id)
        if not issue:
            logger.warning("Cannot set labels: issue not found: id=%s", issue_id)
            return None

        # Replace all labels
        issue.labels = labels
        issue.updated_at = self.clock.now()

        updated_issue = self.uow.issues.save(issue)
        logger.info("Set labels for issue: id=%s, labels=%s", issue_id, labels)
        return updated_issue

    def block_issue(self, issue_id: str, reason: str | None = None) -> Issue | None:
        """Block an issue with an optional reason.

        Transitions the issue to BLOCKED status and stores the reason.

        Args:
            issue_id: Issue identifier
            reason: Optional reason for blocking

        Returns:
            Blocked issue if found, None otherwise
        """
        logger.debug("Blocking issue: id=%s, reason=%s", issue_id, reason)

        issue = self.uow.issues.get(issue_id)
        if not issue:
            logger.warning("Cannot block: issue not found: id=%s", issue_id)
            return None

        # Transition to blocked
        blocked = issue.transition(IssueStatus.BLOCKED)
        blocked.blocked_reason = reason
        blocked.updated_at = self.clock.now()

        saved = self.uow.issues.save(blocked)
        logger.info("Issue blocked: id=%s, reason=%s", saved.id, reason)
        return saved

    def get_stale_issues(self, days: int = 30) -> list[Issue]:
        """Get issues that haven't been updated in a specified number of days.

        Args:
            days: Number of days of inactivity to consider stale (default: 30)

        Returns:
            List of stale issues, sorted by updated_at ascending (oldest first)
        """
        logger.debug("Getting stale issues: days=%d", days)

        # Calculate cutoff time
        from datetime import timedelta

        cutoff = self.clock.now() - timedelta(days=days)

        # Use repository method that filters at SQL level
        with self.uow:
            stale_issues = self.uow.issues.list_updated_before(cutoff, limit=100000)

        logger.info("Found %d stale issues (older than %d days)", len(stale_issues), days)
        return stale_issues

    def _merge_labels(self, target: Issue, source: Issue) -> None:
        """Merge labels from source into target.

        Takes the union of labels, preserving order from target first,
        then adding any new labels from source.

        Args:
            target: Target issue to merge into
            source: Source issue to merge from
        """
        target_label_set = set(target.labels)
        new_labels = [label for label in source.labels if label not in target_label_set]
        merged_labels = target.labels + new_labels
        target.labels = merged_labels

    def _merge_descriptions(self, target: Issue, source: Issue) -> None:
        """Merge descriptions from source into target.

        Combines descriptions with a separator if both exist.

        Args:
            target: Target issue to merge into
            source: Source issue to merge from
        """
        if source.description:
            if target.description:
                separator = "\n\n---\n\n"
                target.description = target.description + separator + source.description
            else:
                target.description = source.description

    def _merge_dependencies(
        self,
        target_id: str,
        source_id: str,
        source_deps: list[Dependency],
        target_deps: list[Dependency],
        source_dependents: list[Dependency],
    ) -> None:
        """Merge dependencies from source into target.

        Remaps all dependencies to point to target instead of source.
        Skips any remapping that would create self-references.

        Args:
            target_id: Target issue ID
            source_id: Source issue ID
            source_deps: Dependencies of source issue
            target_deps: Existing dependencies of target issue
            source_dependents: Issues that depend on source
        """
        # Build sets of existing relationships for target
        target_from_to = {(d.from_issue_id, d.to_issue_id) for d in target_deps}

        # Add unique source dependencies to target
        for dep in source_deps:
            # Skip self-references after remapping
            if dep.to_issue_id == source_id:
                continue  # Source pointing to itself, skip
            if dep.to_issue_id == target_id:
                continue  # Would create self-reference, skip

            # Remap to target
            key = (target_id, dep.to_issue_id)
            if key not in target_from_to:
                new_dep = Dependency(
                    from_issue_id=target_id,
                    to_issue_id=dep.to_issue_id,
                    dependency_type=dep.dependency_type,
                    description=dep.description,
                    created_at=self.clock.now(),
                )
                self.uow.graph.add_dependency(new_dep)
                target_from_to.add(key)

        # Remap dependents (issues that depend on source) to depend on target
        for dep in source_dependents:
            # Skip self-references after remapping
            if dep.from_issue_id == target_id:
                continue  # Would create self-reference, skip

            # Remap to target
            key = (dep.from_issue_id, target_id)
            if key not in target_from_to:
                new_dep = Dependency(
                    from_issue_id=dep.from_issue_id,
                    to_issue_id=target_id,
                    dependency_type=dep.dependency_type,
                    description=dep.description,
                    created_at=self.clock.now(),
                )
                self.uow.graph.add_dependency(new_dep)
                target_from_to.add(key)

    def _copy_comments(self, source_id: str, target_id: str) -> None:
        """Copy comments from source issue to target issue.

        Each copied comment is prefixed with "[Merged from {source_id}]".

        Args:
            source_id: Source issue ID to copy comments from
            target_id: Target issue ID to copy comments to
        """
        source_comments = self.uow.comments.list_by_issue(source_id)
        for comment in source_comments:
            new_comment = Comment(
                id=self.id_service.generate("comment"),
                issue_id=target_id,
                author=comment.author,
                text=f"[Merged from {source_id}]\n{comment.text}",
                created_at=comment.created_at,
                updated_at=comment.updated_at,
            )
            self.uow.comments.save(new_comment)

    def _handle_source_disposal(
        self,
        source: Issue,
        source_id: str,
        close_source: bool,
    ) -> None:
        """Handle disposal of source issue after merge.

        Either closes or deletes the source issue based on flag.

        Args:
            source: Source issue object
            source_id: Source issue ID
            close_source: If True, close the issue; otherwise delete it
        """
        if close_source:
            source = source.transition(IssueStatus.COMPLETED)
            source.updated_at = self.clock.now()
            source.closed_at = self.clock.now()
            self.uow.issues.save(source)
            logger.info("Source issue closed: %s", source_id)
        else:
            self.uow.issues.delete(source_id)
            logger.info("Source issue deleted: %s", source_id)

    def merge_issues(
        self,
        source_id: str,
        target_id: str,
        keep_comments: bool = False,
        close_source: bool = False,
    ) -> Issue | None:
        """Merge source issue into target issue.

        Combines data from source into target:
        - Labels: union of both sets
        - Dependencies: all dependencies remapped to target
        - Comments: optionally copied from source

        Args:
            source_id: Source issue ID (to be merged from)
            target_id: Target issue ID (to be merged into)
            keep_comments: If True, copy comments from source to target
            close_source: If True, close source instead of deleting

        Returns:
            Updated target issue if successful, None otherwise

        Raises:
            ValueError: If source and target are the same
            ValueError: If either issue not found
        """
        logger.debug(
            "Merging issues: source=%s, target=%s, keep_comments=%s, close_source=%s",
            source_id,
            target_id,
            keep_comments,
            close_source,
        )

        if source_id == target_id:
            raise ValueError("Cannot merge issue into itself")

        with self.uow:
            source = self.uow.issues.get(source_id)
            target = self.uow.issues.get(target_id)

            if not source:
                raise ValueError(f"Source issue not found: {source_id}")
            if not target:
                raise ValueError(f"Target issue not found: {target_id}")

            self._merge_labels(target, source)
            self._merge_descriptions(target, source)

            source_deps = self.uow.graph.get_dependencies(source_id)
            target_deps = self.uow.graph.get_dependencies(target_id)
            source_dependents = self.uow.graph.get_dependents(source_id)
            self._merge_dependencies(
                target_id, source_id, source_deps, target_deps, source_dependents
            )

            if keep_comments:
                self._copy_comments(source_id, target_id)

            target.updated_at = self.clock.now()
            self.uow.issues.save(target)
            self._handle_source_disposal(source, source_id, close_source)

            self.uow.commit()

            logger.info("Merged %s into %s", source_id, target_id)
            return target

    def restore_issue(self, issue_id: str) -> Issue | None:
        """Restore a soft-deleted issue.

        Args:
            issue_id: Issue identifier to restore

        Returns:
            Restored issue if successful, None otherwise
        """
        logger.debug("Restoring issue: id=%s", issue_id)

        with self.uow:
            restored = self.uow.issues.restore(issue_id)
            if restored:
                # Get the restored issue to return it
                # Need to query without the deleted filter
                from dot_work.db_issues.adapters.sqlite import IssueModel

                model = self.uow.session.get(IssueModel, issue_id)
                if model:
                    issue = self.uow.issues._model_to_entity(model)
                    self.uow.commit()
                    logger.info("Issue restored: id=%s", issue_id)
                    return issue
            return None

    def list_deleted_issues(self, limit: int = 100) -> list[Issue]:
        """List soft-deleted issues.

        Args:
            limit: Maximum number of issues to return

        Returns:
            List of soft-deleted issues
        """
        logger.debug("Listing deleted issues: limit=%d", limit)
        return self.uow.issues.list_deleted(limit=limit)


__all__ = ["IssueService"]
