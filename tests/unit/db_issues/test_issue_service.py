"""Tests for IssueService."""

from datetime import UTC, datetime

import pytest
from sqlmodel import Session

from dot_work.db_issues.domain.entities import (
    Clock,
    Comment,
    Dependency,
    DependencyType,
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
    NotFoundError,
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
        assert issue.assignee == "testuser"
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
            title="Issue 1", description="Test", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
        )
        issue_service.create_issue(
            title="Issue 2", description="Test", priority=IssuePriority.HIGH, issue_type=IssueType.BUG
        )

        issues = issue_service.list_issues()
        assert len(issues) == 2
        titles = {issue.title for issue in issues}
        assert "Issue 1" in titles
        assert "Issue 2" in titles

    def test_list_issues_with_status_filter(self, issue_service: IssueService) -> None:
        """Test listing issues filtered by status."""
        issue_service.create_issue(
            title="Proposed Issue", description="Test", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
        )
        closed = issue_service.create_issue(
            title="Completed Issue", description="Test", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
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
                title=f"Issue {i}", description="Test", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
            )

        issues = issue_service.list_issues(limit=3)
        assert len(issues) == 3


class TestUpdateIssue:
    """Tests for IssueService.update_issue method."""

    def test_update_issue_modifies_title(self, issue_service: IssueService) -> None:
        """Test updating an issue's title."""
        issue = issue_service.create_issue(
            title="Original", description="Test", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
        )

        updated = issue_service.update_issue(issue.id, title="Updated")
        assert updated.title == "Updated"

    def test_update_issue_modifies_description(self, issue_service: IssueService) -> None:
        """Test updating an issue's description."""
        issue = issue_service.create_issue(
            title="Test", description="Original", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
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
            title="Test", description="Test", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
        )

        updated = issue_service.update_issue(issue.id, assignee="newuser")
        assert updated.assignee == "newuser"

    def test_update_issue_not_found_returns_none(self, issue_service: IssueService) -> None:
        """Test updating a non-existent issue returns None."""
        result = issue_service.update_issue("nonexistent", title="Updated")
        assert result is None


class TestTransitionIssue:
    """Tests for IssueService.transition_issue method."""

    def test_transition_issue_changes_status(self, issue_service: IssueService) -> None:
        """Test transitioning an issue changes its status."""
        issue = issue_service.create_issue(
            title="Test", description="Test", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
        )

        transitioned = issue_service.transition_issue(issue.id, IssueStatus.IN_PROGRESS)
        assert transitioned.status == IssueStatus.IN_PROGRESS

    def test_transition_completed_sets_closed_at(self, issue_service: IssueService) -> None:
        """Test transitioning to COMPLETED sets closed_at timestamp."""
        issue = issue_service.create_issue(
            title="Test", description="Test", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
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
            title="Test", description="Test", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
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
            title="Test", description="Test", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
        )

        # First start the issue (proposed → in_progress) to enable closing
        issue_service.transition_issue(issue.id, IssueStatus.IN_PROGRESS)

        closed = issue_service.close_issue(issue.id)
        assert closed.status == IssueStatus.COMPLETED

    def test_close_issue_sets_closed_at(self, issue_service: IssueService) -> None:
        """Test closing an issue sets closed_at timestamp."""
        issue = issue_service.create_issue(
            title="Test", description="Test", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
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
            title="Test", description="Test", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
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
            title="Test", description="Test", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
        )

        comment = issue_service.add_comment(issue.id, "testuser", "This is a comment")
        assert comment is not None
        assert comment.issue_id == issue.id
        assert comment.author == "testuser"
        assert comment.text == "This is a comment"

    def test_add_comment_to_nonexistent_issue_returns_none(self, issue_service: IssueService) -> None:
        """Test adding a comment to non-existent issue returns None."""
        comment = issue_service.add_comment("nonexistent", "testuser", "Test comment")
        assert comment is None


class TestAddDependency:
    """Tests for IssueService.add_dependency method."""

    def test_add_dependency_links_issues(self, issue_service: IssueService) -> None:
        """Test adding a dependency links two issues."""
        issue1 = issue_service.create_issue(
            title="Issue 1", description="Test", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
        )
        issue2 = issue_service.create_issue(
            title="Issue 2", description="Test", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
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
            title="Test", description="Test", priority=IssuePriority.MEDIUM, issue_type=IssueType.TASK
        )

        result = issue_service.add_dependency(
            from_issue_id=issue.id, to_issue_id=issue.id, dependency_type=DependencyType.BLOCKS
        )
        assert result is None  # Self-referencing dependency returns None
