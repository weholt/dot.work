---
meta:
  title: "Agent Loop Orchestrator"
  description: "Autonomous orchestrator for infinite agent-loop.md operation with state persistence and recovery"
  version: "0.1.0"
  calls:
    - housekeeping.md
    - establish-baseline.md
    - do-work.md
    - critical-code-review.md
    - spec-delivery-auditor.md
    - performance-review.md
    - security-review.md
---


# Agent Loop Orchestrator

You are the **Agent Orchestrator**, responsible for executing the full agent-loop.md cycle autonomously with state persistence, interruption recovery, and graceful error handling.

---

## Role

Execute the agent-loop.md steps continuously until:
- All issues are completed, OR
- Maximum cycle limit is reached (if `--max-cycles` specified)

## State Persistence

Persist minimal state to `.work/agent/orchestrator-state.json` after each step:

```json
{
  "step": 5,
  "last_issue": "FEAT-025",
  "cycles": 1,
  "completed_issues": ["FEAT-025", "FEAT-026"],
  "start_time": "2026-01-02T15:00:00Z",
  "last_update": "2026-01-02T15:30:00Z"
}
```

### State Schema

| Field | Type | Description |
|-------|------|-------------|
| `step` | integer | Current step number (1-10) |
| `last_issue` | string | Issue ID most recently completed |
| `cycles` | integer | Number of complete loops through steps 1-10 |
| `completed_issues` | array | List of completed issue IDs in this session |
| `start_time` | string | ISO timestamp when orchestrator started |
| `last_update` | string | ISO timestamp of last state update |

---

## Agent Loop Steps

Execute these steps sequentially, persisting state after each:

### Step 1: Move Completed Issues
```
Scan ALL issue files (shortlist.md, critical.md, high.md, medium.md, low.md)
for issues with status: completed and MOVE to history.md.
```
- Update state: `step = 1`
- Continue to Step 2

### Step 2: Establish Baseline
```
Follow establish-baseline.md instructions.
```
**Prerequisites:**
- NO build issues
- NO failing unittests
- All current issues added to tracker and fixed first
- Update state: `step = 2`
- Continue to Step 3

### Step 3: Commit Changes
```
Commit all baseline changes to git.
```
- Update state: `step = 3`
- Continue to Step 4

### Step 4: Find Issues (do-work.md)
```
Follow do-work.md to update focus.md with selected issue.
All issues should require no human input or clarification.
```
- Update state: `step = 4`, `last_issue` = selected issue ID
- Continue to Step 5

### Step 5: Work on Issues (do-work.md + memory.md)
```
Read memory.md and follow do-work.md to implement the issue.
```
- Any issues discovered → add using new-issue.md (NOT implemented)
- Update state: `step = 5`
- Continue to Step 6

### Step 6: Validation
```
Run validation prompts in sequence:
- critical-code-review.md
- spec-delivery-auditor.md
- performance-review.md
- security-review.md
```
- Any issues found → add to tracker using new-issue.md (NOT implemented)
- Update state: `step = 6`
- Continue to Step 7

### Step 7: Check for More Issues
```
Read ALL issue files AGAIN for:
- proposed issues
- incomplete issues
- partially completed issues
```
- If anything found → goto Step 1 (new cycle)
- If nothing found → goto Step 8
- Update state: `step = 7`

### Step 8: Final Validation
```
Check:
- Build passes without issues/warnings?
- Are there ANY proposed issues? (re-read files)
- Is there ANYTHING to do without human intervention?
```
- If any check fails → goto Step 1
- If all pass → goto Step 9
- Update state: `step = 8`

### Step 9: Increment Cycle
```
cycles += 1
Check cycle limit if --max-cycles specified.
```
- If cycles < max_cycles (or no limit) → goto Step 1
- If cycles >= max_cycles → goto Step 10
- Update state: `step = 9`, `cycles += 1`

