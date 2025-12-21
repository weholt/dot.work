# 🔄 Optimal Iteration Workflow for AI Agents

This prompt defines the **optimal execution pattern** for AI agents working iteratively on issues in a file-based issue tracking system. It maximizes efficiency, maintains quality, and ensures deterministic behavior across sessions.

---

## 🎯 Workflow Philosophy

1. **Baseline before anything** — No code changes until baseline is established
2. **One issue, complete focus** — No multitasking
3. **Validate before completing** — Every batch of work ends with validation
4. **Fix before moving on** — Regressions block progress, create issues first, then fix
5. **Learn at the end** — Extract lessons to memory/notes after validation passes
6. **Leave breadcrumbs** — Future sessions should resume seamlessly

---

## 📋 Pre-Work Checklist

Before starting any work, verify:

```
□ .work/ structure exists?
  └─ NO → Run `init work`

□ Working in correct branch / clean commit state?
  └─ UNCLEAR → Ask user: "Should I create a new branch or work from current commit?"
  └─ NO → Create branch or commit current state before proceeding
  
□ .work/baseline.md exists and is current for THIS iteration?
  └─ NO → Run `generate-baseline` BEFORE ANY CODE CHANGES
  └─ STALE (new iteration starting) → Regenerate baseline first
  ⚠️  NO CODE CHANGES ARE PERMITTED UNTIL BASELINE IS ESTABLISHED

□ Are there completed issues in the issue files?
  └─ YES → Move all completed issues to history.md first
  └─ NO → Proceed

□ focus.md has active work?
  └─ YES → Resume that work (do not switch)
  └─ NO → Ready to select new issue
  
□ memory.md reviewed for relevant context?
  └─ Check for user preferences affecting this work
  └─ Check for lessons from similar past issues
```

---

## 🔄 The Optimal Iteration Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                    OPTIMAL ITERATION LOOP                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐                                              │
│   │  BASELINE    │  ◄── MUST BE FIRST, NO EXCEPTIONS            │
│   └──────┬───────┘                                              │
│          │                                                       │
│          ▼                                                       │
│   ┌──────────────┐                                              │
│   │   SELECT     │                                              │
│   └──────┬───────┘                                              │
│          │                                                       │
│          ▼                                                       │
│   ┌──────────────┐     ┌──────────────┐                         │
│   │ INVESTIGATE  │────▶│    NOTES     │                         │
│   └──────┬───────┘     └──────────────┘                         │
│          │                                                       │
│          ▼                                                       │
│   ┌──────────────┐                                              │
│   │  IMPLEMENT   │                                              │
│   └──────┬───────┘                                              │
│          │                                                       │
│          ▼                                                       │
│   ┌──────────────┐                                              │
│   │   VALIDATE   │  ◄── Compare against baseline                │
│   └──────┬───────┘                                              │
│          │                                                       │
│     ┌────┴────┐                                                  │
│     │         │                                                  │
│    PASS      FAIL                                                │
│     │         │                                                  │
│     │         ▼                                                  │
│     │    ┌─────────────┐                                        │
│     │    │CREATE ISSUES│  ◄── Log all regressions first         │
│     │    └──────┬──────┘                                        │
│     │           │                                                │
│     │           ▼                                                │
│     │    ┌─────────────┐                                        │
│     │    │  FIX ISSUES │  ◄── Then fix them                     │
│     │    └──────┬──────┘                                        │
│     │           │                                                │
│     │           └──────────▶ (back to VALIDATE)                  │
│     │                                                            │
│     ▼                                                            │
│ ┌──────────────┐                                                │
│ │   COMPLETE   │                                                │
│ └──────┬───────┘                                                │
│        │                                                         │
│        ▼                                                         │
│ ┌──────────────┐                                                │
│ │LEARN (MEMORY)│  ◄── Extract lessons AFTER validation passes   │
│ └──────┬───────┘                                                │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────┐                                                    │
│   │  NEXT   │                                                    │
│   └─────────┘                                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📖 Phase Details

### Phase 1: BASELINE (Mandatory First Step)

**Goal:** Establish the quality floor before any code changes.

⚠️ **NO CODE CHANGES ARE PERMITTED UNTIL BASELINE IS COMPLETE**

