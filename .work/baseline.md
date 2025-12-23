# Baseline Report
Generated: 2024-12-23T09:30:00Z
Commit: ab43b59
Branch: migrating-using-opencode

## Build Status
- Status: passing
- Execution time: ~120s

## Dependencies
- Python 3.13.11
- pytest 9.0.2
- uv package manager

## Linting
- Total errors: 840
- Fixable with --fix: 598
- Critical errors (undefined-name, invalid-syntax): 16

### Error Summary
| Code | Count | Description |
|------|-------|-------------|
| UP006 | 239 | non-pep585-annotation |
| F401 | 93 | unused-import |
| UP045 | 84 | non-pep604-annotation-optional |
| I001 | 63 | unsorted-imports |
| W293 | 61 | blank-line-with-whitespace |
| UP035 | 53 | deprecated-import |

Note: Most errors are style-related and pre-existing. Can run `uv run ruff check --fix` to auto-fix 598 errors.

## Type Checking
- Total errors: 0
- Total warnings: 0
- Status: passing (87 source files)

## Tests
- Unit tests: 1027 passed, 0 failed
- Integration tests: 33 passed, 0 failed
- Total: 1060 collected, 1027 selected
- Execution time: ~90s

### Test Status
All tests passing ✓

## Coverage
- Not measured in this build run

## Security
- No security scanning in this build

## Files Summary
Total Python files: 87
Build status: passing
Test status: all passing
Type checking: passing

### Pre-existing Issues to Address
- Linting: 840 errors (598 auto-fixable)
- Tests: All passing now (version module tests fixed in previous work)

## Invariant for db-issues Migration
During MIGRATE-034 through MIGRATE-085:
- Create new module: `src/dot_work/db_issues/`
- Do NOT introduce new critical errors (undefined-name, invalid-syntax)
- Do NOT break the 1060 passing tests
- Keep mypy errors at 0
- New files should be clean (no new mypy warnings)
