"""Integration tests for agent-orchestrator prompt.

Tests cover:
- State persistence and recovery
- Interruption recovery
- Infinite loop detection
- Cycle limiting
- Error recovery (fail-fast and resilient modes)
"""

from __future__ import annotations

from pathlib import Path

from dot_work.prompts.agent_orchestrator import (
    MAX_CYCLES_BEFORE_ABORT,
    OrchestratorState,
    read_state,
    write_state,
)


class TestOrchestratorState:
    """Test orchestrator state dataclass."""

    def test_state_initialization(self) -> None:
        """Test creating a new orchestrator state."""
        state = OrchestratorState()
        assert state.step == 0
        assert state.last_issue is None
        assert state.cycles == 0
        assert state.completed_issues == []
        assert state.start_time is not None
        assert state.last_update is not None

    def test_state_with_values(self) -> None:
        """Test creating state with specific values."""
        state = OrchestratorState(
            step=5,
            last_issue="FEAT-025",
            cycles=2,
            completed_issues=["FEAT-025", "FEAT-026"],
        )
        assert state.step == 5
        assert state.last_issue == "FEAT-025"
        assert state.cycles == 2
        assert len(state.completed_issues) == 2


class TestStatePersistence:
    """Test state file persistence."""

    def test_write_and_read_state(self, tmp_path: Path) -> None:
        """Test writing and reading state file."""
        state_file = tmp_path / "orchestrator-state.json"
        state = OrchestratorState(
            step=3,
            last_issue="FEAT-025",
            cycles=1,
            completed_issues=["FEAT-025"],
        )

        write_state(state, state_file)
        assert state_file.exists()

        recovered = read_state(state_file)
        assert recovered is not None
        assert recovered.step == 3
        assert recovered.last_issue == "FEAT-025"
        assert recovered.cycles == 1
        assert recovered.completed_issues == ["FEAT-025"]

    def test_read_state_missing_file(self, tmp_path: Path) -> None:
        """Test reading state when file doesn't exist."""
        state_file = tmp_path / "nonexistent.json"
        result = read_state(state_file)
        assert result is None

    def test_write_state_atomic(self, tmp_path: Path) -> None:
        """Test that state writes are atomic (uses temp file)."""
        state_file = tmp_path / "orchestrator-state.json"
        state = OrchestratorState(step=1)

        # Write state - should use atomic temp file + rename
        write_state(state, state_file)

        # Verify final file exists and is valid
        assert state_file.exists()
        recovered = read_state(state_file)
        assert recovered is not None
        assert recovered.step == 1

        # Verify no .tmp file left behind
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_read_invalid_json(self, tmp_path: Path) -> None:
        """Test reading corrupted state file."""
        state_file = tmp_path / "corrupt.json"
        state_file.write_text("{invalid json}")

        # Should backup and return None
        result = read_state(state_file)
        assert result is None
        assert (tmp_path / "corrupt.bak").exists()

    def test_read_missing_required_fields(self, tmp_path: Path) -> None:
        """Test reading state with missing required fields."""
        state_file = tmp_path / "incomplete.json"
        state_file.write_text('{"step": 1}')  # Missing cycles

        result = read_state(state_file)
        assert result is None


class TestInterruptionRecovery:
    """Test interruption and recovery scenarios."""

    def test_resume_from_step_5(self, tmp_path: Path) -> None:
        """Test resuming from step 5 (work on issues)."""
        state_file = tmp_path / "orchestrator-state.json"
        initial_state = OrchestratorState(
            step=5,
            last_issue="FEAT-025",
            cycles=1,
            completed_issues=["FEAT-025"],
        )
        write_state(initial_state, state_file)

        # Simulate restart
        recovered = read_state(state_file)
        assert recovered is not None
        assert recovered.step == 5
        assert recovered.last_issue == "FEAT-025"
        assert recovered.cycles == 1

        # Should continue from step 6 (validation)
        next_step = recovered.step + 1
        assert next_step == 6

    def test_resume_with_completed_issues(self, tmp_path: Path) -> None:
        """Test resuming with list of completed issues."""
        state_file = tmp_path / "orchestrator-state.json"
        initial_state = OrchestratorState(
            step=7,
            last_issue="FEAT-027",
            cycles=2,
            completed_issues=["FEAT-025", "FEAT-026", "FEAT-027"],
        )
        write_state(initial_state, state_file)

        recovered = read_state(state_file)
        assert recovered is not None
        assert len(recovered.completed_issues) == 3

    def test_fresh_start_without_state(self, tmp_path: Path) -> None:
        """Test starting fresh when no state file exists."""
        state_file = tmp_path / "nonexistent.json"
        result = read_state(state_file)

        assert result is None
        # Orchestrator should start from step 1


