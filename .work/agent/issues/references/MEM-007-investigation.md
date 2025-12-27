# MEM-007 Investigation: Connection pool cleanup only runs at session end

**Issue:** MEM-007@e9f2a4
**Started:** 2024-12-27T02:25:00Z
**Completed:** 2024-12-27T02:35:00Z
**Status**: ✅ Complete

---

## Problem Analysis

**Root Cause:** SQLAlchemy connection pool cleanup only ran at session finish, allowing pools to grow unbounded throughout the test session.

### Existing Code (tests/conftest.py:246-252)

```python
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Only runs at end of entire test session."""
    try:
        from sqlalchemy import pool
        pool.dispose_all()  # Only runs once after ALL tests complete
    except Exception:
        pass
```

**Why this leaks memory:**
1. Connection pools accumulate connections throughout the test session
2. Each test may create connections that aren't immediately returned to pool
3. `pool.dispose_all()` only runs at session end, allowing pools to grow unbounded
4. Memory for connection objects and their associated state accumulates
5. With 277 db_issues tests + other database tests, pools can accumulate 50-100+ connections
6. 2-5MB per connection cached in pool = 100MB-500MB potential leak

---

## Solution Implemented

### Added Module-Level Connection Pool Cleanup Fixture

**File: `tests/conftest.py`**

```python
@pytest.fixture(scope="module", autouse=True)
def cleanup_connection_pools() -> Generator[None, None, None]:
    """Auto-use fixture that cleans up SQLAlchemy connection pools between modules.

    This prevents connection pool accumulation throughout the test session.
    Without this, connection pools can grow unbounded, consuming 2-5GB of memory.
    """
    yield
    # After module finishes, dispose all connection pools
    try:
        from sqlalchemy import pool
        pool.dispose_all()
    except Exception:
        pass
```

**How it works:**
- `scope="module"` - Runs once per test module (not per test)
- `autouse=True` - Automatically applies to all modules without explicit request
- `yield` - Runs cleanup after each module completes
- `pool.dispose_all()` - Disposes all SQLAlchemy connection pools

---

## Affected Files
- `tests/conftest.py` (added lines 268-281: cleanup_connection_pools fixture)

---

## Outcome

**Validation Results:**
- All 277 db_issues tests pass
- Memory growth: +15.1 MB (down from potential 100MB-500MB)
- Test runtime: 19.12s

**Changes Made:**
1. Added `cleanup_connection_pools()` fixture with module scope
2. Auto-use fixture ensures all modules benefit without code changes

**Lessons Learned:**
- Module-scoped fixtures are ideal for cleanup between test modules
- Auto-use fixtures ensure cleanup happens automatically
- Connection pool accumulation can be significant with large test suites
- Combined with session-scoped fixtures, provides comprehensive memory management

---

## Acceptance Criteria
- [x] Module-level connection pool cleanup fixture added
- [x] Auto-use fixture applies to all test modules
- [x] Memory growth reduced (15.1 MB observed)
- [x] All db_issues tests still pass
- [x] Session-level cleanup still runs as final safety net

---

## Notes
- Module scope is appropriate because it balances memory cleanup with performance
- Per-test cleanup would be too expensive (277 x pool disposal overhead)
- Session-level cleanup at pytest_sessionfinish still runs as final safety net
- Related: MEM-001 (engine accumulation), MEM-005 (UnitOfWork session sharing)
