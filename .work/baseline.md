# Project Baseline

**Captured:** 2024-12-21T14:30:00Z
**Commit:** c0868fe
**Branch:** main

---

## Scope Summary

- **Primary Language:** Python 3.10+
- **Package Manager:** uv
- **Build Tool:** scripts/build.py
- **Total Python Files:** 13 source files, 9 test files
- **Entry Points:** CLI via `dot-work` command
- **Version:** 0.1.1 (single source: pyproject.toml)

### Source Files
| File | Stmts | Purpose |
|------|-------|---------|
| src/dot_work/__init__.py | 0 | Package exports (no version) |
| src/dot_work/cli.py | 266 | CLI entry point (typer) + review commands |
| src/dot_work/environments.py | 12 | Environment configurations |
| src/dot_work/installer.py | 297 | Prompt installation + work dir initialization |
| src/dot_work/tools/__init__.py | 3 | Tools subpackage |
| src/dot_work/tools/json_validator.py | 109 | JSON validation |
| src/dot_work/tools/yaml_validator.py | 90 | YAML validation |
| src/dot_work/review/__init__.py | 2 | Review subpackage exports |
| src/dot_work/review/config.py | 15 | Config dataclass |
| src/dot_work/review/exporter.py | 53 | Export comments as markdown |
| src/dot_work/review/git.py | 109 | Git operations and diff parsing |
| src/dot_work/review/models.py | 33 | Pydantic data models |
| src/dot_work/review/server.py | 86 | FastAPI web server |
| src/dot_work/review/storage.py | 48 | JSONL comment storage |

## Build Status

- **Status:** ✓ passing
- **Execution Time:** 9.32s
- **Dependencies:** All synced

## Test Evidence

- **Total Tests:** 293
- **Passing:** 293
- **Failing:** 0
- **Skipped:** 0
- **Execution Time:** 6.55s

### Coverage Summary
- **Overall Coverage:** 66%
- **Required Threshold:** 15% (passing)

### Coverage by File
| File | Coverage | Uncovered Lines |
|------|----------|-----------------|
| src/dot_work/__init__.py | 100% | — |
| src/dot_work/cli.py | 69% | 73-75, 81-89, 216-240, 261, 333-335, 394-396, 441-452, 483-485, 502-517, 546-548, 553-555, 570-589, 597 |
| src/dot_work/environments.py | 100% | — |
| src/dot_work/installer.py | 41% | 21-36, 166, 186-210, 217-251, 258-284, 291-312, 319-337, 344-366, 373-390, 397-452, 459-491, 653-680 |
| src/dot_work/tools/__init__.py | 100% | — |
| src/dot_work/tools/json_validator.py | 92% | 35, 50, 130-136, 165, 192-193 |
| src/dot_work/tools/yaml_validator.py | 93% | 81, 134-140, 199 |
| src/dot_work/review/__init__.py | 100% | — |
| src/dot_work/review/config.py | 100% | — |
| src/dot_work/review/exporter.py | 100% | — |
| src/dot_work/review/git.py | 77% | 89-125, 141-150, 228-229, 292 |
| src/dot_work/review/models.py | 100% | — |
| src/dot_work/review/server.py | 0% | 3-193 |
| src/dot_work/review/storage.py | 98% | 91 |

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
| GAP-001 | CLI commands have 69% test coverage | cli.py |
| GAP-002 | install_for_* functions have low coverage | installer.py |
| GAP-003 | review/server.py has 0% test coverage | src/dot_work/review/server.py |

## Completed This Session

| ID | Description | Status |
|----|-------------|--------|
| MIGRATE-001→005,009 | Review module migration | ✓ Committed (21e5e0c) |
| MIGRATE-006 | Migrate unit tests (56 tests) | ✓ Committed (6315b32) |
| MIGRATE-011 | Add CLI tests (8 tests) | ✓ Committed (c0868fe) |

---

## Baseline Invariants

The following must not regress:

1. All 293 tests pass
2. Coverage >= 66%
3. Lint errors = 0
4. Type errors = 0
5. Security issues = 0
6. Build completes in < 15s
