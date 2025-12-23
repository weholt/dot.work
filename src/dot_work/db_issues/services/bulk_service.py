"""Bulk operations service for batch issue management.

Provides efficient batch operations for creating, closing, and updating
multiple issues at once with progress tracking.

Source: MIGRATE-054 - Bulk Operations
"""

import csv
import json
import logging
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import Any

from dot_work.db_issues.domain.entities import (
    Clock,
    IdentifierService,
    IssuePriority,
    IssueStatus,
    IssueType,
)
from dot_work.db_issues.services.issue_service import IssueService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BulkResult:
    """Result of a bulk operation.

    Attributes:
        total: Total number of items processed
        succeeded: Number of successful operations
        failed: Number of failed operations
        errors: List of error messages for failed items
        issue_ids: List of created/modified issue IDs
    """

    total: int
    succeeded: int
    failed: int
    errors: list[tuple[str, str]] = field(default_factory=list)  # (item, error)
    issue_ids: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total == 0:
            return 100.0
        return (self.succeeded / self.total) * 100


@dataclass
class IssueInputData:
    """Parsed issue data from input formats.

    Attributes:
        title: Issue title
        description: Issue description
        priority: Issue priority (string for parsing)
        type: Issue type (string for parsing)
        assignee: Optional assignee
        labels: Optional list of labels
        epic_id: Optional epic ID
        custom_id: Optional custom issue ID
    """

    title: str
    description: str = ""
    priority: str = "medium"
    type: str = "task"
    assignee: str | None = None
    labels: list[str] | None = None
    epic_id: str | None = None
    custom_id: str | None = None

    def to_issue_dict(self) -> dict[str, Any]:
        """Convert to dictionary for issue creation.

        Returns:
            Dictionary with parsed enum values
        """
        result: dict[str, Any] = {
            "title": self.title,
            "description": self.description,
        }

        # Parse priority
        try:
            result["priority"] = IssuePriority[self.priority.upper().replace("-", "_")]
        except (KeyError, ValueError):
            logger.warning("Invalid priority '%s', using MEDIUM", self.priority)
            result["priority"] = IssuePriority.MEDIUM

        # Parse type
        try:
            result["issue_type"] = IssueType[self.type.upper()]
        except (KeyError, ValueError):
            logger.warning("Invalid type '%s', using TASK", self.type)
            result["issue_type"] = IssueType.TASK

        # Optional fields
        if self.assignee:
            result["assignee"] = self.assignee
        if self.labels:
            result["labels"] = self.labels
        if self.epic_id:
            result["epic_id"] = self.epic_id
        if self.custom_id:
            result["custom_id"] = self.custom_id

        return result