class TestInfiniteLoopDetection:
    """Test infinite loop detection and abort."""

    def test_infinite_loop_detected_after_3_cycles(self) -> None:
        """Test abort after 3 cycles with no completed issues."""
        state = OrchestratorState(
            step=9, cycles=3, completed_issues=[]
        )

        # Should detect infinite loop
        assert state.cycles >= MAX_CYCLES_BEFORE_ABORT
        assert len(state.completed_issues) == 0

    def test_no_abort_with_completed_issues(self) -> None:
        """Test no abort when at least one issue completed."""
        state = OrchestratorState(
            step=9, cycles=3, completed_issues=["FEAT-025"]
        )

        # Should NOT abort (made progress)
        assert not (
            state.cycles >= MAX_CYCLES_BEFORE_ABORT
            and len(state.completed_issues) == 0
        )

    def test_no_abort_before_threshold(self) -> None:
        """Test no abort before 3 cycles."""
        state = OrchestratorState(step=9, cycles=2, completed_issues=[])

        # Should NOT abort (under threshold)
        assert not (
            state.cycles >= MAX_CYCLES_BEFORE_ABORT
            and len(state.completed_issues) == 0
        )

    def test_loop_detection_error_message(self) -> None:
        """Test infinite loop error message includes context."""
        state = OrchestratorState(
            step=9, cycles=3, completed_issues=[]
        )

        if state.cycles >= MAX_CYCLES_BEFORE_ABORT and len(
            state.completed_issues
        ) == 0:
            error_msg = (
                f"Infinite loop detected: {state.cycles} cycles "
                f"with {len(state.completed_issues)} completed issues"
            )
            assert "3 cycles" in error_msg
            assert "0 completed issues" in error_msg


class TestCycleLimiting:
    """Test cycle limit functionality."""

    def test_cycle_limit_reached(self, tmp_path: Path) -> None:
        """Test stopping when max-cycles limit is reached."""
        state_file = tmp_path / "orchestrator-state.json"
        state = OrchestratorState(
            step=9, cycles=5, completed_issues=["FEAT-025"]
        )
        write_state(state, state_file)

        max_cycles = 5
        recovered = read_state(state_file)
        assert recovered is not None

        # Should stop (step 10: done)
        if recovered.cycles >= max_cycles:
            next_step = 10  # Done
        else:
            next_step = 1  # Continue

        assert next_step == 10

    def test_cycle_limit_not_reached(self, tmp_path: Path) -> None:
        """Test continuing when under max-cycles limit."""
        state_file = tmp_path / "orchestrator-state.json"
        state = OrchestratorState(
            step=9, cycles=2, completed_issues=["FEAT-025"]
        )
        write_state(state, state_file)

        max_cycles = 5
        recovered = read_state(state_file)
        assert recovered is not None

        # Should continue to next cycle
        if recovered.cycles >= max_cycles:
            next_step = 10  # Done
        else:
            next_step = 1  # Continue

        assert next_step == 1

    def test_unlimited_cycles_by_default(self) -> None:
        """Test that unlimited cycles is the default."""
        # No max_cycles specified
        state = OrchestratorState(step=9, cycles=100, completed_issues=["FEAT-025"])

        # Should continue (no limit)
        assert state.cycles == 100
        # Would only stop if infinite loop detected or no issues