```markdown
Actions:
  1. Verify .work/ structure exists (run `init work` if not)
  2. Confirm branch/commit state with user if unclear:
     - "Should I create a new branch for this work?"
     - "Should I commit current state before starting?"
  3. Generate fresh baseline for this iteration
  4. Read focus.md for context (previous/current/next)
  5. Scan memory.md for relevant lessons

Output: baseline.md with full file-level detail

Example focus.md check:
  - Has current issue → Resume that issue
  - Current empty, next exists → Start next issue
  - All empty → Ready to select new work
```

**Baseline must be regenerated when:**
- Starting a new iteration/batch of issues
- Switching to a new branch
- After a commit that changes the codebase state
- User explicitly requests it

### Phase 2: SELECT

**Goal:** Choose the next issue to work on.

```markdown
Selection Order (strict):
  1. First item in shortlist.md (USER PRIORITY - ALWAYS HIGHEST)
  2. Resume focus.md current issue if exists and shortlist is empty
  3. Start focus.md next issue if current is empty and shortlist is empty
  4. Any item in critical.md (P0)
  5. Any item in high.md (P1)
  6. Any item in medium.md (P2)
  7. Any item in low.md (P3)

Actions:
  1. Check shortlist.md FIRST - user priority always wins
  2. If shortlist empty, read focus.md for current/next context
  3. Select first actionable issue
  4. Update focus.md with all three values:
     - Previous: what was just completed (if any)
     - Current: the issue now being worked on
     - Next: the anticipated next issue
  5. Update issue status in source file

Output: focus.md updated with previous/current/next
```

**Example Selection:**

```markdown
# focus.md after selection

## Previous
- Issue: BUG-002@e5f6a7 – Fix memory leak in parser
- Completed: 2024-01-15T13:45:00Z
- Outcome: Fixed, validated, in history.md

## Current
- Issue: BUG-003@a9f3c2 – Fix config loading on Windows
- Started: 2024-01-15T14:20:00Z
- Status: in-progress
- Phase: Investigation
- Source: shortlist.md

## Next
- Issue: ENHANCE-001@b2c3d4 – Improve error messages
- Source: shortlist.md
- Reason: User priority, follows current work
```

### Phase 3: INVESTIGATE

**Goal:** Understand the problem completely before implementing.

```markdown
Actions:
  1. Create notes file: notes/<issue-id>-investigation.md
  2. Read all affected files mentioned in issue
  3. Reproduce the problem if applicable
  4. Form hypotheses about root cause
  5. Document findings in notes
  6. Determine implementation approach
  7. Update focus.md phase to "Investigation"

Investigation Checklist:
  □ Can I reproduce the issue?
  □ Do I understand the root cause?
  □ Do I know which files need changes?
  □ Is my proposed solution clear?
  □ Are there edge cases to consider?
  □ Does memory.md have relevant lessons?
  □ Will my changes affect files with existing warnings in baseline?

Output: Clear understanding, documented in notes
```

**Example Investigation Notes:**

```markdown
# notes/bug-003-investigation.md

## Issue: BUG-003@a9f3c2 – Fix config loading on Windows
Investigation started: 2024-01-15T14:25:00Z

### Reproduction
✓ Reproduced on Windows
✓ Works on Linux/macOS
✓ Error: FileNotFoundError at config.py:45

### Analysis
Line 45: `path = base_dir + "/" + filename`

This uses forward slash for path concatenation.
- Linux/macOS: Works (forward slash is valid)
- Windows: Fails (expects backslash or mixed handling)

### Root Cause
String-based path concatenation is not cross-platform.

### Hypotheses Tested
1. ✗ Case sensitivity - Not the issue
2. ✓ Path separator - Confirmed as root cause
3. ✗ Permission issue - Not the issue

### Solution
Replace string concatenation with pathlib.Path:
```python
path = Path(base_dir) / filename
```

### Affected Code
- src/config.py:45-50 (path construction)
- src/config.py:72 (similar pattern)
- tests/test_config.py (need Windows test cases)

### Risks
- None significant
- pathlib is stdlib, no new dependencies
```

### Phase 4: IMPLEMENT

**Goal:** Make the necessary changes to resolve the issue.

```markdown
Actions:
  1. Update focus.md phase to "Implementation"
  2. Make code changes as planned
  3. Add/update tests as needed
  4. Update documentation if affected
  5. Update focus.md progress continuously

Implementation Principles:
  - Small, focused changes
  - One logical change per commit concept
  - Tests accompany code changes
  - Follow patterns from memory.md
  - Document non-obvious decisions
  - Check baseline for existing warnings in files you're modifying

Output: Code changes ready for validation
```

**Focus Update During Implementation:**

