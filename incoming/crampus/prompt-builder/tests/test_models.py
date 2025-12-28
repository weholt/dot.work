"""Tests for data models."""

from datetime import datetime

import pytest

from prompt_builder.models import (
    AgentConfig,
    ChangeImpactResult,
    PRInfo,
    Snapshot,
    Subtask,
    SyntheticTestResult,
    Task,
    TaskStatus,
    ValidationContract,
    ValidationResult,
    ValidationType,
)


class TestTask:
    """Test the Task model."""

    def test_task_creation(self):
        """Test basic task creation."""
        task = Task(id="TASK-001", title="Test Task", description="A test task description")

        assert task.id == "TASK-001"
        assert task.title == "Test Task"
        assert task.description == "A test task description"
        assert task.status == TaskStatus.PENDING
        assert task.subtasks == []
        assert task.base_ref is None
        assert task.head_ref is None

    def test_task_with_subtasks(self):
        """Test task with subtasks."""
        subtask = Subtask(id="ST-001", summary="Test subtask", description="A test subtask")

        task = Task(id="TASK-001", title="Test Task", description="A test task description", subtasks=[subtask])

        assert len(task.subtasks) == 1
        assert task.subtasks[0] == subtask

    def test_task_status_transitions(self):
        """Test task status changes."""
        task = Task(id="TASK-001", title="Test Task", description="A test task description")

        assert task.status == TaskStatus.PENDING

        task.status = TaskStatus.IN_PROGRESS
        assert task.status == TaskStatus.IN_PROGRESS

        task.status = TaskStatus.COMPLETED
        assert task.status == TaskStatus.COMPLETED


class TestSubtask:
    """Test the Subtask model."""

    def test_subtask_creation(self):
        """Test basic subtask creation."""
        contract = ValidationContract(
            preconditions=["Code compiles"], postconditions=["Functionality works"], test_cases=["Test basic case"]
        )

        subtask = Subtask(id="ST-001", summary="Test subtask", description="A test subtask", contract=contract)

        assert subtask.id == "ST-001"
        assert subtask.summary == "Test subtask"
        assert subtask.description == "A test subtask"
        assert subtask.status == TaskStatus.PENDING
        assert subtask.contract == contract
        assert subtask.dependencies == []
        assert subtask.affected_files == []

    def test_subtask_with_dependencies(self):
        """Test subtask with dependencies."""
        subtask = Subtask(
            id="ST-002",
            summary="Test subtask with deps",
            description="A test subtask with dependencies",
            dependencies=["ST-001"],
        )

        assert len(subtask.dependencies) == 1
        assert "ST-001" in subtask.dependencies


class TestValidationContract:
    """Test the ValidationContract model."""

    def test_validation_contract_creation(self):
        """Test basic validation contract creation."""
        contract = ValidationContract(
            preconditions=["Precondition 1"],
            postconditions=["Postcondition 1"],
            invariants=["Invariant 1"],
            test_cases=["Test case 1"],
        )

        assert len(contract.preconditions) == 1
        assert len(contract.postconditions) == 1
        assert len(contract.invariants) == 1
        assert len(contract.test_cases) == 1
        assert contract.preconditions[0] == "Precondition 1"

    def test_empty_validation_contract(self):
        """Test empty validation contract."""
        contract = ValidationContract()

        assert contract.preconditions == []
        assert contract.postconditions == []
        assert contract.invariants == []
        assert contract.test_cases == []


class TestValidationResult:
    """Test the ValidationResult model."""

    def test_validation_result_creation(self):
        """Test basic validation result creation."""
        result = ValidationResult(
            validator_type=ValidationType.STATIC,
            subtask_id="ST-001",
            passed=True,
            issues=[],
            warnings=["Warning 1"],
            metrics={"files_checked": 5},
            execution_time=1.5,
        )

        assert result.validator_type == ValidationType.STATIC
        assert result.subtask_id == "ST-001"
        assert result.passed is True
        assert result.issues == []
        assert len(result.warnings) == 1
        assert result.metrics["files_checked"] == 5
        assert result.execution_time == 1.5
        assert isinstance(result.timestamp, datetime)

    def test_validation_result_failure(self):
        """Test validation result with failures."""
        result = ValidationResult(
            validator_type=ValidationType.BEHAVIOR,
            subtask_id="ST-002",
            passed=False,
            issues=["Test failed", "Coverage low"],
        )

        assert result.passed is False
        assert len(result.issues) == 2
        assert "Test failed" in result.issues
        assert "Coverage low" in result.issues


