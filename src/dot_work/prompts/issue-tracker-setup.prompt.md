# 📋 File-Based Issue Tracker & Baseline-Gated Agent Workflow (Final Version)

This document is the **authoritative, baseline-driven execution model** for all AI agents working in this repository.

It defines:
- How work is tracked
- How tasks are selected
- How changes are validated
- When work is allowed to complete

The system is **file-based, deterministic, baseline-gated, and auditable**.  
No external tools. No time-based prioritization. No silent regressions.

---

## 🎯 Core Principles (Non-Negotiable)

1. **Baseline is the quality floor** – nothing may regress
2. **One active issue at a time**
3. **User intent overrides agent autonomy**
4. **All regressions block completion**
5. **All new problems are logged as issues**
6. **Validation is comparative, never absolute**
7. **Issues are the only unit of work**
8. **History is immutable**
9. **Shortlist changes require explicit user instruction**
10. **Every issue must be uniquely identifiable and traceable**
11. **Concrete file references are required when available**

---

## 📁 Canonical Directory Structure

```

.work/
├── agent/
│   ├── focus.md              # Current execution state (single source of truth)
│   ├── memory.md             # Persistent cross-session knowledge
│   ├── notes/                # Scratchpad, research, working notes
│   │   └── .gitkeep
│   └── issues/
│       ├── critical.md       # P0 – blockers, security, data loss
│       ├── high.md           # P1 – broken core functionality
│       ├── medium.md         # P2 – enhancements, tech debt
│       ├── low.md            # P3 – minor improvements
│       ├── backlog.md        # Untriaged ideas
│       ├── shortlist.md      # USER-DIRECTED priorities (conditionally writable)
│       ├── history.md        # Completed / closed issues (append-only)
│       └── references/       # Specs, logs, large docs, research
│           └── .gitkeep

```

### Structural Rules
- Issues exist **only** in `.work/agent/issues/`
- `history.md` is **append-only**
- `.work/` is the single source of operational truth

---

## 🆔 Issue Identity (Mandatory, Enforced)

Every issue **MUST** have:
1. A **semantic issue ID**
2. A **stable 6-character hash**

### Canonical Identifier Format

```

<PREFIX>-<NUMBER>@<HASH>

```

Example:
```

BUG-003@a9f3c2

````

### Identity Rules

- `<PREFIX>-<NUMBER>`
  - Human-readable
  - Sequential within its prefix
- `<HASH>`
  - Exactly **6 lowercase hexadecimal characters**
  - Generated once at creation
  - Immutable for the lifetime of the issue
  - Unique across the entire repository

Issues without hashes or with duplicate hashes are **invalid**.

---

## 📝 Issue Specification (Extended Mandatory Schema)

All issues — including those created directly in `shortlist.md` — **MUST** use this schema.

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
  - .work/agent/issues/references/large-doc.md
---

### Problem
Clear description of the problem or missing behavior.

### Affected Files
Concrete file references **must be listed when known**:
- `src/config.py`
- `tests/unit/test_config.py`

If the issue spans many files or requires extensive context, reference a document in `references/`.

### Error / Exception Details (if applicable)
Include verbatim technical details when relevant:
- Exception type
- Error code
- Stack trace excerpt
- Log output
- HTTP status codes

### Importance
Severity, value, dependencies, and user impact.

### Proposed Solution
High-level approach. No code unless strictly necessary.

### Acceptance Criteria
- [ ] Objective, testable condition
- [ ] Objective, testable condition

### Notes
Progress updates, findings, decisions.

### Code examples (if applicable)
Code snippets illustrating the issue or solving it as fenced code blocks

---
```

## 🏷️ Issue ID Prefixes

| Prefix   | Meaning                     |
| -------- | --------------------------- |
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
| DUPL     | Duplication                 |

---

## 📊 Priority Model (Strict)

### Priority Files

| File         | Priority | Meaning                              |
| ------------ | -------- | ------------------------------------ |
| critical.md  | P0       | Blocks progress, security, data loss |
| high.md      | P1       | Core functionality broken            |
| medium.md    | P2       | Valuable, non-blocking               |
| low.md       | P3       | Cosmetic / incremental               |
| backlog.md   | –        | Untriaged                            |
| shortlist.md | USER     | Explicit user focus                  |

### Allowed Priority Factors

Agents may prioritize **only** by:

* Severity
* Value
* Dependencies
* Complexity (ordering only)

🚫 Time, deadlines, or estimates are forbidden.

---

## 🧭 Control Files

### `focus.md` — Current Execution State

Always reference the **full canonical identifier**.

```markdown
- Issue: BUG-003@a9f3c2 – Fix config loading on Windows
```

Rules:

* Exactly one active issue
* Updated immediately on state change
* Never speculative

---

### `memory.md` — Persistent Knowledge

Stores facts that must survive sessions.

---

### `shortlist.md` — User-Directed Priority Queue

This file represents **explicit user intent**.

#### Access Rules

