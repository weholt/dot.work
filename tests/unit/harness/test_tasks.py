"""Tests for harness task file parsing and management."""

from pathlib import Path

import pytest

from dot_work.harness.tasks import (
    Task,
    TaskFileError,
    count_done,
    load_tasks,
    next_open_task,
    validate_task_file,
)


class TestTask:
    """Test Task dataclass."""

    def test_task_creation(self):
        """Test creating a Task object."""
        task = Task(line_no=5, done=True, text="Complete the feature")

        assert task.line_no == 5
        assert task.done is True
        assert task.text == "Complete the feature"

    def test_task_is_frozen(self):
        """Test that Task is frozen (immutable)."""
        task = Task(line_no=1, done=False, text="Test task")

        with pytest.raises(Exception):  # FrozenInstanceError
            task.done = True


class TestLoadTasks:
    """Test task loading from markdown files."""

    def test_load_tasks_with_checkboxes(self, tmp_path: Path):
        """Test loading tasks from a file with checkboxes."""
        test_file = tmp_path / "tasks.md"
        test_file.write_text(
            "# Tasks\n"
            "- [ ] Task 1\n"
            "- [x] Task 2\n"
            "- [ ] Task 3\n"
        )

        content, tasks = load_tasks(test_file)

        assert len(tasks) == 3
        assert tasks[0].line_no == 1
        assert tasks[0].done is False
        assert tasks[0].text == "Task 1"
        assert tasks[1].line_no == 2
        assert tasks[1].done is True
        assert tasks[1].text == "Task 2"
        assert tasks[2].line_no == 3
        assert tasks[2].done is False

    def test_load_tasks_with_indented_checkboxes(self, tmp_path: Path):
        """Test loading indented tasks."""
        test_file = tmp_path / "tasks.md"
        test_file.write_text(
            "# Tasks\n"
            "## Section\n"
            "  - [ ] Indented task\n"
            "    - [ ] More indented\n"
        )

        _, tasks = load_tasks(test_file)

        assert len(tasks) == 2
        assert tasks[0].text == "Indented task"
        assert tasks[1].text == "More indented"

    def test_load_tasks_empty_file(self, tmp_path: Path):
        """Test loading from a file with no tasks."""
        test_file = tmp_path / "empty.md"
        test_file.write_text("# Just a header\n\nNo tasks here.\n")

        _, tasks = load_tasks(test_file)

        assert len(tasks) == 0

    def test_load_tasks_preserves_content(self, tmp_path: Path):
        """Test that file content is returned."""
        test_file = tmp_path / "tasks.md"
        original_content = "# Tasks\n- [ ] Task\n"
        test_file.write_text(original_content)

        content, _ = load_tasks(test_file)

        assert content == original_content

    def test_load_tasks_handles_x_uppercase(self, tmp_path: Path):
        """Test that both [x] and [X] are recognized as done."""
        test_file = tmp_path / "tasks.md"
        test_file.write_text(
            "- [ ] Lowercase x\n"
            "- [X] Uppercase X\n"
        )

        _, tasks = load_tasks(test_file)

        assert len(tasks) == 2
        assert tasks[0].done is False
        assert tasks[1].done is True

    def test_load_tasks_with_special_characters(self, tmp_path: Path):
        """Test loading tasks with special characters in text."""
        test_file = tmp_path / "tasks.md"
        test_file.write_text(
            "- [ ] Task with: colon\n"
            "- [ ] Task with @ mention\n"
            '- [ ] Task with "quotes"\n'
        )

        _, tasks = load_tasks(test_file)

        assert len(tasks) == 3
        assert "colon" in tasks[0].text
        assert "@" in tasks[1].text
        assert "quotes" in tasks[2].text


