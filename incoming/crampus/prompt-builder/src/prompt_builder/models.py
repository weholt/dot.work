"""Data models for the multi-agent validation system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskStatus(Enum):
    """Status of a task or subtask."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ValidationType(Enum):
    """Types of validation checks."""

    STATIC = "static"
    BEHAVIOR = "behavior"
    REGRESSION = "regression"
    SYNTHETIC = "synthetic"


class Severity(Enum):
    """Severity levels for issues."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationContract:
    """Defines validation contracts for subtasks."""

    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    test_cases: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)


@dataclass
class Subtask:
    """Represents an atomic subtask in the validation workflow."""

    id: str
    summary: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    contract: ValidationContract = field(default_factory=ValidationContract)
    dependencies: list[str] = field(default_factory=list)
    affected_files: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of a validation check."""

    validator_type: ValidationType
    subtask_id: str
    passed: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Snapshot:
    """Represents a system behavior snapshot."""

    id: str
    kind: str  # e.g. "feature", "test"
    test_name: str | None
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    side_effects: dict[str, Any]
    call_graph_nodes: list[str]
    invariants: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangeImpactResult:
    """Result of change impact analysis."""

    touched_files: list[str]
    touched_symbols: list[str]
    affected_snapshots: list[str]
    affected_subtasks: list[str]
    summary: str
    warnings: list[str]
    risk_score: float = 0.0  # 0.0 to 1.0
    estimated_effort: str | None = None


@dataclass
class SyntheticTestResult:
    """Result of synthetic test generation and execution."""

    created_tests: list[str]  # file paths
    passed: bool
    failing_cases: list[dict[str, Any]]
    coverage_increase: float = 0.0
    execution_time: float = 0.0
    test_framework: str = "pytest"


@dataclass
class AgentConfig:
    """Configuration for individual agents."""

    name: str
    enabled: bool = True
    timeout: float = 300.0  # seconds
    max_retries: int = 3
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """Main task containing multiple subtasks."""

    id: str
    title: str
    description: str
    subtasks: list[Subtask] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    base_ref: str | None = None  # git reference
    head_ref: str | None = None  # git reference
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResultSummary:
    """Summary of all validation results for a task."""

    task_id: str
    total_validations: int
    passed_validations: int
    failed_validations: int
    warnings: list[str] = field(default_factory=list)
    critical_issues: list[str] = field(default_factory=list)
    validation_results: list[ValidationResult] = field(default_factory=list)
    overall_passed: bool = False
    execution_time: float = 0.0


@dataclass
class PRInfo:
    """Information for generating a pull request."""

    title: str
    description: str
    base_branch: str
    head_branch: str
    files_changed: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    reviewers: list[str] = field(default_factory=list)
    draft: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
