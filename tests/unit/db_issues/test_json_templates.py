"""Tests for JSON template functionality."""

import json
import shutil
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dot_work.db_issues.domain.entities import IssuePriority, IssueType
from dot_work.db_issues.domain.json_template import JsonTemplate
from dot_work.db_issues.services import JsonTemplateService, TemplateInfo
from dot_work.db_issues.cli import app


@pytest.fixture
def sample_template_content() -> str:
    """Return sample template content."""
    return json.dumps(
        {
            "name": "bug-report",
            "description": "Standard bug report template",
            "defaults": {
                "type": "bug",
                "priority": "high",
                "labels": ["bug", "needs-investigation"],
            },
            "description_template": (
                "## Steps to Reproduce\n\n1. \n\n## Expected Behavior\n\n\n## Actual Behavior\n\n"
            ),
        },
        indent=2,
    )


@pytest.fixture
def temp_templates_dir(sample_template_content: str) -> str:
    """Create temporary templates directory with sample template."""
    temp_dir = tempfile.mkdtemp()
    templates_path = Path(temp_dir)

    # Create sample template file
    template_path = templates_path / "bug-report.json"
    template_path.write_text(sample_template_content)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestJsonTemplate:
    """Tests for JsonTemplate."""

    def test_create_template(self) -> None:
        """Test creating a template."""
        template = JsonTemplate(
            name="test",
            description="Test template",
            defaults={"type": "feature", "priority": "low"},
        )

        assert template.name == "test"
        assert template.description == "Test template"
        assert template.issue_type == IssueType.FEATURE
        assert template.priority == IssuePriority.LOW
        assert template.labels == []

    def test_template_with_labels(self) -> None:
        """Test template with labels."""
        template = JsonTemplate(
            name="test",
            description="Test template",
            defaults={"labels": ["bug", "urgent"]},
        )

        assert template.labels == ["bug", "urgent"]

    def test_template_with_description_template(self) -> None:
        """Test template with description template."""
        description_template = "## Overview\n\nTemplate text here."
        template = JsonTemplate(
            name="test",
            description="Test template",
            defaults={},
            description_template=description_template,
        )

        assert template.description_template == description_template

    def test_to_dict(self) -> None:
        """Test converting template to dictionary."""
        template = JsonTemplate(
            name="test",
            description="Test template",
            defaults={"type": "feature", "priority": "high"},
        )

        data = template.to_dict()
        assert data["name"] == "test"
        assert data["description"] == "Test template"
        assert data["defaults"]["type"] == "feature"
        assert data["defaults"]["priority"] == "high"

    def test_from_dict(self) -> None:
        """Test creating template from dictionary."""
        data = {
            "name": "test",
            "description": "Test template",
            "defaults": {"type": "bug"},
        }

        template = JsonTemplate.from_dict(data, Path("test.json"))

        assert template.name == "test"
        assert template.description == "Test template"
        assert template.defaults["type"] == "bug"

    def test_from_dict_missing_name_raises_error(self) -> None:
        """Test that missing name raises ValueError."""
        data = {"description": "No name"}

        with pytest.raises(ValueError, match="name"):
            JsonTemplate.from_dict(data, Path("test.json"))

    def test_from_file_json(self, sample_template_content: str) -> None:
        """Test loading template from JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(sample_template_content)
            f.flush()

            template = JsonTemplate.from_file(f.name)

        assert template.name == "bug-report"
        assert template.description == "Standard bug report template"
        assert template.issue_type == IssueType.BUG
        assert template.priority == IssuePriority.HIGH
        assert "bug" in template.labels

        # Cleanup
        Path(f.name).unlink()

    def test_to_file(self) -> None:
        """Test saving template to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template = JsonTemplate(
                name="test",
                description="Test template",
                defaults={"type": "feature"},
            )

            save_path = Path(temp_dir) / "test.json"
            template.to_file(save_path)

            assert save_path.exists()

            # Verify content
            data = json.loads(save_path.read_text())
            assert data["name"] == "test"
            assert data["description"] == "Test template"


