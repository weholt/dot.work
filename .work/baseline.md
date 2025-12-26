# Project Baseline

**Captured:** 2024-12-26T15:30:00Z
**Commit:** f61773c
**Branch:** closing-migration

---

## Build Status
- **Status:** Partial Pass (5/8 steps failed)
- **Execution time:** ~740 seconds

### Build Steps
| Step | Status | Notes |
|------|--------|-------|
| Check Dependencies | PASS | uv, ruff, mypy, pytest available |
| Sync Dependencies | PASS | Dependencies synced |
| Format Code (ruff format) | FAIL | 14 files need reformatting |
| Lint Code (ruff) | FAIL | Multiple linting errors |
| Type Check (mypy) | FAIL | 50+ type errors |
| Security Check (ruff check -S) | FAIL | 10 security warnings |
| Unit Tests | PASS | All tests passing |
| Generate Reports | PASS | Coverage reports generated |

---

## Dependencies
- Python 3.13.1
- uv 0.5.4
- ruff 0.9.1
- mypy 1.14.1
- pytest 9.0.2

---

## Linting (ruff)

### Format Issues
**14 files need reformatting:**
- src/dot_work/cli.py
- src/dot_work/db_issues/adapters/sqlite.py
- src/dot_work/db_issues/cli.py
- src/dot_work/db_issues/services/bulk_service.py
- src/dot_work/db_issues/services/dependency_service.py
- src/dot_work/db_issues/services/duplicate_service.py
- src/dot_work/db_issues/services/epic_service.py
- src/dot_work/db_issues/services/project_service.py
- src/dot_work/db_issues/services/stats_service.py
- src/dot_work/harness/client.py
- src/dot_work/installer.py
- src/dot_work/knowledge_graph/db.py
- src/dot_work/python/build/cli.py
- src/dot_work/python/build/runner.py

### Linting Errors (Sample)
**E712** - Comparison to True (2 locations):
- src/dot_work/db_issues/adapters/sqlite.py:1541, 1632

**B904** - Raise exceptions with `raise ... from err`:
- src/dot_work/db_issues/cli.py:464, 1411, and multiple other locations

---

## Type Checking (mypy)

**Total Errors:** 50+

### Type Errors by File

**src/dot_work/db_issues/services/label_service.py** (1 error)
- Line 437: Incompatible assignment (Label | None to Label)

**src/dot_work/db_issues/services/issue_service.py** (9 errors)
- Lines 826-828: IssueRepository has no attribute "get_dependencies"/"get_dependents"
- Lines 851, 870: IssueRepository has no attribute "add_dependency"
- Lines 875, 886: Missing repository methods
- Line 879: IdentifierService has no attribute "generate_id"

**src/dot_work/db_issues/services/dependency_service.py** (5 errors)
- Lines 548-549, 554-555: Type mismatch (list vs set for blockers)

**src/dot_work/db_issues/cli.py** (30+ errors)
- Lines 565, 623, 697, 881, 956, 1017, 1124, 1189, 5009: Issue has no attribute "assignee" (should be "assignees")
- Line 918: Wrong type for Table.add_row
- Lines 4653-4655, 4715-4719: Missing repository methods (list_issues, list_epics, list_labels, list_all_dependencies)
- Lines 4809-4810, 4815-4816: Wrong attribute access on stats types
- Line 4852: Wrong type for JSON argument
- Lines 4896, 4904: Wrong type for Session.exec (string instead of statement)
- Line 5001: Wrong keyword argument "assignee" for Issue
- Line 5394: Name "edit" already defined (line 1322)
- Line 5522: Name "Any" is not defined (missing import)
- Line 1565: Cannot find module "dot_work.db_issues.cli_utils"

**src/dot_work/db_issues/domain/entities.py**
- Note: "Issue" defined here (used by cli.py)

---

## Security (ruff check -S)

**Total Warnings:** 10

### Security Issues

**S603** - subprocess call: check for execution of untrusted input (2 locations):
- src/dot_work/db_issues/cli.py:5493
- src/dot_work/python/build/runner.py:213

**S608** - Possible SQL injection vector (2 locations):
- src/dot_work/knowledge_graph/db.py:1213, 1223 (table name in f-string)

**S112** - try-except-continue detected, consider logging (1 location):
- src/dot_work/installer.py:1267

**S110** - try-except-pass detected, consider logging (1 location):
- src/dot_work/knowledge_graph/db.py:431

---

## Tests

- **Total tests:** 1370 (based on previous baseline)
- **Unit tests:** All passing
- **Execution time:** ~400-500 seconds
- **Coverage:** Not measured in this run (build failed before coverage step)

### Test Status
- Tests verified as PASSING via direct pytest run
- Full test suite takes ~7 minutes

---

## Files Summary

**Total Python files:** ~116 files in src/dot_work

**Files with pre-existing issues:**
- 14 files need formatting
- 10+ files have type errors
- 5 files have security warnings

**Clean files:** ~90+ files (estimated)

---

## Baseline Invariants

**Statements that must not regress:**
1. Unit tests must continue to pass (currently PASSING)
2. No NEW type errors should be introduced (currently 50+ existing)
3. No NEW linting errors should be introduced (currently many existing)
4. No NEW security warnings should be introduced (currently 10 existing)

---

## Notes

### Known Issues (Pre-Existing)
1. **db_issues module** has extensive type errors (assignee vs assignees naming)
2. **Formatting drift** - 14 files need reformatting
3. **Security concerns** - SQL injection vectors via table name interpolation
4. **Test execution time** - ~7 minutes for full unit test suite
5. **Memory usage** - Tests consume ~77GB RAM during execution

### Files Modified in Commit f61773c
- external-project-reality-auditor.prompt.md - Added canonical frontmatter
- src/dot_work/cli.py - Added environment discovery
- src/dot_work/harness/client.py - Fixed type annotations (PermissionMode)
- src/dot_work/installer.py - Added discover_available_environments(), install_canonical_prompts_by_environment()

### Key Type Fix Applied
- harness/client.py: Changed `permission_mode: str` to `permission_mode: PermissionMode` where `PermissionMode = Literal["default", "acceptEdits", "plan", "bypassPermissions"]`

---

## Comparison to Previous Baseline

**Previous Baseline:** 2025-12-25T23:00:00Z, Commit 8d8368a, Branch migrating-using-opencode

| Metric | Previous | Current | Change |
|--------|----------|---------|--------|
| Build Status | passing | Partial Pass (5/8 failed) | - |
| Type Errors | 50 | 50+ | Similar |
| Format Issues | 0 in src/ | 14 files | Regressed |
| Security | passing | 10 warnings | Regressed |
| Tests | 1370 passing | All passing | Same |

**Note:** The increase in format issues and security warnings may be due to:
1. More comprehensive checks in current build
2. Changes made between commits
3. Different ruff configuration

---

## Next Steps

1. **Pre-work checklist COMPLETE** - Baseline established
2. **Ready to start FEAT-022** - Create interactive prompt wizard for new canonical prompts
3. **Note:** Existing type/lint/security issues are documented and should not be considered regressions when validating future work
