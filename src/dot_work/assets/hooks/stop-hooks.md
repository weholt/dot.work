---
name: stop-hooks
description: Completion promises and stop conditions for autonomous loop control
compatibility: Claude Code, compatible harnesses with completion detection
environments:
  claude:
    target: ".claude/hooks/"
    filename: "stop-hooks.md"
  opencode:
    target: ".opencode/hooks/"
    filename: "stop-hooks.md"
  copilot:
    target: ".github/prompts/hooks/"
    filename: "stop-hooks.md"
---

# Stop Hooks

This document defines the completion promises (stop hooks) that signal loop termination in autonomous agent operation. These integrate with harnesses like Claude Code that support completion detection.

---

## Completion Promises

The agent outputs specific promise markers that harnesses detect to control loop continuation.

### LOOP_DONE

**Signal:** All work complete, no remaining issues.

```xml
<promise>LOOP_DONE</promise>
```

**Conditions:**
- No proposed issues in any priority queue
- No in-progress issues remaining
- All blocked issues (if any) require human intervention
- Session goals achieved

**Harness action:** Exit loop with success status.

---

### LOOP_CONTINUE

**Signal:** More work remains, loop should continue.

```xml
<promise>LOOP_CONTINUE</promise>
```

**Conditions:**
- At least one proposed or in-progress issue exists
- Issue was just completed and more remain
- Not blocked and not done

**Harness action:** Start next iteration.

---

### LOOP_BLOCKED

**Signal:** Cannot proceed without human intervention.

```xml
<promise>LOOP_BLOCKED</promise>
```

**Conditions:**
- Current issue is blocked (external dependency, permission needed)
- All remaining issues are blocked
- Encountered unrecoverable error

**Harness action:** Pause loop, request human input.

---

### LOOP_ERROR

**Signal:** Unexpected error occurred.

```xml
<promise>LOOP_ERROR</promise>
```

**Conditions:**
- System error (file not found, parse failure)
- Validation command crashed
- State corruption detected

**Harness action:** Exit loop with error status, preserve state for debugging.

---

## Promise Context

Include context with the promise for logging and debugging:

```xml
<promise>LOOP_DONE</promise>
<context>
  session_id: "sess-2026-01-05-001"
  iterations: 5
  issues_completed: 3
  remaining_blocked: 1
  duration_minutes: 45
  reason: "All proposed issues completed. 1 issue blocked awaiting dependency."
</context>
```

---

## Integration Points

### Loop Evaluator Output

The loop-evaluator subagent outputs the promise:

```python
def evaluate_loop():
    report = load_validation_report()
    
    if all_issues_done() and no_blocked():
        emit("<promise>LOOP_DONE</promise>")
    elif has_selectable_issues():
        emit("<promise>LOOP_CONTINUE</promise>")
    elif all_remaining_blocked():
        emit("<promise>LOOP_BLOCKED</promise>")
    else:
        emit("<promise>LOOP_ERROR</promise>")
```

### Claude Code Harness

The harness detects promises in agent output:

```bash
# Pseudocode for harness loop
while true; do
    output=$(claude agent run)
    
    if contains "$output" "LOOP_DONE"; then
        echo "Loop completed successfully"
        exit 0
    elif contains "$output" "LOOP_CONTINUE"; then
        continue
    elif contains "$output" "LOOP_BLOCKED"; then
        echo "Loop blocked, awaiting input"
        wait_for_human_input
    elif contains "$output" "LOOP_ERROR"; then
        echo "Loop error: $output"
        exit 1
    fi
done
```

---

## Safety Limits

### Max Iterations

```yaml
max_iterations: 100

action_at_limit:
  - Output LOOP_BLOCKED
  - Reason: "Maximum iteration limit (100) reached"
  - Preserve state for resume
```

### Max Time

```yaml
max_duration_hours: 8

action_at_limit:
  - Output LOOP_BLOCKED
  - Reason: "Maximum duration (8 hours) reached"
  - Note issues in progress for resume
```

### Max Failures

```yaml
max_consecutive_failures: 3

action_at_limit:
  - Output LOOP_BLOCKED
  - Reason: "3 consecutive implementation failures"
  - Create meta-issue about repeated failures
```

---

## State Preservation

Before outputting any promise, ensure state is saved:

```yaml
preserved_state:
  - .work/agent/orchestrator-state.json (current phase, iteration)
  - .work/agent/focus.md (current issue)
  - .work/agent/issues/*.md (all issue states)
  - .work/agent/history.md (completed issues)
  - Git commit of any changes (atomic)
```

---

## Resume Protocol

When loop resumes after LOOP_BLOCKED:

```yaml
resume_steps:
  1. Load orchestrator-state.json
  2. Check if blocked issue is now unblocked
  3. If unblocked: start from validation phase
  4. If still blocked: select next issue
  5. Continue normal loop
```

---

## Promise Output Rules

1. **One promise per iteration:** Only one promise output per loop iteration
2. **End of output:** Promise appears at end of agent output
3. **Machine-readable:** Promise in XML tags for reliable parsing
4. **Context follows:** Human-readable context after promise
5. **Deterministic:** Same state always produces same promise

---

## See Also

**Related Subagents:** `loop-evaluator`

**Orchestrator:** `agent-orchestrator-v2`

**References:** [Ralph Wiggum technique](https://atcyrus.com/ralph-wiggum-technique/)
