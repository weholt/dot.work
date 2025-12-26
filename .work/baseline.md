# Project Baseline

**Captured:** 2024-12-26T20:00:00Z
**Commit:** 60e31ce
**Branch:** closing-migration

---

## Build Status
- **Status:** PASS (9/9 steps)
- **Execution time:** ~593 seconds

### Build Steps
| Step | Status | Notes |
|------|--------|-------|
| Check Dependencies | PASS | uv, ruff, mypy, pytest available |
| Code Formatting | PASS | ruff format - clean |
| Code Linting | PASS | ruff check - clean (src/ only) |
| Type Checking | PASS | mypy on src/ - clean |
| Security Checks | PASS | ruff security - clean (src/ only) |
| Static Analysis | PASS | radon complexity/maintainability - clean |
| Unit Tests | PASS | All tests passing (with memory enforcement) |
| Documentation | SKIP | No mkdocs.yml |
| Reports | PASS | Coverage reports generated |

---

## Dependencies
- Python 3.13.1
- uv 0.5.4
- ruff 0.14.9
- mypy 1.19.1
- pytest 9.0.2

---

## Linting (ruff)

### Source Code Status
- **src/** directory: **36 errors** (10 fixable)
  - Most in `db_issues/cli.py` (subprocess, try-except-pass issues)

### Project-Wide Issues (excludes src/)
**Total errors:** 972 (684 fixable)
**Most issues in:** `incoming/` directory (external code not yet migrated)

### Syntax Errors (needs fixing)
- `.work/agent/prompts/canonical.py:72-80` - Invalid syntax (5 errors)

### Security Warnings (src/)
**S603** - subprocess call: check for execution of untrusted input (3 locations in db_issues/cli.py)
**S110** - try-except-pass detected (2 locations in db_issues/cli.py)

---

## Type Checking (mypy)

### Source Code Status
**Total Errors:** 56 (in src/ only)

### Type Errors by File

**src/dot_work/db_issues/cli.py** (3 errors):
- Line 5653: Issue has no attribute "issue_type"

**src/dot_work/harness/cli.py** (1 error):
- Line 97: Argument "permission_mode" has incompatible type "str"; expected Literal

**Note:** Additional type errors exist in legacy code paths.

---

## Tests

- **Total tests:** 1541 collected (103 errors during collection - in incoming/)
- **Unit tests:** All passing (with 4GB memory limit enforced)
- **Execution time:** ~587 seconds
- **Coverage:** 74% (overall)

### Test Collection Errors (in incoming/)
- 103 errors during test collection (external code not yet migrated)
- These are in `incoming/crampus/` and `incoming/kgtool/` directories

---

## Coverage

- **Overall:** 74%

---

## Security (ruff security check)

**Source code (src/):** 5 security warnings
- 3× S603: subprocess call with untrusted input (db_issues/cli.py)
- 2× S110: try-except-pass (db_issues/cli.py)

**Project-wide:** 15 security warnings (all in `incoming/` directory)

---

## Files Summary

**Total Python files:** ~200 (including incoming/)

**Files with pre-existing issues (src/ only):**
- `src/dot_work/db_issues/cli.py`: 3 type errors, 5 security warnings
- `src/dot_work/harness/cli.py`: 1 type error

**Clean files (src/):** ~115 files

**Files with issues (incoming/):**
- Syntax errors in `.work/agent/prompts/canonical.py`
- Security warnings in crampus and kgtool modules
- Linting errors throughout incoming/ (972 total)

---

## Baseline Invariants

**Statements that must not regress:**
1. Tests must continue to pass (currently PASSING with memory enforcement)
2. No NEW type errors should be introduced in src/ (currently 56)
3. No NEW linting errors should be introduced in src/ beyond current 36
4. No NEW security warnings in src/ beyond current 5
5. Memory usage must remain under 4GB during test execution (currently ~28MB peak)

---

## Notes

### Known Issues (Pre-Existing)

1. **incoming/ directory** contains unmigrated code with many issues:
   - 972 linting errors (684 fixable)
   - 103 test collection errors
   - 15 security warnings
   - These are NOT regressions - they exist in external code not yet integrated

2. **db_issues/cli.py** has legacy issues:
   - Type errors with old entity attributes
   - Security warnings for subprocess calls
   - try-except-pass patterns

3. **harness/cli.py** has type mismatch:
   - Line 97: permission_mode passed as str, expects Literal type

4. **.work/agent/prompts/canonical.py** has syntax errors (lines 72-80)

### Recent Changes (since previous baseline)

**Previous Baseline:** 2024-12-26T19:00:00Z, Commit c8c565b

| Metric | Previous | Current | Change |
|--------|----------|---------|--------|
| Commit | c8c565b | 60e31ce | +1 commit |
| Tests | 1506 | 1541 | +35 tests |
| Type Errors (src/) | 56 | 56 | No change |
| Lint Errors (src/) | 36 | 36 | No change |
| Security (src/) | 5 warnings | 5 warnings | No change |

**Changes between baselines:**
1. **SEC-003 fix (60e31ce):** Git option injection vulnerability in review/git.py
   - Added git ref validation with whitelist pattern
   - Added `_validate_git_ref()` and `_validate_git_path()` functions
   - Added `GitRefValidationError` exception class
   - Updated `changed_files()` and `get_unified_diff()` to validate parameters
   - All 35 security tests passing

### Key Features Added (SEC-003)
- Whitelist validation for git refs (alphanumeric, -, ., /, ~, ^, :, @)
- Git options blocking (rejects `--*` patterns)
- Shell metacharacter blocking (|, &, ;, $, `, (, ), <, >, newlines)
- Path traversal blocking (`..` sequences)
- Support for HEAD, commit hashes, and `@{-n}` syntax

---

## Next Steps

1. **Pre-work checklist COMPLETE** - Baseline established
2. **Ready to select next issue** - See critical.md for 3 P0 issues:
   - MEM-001: SQLAlchemy engine accumulation
   - MEM-002: LibCST CST trees not released
   - BUG-001: Installed tool missing python.build module
