"""Agent orchestrator state management for agent-loop.md execution.

This module provides state persistence, interruption recovery, and
infinite loop detection for autonomous agent-loop execution.
"""

from __future__ import annotations

import json
import logging
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Constants
DEFAULT_STATE_PATH = Path(".work/agent/orchestrator-state.json")
MAX_CYCLES_BEFORE_ABORT = 3
DEFAULT_MAX_CYCLES = 0  # 0 = unlimited


@dataclass
class OrchestratorState:
    """State for agent orchestrator execution.

    Attributes:
        step: Current step number (0-10).
        last_issue: Issue ID most recently completed.
        cycles: Number of complete loops through steps 1-10.
        completed_issues: List of completed issue IDs in this session.
        start_time: ISO timestamp when orchestrator started.
        last_update: ISO timestamp of last state update.
    """

    step: int = 0
    last_issue: str | None = None
    cycles: int = 0
    completed_issues: list[str] = field(default_factory=list)
    start_time: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    last_update: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def should_abort_infinite_loop(self) -> bool:
        """Check if orchestrator should abort due to infinite loop.

        Returns:
            True if 3+ cycles with no completed issues.
        """
        return (
            self.cycles >= MAX_CYCLES_BEFORE_ABORT
            and len(self.completed_issues) == 0
        )

    def should_stop_cycle_limit(self, max_cycles: int) -> bool:
        """Check if orchestrator should stop due to cycle limit.

        Args:
            max_cycles: Maximum cycles to run (0 = unlimited).

        Returns:
            True if cycles >= max_cycles (and max_cycles > 0).
        """
        return max_cycles > 0 and self.cycles >= max_cycles


def write_state(state: OrchestratorState, path: Path) -> None:
    """Write orchestrator state to disk atomically.

    Uses temp file + rename for atomic write.

    Args:
        state: State to write.
        path: Destination path for state file.
    """
    state.last_update = datetime.now(UTC).isoformat()

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file first (atomic operation)
    state_dict = {
        "step": state.step,
        "last_issue": state.last_issue,
        "cycles": state.cycles,
        "completed_issues": state.completed_issues,
        "start_time": state.start_time,
        "last_update": state.last_update,
    }

    try:
        # Create temp file in same directory for atomic rename
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=path.parent,
            prefix=f"{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as tmp:
            json.dump(state_dict, tmp, indent=2)
            tmp_path = Path(tmp.name)

        # Atomic replace
        tmp_path.replace(path)
        logger.debug(f"State written to {path}")

    except OSError as e:
        logger.error(f"Failed to write state: {e}")
        # Clean up temp file if it exists
        if "tmp_path" in locals():
            tmp_path.unlink(missing_ok=True)
        raise


def read_state(path: Path) -> OrchestratorState | None:
    """Read orchestrator state from disk.

    Args:
        path: Path to state file.

    Returns:
        OrchestratorState if file exists and valid, None otherwise.
    """
    if not path.exists():
        logger.debug(f"State file not found: {path}")
        return None

    try:
        state_dict = json.loads(path.read_text())

        # Validate required fields
        required_fields = ["step", "last_issue", "cycles", "completed_issues"]
        missing = [f for f in required_fields if f not in state_dict]
        if missing:
            logger.warning(f"State missing required fields: {missing}")
            # Backup corrupted file
            _backup_state(path)
            return None

        return OrchestratorState(
            step=state_dict["step"],
            last_issue=state_dict["last_issue"],
            cycles=state_dict["cycles"],
            completed_issues=state_dict["completed_issues"],
            start_time=state_dict.get("start_time"),
            last_update=state_dict.get("last_update"),
        )

    except (OSError, json.JSONDecodeError) as e:
        logger.warning(f"Invalid state file: {e}")
        # Backup corrupted file
        _backup_state(path)
        return None


def _backup_state(path: Path) -> None:
    """Backup corrupted or invalid state file.

    Args:
        path: Path to state file to backup.
    """
    backup_path = path.with_suffix(".bak")
    try:
        path.replace(backup_path)
        logger.info(f"Backed up invalid state to {backup_path}")
    except OSError as e:
        logger.warning(f"Failed to backup state file: {e}")


def format_progress_report(state: OrchestratorState, step_name: str) -> str:
    """Format progress report for current step.

    Args:
        state: Current orchestrator state.
        step_name: Name of current step.

    Returns:
        Formatted progress report string.
    """
    return (
        f"[Step {state.step}/10] {step_name}\n"
        f"Cycle: {state.cycles}\n"
        f"Completed issues: {len(state.completed_issues)}\n"
        f"Last issue: {state.last_issue or 'None'}"
    )


def format_cycle_report(state: OrchestratorState, cycle_completed: int) -> str:
    """Format report for completed cycle.

    Args:
        state: Current orchestrator state.
        cycle_completed: Number of issues completed this cycle.

    Returns:
        Formatted cycle report string.
    """
    return (
        f"[Cycle {state.cycles} Complete]\n"
        f"Issues completed this cycle: {cycle_completed}\n"
        f"Total completed: {len(state.completed_issues)}"
    )


def classify_error(error: Exception) -> str:
    """Classify error by priority level.

    Args:
        error: Exception to classify.

    Returns:
        Priority level: "Critical", "High", "Medium", or "Low".
    """
    error_type = type(error).__name__
    error_msg = str(error).lower()

    # Critical: Build/syntax errors
    if error_type in ("SyntaxError", "IndentationError"):
        return "Critical"
    if "build" in error_msg and "error" in error_msg:
        return "Critical"

    # High: Test failures, import errors
    if error_type in (
        "ImportError",
        "ModuleNotFoundError",
        "AssertionError",
        "TestFailure",
    ):
        return "High"

    # Medium: Resource limits
    if error_type in ("MemoryError", "OutOfMemoryError"):
        return "Medium"
    if "out of memory" in error_msg or "oom" in error_msg:
        return "Medium"

    # Low: Warnings, lint issues
    if "warning" in error_msg or "lint" in error_msg:
        return "Low"

    # Default to high for unknown errors
    return "High"


def log_error(
    error_log_path: Path,
    error: Exception,
    step: int,
    cycle: int,
    priority: str,
    attempted: str | None = None,
    result: str | None = None,
    action: str | None = None,
) -> None:
    """Append error to error log.

    Args:
        error_log_path: Path to error log file.
        error: Exception that occurred.
        step: Step number when error occurred.
        cycle: Cycle number when error occurred.
        priority: Error priority level.
        attempted: What recovery was attempted (if any).
        result: Result of recovery attempt (if any).
        action: Action taken (e.g., "Aborted", "Escalated to tracker").
    """
    error_log_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).isoformat()
    error_str = f"{type(error).__name__}: {error}"

    with open(error_log_path, "a") as f:
        f.write(f"\n## Error: {timestamp}\n")
        f.write(f"Step: {step}\n")
        f.write(f"Cycle: {cycle}\n")
        f.write(f"Priority: {priority}\n")
        f.write(f"Error: {error_str}\n")
        if attempted:
            f.write(f"Attempted: {attempted}\n")
        if result:
            f.write(f"Result: {result}\n")
        if action:
            f.write(f"Action: {action}\n")

    logger.info(f"Error logged to {error_log_path}")
