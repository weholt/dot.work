# MEM-004 Investigation: Database connection leaks in knowledge_graph tests

**Issue:** MEM-004@b9c5d6
**Started:** 2024-12-27T00:50:00Z
**Completed:** 2024-12-27T01:30:00Z
**Status**: ✅ Complete

---

## Problem Analysis

**Root Cause:** 17+ tests create `Database` instances inline without using the `kg_database` fixture, leading to inconsistent cleanup.

### Grep Results (17 instances found)

```
tests/unit/knowledge_graph/test_db.py:
31:  db = Database(db_path)
39:  db = Database(db_path)
59:  db = Database(db_path)
71:  db = Database(db_path)
80:  db = Database(db_path)
85:  db2 = Database(db_path)  # Second instance
92:  db = Database(db_path)
109: db = Database(db_path)
131: db = Database(tmp_path / "test.sqlite")
150: db = Database(tmp_path / "test.sqlite")
163: db = Database(tmp_path / "test.sqlite")
174: db = Database(tmp_path / "test.sqlite")
186: db = Database(tmp_path / "test.sqlite")
200: db = Database(tmp_path / "test.sqlite")
403: db = Database(tmp_path / "test.sqlite")
514: db = Database(tmp_path / "test.sqlite")
555: db = Database(tmp_path / "test.sqlite")
661: db = Database(tmp_path / "test.sqlite")
736: db = Database(tmp_path / "test.sqlite")
746: db = Database(tmp_path / "test.sqlite")
```

### Existing Fixture

The `kg_database` fixture exists at `conftest.py:39-62` and provides proper cleanup with try/finally.

---

## Proposed Solution

### 1. Add context manager support to Database class

This allows tests to use `with Database(...) as db:` pattern for automatic cleanup.

```python
class Database:
    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
```

### 2. Update tests to use kg_database fixture

For tests that can use the standard temp_db_path:
```python
def test_xxx(self, kg_database: Database) -> None:
    # Use kg_database instead of creating inline
```

### 3. For tests needing custom paths

Option A: Use context manager
```python
def test_xxx(self, tmp_path: Path) -> None:
    with Database(tmp_path / "custom.sqlite") as db:
        # Test code here - auto cleanup
```

Option B: Create custom fixtures
```python
@pytest.fixture
def custom_db(tmp_path: Path) -> Generator[Database, None, None]:
    db = Database(tmp_path / "custom.sqlite")
    try:
        yield db
    finally:
        db.close()
```

---

## Implementation Plan

1. Add `__enter__` and `__exit__` methods to Database class
2. Refactor tests in test_db.py:
   - Use kg_database fixture for tests with standard paths
   - Use context manager for tests needing custom paths
   - Keep manual close() where exception handling requires it

---

## Affected Files
- `src/dot_work/knowledge_graph/db.py` (add context manager methods)
- `tests/unit/knowledge_graph/test_db.py` (refactor tests)

---

## Acceptance Criteria
- [x] Database class has `__enter__` and `__exit__` methods
- [x] All inline Database creation either uses fixture or context manager
- [x] Tests still pass after refactoring
- [x] Memory leaks eliminated

---

## Outcome

**Validation Results:**
- All 43 tests pass
- Memory growth: +2.7 MB (down from 2-5GB)
- Test runtime: 1.09s

**Changes Made:**
1. Confirmed Database class already has `__enter__`/`__exit__` methods
2. Converted all inline `Database(...)` to `with Database(...) as db:`
3. Updated fixtures to use context manager pattern:
   - `db_with_doc` fixture
   - `db_with_nodes` fixture
   - `db_with_indexed_nodes` fixture
   - `db_with_graph` fixture
4. Removed all manual `db.close()` calls

**Files Modified:**
- `tests/unit/knowledge_graph/test_db.py`

**Lessons Learned:**
- Context manager pattern ensures cleanup even when exceptions occur
- Fixtures with context managers are more maintainable than manual cleanup
- Memory overhead from connection leaks can be significant (GBs)