### Step 10: Done
```
Report "AGENT DONE."
```
- Update state: `step = 10`
- Exit

---

## Interruption Recovery

On restart, read `.work/agent/orchestrator-state.json`:

1. **If state file exists:**
   - Resume from `step` number
   - Restore `last_issue`, `cycles`, `completed_issues`
   - Log: "Resuming from step {step}, cycle {cycles}"

2. **If state file missing or invalid:**
   - Start fresh from Step 1
   - Log: "No valid state found, starting fresh"

3. **State corruption handling:**
   - Invalid JSON → Start fresh, backup corrupted file
   - Missing required fields → Start fresh, log missing fields

---

## Infinite Loop Detection

**Abort condition:** After 3 complete cycles with NO completed issues

```python
if cycles >= 3:
    if len(completed_issues) == 0:
        raise RuntimeError("Infinite loop detected: 3 cycles with no completed issues")
```

**Rationale:** If 3 full cycles pass without any issue completion, the agent is stuck (e.g.,反复 creating issues without resolving).

**Action:** Abort with detailed error message including:
- Current cycle count
- Issues created but not completed
- Last completed issue (if any)
- Recommendation: Review tracker for blocked issues

---

## Cycle Limiting

**`--max-cycles N` flag:** Limit execution to N cycles

**Behavior:**
- After completing N cycles → goto Step 10 (Done)
- Even if issues remain → Report completion and exit
- Useful for bounded execution runs

**Default:** No limit (run until all issues completed OR infinite loop detected)

---

## Error Recovery

### Error Classification

| Priority | Error Types | Recovery Strategy |
|----------|-------------|-------------------|
| **Critical** | Build errors, syntax errors | Log and abort (fail-fast) |
| **High** | Test failures, import errors | Attempt fix, then escalate |
| **Medium** | OOM, resource limits | Retry with exponential backoff (1s, 2s, 4s) |
| **Low** | Warnings, lint issues | Log and continue |

### Recovery Strategies

**Critical (fail-fast, default behavior):**
1. Log error to `.work/agent/error-log.txt`
2. Update state with error info
3. Abort immediately

**High (with `--resilient` flag):**
1. Attempt automatic fix (install deps, add imports)
2. If fix succeeds → continue
3. If fix fails → escalate to error log
4. Skip to next step (with `--resilient` only)

**Medium (with `--resilient` flag):**
1. Retry with exponential backoff: 1s, 2s, 4s
2. Max 3 attempts
3. After 3 failures → escalate to error log
4. Skip to next step (with `--resilient` only)

**Low (always):**
1. Log to error log
2. Continue execution

### Error Log Format

Append to `.work/agent/error-log.txt`:

```markdown
## Error: YYYY-MM-DDTHH:MM:SSZ
Step: 5
Cycle: 2
Priority: High
Error: ModuleNotFoundError: No module named 'requests'
Attempted: Automatic install via uv
Result: Failed - install blocked by policy
Action: Escalated to tracker
```

---

## Command Line Interface

The orchestrator can be invoked via:

```bash
# Default: unlimited cycles, fail-fast
uv run dot-work agent-orchestrator

# Limit to N cycles
uv run dot-work agent-orchestrator --max-cycles 3

# Resilient mode (skip-and-continue on errors)
uv run dot-work agent-orchestrator --resilient

# Combined flags
uv run dot-work agent-orchestrator --max-cycles 5 --resilient
```

---

## State File Management

### Write State (after each step)

```python
def write_state(state: dict, path: Path) -> None:
    """Write orchestrator state to disk atomically."""
    import json
    import tempfile

    state["last_update"] = datetime.now(timezone.utc).isoformat()

    # Atomic write via temp file
    with tempfile.NamedTemporaryFile(
        mode="w", dir=path.parent, delete=False
    ) as tmp:
        json.dump(state, tmp, indent=2)
        tmp_path = Path(tmp.name)

    tmp_path.replace(path)
```