```markdown
# focus.md during implementation
Last updated: 2024-01-15T15:30:00Z

## Previous
- Issue: BUG-002@e5f6a7 – Fix memory leak in parser
- Completed: 2024-01-15T13:45:00Z
- Outcome: Fixed and validated

## Current
- Issue: BUG-003@a9f3c2 – Fix config loading on Windows
- Started: 2024-01-15T14:20:00Z
- Status: in-progress
- Phase: Implementation
- Progress:
  - [x] Investigation complete
  - [x] Updated path handling in config.py:45
  - [x] Updated path handling in config.py:72
  - [ ] Add Windows test cases
  - [ ] Run validation
- Files modified:
  - src/config.py (lines 45, 72)
- Notes: notes/bug-003-investigation.md

## Next
- Issue: ENHANCE-001@b2c3d4 – Improve error messages
- Source: shortlist.md
- Reason: User priority
```

### Phase 5: VALIDATE

**Goal:** Ensure changes don't regress quality.

```markdown
Actions:
  1. Update focus.md phase to "Validation"
  2. Run full validation suite
  3. Compare all metrics to baseline.md at FILE LEVEL
  4. Document results with specific file references
  5. Record execution times for tests/build/validation

Validation Checks:
  □ Build passes
  □ All tests pass
  □ Coverage ≥ baseline
  □ No new lint errors (compare by file)
  □ No new type errors (compare by file)
  □ No security issues introduced
  □ Previously clean files remain clean
  □ Files with pre-existing warnings have not gotten worse

Execution Timing (record these):
  - Build time: X seconds
  - Test execution time: X seconds
  - Lint time: X seconds
  - Type check time: X seconds

Output: Validation report with file-level regression analysis
```

**Validation Scenarios:**

```markdown
# Scenario A: Validation Passes

Validation Report:
  Build: ✓ passing
  Tests: ✓ 265/265 (was 263, +2 new)
  Coverage: ✓ 79.1% (was 78.3%, improved)
  Lint: ✓ 0 errors, 10 warnings (was 12, improved)
  Types: ✓ 0 errors
  
Result: PASS - Ready for completion

# Scenario B: Validation Fails

Validation Report:
  Build: ✓ passing
  Tests: ✗ 263/265 (2 failures)
    - test_config_load_json FAILED
    - test_config_default FAILED
  Coverage: ⚠ 77.8% (was 78.3%, regressed)
  
Result: FAIL - Must fix before completion

Actions Required:
  1. Fix failing tests
  2. Add tests to restore coverage
  3. Re-run validation
```

### Phase 6: COMPLETE (on validation pass)

**Goal:** Properly close the issue and transition state.

```markdown
Actions (in order):
  1. Update issue status to "completed"
  2. Move issue block to history.md (append)
  3. Remove issue from source file
  4. Update focus.md and set current issue as previous
     - Current → Previous
     - Next → Current
     - Select new → Next
  5. Archive notes to references/ (if valuable)
  6. Update memory.md with learnings
  7. Report completion to user

Completion Checklist:
  □ Issue status = completed
  □ Issue in history.md (with full details)
  □ Issue removed from source file
  □ focus.md cleared
  □ Notes archived or deleted
  □ Memory updated with learnings
  □ User notified
```

**Example Completion:**

```markdown
─────────────────────────────────
ISSUE COMPLETED: BUG-003@a9f3c2
─────────────────────────────────

Summary:
  Fixed Windows path handling in config.py by replacing
  string concatenation with pathlib.Path operations.

Changes:
  - src/config.py (2 locations)
  - tests/test_config.py (+2 tests)

Metrics Impact:
  - Tests: +2 (263 → 265)
  - Coverage: +0.8% (78.3% → 79.1%)
  - Lint warnings: -2 (12 → 10)

Learnings Added to Memory:
  - Use pathlib.Path for cross-platform file operations
  - String path concatenation fails on Windows

Next Issue:
  ENHANCE-002@c8d3e4 in shortlist.md
  
Say `continue` to proceed.
```

### Phase 7: FIX (on validation failure)

**Goal:** Address regressions before attempting completion again.

⚠️ **CREATE ISSUES FIRST, THEN FIX**

