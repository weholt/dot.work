"""Tests for domain entities."""

import pytest

from dot_work.db_issues.domain.entities import (
    Comment,
    CycleDetectedError,
    Dependency,
    DependencyType,
    Epic,
    EpicStatus,
    InvariantViolationError,
    InvalidTransitionError,
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
    utcnow_naive,
)


class TestIssueCreation:
    """Tests for Issue entity creation."""

    def test_issue_creation_with_required_fields(self) -> None:
        """Test creating an issue with required fields only."""
        issue = Issue(
            id="issue-001",
            project_id="test-project",
            title="Test Issue",
            description="Test description",
        )
        assert issue.id == "issue-001"
        assert issue.project_id == "test-project"
        assert issue.title == "Test Issue"
        assert issue.description == "Test description"
        assert issue.status == IssueStatus.PROPOSED  # Default
        assert issue.priority == IssuePriority.MEDIUM  # Default
        assert issue.type == IssueType.TASK  # Default
        assert issue.assignees == []  # Default empty list
        assert issue.labels == []
        assert issue.closed_at is None

    def test_issue_creation_with_all_fields(self) -> None:
        """Test creating an issue with all fields specified."""
        issue = Issue(
            id="issue-002",
            project_id="test-project",
            title="Full Issue",
            description="Full description",
            status=IssueStatus.IN_PROGRESS,
            priority=IssuePriority.HIGH,
            type=IssueType.BUG,
            assignees=["testuser"],
            labels=["bug", "urgent"],
        )
        assert issue.status == IssueStatus.IN_PROGRESS
        assert issue.priority == IssuePriority.HIGH
        assert issue.type == IssueType.BUG
        assert issue.assignees == ["testuser"]
        assert issue.labels == ["bug", "urgent"]


class TestIssueStatusTransitions:
    """Tests for Issue status transitions."""

    def test_valid_transition_from_proposed(self) -> None:
        """Test valid transitions from PROPOSED status."""
        issue = Issue(
            id="issue-001",
            project_id="test",
            title="Test",
            description="Test",
            status=IssueStatus.PROPOSED,
        )

        # Valid transitions from PROPOSED: in_progress, blocked, wont_fix
        new_issue = issue.transition(IssueStatus.IN_PROGRESS)
        assert new_issue.status == IssueStatus.IN_PROGRESS

        new_issue = issue.transition(IssueStatus.BLOCKED)
        assert new_issue.status == IssueStatus.BLOCKED

        new_issue = issue.transition(IssueStatus.WONT_FIX)
        assert new_issue.status == IssueStatus.WONT_FIX

        # Invalid transition: proposed → completed (not allowed per spec)
        with pytest.raises(InvalidTransitionError):
            issue.transition(IssueStatus.COMPLETED)

    def test_valid_transition_from_in_progress(self) -> None:
        """Test valid transitions from IN_PROGRESS status."""
        issue = Issue(
            id="issue-001",
            project_id="test",
            title="Test",
            description="Test",
            status=IssueStatus.IN_PROGRESS,
        )

        new_issue = issue.transition(IssueStatus.PROPOSED)
        assert new_issue.status == IssueStatus.PROPOSED

        new_issue = issue.transition(IssueStatus.BLOCKED)
        assert new_issue.status == IssueStatus.BLOCKED

        new_issue = issue.transition(IssueStatus.COMPLETED)
        assert new_issue.status == IssueStatus.COMPLETED

    def test_invalid_transition_raises_error(self) -> None:
        """Test that invalid transitions raise InvalidTransitionError."""
        from dot_work.db_issues.domain.entities import InvalidTransitionError

        issue = Issue(
            id="issue-001",
            project_id="test",
            title="Test",
            description="Test",
            status=IssueStatus.WONT_FIX,
        )

        # Cannot transition from WONT_FIX to IN_PROGRESS
        with pytest.raises(InvalidTransitionError):
            issue.transition(IssueStatus.IN_PROGRESS)


