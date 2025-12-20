# Project Baseline

**Captured:** 2024-12-20T16:27:00Z
**Commit:** 92a3cbb
**Branch:** main

---

## Scope Summary

- **Primary Language:** Python 3.10+
- **Package Manager:** uv
- **Build Tool:** scripts/build.py
- **Total Python Files:** 7 source files, 4 test files
- **Entry Points:** CLI via `dot-work` command

### Source Files
| File | Lines | Purpose |
|------|-------|---------|
| src/dot_work/__init__.py | 3 | Package exports |
| src/dot_work/cli.py | 174 stmts | CLI entry point (typer) |
| src/dot_work/environments.py | 12 stmts | Environment configurations |
| src/dot_work/installer.py | 177 stmts | Prompt installation logic |
| src/dot_work/tools/__init__.py | 3 stmts | Tools subpackage |
| src/dot_work/tools/json_validator.py | 109 stmts | JSON validation |
| src/dot_work/tools/yaml_validator.py | 90 stmts | YAML validation |

## Build Status

- **Status:** ✓ passing
- **Execution Time:** 3.98s
- **Dependencies:** All synced

## Test Evidence

- **Total Tests:** 156
- **Passing:** 156
- **Failing:** 0
- **Skipped:** 0
- **Execution Time:** 1.72s

### Coverage Summary
- **Overall Coverage:** 41%
- **Required Threshold:** 15% (passing)

### Coverage by File
| File | Coverage | Uncovered Lines |
|------|----------|-----------------|
| src/dot_work/__init__.py | 100% | — |
| src/dot_work/cli.py | 0% | 3-364 (entire file) |
| src/dot_work/environments.py | 100% | — |
| src/dot_work/installer.py | 19% | 21-36, 114-391 (all install_for_* functions) |
| src/dot_work/tools/__init__.py | 100% | — |
| src/dot_work/tools/json_validator.py | 92% | 35, 50, 130-136, 165, 192-193 |
| src/dot_work/tools/yaml_validator.py | 92% | 81, 134-140, 196, 199 |

## Linting

- **Total Errors:** 0
- **Total Warnings:** 0
- **Tool:** ruff 0.14.10

### Warnings by File
(No warnings - all files clean)

## Type Checking

- **Total Errors:** 0
- **Total Warnings:** 0
- **Tool:** mypy 1.19.1

### Type Warnings by File
(No warnings - all files clean)

## Security

- **Critical:** 0
- **High:** 0
- **Medium:** 0
- **Tool:** ruff security checks (--select S)

## Known Gaps

| ID | Description | Location |
|----|-------------|----------|
| GAP-001 | CLI commands have 0% test coverage | cli.py |
| GAP-002 | install_for_* functions have 19% coverage | installer.py |
| GAP-003 | --force flag documented but not implemented | cli.py:55-60 |
| GAP-004 | init-work command documented in prompts but not implemented | cli.py |

## Documentation Status

- **README.md:** Current
- **AGENTS.md:** Current
- **Prompt files:** 8 prompts in src/dot_work/prompts/

## Unknowns

- UNK-001: Windows-specific path handling not tested in CI
- UNK-002: Performance with large prompt files (>1MB) not verified

---

## Baseline Invariants

The following must not regress:

1. All 156 tests pass
2. Coverage ≥ 41%
3. Lint errors = 0
4. Type errors = 0
5. Security issues = 0
6. Build completes in < 10s
