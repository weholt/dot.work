---
name: issue-management
description: Skill for managing file-based issue tracking - housekeeping, moving, scanning
license: MIT
compatibility: Works with all AI coding assistants

environments:
  claude:
    target: ".claude/skills/"
    filename_suffix: "/issue-management/SKILL.md"
---

# Issue Management Skill

You have expertise in managing file-based issue tracking systems. This includes housekeeping, moving issues between files, scanning for status, and maintaining consistency.

---

## Core Capabilities

### 1. Scan Issues

Scan all issue files and categorize by status:

```yaml
files_to_scan:
  - .work/agent/issues/shortlist.md
  - .work/agent/issues/critical.md
  - .work/agent/issues/high.md
  - .work/agent/issues/medium.md
  - .work/agent/issues/low.md
  - .work/agent/issues/backlog.md

statuses:
  - proposed
  - in-progress
  - blocked
  - completed
  - won't-fix
```

**Output format:**
```
Issue Scan Results:
  shortlist.md:  2 proposed, 0 in-progress, 0 blocked, 1 completed
  critical.md:   1 proposed, 0 in-progress, 0 blocked, 0 completed
  high.md:       3 proposed, 1 in-progress, 1 blocked, 0 completed
  ...
  
Total: 12 proposed, 1 in-progress, 1 blocked, 1 completed
```

### 2. Move Completed Issues

Move issues with status `completed` to history.md:

```yaml
steps:
  1. Find all issues with status: completed
  2. For each completed issue:
     a. Extract full issue block (frontmatter + body)
     b. Add completion timestamp if missing
     c. Append to history.md
     d. Remove from source file
  3. Report: "Moved N issues to history.md"
```

**History entry format:**
```markdown
---
id: "BUG-003@a9f3c2"
title: "Fix config loading on Windows"
completed: 2026-01-05
...original frontmatter...
---

### Problem
...original content...

### Resolution
Completed on 2026-01-05. Used pathlib.Path for cross-platform paths.
```

### 3. Deduplicate Issues

Find and handle duplicate issues:

```yaml
duplicate_criteria:
  - Same title (case-insensitive)
  - Same affected files AND same problem description
  - Same ID prefix (e.g., two BUG-003)

actions:
  - Mark older duplicate as "won't-fix: duplicate of {newer_id}"
  - Keep the more detailed issue
  - Report duplicates found
```

### 4. Validate Issue Format

Check all issues have required fields:

```yaml
required_fields:
  frontmatter:
    - id (format: PREFIX-NUM@HASH)
    - title
    - created
    - type
    - priority
    - status
  body:
    - "### Problem" section
    - "### Acceptance Criteria" section

optional_but_recommended:
  - description
  - affected_files
  - tags
```

**Report invalid issues:**
```
Invalid Issues:
  - high.md: BUG-005@xyz123 - Missing acceptance criteria
  - medium.md: FEAT-002@abc456 - Invalid ID format (missing @hash)
```

### 5. Count Issues

Get counts for orchestrator decisions:

```python
def count_issues():
    return {
        "shortlist": {"proposed": N, "in_progress": N, "blocked": N},
        "critical": {"proposed": N, "in_progress": N, "blocked": N},
        "high": {"proposed": N, "in_progress": N, "blocked": N},
        "medium": {"proposed": N, "in_progress": N, "blocked": N},
        "low": {"proposed": N, "in_progress": N, "blocked": N},
        "total_proposed": N,
        "total_blocked": N
    }
```

---

## Issue Block Extraction

Extract a complete issue block from a file:

```markdown
---
id: "BUG-003@a9f3c2"
title: "Fix config loading on Windows"
...
status: completed
---

### Problem
Description here.

### Acceptance Criteria
- [ ] Criterion 1
```

**Extraction rules:**
1. Start at `---` (frontmatter start)
2. Include everything until next `---\n\n---` (next issue) or EOF
3. Preserve all formatting
4. Include blank lines between sections

---

## History File Management

### Append to History

Always append, never overwrite:

```yaml
steps:
  1. Read current history.md
  2. Append separator: "\n---\n\n"
  3. Append issue block
  4. Write file
```

### History Size Check

If history.md exceeds 150KB:

```yaml
steps:
  1. Rename history.md to history-{N}.md
  2. N = next available number (check existing history-*.md)
  3. Create fresh history.md with header
  4. Continue appending to new file
```

---

## Status Transitions

Valid status transitions:

```
proposed → in-progress → completed
proposed → in-progress → blocked → in-progress → completed
proposed → won't-fix
in-progress → blocked
blocked → in-progress
```

**Invalid transitions (flag as error):**
```
completed → anything (history is immutable)
won't-fix → anything (closed issues stay closed)
```

---

## Housekeeping Workflow

Complete housekeeping sequence:

```yaml
steps:
  1. Scan all issue files
  2. Move completed issues to history
  3. Check history.md size
  4. Validate remaining issue formats
  5. Report duplicates (don't auto-remove)
  6. Report statistics
```

**Housekeeping report:**
```
Housekeeping Complete:
  - Moved 3 issues to history.md
  - History size: 45KB (OK)
  - Issues validated: 12
  - Issues with errors: 1 (see above)
  - Potential duplicates: 0
  
Current state:
  - Proposed: 8
  - In-progress: 1
  - Blocked: 1
```

---

## Priority File Rules

| File | Priority | When to Use |
|------|----------|-------------|
| shortlist.md | USER | Explicit user intent only |
| critical.md | P0 | Security, data loss, blockers |
| high.md | P1 | Core functionality broken |
| medium.md | P2 | Important improvements |
| low.md | P3 | Nice-to-have, cosmetic |
| backlog.md | – | Untriaged, future ideas |

**Shortlist special rules:**
- Agent may NOT add to shortlist autonomously
- Agent may NOT remove from shortlist autonomously
- User must explicitly modify shortlist

---

## Error Handling

### Malformed YAML Frontmatter

```yaml
action:
  - Log error with file and line
  - Skip this issue (don't crash)
  - Report in validation output
  - Create issue for malformed issue
```

### Missing Issue File

```yaml
action:
  - Create file with header
  - Log: "Created missing file: {filename}"
  - Continue processing
```

### History Write Failure

```yaml
action:
  - DO NOT remove from source file
  - Log error
  - Report failure
  - Issue stays in source until successful move
```

---

## Usage in Pre-Iteration

The pre-iteration subagent uses this skill for:

```yaml
pre_iteration_tasks:
  1. count_issues()  # For orchestrator state
  2. move_completed_to_history()  # Housekeeping
  3. get_next_issue()  # Via focus-selector skill
```

---

## See Also

**Related Skills:** `focus-selector`, `issue-creation`

**Used By:** `pre-iteration` subagent