class TestJsonTemplateService:
    """Tests for JsonTemplateService."""

    def test_list_templates(self, temp_templates_dir: str) -> None:
        """Test listing templates from directory."""
        service = JsonTemplateService(temp_templates_dir)
        templates = service.list_templates()

        assert len(templates) == 1
        assert templates[0].name == "bug-report"
        assert templates[0].issue_type == IssueType.BUG
        assert templates[0].priority == IssuePriority.HIGH
        assert "bug" in templates[0].labels

    def test_list_templates_empty_dir(self) -> None:
        """Test listing templates from empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = JsonTemplateService(temp_dir)
            templates = service.list_templates()

        assert templates == []

    def test_list_templates_nonexistent_dir(self) -> None:
        """Test listing templates from non-existent directory."""
        service = JsonTemplateService("/nonexistent/path")
        templates = service.list_templates()

        assert templates == []

    def test_get_template_by_name(self, temp_templates_dir: str) -> None:
        """Test getting template by name."""
        service = JsonTemplateService(temp_templates_dir)
        template = service.get_template("bug-report")

        assert template is not None
        assert template.name == "bug-report"
        assert template.issue_type == IssueType.BUG

    def test_get_template_not_found(self, temp_templates_dir: str) -> None:
        """Test getting non-existent template."""
        service = JsonTemplateService(temp_templates_dir)
        template = service.get_template("nonexistent")

        assert template is None

    def test_save_template(self) -> None:
        """Test saving a template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = JsonTemplateService(temp_dir)

            template = service.save_template(
                name="feature",
                description="Feature template",
                defaults={"type": "feature", "priority": "medium"},
            )

            assert template.name == "feature"
            assert service.template_exists("feature")

            # Verify file was created
            template_path = Path(temp_dir) / "feature.json"
            assert template_path.exists()

    def test_save_template_overwrite_flag(self) -> None:
        """Test that saving existing template requires overwrite flag."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = JsonTemplateService(temp_dir)

            # Save first template
            service.save_template(
                name="test",
                description="First",
                defaults={},
            )

            # Try to save without overwrite flag
            with pytest.raises(ValueError, match="already exists"):
                service.save_template(
                    name="test",
                    description="Second",
                    defaults={},
                )

            # Save with overwrite flag
            template = service.save_template(
                name="test",
                description="Second",
                defaults={},
                overwrite=True,
            )

            assert template.description == "Second"

    def test_delete_template(self) -> None:
        """Test deleting a template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = JsonTemplateService(temp_dir)

            # Create a template
            service.save_template(
                name="test",
                description="Test",
                defaults={},
            )

            assert service.template_exists("test")

            # Delete it
            result = service.delete_template("test")

            assert result is True
            assert not service.template_exists("test")

    def test_delete_template_not_found(self) -> None:
        """Test deleting non-existent template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = JsonTemplateService(temp_dir)
            result = service.delete_template("nonexistent")

            assert result is False

    def test_template_exists(self) -> None:
        """Test checking if template exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = JsonTemplateService(temp_dir)

            assert not service.template_exists("test")

            service.save_template(
                name="test",
                description="Test",
                defaults={},
            )

            assert service.template_exists("test")

    def test_template_caching(self, temp_templates_dir: str) -> None:
        """Test that templates are cached."""
        service = JsonTemplateService(temp_templates_dir)

        # First call loads from disk
        template1 = service.get_template("bug-report")

        # Second call should use cache
        template2 = service.get_template("bug-report")

        assert template1 is template2  # Same object reference (cached)

    def test_reload_cache(self, temp_templates_dir: str) -> None:
        """Test reloading template cache."""
        service = JsonTemplateService(temp_templates_dir)

        # Load template
        template1 = service.get_template("bug-report")
        cache_id_1 = id(template1)

        # Reload cache
        service.reload_cache()

        # Load again - should be new object
        template2 = service.get_template("bug-report")
        cache_id_2 = id(template2)

        # The templates are different objects but have same data
        assert cache_id_1 != cache_id_2
        assert template1.name == template2.name

    def test_create_issue_from_template(self, temp_templates_dir: str) -> None:
        """Test creating issue data from template."""
        service = JsonTemplateService(temp_templates_dir)

        issue_data = service.create_issue_from_template(
            template_name="bug-report",
            title="Fix parser bug",
        )

        assert issue_data["title"] == "Fix parser bug"
        assert issue_data["type"] == IssueType.BUG
        assert issue_data["priority"] == IssuePriority.HIGH
        assert "bug" in issue_data["labels"]
        assert "steps to reproduce" in issue_data["description"].lower()

    def test_create_issue_from_template_with_overrides(self, temp_templates_dir: str) -> None:
        """Test creating issue from template with overrides."""
        service = JsonTemplateService(temp_templates_dir)

        issue_data = service.create_issue_from_template(
            template_name="bug-report",
            title="Fix parser bug",
            priority=IssuePriority.CRITICAL,
            labels=["urgent"],
        )

        assert issue_data["priority"] == IssuePriority.CRITICAL
        assert issue_data["labels"] == ["urgent"]  # Overridden

    def test_create_issue_from_template_not_found(self) -> None:
        """Test creating issue from non-existent template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = JsonTemplateService(temp_dir)

            with pytest.raises(ValueError, match="not found"):
                service.create_issue_from_template("nonexistent", "Test")

    def test_ensure_templates_directory(self) -> None:
        """Test creating templates directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_path = Path(temp_dir) / "templates"
            service = JsonTemplateService(templates_path)

            service.ensure_templates_directory()

            assert templates_path.exists()
            assert (templates_path / "README.md").exists()


