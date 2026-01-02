"""Template application service for creating issues from templates.

Provides business logic for applying instruction templates to create
parent epic issues with child tasks.

Source: .work/prompts/do-work.prompt.md
"""

import logging

from dot_issues.adapters import UnitOfWork
from dot_issues.domain.entities import (
    Clock,
    DependencyType,
    IdentifierService,
)
from dot_issues.services import EpicService, IssueService
from dot_issues.templates import InstructionTemplate

logger = logging.getLogger(__name__)


class TemplateApplicationResult:
    """Result of applying a template.

    Attributes:
        epic_id: ID of created parent epic
        issue_ids: List of created child issue IDs
        task_count: Number of tasks created
    """

    def __init__(
        self,
        epic_id: str,
        issue_ids: list[str],
        task_count: int,
    ) -> None:
        """Initialize template application result.

        Args:
            epic_id: ID of created parent epic
            issue_ids: List of created child issue IDs
            task_count: Number of tasks created
        """
        self.epic_id = epic_id
        self.issue_ids = issue_ids
        self.task_count = task_count


class TemplateService:
    """Service for applying instruction templates to create issues.

    Coordinates template parsing with epic and issue creation
    to generate structured issue hierarchies.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        id_service: IdentifierService,
        clock: Clock,
        issue_service: IssueService,
        epic_service: EpicService,
    ) -> None:
        """Initialize template service.

        Args:
            uow: Unit of work for transaction management
            id_service: Service for generating unique identifiers
            clock: Time provider for timestamps
            issue_service: Issue management service
            epic_service: Epic management service
        """
        self.uow = uow
        self.id_service = id_service
        self.clock = clock
        self.issue_service = issue_service
        self.epic_service = epic_service

    def apply_template(
        self,
        template: InstructionTemplate,
        project_id: str = "default",
        create_dependencies: bool = True,
    ) -> TemplateApplicationResult:
        """Apply a template to create epic and child issues.

        Args:
            template: Parsed instruction template
            project_id: Project identifier (default: "default")
            create_dependencies: Whether to create dependencies between tasks

        Returns:
            TemplateApplicationResult with created IDs

        Raises:
            ValueError: If template has no tasks
        """
        if not template.tasks:
            raise ValueError("Cannot apply template with no tasks")

        logger.info(
            "Applying template: name=%s, title=%s, tasks=%d",
            template.name,
            template.title,
            len(template.tasks),
        )

        # Create parent epic
        epic = self.epic_service.create_epic(
            title=template.title,
            description=template.description,
        )

        logger.info("Created parent epic: %s", epic.id)

        # Create child issues for each task
        issue_ids: list[str] = []
        previous_issue_id: str | None = None

        with self.uow:
            for task in template.tasks:
                issue_dict = task.to_issue_dict()

                # Set epic_id for child issues
                # Note: Using epic_id to associate issues with the epic
                # This is a simplified approach - proper epic association
                # would require setting the issue's epic_id field

                issue = self.issue_service.create_issue(
                    epic_id=epic.id,
                    project_id=project_id,
                    **issue_dict,
                )

                issue_ids.append(issue.id)
                logger.info("Created child issue: %s - %s", issue.id, issue.title)

                # Create dependency chain
                if create_dependencies and previous_issue_id:
                    try:
                        self.issue_service.add_dependency(
                            from_issue_id=issue.id,
                            to_issue_id=previous_issue_id,
                            dependency_type=DependencyType.DEPENDS_ON,
                        )
                        logger.debug(
                            "Created dependency: %s -> %s",
                            issue.id,
                            previous_issue_id,
                        )
                    except Exception as e:
                        logger.warning(
                            "Failed to create dependency: %s -> %s: %s",
                            issue.id,
                            previous_issue_id,
                            e,
                        )

                previous_issue_id = issue.id

            self.uow.commit()

        logger.info(
            "Template applied: epic=%s, issues=%d",
            epic.id,
            len(issue_ids),
        )

        return TemplateApplicationResult(
            epic_id=epic.id,
            issue_ids=issue_ids,
            task_count=len(issue_ids),
        )


__all__ = ["TemplateApplicationResult", "TemplateService"]
