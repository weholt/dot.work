# 📋 Issue Tracker Setup Guide

This document defines **how to initialize** the file-based issue tracking system. For detailed workflow documentation, see [do-work.prompt.md](.github/prompts/do-work.prompt.md).

---

## 🎯 Core Principles

1. **Baseline is the quality floor** – nothing may regress
2. **One active issue at a time**
3. **Shortlist has highest priority** – user intent overrides all
4. **All regressions block completion**
5. **Issues are the only unit of work**
6. **History is immutable**
7. **Every issue must be uniquely identifiable**

---

## 📁 Directory Structure

When `init work` is triggered, create this structure:

```
.work/
├── baseline.md               # Quality metrics snapshot (generated separately)
└── agent/
    ├── focus.md              # Current execution state (Previous/Current/Next)
    ├── memory.md             # Persistent cross-session knowledge
    ├── notes/                # Scratchpad, research, working notes
    │   └── .gitkeep
    └── issues/
        ├── critical.md       # P0 – blockers, security, data loss
        ├── high.md           # P1 – broken core functionality
        ├── medium.md         # P2 – enhancements, tech debt
        ├── low.md            # P3 – minor improvements
        ├── backlog.md        # Untriaged ideas
        ├── shortlist.md      # USER-DIRECTED priorities (highest priority)
        ├── history.md        # Completed / closed issues (append-only)
        └── references/       # Specs, logs, large docs, research
            └── .gitkeep
```

### Structural Rules

- Issues exist **only** in `.work/agent/issues/`
- `history.md` is **append-only**
- `shortlist.md` is **read-only for agents** unless user explicitly instructs changes
- `.work/` is the single source of operational truth

---

## 📄 Initial File Contents

### `.work/agent/focus.md`

```markdown
# Agent Focus
Last updated: <timestamp>

## Previous
None

## Current
None

## Next
None
```

### `.work/agent/memory.md`

```markdown
# Agent Memory

## Project Context
- Primary language: <detected>
- Framework: <detected>
- Package manager: <detected>
- Test framework: <detected>

## User Preferences
(To be populated as preferences are discovered)

## Architectural Decisions
(To be populated as decisions are made)

## Patterns & Conventions
(To be populated as patterns are identified)

## Known Constraints
(To be populated as constraints are discovered)

## Lessons Learned
(To be populated after completing issues)
```

### `.work/agent/issues/shortlist.md`

```markdown
# Shortlist (User-Directed Priority)

This file represents **explicit user intent**. Agent may only modify when explicitly instructed.

---

(No issues yet)
```

### `.work/agent/issues/critical.md`

```markdown
# Critical Issues (P0)

Blockers, security issues, data loss risks.

---

(No issues)
```

### `.work/agent/issues/high.md`

```markdown
# High Priority Issues (P1)

Core functionality broken.

---

(No issues)
```

### `.work/agent/issues/medium.md`

```markdown
# Medium Priority Issues (P2)

Enhancements, technical debt.

---

(No issues)
```

### `.work/agent/issues/low.md`

```markdown
# Low Priority Issues (P3)

Cosmetic, incremental improvements.

---

(No issues)
```

### `.work/agent/issues/backlog.md`

```markdown
# Backlog

Untriaged ideas and future work.

---

(No issues)
```

### `.work/agent/issues/history.md`

```markdown
# Issue History (Append-Only)

Completed and closed issues are archived here.

---

(No completed issues yet)
```

---

## 🆔 Issue Identity Format

Every issue **MUST** have a canonical identifier:

```
<PREFIX>-<NUMBER>@<HASH>
```

**Example:** `BUG-003@a9f3c2`

### Rules

- `<PREFIX>-<NUMBER>`: Human-readable, sequential within prefix
- `<HASH>`: Exactly 6 lowercase hex characters, generated once, immutable

### Issue ID Prefixes

| Prefix   | Meaning                     |
|----------|----------------------------|
| BUG      | Defect                      |
| FEAT     | New feature                 |
| ENHANCE  | Improve existing behavior   |
| REFACTOR | Structural/code improvement |
| DOCS     | Documentation               |
| TEST     | Testing                     |
| SEC      | Security                    |
| PERF     | Performance                 |
| DEBT     | Technical debt              |
| STRUCT   | Architectural issue         |

---

## 📝 Issue Schema

All issues **MUST** use this template:

