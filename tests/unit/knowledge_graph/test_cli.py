"""Unit tests for project and topic CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from dot_work.knowledge_graph.cli import app
from dot_work.knowledge_graph.db import Database


runner = CliRunner()


class TestProjectCreate:
    """Tests for 'kg project create' command."""

    def test_project_create_success(self, tmp_path: Path) -> None:
        """Should create a new project."""
        db_path = tmp_path / "test.sqlite"
        result = runner.invoke(app, ["project", "create", "myproj", "--db", str(db_path)])

        assert result.exit_code == 0
        assert "Created project: myproj" in result.stdout

        # Verify in database
        db = Database(db_path)
        proj = db.get_collection_by_name("myproj")
        assert proj is not None
        assert proj.kind == "project"
        db.close()

    def test_project_create_duplicate_error(self, tmp_path: Path) -> None:
        """Should error on duplicate project name."""
        db_path = tmp_path / "test.sqlite"
        runner.invoke(app, ["project", "create", "myproj", "--db", str(db_path)])
        result = runner.invoke(app, ["project", "create", "myproj", "--db", str(db_path)])

        assert result.exit_code == 1
        assert "already exists" in result.stdout


class TestProjectLs:
    """Tests for 'kg project ls' command."""

    def test_project_ls_empty(self, tmp_path: Path) -> None:
        """Should show no projects message."""
        db_path = tmp_path / "test.sqlite"
        Database(db_path).close()  # Create empty db
        result = runner.invoke(app, ["project", "ls", "--db", str(db_path)])

        assert result.exit_code == 0
        assert "No projects found" in result.stdout

    def test_project_ls_with_projects(self, tmp_path: Path) -> None:
        """Should list existing projects."""
        db_path = tmp_path / "test.sqlite"
        runner.invoke(app, ["project", "create", "project-a", "--db", str(db_path)])
        runner.invoke(app, ["project", "create", "project-b", "--db", str(db_path)])

        result = runner.invoke(app, ["project", "ls", "--db", str(db_path)])

        assert result.exit_code == 0
        assert "project-a" in result.stdout
        assert "project-b" in result.stdout


class TestProjectAdd:
    """Tests for 'kg project add' command."""

    def test_project_add_document(self, tmp_path: Path) -> None:
        """Should add a document to a project."""
        db_path = tmp_path / "test.sqlite"
        db = Database(db_path)
        db.insert_document("doc-001", "/path/to/doc.md", b"# Test")
        db.close()

        runner.invoke(app, ["project", "create", "myproj", "--db", str(db_path)])
        result = runner.invoke(app, ["project", "add", "myproj", "doc-001", "--db", str(db_path)])

        assert result.exit_code == 0
        assert "Added document: doc-001" in result.stdout

    def test_project_add_not_found(self, tmp_path: Path) -> None:
        """Should report when project not found."""
        db_path = tmp_path / "test.sqlite"
        Database(db_path).close()

        result = runner.invoke(
            app, ["project", "add", "nonexistent", "doc-001", "--db", str(db_path)]
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout


class TestProjectRm:
    """Tests for 'kg project rm' command."""

    def test_project_rm_with_force(self, tmp_path: Path) -> None:
        """Should delete project with --force."""
        db_path = tmp_path / "test.sqlite"
        runner.invoke(app, ["project", "create", "myproj", "--db", str(db_path)])

        result = runner.invoke(app, ["project", "rm", "myproj", "--force", "--db", str(db_path)])

        assert result.exit_code == 0
        assert "Deleted project: myproj" in result.stdout

        db = Database(db_path)
        assert db.get_collection_by_name("myproj") is None
        db.close()

    def test_project_rm_not_found(self, tmp_path: Path) -> None:
        """Should error when project not found."""
        db_path = tmp_path / "test.sqlite"
        Database(db_path).close()

        result = runner.invoke(
            app, ["project", "rm", "nonexistent", "--force", "--db", str(db_path)]
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout


class TestProjectShow:
    """Tests for 'kg project show' command."""

    def test_project_show_empty(self, tmp_path: Path) -> None:
        """Should show project with no members."""
        db_path = tmp_path / "test.sqlite"
        runner.invoke(app, ["project", "create", "myproj", "--db", str(db_path)])

        result = runner.invoke(app, ["project", "show", "myproj", "--db", str(db_path)])

        assert result.exit_code == 0
        assert "myproj" in result.stdout
        assert "No members" in result.stdout

    def test_project_show_with_members(self, tmp_path: Path) -> None:
        """Should show project members."""
        db_path = tmp_path / "test.sqlite"
        db = Database(db_path)
        db.insert_document("doc-001", "/path/to/doc.md", b"# Test")
        db.close()

        runner.invoke(app, ["project", "create", "myproj", "--db", str(db_path)])
        runner.invoke(app, ["project", "add", "myproj", "doc-001", "--db", str(db_path)])

        result = runner.invoke(app, ["project", "show", "myproj", "--db", str(db_path)])

        assert result.exit_code == 0
        assert "doc-001" in result.stdout


class TestTopicCreate:
    """Tests for 'kg topic create' command."""

    def test_topic_create_success(self, tmp_path: Path) -> None:
        """Should create a new topic."""
        db_path = tmp_path / "test.sqlite"
        result = runner.invoke(app, ["topic", "create", "python", "--db", str(db_path)])

        assert result.exit_code == 0
        assert "Created topic: python" in result.stdout

        db = Database(db_path)
        topic = db.get_topic_by_name("python")
        assert topic is not None
        db.close()

    def test_topic_create_duplicate_error(self, tmp_path: Path) -> None:
        """Should error on duplicate topic name."""
        db_path = tmp_path / "test.sqlite"
        runner.invoke(app, ["topic", "create", "python", "--db", str(db_path)])
        result = runner.invoke(app, ["topic", "create", "python", "--db", str(db_path)])

        assert result.exit_code == 1
        assert "already exists" in result.stdout


class TestTopicLs:
    """Tests for 'kg topic ls' command."""

    def test_topic_ls_empty(self, tmp_path: Path) -> None:
        """Should show no topics message."""
        db_path = tmp_path / "test.sqlite"
        Database(db_path).close()

        result = runner.invoke(app, ["topic", "ls", "--db", str(db_path)])

        assert result.exit_code == 0
        assert "No topics found" in result.stdout

    def test_topic_ls_with_topics(self, tmp_path: Path) -> None:
        """Should list existing topics."""
        db_path = tmp_path / "test.sqlite"
        runner.invoke(app, ["topic", "create", "python", "--db", str(db_path)])
        runner.invoke(app, ["topic", "create", "testing", "--db", str(db_path)])

        result = runner.invoke(app, ["topic", "ls", "--db", str(db_path)])

        assert result.exit_code == 0
        assert "python" in result.stdout
        assert "testing" in result.stdout


class TestTopicTag:
    """Tests for 'kg topic tag' command."""

    def test_topic_tag_document(self, tmp_path: Path) -> None:
        """Should tag a document with a topic."""
        db_path = tmp_path / "test.sqlite"
        db = Database(db_path)
        db.insert_document("doc-001", "/path/to/doc.md", b"# Test")
        db.close()

        runner.invoke(app, ["topic", "create", "python", "--db", str(db_path)])
        result = runner.invoke(
            app, ["topic", "tag", "python", "--id", "doc-001", "--db", str(db_path)]
        )

        assert result.exit_code == 0
        assert "Tagged document 'doc-001' with 'python'" in result.stdout

    def test_topic_tag_with_weight(self, tmp_path: Path) -> None:
        """Should tag with custom weight."""
        db_path = tmp_path / "test.sqlite"
        db = Database(db_path)
        db.insert_document("doc-001", "/path/to/doc.md", b"# Test")
        db.close()

        runner.invoke(app, ["topic", "create", "python", "--db", str(db_path)])
        result = runner.invoke(
            app,
            [
                "topic",
                "tag",
                "python",
                "--id",
                "doc-001",
                "--weight",
                "0.8",
                "--db",
                str(db_path),
            ],
        )

        assert result.exit_code == 0

    def test_topic_tag_not_found(self, tmp_path: Path) -> None:
        """Should error when topic not found."""
        db_path = tmp_path / "test.sqlite"
        Database(db_path).close()

        result = runner.invoke(
            app, ["topic", "tag", "nonexistent", "--id", "doc-001", "--db", str(db_path)]
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout


class TestTopicUntag:
    """Tests for 'kg topic untag' command."""

    def test_topic_untag_success(self, tmp_path: Path) -> None:
        """Should remove topic from target."""
        db_path = tmp_path / "test.sqlite"
        db = Database(db_path)
        db.insert_document("doc-001", "/path/to/doc.md", b"# Test")
        db.close()

        runner.invoke(app, ["topic", "create", "python", "--db", str(db_path)])
        runner.invoke(app, ["topic", "tag", "python", "--id", "doc-001", "--db", str(db_path)])

        result = runner.invoke(
            app, ["topic", "untag", "python", "--id", "doc-001", "--db", str(db_path)]
        )

        assert result.exit_code == 0
        assert "Removed 'python' from 'doc-001'" in result.stdout

    def test_topic_untag_not_tagged(self, tmp_path: Path) -> None:
        """Should report when tag not found."""
        db_path = tmp_path / "test.sqlite"
        db = Database(db_path)
        db.insert_document("doc-001", "/path/to/doc.md", b"# Test")
        db.close()

        runner.invoke(app, ["topic", "create", "python", "--db", str(db_path)])
        result = runner.invoke(
            app, ["topic", "untag", "python", "--id", "doc-001", "--db", str(db_path)]
        )

        assert result.exit_code == 0
        assert "Tag not found" in result.stdout


class TestTopicRm:
    """Tests for 'kg topic rm' command."""

    def test_topic_rm_with_force(self, tmp_path: Path) -> None:
        """Should delete topic with --force."""
        db_path = tmp_path / "test.sqlite"
        runner.invoke(app, ["topic", "create", "python", "--db", str(db_path)])

        result = runner.invoke(app, ["topic", "rm", "python", "--force", "--db", str(db_path)])

        assert result.exit_code == 0
        assert "Deleted topic: python" in result.stdout

        db = Database(db_path)
        assert db.get_topic_by_name("python") is None
        db.close()

    def test_topic_rm_not_found(self, tmp_path: Path) -> None:
        """Should error when topic not found."""
        db_path = tmp_path / "test.sqlite"
        Database(db_path).close()

        result = runner.invoke(app, ["topic", "rm", "nonexistent", "--force", "--db", str(db_path)])

        assert result.exit_code == 1
        assert "not found" in result.stdout


class TestTopicShow:
    """Tests for 'kg topic show' command."""

    def test_topic_show_empty(self, tmp_path: Path) -> None:
        """Should show topic with no links."""
        db_path = tmp_path / "test.sqlite"
        runner.invoke(app, ["topic", "create", "python", "--db", str(db_path)])

        result = runner.invoke(app, ["topic", "show", "python", "--db", str(db_path)])

        assert result.exit_code == 0
        assert "python" in result.stdout
        assert "No linked targets" in result.stdout

    def test_topic_show_with_links(self, tmp_path: Path) -> None:
        """Should show topic links."""
        db_path = tmp_path / "test.sqlite"
        db = Database(db_path)
        db.insert_document("doc-001", "/path/to/doc.md", b"# Test")
        db.close()

        runner.invoke(app, ["topic", "create", "python", "--db", str(db_path)])
        runner.invoke(app, ["topic", "tag", "python", "--id", "doc-001", "--db", str(db_path)])

        result = runner.invoke(app, ["topic", "show", "python", "--db", str(db_path)])

        assert result.exit_code == 0
        assert "doc-001" in result.stdout


class TestCLIHelp:
    """Tests for CLI help output."""

    def test_project_help(self) -> None:
        """Should show project subcommands in help."""
        result = runner.invoke(app, ["project", "--help"])

        assert result.exit_code == 0
        assert "create" in result.stdout
        assert "ls" in result.stdout
        assert "add" in result.stdout
        assert "rm" in result.stdout
        assert "show" in result.stdout

    def test_topic_help(self) -> None:
        """Should show topic subcommands in help."""
        result = runner.invoke(app, ["topic", "--help"])

        assert result.exit_code == 0
        assert "create" in result.stdout
        assert "ls" in result.stdout
        assert "tag" in result.stdout
        assert "untag" in result.stdout
        assert "rm" in result.stdout
        assert "show" in result.stdout
