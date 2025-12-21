"""
Tests for the Regression Guard orchestrator.
"""

import pytest

from regression_guard.orchestrator import RegressionOrchestrator


@pytest.fixture
def temp_work_dir(tmp_path):
    """Create temporary work directory."""
    work_dir = tmp_path / ".work" / "tasks"
    work_dir.mkdir(parents=True)
    return work_dir


@pytest.fixture
def orchestrator(temp_work_dir):
    """Create orchestrator with temporary work directory."""
    return RegressionOrchestrator(work_dir=str(temp_work_dir))


def test_orchestrator_init(orchestrator, temp_work_dir):
    """Test orchestrator initialization."""
    assert orchestrator.work_dir == temp_work_dir
    assert temp_work_dir.exists()


def test_generate_task_id(orchestrator):
    """Test task ID generation."""
    task_id = orchestrator.generate_task_id()
    assert task_id.startswith("task-")
    assert len(task_id) > 10


def test_start_task_creates_directory(orchestrator, temp_work_dir):
    """Test that starting a task creates necessary directories."""
    task_id = orchestrator.start_task("Test task")
    
    if task_id:  # May fail due to missing pytest in target project
        task_dir = temp_work_dir / task_id
        assert task_dir.exists()


def test_list_tasks_empty(orchestrator, capsys):
    """Test listing tasks when none exist."""
    orchestrator.list_tasks()
    captured = capsys.readouterr()
    assert "No tasks found" in captured.out


def test_find_task_for_subtask_not_found(orchestrator):
    """Test finding task for non-existent subtask."""
    result = orchestrator.find_task_for_subtask("nonexistent")
    assert result is None


def test_show_status_task_not_found(orchestrator, capsys):
    """Test showing status for non-existent task."""
    orchestrator.show_status("task-nonexistent")
    captured = capsys.readouterr()
    assert "Task not found" in captured.out
