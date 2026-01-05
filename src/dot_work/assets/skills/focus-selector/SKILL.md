---
name: focus-selector
description: Skill for selecting the next issue to work on based on priority, blocked status, and session context
license: MIT
compatibility: Works with all AI coding assistants

environments:
  claude:
    target: ".claude/skills/"
    filename_suffix: "/focus-selector/SKILL.md"
---

# Focus Selector Skill

You have expertise in selecting the optimal next issue to focus on. This skill implements priority ordering, blocked issue detection, and session-aware selection.

---

## Selection Algorithm

### Priority Order (Strict)

```yaml
priority_order:
  1. shortlist.md (proposed or in-progress)
  2. critical.md (proposed, then in-progress)
  3. high.md (proposed, then in-progress)  
  4. medium.md (proposed, then in-progress)
  5. low.md (proposed, then in-progress)
  6. backlog.md (only if all above empty)
```

**Rule:** Always complete shortlist issues before moving to any other priority level.

### Issue Status Priority

Within each file:

```yaml
status_priority:
  1. in-progress (resume existing work first)
  2. proposed (start new work)
  # Never select: blocked, completed, won't-fix
```

### Blocked Issue Handling

If an issue is `blocked`:

```yaml
blocked_handling:
  - Skip during selection
  - Log: "Skipping blocked issue: {id}"
  - Include in blocked_count for orchestrator
  - Move to next candidate
```

---

## Selection Process

### Step 1: Load Issues

```yaml
load_order:
  - shortlist.md
  - critical.md
  - high.md
  - medium.md
  - low.md
  - backlog.md

per_file:
  - Parse all issues
  - Extract: id, title, status, type, affected_files, tags
  - Filter: status in [proposed, in-progress]
```

### Step 2: Apply Filters

```yaml
exclusions:
  - status: blocked
  - status: completed
  - status: won't-fix
  - In session's completed_issues list (avoid re-selection)
```

### Step 3: Sort Candidates

```yaml
sort_criteria:
  1. File priority (shortlist > critical > high > ...)
  2. Status (in-progress > proposed)
  3. Creation date (older first, for fairness)
```

### Step 4: Return Selection

```yaml
output:
  selected_issue:
    id: "BUG-003@a9f3c2"
    title: "Fix config loading on Windows"
    type: bug
    priority: high
    affected_files:
      - src/config/loader.py
      - src/config/parser.py
    file_location: .work/agent/issues/high.md
    
  candidates_remaining: 5
  blocked_count: 1
  
  selection_reason: |
    Selected highest priority non-blocked issue.
    In-progress issue from previous session.
```

---

## Special Cases

### Empty Queue

When no selectable issues exist:

```yaml
empty_queue:
  selected_issue: null
  candidates_remaining: 0
  blocked_count: N  # May still have blocked issues
  
  selection_reason: |
    No proposed or in-progress issues found.
    {N} issues are currently blocked.
    Work queue is empty - loop may complete.
```

### All Issues Blocked

When only blocked issues remain:

```yaml
all_blocked:
  selected_issue: null
  candidates_remaining: 0
  blocked_count: N
  
  selection_reason: |
    All {N} remaining issues are blocked.
    No actionable work available.
    Human intervention may be required to unblock.
```

### Session Fatigue Detection

If same issue selected 3+ consecutive times:

```yaml
fatigue_detection:
  - Check session's iteration history
  - If issue appeared 3+ consecutive times without completion
  - Mark as: potential_stuck = true
  - Add to selection output: "Issue may be stuck - consider blocking"
```

---

## Focus File Update

After selection, update `.work/agent/focus.md`:

```markdown
# Current Focus

## Active Issue

**ID:** BUG-003@a9f3c2
**Title:** Fix config loading on Windows
**Type:** bug
**Priority:** high
**File:** .work/agent/issues/high.md

## Context
- Affected files: src/config/loader.py, src/config/parser.py
- Tags: cross-platform, windows
- Created: 2026-01-03
- Started: 2026-01-05

## Acceptance Criteria
- [ ] Config loads correctly on Windows paths
- [ ] Uses pathlib.Path consistently
- [ ] Tests pass on Windows CI

---

*Last updated: 2026-01-05T10:30:00Z by pre-iteration subagent*
```

---

## Prepared Context Generation

The focus-selector also generates minimal context for the implementer:

```yaml
prepared_context:
  issue:
    full_content: |
      <complete issue markdown>
  
  relevant_files:
    - path: src/config/loader.py
      summary: "Config loading logic, 120 lines"
      read_required: true
    - path: tests/test_config.py
      summary: "Config tests, 80 lines"
      read_required: true
  
  constitution_excerpt:
    build_command: "uv run python scripts/build.py"
    test_command: "./scripts/pytest-with-cgroup.sh 30"
    style_rules:
      - "Use pathlib.Path for all file operations"
      - "Type hints on all functions"
  
  recent_history:
    - "Iteration 3: Fixed BUG-001 (COMPLETE)"
    - "Iteration 4: Attempted BUG-002 (BLOCKED - external dep)"
```

**Output file:** `.work/agent/prepared-context.json`

---

## Integration with Pre-Iteration

The pre-iteration subagent calls focus-selector:

```yaml
pre_iteration_workflow:
  1. Call issue-management skill for counts
  2. Call focus-selector for next issue
  3. If no issue selected:
     - If blocked_count > 0: report BLOCKED
     - If blocked_count = 0: report DONE
  4. If issue selected:
     - Write focus.md
     - Write prepared-context.json
     - Report ready for implementation
```

---

## Backlog Promotion

If higher priority files are empty:

```yaml
backlog_promotion:
  trigger: shortlist + critical + high + medium + low all empty
  
  action:
    - Select oldest proposed issue from backlog
    - Note in selection_reason: "Promoted from backlog (all priority queues empty)"
    - Do NOT move issue between files (just select it)
```

---

## Session Context Awareness

Selection considers session state:

```yaml
session_awareness:
  completed_this_session:
    - BUG-001@xyz123
    - FEAT-005@abc789
    
  avoid_patterns:
    - Recently completed issues (no re-selection)
    - Issues that failed 2+ times this session
    
  prefer_patterns:
    - Issues related to recently completed work (momentum)
    - Issues in same module/directory as last success
```

---

## Selection Logging

Log selection decisions for auditability:

```
[focus-selector] Scanning issue files...
[focus-selector] shortlist.md: 0 selectable, 0 blocked
[focus-selector] critical.md: 0 selectable, 0 blocked
[focus-selector] high.md: 2 selectable, 1 blocked
[focus-selector] Selected: BUG-003@a9f3c2 from high.md
[focus-selector] Reason: Highest priority non-blocked issue (in-progress)
[focus-selector] Wrote focus.md
[focus-selector] Wrote prepared-context.json (3.2KB)
```

---

## Error Handling

### Malformed Issue

```yaml
action:
  - Skip issue
  - Log: "Skipping malformed issue in {file}: {error}"
  - Continue with next candidate
  - Don't crash selection process
```

### No Issues Parse

```yaml
action:
  - Report empty queue
  - Include error count in output
  - Let orchestrator decide next action
```

---

## See Also

**Related Skills:** `issue-management`

**Used By:** `pre-iteration`, `loop-evaluator` subagents

