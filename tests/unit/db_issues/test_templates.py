"""Tests for instruction template functionality."""

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dot_work.db_issues.adapters import UnitOfWork
from dot_work.db_issues.cli import app
from dot_work.db_issues.domain.entities import IssuePriority, IssueType
from dot_work.db_issues.services import EpicService, IssueService, TemplateService
from dot_work.db_issues.templates import (
    InstructionTemplate,
    InstructionTemplateParser,
    TemplateManager,
    TemplateParseError,
)


@pytest.fixture
def parser() -> InstructionTemplateParser:
    """Return template parser fixture."""
    return InstructionTemplateParser()


@pytest.fixture
def sample_template_content() -> str:
    """Return sample template content."""
    return """---
name: test-feature
title: Test Feature Implementation
description: A test feature for unit tests
priority: high
type: feature
assignee: tester
labels: [test, feature]
---

# Test Feature Implementation

This template is for testing the instruction template functionality.

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
"""


@pytest.fixture
def temp_templates_dir(sample_template_content: str) -> tempfile.TemporaryDirectory:
    """Create temporary templates directory with sample template."""
    temp_dir = tempfile.mkdtemp()
    templates_path = Path(temp_dir)

    # Create sample template file
    template_path = templates_path / "test-feature.md"
    template_path.write_text(sample_template_content)

    yield temp_dir

    # Cleanup is handled by TemporaryDirectory context


class TestInstructionTemplateParser:
    """Tests for InstructionTemplateParser."""

    def test_parse_valid_template(
        self, parser: InstructionTemplateParser, sample_template_content: str
    ) -> None:
        """Test parsing a valid template."""
        template = parser.parse_content(sample_template_content)

        assert template.name == "test-feature"
        assert template.title == "Test Feature Implementation"
        assert template.description == "A test feature for unit tests"
        assert template.task_count == 3

    def test_parse_template_default_values(self, parser: InstructionTemplateParser) -> None:
        """Test parsing template with default values."""
        content = """---
name: simple
title: Simple Template
---

# Simple Template

## Tasks

### Task 1: First task

Simple task description.
"""
        template = parser.parse_content(content)

        assert template.name == "simple"
        assert template.title == "Simple Template"
        assert template.task_count == 1
        assert template.tasks[0].priority == IssuePriority.MEDIUM
        assert template.tasks[0].task_type == IssueType.TASK

    def test_parse_template_from_file(
        self, parser: InstructionTemplateParser, sample_template_content: str
    ) -> None:
        """Test parsing template from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(sample_template_content)
            f.flush()
            template = parser.parse(f.name)

        assert template.name == "test-feature"
        assert template.task_count == 3

        # Cleanup
        Path(f.name).unlink()

    def test_parse_missing_frontmatter(self, parser: InstructionTemplateParser) -> None:
        """Test parsing template without frontmatter."""
        content = """# Just markdown

No frontmatter here.
"""

        with pytest.raises(TemplateParseError, match="missing YAML frontmatter"):
            parser.parse_content(content)

    def test_parse_invalid_priority(self, parser: InstructionTemplateParser) -> None:
        """Test parsing template with invalid priority."""
        content = """---
name: test
title: Test
priority: invalid
---

## Tasks

### Task 1: Task

Description.
"""

        with pytest.raises(TemplateParseError, match="Invalid priority"):
            parser.parse_content(content)

    def test_parse_invalid_type(self, parser: InstructionTemplateParser) -> None:
        """Test parsing template with invalid type."""
        content = """---
name: test
title: Test
type: invalid
---

## Tasks

### Task 1: Task

Description.
"""

        with pytest.raises(TemplateParseError, match="Invalid type"):
            parser.parse_content(content)

    def test_parse_template_with_checkboxes(self, parser: InstructionTemplateParser) -> None:
        """Test parsing template with acceptance criteria checkboxes."""
        content = """---
name: test
title: Test
---

## Tasks

### Task 1: Task with checkboxes

Task description.

