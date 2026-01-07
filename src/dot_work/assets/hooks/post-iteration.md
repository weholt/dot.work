---
name: post-iteration
description: Hook run after each iteration to maintain state and log progress
compatibility: All harnesses that support post-iteration hooks
environments:
  claude:
    target: ".claude/hooks/"
    filename: "post-iteration.md"
  opencode:
    target: ".opencode/hooks/"
    filename: "post-iteration.md"
  copilot:
    target: ".github/prompts/hooks/"
    filename: "post-iteration.md"
---

# Post-Iteration Hook

This hook runs after each loop iteration completes, handling state persistence, logging, and preparation for the next iteration.

---

## Post-Iteration Tasks

### 1. Persist State

```yaml
state_update:
  file: .work/agent/orchestrator-state.json
  
  updates:
    - iteration: increment by 1
    - last_completed_at: current timestamp
    - current_issue: null (between iterations)
    - last_issue: completed issue ID
    - phase: "complete" | "blocked" | "error"
```

### 2. Update Issue Status

```yaml
issue_update:
  on_success:
    - Mark issue as completed
    - Add completion timestamp
    - Move to history.md (via issue-management skill)
    
  on_blocked:
    - Mark issue as blocked
    - Add blocked_reason
    - Leave in current priority file
    
  on_error:
    - Keep issue as in-progress
    - Add error note
    - Log error details
```

### 3. Commit Changes

```yaml
git_commit:
  condition: "Changes exist and tests pass"
  
  actions:
    - Stage changed files (code + tests)
    - Commit with conventional message
    - Include issue ID in commit footer
    
  skip_if:
    - No code changes (documentation only)
    - Tests failing
    - Validation failed
```

### 4. Log Progress

```yaml
progress_log:
  file: .work/agent/session-log.md
  
  entry:
    iteration: 5
    timestamp: 2026-01-05T10:50:00Z
    issue: BUG-003@a9f3c2
    result: completed
    duration_minutes: 8
    commits: ["a1b2c3d: fix(config): use pathlib for cross-platform paths"]
    validation: pass
```

### 5. Cleanup Temporary Files

```yaml
cleanup:
  remove:
    - .work/agent/prepared-context.json
    - .work/agent/implementation-report.json
    
  preserve:
    - .work/agent/validation-*.json (for evaluator)
    - .work/agent/orchestrator-state.json
    - .work/agent/focus.md (clear content, keep file)
```

---

## Session Metrics

Track metrics across iterations:

```yaml
session_metrics:
  iterations_completed: 5
  issues_completed: 3
  issues_blocked: 1
  issues_created: 2  # By validation subagents
  
  time_metrics:
    total_minutes: 45
    avg_iteration_minutes: 9
    
  code_metrics:
    files_changed: 12
    lines_added: 150
    lines_removed: 45
    commits: 8
    
  validation_metrics:
    tests_added: 5
    coverage_delta: +1.2%
```

---

## Iteration Summary

Output iteration summary for logging:

```
Iteration 5 Complete
====================
Issue: BUG-003@a9f3c2 (Fix config loading on Windows)
Result: COMPLETED

Changes:
  - src/config/loader.py (+25, -10)
  - tests/test_config.py (+40, -5)

Commits:
  - a1b2c3d: test(config): add Windows path handling test
  - e4f5g6h: fix(config): use pathlib for cross-platform paths

Validation:
  - Code review: pass
  - Security audit: pass
  - Spec compliance: pass

Duration: 8 minutes
```

---

## Health Checks

### Memory Check

```yaml
memory_check:
  - Log context window usage estimate
  - If near limit: flag for potential issues
  - Next iteration starts fresh regardless
```

### State Consistency

```yaml
consistency_check:
  - Verify focus.md matches state.json
  - Verify issue status matches filesystem
  - If inconsistent: log warning, attempt repair
```

### Git Status

```yaml
git_check:
  - Verify working tree clean after commit
  - Check for uncommitted changes
  - If dirty: log warning
```

---

## Handoff Preparation

Prepare for next iteration:

```yaml
handoff:
  clear:
    - focus.md content (keep file)
    - prepared-context.json
    - implementation-report.json
    
  preserve:
    - orchestrator-state.json
    - validation-*.json (for evaluator)
    - All issue files
    
  ready_for:
    - Loop evaluator to check state
    - Pre-iteration subagent to select next issue
```

---

## Error Recovery

### Commit Failure

```yaml
error: commit_failed
actions:
  - Log git error
  - Keep changes staged
  - Mark iteration as incomplete
  - Let next iteration retry
```

### State Write Failure

```yaml
error: state_write_failed
actions:
  - Retry once
  - If still fails: log critical error
  - Output LOOP_ERROR promise
```

### Issue Move Failure

```yaml
error: history_move_failed
actions:
  - Keep issue in original file
  - Mark as completed (status field)
  - Log warning
  - Housekeeping will retry later
```

---

## Integration Points

### With Orchestrator

```yaml
orchestrator_calls:
  - Post-iteration runs automatically after validation
  - Orchestrator checks post-iteration success
  - Then invokes loop-evaluator
```

### With Loop Evaluator

```yaml
evaluator_inputs:
  - Post-iteration produces clean state
  - Evaluator reads updated state
  - Decides CONTINUE/DONE/BLOCKED
```

---

## See Also

**Related Hooks:** `pre-loop`, `stop-hooks`

**Related Subagents:** `loop-evaluator`

**Skills:** `git-workflow`, `issue-management`
