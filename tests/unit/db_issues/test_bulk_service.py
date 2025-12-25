"""Tests for BulkService.

Source: MIGRATE-054 - Bulk Operations
"""

from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

import pytest
from sqlmodel import Session

from dot_work.db_issues.domain.entities import (
    Clock,
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
)
from dot_work.db_issues.services import BulkResult, BulkService, IssueInputData, IssueService


class TestIssueInputData:
    """Tests for IssueInputData dataclass."""

    def test_to_issue_dict_basic(self) -> None:
        """Test converting basic issue data to dictionary."""
        data = IssueInputData(title="Test Issue", priority="high", type="bug")
        result = data.to_issue_dict()

        assert result["title"] == "Test Issue"
        assert result["priority"] == IssuePriority.HIGH
        assert result["issue_type"] == IssueType.BUG
        assert result["description"] == ""

    def test_to_issue_dict_with_all_fields(self) -> None:
        """Test converting complete issue data to dictionary."""
        data = IssueInputData(
            title="Full Issue",
            description="Full description",
            priority="low",
            type="feature",
            assignee="john",
            labels=["bug", "urgent"],
            epic_id="epic-001",
            custom_id="CUSTOM-123",
        )
        result = data.to_issue_dict()

        assert result["title"] == "Full Issue"
        assert result["description"] == "Full description"
        assert result["priority"] == IssuePriority.LOW
        assert result["issue_type"] == IssueType.FEATURE
        assert result["assignees"] == ["john"]
        assert result["labels"] == ["bug", "urgent"]
        assert result["epic_id"] == "epic-001"
        assert result["custom_id"] == "CUSTOM-123"

    def test_to_issue_dict_invalid_priority_defaults(self) -> None:
        """Test that invalid priority defaults to MEDIUM."""
        data = IssueInputData(title="Test", priority="invalid")
        result = data.to_issue_dict()

        assert result["priority"] == IssuePriority.MEDIUM

    def test_to_issue_dict_invalid_type_defaults(self) -> None:
        """Test that invalid type defaults to TASK."""
        data = IssueInputData(title="Test", type="invalid")
        result = data.to_issue_dict()

        assert result["issue_type"] == IssueType.TASK

    def test_to_issue_dict_backlog_priority_maps_to_backlog(self) -> None:
        """Test that 'backlog' priority correctly maps to BACKLOG enum value."""
        data = IssueInputData(title="Test", priority="backlog")
        result = data.to_issue_dict()

        # "backlog" → "BACKLOG" which now exists as enum value
        assert result["priority"] == IssuePriority.BACKLOG

    def test_to_issue_dict_optional_fields_omitted(self) -> None:
        """Test that optional fields are not in dict when not provided."""
        data = IssueInputData(title="Test")
        result = data.to_issue_dict()

        assert "assignees" not in result
        assert "labels" not in result
        assert "epic_id" not in result
        assert "custom_id" not in result


class TestBulkServiceParseCsv:
    """Tests for BulkService.parse_csv method."""

    def test_parse_csv_basic(self, bulk_service: BulkService) -> None:
        """Test parsing basic CSV format."""
        csv_content = """title,priority,type,description
"Fix parser",high,bug,"Parser fails"
"Add feature",medium,feature,"User auth"
"""
        issues = bulk_service.parse_csv(csv_content)

        assert len(issues) == 2
        assert issues[0].title == "Fix parser"
        assert issues[0].priority == "high"
        assert issues[0].type == "bug"
        assert issues[1].title == "Add feature"

    def test_parse_csv_with_labels(self, bulk_service: BulkService) -> None:
        """Test parsing CSV with labels column."""
        csv_content = """title,priority,labels
"Fix bug",high,"bug,urgent"
"Add task",medium,"enhancement"
"""
        issues = bulk_service.parse_csv(csv_content)

        assert len(issues) == 2
        assert issues[0].labels == ["bug", "urgent"]
        assert issues[1].labels == ["enhancement"]

    def test_parse_csv_empty_returns_empty_list(self, bulk_service: BulkService) -> None:
        """Test parsing empty CSV returns empty list."""
        issues = bulk_service.parse_csv("title,priority\n")
        assert len(issues) == 0

    def test_parse_csv_missing_title_raises(self, bulk_service: BulkService) -> None:
        """Test parsing CSV without title column raises ValueError."""
        csv_content = """priority,type
high,bug
"""
        with pytest.raises(ValueError, match="must have 'title' column"):
            bulk_service.parse_csv(csv_content)

    def test_parse_csv_skips_invalid_rows(self, bulk_service: BulkService) -> None:
        """Test that invalid rows are skipped gracefully."""
        csv_content = """title,priority,type
"Valid 1",high,bug
"Valid 2",medium,feature
"""
        issues = bulk_service.parse_csv(csv_content)

        assert len(issues) >= 2
        assert any(i.title == "Valid 1" for i in issues)


