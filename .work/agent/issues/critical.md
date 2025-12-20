# Critical Issues (P0)

Blockers, security issues, data loss risks.

---

---
id: "TEST-002@d8c4e1"
title: "CLI has 0% test coverage - regressions go undetected"
description: "All 8 CLI commands were completely untested, now resolved"
created: 2024-12-20
completed: 2024-12-20
section: "tests"
tags: [testing, cli, regression, critical]
type: bug
priority: critical
status: completed
references:
  - src/dot_work/cli.py
  - tests/unit/test_cli.py
---

### Problem
The CLI module (`src/dot_work/cli.py`) had **0% test coverage** across all 403 lines. A regression occurred where `cli.py:212` referenced `__version__` that was removed in a previous fix (BUG-001). The regression was only caught by running the build, not by tests.

### Solution Implemented
Created comprehensive `tests/unit/test_cli.py` with 49 tests using `typer.testing.CliRunner`:

**Test Classes (11):**
1. `TestVersionCommand` - 4 tests (regression guard for BUG-001)
2. `TestHelpCommand` - 10 tests (all commands --help)
3. `TestListCommand` - 3 tests
4. `TestDetectCommand` - 4 tests
5. `TestInitWorkCommand` - 5 tests
6. `TestInstallCommand` - 5 tests
7. `TestInitCommand` - 2 tests
8. `TestValidateJsonCommand` - 7 tests
9. `TestValidateYamlCommand` - 5 tests
10. `TestEdgeCases` - 4 tests (integration)

### Results
| Metric | Before | After | Δ |
|--------|--------|-------|---|
| Tests | 180 | 229 | +49 |
| Coverage | 46% | 67% | +21% |
| CLI Coverage | 0% | 80% | +80% |

### Acceptance Criteria
- [x] `tests/unit/test_cli.py` created with CliRunner
- [x] Each of 8 commands has at least one test
- [x] `--version` command tested (regression guard)
- [x] CLI coverage ≥ 50% (achieved: 80%)
- [x] No regressions in existing tests

---