```markdown
Actions:
  1. Analyze validation failures
  2. FIRST: Create issues for ALL regressions found:
     - One issue per distinct regression
     - Include file name, line number, error details
     - Link to original issue that caused it
  3. THEN: Fix each regression issue
     - Update focus.md current to the fix issue
     - Track progress on each fix
  4. Re-run validation after fixes
  5. Repeat until all regressions resolved

Regression Categories:
  - Direct regression: New error in file you modified
  - Indirect regression: New error in file you didn't modify
  - Pre-existing exposed: Error that baseline already had

Fix Priority:
  1. Failing tests (blocks everything)
  2. New errors in modified files
  3. New errors in unmodified files
  4. Coverage regression
  5. Warning increases
```

### Phase 8: LEARN (Memory & Notes)

**Goal:** Extract and preserve learnings AFTER validation passes.

This phase happens ONLY after validation succeeds. Take time to investigate the code and changes for lessons.

```markdown
Actions:
  1. Review the completed work:
     - What problem was solved?
     - How was it solved?
     - What was unexpected?
  2. Investigate the code for patterns:
     - Did this reveal anything about the codebase?
     - Are there similar issues elsewhere?
     - Should a pattern be documented?
  3. Update memory.md with dated entries:
     - User preferences discovered
     - Technical lessons learned
     - Patterns to follow/avoid
     - Architectural decisions made
  4. Archive useful notes to references/
  5. Delete temporary notes no longer needed

Memory Entry Criteria:
  - Will this knowledge help with future issues? → Add
  - Is this specific to only this issue? → Skip
  - Did the user express a preference? → Add
  - Was there a non-obvious solution? → Add
  - Did fixing a regression teach something? → Add
```

**Example Memory Update:**

```markdown
# Added to memory.md

## Lessons Learned
- [BUG-003@a9f3c2] 2024-01-15: Cross-platform file paths
  - Always use pathlib.Path, never string concatenation
  - Forward slash fails on Windows in path construction
  - pathlib handles OS differences automatically

## Patterns
- File path operations: Use `Path(base) / child` pattern
```

### Phase 9: NEXT

**Goal:** Seamlessly transition to next issue.

```markdown
Actions:
  1. Check shortlist.md for user priorities
  2. If shortlist empty, check priority files
  3. Select next actionable issue
  4. Return to Phase 2 (SELECT)

Transition Flow:
  shortlist.md → critical.md → high.md → medium.md → low.md
  
If no issues available:
  - Report "No actionable issues"
  - Suggest running `housekeeping`
  - Wait for user input
```

---

## ⏰ When to Generate Baseline

**Baseline is ALWAYS the first step of an iteration.**

| Trigger | Command | Reason |
|---------|---------|--------|
| Starting new iteration | `generate-baseline` | **MANDATORY FIRST STEP** |
| New branch created | `generate-baseline` | Fresh reference for branch |
| After commit (before new work) | `generate-baseline` | Establish new floor |
| Baseline missing | `generate-baseline` | Required for any validation |
| User requests | `generate-baseline` | Explicit intent |

**When unclear about branch/commit state:**
```
Agent: "Should I create a new branch for this work, or commit 
        current state first? I need to establish baseline before
        making any code changes."
```

**Do NOT regenerate baseline:**
- After each issue (only at iteration start)
- When validation fails (would hide regressions)
- To "pass" a failing validation (cheating)
- During active work on an issue

---

## 📊 Baseline Content Requirements

The baseline MUST include file-level detail to enable regression tracking to specific files.

**Required Baseline Structure:**