class TestTemplateCLI:
    """Tests for template CLI commands."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Return CLI runner."""
        return CliRunner()

    def test_template_list_empty(self, runner: CliRunner) -> None:
        """Test template list with no templates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(
                app,
                ["template", "list", "--templates-dir", temp_dir],
            )

        assert result.exit_code == 0
        assert "No templates found" in result.stdout

    def test_template_list_with_templates(
        self, runner: CliRunner, temp_templates_dir: str
    ) -> None:
        """Test template list with templates."""
        result = runner.invoke(
            app,
            ["template", "list", "--templates-dir", temp_templates_dir],
        )

        assert result.exit_code == 0
        assert "bug-report" in result.stdout
        assert "Standard bug report" in result.stdout  # Truncated to 40 chars
        assert "bug" in result.stdout  # issue_type is lowercase
        assert "HIGH" in result.stdout  # priority.name is uppercase

    def test_template_show(self, runner: CliRunner, temp_templates_dir: str) -> None:
        """Test template show command."""
        result = runner.invoke(
            app,
            ["template", "show", "bug-report", "--templates-dir", temp_templates_dir],
        )

        assert result.exit_code == 0
        assert "bug-report" in result.stdout
        assert "Standard bug report template" in result.stdout
        assert "bug" in result.stdout  # issue_type.value is lowercase
        assert "HIGH" in result.stdout  # priority.name is uppercase
        assert "bug, needs-investigation" in result.stdout  # labels list

    def test_template_show_not_found(self, runner: CliRunner) -> None:
        """Test template show with non-existent template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(
                app,
                ["template", "show", "nonexistent", "--templates-dir", temp_dir],
            )

        assert result.exit_code == 1
        assert "Template not found" in result.stdout

    def test_template_delete(self, runner: CliRunner, temp_templates_dir: str) -> None:
        """Test template delete command."""
        # First verify template exists
        service = JsonTemplateService(temp_templates_dir)
        assert service.template_exists("bug-report")

        result = runner.invoke(
            app,
            ["template", "delete", "bug-report", "--templates-dir", temp_templates_dir, "--force"],
        )

        assert result.exit_code == 0
        assert "Template deleted" in result.stdout
        assert not service.template_exists("bug-report")

    def test_template_delete_not_found(self, runner: CliRunner) -> None:
        """Test template delete with non-existent template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(
                app,
                ["template", "delete", "nonexistent", "--templates-dir", temp_dir, "--force"],
            )

        assert result.exit_code == 1
        assert "Template not found" in result.stdout
