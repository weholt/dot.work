# Baseline Report
Generated: 2024-12-23T17:45:00Z
Commit: 7a87454
Branch: migrating-using-opencode

## Build Status
- Status: passing
- Execution time: ~125s

## Dependencies
- Python 3.13.11
- pytest 9.0.2
- uv package manager

## Linting
- Total errors: 851 (pre-existing)
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
| B904 | 7 | raise-without-from-inside-except (db_issues) |
| S603 | 2 | subprocess-without-shell-equals-true (db_issues) |
| S110 | 2 | try-except-pass (db_issues) |

### db_issues Specific Issues
Pre-existing issues in `src/dot_work/db_issues/`:
- B904: 7 locations (exception chaining)
- S603: 1 location (subprocess call)
- S110: 2 locations (try-except-pass)

Note: Most errors are style-related and pre-existing. Can run `uv run ruff check --fix` to auto-fix 598 errors.

## Type Checking
- Total errors: 0
- Total warnings: 0
- Status: passing (87+ source files)

## Tests
- Unit tests: 1188 passed, 0 failed
- Integration tests: 14 passed, 0 failed
- Total: 1202 collected, 1202 passing
- Execution time: ~115s

### Test Status
All tests passing ✓ (including 31 new tests from MIGRATE-054 Bulk Operations)

### Test Files Added (MIGRATE-054)
- `tests/unit/db_issues/test_bulk_service.py` - 31 tests

## Coverage
- Overall: 57.88%

### Coverage by File
| File | Coverage | Uncovered Lines |
|------|----------|----------------|
| src/dot_work/db_issues/services/bulk_service.py | 92% | 30-40 |
| src/dot_work/db_issues/services/label_service.py | 85% | 110-130 |

## Security
- No security scanning in this build

## Files Summary
Total Python files: 87+
Build status: passing
Test status: all passing
Type checking: passing

### Recent Additions (MIGRATE-054)
- `src/dot_work/db_issues/services/bulk_service.py` (517 lines)
- `src/dot_work/db_issues/cli.py` - bulk commands
- `tests/unit/db_issues/test_bulk_service.py` (472 lines)

### Pre-existing Issues to Address
- Linting: 851 errors (598 auto-fixable)
- db_issues specific: 7 B904, 2 S110, 1 S603

## Invariant for db-issues Migration
During MIGRATE-034 through MIGRATE-085:
- Create new module: `src/dot_work/db_issues/`
- Do NOT introduce new critical errors (undefined-name, invalid-syntax)
- Do NOT break the 1202 passing tests
- Keep mypy errors at 0
- New files should be clean (no new mypy warnings)

## Migration Progress
- Completed: MIGRATE-034 through MIGRATE-054 (21 issues)
- In Progress: MIGRATE-055 (Bulk Label Operations)
- Remaining: MIGRATE-056 through MIGRATE-085 (30 issues)
