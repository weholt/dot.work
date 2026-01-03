---
meta:
  title: "Agent Prompts Reference"
  description: "Quick reference for all available agent prompts and their integration with the issue tracker system"
  version: "0.1.1"
---
---

````prompt
# 🤖 Agent Prompts Reference

Quick reference for all available agent prompts and their integration with the issue tracker system.

---

## 📋 Available Agents

| Agent | Purpose | Issue Prefix | Output Modes |
|-------|---------|--------------|--------------|
| [critical-code-review]({{ prompt_path }}/critical-code-review.prompt.md) | Critical, evidence-based code review | `CR` | report, issues, both |
| [spec-delivery-auditor]({{ prompt_path }}/spec-delivery-auditor.prompt.md) | Verify specs were delivered in code | `SDA` | report, issues, both |
| [establish-baseline]({{ prompt_path }}/establish-baseline.prompt.md) | Capture frozen project snapshot | — | report, file, both |
| [compare-baseline]({{ prompt_path }}/compare-baseline.prompt.md) | Detect regressions vs baseline | `REG` | report, issues, both |

---

## 🔄 Agent Workflow Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                     AGENT WORKFLOW                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌────────────────────┐                                        │
│   │ ESTABLISH BASELINE  │  ← Run first, before any changes      │
│   │ (.work/baseline.md) │                                        │
│   └─────────┬──────────┘                                        │
│             │                                                    │
│             ▼                                                    │
│   ┌────────────────────┐                                        │
│   │    DO WORK         │  ← Main iteration loop                 │
│   │  (see do-work.md)  │                                        │
│   └─────────┬──────────┘                                        │
│             │                                                    │
│     ┌───────┴───────┐                                           │
│     ▼               ▼                                           │
│ ┌─────────┐   ┌─────────────┐                                   │
│ │ REVIEW  │   │ SPEC AUDIT  │  ← Quality gates (optional)       │
│ │  (CR)   │   │   (SDA)     │                                   │
│ └────┬────┘   └──────┬──────┘                                   │
│      │               │                                           │
│      └───────┬───────┘                                           │
│              ▼                                                   │
│   ┌────────────────────┐                                        │
│   │ BASELINE COMPARISON│  ← Validation phase                    │
│   │       (REG)        │                                        │
│   └─────────┬──────────┘                                        │
│             │                                                    │
│      ┌──────┴──────┐                                            │
│      ▼             ▼                                            │
│    PASS          FAIL                                           │
│      │             │                                            │
│      │             ▼                                            │
│      │   ┌─────────────────┐                                    │
│      │   │ CREATE ISSUES   │  ← Auto-emit to issue tracker      │
│      │   └─────────────────┘                                    │
│      │                                                           │
│      ▼                                                           │
│   COMPLETE                                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 Universal Issue Schema

All agents use this schema when emitting issues:

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
Include verbatim technical details when relevant.

### Importance
Severity, value, dependencies, and user impact.

### Proposed Solution
High-level approach. No code unless strictly necessary.

### Acceptance Criteria
- [ ] Objective, testable condition
- [ ] Objective, testable condition

### Notes
Progress updates, findings, decisions.
```

---

## 🏷️ Issue Prefix Registry

| Prefix | Source | Meaning |
|--------|--------|---------|
| `BUG` | Manual / Workflow | Defect |
| `FEAT` | Manual / Workflow | New feature |
| `ENHANCE` | Manual / Workflow | Improve existing |
| `REFACTOR` | Manual / Workflow | Code improvement |
| `DOCS` | Manual / Workflow | Documentation |
| `TEST` | Manual / Workflow | Testing |
| `SEC` | Manual / Workflow | Security |
| `PERF` | Manual / Workflow | Performance |
| `DEBT` | Manual / Workflow | Technical debt |
| `STRUCT` | Manual / Workflow | Architecture |
| `CR` | critical-code-review | Code review finding |
| `SDA` | spec-delivery-auditor | Spec delivery gap |
| `REG` | baseline-comparison | Regression |

---

## 📊 Priority → File Mapping

All agents place issues in the same locations:

| Priority | File |
|----------|------|
| `critical` | `.work/agent/issues/critical.md` |
| `high` | `.work/agent/issues/high.md` |
| `medium` | `.work/agent/issues/medium.md` |
| `low` | `.work/agent/issues/low.md` |

---

## 🔧 How to Use These Prompts

These are instruction documents for AI agents, not executable commands. To use them:

### Option 1: Reference in Your Agent Config

Add to your AGENTS.md or tool-specific config:
```markdown
For code reviews, follow the instructions in:
- [critical-code-review.prompt.md]({{ prompt_path }}/critical-code-review.prompt.md)

For spec verification, follow:
- [spec-delivery-auditor.prompt.md]({{ prompt_path }}/spec-delivery-auditor.prompt.md)
```

### Option 2: Direct Invocation

Ask your AI assistant to follow a specific prompt:

> "Establish a project baseline using the baseline-establisher prompt"

> "Review this code following the critical-code-review prompt. Output mode: issues"

> "Audit this implementation against the spec using spec-delivery-auditor"

> "Compare current state against baseline using baseline-comparison"

### Option 3: Parameters for Orchestration

When delegating work to these prompts, pass parameters:

```yaml
# For critical-code-review
output_mode: issues  # or: report, both
issue_prefix: CR

# For spec-delivery-auditor
output_mode: issues
issue_prefix: SDA
specification: "<issue or requirements>"
strictness: strict

# For baseline-establisher
scope: repository
output_mode: both

# For baseline-comparison
baseline_path: .work/baseline.md
current_ref: HEAD
output_mode: both
issue_prefix: REG
strictness: strict
```

---

## 🎯 When to Use Each Agent

| Situation | Agent | Purpose |
|-----------|-------|---------|
| Starting work on a project | establish-baseline | Capture starting state |
| Reviewing a PR or code changes | critical-code-review | Find issues in code |
| Verifying work is complete | spec-delivery-auditor | Ensure spec was delivered |
| Validation before completing issue | compare-baseline | Check for regressions |

---

## 📁 Directory Structure

```
.work/
├── baseline.md                 # Project baseline snapshot
└── agent/
    ├── focus.md
    ├── memory.md
    ├── notes/
    └── issues/
        ├── critical.md
        ├── high.md
        ├── medium.md
        ├── low.md
        ├── backlog.md
        ├── shortlist.md
        ├── history.md
        └── references/
```

---

## 🔗 Related Documentation

| Document | Purpose |
|----------|---------|
| [do-work.prompt.md]({{ prompt_path }}/do-work.prompt.md) | Main workflow loop |
| [setup-issue-tracker.prompt.md]({{ prompt_path }}/setup-issue-tracker.prompt.md) | Issue tracker initialization |
| [critical-code-review.prompt.md]({{ prompt_path }}/critical-code-review.prompt.md) | Code review agent |
| [spec-delivery-auditor.prompt.md]({{ prompt_path }}/spec-delivery-auditor.prompt.md) | Spec verification agent |
| [establish-baseline.prompt.md]({{ prompt_path }}/establish-baseline.prompt.md) | Baseline capture agent |
| [compare-baseline.prompt.md]({{ prompt_path }}/compare-baseline.prompt.md) | Regression detection agent |

```