```markdown
---
id: "<PREFIX>-<NUMBER>@<HASH>"
title: "Concise, specific title"
description: "One-sentence summary"
created: YYYY-MM-DD
section: "<area of codebase>"
tags: [tag1, tag2]
type: bug | enhancement | refactor | docs | test | security | performance
priority: critical | high | medium | low
status: proposed | in-progress | blocked | completed | won't-fix
references:
  - path/to/file.py
---

### Problem
Clear description of the problem or missing behavior.

### Affected Files
- `src/example.py`
- `tests/test_example.py`

### Error / Exception Details (if applicable)
- Exception type
- Error code
- Stack trace excerpt

### Importance
Severity, value, dependencies, and user impact.

### Proposed Solution
High-level approach.

### Acceptance Criteria
- [ ] Objective, testable condition
- [ ] Objective, testable condition

### Notes
Progress updates, findings, decisions.
```

---

## 📊 Priority Files

| File         | Priority | Meaning                              |
|--------------|----------|--------------------------------------|
| shortlist.md | **USER** | **Explicit user focus (HIGHEST)**    |
| critical.md  | P0       | Blocks progress, security, data loss |
| high.md      | P1       | Core functionality broken            |
| medium.md    | P2       | Valuable, non-blocking               |
| low.md       | P3       | Cosmetic / incremental               |
| backlog.md   | –        | Untriaged                            |

**Selection order:** `shortlist → critical → high → medium → low`

---

## 🔑 Trigger Commands

| Command                   | Action                                          |
|---------------------------|------------------------------------------------|
| `init work`               | Create .work/ structure                         |
| `generate-baseline`       | Full repo audit → `.work/baseline.md`           |
| `create issue`            | Create issue with generated hash                |
| `focus on <topic>`        | Create issue(s) in `shortlist.md`               |
| `add to shortlist X`      | Add issue to shortlist                          |
| `remove from shortlist X` | Remove issue from shortlist                     |
| `continue`                | Resume work (see workflow documentation)        |
| `status`                  | Report focus + issue counts                     |
| `what's next`             | Recommend next issue (no state change)          |
| `validate`                | Run baseline-relative validation                |
| `housekeeping`            | Cleanup (excluding shortlist unless instructed) |

---

## ⚠️ After `init work`

After creating the structure:

1. ⚠️ **Generate baseline before any code changes**
   ```
   generate-baseline
   ```

2. Review detected project context in `memory.md`

3. Ready for work via `continue` or `focus on <topic>`

---

## 🤖 Configuring AGENTS.md

To enable agents to use the workflow system, add a reference to `do-work.prompt.md` in your agent configuration file.

### Template Variables

This prompt system uses Jinja2 templates. The following variables are resolved at runtime:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `.github/prompts` | Path to prompt files | `.github/prompts`, `.work/prompts` |
| `copilot` | Current AI tool name | `copilot`, `claude`, `cursor` |
| `` | Project root directory | `/home/user/myproject` |

### AI Tool Prompt Locations

Different AI tools expect prompts in different locations:

| AI Tool | Configuration Location |
|---------|------------------------|
| GitHub Copilot | `.github/copilot-instructions.md` or `.github/prompts/` |
| Claude Code | `CLAUDE.md` in project root, or `.claude/` |
| Cursor | `.cursor/rules/` or `.cursorrules` |
| Windsurf | `.windsurfrules` |
| Aider | `.aider/` or conventions file |
| Tool-agnostic | `.work/prompts/` |

### Adding the Reference

Add the following to your agent configuration, using the template variable:

```markdown
## Workflow

When working on issues or tasks, follow the workflow defined in:

- [do-work.prompt.md](.github/prompts/do-work.prompt.md)

Key commands:
- `init work` – Initialize the issue tracking system
- `continue` – Resume work following the optimal iteration loop
- `focus on <topic>` – Create prioritized issues for a specific topic
```

### Copying Prompt Files

Copy the prompt files to your project's prompt directory:

```
.github/prompts/
├── do-work.prompt.md              # Workflow documentation
└── setup-issue-tracker.prompt.md  # This setup guide
```

### Minimal Agent Configuration Example

```markdown
# Agent Instructions

## Project Overview
<your project description>

## Workflow

This project uses file-based issue tracking. Follow the workflow in:
- [do-work.prompt.md](.github/prompts/do-work.prompt.md)

Before making any code changes:
1. Run `init work` if `.work/` doesn't exist
2. Run `generate-baseline` before any code changes
3. Use `continue` to start/resume work

## Code Standards
<your coding standards>
```

---

## 📚 Detailed Documentation

For complete workflow documentation including:

- **Baseline system** (file-level detail, when to generate)
- **Focus management** (Previous/Current/Next structure)
- **Notes and Memory usage**
- **Validation protocol**
- **Iteration loop** (BASELINE → SELECT → INVESTIGATE → IMPLEMENT → VALIDATE → COMPLETE → LEARN → NEXT)
- **Regression handling** (create issues first, then fix)
- **Session handoff**

**See:** [do-work.prompt.md](.github/prompts/do-work.prompt.md)
