"""Tests for CLI functionality."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
import typer

from prompt_builder.cli import (
    app,
    run_validation_workflow,
    save_task_state,
    display_results,
)
from prompt_builder.models import (
    Task,
    TaskStatus,
    ValidationResult,
    ValidationType,
    ValidationResultSummary,
)


class TestCLICommands:
    """Test CLI command functions."""

    @patch('prompt_builder.cli.run_validation_workflow')
    @patch('prompt_builder.cli.setup_logging')
    def test_start_command_success(self, mock_logging, mock_workflow, tmp_path):
        """Test successful start command."""
        # Mock successful validation
        mock_summary = ValidationResultSummary(
            task_id="TASK-001",
            total_validations=3,
            passed_validations=3,
            failed_validations=0,
            validation_results=[],
            overall_passed=True,
            execution_time=10.5
        )
        mock_workflow.return_value = mock_summary

        # Test command invocation
        runner = typer.testing.CliRunner()
        result = runner.invoke(app, [
            'start',
            'Test task description',
            '--title', 'Test Task',
            '--dry-run'
        ])

        assert result.exit_code == 0
        mock_logging.assert_called_once()

    def test_init_command(self, tmp_path):
        """Test init command."""
        runner = typer.testing.CliRunner()

        with patch('pathlib.Path.cwd', return_value=tmp_path):
            result = runner.invoke(app, ['init', '--force'])

        assert result.exit_code == 0
        assert '✅' in result.stdout

    @patch('pathlib.Path.exists')
    def test_init_command_exists_no_force(self, mock_exists):
        """Test init command when config exists and no force flag."""
        mock_exists.return_value = True

        runner = typer.testing.CliRunner()
        result = runner.invoke(app, ['init'])

        assert result.exit_code == 0
        assert 'already exists' in result.stdout


class TestValidationWorkflow:
    """Test validation workflow functionality."""

    @pytest.mark.asyncio
    async def test_run_validation_workflow_success(self, tmp_path):
        """Test successful validation workflow."""
        task = Task(
            id="TASK-001",
            title="Test Task",
            description="Test description"
        )

        with patch('prompt_builder.agents.PlannerAgent') as mock_planner, \
             patch('prompt_builder.agents.StaticValidatorAgent') as mock_static, \
             patch('prompt_builder.agents.BehaviorValidatorAgent') as mock_behavior:

            # Mock agent responses
            mock_planner.return_value.execute.return_value = ValidationResult(
                validator_type=ValidationType.STATIC,
                subtask_id="TASK-001",
                passed=True,
                issues=[]
            )

            mock_static.return_value.execute.return_value = ValidationResult(
                validator_type=ValidationType.STATIC,
                subtask_id="ST-001",
                passed=True,
                issues=[]
            )

            mock_behavior.return_value.execute.return_value = ValidationResult(
                validator_type=ValidationType.BEHAVIOR,
                subtask_id="ST-001",
                passed=True,
                issues=[]
            )

            with patch('prompt_builder.cli.save_task_state'):
                summary = await run_validation_workflow(task)

                assert summary.task_id == "TASK-001"
                assert summary.overall_passed is True
                assert summary.total_validations >= 3

    @pytest.mark.asyncio
    async def test_run_validation_workflow_with_specific_agents(self, tmp_path):
        """Test validation workflow with specific agents only."""
        task = Task(
            id="TASK-002",
            title="Test Task",
            description="Test description"
        )

        with patch('prompt_builder.agents.PlannerAgent') as mock_planner:
            mock_planner.return_value.execute.return_value = ValidationResult(
                validator_type=ValidationType.STATIC,
                subtask_id="TASK-002",
                passed=True,
                issues=[]
            )

            with patch('prompt_builder.cli.save_task_state'):
                summary = await run_validation_workflow(
                    task,
                    specific_agents=["planner"]
                )

                assert summary.task_id == "TASK-002"
                assert summary.overall_passed is True
                # Should only have planner validation
                assert summary.total_validations == 1


class TestTaskState:
    """Test task state management."""

    def test_save_task_state(self, tmp_path):
        """Test saving task state to file."""
        task = Task(
            id="TASK-001",
            title="Test Task",
            description="Test description",
            status=TaskStatus.COMPLETED
        )

        # Create subtask
        from prompt_builder.models import Subtask, ValidationContract
        subtask = Subtask(
            id="ST-001",
            summary="Test subtask",
            description="Test subtask description",
            contract=ValidationContract()
        )
        task.subtasks = [subtask]

        tasks_dir = tmp_path / ".prompt-builder" / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)

        with patch('pathlib.Path') as mock_path:
            mock_path.return_value = tasks_dir / f"{task.id}.json"

            save_task_state(task)

            # Verify file was created and contains correct data
            task_file = tasks_dir / f"{task.id}.json"
            assert task_file.exists()

            with open(task_file, 'r') as f:
                saved_data = json.load(f)

            assert saved_data['id'] == task.id
            assert saved_data['title'] == task.title
            assert saved_data['status'] == TaskStatus.COMPLETED.value
            assert len(saved_data['subtasks']) == 1
            assert saved_data['subtasks'][0]['id'] == subtask.id


class TestDisplayFunctions:
    """Test display and formatting functions."""

    def test_display_results(self):
        """Test results display function."""
        task = Task(
            id="TASK-001",
            title="Test Task",
            description="Test description"
        )

        validation_result = ValidationResult(
            validator_type=ValidationType.STATIC,
            subtask_id="ST-001",
            passed=True,
            issues=["Minor issue"],
            warnings=["Warning"],
            execution_time=1.5
        )

        summary = ValidationResultSummary(
            task_id="TASK-001",
            total_validations=1,
            passed_validations=1,
            failed_validations=0,
            warnings=["Warning"],
            validation_results=[validation_result],
            overall_passed=True,
            execution_time=1.5
        )

        # Mock console to capture output
        with patch('prompt_builder.cli.console') as mock_console:
            display_results(task, summary)

            # Should have called console methods
            assert mock_console.print.called

    def test_display_results_with_failures(self):
        """Test displaying results with validation failures."""
        task = Task(
            id="TASK-002",
            title="Failed Task",
            description="Test description"
        )

        validation_result = ValidationResult(
            validator_type=ValidationType.BEHAVIOR,
            subtask_id="ST-001",
            passed=False,
            issues=["Test failed"],
            warnings=[],
            execution_time=2.0
        )

        summary = ValidationResultSummary(
            task_id="TASK-002",
            total_validations=1,
            passed_validations=0,
            failed_validations=1,
            critical_issues=["Critical issue"],
            validation_results=[validation_result],
            overall_passed=False,
            execution_time=2.0
        )

        with patch('prompt_builder.cli.console') as mock_console:
            display_results(task, summary)

            # Should display failures
            assert mock_console.print.called


class TestUtilityFunctions:
    """Test utility functions used by CLI."""

    def test_display_task_status_verbose(self):
        """Test task status display with verbose output."""
        from datetime import datetime, timedelta

        task = Task(
            id="TASK-001",
            title="Test Task",
            description="Test description",
            status=TaskStatus.COMPLETED,
            created_at=datetime.now(),
            started_at=datetime.now(),
            completed_at=datetime.now() + timedelta(hours=1)
        )

        with patch('prompt_builder.cli.console') as mock_console:
            from prompt_builder.cli import display_task_status
            display_task_status(task, verbose=True)

            assert mock_console.print.called

    def test_display_task_list_verbose(self):
        """Test task list display with verbose output."""
        from datetime import datetime, timedelta

        task = Task(
            id="TASK-001",
            title="Test Task",
            description="Test description",
            status=TaskStatus.COMPLETED,
            created_at=datetime.now(),
            started_at=datetime.now(),
            completed_at=datetime.now() + timedelta(hours=1)
        )

        with patch('prompt_builder.cli.console') as mock_console:
            from prompt_builder.cli import display_task_list
            display_task_list([task], verbose=True)

            assert mock_console.print.called


if __name__ == "__main__":
    pytest.main([__file__])