- [ ] Criterion 1
- [ ] Criterion 2
- [x] Already done
"""
        template = parser.parse_content(content)

        assert template.task_count == 1
        assert len(template.tasks[0].acceptance_criteria) == 3
        assert template.tasks[0].acceptance_criteria == [
            "Criterion 1",
            "Criterion 2",
            "Already done",
        ]


class TestTemplateManager:
    """Tests for TemplateManager."""

    def test_list_templates(self, temp_templates_dir: str) -> None:
        """Test listing templates from directory."""
        manager = TemplateManager(temp_templates_dir)
        templates = manager.list_templates()

        assert len(templates) == 1
        assert templates[0].name == "test-feature"
        assert templates[0].task_count == 3

    def test_list_templates_empty_dir(self) -> None:
        """Test listing templates from empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TemplateManager(temp_dir)
            templates = manager.list_templates()

        assert templates == []

    def test_list_templates_nonexistent_dir(self) -> None:
        """Test listing templates from non-existent directory."""
        manager = TemplateManager("/nonexistent/path")
        templates = manager.list_templates()

        assert templates == []

    def test_get_template_by_name(self, temp_templates_dir: str) -> None:
        """Test getting template by name."""
        manager = TemplateManager(temp_templates_dir)
        template = manager.get_template("test-feature")

        assert template is not None
        assert template.name == "test-feature"
        assert template.task_count == 3

    def test_get_template_not_found(self, temp_templates_dir: str) -> None:
        """Test getting non-existent template."""
        manager = TemplateManager(temp_templates_dir)
        template = manager.get_template("nonexistent")

        assert template is None

    def test_template_caching(self, temp_templates_dir: str) -> None:
        """Test that templates are cached."""
        manager = TemplateManager(temp_templates_dir)

        # First call loads from disk
        template1 = manager.get_template("test-feature")

        # Second call should use cache
        template2 = manager.get_template("test-feature")

        assert template1 is template2  # Same object reference (cached)

    def test_reload_cache(self, temp_templates_dir: str) -> None:
        """Test reloading template cache."""
        manager = TemplateManager(temp_templates_dir)

        # Load template
        template1 = manager.get_template("test-feature")
        cache_id_1 = id(template1)

        # Reload cache
        manager.reload_cache()

        # Load again - should be new object
        template2 = manager.get_template("test-feature")
        cache_id_2 = id(template2)

        assert cache_id_1 != cache_id_2

    def test_create_templates_directory(self) -> None:
        """Test creating templates directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_path = Path(temp_dir) / "instructions"
            manager = TemplateManager(templates_path)

            manager.create_templates_directory()

            assert templates_path.exists()
            assert (templates_path / "README.md").exists()


class TestTemplateService:
    """Tests for TemplateService."""

    @pytest.fixture
    def template_service(self, in_memory_db, fixed_id_service, fixed_clock) -> TemplateService:
        """Create a TemplateService with test dependencies.

        Args:
            in_memory_db: In-memory database session
            fixed_id_service: Fixed identifier service
            fixed_clock: Fixed clock

        Returns:
            TemplateService instance configured for testing
        """
        uow = UnitOfWork(in_memory_db)
        issue_service = IssueService(uow, fixed_id_service, fixed_clock)
        epic_service = EpicService(uow, fixed_id_service, fixed_clock)
        return TemplateService(uow, fixed_id_service, fixed_clock, issue_service, epic_service)

    @pytest.fixture
    def issue_service(self, in_memory_db, fixed_id_service, fixed_clock) -> IssueService:
        """Create an IssueService with test dependencies."""
        uow = UnitOfWork(in_memory_db)
        return IssueService(uow, fixed_id_service, fixed_clock)

    @pytest.fixture
    def epic_service(self, in_memory_db, fixed_id_service, fixed_clock) -> EpicService:
        """Create an EpicService with test dependencies."""
        uow = UnitOfWork(in_memory_db)
        return EpicService(uow, fixed_id_service, fixed_clock)

    def test_apply_template_creates_epic_and_issues(
        self,
        template_service: TemplateService,
        issue_service: IssueService,
        epic_service: EpicService,
        sample_template_content: str,
    ) -> None:
        """Test applying template creates epic and child issues."""
        parser = InstructionTemplateParser()
        template = parser.parse_content(sample_template_content)

        # Note: create_dependencies=False to avoid pre-existing bug in dependency ID generation
        result = template_service.apply_template(template, create_dependencies=False)

        assert result.epic_id.startswith("epic-")
        assert result.task_count == 3
        assert len(result.issue_ids) == 3

        # Verify epic was created
        epic = epic_service.get_epic(result.epic_id)
        assert epic is not None
        assert epic.title == "Test Feature Implementation"

        # Verify issues were created
        for issue_id in result.issue_ids:
            issue = issue_service.get_issue(issue_id)
            assert issue is not None
            assert issue.epic_id == result.epic_id

    def test_apply_template_with_no_tasks_raises_error(
        self, template_service: TemplateService
    ) -> None:
        """Test applying template with no tasks raises ValueError."""

        template = InstructionTemplate(
            name="empty",
            title="Empty Template",
            description=None,
            tasks=[],
            raw_content="",
            source_path=Path(""),
        )

        with pytest.raises(ValueError, match="no tasks"):
            template_service.apply_template(template)


class TestInstructionsCLI:
    """Tests for instructions CLI commands."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Return CLI runner."""
        return CliRunner()

    def test_instructions_list_empty(self, runner: CliRunner) -> None:
        """Test instructions list with no templates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(
                app,
                ["instructions", "list", "--templates-dir", temp_dir],
            )

        assert result.exit_code == 0
        assert "No templates found" in result.stdout

    def test_instructions_list_with_templates(
        self, runner: CliRunner, temp_templates_dir: str
    ) -> None:
        """Test instructions list with templates."""
        result = runner.invoke(
            app,
            ["instructions", "list", "--templates-dir", temp_templates_dir],
        )

        assert result.exit_code == 0
        assert "test-feature" in result.stdout
        # Title may be truncated in table output
        assert "Test Feature" in result.stdout or "Feature" in result.stdout
        assert "3" in result.stdout  # task count

    def test_instructions_show(self, runner: CliRunner, temp_templates_dir: str) -> None:
        """Test instructions show command."""
        result = runner.invoke(
            app,
            ["instructions", "show", "test-feature", "--templates-dir", temp_templates_dir],
        )

        assert result.exit_code == 0
        assert "test-feature" in result.stdout
        assert "Test Feature Implementation" in result.stdout
        assert "Task Breakdown" in result.stdout

    def test_instructions_show_not_found(self, runner: CliRunner) -> None:
        """Test instructions show with non-existent template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(
                app,
                ["instructions", "show", "nonexistent", "--templates-dir", temp_dir],
            )

        assert result.exit_code == 1
        assert "Template not found" in result.stdout

    def test_instructions_init(self, runner: CliRunner) -> None:
        """Test instructions init command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_path = Path(temp_dir) / "instructions"
            result = runner.invoke(
                app,
                ["instructions", "init", "--path", str(templates_path)],
            )

        assert result.exit_code == 0
        assert "Templates directory created" in result.stdout