```markdown
# Baseline Report
Generated: 2024-01-15T10:30:00Z
Commit: abc1234
Branch: feature/improve-config

## Build Status
- Status: passing
- Execution time: 45s

## Dependencies
- Total: 127
- Outdated: 3
  - requests (2.28.0 → 2.31.0)
  - pyyaml (6.0 → 6.0.1)
  - pytest (7.2.0 → 7.4.0)
- Vulnerable: 0

## Linting
- Total errors: 0
- Total warnings: 12

### Warnings by File
| File | Count | Details |
|------|-------|---------|
| src/config.py | 3 | W0611:unused-import (L5, L12), W0612:unused-variable (L45) |
| src/parser.py | 5 | W0612:unused-variable (L23, L67, L89), W0611:unused-import (L3, L8) |
| src/cli.py | 4 | W0702:bare-except (L34, L78), W0612:unused-variable (L92, L105) |

## Formatting
- Status: compliant
- Files checked: 45
- Execution time: 3s

## Type Checking
- Total errors: 0
- Total warnings: 5

### Type Warnings by File
| File | Count | Details |
|------|-------|---------|
| src/config.py | 2 | Missing return type (L45), Incompatible type (L72) |
| src/api.py | 3 | Missing type annotation (L12, L34, L56) |

## Tests
- Unit tests: 245 passed, 0 failed
- Integration tests: 18 passed, 0 failed
- Execution time: 127s

### Test Files
| File | Tests | Status |
|------|-------|--------|
| tests/test_config.py | 23 | all passing |
| tests/test_parser.py | 45 | all passing |
| tests/test_cli.py | 31 | all passing |
| ... | ... | ... |

## Coverage
- Overall: 78.3%

### Coverage by File
| File | Coverage | Uncovered Lines |
|------|----------|----------------|
| src/config.py | 92% | 45-50, 112 |
| src/parser.py | 67% | 23-45, 89-120, 145 |
| src/cli.py | 81% | 34-40, 156-160 |
| src/api.py | 45% | 12-80 |

## Security
- Critical: 0
- High: 0
- Medium: 1
  - SEC-001@f3a2b1: Known issue in src/auth.py (tracked)

## Files Summary
Total Python files: 45
Files with issues: 4
Clean files: 41

### Clean Files (no warnings/errors)
src/utils.py
src/models.py
src/database.py
... (list all clean files)

### Files with Pre-existing Issues
src/config.py: 3 lint warnings, 2 type warnings, 92% coverage
src/parser.py: 5 lint warnings, 67% coverage
src/cli.py: 4 lint warnings, 81% coverage
src/api.py: 3 type warnings, 45% coverage
```

**Why File-Level Detail Matters:**

```markdown
During validation, we can detect:

1. New issues in previously clean files → CLEAR REGRESSION
   - config.py was clean, now has warnings → Your change broke it

2. More issues in already-problematic files → REGRESSION
   - parser.py had 5 warnings, now has 7 → You added 2 warnings

3. Issues in unmodified files → INVESTIGATE
   - api.py wasn't touched but has new error → Indirect breakage

4. Issues in files you modified → YOUR RESPONSIBILITY
   - If baseline says config.py had 3 warnings
   - And you modified config.py
   - And now it has 5 warnings
   - You introduced 2 warnings
```

---

## 📝 When to Use Notes

Create/update notes for:

| Situation | Notes File | Content |
|-----------|------------|---------|
| Starting investigation | `<issue-id>-investigation.md` | Hypotheses, findings |
| Comparing solutions | `<topic>-comparison.md` | Options, tradeoffs |
| Performance analysis | `<issue-id>-benchmarks.md` | Measurements, results |
| Complex debugging | `<issue-id>-debug.md` | Stack traces, steps |
| API research | `<topic>-api-notes.md` | Endpoints, schemas |
| User conversation | `meeting-<date>.md` | Decisions, context |

**Notes Lifecycle:**
```
Create → Update during work → Archive to references/ or Delete
```

---

## 🧠 When to Use Memory

Update memory.md for:

| Discovery | Memory Section | Example |
|-----------|----------------|---------|
| User preference | User Preferences | "Prefers explicit imports" |
| Technical lesson | Lessons Learned | "pathlib for cross-platform" |
| Architecture decision | Architectural Decisions | "SQLite for storage" |
| Code pattern | Patterns & Conventions | "Factory pattern for services" |
| Project constraint | Known Constraints | "Support Python 3.8+" |
| Cross-cutting knowledge | Cross-Issue Knowledge | "Config affects 12 modules" |

**Memory Rules:**
- Always cite the source issue
- Always include date
- Keep entries concise
- Review and prune periodically

---

## 🎯 Focus State Management

### Focus Structure (Three Values)

focus.md MUST always contain three sections, updated continuously:

```markdown
# Agent Focus

## Previous
The last completed issue (provides context)

## Current  
The issue actively being worked on (single source of truth)

## Next
The anticipated next issue (enables planning)
```

### Focus States

```
CURRENT EMPTY    → Ready for new work (check Next)
IN-PROGRESS      → Actively working on Current
BLOCKED          → Waiting for input
VALIDATING       → Running checks
FIXING           → Resolving regressions
```

### Focus Transitions

```
[Complete issue]
  Current → Previous
  Next → Current
  (select new) → Next

[Start new issue]
  (keep) Previous
  Next → Current  
  (select new) → Next

[Validation failure]
  (keep) Previous
  Current → Current (status: fixing)
  (keep) Next
```

### Complete Focus Template

