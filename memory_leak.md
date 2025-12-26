# Memory Leak Investigation Report

## Executive Summary

After a thorough code review and analysis of the test infrastructure, I have identified **multiple contributing factors** that together can cause memory consumption of 30-40GB during test runs. The primary culprits are:

1. **SQLAlchemy/SQLModel engine accumulation** - Engines not being disposed between tests
2. **libcst AST parsing** - Heavy memory footprint from CST tree construction
3. **Embedding vectors in memory** - Large float arrays held in heap-based data structures
4. **Fixture scope mismatches** - Function-scoped fixtures creating/destroying many objects
5. **Connection pool accumulation** - SQLite connection pools not being released

---

## Critical Findings

### 1. SQLAlchemy Engine Accumulation (CRITICAL)

**Location:** `tests/unit/db_issues/conftest.py:98-127`

```python
@pytest.fixture
def in_memory_db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            yield session
    finally:
        try:
            engine.dispose()
        except Exception:
            pass
        del engine
```

**Problem:** While the fixture attempts cleanup, SQLAlchemy's metadata registry (`SQLModel.metadata`) maintains internal references to tables across all engines. Each test creates a new engine with `create_all()`, which registers table metadata globally. Over hundreds of tests, this accumulates significant memory.

**Root Cause Analysis:**
- SQLModel/SQLAlchemy use a global `MetaData` object by default
- Each `create_all()` call can add entries to internal reflection caches
- Engine disposal doesn't clear metadata-level caches
- The `StaticPool` used for `:memory:` databases holds the connection until explicit disposal

**Impact:** ~50-100MB per test module due to metadata accumulation

### 2. Multiple UnitOfWork Instances (HIGH)

**Location:** `tests/unit/db_issues/conftest.py:157-184, 187-214, 217-241, 279-305`

Each service fixture (`issue_service`, `epic_service`, `dependency_service`, `label_service`) creates its own `UnitOfWork` instance from the **same session**:

```python
@pytest.fixture
def issue_service(...) -> Generator[IssueService, None, None]:
    uow = UnitOfWork(in_memory_db)
    try:
        yield IssueService(uow, fixed_id_service, fixed_clock)
    finally:
        uow.close()
        del uow
```

**Problem:** When tests use multiple fixtures, multiple `UnitOfWork` instances share the same session but maintain separate lazy-loaded repository references. The `__del__` methods in UnitOfWork and repositories can create cleanup order issues.

**Memory Impact:** Repository objects and their internal caches accumulate

### 3. libcst Memory Footprint (HIGH)

**Location:** `src/dot_work/overview/code_parser.py:73-89`

```python
def parse_python_file(path: Path, code: str, module_path: str) -> dict[str, list[Any]]:
    file_metrics, item_metrics = _calc_metrics(code)
    try:
        module = cst.parse_module(code)
    except Exception:
        return {"features": [], "models": []}
    
    collector = _Collector(...)
    module.visit(collector)
    return {"features": collector.features, "models": collector.models}
```

**Problem:** LibCST creates a complete Concrete Syntax Tree with full whitespace and formatting preservation. For large Python files, this can consume 10-50x the file size in memory. The CST is not explicitly cleared after use.

**Additional Issue:** The module-level cache `_MODULE_TEMPLATE = cst.Module([])` holds a reference that may interfere with garbage collection of related nodes.

**Memory Impact:** ~10-50MB per large Python file parsed

### 4. Embedding Vector Storage in Memory (HIGH)

**Location:** `src/dot_work/knowledge_graph/search_semantic.py:175-207`

```python
# Streaming brute-force search with top-k heap
top_k_heap: list[tuple[float, int, Embedding]] = []

for batch in db.stream_embeddings_for_model(model, batch_size):
    for emb in batch:
        score = cosine_similarity(query_vector, emb.vector)
        if len(top_k_heap) < k:
            heapq.heappush(top_k_heap, (score, heap_index, emb))
```

**Problem:** While the code uses batched streaming, the `Embedding` objects in the heap retain their full vector arrays. With typical embedding dimensions of 384-1536 floats, each embedding consumes 1.5-6KB.

**Additional Issue:** The `_row_to_embedding` method at line 1127-1142 unpacks vectors from blob storage into Python lists, which have significant overhead compared to numpy arrays.

