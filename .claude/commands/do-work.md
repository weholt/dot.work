---
meta:
  title: "Autonomous Agent Workflow"
  description: "Lean orchestration flow that delegates to subagents for context-optimized execution"
  version: "2.0.0"

environments:
  claude:
    target: ".claude/commands/"
    prefix: "do-work"
    
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"
---

# Autonomous Agent Workflow

This prompt defines the lean orchestration pattern for autonomous agents. It delegates work to specialized subagents to optimize context window usage per phase.

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────┐
│                  AUTONOMOUS LOOP                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   ┌──────────────┐                                      │
│   │  PRE-LOOP    │  ← Verify prerequisites              │
│   │    HOOK      │    (constitution, baseline)          │
│   └──────┬───────┘                                      │
│          │                                               │
│          ▼                                               │
│   ┌──────────────┐                                      │
│   │ PRE-ITERATION│  ← Select issue, prepare context     │
│   │   SUBAGENT   │    (lightweight, ~3K tokens)         │
│   └──────┬───────┘                                      │
│          │                                               │
│          ▼                                               │
│   ┌──────────────┐                                      │
│   │ IMPLEMENTER  │  ← Focused implementation            │
│   │   SUBAGENT   │    (single issue, ~8K tokens)        │
│   └──────┬───────┘                                      │
│          │                                               │
│          ▼                                               │
│   ┌──────────────────────────────────────┐              │
│   │         VALIDATION SUBAGENTS         │              │
│   │  ┌────────┐ ┌────────┐ ┌────────┐   │              │
│   │  │ Code   │ │Security│ │ Spec   │   │  ← Parallel  │
│   │  │ Review │ │ Audit  │ │ Audit  │   │    (~4K each)│
│   │  └────────┘ └────────┘ └────────┘   │              │
│   └──────────────────┬───────────────────┘              │
│                      │                                   │
│                      ▼                                   │
│   ┌──────────────┐                                      │
│   │POST-ITERATION│  ← Commit, cleanup, update state     │
│   │    HOOK      │                                      │
│   └──────┬───────┘                                      │
│          │                                               │
│          ▼                                               │
│   ┌──────────────┐     ┌─────────────┐                  │
│   │    LOOP      │────▶│  CONTINUE   │──▶ Next iter     │
│   │  EVALUATOR   │     ├─────────────┤                  │
│   │   SUBAGENT   │────▶│    DONE     │──▶ Exit success  │
│   │              │     ├─────────────┤                  │
│   │              │────▶│   BLOCKED   │──▶ Pause/exit    │
│   └──────────────┘     └─────────────┘                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Core Principles

1. **Delegate, don't accumulate** - Subagents do the work, orchestrator coordinates
2. **Fresh context per phase** - Each subagent starts with minimal, relevant context
3. **State via files** - Persist state to JSON, not conversation memory
4. **Parallel validation** - Run reviews concurrently to save time
5. **Explicit stop hooks** - Clear signals for loop control

---

## Phase 1: Pre-Loop (One Time)

**Hook:** `pre-loop`

```yaml
prerequisites:
  - .work/constitution.md exists (run create-constitution if not)
  - .work/baseline.md exists (run establish-baseline if not)
  - .work/agent/issues/ has at least one issue
  
actions:
  - Initialize orchestrator-state.json
  - Clear stale context files
  - Report ready status
```

---

## Phase 2: Pre-Iteration

**Subagent:** `pre-iteration`

```yaml
context_budget: ~3K tokens

inputs:
  - .work/agent/issues/*.md (scan only)
  - .work/constitution.md (commands section only)
  
skills:
  - issue-management
  - focus-selector

outputs:
  - .work/agent/focus.md (updated)
  - .work/agent/prepared-context.json
  
decision:
  - Issue selected → Continue to implementation
  - No issues → Signal DONE
  - All blocked → Signal BLOCKED
```

---

## Phase 3: Implementation

**Subagent:** `implementer`

```yaml
context_budget: ~8K tokens

inputs:
  - .work/agent/prepared-context.json (from pre-iteration)
  - Source files relevant to issue
  - Test files relevant to issue
  
skills:
  - git-workflow
  - baseline-validation (quick mode)
  - (issue-type specific skills)

outputs:
  - Code changes (atomic commits)
  - .work/agent/implementation-report.json
  
success_criteria:
  - Changes compile/build
  - Tests pass
  - Quick validation passes
```

---

## Phase 4: Validation (Parallel)

**Subagents:** Run concurrently

