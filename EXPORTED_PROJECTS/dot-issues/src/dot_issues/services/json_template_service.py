"""JSON template service for managing issue templates.

Provides CRUD operations for JSON issue templates.

Source: MIGRATE-053 - JSON Template Management
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dot_issues.domain.entities import Issue, IssuePriority, IssueType
from dot_issues.domain.json_template import JsonTemplate

logger = logging.getLogger(__name__)


# Type for template defaults values
TemplateDefaultsValue = str | int | list[str]


@dataclass(frozen=True)
class TemplateInfo:
    """Lightweight information about a template.

    Attributes:
        name: Template name
        description: Template description
        priority: Default priority
        issue_type: Default issue type
        labels: Default labels
        source_path: Path to template file
    """

    name: str
    description: str
    priority: IssuePriority
    issue_type: IssueType
    labels: list[str]
    source_path: Path


class JsonTemplateService:
    """Service for managing JSON issue templates.

    Templates are stored as JSON files in .work/db-issues/templates/
    """

    DEFAULT_TEMPLATES_DIR = Path(".work/db-issues/templates")

    def __init__(self, templates_dir: str | Path | None = None) -> None:
        """Initialize template service.

        Args:
            templates_dir: Path to templates directory. Defaults to .work/db-issues/templates
        """
        self.templates_dir = Path(templates_dir or self.DEFAULT_TEMPLATES_DIR)
        self._cache: dict[str, JsonTemplate] = {}

    def list_templates(self) -> list[TemplateInfo]:
        """List all available templates.

        Returns:
            List of TemplateInfo objects for discovered templates
        """
        templates: list[TemplateInfo] = []

        if not self.templates_dir.exists():
            logger.debug(f"Templates directory does not exist: {self.templates_dir}")
            return templates

        for path in self.templates_dir.glob("*.json"):
            try:
                template = self._load_template_cached(path)
                templates.append(
                    TemplateInfo(
                        name=template.name,
                        description=template.description,
                        priority=template.priority,
                        issue_type=template.issue_type,
                        labels=template.labels,
                        source_path=path,
                    )
                )
            except Exception as e:
                logger.warning(f"Skipping invalid template: {path}: {e}")

        return templates

    def get_template(self, name: str) -> JsonTemplate | None:
        """Get a template by name.

        Args:
            name: Template name (filename without .json extension)

        Returns:
            JsonTemplate if found, None otherwise
        """
        template_path = self.templates_dir / f"{name}.json"

        if not template_path.exists():
            logger.debug(f"Template not found: {template_path}")
            return None

        try:
            return self._load_template_cached(template_path)
        except Exception as e:
            logger.error(f"Failed to load template {name}: {e}")
            return None

    def save_template(
        self,
        name: str,
        description: str,
        defaults: dict[str, Any],
        description_template: str | None = None,
        overwrite: bool = False,
    ) -> JsonTemplate:
        """Save a template.

        Args:
            name: Template name
            description: Template description
            defaults: Default values for issues
            description_template: Optional template for issue description body
            overwrite: Whether to overwrite existing template

        Returns:
            Saved JsonTemplate

        Raises:
            ValueError: If template exists and overwrite=False
        """
        template_path = self.templates_dir / f"{name}.json"

        if template_path.exists() and not overwrite:
            raise ValueError(f"Template already exists: {name}. Use --overwrite to replace.")

        template = JsonTemplate(
            name=name,
            description=description,
            defaults=defaults,
            description_template=description_template,
            source_path=template_path,
        )

        # Save to file
        saved_path = template.to_file(template_path)
        logger.info(f"Saved template: {name} to {saved_path}")

        # Update cache
        cache_key = str(saved_path.absolute())
        self._cache[cache_key] = template

        return template

    def save_issue_as_template(
        self,
        issue: Issue,
        name: str,
        description: str | None = None,
        overwrite: bool = False,
    ) -> JsonTemplate:
        """Save an issue as a template.

        Args:
            issue: Issue to save as template
            name: Template name
            description: Optional template description (defaults to issue title)
            overwrite: Whether to overwrite existing template

        Returns:
            Saved JsonTemplate
        """
        defaults: dict[str, TemplateDefaultsValue] = {
            "type": issue.type.value,
            "priority": issue.priority.value,
        }

        if issue.labels:
            defaults["labels"] = issue.labels

        template = self.save_template(
            name=name,
            description=description or f"Template from issue: {issue.title}",
            defaults=defaults,
            description_template=issue.description,
            overwrite=overwrite,
        )

        logger.info(f"Saved issue {issue.id} as template: {name}")
        return template

    def delete_template(self, name: str) -> bool:
        """Delete a template.

        Args:
            name: Template name

        Returns:
            True if deleted, False if not found
        """
        template_path = self.templates_dir / f"{name}.json"

        if not template_path.exists():
            return False

        template_path.unlink()
        logger.info(f"Deleted template: {name}")

        # Remove from cache
        cache_key = str(template_path.absolute())
        self._cache.pop(cache_key, None)

        return True

    def template_exists(self, name: str) -> bool:
        """Check if a template exists.

        Args:
            name: Template name

        Returns:
            True if template exists, False otherwise
        """
        return (self.templates_dir / f"{name}.json").exists()

    def reload_cache(self) -> None:
        """Clear the template cache.

        Forces templates to be reloaded from disk on next access.
        """
        self._cache.clear()
        logger.debug("Template cache cleared")

    def create_issue_from_template(
        self,
        template_name: str,
        title: str,
        **overrides: Any,
    ) -> dict[str, Any]:
        """Create issue data from template.

        Args:
            template_name: Name of template to use
            title: Issue title
            **overrides: Override values for defaults

        Returns:
            Dictionary with issue data for creation

        Raises:
            ValueError: If template not found
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")

        # Start with template defaults
        issue_data: dict[str, Any] = {
            "title": title,
            "type": template.issue_type,
            "priority": template.priority,
        }

        # Add labels if present
        if template.labels:
            issue_data["labels"] = template.labels

        # Add description template if present
        if template.description_template:
            issue_data["description"] = template.description_template

        # Apply overrides
        issue_data.update(overrides)

        return issue_data

    def _load_template_cached(self, path: Path) -> JsonTemplate:
        """Load template with caching.

        Args:
            path: Path to template file

        Returns:
            Parsed JsonTemplate

        Raises:
            ValueError: If parsing fails
        """
        cache_key = str(path.absolute())

        if cache_key not in self._cache:
            logger.debug(f"Loading template: {path}")
            self._cache[cache_key] = JsonTemplate.from_file(path)
            logger.debug(f"Cached template: {cache_key}")

        return self._cache[cache_key]

    def ensure_templates_directory(self) -> None:
        """Create the templates directory if it doesn't exist."""
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Create README if not exists
        readme_path = self.templates_dir / "README.md"
        if not readme_path.exists():
            readme_content = """# JSON Issue Templates

This directory contains JSON templates for creating issues with predefined configurations.

## Template Format

```json
{
  "name": "bug-report",
  "description": "Standard bug report template",
  "defaults": {
    "type": "bug",
    "priority": "high",
    "labels": ["bug", "needs-investigation"]
  },
  "description_template": "## Steps to Reproduce\\n\\n1. \\n\\n## Expected Behavior\\n\\n\\n## Actual Behavior\\n\\n"
}
```

## Usage

Create new issues from templates:

```bash
# Save current issue as template
dot-work db-issues template save <issue_id> --name bug-report

# List all templates
dot-work db-issues template list

# Show template details
dot-work db-issues template show bug-report

# Create issue from template
dot-work db-issues create "Fix parser" --template bug-report

# Delete template
dot-work db-issues template delete bug-report
```
"""
            readme_path.write_text(readme_content)
            logger.info(f"Created templates directory: {self.templates_dir}")


__all__ = ["JsonTemplateService", "TemplateInfo"]