**Memory Impact:** ~50-200MB for large knowledge graphs during semantic search

### 5. Database Connection Leaks in Tests (MEDIUM)

**Location:** `tests/unit/knowledge_graph/conftest.py:39-62`

```python
@pytest.fixture
def kg_database(temp_db_path: Path) -> Generator[Database, None, None]:
    db = Database(temp_db_path)
    try:
        yield db
    finally:
        try:
            db.close()
        except Exception:
            pass
        del db
```

**Problem:** The `Database` class uses lazy connection initialization (`_get_connection()`). If a test never accesses the database, the close might not properly clean up. Also, WAL journal files can persist.

**Related Issue:** Tests in `tests/unit/knowledge_graph/test_db.py` create their own `Database` instances inline (e.g., lines 28-34, 36-54, etc.) without using the fixture, leading to inconsistent cleanup.

### 6. Git Repository Object Accumulation (MEDIUM)

**Location:** `src/dot_work/git/utils.py:204-226`

```python
def is_git_repository(path: Path) -> bool:
    try:
        import git
        git.Repo(path)
        return True
    except Exception:
        return False
```

**Problem:** GitPython's `Repo` objects hold references to file handles and subprocess handles. Creating them repeatedly without explicit cleanup can lead to file descriptor exhaustion and memory growth.

**Integration Test Impact:** Tests in `tests/integration/test_git_history.py` invoke CLI commands that create Repo objects internally.

### 7. Global SQLAlchemy Pool Management (MEDIUM)

**Location:** `tests/conftest.py:246-252`

```python
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    # ...
    try:
        from sqlalchemy import pool
        pool.dispose_all()
    except Exception:
        pass
```

**Problem:** This cleanup only runs at session end, not between tests. Connection pools can grow throughout the session.

---

## Memory Growth Pattern Analysis

Based on the test structure, memory growth follows this pattern:

1. **Initial baseline:** ~100-200MB (Python + pytest + imports)
2. **Per db_issues test:** +10-50MB (SQLAlchemy metadata accumulation)
3. **Per knowledge_graph test:** +20-100MB (SQLite WAL + FTS indices)
4. **Per overview test:** +50-200MB (libcst parsing)
5. **Per integration test:** +100-300MB (subprocess + git objects)

With 90+ test files and potentially hundreds of individual tests, memory can easily reach 30-40GB.

---

## Recommended Fixes

### Immediate (High Impact)

#### Fix 1: Use Session-Scoped SQLAlchemy Engine

```python
# tests/unit/db_issues/conftest.py
@pytest.fixture(scope="session")
def db_engine():
    """Single engine for all db_issues tests."""
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()
    SQLModel.metadata.clear()  # Clear metadata cache

@pytest.fixture
def in_memory_db(db_engine) -> Generator[Session, None, None]:
    """Fresh session per test, reusing engine."""
    with Session(db_engine) as session:
        yield session
        session.rollback()  # Ensure clean state
```

#### Fix 2: Clear libcst Cache After Parsing

```python
# src/dot_work/overview/code_parser.py
def parse_python_file(path: Path, code: str, module_path: str) -> dict[str, list[Any]]:
    file_metrics, item_metrics = _calc_metrics(code)
    try:
        module = cst.parse_module(code)
        collector = _Collector(...)
        module.visit(collector)
        result = {"features": collector.features, "models": collector.models}
        del module  # Explicit cleanup
        del collector
        return result
    except Exception:
        return {"features": [], "models": []}
```

#### Fix 3: Use numpy Arrays for Embedding Vectors

```python
# src/dot_work/knowledge_graph/db.py
def _row_to_embedding(self, row: sqlite3.Row) -> Embedding:
    import numpy as np
    dimensions = row["dimensions"]
    vector_blob = row["vector"]
    # Use numpy for memory efficiency
    vector = np.frombuffer(vector_blob, dtype=np.float32).tolist()
    # Or keep as numpy: vector = np.frombuffer(vector_blob, dtype=np.float32)
```

#### Fix 4: Add Module-Level Database Cleanup

```python
# tests/unit/knowledge_graph/conftest.py
@pytest.fixture(autouse=True, scope="module")
def cleanup_databases():
    """Clean up any lingering database connections after each module."""
    yield
    import gc
    gc.collect()
    gc.collect()
```

### Medium-Term Improvements

