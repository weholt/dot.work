"""Tests for IssueService."""


import pytest

from dot_work.db_issues.domain.entities import (
    DependencyType,
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
)
from dot_work.db_issues.services import IssueService


class TestCreateIssue:
    """Tests for IssueService.create_issue method."""

    def test_create_issue_returns_issue(self, issue_service: IssueService) -> None:
        """Test creating an issue returns an Issue entity."""
        issue = issue_service.create_issue(
            title="Test Issue",
            description="Test description",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
            assignee=None,
            labels=[],
        )
        assert isinstance(issue, Issue)
        assert issue.title == "Test Issue"
        assert issue.description == "Test description"
        assert issue.status == IssueStatus.PROPOSED
        assert issue.id.startswith("issue-")

    def test_create_issue_with_assignee(self, issue_service: IssueService) -> None:
        """Test creating an issue with an assignee."""
        issue = issue_service.create_issue(
            title="Assigned Issue",
            description="Test",
            priority=IssuePriority.HIGH,
            issue_type=IssueType.BUG,
            assignee="testuser",
            labels=["bug"],
        )
        assert "testuser" in issue.assignees
        assert "bug" in issue.labels

    def test_create_issue_with_multiple_assignees(self, issue_service: IssueService) -> None:
        """Test creating an issue with multiple assignees."""
        issue = issue_service.create_issue(
            title="Multi-Assigned Issue",
            description="Test",
            priority=IssuePriority.HIGH,
            issue_type=IssueType.BUG,
            assignees=["user1", "user2"],
            labels=["bug"],
        )
        assert "user1" in issue.assignees
        assert "user2" in issue.assignees
        assert "bug" in issue.labels

    def test_create_issue_with_labels(self, issue_service: IssueService) -> None:
        """Test creating an issue with labels."""
        issue = issue_service.create_issue(
            title="Labeled Issue",
            description="Test",
            priority=IssuePriority.LOW,
            issue_type=IssueType.FEATURE,
            assignee=None,
            labels=["enhancement", "backlog"],
        )
        assert set(issue.labels) == {"enhancement", "backlog"}