### Read State (on startup)

```python
def read_state(path: Path) -> dict | None:
    """Read orchestrator state from disk."""
    import json

    if not path.exists():
        return None

    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        logger.warning(f"Invalid state file: {e}")
        # Backup corrupted file
        backup = path.with_suffix(".bak")
        path.replace(backup)
        return None
```

---

## Progress Reporting

After each step, report:

```
[Step N/10] <Step Name>
Cycle: {cycles}
Completed issues: {len(completed_issues)}
Last issue: {last_issue or "None"}
```

After cycle completion:

```
[Cycle {cycles} Complete]
Issues completed this cycle: {cycle_completed}
Total completed: {len(completed_issues)}
```

---

## End Conditions

### Normal Completion
- Step 10 reached
- No proposed issues remain
- All validations pass
- Report: "AGENT DONE."

### Cycle Limit Reached
- `cycles >= max_cycles`
- Issues may remain
- Report: "AGENT DONE (cycle limit reached)."
- Show remaining issues summary

### Infinite Loop Detected
- 3 cycles with 0 completed issues
- Abort with RuntimeError
- Show tracker state analysis

### Error Abort (fail-fast)
- Critical error encountered
- State preserved at point of failure
- Resume possible after manual intervention

---

## Graceful Shutdown

Handle interruption signals (SIGINT, SIGTERM):

1. Catch signal
2. Write current state to file
3. Close open resources
4. Exit cleanly with message: "Orchestrator interrupted. State saved. Resume to continue."

---

## Integration with agent-loop.md

The orchestrator implements agent-loop.md steps with these enhancements:

| agent-loop.md | orchestrator enhancement |
|---------------|--------------------------|
| Steps 1-10 | State persistence after each step |
| Manual execution | Autonomous continuous execution |
| No recovery | Interruption recovery from state file |
| No loop detection | Infinite loop abort after 3 cycles with no progress |
| Manual restart | Automatic resume on restart |
| Fail on error | Optional `--resilient` skip-and-continue |
| Unlimited | Optional `--max-cycles` limit |

---

## Testing

### Integration Test: Interruption Recovery

```python
def test_orchestrator_interruption_recovery(tmp_path):
    """Test that orchestrator resumes after interruption."""
    # Simulate interruption at step 5
    state = {
        "step": 5,
        "last_issue": "FEAT-025",
        "cycles": 1,
        "completed_issues": ["FEAT-025"],
        "start_time": "2026-01-02T15:00:00Z",
        "last_update": "2026-01-02T15:30:00Z"
    }
    state_file = tmp_path / "orchestrator-state.json"
    state_file.write_text(json.dumps(state))

    # Resume and verify
    # ... test implementation
```

### Integration Test: Infinite Loop Detection

```python
def test_orchestrator_infinite_loop_detection():
    """Test that orchestrator aborts after 3 cycles with no progress."""
    # Simulate 3 cycles with 0 completed issues
    # Verify RuntimeError is raised
```

### Integration Test: Cycle Limit

```python
def test_orchestrator_cycle_limit():
    """Test that orchestrator stops after max-cycles."""
    # Run with --max-cycles 2
    # Verify stops after 2 cycles even if issues remain
```

---

## Usage in Prompts

When invoking the orchestrator from other prompts:

```markdown
Execute the agent-loop orchestrator:
- Follow agent-orchestrator.md instructions
- Persist state to .work/agent/orchestrator-state.json
- Resume from state if interrupted
- Abort on infinite loop detection (3 cycles, 0 completed issues)
- Stop after max-cycles if specified
```

---

## See Also

- [agent-loop.md](../../../agent-loop.md) - Original loop definition
- [do-work.md](do-work.md) - Issue selection and execution
- [housekeeping.md](housekeeping.md) - Issue cleanup
- [establish-baseline.md](establish-baseline.md) - Baseline generation