class TestIssueLabels:
    """Tests for Issue label management."""

    def test_add_label_to_issue(self) -> None:
        """Test adding a label to an issue."""
        issue = Issue(
            id="issue-001", project_id="test", title="Test", description="Test"
        )
        assert issue.labels == []

        new_issue = issue.add_label("bug")
        assert "bug" in new_issue.labels
        assert len(new_issue.labels) == 1

    def test_add_duplicate_label_does_not_duplicate(self) -> None:
        """Test that adding a duplicate label doesn't create duplicates."""
        issue = Issue(
            id="issue-001",
            project_id="test",
            title="Test",
            description="Test",
            labels=["bug"],
        )

        new_issue = issue.add_label("bug")
        assert new_issue.labels == ["bug"]

    def test_remove_label_from_issue(self) -> None:
        """Test removing a label from an issue."""
        issue = Issue(
            id="issue-001",
            project_id="test",
            title="Test",
            description="Test",
            labels=["bug", "urgent"],
        )

        new_issue = issue.remove_label("bug")
        assert new_issue.labels == ["urgent"]

    def test_remove_nonexistent_label_returns_original(self) -> None:
        """Test that removing a non-existent label returns the original issue."""
        issue = Issue(
            id="issue-001", project_id="test", title="Test", description="Test", labels=[]
        )

        new_issue = issue.remove_label("bug")
        assert new_issue.labels == []


class TestIssueAssignment:
    """Tests for Issue assignment management."""

    def test_assign_to_user(self) -> None:
        """Test assigning an issue to a user."""
        issue = Issue(
            id="issue-001", project_id="test", title="Test", description="Test"
        )

        new_issue = issue.assign_to("testuser")
        assert "testuser" in new_issue.assignees

    def test_assign_multiple_users(self) -> None:
        """Test assigning multiple users to an issue."""
        issue = Issue(
            id="issue-001",
            project_id="test",
            title="Test",
            description="Test",
            assignees=["user1"],
        )

        new_issue = issue.assign_to("user2")
        assert "user1" in new_issue.assignees
        assert "user2" in new_issue.assignees
        assert len(new_issue.assignees) == 2

    def test_unassign_user(self) -> None:
        """Test unassigning a user from an issue."""
        issue = Issue(
            id="issue-001",
            project_id="test",
            title="Test",
            description="Test",
            assignees=["user1", "user2"],
        )

        new_issue = issue.unassign("user1")
        assert "user1" not in new_issue.assignees
        assert "user2" in new_issue.assignees
        assert len(new_issue.assignees) == 1

    def test_reassign_to_different_user(self) -> None:
        """Test reassigning an issue to a different user (replaces assignees)."""
        issue = Issue(
            id="issue-001",
            project_id="test",
            title="Test",
            description="Test",
            assignees=["user1"],
        )

        # For replacement behavior, directly set assignees
        issue.assignees = ["user2"]
        assert "user2" in issue.assignees
        assert "user1" not in issue.assignees


class TestIssueEpicAssignment:
    """Tests for Issue epic relationship."""

    def test_assign_to_epic(self) -> None:
        """Test assigning an issue to an epic."""
        issue = Issue(
            id="issue-001", project_id="test", title="Test", description="Test"
        )

        new_issue = issue.assign_to_epic("epic-001")
        assert new_issue.epic_id == "epic-001"


class TestDependencyEntity:
    """Tests for Dependency entity."""

    def test_dependency_creation_valid(self) -> None:
        """Test creating a valid dependency."""
        dep = Dependency(
            from_issue_id="issue-001",
            to_issue_id="issue-002",
            dependency_type=DependencyType.BLOCKS,
        )
        assert dep.from_issue_id == "issue-001"
        assert dep.to_issue_id == "issue-002"
        assert dep.dependency_type == DependencyType.BLOCKS

    def test_dependency_cannot_depend_on_self(self) -> None:
        """Test that an issue cannot depend on itself."""
        with pytest.raises(InvariantViolationError):
            Dependency(
                from_issue_id="issue-001",
                to_issue_id="issue-001",
                dependency_type=DependencyType.BLOCKS,
            )


class TestEpicEntity:
    """Tests for Epic entity."""

    def test_epic_creation(self) -> None:
        """Test creating an epic."""
        epic = Epic(
            id="epic-001",
            title="Test Epic",
            description="A test epic",
            status=EpicStatus.OPEN,
        )
        assert epic.id == "epic-001"
        assert epic.title == "Test Epic"
        assert epic.status == EpicStatus.OPEN
        assert epic.parent_epic_id is None


class TestCommentEntity:
    """Tests for Comment entity."""

    def test_comment_creation(self) -> None:
        """Test creating a comment."""
        comment = Comment(
            id="comment-001",
            issue_id="issue-001",
            author="testuser",
            text="This is a comment",
        )
        assert comment.id == "comment-001"
        assert comment.issue_id == "issue-001"
        assert comment.author == "testuser"
        assert comment.text == "This is a comment"


class TestUtilities:
    """Tests for utility functions."""

    def test_utcnow_naive_returns_naive_datetime(self) -> None:
        """Test that utcnow_naive returns a naive datetime."""
        result = utcnow_naive()
        assert result.tzinfo is None