```markdown
# Agent Focus
Last updated: 2024-01-15T14:45:00Z

## Previous
- Issue: BUG-002@e5f6a7 – Fix memory leak in parser
- Completed: 2024-01-15T13:45:00Z
- Outcome: Fixed and validated
- Lesson: Added to memory.md (use context managers for file handles)

## Current
- Issue: BUG-003@a9f3c2 – Fix config loading on Windows
- Started: 2024-01-15T14:20:00Z
- Status: in-progress
- Phase: Implementation
- Progress:
  - [x] Investigation complete
  - [x] Updated path handling in config.py
  - [ ] Add Windows test cases
  - [ ] Run validation
- Files modified:
  - src/config.py (lines 45, 72)
- Notes: notes/bug-003-investigation.md

## Next
- Issue: ENHANCE-001@b2c3d4 – Improve error messages
- Source: shortlist.md (user priority)
- Reason: User requested, natural follow-up to config work
- Prep: May need to review memory.md for error message patterns
```

### Focus Update Rules

1. **Update immediately** when any state changes
2. **Previous** is set when Current completes (not before)
3. **Current** is the single source of truth for active work
4. **Next** should always be populated when possible
5. **All three sections** must exist (use "None" if empty)

### Focus During Validation Failure

```markdown
## Current
- Issue: BUG-003@a9f3c2 – Fix config loading on Windows
- Started: 2024-01-15T14:20:00Z
- Status: fixing-regressions
- Phase: Validation failed, fixing issues
- Regressions found:
  - BUG-004@c3d4e5: New lint warning in config.py:48 (created)
  - BUG-005@d4e5f6: Test failure test_config_yaml (created)
- Progress:
  - [x] Issues created for all regressions
  - [ ] Fix BUG-004@c3d4e5
  - [ ] Fix BUG-005@d4e5f6
  - [ ] Re-run validation
```

---

## 🔄 Session Handoff Protocol

When a session ends (or may end):

```markdown
Handoff Checklist:
  1. ✓ focus.md has all three sections (Previous/Current/Next)
  2. ✓ Current section has detailed progress
  3. ✓ Any partial work is clearly described
  4. ✓ Blockers are documented with context
  5. ✓ Next is populated for seamless continuation

The next session should be able to:
  - Read focus.md and understand immediately
  - Know what was just done (Previous)
  - Resume Current work without re-investigation
  - Know what's coming (Next)
```

**Example Handoff State:**

```markdown
# Agent Focus
Last updated: 2024-01-15T17:30:00Z

## Previous
- Issue: BUG-002@e5f6a7 – Fix memory leak in parser
- Completed: 2024-01-15T13:45:00Z
- Outcome: Fixed and validated

## Current
- Issue: FEAT-012@b2c3d4 – Add dark mode support
- Started: 2024-01-15T14:00:00Z
- Status: in-progress
- Phase: Implementation (60% complete)
- Progress:
  - [x] Created theme context provider
  - [x] Added color token system
  - [x] Updated 3/7 components for theme support
  - [ ] Update remaining 4 components
  - [ ] Add theme persistence to localStorage
  - [ ] Create theme toggle UI
  - [ ] Add tests
- Current file: src/components/Button.tsx (line 45)
- Notes: notes/feat-012-implementation.md
- Blockers: None

## Next
- Issue: REFACTOR-001@a1b2c3 – Consolidate color constants
- Source: medium.md
- Reason: Natural follow-up, shares color token work
```

---

## 🏃 Quick Reference: Common Flows

### Flow 1: Starting a New Iteration
```
1. Confirm branch/commit state (ask if unclear)
2. Generate baseline ← BEFORE ANY CODE
3. Check shortlist.md FIRST (user priority always wins)
4. If shortlist empty, read focus.md for context
5. If Current exists → Resume
6. If Current empty, Next exists → Start Next
7. Otherwise → Select from priority files
```

### Flow 2: User Says "continue"
```
1. Is baseline current for this iteration?
   NO → Generate baseline first
2. Check shortlist.md FIRST (user priority always wins)
   HAS ITEMS → Select first item, update focus.md
3. If shortlist empty, read focus.md (Previous/Current/Next)
4. If Current has active issue → Resume it
5. If Current empty, Next exists → Promote Next to Current
6. Select new Next issue
7. Update focus.md with all three values
8. Begin work
```

### Flow 3: User Says "focus on X"
```
1. Interpret X as intent
2. Create issue(s) in shortlist.md
3. Full schema, generated IDs
4. Update focus.md Next with first new issue
5. Report created issues
6. Wait for `continue` or begin
```