class TestGetIssue:
    """Tests for IssueService.get_issue method."""

    def test_get_issue_returns_existing(self, issue_service: IssueService) -> None:
        """Test getting an existing issue returns the issue."""
        created = issue_service.create_issue(
            title="Test",
            description="Test",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )

        retrieved = issue_service.get_issue(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Test"

    def test_get_issue_not_found_returns_none(self, issue_service: IssueService) -> None:
        """Test getting a non-existent issue returns None."""
        result = issue_service.get_issue("nonexistent-id")
        assert result is None


class TestListIssues:
    """Tests for IssueService.list_issues method."""

    def test_list_issues_returns_all(self, issue_service: IssueService) -> None:
        """Test listing issues returns all issues."""
        issue_service.create_issue(
            title="Issue 1",
            description="Test",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )
        issue_service.create_issue(
            title="Issue 2",
            description="Test",
            priority=IssuePriority.HIGH,
            issue_type=IssueType.BUG,
        )

        issues = issue_service.list_issues()
        assert len(issues) == 2
        titles = {issue.title for issue in issues}
        assert "Issue 1" in titles
        assert "Issue 2" in titles

    def test_list_issues_with_status_filter(self, issue_service: IssueService) -> None:
        """Test listing issues filtered by status."""
        issue_service.create_issue(
            title="Proposed Issue",
            description="Test",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )
        closed = issue_service.create_issue(
            title="Completed Issue",
            description="Test",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )
        # First start, then close (follows proper workflow)
        issue_service.transition_issue(closed.id, IssueStatus.IN_PROGRESS)
        issue_service.close_issue(closed.id)

        proposed_issues = issue_service.list_issues(status=IssueStatus.PROPOSED)
        completed_issues = issue_service.list_issues(status=IssueStatus.COMPLETED)

        assert len(proposed_issues) == 1
        assert proposed_issues[0].title == "Proposed Issue"
        assert len(completed_issues) == 1
        assert completed_issues[0].title == "Completed Issue"

    def test_list_issues_with_limit(self, issue_service: IssueService) -> None:
        """Test listing issues with a limit."""
        for i in range(5):
            issue_service.create_issue(
                title=f"Issue {i}",
                description="Test",
                priority=IssuePriority.MEDIUM,
                issue_type=IssueType.TASK,
            )

        issues = issue_service.list_issues(limit=3)
        assert len(issues) == 3


class TestUpdateIssue:
    """Tests for IssueService.update_issue method."""

    def test_update_issue_modifies_title(self, issue_service: IssueService) -> None:
        """Test updating an issue's title."""
        issue = issue_service.create_issue(
            title="Original",
            description="Test",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )

        updated = issue_service.update_issue(issue.id, title="Updated")
        assert updated.title == "Updated"

    def test_update_issue_modifies_description(self, issue_service: IssueService) -> None:
        """Test updating an issue's description."""
        issue = issue_service.create_issue(
            title="Test",
            description="Original",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )

        updated = issue_service.update_issue(issue.id, description="Updated")
        assert updated.description == "Updated"

    def test_update_issue_modifies_priority(self, issue_service: IssueService) -> None:
        """Test updating an issue's priority."""
        issue = issue_service.create_issue(
            title="Test", description="Test", priority=IssuePriority.LOW, issue_type=IssueType.TASK
        )

        updated = issue_service.update_issue(issue.id, priority=IssuePriority.CRITICAL)
        assert updated.priority == IssuePriority.CRITICAL

    def test_update_issue_modifies_assignee(self, issue_service: IssueService) -> None:
        """Test updating an issue's assignee."""
        issue = issue_service.create_issue(
            title="Test",
            description="Test",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )

        updated = issue_service.update_issue(issue.id, assignees=["newuser"])
        assert "newuser" in updated.assignees

    def test_update_issue_not_found_returns_none(self, issue_service: IssueService) -> None:
        """Test updating a non-existent issue returns None."""
        result = issue_service.update_issue("nonexistent", title="Updated")
        assert result is None


class TestTransitionIssue:
    """Tests for IssueService.transition_issue method."""

    def test_transition_issue_changes_status(self, issue_service: IssueService) -> None:
        """Test transitioning an issue changes its status."""
        issue = issue_service.create_issue(
            title="Test",
            description="Test",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )

        transitioned = issue_service.transition_issue(issue.id, IssueStatus.IN_PROGRESS)
        assert transitioned.status == IssueStatus.IN_PROGRESS

    def test_transition_completed_sets_closed_at(self, issue_service: IssueService) -> None:
        """Test transitioning to COMPLETED sets closed_at timestamp."""
        issue = issue_service.create_issue(
            title="Test",
            description="Test",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )

        assert issue.closed_at is None

        # First start the issue (proposed → in_progress)
        issue_service.transition_issue(issue.id, IssueStatus.IN_PROGRESS)

        # Then close it (in_progress → completed)
        transitioned = issue_service.transition_issue(issue.id, IssueStatus.COMPLETED)
        assert transitioned.status == IssueStatus.COMPLETED
        assert transitioned.closed_at is not None

    def test_transition_invalid_status_raises_error(self, issue_service: IssueService) -> None:
        """Test that invalid transitions raise an error."""
        from dot_work.db_issues.domain.entities import InvalidTransitionError

        issue = issue_service.create_issue(
            title="Test",
            description="Test",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )

        # First mark as won't fix
        issue_service.transition_issue(issue.id, IssueStatus.WONT_FIX)

        # Then try to transition to IN_PROGRESS (invalid from WONT_FIX)
        with pytest.raises(InvalidTransitionError):
            issue_service.transition_issue(issue.id, IssueStatus.IN_PROGRESS)


class TestCloseIssue:
    """Tests for IssueService.close_issue method."""

    def test_close_issue_sets_completed_status(self, issue_service: IssueService) -> None:
        """Test closing an issue sets status to COMPLETED."""
        issue = issue_service.create_issue(
            title="Test",
            description="Test",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )

        # First start the issue (proposed → in_progress) to enable closing
        issue_service.transition_issue(issue.id, IssueStatus.IN_PROGRESS)

        closed = issue_service.close_issue(issue.id)
        assert closed.status == IssueStatus.COMPLETED

    def test_close_issue_sets_closed_at(self, issue_service: IssueService) -> None:
        """Test closing an issue sets closed_at timestamp."""
        issue = issue_service.create_issue(
            title="Test",
            description="Test",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )

        assert issue.closed_at is None

        # First start the issue (proposed → in_progress) to enable closing
        issue_service.transition_issue(issue.id, IssueStatus.IN_PROGRESS)

        closed = issue_service.close_issue(issue.id)
        assert closed.closed_at is not None


class TestDeleteIssue:
    """Tests for IssueService.delete_issue method."""

    def test_delete_issue_removes_issue(self, issue_service: IssueService) -> None:
        """Test deleting an issue removes it from storage."""
        issue = issue_service.create_issue(
            title="Test",
            description="Test",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )

        result = issue_service.delete_issue(issue.id)
        assert result is True

        # Verify issue is gone
        retrieved = issue_service.get_issue(issue.id)
        assert retrieved is None

    def test_delete_nonexistent_issue_returns_false(self, issue_service: IssueService) -> None:
        """Test deleting a non-existent issue returns False."""
        result = issue_service.delete_issue("nonexistent-id")
        assert result is False


class TestAddComment:
    """Tests for IssueService.add_comment method."""

    def test_add_comment_to_issue(self, issue_service: IssueService) -> None:
        """Test adding a comment to an issue."""
        issue = issue_service.create_issue(
            title="Test",
            description="Test",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )

        comment = issue_service.add_comment(issue.id, "testuser", "This is a comment")
        assert comment is not None
        assert comment.issue_id == issue.id
        assert comment.author == "testuser"
        assert comment.text == "This is a comment"

    def test_add_comment_to_nonexistent_issue_returns_none(
        self, issue_service: IssueService
    ) -> None:
        """Test adding a comment to non-existent issue returns None."""
        comment = issue_service.add_comment("nonexistent", "testuser", "Test comment")
        assert comment is None


class TestAddDependency:
    """Tests for IssueService.add_dependency method."""

    def test_add_dependency_links_issues(self, issue_service: IssueService) -> None:
        """Test adding a dependency links two issues."""
        issue1 = issue_service.create_issue(
            title="Issue 1",
            description="Test",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )
        issue2 = issue_service.create_issue(
            title="Issue 2",
            description="Test",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )

        dep = issue_service.add_dependency(
            from_issue_id=issue1.id, to_issue_id=issue2.id, dependency_type=DependencyType.BLOCKS
        )
        assert dep is not None
        assert dep.from_issue_id == issue1.id
        assert dep.to_issue_id == issue2.id
        assert dep.dependency_type == DependencyType.BLOCKS

    def test_add_dependency_self_referencing_fails(self, issue_service: IssueService) -> None:
        """Test that self-referencing dependencies fail."""
        issue = issue_service.create_issue(
            title="Test",
            description="Test",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )

        result = issue_service.add_dependency(
            from_issue_id=issue.id, to_issue_id=issue.id, dependency_type=DependencyType.BLOCKS
        )
        assert result is None  # Self-referencing dependency returns None


class TestSetLabels:
    """Tests for IssueService.set_labels method."""

    def test_set_labels_replaces_all_labels(self, issue_service: IssueService) -> None:
        """Test that set_labels replaces all existing labels."""
        issue = issue_service.create_issue("Test Issue", labels=["old-label", "another-old"])

        updated = issue_service.set_labels(issue.id, ["bug", "urgent", "critical"])

        assert updated is not None
        # Labels are stored in sorted order
        assert set(updated.labels) == {"bug", "urgent", "critical"}

    def test_set_labels_clears_all_labels(self, issue_service: IssueService) -> None:
        """Test that set_labels with empty list clears all labels."""
        issue = issue_service.create_issue("Test Issue", labels=["old-label", "another-old"])

        updated = issue_service.set_labels(issue.id, [])

        assert updated is not None
        assert updated.labels == []

    def test_set_labels_on_nonexistent_issue_returns_none(
        self, issue_service: IssueService
    ) -> None:
        """Test that set_labels on nonexistent issue returns None."""
        result = issue_service.set_labels("nonexistent", ["bug"])
        assert result is None

    def test_set_labels_updates_timestamp(self, issue_service: IssueService) -> None:
        """Test that set_labels updates the updated_at timestamp."""
        # Note: With fixed_clock, timestamps don't actually advance
        # We just verify that updated_at is set
        issue = issue_service.create_issue("Test Issue", labels=["old"])

        updated = issue_service.set_labels(issue.id, ["new-label"])

        assert updated is not None
        assert updated.updated_at is not None


class TestBlockIssue:
    """Tests for IssueService.block_issue method."""

    def test_block_issue_sets_blocked_status(self, issue_service: IssueService) -> None:
        """Test blocking an issue sets status to BLOCKED."""
        issue = issue_service.create_issue("Test Issue")

        blocked = issue_service.block_issue(issue.id)

        assert blocked is not None
        assert blocked.status == IssueStatus.BLOCKED

    def test_block_issue_with_reason(self, issue_service: IssueService) -> None:
        """Test blocking an issue stores the reason."""
        issue = issue_service.create_issue("Test Issue")

        blocked = issue_service.block_issue(issue.id, "Waiting for dependency")

        assert blocked is not None
        assert blocked.blocked_reason == "Waiting for dependency"

    def test_block_issue_without_reason(self, issue_service: IssueService) -> None:
        """Test blocking an issue without reason stores None."""
        issue = issue_service.create_issue("Test Issue")

        blocked = issue_service.block_issue(issue.id)

        assert blocked is not None
        assert blocked.blocked_reason is None

    def test_block_nonexistent_issue_returns_none(self, issue_service: IssueService) -> None:
        """Test blocking a nonexistent issue returns None."""
        result = issue_service.block_issue("nonexistent", "reason")
        assert result is None


class TestResolveIssue:
    """Tests for resolving issues via transition_issue."""

    def test_transition_to_resolved(self, issue_service: IssueService) -> None:
        """Test transitioning an issue to RESOLVED status."""
        issue = issue_service.create_issue("Test Issue")

        # Start the issue first (proposed -> in_progress)
        issue_service.transition_issue(issue.id, IssueStatus.IN_PROGRESS)

        # Then resolve it
        resolved = issue_service.transition_issue(issue.id, IssueStatus.RESOLVED)

        assert resolved is not None
        assert resolved.status == IssueStatus.RESOLVED

    def test_transition_to_stale(self, issue_service: IssueService) -> None:
        """Test transitioning an issue to STALE status."""
        issue = issue_service.create_issue("Test Issue")

        stale = issue_service.transition_issue(issue.id, IssueStatus.STALE)

        assert stale is not None
        assert stale.status == IssueStatus.STALE


class TestGetStaleIssues:
    """Tests for IssueService.get_stale_issues method."""

    def test_get_stale_issues_empty(self, issue_service: IssueService) -> None:
        """Test get_stale_issues returns empty list when no issues."""

        stale = issue_service.get_stale_issues(days=30)
        assert stale == []

    def test_get_stale_issues_with_old_issue(self, issue_service: IssueService) -> None:
        """Test get_stale_issues finds issues older than specified days."""
        from datetime import timedelta

        # Create an issue
        issue = issue_service.create_issue("Old Issue")

        # Manually set updated_at to be older than 30 days
        # We need to directly modify in the repository
        old_time = issue.updated_at - timedelta(days=35)
        issue.updated_at = old_time
        issue_service.uow.issues.save(issue)

        # Get stale issues
        stale = issue_service.get_stale_issues(days=30)

        assert len(stale) == 1
        assert stale[0].id == issue.id

    def test_get_stale_issues_with_recent_issue(self, issue_service: IssueService) -> None:
        """Test get_stale_issues excludes recent issues."""
        from datetime import timedelta

        # Create an issue
        issue = issue_service.create_issue("Recent Issue")

        # Set updated_at to be recent (10 days ago)
        recent_time = issue.updated_at - timedelta(days=10)
        issue.updated_at = recent_time
        issue_service.uow.issues.save(issue)

        # Get stale issues (30 day threshold)
        stale = issue_service.get_stale_issues(days=30)

        assert len(stale) == 0

    def test_get_stale_issues_sorts_by_updated_at(self, issue_service: IssueService) -> None:
        """Test get_stale_issues sorts by updated_at ascending (oldest first)."""
        from datetime import timedelta

        # Create multiple issues with different ages
        issue1 = issue_service.create_issue("Issue 1")
        issue2 = issue_service.create_issue("Issue 2")
        issue3 = issue_service.create_issue("Issue 3")

        # Set different ages
        base_time = issue_service.clock.now()
        issue1.updated_at = base_time - timedelta(days=40)
        issue2.updated_at = base_time - timedelta(days=50)
        issue3.updated_at = base_time - timedelta(days=35)

        issue_service.uow.issues.save(issue1)
        issue_service.uow.issues.save(issue2)
        issue_service.uow.issues.save(issue3)

        # Get stale issues
        stale = issue_service.get_stale_issues(days=30)

        # Should be sorted by updated_at ascending (oldest first)
        assert len(stale) == 3
        assert stale[0].id == issue2.id  # 50 days - oldest
        assert stale[1].id == issue1.id  # 40 days
        assert stale[2].id == issue3.id  # 35 days - newest
