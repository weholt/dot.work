"""Data models for the multi-agent validation system."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime


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
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    invariants: List[str] = field(default_factory=list)
    test_cases: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)


@dataclass
class Subtask:
    """Represents an atomic subtask in the validation workflow."""
    id: str
    summary: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    contract: ValidationContract = field(default_factory=ValidationContract)
    dependencies: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    validator_type: ValidationType
    subtask_id: str
    passed: bool
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Snapshot:
    """Represents a system behavior snapshot."""
    id: str
    kind: str  # e.g. "feature", "test"
    test_name: Optional[str]
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    side_effects: Dict[str, Any]
    call_graph_nodes: List[str]
    invariants: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangeImpactResult:
    """Result of change impact analysis."""
    touched_files: List[str]
    touched_symbols: List[str]
    affected_snapshots: List[str]
    affected_subtasks: List[str]
    summary: str
    warnings: List[str]
    risk_score: float = 0.0  # 0.0 to 1.0
    estimated_effort: Optional[str] = None


@dataclass
class SyntheticTestResult:
    """Result of synthetic test generation and execution."""
    created_tests: List[str]  # file paths
    passed: bool
    failing_cases: List[Dict[str, Any]]
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
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """Main task containing multiple subtasks."""
    id: str
    title: str
    description: str
    subtasks: List[Subtask] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    base_ref: Optional[str] = None  # git reference
    head_ref: Optional[str] = None  # git reference
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResultSummary:
    """Summary of all validation results for a task."""
    task_id: str
    total_validations: int
    passed_validations: int
    failed_validations: int
    warnings: List[str] = field(default_factory=list)
    critical_issues: List[str] = field(default_factory=list)
    validation_results: List[ValidationResult] = field(default_factory=list)
    overall_passed: bool = False
    execution_time: float = 0.0


@dataclass
class PRInfo:
    """Information for generating a pull request."""
    title: str
    description: str
    base_branch: str
    head_branch: str
    files_changed: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    reviewers: List[str] = field(default_factory=list)
    draft: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)