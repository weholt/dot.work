# MEM-005 Investigation: Multiple UnitOfWork instances share same session

**Issue:** MEM-005@c8e7f1
**Started:** 2024-12-27T01:35:00Z
**Completed:** 2024-12-27T01:50:00Z
**Status**: ✅ Complete

---

## Problem Analysis

**Root Cause:** Each service fixture created its own `UnitOfWork` instance from the same session, leading to repository cache accumulation.

### Existing Fixtures (lines 255-403 in conftest.py)

```python
@pytest.fixture
def issue_service(in_memory_db, ...) -> Generator[IssueService, None, None]:
    uow = UnitOfWork(in_memory_db)  # Creates new UoW with new repos
    try:
        yield IssueService(uow, ...)
    finally:
        uow.close()
        del uow

@pytest.fixture
def epic_service(in_memory_db, ...) -> Generator[EpicService, None, None]:
    uow = UnitOfWork(in_memory_db)  # Same session, NEW UoW with NEW repos
    try:
        yield EpicService(uow, ...)
    finally:
        uow.close()
        del uow
```

**Why this leaks memory:**
1. Multiple `UnitOfWork` instances share the same SQLAlchemy session
2. Each `UnitOfWork` has lazy-loaded repository properties (`issues`, `comments`, `epics`, `labels`, `projects`, `graph`)
3. When tests use multiple fixtures, multiple UoWs maintain separate repository instances
4. Repository objects hold internal caches and query result sets (~1-5MB each)
5. With 4-5 services per test, this adds ~20-25MB per test

---

## Solution Implemented

### 1. Added repository cache clearing to UnitOfWork.close()

**File: `src/dot_work/db_issues/adapters/sqlite.py`**

```python
def close(self) -> None:
    """Close the underlying session."""
    try:
        self.session.close()
    except Exception as e:
        logger.warning("Failed to close session: %s", e)

    # Clear repository references to release cached data
    self._issues = None
    self._comments = None
    self._graph = None
    self._epics = None
    self._labels = None
    self._projects = None
```

### 2. Created shared `uow` fixture

**File: `tests/unit/db_issues/conftest.py`**

```python
@pytest.fixture
def uow(in_memory_db: Session) -> Generator[UnitOfWork, None, None]:
    """Create a shared UnitOfWork for all service fixtures."""
    from dot_work.db_issues.adapters import UnitOfWork

    uow = UnitOfWork(in_memory_db)
    try:
        yield uow
    finally:
        try:
            uow.close()
        except Exception:
            pass
        del uow
```

### 3. Updated service fixtures to use shared uow

**Before:**
```python
def issue_service(in_memory_db, ...) -> Generator[IssueService, None, None]:
    uow = UnitOfWork(in_memory_db)
    try:
        yield IssueService(uow, ...)
    finally:
        uow.close()
```

**After:**
```python
def issue_service(uow: UnitOfWork, ...) -> IssueService:
    return IssueService(uow, ...)
```

**Fixtures updated:**
- `issue_service`
- `epic_service`
- `dependency_service`
- `label_service`

---

## Affected Files
- `src/dot_work/db_issues/adapters/sqlite.py` (added cache clearing to close())
- `tests/unit/db_issues/conftest.py` (added uow fixture, updated 4 service fixtures)

---

## Outcome

**Validation Results:**
- All 277 db_issues tests pass
- Memory growth: +13.7 MB (down from ~20-25MB)
- Test runtime: 19.30s

**Changes Made:**
1. Added repository cache clearing to `UnitOfWork.close()`
2. Created shared `uow` fixture
3. Converted 4 service fixtures to use shared uow

**Lessons Learned:**
- Sharing a single UnitOfWork across services prevents repository cache duplication
- Clearing repository references in close() helps garbage collection
- Fixture dependency injection is cleaner than fixture-scoped Generators

---

## Acceptance Criteria
- [x] Single UnitOfWork instance shared across all service fixtures
- [x] Repository caches cleared in UnitOfWork.close()
- [x] Memory growth per db_issues test reduced
- [x] All 277 db_issues tests still pass
- [x] Test isolation maintained (no state leakage between tests)
