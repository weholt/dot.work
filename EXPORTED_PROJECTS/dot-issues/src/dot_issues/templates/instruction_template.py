"""Instruction template parser for creating structured issues from markdown templates.

Parses markdown files with YAML frontmatter to extract template metadata
and tasks for creating parent epic issues with child issues.

Source: .work/prompts/do-work.prompt.md
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from dot_issues.domain.entities import (
    IssuePriority,
    IssueStatus,
    IssueType,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TaskMetadata:
    """Metadata for a single task extracted from a template.

    Attributes:
        title: Task title
        description: Task description (may be None)
        priority: Task priority level
        task_type: Task type/issue type
        assignee: Optional assignee username
        labels: Optional list of labels
        acceptance_criteria: List of acceptance criteria items
    """

    title: str
    description: str | None
    priority: IssuePriority
    task_type: IssueType
    assignee: str | None
    labels: list[str] | None
    acceptance_criteria: list[str]

    def to_issue_dict(self) -> dict:
        """Convert to dictionary for issue creation.

        Returns:
            Dictionary with issue fields matching IssueService.create_issue signature
        """
        return {
            "title": self.title,
            "description": self.description or "",
            "priority": self.priority,
            "issue_type": self.task_type,
            "assignee": self.assignee,
            "labels": self.labels or [],
        }


@dataclass(frozen=True)
class InstructionTemplate:
    """Parsed instruction template.

    Attributes:
        name: Template name (from filename or frontmatter)
        title: Epic title
        description: Epic description
        tasks: List of tasks extracted from template
        raw_content: Original markdown content
        source_path: Path to template file
    """

    name: str
    title: str
    description: str | None
    tasks: list[TaskMetadata]
    raw_content: str
    source_path: Path

    @property
    def task_count(self) -> int:
        """Return number of tasks in template."""
        return len(self.tasks)


class TemplateParseError(Exception):
    """Raised when template parsing fails."""

    def __init__(
        self, message: str, path: str | None = None, line_number: int | None = None
    ) -> None:
        """Initialize parse error.

        Args:
            message: Error message
            path: Optional path to template file
            line_number: Optional line number where error occurred
        """
        self.path = path
        self.line_number = line_number
        full_message = message
        if path:
            full_message = f"{path}: {message}"
        if line_number:
            full_message = f"{full_message} (line {line_number})"
        super().__init__(full_message)


class InstructionTemplateParser:
    """Parser for instruction templates with YAML frontmatter.

    Template format:
    ```markdown
    ---
    name: template-name
    title: Epic Title
    description: Optional epic description
    priority: medium  # default priority for tasks
    type: task  # default type for tasks
    assignee: username  # optional default assignee
    labels: [label1, label2]  # optional default labels
    ---

    # Template content

    ## Tasks

    ### Task 1: First task

    Task description here.

    ### Task 2: Second task

    - [ ] Acceptance criterion 1
    - [ ] Acceptance criterion 2
    ```
    """

    # Default values for unspecified fields
    DEFAULT_PRIORITY = IssuePriority.MEDIUM
    DEFAULT_TYPE = IssueType.TASK
    DEFAULT_STATUS = IssueStatus.PROPOSED

    # Regex patterns for parsing
    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
    TASK_HEADER_PATTERN = re.compile(r"^###\s+Task\s+\d+:\s*(.+)$", re.MULTILINE)
    CHECKBOX_PATTERN = re.compile(r"^-\s*\[[ xX]\]\s*(.+)$", re.MULTILINE)

    def parse(self, template_path: str | Path) -> InstructionTemplate:
        """Parse an instruction template from file.

        Args:
            template_path: Path to template markdown file

        Returns:
            Parsed InstructionTemplate

        Raises:
            TemplateParseError: If parsing fails
        """
        path = Path(template_path)
        if not path.exists():
            raise TemplateParseError(f"Template not found: {path}")

        content = path.read_text(encoding="utf-8")
        return self.parse_content(content, path)

    def parse_content(self, content: str, source_path: Path | None = None) -> InstructionTemplate:
        """Parse instruction template from markdown content.

        Args:
            content: Markdown content with YAML frontmatter
            source_path: Optional source path for error reporting

        Returns:
            Parsed InstructionTemplate

        Raises:
            TemplateParseError: If parsing fails
        """
        # Extract frontmatter and content
        frontmatter_match = self.FRONTMATTER_PATTERN.match(content)
        if not frontmatter_match:
            raise TemplateParseError(
                "Invalid template format: missing YAML frontmatter",
                path=str(source_path) if source_path else None,
            )

        frontmatter_text = frontmatter_match.group(1)
        body_content = frontmatter_match.group(2)

        # Parse frontmatter
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
            if not isinstance(frontmatter, dict):
                raise TemplateParseError(
                    "Invalid frontmatter: must be a YAML dictionary",
                    path=str(source_path) if source_path else None,
                )
        except yaml.YAMLError as e:
            raise TemplateParseError(
                f"Invalid YAML in frontmatter: {e}",
                path=str(source_path) if source_path else None,
            ) from None

        # Extract template metadata
        name = frontmatter.get("name", source_path.stem if source_path else "unnamed")
        title = frontmatter.get("title", "Untitled Template")
        description = frontmatter.get("description")
        default_priority = self._parse_priority(frontmatter.get("priority"))
        default_type = self._parse_type(frontmatter.get("type"))
        default_assignee = frontmatter.get("assignee")
        default_labels = frontmatter.get("labels")

        # Parse tasks from body
        tasks = self._parse_tasks(
            body_content,
            default_priority,
            default_type,
            default_assignee,
            default_labels,
            str(source_path) if source_path else None,
        )

        return InstructionTemplate(
            name=name,
            title=title,
            description=description,
            tasks=tasks,
            raw_content=content,
            source_path=source_path or Path(""),
        )

    def _parse_priority(self, value: str | None) -> IssuePriority:
        """Parse priority string to enum.

        Args:
            value: Priority string value

        Returns:
            IssuePriority enum value

        Raises:
            TemplateParseError: If priority is invalid
        """
        if not value:
            return self.DEFAULT_PRIORITY

        try:
            # Normalize priority string
            normalized = value.upper().replace("-", "_")
            return IssuePriority[normalized]
        except KeyError:
            valid_values = [str(p.value) for p in IssuePriority]
            raise TemplateParseError(
                f"Invalid priority: {value}. Valid values: {', '.join(valid_values)}"
            ) from None

    def _parse_type(self, value: str | None) -> IssueType:
        """Parse type string to enum.

        Args:
            value: Type string value

        Returns:
            IssueType enum value

        Raises:
            TemplateParseError: If type is invalid
        """
        if not value:
            return self.DEFAULT_TYPE

        try:
            normalized = value.upper()
            return IssueType[normalized]
        except KeyError:
            valid_values = [t.value for t in IssueType]
            raise TemplateParseError(
                f"Invalid type: {value}. Valid values: {', '.join(valid_values)}"
            ) from None

    def _parse_tasks(
        self,
        body: str,
        default_priority: IssuePriority,
        default_type: IssueType,
        default_assignee: str | None,
        default_labels: list[str] | None,
        source_path: str | None,
    ) -> list[TaskMetadata]:
        """Parse tasks from template body content.

        Args:
            body: Template body content
            default_priority: Default priority for tasks
            default_type: Default type for tasks
            default_assignee: Default assignee for tasks
            default_labels: Default labels for tasks
            source_path: Optional source path for error reporting

        Returns:
            List of TaskMetadata objects
        """
        tasks: list[TaskMetadata] = []

        # Find all task headers
        for match in self.TASK_HEADER_PATTERN.finditer(body):
            title = match.group(1).strip()
            start_pos = match.end()

            # Find the next task header or end of content
            next_match = self.TASK_HEADER_PATTERN.search(body, start_pos)
            end_pos = next_match.start() if next_match else len(body)

            # Extract task content
            task_content = body[start_pos:end_pos].strip()

            # Extract acceptance criteria from checkboxes
            acceptance_criteria: list[str] = []
            description_lines: list[str] = []

            for line in task_content.split("\n"):
                checkbox_match = self.CHECKBOX_PATTERN.match(line)
                if checkbox_match:
                    acceptance_criteria.append(checkbox_match.group(1).strip())
                elif line.strip() and not line.strip().startswith("#"):
                    description_lines.append(line)

            # Build description from non-checkbox lines
            description = "\n".join(description_lines).strip() or None

            # Add acceptance criteria to description if present
            if acceptance_criteria:
                if description:
                    description += "\n\n**Acceptance Criteria:**\n" + "\n".join(
                        f"- [ ] {c}" for c in acceptance_criteria
                    )
                else:
                    description = "**Acceptance Criteria:**\n" + "\n".join(
                        f"- [ ] {c}" for c in acceptance_criteria
                    )

            tasks.append(
                TaskMetadata(
                    title=title,
                    description=description,
                    priority=default_priority,
                    task_type=default_type,
                    assignee=default_assignee,
                    labels=default_labels,
                    acceptance_criteria=acceptance_criteria,
                )
            )

        if not tasks:
            logger.warning("No tasks found in template")
            if source_path:
                logger.warning(f"  Source: {source_path}")

        return tasks


__all__ = [
    "InstructionTemplate",
    "InstructionTemplateParser",
    "TaskMetadata",
    "TemplateParseError",
]
