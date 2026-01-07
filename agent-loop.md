# Agent Loop

**MANDATORY RULES**
- Do NOT adjust defined threshold values, like test coverage requirements
- Do NOT skip or disable unittests to continue work: create issues to fix, modify or remove the unittest
- Do NOT skip steps in the instructions under any condition
- Do NOT stop for user intervention: research, plan and create notes in `.work/agent/notes/` for decisions
- DO NOT USE THE `rm -rf` COMMAND
- Target source code: `./src` folder. Tests: `./tests` folder. Do not process code outside these unless explicitly referenced.

---

## Quick Start

```
continue    # Start or resume autonomous loop
status      # Show current focus and issue counts
```

---

## Architecture

The autonomous loop uses a subagent-based architecture for context-optimized execution:

```
Orchestrator
    ├── Pre-Iteration Subagent (issue selection, ~3K context)
    ├── Implementer Subagent (focused work, ~8K context)
    ├── Validation Subagents (parallel, ~4K each)
    │   ├── Code Reviewer
    │   ├── Security Auditor
    │   ├── Spec Auditor
    │   └── Performance Reviewer
    └── Loop Evaluator (continue/done/blocked, ~2K context)
```

---

## Installed Assets

After running `dot-work install`, assets are available at environment-specific locations.

### For Claude Code (`.claude/`)

**Commands** (`.claude/commands/`):
- `agent-orchestrator-v2` - Main orchestrator with subagent delegation
- `agent-rules` - Immutable constraints
- `do-work` - Workflow overview
- `create-constitution` - Project setup
- `establish-baseline` - Quality baseline

**Agents** (`.claude/agents/`):
- `pre-iteration` - Issue selection
- `implementer` - Implementation
- `loop-evaluator` - Loop control
- `code-reviewer` - Code review
- `security-auditor` - Security audit
- `spec-auditor` - Spec compliance
- `performance-reviewer` - Performance

**Skills** (`.claude/skills/`):
- `issue-management/` - Issue housekeeping
- `focus-selector/` - Issue selection
- `baseline-validation/` - Baseline comparison
- `git-workflow/` - Atomic commits
- `issue-creation/` - Creating issues

### For GitHub Copilot (`.github/`)

Prompts installed to `.github/prompts/`
Agents installed to `.github/agents/`

### For OpenCode (`.opencode/`)

Prompts installed to `.opencode/prompts/`
Agents installed to `.opencode/agent/`

---

## State Files

```
.work/
├── constitution.md          # Project configuration (generated)
├── baseline.md              # Quality metrics baseline
└── agent/
    ├── focus.md             # Current issue focus
    ├── memory.md            # Accumulated learnings
    ├── orchestrator-state.json
    ├── prepared-context.json
    ├── implementation-report.json
    ├── validation-*.json
    ├── notes/               # Investigation notes
    └── issues/
        ├── shortlist.md     # User priority (don't modify autonomously)
        ├── critical.md      # P0 issues
        ├── high.md          # P1 issues
        ├── medium.md        # P2 issues
        ├── low.md           # P3 issues
        ├── backlog.md       # Untriaged
        ├── history.md       # Completed issues
        └── references/      # Related documentation
```

---

## Completion Signals

The loop evaluator outputs these promises for harness integration:

| Promise | Meaning |
|---------|---------|
| `<promise>LOOP_DONE</promise>` | All work complete |
| `<promise>LOOP_CONTINUE</promise>` | More work remains |
| `<promise>LOOP_BLOCKED</promise>` | Needs human intervention |
| `<promise>LOOP_ERROR</promise>` | Unrecoverable error |

---

## Manual Execution

If not using the orchestrator:

1. Move completed issues from issue files to `history.md`
2. Establish baseline: run `establish-baseline` command
3. Commit clean baseline state
4. Select issue and update `focus.md`
5. Review `memory.md` for context
6. Implement the issue
7. Log new issues found via `new-issue` command
8. Run validation: code-review, security-review, performance-review, spec-delivery-auditor
9. Move completed issue to history
10. Repeat from step 4 until no issues remain
11. Report "AGENT DONE"

---

## Key Principles

1. **Baseline before anything** — No code changes until baseline is established
2. **One issue, complete focus** — No multitasking
3. **Validate before completing** — Every batch of work ends with validation
4. **Create issues first, then fix** — Regressions create issues before being fixed
5. **Learn at the end** — Extract lessons to memory after validation passes
6. **Leave breadcrumbs** — Future sessions should resume seamlessly

---

*Run `dot-work install` to install assets to your environment*