### Flow 4: Completing an Issue
```
1. Run validation
2. All pass → Mark completed
3. Move to history.md
4. Update focus.md:
   - Current → Previous
   - Next → Current
   - Select new → Next
5. LEARN: Investigate code, update memory.md
6. Report completion
7. Offer to continue with new Current
```

### Flow 5: Validation Fails
```
1. Analyze failures at FILE LEVEL
2. CREATE ISSUES FIRST for all regressions
3. Update focus.md status to "fixing-regressions"
4. Fix each regression issue
5. Re-validate
6. If still failing → Create more issues, repeat
7. When passing → Proceed to Complete
```

### Flow 6: Session Resume
```
1. Read focus.md (all three sections)
2. Previous tells you what just happened
3. Current tells you what to resume
4. Next tells you what's coming
5. Load relevant notes for Current
6. Check memory.md for context
7. Continue from documented state
```

---

## ⚠️ Anti-Patterns to Avoid

| Anti-Pattern | Correct Behavior |
|--------------|------------------|
| Making code changes before baseline | Generate baseline FIRST, no exceptions |
| Unclear about branch/commit state | Ask user before proceeding |
| Switching issues mid-work | Complete or explicitly park current issue |
| Skipping validation | Always validate before completion |
| Not updating focus.md | Update all three sections immediately |
| Focus.md missing Previous/Current/Next | All three must always exist |
| Putting temp data in memory.md | Use notes/ for temporary information |
| Regenerating baseline to pass | Fix regressions instead |
| Fixing regressions without creating issues first | CREATE ISSUES FIRST, then fix |
| Silent issue creation | Always report new issues to user |
| Ignoring memory.md | Check for relevant context each issue |
| Notes without issue reference | Always link notes to their issue |
| Updating memory before validation passes | LEARN phase comes after validation |
| Modifying shortlist autonomously | Only on explicit user instruction |
| Baseline without file-level detail | Must track warnings/errors by file |

---

## 📊 Success Metrics

An optimal iteration demonstrates:

- **Focus clarity:** Always know what's being worked on
- **No context loss:** Sessions resume seamlessly  
- **Zero regressions:** Validation catches all quality drops
- **Accumulated knowledge:** Memory grows with useful learnings
- **Clean state:** Notes archived, issues closed properly
- **User visibility:** Clear reporting at each phase

---

## 🎬 Example: Complete Iteration Transcript

```
User: continue

Agent:
[BASELINE CHECK]
Is this a new iteration? Checking baseline...
⚠️  No baseline found for current branch.

Generating baseline before any code changes...

✓ Build: passing (52s)
✓ Tests: 263/263 passing (127s)
✓ Coverage: 78.3%
✓ Lint: 0 errors, 12 warnings
  - src/config.py: 3 warnings (L5, L12, L45)
  - src/parser.py: 5 warnings (L23, L67, L89, L3, L8)
  - src/cli.py: 4 warnings (L34, L78, L92, L105)
✓ Types: 0 errors, 5 warnings
  - src/config.py: 2 warnings (L45, L72)
  - src/api.py: 3 warnings (L12, L34, L56)

Baseline generated: .work/baseline.md

[SELECT]
Reading focus.md...
  Previous: BUG-002@e5f6a7 (completed earlier)
  Current: None
  Next: ENHANCE-001@f7a2b3 (from shortlist)

Promoting Next to Current.
Selecting new Next: REFACTOR-001@a1b2c3 (from medium.md)

Updating focus.md:
  Previous: BUG-002@e5f6a7
  Current: ENHANCE-001@f7a2b3 (in-progress)
  Next: REFACTOR-001@a1b2c3

[INVESTIGATE]
Creating notes/enhance-001-investigation.md...

Analyzing src/dot_work/cli.py...
Checking baseline: cli.py has 4 pre-existing lint warnings.
Found 7 error messages to improve.

Checking memory.md... Found relevant entry:
  - "CLI errors should include: context, cause, fix"

Investigation complete. Proceeding to implementation.

[IMPLEMENT]
Updating focus.md phase: Implementation

Changes:
  - src/dot_work/cli.py: 7 error messages improved
  - tests/test_cli.py: 7 test cases added

[VALIDATE]
Running validation...

  Build: ✓ passing (48s)
  Tests: ✓ 270/270 (was 263, +7) (134s)
  Coverage: ✓ 79.8% (was 78.3%, +1.5%)
  Lint: ✓ 0 errors, 12 warnings (unchanged)
    - src/cli.py: still 4 warnings (no regression)
  Types: ✓ 0 errors, 5 warnings (unchanged)
  
File-level comparison:
  - src/cli.py: MODIFIED, warnings unchanged (4→4) ✓
  - tests/test_cli.py: NEW FILE, clean ✓
  - No regressions in any file

Result: PASS

[COMPLETE]
✓ Issue status → completed
✓ Moved to history.md
✓ Removed from shortlist.md
✓ Updated focus.md:
    Previous: ENHANCE-001@f7a2b3 (just completed)
    Current: REFACTOR-001@a1b2c3 (promoted from Next)
    Next: (selecting...)

[LEARN]
Investigating code for lessons...

Added to memory.md:
  - [ENHANCE-001@f7a2b3] 2024-01-15: Error message pattern:
    "Error: {what}\nContext: {where}\nFix: {how}"
  - [ENHANCE-001@f7a2b3] Click library has built-in error formatting
    helpers that could simplify future error handling.

Archived: notes/enhance-001-investigation.md → references/

─────────────────────────────────
COMPLETED: ENHANCE-001@f7a2b3
─────────────────────────────────

Improved 7 CLI error messages with user-friendly format.
Added 7 tests. Coverage improved to 79.8%.
No regressions. Lessons added to memory.

Now ready: REFACTOR-001@a1b2c3 (Current)
Up next: (will select when starting)

Say `continue` to proceed.
```

