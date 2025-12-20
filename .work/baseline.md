# Project Baseline

**Captured:** 2024-12-20T19:55:00Z
**Commit:** pending (unstaged changes)
**Branch:** main

---

## Scope Summary

- **Primary Language:** Python 3.10+
- **Package Manager:** uv
- **Build Tool:** scripts/build.py
- **Total Python Files:** 7 source files, 4 test files
- **Entry Points:** CLI via `dot-work` command
- **Version:** 0.1.1 (single source: pyproject.toml)

### Source Files
| File | Stmts | Purpose |
|------|-------|---------|
| src/dot_work/__init__.py | 0 | Package exports (no version) |
| src/dot_work/cli.py | 185 | CLI entry point (typer) |
| src/dot_work/environments.py | 12 | Environment configurations |
| src/dot_work/installer.py | 297 | Prompt installation + work dir initialization |
| src/dot_work/tools/__init__.py | 3 | Tools subpackage |
| src/dot_work/tools/json_validator.py | 109 | JSON validation |
| src/dot_work/tools/yaml_validator.py | 90 | YAML validation |

## Build Status

- **Status:** ✓ passing
- **Execution Time:** 4.55s
- **Dependencies:** All synced

## Test Evidence

- **Total Tests:** 180
- **Passing:** 180
- **Failing:** 0
- **Skipped:** 0
- **Execution Time:** 1.96s

### Coverage Summary
- **Overall Coverage:** 46%
- **Required Threshold:** 15% (passing)

### Coverage by File
| File | Coverage | Uncovered Lines |
|------|----------|-----------------|
| src/dot_work/__init__.py | 100% | — |
| src/dot_work/cli.py | 0% | 3-403 (entire file) |
| src/dot_work/environments.py | 100% | — |
| src/dot_work/installer.py | 41% | 21-36, 166, 186-491, 653-680 (install_for_* + some context) |
| src/dot_work/tools/__init__.py | 100% | — |
| src/dot_work/tools/json_validator.py | 92% | 35, 50, 130-136, 165, 192-193 |
| src/dot_work/tools/yaml_validator.py | 92% | 81, 134-140, 196, 199 |

## Linting

- **Total Errors:** 0
- **Total Warnings:** 0
- **Tool:** ruff 0.14.10

## Type Checking

- **Total Errors:** 0
- **Total Warnings:** 0
- **Tool:** mypy 1.19.1

## Security

- **Critical:** 0
- **High:** 0
- **Medium:** 0

## Known Gaps

| ID | Description | Location |
|----|-------------|----------|
| GAP-001 | CLI commands have 0% test coverage | cli.py |
| GAP-002 | install_for_* functions have low coverage | installer.py |

## Completed This Session

| ID | Description | Status |
|----|-------------|--------|
| FEAT-003@a3f7c2 | --force flag implementation | ✓ Completed |
| BUG-001@c5e8f1 | Version mismatch fix | ✓ Completed |
| FEAT-004@b8e1d4 | init-work CLI command | ✓ Completed |

---

## Baseline Invariants

The following must not regress:

1. All 180 tests pass
2. Coverage ≥ 46%
3. Lint errors = 0
4. Type errors = 0
5. Security issues = 0
6. Build completes in < 10s
