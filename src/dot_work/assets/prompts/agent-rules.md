---
meta:
  title: "Agent Rules"
  description: "Immutable constraints that apply to ALL agent operations"
  version: "1.0.0"
---

# Agent Rules (Mandatory)

These rules apply to **ALL agent operations** regardless of mode, phase, or environment.
They are non-negotiable and must be enforced before any other logic.

---

## 🚫 Immutable Constraints

### Code Safety

1. **NEVER use destructive commands without explicit user confirmation**
   - No `rm -rf` under any circumstances
   - No `git reset --hard` without user approval
   - No `DROP TABLE` or equivalent destructive SQL

2. **NEVER skip or disable tests to make progress**
   - Failing tests block completion
   - Create issues to fix, modify, or remove tests — don't skip them
   - All tests must run at all times

3. **NEVER adjust threshold values to pass validation**
   - Coverage requirements are fixed
   - Lint error limits are fixed
   - Performance baselines are fixed
   - If you can't meet thresholds, create an issue

4. **NEVER commit with failing tests or decreased coverage**
   - Build must pass
   - All tests must pass
   - Coverage must not regress

### Workflow Integrity

5. **NEVER skip steps in workflow instructions**
   - Baseline before code changes
   - Validation before completion
   - Issues before fixes
   - No shortcuts

6. **NEVER stop for user intervention during autonomous operation**
   - Research and plan alternatives
   - Create notes in `.work/agent/notes/` for decisions made
   - Create issues for blockers requiring human input
   - Continue with next actionable work

7. **NEVER modify shortlist.md autonomously**
   - Shortlist represents explicit user intent
   - Only modify when explicitly instructed by user

### Scope Boundaries

8. **Target source code: `./src` folder only**
   - Do not process source code outside `./src` unless explicitly referenced

9. **Target tests: `./tests` folder only**
   - Do not process test code outside `./tests` unless explicitly referenced

10. **Respect `.gitignore` and sensitive paths**
    - Never expose secrets, credentials, or API keys
    - Never commit `.env` files or secrets

---

## ✅ Required Behaviors

### Before Any Code Operations (CRITICAL)

1. **READ `.work/constitution.md` FIRST** — This defines:
   - Workspace root (absolute path)
   - Source code location (`src/` or similar)
   - Test location (`tests/` or similar)
   - Package name and import style
   - Off-limits paths
   
2. **Do NOT hallucinate file paths** — Only operate on files that:
   - Exist at the paths defined in constitution
   - Are within `src/` or `tests/` as defined
   - You have verified exist via Read or Glob

3. Verify `.work/` structure exists
4. Verify baseline exists and is current
5. Read `focus.md` for current state
6. Check `memory.md` for relevant context

### During Implementation

1. One issue at a time — complete focus
2. Update `focus.md` continuously
3. Create notes for investigation and decisions
4. Follow patterns from `memory.md`
5. Use commands from `constitution.md` (not hardcoded)

### After Implementation

1. Run full validation suite
2. Compare against baseline at file level
3. Create issues for ALL regressions found
4. Fix regressions before completing
5. Update `memory.md` with learnings
6. Move completed issue to `history.md`

---

## 🔧 Platform-Agnostic Requirements

### Commands

- **Do NOT hardcode commands** — read from `constitution.md`
- **Do NOT assume shell type** — use portable constructs
- **Do NOT assume path separators** — use platform-appropriate handling

### File Operations

- Use platform-agnostic path handling
- Handle both Unix and Windows paths
- Respect platform-specific line endings in output

### Dependencies

- Use project's declared package manager
- Do not assume global installations
- Respect version constraints

---

## 📋 Rule Enforcement

These rules are checked at multiple points:

| Checkpoint | Rules Verified |
|------------|----------------|
| Session start | Scope boundaries, baseline exists |
| Before code change | Baseline current, focus.md set |
| Before commit | Tests pass, coverage maintained |
| Before completion | Validation passed, no regressions |
| Before loop continue | No blocked issues, progress made |

### Violation Handling

If a rule would be violated:

1. **STOP** the current action
2. **LOG** the violation to `.work/agent/notes/violations.md`
3. **CREATE** an issue if the violation reveals a problem
4. **REPORT** to user if in interactive mode
5. **CONTINUE** with alternative action if possible

---

## 🔗 Integration

This file is referenced by:

- `agent-orchestrator.md` — loads rules at session start
- All subagents — inherit rules via orchestrator
- `do-work.md` — enforces rules during workflow

### Loading Rules

Agents must read this file at session start:

```
1. Load agent-rules.md
2. Load constitution.md (project-specific)
3. Merge: agent-rules take precedence
4. Apply combined rules to all operations
```

---

## 📚 See Also

**Related Prompts:** `agent-orchestrator-v2` (Main orchestrator), `do-work` (Workflow implementation)

**State Files:** `.work/constitution.md` (Project-specific rules, generated)

