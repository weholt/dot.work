"""Template manager for storing and retrieving instruction templates.

Provides discovery, loading, and caching of instruction templates
from the .work/instructions directory.

Source: .work/prompts/do-work.prompt.md
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from dot_issues.templates.instruction_template import (
    InstructionTemplate,
    InstructionTemplateParser,
    TemplateParseError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TemplateInfo:
    """Lightweight information about a template.

    Attributes:
        name: Template name
        title: Template title
        task_count: Number of tasks in template
        source_path: Path to template file
    """

    name: str
    title: str
    task_count: int
    source_path: Path


class TemplateManager:
    """Manages instruction templates storage and retrieval.

    Templates are stored in .work/instructions/ directory by default.
    The manager handles discovery, loading, and caching of templates.
    """

    DEFAULT_TEMPLATES_DIR = Path(".work/instructions")

    def __init__(self, templates_dir: str | Path | None = None) -> None:
        """Initialize template manager.

        Args:
            templates_dir: Path to templates directory. Defaults to .work/instructions
        """
        self.templates_dir = Path(templates_dir or self.DEFAULT_TEMPLATES_DIR)
        self.parser = InstructionTemplateParser()
        self._cache: dict[str, InstructionTemplate] = {}

    def list_templates(self) -> list[TemplateInfo]:
        """List all available templates.

        Returns:
            List of TemplateInfo objects for discovered templates
        """
        templates: list[TemplateInfo] = []

        if not self.templates_dir.exists():
            logger.debug(f"Templates directory does not exist: {self.templates_dir}")
            return templates

        for path in self.templates_dir.glob("*.md"):
            try:
                template = self._load_template_cached(path)
                templates.append(
                    TemplateInfo(
                        name=template.name,
                        title=template.title,
                        task_count=template.task_count,
                        source_path=path,
                    )
                )
            except TemplateParseError as e:
                logger.warning(f"Skipping invalid template: {path}: {e}")

        return templates

    def get_template(self, name: str) -> InstructionTemplate | None:
        """Get a template by name.

        Args:
            name: Template name (filename without .md extension)

        Returns:
            InstructionTemplate if found, None otherwise
        """
        template_path = self.templates_dir / f"{name}.md"

        if not template_path.exists():
            logger.debug(f"Template not found: {template_path}")
            return None

        try:
            return self._load_template_cached(template_path)
        except TemplateParseError as e:
            logger.error(f"Failed to load template {name}: {e}")
            return None

    def get_template_by_path(self, path: str | Path) -> InstructionTemplate:
        """Get a template by file path.

        Args:
            path: Path to template file

        Returns:
            Parsed InstructionTemplate

        Raises:
            TemplateParseError: If parsing fails
            FileNotFoundError: If file doesn't exist
        """
        template_path = Path(path)
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        return self._load_template_cached(template_path)

    def reload_cache(self) -> None:
        """Clear the template cache.

        Forces templates to be reloaded from disk on next access.
        """
        self._cache.clear()
        logger.debug("Template cache cleared")

    def _load_template_cached(self, path: Path) -> InstructionTemplate:
        """Load template with caching.

        Args:
            path: Path to template file

        Returns:
            Parsed InstructionTemplate

        Raises:
            TemplateParseError: If parsing fails
        """
        cache_key = str(path.absolute())

        if cache_key not in self._cache:
            logger.debug(f"Loading template: {path}")
            self._cache[cache_key] = self.parser.parse(path)
            logger.debug(f"Cached template: {cache_key}")

        return self._cache[cache_key]

    def create_templates_directory(self) -> None:
        """Create the templates directory if it doesn't exist.

        Creates .work/instructions/ directory with a README example.
        """
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        readme_path = self.templates_dir / "README.md"
        if not readme_path.exists():
            readme_content = """# Instruction Templates

This directory contains instruction templates for creating structured issues.

## Template Format

Templates use markdown with YAML frontmatter:

```markdown
---
name: my-feature
title: Implement My Feature
description: A comprehensive feature implementation
priority: high
type: feature
assignee: developer
labels: [feature, backend]
---

# Implement My Feature

This template creates a parent epic with child tasks for implementing
a new feature.

## Tasks

### Task 1: Design the feature

Create technical design document with API specifications.

### Task 2: Implement core logic

- [ ] Implement data models
- [ ] Implement business logic
- [ ] Add error handling

### Task 3: Add tests

- [ ] Unit tests for core logic
- [ ] Integration tests for API endpoints
```

## Applying Templates

Use the CLI to apply a template:

```bash
uv run dot-work db-issues instructions apply my-feature
```

This will create:
1. A parent epic issue with the template title and description
2. Child issues for each task in the template
3. Dependencies between tasks in order
"""
            readme_path.write_text(readme_content)
            logger.info(f"Created templates directory: {self.templates_dir}")


__all__ = ["TemplateInfo", "TemplateManager"]