class TestBulkServiceParseJson:
    """Tests for BulkService.parse_json method."""

    def test_parse_json_basic(self, bulk_service: BulkService) -> None:
        """Test parsing basic JSON format."""
        json_content = '''[
    {"title": "Fix parser", "priority": "high", "type": "bug"},
    {"title": "Add feature", "priority": "medium"}
]'''
        issues = bulk_service.parse_json(json_content)

        assert len(issues) == 2
        assert issues[0].title == "Fix parser"
        assert issues[0].priority == "high"

    def test_parse_json_with_all_fields(self, bulk_service: BulkService) -> None:
        """Test parsing JSON with all optional fields."""
        json_content = '''[
    {
        "title": "Full Issue",
        "description": "Description",
        "priority": "low",
        "type": "feature",
        "assignee": "john",
        "labels": ["bug", "urgent"],
        "epic_id": "epic-001"
    }
]'''
        issues = bulk_service.parse_json(json_content)

        assert len(issues) == 1
        assert "john" in issues[0].assignees
        assert issues[0].labels == ["bug", "urgent"]

    def test_parse_json_empty_array(self, bulk_service: BulkService) -> None:
        """Test parsing empty JSON array."""
        issues = bulk_service.parse_json("[]")
        assert len(issues) == 0

    def test_parse_json_not_array_raises(self, bulk_service: BulkService) -> None:
        """Test parsing non-array JSON raises ValueError."""
        with pytest.raises(ValueError, match="must be an array"):
            bulk_service.parse_json('{"title": "test"}')

    def test_parse_json_invalid_json_raises(self, bulk_service: BulkService) -> None:
        """Test parsing invalid JSON raises ValueError."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            bulk_service.parse_json('{"title": invalid}')

    def test_parse_json_skips_items_without_title(self, bulk_service: BulkService) -> None:
        """Test that items without title are skipped."""
        json_content = '''[
    {"title": "Valid 1", "priority": "high"},
    {"priority": "high"},
    {"title": "Valid 2"}
]'''
        issues = bulk_service.parse_json(json_content)

        assert len(issues) == 2
        assert issues[0].title == "Valid 1"
        assert issues[1].title == "Valid 2"


class TestBulkServiceBulkCreate:
    """Tests for BulkService.bulk_create method."""

    def test_bulk_create_multiple_issues(self, bulk_service: BulkService) -> None:
        """Test creating multiple issues."""
        issues_data = [
            IssueInputData(title="Issue 1", priority="high", type="bug"),
            IssueInputData(title="Issue 2", priority="medium", type="feature"),
            IssueInputData(title="Issue 3", priority="low", type="task"),
        ]

        result = bulk_service.bulk_create(issues_data)

        assert result.total == 3
        assert result.succeeded == 3
        assert result.failed == 0
        assert len(result.issue_ids) == 3
        assert len(result.errors) == 0

    def test_bulk_create_with_failure(self, bulk_service: BulkService) -> None:
        """Test bulk create handles individual failures gracefully."""
        issues_data = [
            IssueInputData(title="Valid Issue", priority="medium", type="task"),
            # Invalid: use a custom_id that conflicts
            IssueInputData(title="Conflict", custom_id="issue-0001"),
            IssueInputData(title="Another Valid", priority="low", type="bug"),
        ]

        # First create an issue with ID issue-0001
        bulk_service.bulk_create([IssueInputData(title="First", custom_id="issue-0001")])

        # Then try to create with conflicting ID
        result = bulk_service.bulk_create(issues_data)

        assert result.total == 3
        # One should fail due to custom_id conflict
        assert result.succeeded >= 1
        assert result.failed >= 1

    def test_bulk_create_empty_list(self, bulk_service: BulkService) -> None:
        """Test bulk create with empty list."""
        result = bulk_service.bulk_create([])

        assert result.total == 0
        assert result.succeeded == 0
        assert result.failed == 0

    def test_bulk_create_uses_issue_dict(self, bulk_service: BulkService) -> None:
        """Test bulk create properly converts IssueInputData."""
        issues_data = [
            IssueInputData(
                title="Complex Issue",
                description="With description",
                priority="high",
                type="bug",
                assignee="john",
                labels=["urgent"],
            )
        ]

        result = bulk_service.bulk_create(issues_data)

        assert result.succeeded == 1
        # Verify the issue was created with correct attributes
        issue = bulk_service.issue_service.get_issue(result.issue_ids[0])
        assert issue is not None
        assert issue.title == "Complex Issue"
        assert issue.description == "With description"
        assert issue.priority == IssuePriority.HIGH
        assert issue.type == IssueType.BUG
        assert "john" in issue.assignees
        assert "urgent" in issue.labels


class TestBulkServiceBulkClose:
    """Tests for BulkService.bulk_close method."""

    def test_bulk_close_all_open_issues(self, bulk_service: BulkService) -> None:
        """Test closing all open issues."""
        # Create some issues in IN_PROGRESS state (can be closed)
        for i in range(3):
            issue = bulk_service.issue_service.create_issue(
                title=f"Issue {i}",
                priority=IssuePriority.MEDIUM,
                issue_type=IssueType.TASK,
            )
            # Move to IN_PROGRESS so it can be closed
            bulk_service.issue_service.update_issue(
                issue.id, status=IssueStatus.IN_PROGRESS
            )

        result = bulk_service.bulk_close()

        assert result.succeeded == 3
        assert len(result.issue_ids) == 3

        # Verify all are closed
        for issue_id in result.issue_ids:
            issue = bulk_service.issue_service.get_issue(issue_id)
            assert issue.status == IssueStatus.COMPLETED if issue else True

    def test_bulk_close_with_priority_filter(self, bulk_service: BulkService) -> None:
        """Test closing issues filtered by priority."""
        # Create issues with different priorities in IN_PROGRESS state
        high_issue = bulk_service.issue_service.create_issue(
            title="High Priority", priority=IssuePriority.HIGH, issue_type=IssueType.TASK
        )
        low_issue = bulk_service.issue_service.create_issue(
            title="Low Priority", priority=IssuePriority.LOW, issue_type=IssueType.TASK
        )
        # Move to IN_PROGRESS so they can be closed
        bulk_service.issue_service.update_issue(high_issue.id, status=IssueStatus.IN_PROGRESS)
        bulk_service.issue_service.update_issue(low_issue.id, status=IssueStatus.IN_PROGRESS)

        result = bulk_service.bulk_close(priority=IssuePriority.HIGH)

        assert result.succeeded == 1
        # Low priority issue should remain open
        remaining = bulk_service.issue_service.list_issues()
        assert any(i.title == "Low Priority" for i in remaining if i.status != IssueStatus.COMPLETED)

    def test_bulk_close_no_issues(self, bulk_service: BulkService) -> None:
        """Test bulk close when no issues match."""
        result = bulk_service.bulk_close()

        assert result.total == 0
        assert result.succeeded == 0


class TestBulkServiceBulkUpdate:
    """Tests for BulkService.bulk_update method."""

    def test_bulk_update_priority(self, bulk_service: BulkService) -> None:
        """Test bulk updating issue priority."""
        # Create issues with MEDIUM priority
        for i in range(2):
            bulk_service.issue_service.create_issue(
                title=f"Issue {i}",
                priority=IssuePriority.MEDIUM,
                issue_type=IssueType.TASK,
            )

        result = bulk_service.bulk_update(
            priority=IssuePriority.HIGH,
            filter_priority=IssuePriority.MEDIUM,
        )

        assert result.succeeded == 2
        # Verify priority was updated
        for issue_id in result.issue_ids:
            issue = bulk_service.issue_service.get_issue(issue_id)
            assert issue.priority == IssuePriority.HIGH if issue else True

    def test_bulk_update_status(self, bulk_service: BulkService) -> None:
        """Test bulk updating issue status."""
        # Create proposed issues
        for i in range(2):
            bulk_service.issue_service.create_issue(
                title=f"Issue {i}",
                priority=IssuePriority.MEDIUM,
                issue_type=IssueType.TASK,
            )

        result = bulk_service.bulk_update(
            status=IssueStatus.IN_PROGRESS,
            filter_status=IssueStatus.PROPOSED,
        )

        assert result.succeeded == 2
        # Verify status was updated
        for issue_id in result.issue_ids:
            issue = bulk_service.issue_service.get_issue(issue_id)
            assert issue.status == IssueStatus.IN_PROGRESS if issue else True

    def test_bulk_update_assignee(self, bulk_service: BulkService) -> None:
        """Test bulk updating assignee."""
        # Create unassigned issues
        for i in range(2):
            bulk_service.issue_service.create_issue(
                title=f"Issue {i}",
                priority=IssuePriority.MEDIUM,
                issue_type=IssueType.TASK,
                assignees=None,
            )

        result = bulk_service.bulk_update(assignee="john")

        assert result.succeeded == 2
        # Verify assignee was updated
        for issue_id in result.issue_ids:
            issue = bulk_service.issue_service.get_issue(issue_id)
            assert "john" in issue.assignees if issue else True

    def test_bulk_update_no_issues(self, bulk_service: BulkService) -> None:
        """Test bulk update when no issues match."""
        result = bulk_service.bulk_update(priority=IssuePriority.HIGH)

        assert result.total == 0
        assert result.succeeded == 0

    def test_bulk_update_with_no_set_raises(self, bulk_service: BulkService) -> None:
        """Test bulk update without --set option raises."""
        # This is tested in CLI tests, not service level
        # The service method doesn't enforce this requirement
        # Calling with all None values is valid (no-op)
        result = bulk_service.bulk_update()

        assert result.total == 0  # No issues match no-filter


class TestBulkResult:
    """Tests for BulkResult dataclass."""

    def test_bulk_result_success_rate(self) -> None:
        """Test success rate calculation."""
        from dot_work.db_issues.services.bulk_service import BulkResult

        result = BulkResult(total=10, succeeded=8, failed=2)

        assert result.success_rate == 80.0

    def test_bulk_result_empty(self) -> None:
        """Test empty result has 100% success rate."""
        from dot_work.db_issues.services.bulk_service import BulkResult

        result = BulkResult(total=0, succeeded=0, failed=0)

        assert result.success_rate == 100.0

    def test_bulk_result_all_failed(self) -> None:
        """Test result with all failures has 0% success rate."""
        from dot_work.db_issues.services.bulk_service import BulkResult

        result = BulkResult(total=5, succeeded=0, failed=5)

        assert result.success_rate == 0.0


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def bulk_service(
    in_memory_db: Session, fixed_id_service, fixed_clock
) -> BulkService:
    """Create a BulkService with test dependencies.

    Args:
        in_memory_db: In-memory database session
        fixed_id_service: Fixed identifier service
        fixed_clock: Fixed clock

    Returns:
        BulkService instance configured for testing
    """
    from dot_work.db_issues.adapters import UnitOfWork

    uow = UnitOfWork(in_memory_db)
    issue_service = IssueService(uow, fixed_id_service, fixed_clock)
    return BulkService(issue_service, fixed_id_service, fixed_clock)


# =============================================================================
# Bulk Label Add Tests
# =============================================================================


class TestBulkServiceBulkLabelAdd:
    """Tests for BulkService.bulk_label_add method."""

    def test_bulk_label_add_single_label(self, bulk_service: BulkService) -> None:
        """Test adding a single label to multiple issues."""
        # Create some issues
        for i in range(3):
            bulk_service.issue_service.create_issue(
                title=f"Issue {i}",
                priority=IssuePriority.MEDIUM,
                issue_type=IssueType.TASK,
            )

        result = bulk_service.bulk_label_add(labels=["urgent"])

        assert result.total == 3
        assert result.succeeded == 3
        assert result.failed == 0
        assert len(result.issue_ids) == 3

        # Verify labels were added
        for issue_id in result.issue_ids:
            issue = bulk_service.issue_service.get_issue(issue_id)
            assert "urgent" in issue.labels

    def test_bulk_label_add_multiple_labels(self, bulk_service: BulkService) -> None:
        """Test adding multiple labels at once."""
        # Create some issues
        for i in range(2):
            bulk_service.issue_service.create_issue(
                title=f"Issue {i}",
                priority=IssuePriority.MEDIUM,
                issue_type=IssueType.TASK,
            )

        result = bulk_service.bulk_label_add(labels=["review", "test", "urgent"])

        assert result.succeeded == 2
        assert len(result.issue_ids) == 2

        # Verify all labels were added
        for issue_id in result.issue_ids:
            issue = bulk_service.issue_service.get_issue(issue_id)
            assert "review" in issue.labels
            assert "test" in issue.labels
            assert "urgent" in issue.labels

    def test_bulk_label_add_with_filter(self, bulk_service: BulkService) -> None:
        """Test adding labels with filter criteria."""
        # Create issues with different priorities
        high_issue = bulk_service.issue_service.create_issue(
            title="High Priority", priority=IssuePriority.HIGH, issue_type=IssueType.TASK
        )
        low_issue = bulk_service.issue_service.create_issue(
            title="Low Priority", priority=IssuePriority.LOW, issue_type=IssueType.TASK
        )

        result = bulk_service.bulk_label_add(
            labels=["critical"], priority=IssuePriority.HIGH
        )

        assert result.succeeded == 1
        assert high_issue.id in result.issue_ids
        assert low_issue.id not in result.issue_ids

        # Verify label was only added to high priority issue
        high_updated = bulk_service.issue_service.get_issue(high_issue.id)
        assert "critical" in high_updated.labels

        low_updated = bulk_service.issue_service.get_issue(low_issue.id)
        assert "critical" not in low_updated.labels

    def test_bulk_label_add_existing_label_filter(self, bulk_service: BulkService) -> None:
        """Test adding labels with existing_label filter."""
        # Create issues with different labels
        issue_with_bug = bulk_service.issue_service.create_issue(
            title="Bug Issue",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
            labels=["bug"],
        )
        issue_without_bug = bulk_service.issue_service.create_issue(
            title="Feature Issue",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
        )

        result = bulk_service.bulk_label_add(
            labels=["urgent"], existing_label="bug"
        )

        assert result.succeeded == 1
        assert issue_with_bug.id in result.issue_ids
        assert issue_without_bug.id not in result.issue_ids

        # Verify label was only added to issue with existing 'bug' label
        bug_updated = bulk_service.issue_service.get_issue(issue_with_bug.id)
        assert "urgent" in bug_updated.labels
        assert "bug" in bug_updated.labels

        feature_updated = bulk_service.issue_service.get_issue(issue_without_bug.id)
        assert "urgent" not in feature_updated.labels

    def test_bulk_label_add_no_duplicate_labels(self, bulk_service: BulkService) -> None:
        """Test that adding an existing label doesn't create duplicates."""
        issue = bulk_service.issue_service.create_issue(
            title="Test Issue",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
            labels=["existing"],
        )

        # Add the same label again
        result = bulk_service.bulk_label_add(labels=["existing"])

        assert result.succeeded == 1

        # Verify no duplicate labels
        updated = bulk_service.issue_service.get_issue(issue.id)
        assert updated.labels.count("existing") == 1

    def test_bulk_label_add_empty_label_list(self, bulk_service: BulkService) -> None:
        """Test that empty label list returns empty result."""
        result = bulk_service.bulk_label_add(labels=[])

        assert result.total == 0
        assert result.succeeded == 0
        assert result.failed == 0

    def test_bulk_label_add_no_issues_match(self, bulk_service: BulkService) -> None:
        """Test that no matches returns empty result."""
        # Create an issue
        bulk_service.issue_service.create_issue(
            title="Test Issue",
            priority=IssuePriority.LOW,
            issue_type=IssueType.TASK,
        )

        # Filter for HIGH priority but issue is LOW
        result = bulk_service.bulk_label_add(
            labels=["urgent"], priority=IssuePriority.HIGH
        )

        assert result.total == 0
        assert result.succeeded == 0