class TestSnapshot:
    """Test the Snapshot model."""

    def test_snapshot_creation(self):
        """Test basic snapshot creation."""
        snapshot = Snapshot(
            id="SNAP-001",
            kind="feature",
            test_name="test_login",
            inputs={"username": "user", "password": "pass"},
            outputs={"status": "success"},
            side_effects={"db_updated": True},
            call_graph_nodes=["login_handler", "auth_service"],
            invariants={"session_created": True},
        )

        assert snapshot.id == "SNAP-001"
        assert snapshot.kind == "feature"
        assert snapshot.test_name == "test_login"
        assert snapshot.inputs["username"] == "user"
        assert snapshot.outputs["status"] == "success"
        assert snapshot.side_effects["db_updated"] is True
        assert len(snapshot.call_graph_nodes) == 2
        assert snapshot.invariants["session_created"] is True


class TestChangeImpactResult:
    """Test the ChangeImpactResult model."""

    def test_change_impact_result_creation(self):
        """Test basic change impact result creation."""
        result = ChangeImpactResult(
            touched_files=["src/auth.py", "tests/test_auth.py"],
            touched_symbols=["Auth.login", "Auth.validate_token"],
            affected_snapshots=["SNAP-001", "SNAP-002"],
            affected_subtasks=["ST-001"],
            summary="Authentication system modified",
            warnings=["Breaking change detected"],
            risk_score=0.7,
            estimated_effort="Medium (1-2 hours)",
        )

        assert len(result.touched_files) == 2
        assert len(result.touched_symbols) == 2
        assert len(result.affected_snapshots) == 2
        assert result.summary == "Authentication system modified"
        assert len(result.warnings) == 1
        assert result.risk_score == 0.7
        assert result.estimated_effort == "Medium (1-2 hours)"


class TestSyntheticTestResult:
    """Test the SyntheticTestResult model."""

    def test_synthetic_test_result_creation(self):
        """Test basic synthetic test result creation."""
        result = SyntheticTestResult(
            created_tests=["tests/synthetic/test_edge_case.py"],
            passed=True,
            failing_cases=[],
            coverage_increase=15.5,
            execution_time=2.3,
            test_framework="pytest",
        )

        assert len(result.created_tests) == 1
        assert result.passed is True
        assert result.failing_cases == []
        assert result.coverage_increase == 15.5
        assert result.execution_time == 2.3
        assert result.test_framework == "pytest"


class TestAgentConfig:
    """Test the AgentConfig model."""

    def test_agent_config_creation(self):
        """Test basic agent config creation."""
        config = AgentConfig(
            name="TestAgent", enabled=True, timeout=300.0, max_retries=3, parameters={"strict_mode": True}
        )

        assert config.name == "TestAgent"
        assert config.enabled is True
        assert config.timeout == 300.0
        assert config.max_retries == 3
        assert config.parameters["strict_mode"] is True

    def test_agent_config_defaults(self):
        """Test agent config with default values."""
        config = AgentConfig(name="TestAgent")

        assert config.name == "TestAgent"
        assert config.enabled is True
        assert config.timeout == 300.0
        assert config.max_retries == 3
        assert config.parameters == {}


class TestPRInfo:
    """Test the PRInfo model."""

    def test_pr_info_creation(self):
        """Test basic PR info creation."""
        pr_info = PRInfo(
            title="Add new feature",
            description="Implementation of new feature with tests",
            base_branch="main",
            head_branch="feature/new-feature",
            files_changed=["src/feature.py", "tests/test_feature.py"],
            labels=["enhancement", "needs-review"],
            reviewers=["team-lead", "senior-dev"],
            draft=False,
        )

        assert pr_info.title == "Add new feature"
        assert "Implementation of new feature" in pr_info.description
        assert pr_info.base_branch == "main"
        assert pr_info.head_branch == "feature/new-feature"
        assert len(pr_info.files_changed) == 2
        assert len(pr_info.labels) == 2
        assert len(pr_info.reviewers) == 2
        assert pr_info.draft is False


class TestEnums:
    """Test enum values."""

    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.SKIPPED.value == "skipped"

    def test_validation_type_values(self):
        """Test ValidationType enum values."""
        assert ValidationType.STATIC.value == "static"
        assert ValidationType.BEHAVIOR.value == "behavior"
        assert ValidationType.REGRESSION.value == "regression"
        assert ValidationType.SYNTHETIC.value == "synthetic"


if __name__ == "__main__":
    pytest.main([__file__])
