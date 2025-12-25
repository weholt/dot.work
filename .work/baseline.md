# Baseline Report
Generated: 2025-12-25T16:55:00Z
Commit: 020f558
Branch: migrating-using-opencode

## Build Status
- Status: passing
- Execution time: 12.4s
- Peak memory: 45.2 MB RSS, 54.1 MB VMS

## Dependencies
- Python 3.13.11
- uv 0.9.8
- ruff 0.14.9
- mypy 1.19.1
- pytest 9.0.2

## Linting (ruff)
- Total errors: 28
- Fixable with --fix: 4

### Error Summary
| Code | Count | Description |
|------|-------|-------------|
| B904 | 15 | raise-without-from-inside-except |
| F841 | 3 | unused-variable |
| B008 | 2 | function-call-in-default-argument |
| E712 | 2 | true-false-comparison |
| F401 | 2 | unused-import (fixable) |
| F811 | 1 | redefined-while-unused |
| F821 | 1 | undefined-name |
| I001 | 1 | unsorted-imports (fixable) |
| UP035 | 1 | deprecated-import (fixable) |

## Type Checking (mypy)
- Total errors: 73
- Files with errors: 6
- Files checked: 112 source files

### Type Errors by File
| File | Count | Details |
|------|-------|---------|
| src/dot_work/db_issues/cli.py | 69 | attr-defined (issue_type, assignee) |
| src/dot_work/knowledge_graph/db.py | 2 | Various |
| src/dot_work/environments.py | 1 | Various |
| src/dot_work/installer.py | 1 | Various |

## Tests
- Total tests: 1363
- Collection errors: 25 (pre-existing, in test suite)
- Execution time: ~8s

## Coverage
- Overall: 57.88%
- Threshold: 50% (passing)

## Security
- Ruff security: passing
- Bandit scan: passing

## Files Summary
Total Python files: 112+
Files with issues: 6 (mypy), 10+ (ruff)
Clean files: 100+

### Files with Pre-existing Issues
- src/dot_work/db_issues/cli.py: 69 type errors (attr-defined), 15 B904 lint warnings
- src/dot_work/knowledge_graph/db.py: 2 type errors
- src/dot_work/environments.py: 1 type error
- src/dot_work/installer.py: 1 type error