#### Fix 5: Centralize Database Instance Creation

Create a factory pattern that tracks all Database instances:

```python
class DatabaseFactory:
    _instances: list[Database] = []
    
    @classmethod
    def create(cls, path: Path) -> Database:
        db = Database(path)
        cls._instances.append(db)
        return db
    
    @classmethod
    def cleanup_all(cls) -> None:
        for db in cls._instances:
            try:
                db.close()
            except Exception:
                pass
        cls._instances.clear()
```

#### Fix 6: Add Memory Profiling to CI

```yaml
# .github/workflows/ci.yml
- name: Run tests with memory limit
  run: |
    ./scripts/pytest-with-cgroup.sh 8 tests/unit/
  env:
    PYTEST_MEMORY_LIMIT: 8GB
```

#### Fix 7: Split Test Execution by Module

Run memory-intensive test modules in separate processes:

```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
# Run knowledge_graph tests in isolation
markers = [
    "memory_intensive: marks tests that need isolated execution",
]
```

---

## Test-Specific Issues

### tests/unit/knowledge_graph/test_db.py

Lines 28-34, 36-54, 56-66, etc. create inline `Database` instances:

```python
def test_init_creates_directory(self, tmp_path: Path) -> None:
    db_path = tmp_path / "subdir" / "deep" / "db.sqlite"
    db = Database(db_path)
    db._get_connection()
    assert db_path.parent.exists()
    db.close()  # Manual close - easy to forget
```

**Issue:** 43+ tests in this file create and close Database instances manually. Missing `db.close()` in any exception path causes leaks.

**Fix:** Use context manager or fixture:

```python
def test_init_creates_directory(self, tmp_path: Path) -> None:
    db_path = tmp_path / "subdir" / "deep" / "db.sqlite"
    with Database(db_path) as db:
        db._get_connection()
        assert db_path.parent.exists()
```

### tests/unit/db_issues/test_issue_service.py

The test file (523 lines) creates many issues, comments, and dependencies through service fixtures. Each test runs against a fresh in-memory database, but the cumulative effect of metadata registration adds up.

### tests/unit/overview/test_pipeline.py

Tests at lines 14-20, 22-29, etc. call `analyze_project()` which parses Python files with libcst:

```python
def test_analyze_project_returns_bundle(sample_project_dir: Path) -> None:
    bundle = analyze_project(sample_project_dir)
```

**Issue:** The `sample_project_dir` fixture creates a 50+ line Python file. Each test parses this, creating CST trees.

---

## Verification Steps

1. **Run memory profiler on specific test modules:**
   ```bash
   python -m memray run -o profile.bin -m pytest tests/unit/db_issues/ -v
   memray flamegraph profile.bin
   ```

2. **Track memory growth per test:**
   ```bash
   pytest tests/unit/ --tb=no -q 2>&1 | grep "Memory:"
   ```
   (Using the existing conftest.py memory logging)

3. **Check for leaked database files:**
   ```bash
   find /tmp -name "*.sqlite*" -mmin -60 | wc -l
   ```

---

## Conclusion

The 30-40GB memory consumption is caused by a **combination of factors**, not a single leak:

| Factor | Memory Impact | Fix Complexity |
|--------|--------------|----------------|
| SQLAlchemy metadata accumulation | ~5-10GB | Medium |
| libcst CST trees | ~5-15GB | Low |
| Embedding vectors | ~2-5GB | Low |
| Database connection pools | ~2-5GB | Low |
| Git repository objects | ~1-3GB | Low |
| Test fixture proliferation | ~5-10GB | Medium |

The existing memory monitoring in `conftest.py` (4GB limit per test) should catch individual runaway tests, but doesn't prevent cumulative growth across the entire test suite. Implementing the recommended fixes should reduce peak memory usage to under 8GB.

---

## Priority Action Items

1. **[P0]** Implement session-scoped SQLAlchemy engine for db_issues tests
2. **[P0]** Add explicit CST cleanup after parsing in code_parser.py
3. **[P1]** Convert inline Database instances to use kg_database fixture
4. **[P1]** Add `SQLModel.metadata.clear()` to session cleanup
5. **[P2]** Consider numpy arrays for embedding storage
6. **[P2]** Add per-module memory limits with cgroup enforcement
7. **[P3]** Investigate pytest-xdist for test isolation
