"""JSON template entity for saving and reusing issue configurations.

Stores predefined issue configurations as JSON templates for quick reuse.

Source: MIGRATE-053 - JSON Template Management
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from dot_issues.domain.entities import (
    IssuePriority,
    IssueType,
)


@dataclass(frozen=True)
class JsonTemplate:
    """A JSON template for predefined issue configurations.

    Attributes:
        name: Template name (unique identifier)
        description: Template description
        defaults: Default values for issues (type, priority, labels, etc.)
        description_template: Optional template for issue description body
        source_path: Path to template JSON file
    """

    name: str
    description: str
    defaults: dict[str, Any]
    description_template: str | None = None
    source_path: Path = field(default_factory=lambda: Path(""))

    @property
    def priority(self) -> IssuePriority:
        """Get default priority from template defaults."""
        value = self.defaults.get("priority", "medium")
        try:
            return IssuePriority[value.upper().replace("-", "_")]
        except (ValueError, KeyError):
            return IssuePriority.MEDIUM

    @property
    def issue_type(self) -> IssueType:
        """Get default issue type from template defaults."""
        value = self.defaults.get("type", "task")
        try:
            return IssueType(value.lower())
        except ValueError:
            return IssueType.TASK

    @property
    def labels(self) -> list[str]:
        """Get default labels from template defaults."""
        return self.defaults.get("labels", [])

    def to_dict(self) -> dict[str, Any]:
        """Convert template to dictionary for JSON serialization.

        Returns:
            Dictionary representation of template
        """
        return {
            "name": self.name,
            "description": self.description,
            "defaults": self.defaults,
            "description_template": self.description_template,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], source_path: Path) -> "JsonTemplate":
        """Create template from dictionary.

        Args:
            data: Dictionary containing template data
            source_path: Path to template file

        Returns:
            JsonTemplate instance

        Raises:
            ValueError: If required fields are missing
        """
        if "name" not in data:
            raise ValueError("Template missing required field: 'name'")

        return cls(
            name=data["name"],
            description=data.get("description", ""),
            defaults=data.get("defaults", {}),
            description_template=data.get("description_template"),
            source_path=source_path,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "JsonTemplate":
        """Load template from JSON or YAML file.

        Args:
            path: Path to template file

        Returns:
            JsonTemplate instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {path}")

        content = path.read_text(encoding="utf-8")

        # Try JSON first, then YAML
        try:
            import json

            data = json.loads(content)
        except json.JSONDecodeError:
            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid template file: {e}") from e

        return cls.from_dict(data, path)

    def to_file(self, path: str | Path | None = None) -> Path:
        """Save template to JSON file.

        Args:
            path: Optional path to save to. Defaults to source_path or .work/db-issues/templates/<name>.json

        Returns:
            Path where template was saved
        """
        if path is None:
            if self.source_path and self.source_path.exists():
                path = self.source_path
            else:
                templates_dir = Path(".work/db-issues/templates")
                templates_dir.mkdir(parents=True, exist_ok=True)
                path = templates_dir / f"{self.name}.json"
        else:
            path = Path(path)

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        import json

        content = json.dumps(self.to_dict(), indent=2)
        path.write_text(content, encoding="utf-8")

        return path


__all__ = ["JsonTemplate"]
