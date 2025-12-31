---
id: "SDA-003@e3f4g5"
title: "Document issue tracking system comparison and migration"
description: "Two issue tracking systems exist - comparison and migration path undocumented"
created: 2025-12-31
section: "documentation"
tags: [documentation, db-issues, migration, comparison, spec-delivery-audit]
type: docs
priority: medium
status: proposed
references:
  - .work/agent/issues/references/SDA-001-spec-delivery-audit-report.md
  - src/dot_work/db_issues/
  - .work/agent/issues/
---

### Problem
Two issue tracking systems (file-based and db-issues) with different interfaces. Comparison and migration between them is undocumented.

**Undocumented:**
- How do the two systems compare?
- Can both systems coexist?
- Which one should I use?
- Is there a migration path?

### Affected Files
- Documentation files (README.md, docs/)
- Both issue tracking implementations

### Systems Comparison

**File-based (.work/agent/issues/)**
- Storage: Markdown files
- Best for: AI-driven workflows, git-tracked issues
- Features: Human-readable, git history, AI-native format
- CLI: Direct file editing (no dedicated CLI)

**db-issues (.work/db-issues/issues.db)**
- Storage: SQLite database
- Best for: Complex queries, relational data, large projects
- Features: Full-text search, relationships, epics, dependencies
- CLI: Comprehensive command set (create, list, search, etc.)

### Importance
**MEDIUM**: Users need guidance on choosing and migrating between systems:
- Unclear which system to use for new projects
- No documented migration path
- Risk of data loss during migration

### Proposed Solution
Add documentation section to tooling-reference.md:
```markdown
## Issue Tracking Options

dot-work provides two issue tracking systems:

### File-based Issues (.work/agent/issues/)

**Use for:** AI-driven workflows, git-tracked issues

**Best for:**
- Individual developers
- AI-heavy workflows
- Projects wanting git history for issues
- Simple issue tracking

**Commands:**
- Edit files directly in `.work/agent/issues/`
- Use AI agents to create/update issues
- Issues tracked in git

### Database Issues (db-issues)

**Use for:** Complex queries, relational data

**Best for:**
- Teams with complex workflows
- Projects with many issues (1000+)
- Need for full-text search
- Complex dependencies and epics

**Commands:**
```bash
dot-work db-issues create "Fix bug"
dot-work db-issues list --status open
dot-work db-issues search "authentication"
dot-work db-issues ready
```

### Which to Choose?

| Factor | File-based | db-issues |
|--------|-----------|-----------|
| Team size | Individual | Small team |
| Issue count | < 100 | 100+ |
| AI workflow | Native | Possible |
| Complex queries | No | Yes (FTS) |
| Git history | Yes | No |

### Coexistence

Both systems can coexist in the same project. However:
- They do not share data
- Choose one as primary
- Mixing may cause confusion

### Migration

**File-based → db-issues:** Not currently supported

**db-issues → File-based:** Export via JSONL:
```bash
dot-work db-issues export > issues.jsonl
# Then manually import to file-based
```
```

### Acceptance Criteria
- [ ] Both systems documented with use cases
- [ ] Comparison table provided
- [ ] Guidance on which to use
- [ ] Warning about coexistence risks
- [ ] Migration path documented (if supported)

### Notes
Found during spec delivery audit SDA-001. Both systems work correctly but users need guidance on choosing.