| Subagent | Context | Output |
|----------|---------|--------|
| `code-reviewer` | ~4K | validation-code-review.json |
| `security-auditor` | ~4K | validation-security.json |
| `spec-auditor` | ~4K | validation-spec.json |
| `performance-reviewer` | ~4K | validation-performance.json |

```yaml
inputs_each:
  - .work/agent/implementation-report.json
  - Changed files only
  - Issue acceptance criteria

skills_each:
  - issue-creation

outputs_each:
  - validation-{type}.json
  - New issues created for findings
```

---

## Phase 5: Post-Iteration

**Hook:** `post-iteration`

```yaml
actions:
  - Update issue status (completed/blocked)
  - Move completed issues to history.md
  - Commit changes with conventional message
  - Update orchestrator-state.json
  - Clear temporary files
```

---

## Phase 6: Loop Evaluation

**Subagent:** `loop-evaluator`

```yaml
context_budget: ~2K tokens

inputs:
  - .work/agent/orchestrator-state.json
  - .work/agent/validation-*.json
  - Issue counts (from pre-iteration)

decision_tree:
  all_validation_pass AND more_issues:
    output: <promise>LOOP_CONTINUE</promise>
    
  all_validation_pass AND no_more_issues:
    output: <promise>LOOP_DONE</promise>
    
  validation_fail_blocking:
    output: <promise>LOOP_BLOCKED</promise>
    
  max_iterations_reached:
    output: <promise>LOOP_BLOCKED</promise>
```

---

## State Files

### orchestrator-state.json

```json
{
  "session_id": "sess-2026-01-05-001",
  "started_at": "2026-01-05T10:00:00Z",
  "iteration": 5,
  "phase": "validation",
  "current_issue": "BUG-003@a9f3c2",
  "issues_completed": 3,
  "issues_blocked": 1,
  "issues_created": 2
}
```

### prepared-context.json

```json
{
  "issue": {
    "id": "BUG-003@a9f3c2",
    "title": "Fix config loading on Windows",
    "type": "bug",
    "acceptance_criteria": ["..."]
  },
  "relevant_files": ["src/config/loader.py", "tests/test_config.py"],
  "constitution_excerpt": {
    "test_command": "uv run pytest",
    "build_command": "uv run python scripts/build.py"
  }
}
```

---

## Immutable Rules

Load `agent-rules` before any phase.

Summary:
- NO destructive commands without confirmation
- NO skipping tests
- NO regressing baseline
- NO modifying shortlist.md autonomously
- NO deleting code without tests

---

## Commands Reference

| Command | Action |
|---------|--------|
| `continue` | Resume/start loop iteration |
| `status` | Show current focus and issue counts |
| `focus on <topic>` | Create prioritized issues for topic |
| `generate-baseline` | Capture current quality metrics |
| `housekeeping` | Clean up issues, move completed |

---

## Error Handling

```yaml
subagent_failure:
  - Log error to orchestrator-state.json
  - Attempt recovery via issue-creation skill
  - Mark issue as blocked if unrecoverable
  
max_retries: 3

fatal_errors:
  - Baseline regression (exit immediately)
  - No issues + no work done (exit DONE)
```

---

## Completion Signals

The loop evaluator outputs these promises:

| Promise | Meaning |
|---------|---------|
| `<promise>LOOP_DONE</promise>` | All work complete |
| `<promise>LOOP_CONTINUE</promise>` | More work remains |
| `<promise>LOOP_BLOCKED</promise>` | Needs human intervention |
| `<promise>LOOP_ERROR</promise>` | Unrecoverable error |

---

## Asset Summary

**Prompts (installed to commands directory):**
- `agent-orchestrator-v2` - Main orchestrator
- `agent-rules` - Immutable constraints
- `do-work` - This workflow overview
- `create-constitution` - Project setup
- `establish-baseline` - Quality baseline

**Subagents (installed to agents directory):**
- `pre-iteration` - Issue selection (~3K context)
- `implementer` - Implementation (~8K context)
- `loop-evaluator` - Loop control (~2K context)
- `code-reviewer` - Code review (~4K context)
- `security-auditor` - Security audit (~4K context)
- `spec-auditor` - Spec compliance (~4K context)
- `performance-reviewer` - Performance (~4K context)

**Skills (installed to skills directory):**
- `issue-management` - Issue file operations
- `focus-selector` - Issue selection algorithm
- `baseline-validation` - Baseline comparison
- `git-workflow` - Atomic commits
- `issue-creation` - Create issues from findings

**Hooks:**
- `pre-loop` - Initialization
- `post-iteration` - Cleanup
- `stop-hooks` - Completion promises
