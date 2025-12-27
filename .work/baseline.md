# Project Baseline

**Captured:** 2024-12-26T23:10:00Z
**Commit:** 95b0765
**Branch:** closing-migration

---

## Build Status
- **Status:** PASS (9/9 steps)
- **Execution time:** ~30 seconds

### Build Steps
| Step | Status | Notes |
|------|--------|-------|
| Check Dependencies | PASS | uv, ruff, mypy, pytest available |
| Code Formatting | PASS | ruff format - clean |
| Code Linting | PASS | ruff check - clean |
| Type Checking | PASS | mypy on src/ - clean |
| Security Checks | PASS | ruff security - clean |
| Static Analysis | PASS | radon complexity/maintainability - clean |
| Unit Tests | PASS | 1434 tests collected (all passing) |
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
- **src/** directory: **Clean** (0 errors)
- **Project-wide:** Clean (excluding incoming/)

---

## Type Checking (mypy)

### Source Code Status
**Total Errors:** 0 (clean)

---

## Tests

- **Total tests:** 1434 collected
- **All tests:** Passing
- **Execution time:** ~25 seconds
- **Coverage:** ≥70%
- **Memory limit:** 4GB enforced via cgroup v2

### Memory Performance
- Peak memory: 29.5 MB RSS, 36.3 MB VMS
- Memory enforcement: ENABLED (systemd-run with MemoryMax=4096M)

---

## Coverage

- **Overall:** ≥70% (threshold met)

---

## Security (ruff security check)

**Source code:** Clean

---

## Files Summary

**Total Python files:** 118 (in src/)

**Clean files:** All files passing

**Files with pre-existing issues:**
- None (all clean)

---

## Baseline Invariants

**Statements that must not regress:**
1. Tests must continue to pass (currently PASSING - 1434 tests)
2. No type errors (currently 0)
3. No linting errors (currently 0)
4. No security warnings (currently 0)
5. Memory usage must remain under 4GB during test execution (currently ~29.5 MB baseline)

---

## Notes

### Recent Changes (since previous baseline)

**Previous Baseline:** 2024-12-26T21:40:00Z, Commit 47e1b6a

| Metric | Previous | Current | Change |
|--------|----------|---------|--------|
| Commit | 47e1b6a | 95b0765 | +2 commits |
| Tests | 1396 | 1434 | +38 tests |
| Type Errors (src/) | 56 | 0 | CLEANED |
| Lint Errors (src/) | 36 | 0 | CLEANED |
| Security (src/) | 5 warnings | 0 | CLEANED |

**Changes between baselines:**

**All Source Code Issues Resolved:**

1. **CR-009 fix (95b0765):** Module naming conflict in dot_work.python.build
   - Created `__main__.py` in dot_work/python/build/ directory
   - Eliminates RuntimeWarning when running `python -m dot_work.python.build`
   - Proper Python package module execution pattern per PEP 338

2. **Type and lint cleanup:** All 56 type errors and 36 lint errors resolved
   - Source code is now completely clean
   - Ready for production development

---

## Next Steps

1. **All critical and code quality issues COMPLETE**
2. **Source code is clean** - Ready for feature development
3. **Memory management solid** - 4GB enforcement working correctly
4. **Resume PERF-002 investigation** - File scanner performance optimization
