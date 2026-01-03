# Issue Tracking System

This directory contains a file-based issue tracking system for AI-driven development.

## Editing Issues

**IMPORTANT:** Issues are managed by AI agents via prompts. **Direct manual editing of issue files is NOT recommended.**

### AI-Only Workflow

Issues should be created, updated, and moved exclusively through AI agent prompts:

- **`/new-issue`** – Create a new issue with auto-generated ID
- **`/do-work`** – Move issues through workflow states (proposed → in-progress → completed)
- **`/focus on <topic>`** – Create prioritized issues in shortlist.md

### Why AI-Only?

The issue tracking format has specific requirements:
- Consistent YAML frontmatter structure
- Proper ID generation and referencing
- Correct status transitions
- Attachment tracking (completed → history.md)

Manual editing can introduce:
- Malformed YAML that breaks parsing
- Incorrect status transitions
- Missing or invalid issue IDs
- Inconsistent formatting

### Issue File Locations

| Priority Level | File | Purpose |
|---------------|------|---------|
| Shortlist | `shortlist.md` | Current sprint/iteration issues |
| Critical | `critical.md` | Blocking issues requiring immediate attention |
| High | `high.md` | Important issues for next iteration |
| Medium | `medium*.md` | Standard enhancements and technical debt |
| Low | `low.md` | Nice-to-have improvements |
| Backlog | `backlog*.md` | Future work not yet scheduled |
| History | `history.md` | Completed issues (append-only) |

### Issue Status Values

- **`proposed`** – Issue identified, not yet started
- **`in-progress`** – Currently being worked on
- **`completed`** – Finished and validated (should be moved to history.md)

### Issue Lifecycle

1. **Creation** – Issue created via `/new-issue` or `/focus on` with auto-generated ID
2. **Selection** – Issue moved to appropriate priority file (critical/high/medium/low)
3. **In Progress** – Issue marked `in-progress` when work begins
4. **Completion** – Issue marked `completed` when acceptance criteria met
5. **Archival** – Completed issue moved to `history.md` (append-only, never modified)

### For Human Review Only

Humans should **READ** these files to:
- Track progress on current work
- Review issue history
- Understand what's being worked on

Humans should **NOT** directly edit these files. Use the AI prompts instead.

---

**See also:** [`.work/agent/focus.md`](../focus.md) for current active work.