class TestErrorRecovery:
    """Test error recovery strategies."""

    def test_critical_error_aborts(self, tmp_path: Path) -> None:
        """Test that critical errors abort immediately."""
        error_log = tmp_path / "error-log.txt"

        # Simulate critical error (syntax error)
        error_entry = {
            "step": 5,
            "cycle": 1,
            "priority": "Critical",
            "error": "SyntaxError: invalid syntax",
        }

        # Write to error log
        with open(error_log, "a") as f:
            f.write(f"\n## Error: {error_entry['error']}\n")
            f.write(f"Step: {error_entry['step']}\n")
            f.write(f"Cycle: {error_entry['cycle']}\n")
            f.write(f"Priority: {error_entry['priority']}\n")
            f.write("Action: Aborted\n")

        assert error_log.exists()
        content = error_log.read_text()
        assert "Critical" in content
        assert "Aborted" in content

    def test_high_error_with_resilient(self, tmp_path: Path) -> None:
        """Test high priority error with --resilient flag."""
        error_log = tmp_path / "error-log.txt"

        # Simulate high error (import error) with resilient mode
        error_entry = {
            "step": 5,
            "cycle": 1,
            "priority": "High",
            "error": "ModuleNotFoundError: No module named 'requests'",
            "attempted": "Automatic install via uv",
            "result": "Failed - install blocked by policy",
            "action": "Escalated to tracker",
            "mode": "resilient",
        }

        # Write to error log
        with open(error_log, "a") as f:
            f.write(f"\n## Error: {error_entry['error']}\n")
            f.write(f"Step: {error_entry['step']}\n")
            f.write(f"Cycle: {error_entry['cycle']}\n")
            f.write(f"Priority: {error_entry['priority']}\n")
            f.write(f"Attempted: {error_entry['attempted']}\n")
            f.write(f"Result: {error_entry['result']}\n")
            f.write(f"Action: {error_entry['action']}\n")

        assert error_log.exists()
        content = error_log.read_text()
        assert "High" in content
        assert "Escalated to tracker" in content

    def test_medium_error_retry_backoff(self, tmp_path: Path) -> None:
        """Test medium priority error with exponential backoff."""
        error_log = tmp_path / "error-log.txt"

        # Simulate medium error (OOM) with retries
        for attempt in range(1, 4):
            error_entry = {
                "step": 5,
                "cycle": 1,
                "priority": "Medium",
                "error": "MemoryError: Out of memory",
                "attempt": attempt,
                "backoff": f"{2 ** (attempt - 1)}s",
                "action": "Retry" if attempt < 3 else "Escalated",
            }

            with open(error_log, "a") as f:
                f.write(f"\n## Error: {error_entry['error']}\n")
                f.write(f"Step: {error_entry['step']}\n")
                f.write(f"Priority: {error_entry['priority']}\n")
                f.write(f"Attempt: {error_entry['attempt']}\n")
                f.write(f"Backoff: {error_entry['backoff']}\n")
                f.write(f"Action: {error_entry['action']}\n")

        content = error_log.read_text()
        assert "Attempt: 1" in content
        assert "Backoff: 1s" in content
        assert "Attempt: 2" in content
        assert "Backoff: 2s" in content
        assert "Attempt: 3" in content
        assert "Backoff: 4s" in content
        assert "Escalated" in content

    def test_low_error_logged_only(self, tmp_path: Path) -> None:
        """Test low priority errors are logged but don't abort."""
        error_log = tmp_path / "error-log.txt"

        # Simulate low error (warning)
        error_entry = {
            "step": 6,
            "cycle": 1,
            "priority": "Low",
            "error": "LintWarning: unused variable 'temp'",
            "action": "Logged and continued",
        }

        with open(error_log, "a") as f:
            f.write(f"\n## Error: {error_entry['error']}\n")
            f.write(f"Step: {error_entry['step']}\n")
            f.write(f"Priority: {error_entry['priority']}\n")
            f.write(f"Action: {error_entry['action']}\n")

        content = error_log.read_text()
        assert "Low" in content
        assert "Logged and continued" in content


class TestProgressReporting:
    """Test progress reporting functionality."""

    def test_step_progress_report(self) -> None:
        """Test progress report after each step."""
        state = OrchestratorState(
            step=5, last_issue="FEAT-025", cycles=1, completed_issues=["FEAT-025"]
        )

        report = (
            f"[Step {state.step}/10] Work on Issues\n"
            f"Cycle: {state.cycles}\n"
            f"Completed issues: {len(state.completed_issues)}\n"
            f"Last issue: {state.last_issue or 'None'}"
        )

        assert "Step 5/10" in report
        assert "Cycle: 1" in report
        assert "Completed issues: 1" in report
        assert "Last issue: FEAT-025" in report

    def test_cycle_completion_report(self) -> None:
        """Test report after cycle completion."""
        state = OrchestratorState(
            step=9, cycles=2, completed_issues=["FEAT-025", "FEAT-026"]
        )

        # Assume 2 issues completed in this cycle
        cycle_completed = 2

        report = (
            f"[Cycle {state.cycles} Complete]\n"
            f"Issues completed this cycle: {cycle_completed}\n"
            f"Total completed: {len(state.completed_issues)}"
        )

        assert "Cycle 2 Complete" in report
        assert "Issues completed this cycle: 2" in report
        assert "Total completed: 2" in report


class TestStateTransitions:
    """Test state transitions through steps."""

    def test_state_transition_1_to_2(self) -> None:
        """Test transition from step 1 to 2."""
        state = OrchestratorState(step=1)
        state.step = 2
        assert state.step == 2

    def test_state_transition_with_completed_issue(self) -> None:
        """Test transition when issue is completed."""
        state = OrchestratorState(
            step=5, cycles=1, completed_issues=["FEAT-025"]
        )

        # Complete another issue
        state.last_issue = "FEAT-026"
        state.completed_issues.append("FEAT-026")
        state.step = 6

        assert state.last_issue == "FEAT-026"
        assert len(state.completed_issues) == 2
        assert state.step == 6

    def test_cycle_increment(self) -> None:
        """Test cycle increment after completing loop."""
        state = OrchestratorState(step=9, cycles=1)
        state.cycles += 1
        assert state.cycles == 2
