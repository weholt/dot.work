"""JSONL export/import service for db-issues module.

Provides serialization and deserialization of issues to/from JSONL format
with optional git integration for version control.

Source reference: /home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/
"""

import json
import logging
from pathlib import Path
from typing import Literal

from dot_work.db_issues.adapters import UnitOfWork
from dot_work.db_issues.domain.entities import (
    Clock,
    IdentifierService,
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
)

logger = logging.getLogger(__name__)


class JsonlService:
    """Service for JSONL export/import operations.

    Supports:
    - Export issues to JSONL format
    - Import issues from JSONL format
    - Merge vs replace strategies for imports
    - Optional git integration for auto-commit
    """

    def __init__(
        self,
        uow: UnitOfWork,
        id_service: IdentifierService,
        clock: Clock,
    ) -> None:
        """Initialize JSONL service.

        Args:
            uow: Unit of work for transaction management
            id_service: Service for generating unique identifiers
            clock: Time provider for timestamps
        """
        self.uow = uow
        self.id_service = id_service
        self.clock = clock

    def export(
        self,
        output_path: Path | str,
        include_completed: bool = True,
        status_filter: IssueStatus | None = None,
        batch_size: int = 1000,
    ) -> int:
        """Export issues to JSONL format.

        Args:
            output_path: Path to output JSONL file
            include_completed: Whether to include completed issues (default: True)
            status_filter: Optional status to filter by
            batch_size: Number of issues to load per batch (default: 1000)

        Returns:
            Number of issues exported

        Raises:
            OSError: If output file cannot be written
        """
        logger.debug(
            "Exporting issues to JSONL: output=%s, include_completed=%s, status=%s, batch_size=%d",
            output_path,
            include_completed,
            status_filter,
            batch_size,
        )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSONL with batching to avoid loading all issues into memory
        count = 0
        offset = 0

        with output_path.open("w", encoding="utf-8") as f:
            while True:
                # Get issues in batches
                if status_filter:
                    batch = self.uow.issues.list_by_status(
                        status_filter, limit=batch_size, offset=offset
                    )
                else:
                    batch = self.uow.issues.list_all(limit=batch_size, offset=offset)

                # Stop if no more issues
                if not batch:
                    break

                # Write batch to file
                for issue in batch:
                    # Filter out completed if requested
                    if not include_completed and issue.status == IssueStatus.COMPLETED:
                        continue

                    jsonl_line = self._issue_to_jsonl(issue)
                    f.write(jsonl_line + "\n")
                    count += 1

                # Move to next batch
                if len(batch) < batch_size:
                    # Last batch
                    break
                offset += batch_size

        logger.info("Exported %d issues to %s", count, output_path)
        return count

    def import_(
        self,
        input_path: Path | str,
        strategy: Literal["merge", "replace"] = "merge",
        batch_size: int = 1000,
    ) -> tuple[int, int, int]:
        """Import issues from JSONL format.

        Args:
            input_path: Path to input JSONL file
            strategy: Import strategy - "merge" (skip existing IDs) or "replace" (clear and reload)
            batch_size: Number of issues to process per batch for delete operations (default: 1000)

        Returns:
            Tuple of (created, skipped, updated) counts

        Raises:
            OSError: If input file cannot be read
            json.JSONDecodeError: If JSONL format is invalid
        """
        logger.debug(
            "Importing issues from JSONL: input=%s, strategy=%s, batch_size=%d",
            input_path,
            strategy,
            batch_size,
        )

        input_path = Path(input_path)
        if not input_path.exists():
            raise OSError(f"Input file not found: {input_path}")

        created = 0
        skipped = 0
        updated = 0

        if strategy == "replace":
            # Delete all existing issues in batches to avoid loading all into memory
            offset = 0
            deleted_count = 0
            while True:
                batch = self.uow.issues.list_all(limit=batch_size, offset=offset)
                if not batch:
                    break

                for issue in batch:
                    self.uow.issues.delete(issue.id)
                    deleted_count += 1

                if len(batch) < batch_size:
                    break
                offset += batch_size

            logger.info("Cleared %d existing issues (replace strategy)", deleted_count)

        with input_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.error("Invalid JSON on line %d: %s", line_num, e)
                    continue

                try:
                    issue = self._jsonl_to_issue(data)

                    if strategy == "merge":
                        # Check if issue exists
                        existing = self.uow.issues.get(issue.id)
                        if existing:
                            # Update existing issue
                            existing.title = issue.title
                            existing.description = issue.description
                            existing.status = issue.status
                            existing.priority = issue.priority
                            existing.type = issue.type
                            existing.assignees = issue.assignees
                            existing.labels = issue.labels
                            existing.updated_at = self.clock.now()
                            self.uow.issues.save(existing)
                            updated += 1
                        else:
                            # Create new issue
                            self.uow.issues.save(issue)
                            created += 1
                    else:  # replace
                        self.uow.issues.save(issue)
                        created += 1

                except (ValueError, KeyError) as e:
                    logger.error("Failed to import issue on line %d: %s", line_num, e)
                    continue

        logger.info(
            "Import complete: created=%d, skipped=%d, updated=%d",
            created,
            skipped,
            updated,
        )
        return created, skipped, updated

    def sync_git(
        self,
        repo_path: Path | str | None = None,
        message: str | None = None,
        push: bool = False,
    ) -> tuple[int, str]:
        """Export issues to JSONL and commit to git.

        Args:
            repo_path: Path to git repository (default: current directory)
            message: Optional custom commit message
            push: Whether to push to remote after commit

        Returns:
            Tuple of (exported count, commit hash)

        Raises:
            OSError: If git operations fail
            ImportError: If gitpython is not available
        """
        try:
            import git as gitpython
        except ImportError as e:
            raise ImportError(
                "gitpython is required for git sync. Install it with: pip install GitPython"
            ) from e

        logger.debug("Syncing issues to git: push=%s", push)

        # Export to default JSONL location
        repo_path = Path(repo_path) if repo_path else Path.cwd()
        jsonl_path = repo_path / ".work" / "db-issues" / "issues.jsonl"

        count = self.export(jsonl_path, include_completed=True)

        # Commit to git
        repo = gitpython.Repo(repo_path)

        # Check if file changed
        if jsonl_path.exists():
            repo.index.add([str(jsonl_path.relative_to(repo_path))])

        # Generate default message if not provided
        if message is None:
            from datetime import UTC, datetime

            timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
            message = f"Update issues ({count} issues) - {timestamp}"

        # Commit if there are changes
        if repo.is_dirty(untracked_files=True):
            commit = repo.index.commit(message)
            commit_hash = commit.hexsha[:8]
            logger.info("Committed changes: %s", commit_hash)
        else:
            commit_hash = "no-changes"
            logger.info("No changes to commit")

        # Push if requested
        if push and commit_hash != "no-changes":
            origin = repo.remote(name="origin")
            origin.push()
            logger.info("Pushed changes to remote")

        return count, commit_hash

    def _issue_to_jsonl(self, issue: Issue) -> str:
        """Convert issue to JSONL format.

        Args:
            issue: Issue entity

        Returns:
            JSONL string (single line JSON)
        """
        data = {
            "id": issue.id,
            "title": issue.title,
            "description": issue.description or "",
            "status": issue.status.value,
            "priority": issue.priority.value,
            "type": issue.type.value,
            "assignees": issue.assignees,
            "epic_id": issue.epic_id,
            "labels": issue.labels,
            "created_at": issue.created_at.isoformat(),
            "updated_at": issue.updated_at.isoformat(),
        }
        if issue.closed_at:
            data["closed_at"] = issue.closed_at.isoformat()

        return json.dumps(data, separators=(",", ":"))

    def _jsonl_to_issue(self, data: dict) -> Issue:
        """Convert JSONL data to Issue entity.

        Args:
            data: Parsed JSON dictionary

        Returns:
            Issue entity

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate required fields
        if "id" not in data:
            raise ValueError("Missing required field: id")
        if "title" not in data:
            raise ValueError("Missing required field: title")

        # Parse enums with fallbacks
        try:
            status = IssueStatus(data.get("status", "proposed"))
        except ValueError:
            logger.warning("Invalid status '%s', using default", data.get("status"))
            status = IssueStatus.PROPOSED

        try:
            priority = IssuePriority(data.get("priority", 2))  # Default to MEDIUM
        except ValueError:
            logger.warning("Invalid priority '%s', using default", data.get("priority"))
            priority = IssuePriority.MEDIUM

        try:
            issue_type = IssueType(data.get("type", "task"))
        except ValueError:
            logger.warning("Invalid type '%s', using default", data.get("type"))
            issue_type = IssueType.TASK

        # Parse timestamps
        from datetime import UTC, datetime

        created_at = self.clock.now()
        if "created_at" in data:
            try:
                created_at = (
                    datetime.fromisoformat(data["created_at"])
                    .replace(tzinfo=UTC)
                    .replace(tzinfo=None)
                )
            except (ValueError, AttributeError):
                logger.warning("Invalid created_at, using current time")

        updated_at = self.clock.now()
        if "updated_at" in data:
            try:
                updated_at = (
                    datetime.fromisoformat(data["updated_at"])
                    .replace(tzinfo=UTC)
                    .replace(tzinfo=None)
                )
            except (ValueError, AttributeError):
                logger.warning("Invalid updated_at, using current time")

        closed_at = None
        if "closed_at" in data and data["closed_at"]:
            try:
                closed_at = (
                    datetime.fromisoformat(data["closed_at"])
                    .replace(tzinfo=UTC)
                    .replace(tzinfo=None)
                )
            except (ValueError, AttributeError):
                logger.warning("Invalid closed_at, ignoring")

        # Handle assignee/assignees for backward compatibility
        assignees_val = data.get("assignees", [])
        if not assignees_val and "assignee" in data:
            assignee_single = data.get("assignee")
            if assignee_single:
                assignees_val = [assignee_single]

        return Issue(
            id=data["id"],
            project_id=data.get("project_id", "default"),
            title=data["title"],
            description=data.get("description", ""),
            status=status,
            priority=priority,
            type=issue_type,
            assignees=assignees_val,
            epic_id=data.get("epic_id"),
            labels=data.get("labels", []),
            created_at=created_at,
            updated_at=updated_at,
            closed_at=closed_at,
        )


__all__ = ["JsonlService"]