* The agent **MAY modify `shortlist.md` only when explicitly instructed by the user**
* The agent **MUST NOT** autonomously add, remove, reorder, or edit items
* All entries **MUST** use the full issue template and canonical identifier

#### `focus on <topic>` Behavior

When the user says:

```
focus on <some topic>
```

The agent **MUST**:

1. Interpret `<some topic>` as intent, not an identifier
2. Create **one or more issues directly in `shortlist.md`**
3. Use the **full issue schema**, including:

   * Newly generated ID + 6-char hash
   * Best-effort concrete file references
   * Error / exception details if applicable
4. Set `status: proposed`
5. Ask clarifying questions **only if**:

   * Multiple plausible interpretations exist
   * Scope cannot be reasonably inferred
   * Conflicting files or components are involved

If clarification is required:

* Do **not** create issues yet
* Ask targeted questions

---

## 🔑 Trigger Commands

| User Input                | Agent Action                                          |
| ------------------------- | ----------------------------------------------------- |
| `init work`               | Initialize structure + AGENTS.md                      |
| `create issue`            | Create issue with generated hash                      |
| `focus on <topic>`        | Create issue(s) in `shortlist.md` using full template |
| `add to shortlist X`      | Add canonical issue entry                             |
| `remove from shortlist X` | Remove exact identifier                               |
| `continue`                | Resume work deterministically (see below)             |
| `status`                  | Report focus + issue counts                           |
| `what’s next`             | Recommend next issue (no state change)                |
| `validate`                | Run baseline-relative validation                      |
| `generate-baseline`       | Full repo audit → `.work/baseline.md`                 |
| `housekeeping`            | Cleanup (excluding shortlist unless instructed)       |

---

## ▶️ `continue` — Deterministic Work Continuation

### Intent

Resume work without new user direction, strictly following workflow rules.

---

### Execution Order (Mandatory)

#### 1️⃣ Inspect Current Focus

* Read `focus.md`
* If an issue is already active:

  * Resume work
  * Do not switch tasks

#### 2️⃣ Process `shortlist.md`

If no active issue exists:

1. Read `shortlist.md`
2. If entries exist:

   * Select the **first issue**
   * Update `focus.md`
   * Set issue `status: in-progress`
   * Begin work

##### Completion Handling

When a shortlist issue completes:

1. Run `validate`
2. If validation passes:

   * Mark issue `completed`
   * Move issue block to `history.md`
   * Update `focus.md`
3. Remove issue from `shortlist.md`
4. Repeat until shortlist is empty

#### 3️⃣ Priority-Based Selection

If shortlist is empty and no active issue exists:

1. Scan in order:

   ```
   critical → high → medium → low
   ```
2. Select next eligible issue
3. Update `focus.md`
4. Set issue `status: in-progress`
5. Begin work

#### 4️⃣ No Work Available

If no actionable issues exist:

* Report “No actionable issues available”
* Make no state changes

---

## 📊 Baseline (`.work/baseline.md`)

The baseline defines the **minimum acceptable quality**.

* Generated only via `generate-baseline`
* Treated as authoritative
* Validation is always relative to baseline

If missing or stale:

* Validation **cannot pass**
* Agent must request regeneration

---

## ✅ VALIDATE — Baseline-Relative Validation Protocol

Validation ensures **nothing is worse than baseline**.

* Improvements allowed
* Regressions forbidden
* New problems logged as new issues

Validation covers:

1. Build & dependencies
2. Linting
3. Formatting
4. Type checking
5. Unit tests
6. Integration tests
7. Coverage
8. Security
9. Performance
10. Structural signals

---

## 🏁 Completion Protocol (Absolute)

An issue may be marked `completed` **only if**:

* Validation passes
* No metric is worse than baseline
* All regressions fixed
* All new problems logged

Mandatory steps:

1. Run `validate`
2. Update issue status
3. Move to `history.md` (ID unchanged)
4. Update `focus.md`
5. Update `memory.md` if needed
6. Report to user
7. Start next issue immediately

---

## 🧹 Housekeeping Mode

Performed periodically to:

* Remove duplicates
* Archive stale issues
* Re-evaluate priorities
* Consolidate notes
* Validate references

Housekeeping **MUST NOT** modify `shortlist.md` unless explicitly instructed.

---

## 🔒 Global Rules (Enforced)

1. Every issue has a unique `<PREFIX>-<NUMBER>@<HASH>`
2. Hashes never change
3. No duplicate hashes
4. Concrete file references required when available
5. Shortlist changes require explicit user instruction
6. One active issue at a time
7. No silent regressions
8. Validate before completion
9. Priority ≠ time
10. User intent > agent autonomy
11. `continue` never invents or skips work

---

## 📌 Final Guarantee

If followed correctly, this workflow guarantees:

* Stable, traceable issue identity
* Explicit linkage between problems and code
* No quality regression over time
* Deterministic, auditable agent behavior
* Safe long-running autonomous execution
