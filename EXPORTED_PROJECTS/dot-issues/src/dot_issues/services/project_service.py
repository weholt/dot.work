"""Project service for project management.

Provides operations for:
- Project CRUD operations (create, update, delete, list)
- Default project management
- Project status management

Source reference: /home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/
"""

import logging

from dot_issues.adapters import UnitOfWork
from dot_issues.domain.entities import (
    Clock,
    IdentifierService,
    Project,
    ProjectStatus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Project Service
# =============================================================================


class ProjectService:
    """Service for project management operations.

    Coordinates between repositories and enforces business rules.
    All operations use UnitOfWork for transaction management.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        id_service: IdentifierService,
        clock: Clock,
    ) -> None:
        """Initialize project service.

        Args:
            uow: Unit of work for transaction management
            id_service: Service for generating unique identifiers
            clock: Time provider for timestamps
        """
        self.uow = uow
        self.id_service = id_service
        self.clock = clock

    def create_project(
        self,
        name: str,
        description: str | None = None,
        status: ProjectStatus = ProjectStatus.ACTIVE,
        set_as_default: bool = False,
    ) -> Project:
        """Create a new project.

        Args:
            name: Project name
            description: Optional project description
            status: Project status (default: ACTIVE)
            set_as_default: Whether to set as the default project

        Returns:
            Created project entity

        Raises:
            ValidationError: If name is empty
        """
        if not name or not name.strip():
            from dot_issues.domain.entities import ValidationError

            raise ValidationError("Project name cannot be empty", field="name")

        project_id = self.id_service.generate("proj")

        if set_as_default:
            # Clear existing default
            default = self.uow.projects.get_default()
            if default:
                self.uow.projects.set_default(project_id)

        project = Project(
            id=project_id,
            name=name.strip(),
            description=description.strip() if description else None,
            status=status,
            is_default=set_as_default,
            created_at=self.clock.now(),
            updated_at=self.clock.now(),
        )

        saved = self.uow.projects.save(project)
        logger.info("Created project: %s (%s)", saved.name, saved.id)
        return saved

    def get_project(self, project_id: str) -> Project | None:
        """Get a project by ID.

        Args:
            project_id: Project identifier

        Returns:
            Project entity if found, None otherwise
        """
        return self.uow.projects.get(project_id)

    def get_default_project(self) -> Project | None:
        """Get the default project.

        Returns:
            Default project entity if found, None otherwise

        Note:
            Creates a default project if none exists
        """
        project = self.uow.projects.get_default()
        if project is None:
            # Auto-create default project
            project = self.create_project(
                name="default",
                description="Default project",
                status=ProjectStatus.ACTIVE,
                set_as_default=True,
            )
            logger.info("Auto-created default project: %s", project.id)
        return project

    def list_projects(self, status: ProjectStatus | None = None) -> list[Project]:
        """List all projects or filter by status.

        Args:
            status: Optional status to filter by

        Returns:
            List of project entities
        """
        if status:
            return self.uow.projects.list_by_status(status)
        return self.uow.projects.list_all()

    def update_project(
        self,
        project_id: str,
        name: str | None = None,
        description: str | None = None,
        status: ProjectStatus | None = None,
    ) -> Project | None:
        """Update a project.

        Args:
            project_id: Project identifier
            name: New project name
            description: New project description
            status: New project status

        Returns:
            Updated project entity, or None if not found
        """
        project = self.uow.projects.get(project_id)
        if project is None:
            return None

        # Only update provided fields
        if name is not None:
            if not name.strip():
                from dot_issues.domain.entities import ValidationError

                raise ValidationError("Project name cannot be empty", field="name")
            project = Project(
                id=project.id,
                name=name.strip(),
                description=description if description is not None else project.description,
                status=status if status is not None else project.status,
                is_default=project.is_default,
                created_at=project.created_at,
                updated_at=self.clock.now(),
            )
        elif description is not None or status is not None:
            project = Project(
                id=project.id,
                name=project.name,
                description=description if description is not None else project.description,
                status=status if status is not None else project.status,
                is_default=project.is_default,
                created_at=project.created_at,
                updated_at=self.clock.now(),
            )

        saved = self.uow.projects.save(project)
        logger.info("Updated project: %s (%s)", saved.name, saved.id)
        return saved

    def delete_project(self, project_id: str) -> bool:
        """Delete a project.

        Args:
            project_id: Project identifier

        Returns:
            True if deleted, False if not found

        Raises:
            ValidationError: If trying to delete the default project
        """
        project = self.uow.projects.get(project_id)
        if project is None:
            return False

        if project.is_default:
            from dot_issues.domain.entities import ValidationError

            raise ValidationError(
                "Cannot delete the default project. Set another project as default first.",
                field="is_default",
            )

        result = self.uow.projects.delete(project_id)
        if result:
            logger.info("Deleted project: %s", project_id)
        return result

    def set_default_project(self, project_id: str) -> Project | None:
        """Set a project as the default.

        Args:
            project_id: Project identifier

        Returns:
            Updated project entity, or None if not found
        """
        project = self.uow.projects.set_default(project_id)
        if project:
            logger.info("Set default project: %s (%s)", project.name, project.id)
        return project

    def archive_project(self, project_id: str) -> Project | None:
        """Archive a project.

        Args:
            project_id: Project identifier

        Returns:
            Updated project entity, or None if not found
        """
        return self.update_project(project_id, status=ProjectStatus.ARCHIVED)

    def activate_project(self, project_id: str) -> Project | None:
        """Activate an archived project.

        Args:
            project_id: Project identifier

        Returns:
            Updated project entity, or None if not found
        """
        return self.update_project(project_id, status=ProjectStatus.ACTIVE)


__all__ = ["ProjectService", "ProjectStatus"]
