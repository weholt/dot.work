---
name: pre-loop
description: Initialization hook run before autonomous loop starts
compatibility: All harnesses that support initialization hooks
environments:
  claude:
    target: ".claude/hooks/"
    filename: "pre-loop.md"
  opencode:
    target: ".opencode/hooks/"
    filename: "pre-loop.md"
  copilot:
    target: ".github/prompts/hooks/"
    filename: "pre-loop.md"
---

# Pre-Loop Hook

This hook runs once before the autonomous loop begins. It ensures the workspace is properly initialized for autonomous operation.

---

## Pre-Loop Checklist

### Required Files Check

```yaml
required_files:
  - path: .work/constitution.md
    action_if_missing: "Run create-constitution to generate"
    
  - path: .work/baseline.md
    action_if_missing: "Run establish-baseline to capture"
    
  - path: .work/agent/focus.md
    action_if_missing: "Create empty focus file"
    
  - path: .work/agent/issues/shortlist.md
    action_if_missing: "Initialize issue tracker"
```

### Issue Queue Check

```yaml
issue_check:
  - Verify at least one issue exists
  - If no issues: prompt user or abort
  - Count issues by priority for reporting
```

### Baseline Freshness

```yaml
baseline_check:
  - Compare baseline timestamp to last code change
  - If stale (>24 hours or code changed): warn
  - Recommend: re-run establish-baseline
```

---

## Initialization Steps

### Step 1: Verify Workspace Structure

```bash
# Ensure required directories exist
mkdir -p .work/agent/issues
mkdir -p .work/agent/notes
mkdir -p .work/agent/references
```

### Step 2: Load Constitution

```yaml
constitution:
  - Read .work/constitution.md
  - Extract: build_command, test_command, style_rules
  - Store in session context
  
  failure: "Cannot start loop without constitution"
```

### Step 3: Verify Baseline

```yaml
baseline:
  - Read .work/baseline.md
  - Parse test counts, coverage, lint status
  - Store as reference for validation
  
  failure: "Cannot start loop without baseline"
```

### Step 4: Initialize State

```yaml
state_initialization:
  file: .work/agent/orchestrator-state.json
  
  initial_state:
    session_id: "sess-{date}-{random}"
    started_at: "{timestamp}"
    phase: "pre-iteration"
    iteration: 0
    issues_completed: 0
    issues_blocked: 0
```

### Step 5: Clear Stale Context

```yaml
cleanup:
  - Remove old prepared-context.json
  - Remove old implementation-report.json
  - Remove old validation-*.json
  - Preserve: focus.md, issues/*.md, history.md
```

---

## Pre-Loop Report

Output initialization status:

```
Pre-Loop Initialization Complete
================================
Session: sess-2026-01-05-001
Constitution: ✓ loaded
Baseline: ✓ loaded (captured 2 hours ago)

Issue Queue:
  - Shortlist: 1
  - Critical: 0
  - High: 3
  - Medium: 5
  - Low: 2
  - Total: 11 issues pending

Ready to begin autonomous loop.
```

---

## Failure Handling

### Missing Constitution

```yaml
error: constitution_missing
message: |
  Constitution not found at .work/constitution.md
  
  Run create-constitution to generate project-specific rules:
  - Build commands
  - Test commands  
  - Style guidelines
  - Platform-specific settings

action: Abort loop, exit with error
```

### Missing Baseline

```yaml
error: baseline_missing
message: |
  Baseline not found at .work/baseline.md
  
  Run establish-baseline to capture current state:
  - Test counts
  - Coverage percentage
  - Lint status
  - Type check status

action: Abort loop, exit with error
```

### No Issues

```yaml
warning: no_issues
message: |
  No issues found in queue.
  
  Add issues to:
  - .work/agent/issues/shortlist.md (explicit user intent)
  - .work/agent/issues/high.md (important work)
  - etc.

action: Abort loop (nothing to do)
```

---

## Integration

### With Agent Orchestrator

```yaml
orchestrator_flow:
  1. Orchestrator invokes pre-loop
  2. Pre-loop validates and initializes
  3. If success: return to orchestrator for first iteration
  4. If failure: abort with error message
```

### With Harness

```yaml
harness_integration:
  - Harness calls agent with pre-loop command
  - Agent outputs initialization status
  - Harness parses for success/failure
  - On success: begin main loop
  - On failure: exit with error
```

---

## See Also

**Related Hooks:** `stop-hooks`, `post-iteration`

**Orchestrator:** `agent-orchestrator-v2`