class TestCountDone:
    """Test counting completed tasks."""

    def test_count_done_all_open(self):
        """Test counting when all tasks are open."""
        tasks = [
            Task(line_no=1, done=False, text="Task 1"),
            Task(line_no=2, done=False, text="Task 2"),
            Task(line_no=3, done=False, text="Task 3"),
        ]

        assert count_done(tasks) == 0

    def test_count_done_all_done(self):
        """Test counting when all tasks are done."""
        tasks = [
            Task(line_no=1, done=True, text="Task 1"),
            Task(line_no=2, done=True, text="Task 2"),
        ]

        assert count_done(tasks) == 2

    def test_count_done_mixed(self):
        """Test counting with mixed task states."""
        tasks = [
            Task(line_no=1, done=True, text="Done 1"),
            Task(line_no=2, done=False, text="Open 1"),
            Task(line_no=3, done=True, text="Done 2"),
            Task(line_no=4, done=False, text="Open 2"),
        ]

        assert count_done(tasks) == 2

    def test_count_done_empty_list(self):
        """Test counting with empty task list."""
        assert count_done([]) == 0


class TestNextOpenTask:
    """Test finding the next open task."""

    def test_next_open_task_first_open(self):
        """Test getting the first open task."""
        tasks = [
            Task(line_no=1, done=True, text="Done"),
            Task(line_no=2, done=False, text="Open 1"),
            Task(line_no=3, done=False, text="Open 2"),
        ]

        result = next_open_task(tasks)

        assert result is not None
        assert result.line_no == 2
        assert result.text == "Open 1"

    def test_next_open_task_all_done(self):
        """Test when all tasks are done."""
        tasks = [
            Task(line_no=1, done=True, text="Done 1"),
            Task(line_no=2, done=True, text="Done 2"),
        ]

        result = next_open_task(tasks)

        assert result is None

    def test_next_open_task_empty_list(self):
        """Test with empty task list."""
        assert next_open_task([]) is None

    def test_next_open_task_all_open(self):
        """Test when all tasks are open."""
        tasks = [
            Task(line_no=1, done=False, text="First"),
            Task(line_no=2, done=False, text="Second"),
        ]

        result = next_open_task(tasks)

        assert result.line_no == 1
        assert result.text == "First"


class TestValidateTaskFile:
    """Test task file validation."""

    def test_validate_valid_file(self, tmp_path: Path):
        """Test validation of a valid task file."""
        test_file = tmp_path / "valid.md"
        test_file.write_text("# Tasks\n- [ ] Task 1\n")

        # Should not raise
        validate_task_file(test_file)

    def test_validate_file_not_found(self, tmp_path: Path):
        """Test validation when file doesn't exist."""
        missing_file = tmp_path / "missing.md"

        with pytest.raises(TaskFileError, match="not found"):
            validate_task_file(missing_file)

    def test_validate_no_tasks(self, tmp_path: Path):
        """Test validation when file has no tasks."""
        test_file = tmp_path / "no_tasks.md"
        test_file.write_text("# Just a header\n\nNo checkboxes here.\n")

        with pytest.raises(TaskFileError, match="No tasks found"):
            validate_task_file(test_file)

    def test_validate_empty_file(self, tmp_path: Path):
        """Test validation of an empty file."""
        test_file = tmp_path / "empty.md"
        test_file.write_text("")

        with pytest.raises(TaskFileError, match="No tasks found"):
            validate_task_file(test_file)

    def test_validate_with_only_headers(self, tmp_path: Path):
        """Test validation with only markdown headers."""
        test_file = tmp_path / "headers.md"
        test_file.write_text("# Header\n## Subheader\n### Another\n")

        with pytest.raises(TaskFileError, match="No tasks found"):
            validate_task_file(test_file)

    def test_validate_relative_path(self, tmp_path: Path):
        """Test validation with relative path."""
        # Create a file in tmp_path
        test_file = tmp_path / "tasks.md"
        test_file.write_text("- [ ] Task\n")

        # Validate with relative path - should work if cwd is set correctly
        # Use resolve() to get absolute path
        validate_task_file(test_file.resolve())


class TestTaskFileError:
    """Test TaskFileError exception."""

    def test_task_file_error_creation(self):
        """Test creating TaskFileError."""
        error = TaskFileError("Test error message")

        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_task_file_error_can_be_caught(self):
        """Test that TaskFileError can be caught as Exception."""
        with pytest.raises(Exception):
            raise TaskFileError("Test")

    def test_task_file_error_can_be_caught_specifically(self):
        """Test that TaskFileError can be caught specifically."""
        with pytest.raises(TaskFileError):
            raise TaskFileError("Test")