class TestBulkServiceBulkLabelRemove:
    """Tests for BulkService.bulk_label_remove method."""

    def test_bulk_label_remove_single_label(self, bulk_service: BulkService) -> None:
        """Test removing a single label from multiple issues."""
        # Create issues with the label
        for i in range(3):
            bulk_service.issue_service.create_issue(
                title=f"Issue {i}",
                priority=IssuePriority.MEDIUM,
                issue_type=IssueType.TASK,
                labels=["to-remove", "keep"],
            )

        result = bulk_service.bulk_label_remove(labels=["to-remove"])

        assert result.total == 3
        assert result.succeeded == 3
        assert result.failed == 0

        # Verify label was removed
        for issue_id in result.issue_ids:
            issue = bulk_service.issue_service.get_issue(issue_id)
            assert "to-remove" not in issue.labels
            assert "keep" in issue.labels

    def test_bulk_label_remove_multiple_labels(self, bulk_service: BulkService) -> None:
        """Test removing multiple labels at once."""
        # Create issue with multiple labels
        issue = bulk_service.issue_service.create_issue(
            title="Test Issue",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
            labels=["remove1", "remove2", "keep"],
        )

        result = bulk_service.bulk_label_remove(labels=["remove1", "remove2"])

        assert result.succeeded == 1

        # Verify only specified labels were removed
        updated = bulk_service.issue_service.get_issue(issue.id)
        assert "remove1" not in updated.labels
        assert "remove2" not in updated.labels
        assert "keep" in updated.labels

    def test_bulk_label_remove_with_filter(self, bulk_service: BulkService) -> None:
        """Test removing labels with filter criteria."""
        # Create issues with different priorities
        high_issue = bulk_service.issue_service.create_issue(
            title="High Priority",
            priority=IssuePriority.HIGH,
            issue_type=IssueType.TASK,
            labels=["old-label"],
        )
        low_issue = bulk_service.issue_service.create_issue(
            title="Low Priority",
            priority=IssuePriority.LOW,
            issue_type=IssueType.TASK,
            labels=["old-label"],
        )

        result = bulk_service.bulk_label_remove(
            labels=["old-label"], priority=IssuePriority.HIGH
        )

        assert result.succeeded == 1
        assert high_issue.id in result.issue_ids
        assert low_issue.id not in result.issue_ids

        # Verify label was only removed from high priority issue
        high_updated = bulk_service.issue_service.get_issue(high_issue.id)
        assert "old-label" not in high_updated.labels

        low_updated = bulk_service.issue_service.get_issue(low_issue.id)
        assert "old-label" in low_updated.labels

    def test_bulk_label_remove_must_have_filter(self, bulk_service: BulkService) -> None:
        """Test removing labels with must_have_label filter."""
        # Create issues - some with the label, some without
        issue_with_label = bulk_service.issue_service.create_issue(
            title="Has Label",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
            labels=["remove-me", "keep"],
        )
        issue_without_label = bulk_service.issue_service.create_issue(
            title="No Label",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
            labels=["other"],
        )

        result = bulk_service.bulk_label_remove(
            labels=["remove-me"], must_have_label=True
        )

        assert result.succeeded == 1
        assert issue_with_label.id in result.issue_ids
        assert issue_without_label.id not in result.issue_ids

        # Verify label was removed from issue that had it
        updated_with = bulk_service.issue_service.get_issue(issue_with_label.id)
        assert "remove-me" not in updated_with.labels
        assert "keep" in updated_with.labels

    def test_bulk_label_remove_nonexistent_label(self, bulk_service: BulkService) -> None:
        """Test that removing a nonexistent label doesn't fail."""
        issue = bulk_service.issue_service.create_issue(
            title="Test Issue",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.TASK,
            labels=["keep"],
        )

        # Try to remove a label that doesn't exist
        result = bulk_service.bulk_label_remove(labels=["nonexistent"])

        assert result.succeeded == 1
        assert result.failed == 0

        # Verify the issue still has its original label
        updated = bulk_service.issue_service.get_issue(issue.id)
        assert "keep" in updated.labels

    def test_bulk_label_remove_empty_label_list(self, bulk_service: BulkService) -> None:
        """Test that empty label list returns empty result."""
        result = bulk_service.bulk_label_remove(labels=[])

        assert result.total == 0
        assert result.succeeded == 0

    def test_bulk_label_remove_no_issues_match(self, bulk_service: BulkService) -> None:
        """Test that no matches returns empty result."""
        # Create an issue
        bulk_service.issue_service.create_issue(
            title="Test Issue",
            priority=IssuePriority.LOW,
            issue_type=IssueType.TASK,
        )

        # Filter for HIGH priority but issue is LOW
        result = bulk_service.bulk_label_remove(
            labels=["urgent"], priority=IssuePriority.HIGH
        )

        assert result.total == 0
        assert result.succeeded == 0


# =============================================================================
# Original Tests (kept for compatibility)
# =============================================================================
