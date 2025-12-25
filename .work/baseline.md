# Baseline Report
Generated: 2025-12-25T23:00:00Z
Commit: 8d8368a
Branch: migrating-using-opencode

## Build Status
- Status: passing
- Execution time: 28.38s
- Peak memory: 27.4 MB RSS, 34.1 MB VMS
- Test memory: Baseline 37.5 MB, Final 109.6 MB, Growth: +72.1 MB

## Dependencies
- Python 3.13.1
- uv 0.5.4
- ruff 0.9.1
- mypy 1.14.1
- pytest 9.0.2

## Linting (ruff)
- Total errors (all): 962 (677 fixable with --fix)
- Errors in src/: **0**
- Errors in incoming/: 962 (pre-existing, legacy code)
- Fixable with --fix: 677

### Error Summary (all files)
| Code | Count | Description |
|------|-------|-------------|
| UP006 | 239 | non-pep585-annotation |
| F401 | 143 | unused-import |
| UP045 | 84 | non-pep604-annotation-optional |
| I001 | 72 | unsorted-imports |
| UP035 | 61 | deprecated-import |
| W293 | 61 | blank-line-with-whitespace |
| B904 | 33 | raise-without-from-inside-except |
| W292 | 32 | missing-newline-at-end-of-file |
| F541 | 31 | f-string-missing-placeholders |
| F841 | 26 | unused-variable |

## Type Checking (mypy)
- Total errors in src/: **50**
- Files with errors in src/: 3
- Files checked: 112 source files

### Type Errors by File (src/ only)
| File | Count | Details |
|------|-------|---------|
| src/dot_work/db_issues/cli.py | 37 | attr-defined (assignee), call-overload (exec), no-redef |
| src/dot_work/db_issues/services/issue_service.py | 9 | attr-defined (get_dependencies, add_dependency, add_comment, generate_id) |
| src/dot_work/db_issues/services/dependency_service.py | 4 | assignment (list vs set for blockers) |
| src/dot_work/db_issues/services/label_service.py | 1 | assignment (Label | None to Label) |
| src/dot_work/installer.py | 4 | assignment (tuple with None to tuple[str, str, str]) |

## Tests
- Total tests: 1370
- Collection errors: 25 (all in incoming/kg/tests/ - pre-existing)
- Execution time: ~25s
- Memory enforced: 4GB limit via cgroup v2

## Coverage
- Overall: 57.9%
- Threshold: 50% (passing)

## Security
- Ruff security: passing
- Bandit scan: passing

## Files Summary
Total Python files: 112+
Files with issues in src/: 3 (mypy only)
Clean files in src/: 100+

### Files with Pre-existing Issues (src/ only)
- src/dot_work/db_issues/cli.py: 37 type errors (attr-defined, call-overload, no-redef)
- src/dot_work/db_issues/services/issue_service.py: 9 type errors (attr-defined)
- src/dot_work/db_issues/services/dependency_service.py: 4 type errors (assignment)
- src/dot_work/db_issues/services/label_service.py: 1 type error (assignment)
- src/dot_work/installer.py: 4 type errors (assignment)

### Clean Files (src/ only)
All other src/ files are clean (no lint or type errors)