---

## 🎬 Example: Validation Failure Flow

```
[VALIDATE]
Running validation...

  Build: ✓ passing (48s)
  Tests: ✗ 268/270 (2 failures) (145s)
    - test_config_yaml FAILED
    - test_config_default FAILED
  Coverage: ⚠️ 77.8% (was 78.3%, -0.5%)
  Lint: ✗ 0 errors, 14 warnings (was 12, +2)
    - src/config.py: 5 warnings (was 3, +2 NEW)
      - NEW: W0612 unused variable 'temp' L52
      - NEW: W0611 unused import 'os' L3

File-level comparison:
  - src/config.py: REGRESSION (+2 lint warnings)
  - tests/test_config.py: REGRESSION (2 test failures)
  - Coverage: REGRESSION (-0.5%)

Result: FAIL - 4 regressions detected

⚠️ CREATING ISSUES FIRST...

Created:
  BUG-010@a1b2c3: Lint regressions in config.py (2 new warnings)
  BUG-011@b2c3d4: Test failures in test_config.py (2 failing tests)
  BUG-012@c3d4e5: Coverage regression (-0.5%)

Updating focus.md:
  Current: BUG-003@a9f3c2 (status: fixing-regressions)
  Regressions: BUG-010, BUG-011, BUG-012

Now fixing regressions...

[FIX BUG-010@a1b2c3]
Removing unused variable 'temp' from config.py:52...
Removing unused import 'os' from config.py:3...
✓ Fixed

[FIX BUG-011@b2c3d4]
Analyzing test failures...
test_config_yaml expects dict, getting list.
Fixed return type in config.py:67.
✓ Fixed

[FIX BUG-012@c3d4e5]
Coverage dropped due to new uncovered lines.
Adding test for config.py:52-55.
✓ Fixed

[RE-VALIDATE]
Running validation...

  Build: ✓ passing (49s)
  Tests: ✓ 271/271 (+1 new test) (138s)
  Coverage: ✓ 78.5% (was 78.3%, +0.2%)
  Lint: ✓ 0 errors, 12 warnings (back to baseline)

File-level comparison:
  - src/config.py: CLEAN (warnings fixed)
  - tests/test_config.py: PASSING
  - No regressions

Result: PASS

[COMPLETE]
Proceeding with completion...
```

---

## 📌 Final Notes

This workflow ensures:
- **Baseline-first**: No code changes until quality floor is established
- **Predictable behavior**: Same inputs produce same outputs
- **Quality maintenance**: File-level tracking prevents silent regressions
- **Knowledge accumulation**: Memory preserves learnings (after validation)
- **Session resilience**: Three-value focus enables clean resumption
- **Auditability**: Every action is documented with file references
- **Regression discipline**: Create issues first, then fix

**Critical Rules:**
1. BASELINE before ANY code changes
2. Ask about branch/commit if unclear
3. Focus.md has Previous/Current/Next (always)
4. Validation compares at FILE level
5. CREATE ISSUES before fixing regressions
6. LEARN phase comes AFTER validation passes

Follow this workflow for optimal autonomous operation.