class BulkService:
    """Service for bulk issue operations.

    Provides efficient batch creation, closing, and updating with
    progress tracking and error handling.
    """

    def __init__(
        self,
        issue_service: IssueService,
        id_service: IdentifierService,
        clock: Clock,
    ) -> None:
        """Initialize bulk service.

        Args:
            issue_service: Issue service for individual operations
            id_service: ID generator service
            clock: Time provider
        """
        self.issue_service = issue_service
        self.id_service = id_service
        self.clock = clock

    def parse_csv(self, csv_content: str) -> list[IssueInputData]:
        """Parse issues from CSV format.

        CSV format:
        ```csv
        title,priority,type,description,assignee,labels
        "Fix parser",high,bug,"Parser fails","john","bug,urgent"
        "Add feature",medium,feature,"User auth",,
        ```

        Args:
            csv_content: CSV string content

        Returns:
            List of parsed issue data

        Raises:
            ValueError: If CSV format is invalid
        """
        issues: list[IssueInputData] = []

        reader = csv.DictReader(StringIO(csv_content))
        if not reader.fieldnames:
            raise ValueError("CSV has no columns")

        # Validate required columns
        if "title" not in reader.fieldnames:
            raise ValueError("CSV must have 'title' column")

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
            try:
                # Parse labels if present
                labels = None
                if "labels" in row and row["labels"]:
                    labels = [label.strip() for label in row["labels"].split(",") if label.strip()]

                issue_data = IssueInputData(
                    title=row["title"],
                    description=row.get("description", ""),
                    priority=row.get("priority", "medium"),
                    type=row.get("type", "task"),
                    assignee=row.get("assignee") or None,
                    labels=labels,
                    epic_id=row.get("epic_id") or None,
                    custom_id=row.get("id") or None,
                )
                issues.append(issue_data)
            except Exception as e:
                logger.warning("Skipping invalid CSV row %d: %s", row_num, e)

        logger.info("Parsed %d issues from CSV", len(issues))
        return issues

    def parse_json(self, json_content: str) -> list[IssueInputData]:
        """Parse issues from JSON format.

        JSON format:
        ```json
        [
          {"title": "Fix parser", "priority": "high", "type": "bug"},
          {"title": "Add feature", "priority": "medium", "type": "feature"}
        ]
        ```

        Args:
            json_content: JSON string content

        Returns:
            List of parsed issue data

        Raises:
            ValueError: If JSON format is invalid
        """
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e

        if not isinstance(data, list):
            raise ValueError("JSON must be an array of issue objects")

        issues: list[IssueInputData] = []

        for idx, item in enumerate(data):
            try:
                if not isinstance(item, dict):
                    logger.warning("Skipping non-dict item at index %d", idx)
                    continue

                if "title" not in item:
                    logger.warning("Skipping item at index %d: missing 'title'", idx)
                    continue

                issue_data = IssueInputData(
                    title=item["title"],
                    description=item.get("description", ""),
                    priority=item.get("priority", "medium"),
                    type=item.get("type", "task"),
                    assignee=item.get("assignee"),
                    labels=item.get("labels"),
                    epic_id=item.get("epic_id"),
                    custom_id=item.get("id"),
                )
                issues.append(issue_data)
            except Exception as e:
                logger.warning("Skipping invalid JSON item at index %d: %s", idx, e)

        logger.info("Parsed %d issues from JSON", len(issues))
        return issues

    def parse_file(self, file_path: str | Path) -> list[IssueInputData]:
        """Parse issues from CSV or JSON file.

        Args:
            file_path: Path to input file

        Returns:
            List of parsed issue data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        content = path.read_text(encoding="utf-8")

        # Detect format from extension
        if path.suffix.lower() == ".csv":
            return self.parse_csv(content)
        elif path.suffix.lower() == ".json":
            return self.parse_json(content)
        else:
            # Try to parse as JSON first, then CSV
            try:
                return self.parse_json(content)
            except ValueError:
                try:
                    return self.parse_csv(content)
                except ValueError:
                    raise ValueError(f"Unsupported file format: {path.suffix}") from None

    def bulk_create(self, issues_data: list[IssueInputData]) -> BulkResult:
        """Create multiple issues in batch.

        Args:
            issues_data: List of issue data to create

        Returns:
            Bulk operation result with success/failure counts
        """
        total = len(issues_data)
        succeeded = 0
        failed = 0
        errors: list[tuple[str, str]] = []
        issue_ids: list[str] = []

        for idx, issue_data in enumerate(issues_data, start=1):
            try:
                logger.debug(
                    "Creating issue %d/%d: %s",
                    idx,
                    total,
                    issue_data.title[:50],
                )
                issue_dict = issue_data.to_issue_dict()
                issue = self.issue_service.create_issue(**issue_dict)
                issue_ids.append(issue.id)
                succeeded += 1
            except Exception as e:
                failed += 1
                errors.append((issue_data.title, str(e)))
                logger.warning("Failed to create issue %d: %s", idx, e)

        logger.info(
            "Bulk create complete: %d/%d succeeded, %d failed",
            succeeded,
            total,
            failed,
        )

        return BulkResult(
            total=total,
            succeeded=succeeded,
            failed=failed,
            errors=errors,
            issue_ids=issue_ids,
        )

    def bulk_close(
        self,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        issue_type: IssueType | None = None,
        assignee: str | None = None,
        limit: int = 1000,
    ) -> BulkResult:
        """Close multiple issues by filter criteria.

        Args:
            status: Filter by status (default: only open issues)
            priority: Filter by priority
            issue_type: Filter by issue type
            assignee: Filter by assignee
            limit: Maximum issues to process

        Returns:
            Bulk operation result
        """
        # Default to closing only open/proposed/in-progress issues
        if status is None:
            # List all issues with filters and filter by status in code
            all_issues = self.issue_service.list_issues(
                priority=priority,
                assignee=assignee,
                issue_type=issue_type,
                limit=limit,
            )
            issues_to_close = [
                i for i in all_issues if i.status in (IssueStatus.PROPOSED, IssueStatus.IN_PROGRESS)
            ]
        else:
            issues_to_close = self.issue_service.list_issues(
                status=status,
                priority=priority,
                assignee=assignee,
                issue_type=issue_type,
                limit=limit,
            )

        total = len(issues_to_close)
        if total == 0:
            logger.info("No issues found matching close criteria")
            return BulkResult(total=0, succeeded=0, failed=0)

        succeeded = 0
        failed = 0
        errors: list[tuple[str, str]] = []
        issue_ids: list[str] = []

        for idx, issue in enumerate(issues_to_close, start=1):
            try:
                logger.debug(
                    "Closing issue %d/%d: %s (%s)",
                    idx,
                    total,
                    issue.id,
                    issue.title[:50],
                )
                result = self.issue_service.close_issue(issue.id)
                if result:
                    issue_ids.append(issue.id)
                    succeeded += 1
                else:
                    failed += 1
                    errors.append((issue.id, "Failed to close"))
            except Exception as e:
                failed += 1
                errors.append((issue.id, str(e)))
                logger.warning("Failed to close issue %s: %s", issue.id, e)

        logger.info(
            "Bulk close complete: %d/%d succeeded, %d failed",
            succeeded,
            total,
            failed,
        )

        return BulkResult(
            total=total,
            succeeded=succeeded,
            failed=failed,
            errors=errors,
            issue_ids=issue_ids,
        )

    def bulk_update(
        self,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        issue_type: IssueType | None = None,
        assignee: str | None = None,
        epic_id: str | None = None,
        filter_status: IssueStatus | None = None,
        filter_priority: IssuePriority | None = None,
        filter_type: IssueType | None = None,
        filter_assignee: str | None = None,
        limit: int = 1000,
    ) -> BulkResult:
        """Update multiple issues by filter criteria.

        Args:
            status: New status to set
            priority: New priority to set
            issue_type: New issue type to set
            assignee: New assignee to set
            epic_id: New epic ID to set
            filter_status: Filter by current status
            filter_priority: Filter by current priority
            filter_type: Filter by current type
            filter_assignee: Filter by current assignee
            limit: Maximum issues to process

        Returns:
            Bulk operation result
        """
        # Get issues matching filter criteria
        issues_to_update = self.issue_service.list_issues(
            status=filter_status,
            priority=filter_priority,
            issue_type=filter_type,
            assignee=filter_assignee,
            limit=limit,
        )

        total = len(issues_to_update)
        if total == 0:
            logger.info("No issues found matching update criteria")
            return BulkResult(total=0, succeeded=0, failed=0)

        succeeded = 0
        failed = 0
        errors: list[tuple[str, str]] = []
        issue_ids: list[str] = []

        for idx, issue in enumerate(issues_to_update, start=1):
            try:
                logger.debug(
                    "Updating issue %d/%d: %s (%s)",
                    idx,
                    total,
                    issue.id,
                    issue.title[:50],
                )
                result = self.issue_service.update_issue(
                    issue.id,
                    status=status,
                    priority=priority,
                    type=issue_type,
                    assignee=assignee,
                    epic_id=epic_id,
                )
                if result:
                    issue_ids.append(issue.id)
                    succeeded += 1
                else:
                    failed += 1
                    errors.append((issue.id, "Failed to update"))
            except Exception as e:
                failed += 1
                errors.append((issue.id, str(e)))
                logger.warning("Failed to update issue %s: %s", issue.id, e)

        logger.info(
            "Bulk update complete: %d/%d succeeded, %d failed",
            succeeded,
            total,
            failed,
        )

        return BulkResult(
            total=total,
            succeeded=succeeded,
            failed=failed,
            errors=errors,
            issue_ids=issue_ids,
        )


__all__ = [
    "BulkService",
    "BulkResult",
    "IssueInputData",
]
