# Critical Issues (P0)

Blockers, security issues, data loss risks.

---

---
id: "TEST-002@d8c4e1"
title: "CLI has 0% test coverage - regressions go undetected"
description: "All 8 CLI commands are completely untested, causing regressions"
created: 2024-12-20
section: "tests"
tags: [testing, cli, regression, critical]
type: bug
priority: critical
status: proposed
references:
  - src/dot_work/cli.py
  - tests/unit/test_cli.py (to create)
---

### Problem
The CLI module (`src/dot_work/cli.py`) has **0% test coverage** across all 403 lines. This session, a regression occurred where `cli.py:212` referenced `__version__` that was removed in a previous fix (BUG-001). The regression was only caught by running the build, not by tests.

### Evidence of Risk
- **BUG-001 regression**: CLI broke because `__version__` was removed but CLI still imported it
- **Zero coverage**: Lines 3-403 are entirely untested per baseline.md
- **8 untested commands**: `install`, `list`, `detect`, `init`, `init-work`, `validate json`, `validate yaml`, `--version`

### Impact
- User-facing commands can break silently
- Regressions discovered late (by users, not tests)
- Blocks confident refactoring of CLI code

### Proposed Solution
Create `tests/unit/test_cli.py` using `typer.testing.CliRunner`:

1. **Smoke tests** for each command (exits 0, produces expected output)
2. **--version test** (would have caught this session's regression)
3. **--help test** for each command
4. **Error path tests** (invalid env, missing file, etc.)

### Acceptance Criteria
- [ ] `tests/unit/test_cli.py` created with CliRunner
- [ ] Each of 8 commands has at least one test
- [ ] `--version` command tested (regression guard)
- [ ] CLI coverage ≥ 50%
- [ ] No regressions in existing tests

### Priority Justification
Elevated to P0 because:
1. Regression already occurred this session
2. Core user interface is completely unguarded
3. Blocks other work (refactoring, new features)

### Notes
This complements TEST-001 (installer tests) but focuses specifically on CLI entry points. May be merged with TEST-001 during implementation.

---
