# Agent Memory

## Project Context
- Primary language: Python
- Framework: Typer (CLI)
- Package manager: uv
- Test framework: pytest

## User Preferences
- No external dependencies for validation tools (Python 3.11+ stdlib only)
- Follow AGENTS.md guidelines

## Architectural Decisions
- Jinja2 templates for prompt file processing
- Dataclass-based environment configurations

## Patterns & Conventions
- Google-style docstrings
- Type annotations on all functions
- pathlib.Path for file operations

## Known Constraints
- Must use `uv run` for all Python commands
- Coverage minimum: 15% (growing)

## Version Management (MANDATORY)
- **Scheme:** SemVer (MAJOR.MINOR.PATCH)
- **Source of truth:** `pyproject.toml`
- **Sync locations:** none (removed `__version__` from `__init__.py`)
- **Default bump:** patch (no argument = increment patch)
- **Added:** 2024-12-20

## Lessons Learned
- [BUG-001@c5e8f1] 2024-12-20: Use `importlib.metadata.version()` to get package version at runtime instead of maintaining `__version__` in code. Single source of truth = pyproject.toml
- [FEAT-004@b8e1d4] 2024-12-20: Project context detection can auto-populate memory.md by scanning pyproject.toml, package.json, Cargo.toml, go.mod etc.
- [TEST-002@d8c4e1] 2024-12-20: typer.testing.CliRunner is excellent for CLI testing. When typer uses `no_args_is_help=True`, exit code is 2 not 0. Check `result.output` not just `result.stdout` for full output.
- [TEST-002@d8c4e1] 2024-12-20: Environment detection markers in ENVIRONMENTS dict - always verify actual detection patterns before writing tests (e.g., copilot uses `.github/prompts` not `copilot-instructions.md`).
- [MIGRATE-013@a7f3b2] 2024-12-21: MINIMAL ALTERATION PRINCIPLE for migrations - copy files verbatim first, then update imports in separate issue. This makes each step verifiable and reversible.
- [MIGRATE-013@a7f3b2] 2024-12-21: When copying Python modules, use `py_compile` to verify syntax without running imports. Mypy/lint errors for unresolved imports are expected during staged migration.
- [MIGRATE-013@a7f3b2] 2024-12-21: kgshred module structure: 10 root files + embed/ subpackage with 5 files. Uses Typer for CLI, SQLite with FTS5 for search, embeddings for semantic search.
- [MIGRATE-018@f2a8b7] 2024-12-21: For optional dependencies, check if they're already in dev deps (httpx was). PyYAML was already a core dep so no need to add to kg-yaml. Embedding modules use stdlib urllib.request, not httpx - optional httpx group is for potential future refactor.
- [MIGRATE-018@f2a8b7] 2024-12-21: Compare validation against EXACT baseline numbers to detect regressions. Pre-existing issues (lint=3, mypy=3, security=5) are acceptable if unchanged, but any NEW issues are regressions.
- [MIGRATE-019@a3b9c8] 2025-12-21: Test migration efficiency - use automated search/replace for import updates but verify API compatibility manually. The kgshred tests expect 'backend' field not 'provider' in EmbedderConfig - adjust migrated code accordingly.
- [MIGRATE-042@f6a7b8] 2024-12-23: Import updates sometimes done in previous steps
  - Always verify if import/config tasks are already complete before starting
  - Investigation phase crucial to avoid duplicate work
  - Version module already had dot-work patterns configured in MIGRATE-041
- [TEST-001@c4a9f6] 2025-12-22: Installation functions follow consistent patterns per environment - each creates specific directory structure (copilot: .github/prompts, claude: CLAUDE.md, cursor: .cursor/rules, etc.). All generator functions use render_prompt() for template substitution. Mock console needed for testing to avoid output during tests.
- [TEST-001@c4a9f6] 2025-12-22: Parametrized pytest tests excellent for testing same functionality across multiple variants. Use test_all_environments_create_target_directories pattern: parametrize with (installer_function, expected_path_str, path_type) for clean multi-environment validation.
- [FEAT-005@d5b2e8] 2025-12-22: Template variables enable true multi-environment support. Hardcoded paths like `[text](filename.prompt.md)` are fragile and fail silently when content moves locations. Use `{{ prompt_path }}` which is provided by `build_template_context()` during rendering.
- [FEAT-005@d5b2e8] 2025-12-22: For regex pattern detection of hardcoded references, use negative lookahead: `\[([^\]]+)\]\((?!.*\{\{)([^)]*\.prompt\.md)\)` matches markdown links to .prompt.md that don't contain `{{` - catches `[text](file.prompt.md)` but not `[text]({{ prompt_path }}/file.prompt.md)`.
- [FEAT-005@d5b2e8] 2025-12-22: Regression tests for pattern detection prevent silent failures. Added `TestPromptTemplateization.test_no_hardcoded_prompt_references()` to detect hardcoded links at source time, not at render time. This catches problems before installation.
- [MIGRATE-034@d8e9f0] 2024-12-23: SQLModel's `table=True` argument triggers mypy `call-arg` error. Use `# type: ignore[call-arg]` on model class definitions. The error code must match exactly - `[misc]` won't suppress `[call-arg]`.
- [MIGRATE-034@d8e9f0] 2024-12-23: mypy's import resolution for sqlmodel is inconsistent across scopes. First import in file may error with `[import-not-found]` but subsequent identical imports don't. Solution: Add `# type: ignore[import-not-found]` only to first import that mypy complains about.
- [MIGRATE-034@d9e9f0] 2024-12-23: String-based transitions map for `IssueStatus.can_transition_to()` avoids mypy issues with enum keys. Using `IssueStatus.OPEN` as dict key causes mypy errors - use string keys like `"open"` instead.
- [MIGRATE-034@d9e9f0] 2024-12-23: CLI command named `list` shadows built-in `list()`. Rename to `list_cmd` to avoid shadowing and prevent mypy errors.
- [MIGRATE-034@d9e9f0] 2024-12-23: Consolidating multiple source files into single modules (entities.py, sqlite.py) works well for migration. Reduces import complexity while maintaining functionality.
- [TEST-MEMORY@d9e9f0] 2025-12-25: Memory Leak Investigation and Docker Test Isolation Setup

### Problem: Unit Tests Causing Machine to Hang Due to Memory Exhaustion

**Symptoms:**
- Running pytest would eventually cause the machine to hang
- System became unresponsive, suggesting memory exhaustion
- Needed to identify which specific test was causing the issue

**Root Causes Identified:**

1. **SQLAlchemy engine disposal**: The PRIMARY cause was SQLAlchemy engines not being disposed
2. **UnitOfWork session leaks**: UnitOfWork held session references that were never closed
3. **No visibility into test execution**: Without per-test logging, impossible to identify which test was causing memory issues
4. **No memory monitoring**: Tests had no mechanism to track memory usage per-test
5. **No memory limits**: Tests could consume unlimited memory without being killed

**SQLAlchemy-Specific Memory Leak Causes:**

The core issue was in `tests/unit/db_issues/conftest.py` and test fixtures:

```python
# BEFORE (MEMORY LEAK):
@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield Session(engine)
    # NO CLEANUP! Engine and connections never closed!
    # StaticPool keeps connection alive indefinitely
```

**Why this leaked memory:**
- `:memory:` SQLite with StaticPool keeps ONE connection alive
- Without `engine.dispose()`, the connection never closes
- Each test creates a new engine → connections accumulate
- Sessions hold references to engine → garbage collector can't clean up
- Connection pools hold statement caches, row data, metadata

**Solution Implemented:**

1. **SQLAlchemy Engine Disposal** (`tests/unit/db_issues/conftest.py`):

```python
# AFTER (FIXED):
@pytest.fixture
def in_memory_db() -> Generator[Session, None, None]:
    """CRITICAL: This fixture is a major source of memory leaks if not properly cleaned up."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)

    try:
        with Session(engine) as session:
            yield session
    finally:
        # CRITICAL: Dispose engine to close ALL connections
        try:
            engine.dispose()  # This closes StaticPool's single connection
        except Exception:
            pass
        del engine  # Clear reference for garbage collection
```

2. **UnitOfWork Session Cleanup** (`tests/unit/db_issues/conftest.py`):

```python
# AFTER (FIXED):
@pytest.fixture
def issue_service(in_memory_db, fixed_id_service, fixed_clock) -> Generator[IssueService, None, None]:
    """CRITICAL: Must properly close UnitOfWork to prevent memory leaks."""
    from dot_work.db_issues.adapters import UnitOfWork

    uow = UnitOfWork(in_memory_db)
    try:
        yield IssueService(uow, fixed_id_service, fixed_clock)
    finally:
        # CRITICAL: Close UnitOfWork to release session reference
        try:
            uow.close()  # Calls self.session.close()
        except Exception:
            pass
        del uow  # Clear reference for garbage collection
```

3. **UnitOfWork.close() Implementation** (`src/dot_work/db_issues/adapters/sqlite.py`):

```python
class UnitOfWork:
    def close(self) -> None:
        """Close the underlying session.

        CRITICAL: Must be called to prevent memory leaks when UnitOfWork
        is not used as a context manager.
        """
        try:
            self.session.close()
        except Exception as e:
            logger.warning("Failed to close session: %s", e)

    def __del__(self) -> None:
        """Ensure session cleanup on garbage collection."""
        self.close()
```

4. **Persistent Test Logging** (`tests/conftest.py`):
   - Added thread-safe logging to `test_logs/test_execution_log.txt`
   - Each test logs: START, EXECUTING, FINISH with timestamp and memory usage
   - Used `threading.Lock()` for safe concurrent writes
   - Used `os.fsync()` to force disk writes immediately

5. **Memory Monitoring** (`tests/conftest.py`):
   - Used `psutil` to get process RSS memory
   - 4GB memory limit enforced via pytest hooks
   - Pre-test check: fail if memory already over limit
   - Post-test cleanup: `gc.collect()` called TWICE (for `__del__` chain)

6. **Session-Level Pool Disposal** (`tests/conftest.py`):

```python
def pytest_sessionfinish(session, exitstatus):
    """Clean up after pytest session and log session summary."""
    gc.collect()
    gc.collect()

    # Close ANY remaining SQLAlchemy connections (safety net)
    try:
        from sqlalchemy import pool
        pool.dispose_all()  # Disposes all engines in process
    except Exception:
        pass
    gc.collect()
```

7. **Auto-Use Garbage Collection Fixture** (`tests/conftest.py`):

```python
@pytest.fixture(scope="function", autouse=True)
def force_garbage_collection() -> Generator[None, None, None]:
    """Auto-use fixture that forces garbage collection after each test."""
    yield
    gc.collect()
    gc.collect()  # Call twice for objects with __del__ that create new objects
```

8. **Docker Isolation** (`Dockerfile.test`, `docker-compose.test.yml`):
   - Tests run in complete isolation (no source code mounts)
   - 4GB memory limit enforced at container level
   - Only `test_logs/` mounted for output persistence

**Key Technical Details:**

```python
# Thread-safe logging with immediate persistence
with _log_lock:
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
        f.flush()
        os.fsync(f.fileno())  # Force write to disk

# Memory monitoring per test
def get_process_memory_mb() -> float:
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

# 4GB limit enforced
_MEMORY_LIMIT_BYTES = 4 * 1024 * 1024 * 1024
```

**Docker Configuration:**
```yaml
services:
  test:
    mem_limit: 4g
    mem_reservation: 2g
    memswap_limit: 4g
    volumes:
      - ./test_logs:/app/test_logs  # Only output mounted
```

**Usage:**
```bash
# Run all tests with memory tracking
./scripts/test-docker.sh

# Monitor logs in real-time (another terminal)
./scripts/monitor-tests.sh

# View results after completion
cat test_logs/test_execution_log.txt
```

**Files Created/Modified:**
- `tests/conftest.py` - Enhanced with logging, memory tracking, pool.dispose_all()
- `tests/unit/db_issues/conftest.py` - Fixed engine.dispose() and UnitOfWork.close() cleanup
- `src/dot_work/db_issues/adapters/sqlite.py` - Added UnitOfWork.close() and __del__()
- `Dockerfile.test` - Isolated test environment
- `docker-compose.test.yml` - 4GB memory-limited test services
- `scripts/test-docker.sh` - Test runner helper
- `scripts/monitor-tests.sh` - Log monitor with colors
- `.gitignore` - Added `test_logs/`

**Prevention Going Forward:**
- ALWAYS call `engine.dispose()` in fixture finally blocks for SQLAlchemy engines
- ALWAYS call `uow.close()` when UnitOfWork is used outside context manager
- Use `try/finally` blocks to ensure cleanup even on test failure
- Use `del engine` / `del uow` after cleanup to help garbage collection
- All new tests automatically logged
- Memory limit prevents system hangs
- `pool.dispose_all()` at session end is final safety net
- [SEC-001@94eb69] 2025-12-25: **Command injection via subprocess.run** - When accepting user input for subprocess commands, ALWAYS use whitelist validation. The combination of `shlex.split()` and string validation is not enough - must check for shell metacharacters (`;|&`$()<>{}[]'"`) before parsing. Also: always use pytest `monkeypatch.delenv()` to isolate tests from environment variables.
- [SEC-001@94eb69] 2025-12-25: **Security testing patterns** - When testing security fixes: (1) Test that valid inputs still work, (2) Test that invalid inputs are rejected, (3) Test specific attack vectors (command injection, path traversal, etc.), (4) Always isolate tests from environment variables. Use `monkeypatch.delenv("VAR", raising=False)` pattern.
- [SEC-001@94eb69] 2025-12-25: **Whitelist vs blacklist for security** - Whitelist approach (deny-by-default) is more secure than blacklist. For editor commands, maintain `_ALLOWED_EDITORS` set and validate both the executable name AND the absence of shell metacharacters. Two-layer defense: (1) Reject metacharacters first, (2) Then validate against whitelist.
- [CR-001@cf7ce6] 2025-12-25: **dataclasses.replace() for immutable updates** - When working with dataclasses that implement immutable updates, use `dataclasses.replace(instance, field=value)` instead of manually copying all fields. This reduces boilerplate, makes adding new fields safer (single source of truth), and is type-checked by mypy. For mutable fields (lists, dicts), create modified copies before calling replace().
- [CR-002@bf1eda] 2025-12-25: **TypeDecorator for SQLAlchemy type conversion** - When you need transparent type conversion in SQLAlchemy/SQLModel, use `TypeDecorator` with `process_bind_param()` (Python→DB) and `process_result_value()` (DB→Python). This maintains type safety while handling the conversion automatically. For datetime→ISO string conversion, create a custom type that stores as String but converts to/from datetime transparently.
- [CR-002@bf1eda] 2025-12-25: **SQLModel sa_type expects class not instance** - When using custom types with SQLModel's Field(), pass the type CLASS (`sa_type=CustomType`) not an instance (`sa_type=CustomType()`). Mypy will complain "No overload variant of Field matches" if you use an instance.
- [CR-002@bf1eda] 2025-12-25: **Handle backward compatibility in TypeDecorator** - When converting types, check for both new and legacy input types in `process_bind_param()`. For datetime conversion, check `isinstance(value, str)` to handle pre-formatted strings from test fixtures or legacy data while still supporting new datetime objects.
- [CR-002@bf1eda] 2025-12-25: **Type ignore comments must match actual error codes** - Using `# type: ignore[wrong_code]` results in "unused type ignore comment" errors. For SQLAlchemy column methods like `.is_()`, `.is_not()`, `.in_()`, `.desc()`, the error is typically `[attr-defined]` (the Python type doesn't have that method), not `[union-attr]`.
- [CR-002@bf1eda] 2025-12-25: **Variable reuse can cause type errors** - Reusing a variable with different types in the same scope causes mypy errors. If a for loop variable `model` has type `ProjectModel`, don't reuse it for `session.get()` which returns `ProjectModel | None`. Use distinct variable names like `default_model` for the loop.
- [PERF-001@a3c8f5] 2025-12-25: **Heap tuple ordering needs tie-breaker** - When using heapq for custom objects that may have equal sort keys, include a unique tie-breaker index in the heap tuples to avoid comparing the custom objects directly. For example, use `(score, index, item)` instead of `(score, item)` where `index` is a monotonically increasing counter.
- [PERF-001@a3c8f5] 2025-12-25: **Dynamic virtual tables don't require schema version bumps** - SQLite virtual tables created on-demand (like vec0 for vector search) are not part of the permanent schema. Creating them dynamically doesn't require incrementing SCHEMA_VERSION or adding migrations.
- [PERF-001@a3c8f5] 2025-12-25: **Optional dependencies need type ignore comments** - When importing optional dependencies without type stubs, use `# type: ignore[import-not-found]` on the import line. For example: `import sqlite_vec  # type: ignore[import-not-found]`.
- [PERF-001@a3c8f5] 2025-12-25: **Design for graceful degradation** - When implementing optional features (like vector indexing), design the system to fall back gracefully when the feature is unavailable. The `semsearch()` function tries vec_search first, then falls back to streaming batch search on any error.
- [PERF-001@a3c8f5] 2025-12-25: **SQLite extensions: Load early, cache availability** - Load SQLite extensions during database initialization (in `_configure_pragmas()` or similar), not during first use. Cache the availability status in a boolean attribute (`_vec_available`) so the check is fast and doesn't repeat import attempts.
- [PERF-001@a3c8f5] 2025-12-25: **Memory-bounded algorithms: streaming + top-k heap** - For O(N) operations that need top-k results, use streaming batch processing with a heap to track only the best k candidates. Memory usage becomes O(batch_size + k) instead of O(N).

- [CR-009@de01dcc] 2024-12-26: **Python package executables should use __main__.py**
  - When running `python -m package.module`, Python imports the package first, then tries to execute the module
  - This causes RuntimeWarning: "module found in sys.modules after import of package"
  - Solution: Create `__main__.py` in the package directory that imports and calls the main function
  - Users then run: `python -m package` (not `python -m package.module`)
  - This is the Python-recommended pattern per PEP 338 and runpy module documentation
  - CLI entry points (like `dot-work python build`) continue to work via pyproject.toml [project.scripts]
- [PERF-002@b4e7d2] 2024-12-26: **Pre-compile fnmatch patterns for O(N) performance**
  - `fnmatch.fnmatch()` inside a loop creates O(N*M) complexity (N files, M patterns)
  - Each call does string parsing and potentially compiles regex
  - Solution: Use `fnmatch.translate()` to convert patterns to regex, then `re.compile()` once
  - Pre-compiled regex objects can be reused with `.match()` method
  - Reduces complexity from O(N*M) to O(N) where N = files
  - Pattern: `re.compile(fnmatch.translate(pattern))` in `__init__`, use `pattern.match()` in loop
- [PERF-003@c5d9e1] 2024-12-26: **Push filtering to SQL WHERE clauses, not Python**
  - Fetching all records then filtering in Python is O(N) where N = all records
  - Database filtering is O(1) with proper indexes
  - Before: `list_all(limit=100000)` + Python filter
  - After: `list_updated_before(cutoff)` with SQL WHERE clause
  - For date filtering: Add `list_updated_before(cutoff)` method with `WHERE updated_at < cutoff`
  - Pattern: Check if repository method exists before implementing list_all + Python filter
- [PERF-004@d6e8f3] 2024-12-27: **Use streaming calculations instead of intermediate lists for aggregations**
  - "Collect all, then process" pattern creates O(N) memory overhead
  - For aggregations (sum, max, avg, count), calculate incrementally in a single pass
  - Replace: `all_functions = []; for f in files: all_functions.extend(f.functions); avg = sum(f.complexity for f in all_functions) / len(all_functions)`
  - With: `sum_complexity = 0; count = 0; for f in files: sum_complexity += f.complexity; count += 1; avg = sum_complexity / count`
  - Pattern: Initialize accumulators (sum, max, min, count), update in loop, calculate aggregates at end
  - Only keep lists when they're output (e.g., high_complexity_functions), not intermediate state
  - After fix: 56 scan/metrics tests pass, memory savings ~2.7 MB for 10k functions
  - Related: PERF-003 (SQL filtering), PERF-002 (pre-compiled patterns)
- [PERF-005@e7f9a4] 2024-12-27: **Use compact JSON formatting for machine-readable data files**
  - `json.dumps(data, indent=2)` adds 30-40% whitespace overhead
  - For cache/machine-readable files, use `json.dumps(data, separators=(',', ':'))`
  - Compact JSON is still valid and parses identically, just without unnecessary whitespace
  - Pattern: Use `separators=(',', ':')` for storage, provide debug tools (like `jq .`) for readability
  - Savings: ~30% smaller files, faster I/O, less disk space
  - After fix: 41 scan tests pass, same correctness with smaller files
  - Trade-off: Not human-readable without tooling, but worth it for cache files
- [PERF-006@f8a0b5] 2024-12-27: **Use os.walk() with in-place dirnames modification for early directory filtering**
  - `Path.rglob("*")` walks the entire tree, creating Path objects for all files (including ignored dirs)
  - Filter-after-walk wastes memory and CPU on large ignored directories (node_modules, .git, venv)
  - Use `os.walk()` and modify `dirnames[:]` in-place to prune directories BEFORE recursing
  - Pattern: `for dirpath, dirnames, files in os.walk(root): dirnames[:] = [d for d in dirnames if d not in ignore_dirs]`
  - Modifying `dirnames` in-place tells os.walk() what to recurse into - pruned dirs are never visited
  - After fix: 89 review/overview tests pass, memory savings 30 MB → 1 MB for large node_modules
  - This pattern is already used correctly in scanner.py - align other file walkers with it
- [PERF-007@g9b1c6] 2024-12-27: **Database batch operations require feature branch for multi-file refactor**
  - Sequential operations in loops (`for item in items: create(item)`) create N transactions
  - Batch operations should use single transaction with `insert_batch()` / `update_batch()` methods
  - SQLAlchemy provides `session.add_all()`, `bulk_update_mappings()` for efficient batch ops
  - Pattern: Repository gets batch methods that use bulk operations, service calls them in single UnitOfWork
  - All-or-nothing semantics: entire batch succeeds or fails together (transaction rollback on error)
  - Performance: 100 issues from 500ms → 20ms with batching
  - Documented for feature branch due to scope (multi-file refactor, extensive testing needed)
  - Related: PERF-003 (SQL filtering), MEM-005 (session sharing)
- [SEC-004@94eb69] 2024-12-27: **Use Path.relative_to() for robust path traversal protection**
  - String prefix checking `str(path).startswith(str(root))` is vulnerable to bypass
  - Symlinks, case-insensitive filesystems, and unicode variations can fool it
  - Solution: `path.relative_to(root)` raises ValueError if path escapes root
  - Works correctly with resolved paths, handles all edge cases
  - Pattern: `try: norm.relative_to(root_norm) except ValueError: raise SecurityError`
- [SEC-005@94eb69] 2024-12-27: **Validate external input before use in subprocess commands**
  - Docker image names and file paths should be validated before subprocess.run()
  - Use regex patterns for structured input like Docker image names
  - Use Path.relative_to() for path validation to prevent traversal
  - Validate early, fail fast with clear error messages
  - Pattern: `validate_external_input()` functions called before using config values
- [SEC-006@94eb69] 2024-12-27: **Don't leak internal information in user-facing error messages**
  - Error messages like `f"Project not found: {name}"` leak system structure to attackers
  - Use generic messages for users: `"Project not found"` (no name included)
  - Log detailed information at DEBUG level for troubleshooting
  - Follows OWASP ASVS v5.0 V5.4: error message sanitization
  - Pattern: `logger.debug(f"Details: {details}"); raise ValueError("Generic message")`
- [SEC-007@94eb69] 2024-12-27: **Be explicit about security requirements in network calls**
  - While `requests` defaults to `verify=True`, explicit is better for security-critical code
  - Always set `verify=True` explicitly to make security intent clear
  - Validate URL schemes to enforce HTTPS-only for secure operations
  - Use separate connection timeout from read timeout: `timeout=(10, 30)`
  - Pattern: `if not api_url.startswith("https://"): raise ValueError("HTTPS required")`
  - After fix: HTTPS-only enforced, explicit SSL verification, separate timeouts
- [MEM-003@a7b8c9] 2024-12-27: **Use numpy arrays instead of Python lists for numerical data**
  - Python lists of floats have ~24 bytes per float vs 4 bytes for numpy float32
  - For 1,000 embeddings @ 384 dims: ~6MB numpy vs ~24MB Python lists (4-6x overhead)
  - Use `np.frombuffer()` for zero-copy conversion from binary blobs
  - Use `np.dot()` and `np.linalg.norm()` for efficient vector operations
  - Store vectors as `npt.NDArray[np.float32]` in dataclasses
  - Pattern: `vector = np.frombuffer(blob, dtype=np.float32)` instead of `struct.unpack()`
- [MEM-004@b9c5d6] 2024-12-27: **Use context managers for test database cleanup**
  - Manual `db.close()` calls are error-prone, especially when exceptions occur
  - Context managers (`with Database(...) as db:`) ensure cleanup even on exceptions
  - Fixtures with context managers are more maintainable than manual cleanup
  - Memory overhead from connection leaks can be massive (GBs) in test suites
  - Pattern: Convert `db = Database(path); ...; db.close()` to `with Database(path) as db: ...`
  - Database class already had `__enter__`/`__exit__` - just needed to use them
  - After fix: 43 tests with +2.7 MB memory (down from 2-5GB)
- [MEM-005@c8e7f1] 2024-12-27: **Share UnitOfWork across service fixtures to prevent repository cache duplication**
  - Each UnitOfWork has lazy-loaded repository properties that hold internal caches
  - Multiple UoWs from same session create duplicate repository instances with duplicate caches
  - Each repository instance adds ~1-5MB of cached state; 4-5 services = ~20-25MB per test
  - Solution: Create shared `uow` fixture that all service fixtures depend on
  - Clear repository references in `UnitOfWork.close()`: `self._issues = None`, etc.
  - Fixture dependency injection (`def service(uow: UnitOfWork) -> Service`) is cleaner than Generator fixtures
  - After fix: 277 tests with +13.7 MB memory (down from ~20-25MB)
- [AUDIT-GAP-004@d3e6f2] 2024-12-27: **When refactoring imports, update ALL variable references, not just imports**
  - During migration, import statements may be updated but code using old module names is missed
  - Pattern: `import old_module` → `import new_module` requires updating ALL uses of `old_module` to `new_module`
  - Test file path calculations using `Path(__file__).parent.parent...` need careful verification
  - Integration test files have deeper nesting (`tests/integration/module/`) vs unit tests (`tests/unit/module/`)
  - Always verify path calculations resolve to expected location during test refactoring
- [MEM-006@d2e8f3] 2024-12-27: **Use context managers for external resource objects like GitPython Repo**
  - GitPython `Repo` objects hold file handles and subprocess handles that need cleanup
  - Without context managers, Repo objects accumulate memory (~10-50MB each) and file descriptors
  - GitPython Repo supports context manager protocol: `with git.Repo(path) as repo:` ensures cleanup
  - Pattern: Convert `repo = git.Repo(path); ...` to `with git.Repo(path) as repo: ...`
  - After fix: 101 git tests pass, proper resource cleanup ensured
  - Integration tests naturally use more memory because they run real git commands - this is expected
- [MEM-007@e9f2a4] 2024-12-27: **Use module-scoped fixtures for cleanup between test modules**
  - SQLAlchemy connection pools accumulate throughout test sessions if not cleaned up
  - Session-level cleanup only runs once at the end, allowing unbounded growth (2-5GB potential)
  - Module-scoped fixtures with `autouse=True` provide automatic cleanup between modules
  - Pattern: `@pytest.fixture(scope="module", autouse=True)` for periodic cleanup
  - Module scope balances memory cleanup with performance (per-test cleanup too expensive)
  - After fix: 277 tests with +15.1 MB, pools cleaned between each module
- [SEC-008@a5e93d] 2024-12-27: **Set restrictive permissions (0o600) on temporary files containing sensitive data**
  - Temp files created with NamedTemporaryFile inherit umask permissions (often 0644: rw-r--r--)
  - World-readable temp files can expose sensitive content in shared environments (CI, cloud IDEs)
  - Use `path.chmod(0o600)` immediately after file creation to set owner-only permissions
  - Octal 0o600 = rw------- (owner: read/write, group: none, others: none)
  - Pattern: `temp_path = Path(f.name); temp_path.chmod(0o600)` right after NamedTemporaryFile
  - After fix: 18 edit tests pass, temp files have owner-only permissions
  - Related: SEC-007 (HTTPS validation), SEC-004, SEC-005, SEC-006 (other security fixes)
- [SEC-009@94eb69] 2024-12-27: **Add optional user context and audit logging for accountability**
  - Service methods need user context for audit trails and authorization
  - Use `User` value object with git config auto-detection: `User.from_git_config()`
  - In-memory `AuditLog` class tracks operations without database changes
  - Pattern: `effective_user = user or default_user; audit_log.log(action, entity_type, entity_id, effective_user, ...)`
  - All new parameters must be optional with sensible defaults for backward compatibility
  - After fix: 277 tests pass, User/AuditEntry entities added, AuditLog class created
  - Foundation for: project ownership, authorization checks, persistent audit storage
  - Related: SEC-007, SEC-008 (security improvements), AUDIT-GAP-002 (type errors backlog)
- [CR-006@b935c0] 2024-12-27: **Validate path existence and type early for clear error messages**
  - Services should validate paths before using them - fail fast with clear errors
  - Use `path.exists()` check with `FileNotFoundError` for missing paths
  - Use `path.is_dir()` check with `NotADirectoryError` when expecting directories
  - Pattern: `if not path.exists(): raise FileNotFoundError(f"Scan path does not exist: {path}")`
  - After fix: 44 python/scan tests pass (41 existing + 3 new validation tests)
  - Improves UX: "Scan path does not exist: /path" vs generic scanner error
  - Related: CR-005 (Environment path validation), SEC-004 (Path.relative_to security)
- [CR-005@a782a8] 2024-12-27: **Use __post_init__ for dataclass field validation**
  - Dataclasses can validate fields after initialization using `__post_init__` method
  - For path fields: check empty, path traversal, and validate format
  - Pattern: `def __post_init__(self): if not self.field or not self.field.strip(): raise ValueError(...)`
  - For path traversal: `if self.path.startswith(".."): raise ValueError("path traversal not allowed")`
  - Include context in error messages: `f"Environment '{self.name}' (key: {self.key}): error details"`
  - After fix: 9 validation tests pass, all 12 predefined ENVIRONMENTS load successfully
  - Related: CR-006 (path validation), SEC-004 (Path.relative_to security)
- [AUDIT-GAP-003@c3d5f2] 2024-12-27: **Large files (200KB+, 5000+ lines) should be split into focused modules**
  - During migration, multiple smaller files were consolidated: 7 entity files → entities.py (16KB), multiple adapters → sqlite.py (62KB), 11 CLI files → cli.py (209KB, 5718 lines)
  - Large consolidated files have trade-offs: simpler directory structure vs reduced modularity, harder to review, more merge conflicts
  - Split large files using phased approach: extract utilities first (output functions, helpers), then group related commands
  - Pattern: Identify extractable subsets by function type (_output_*, editor helpers, command groups), create new modules, import and use
  - For cli.py (5718 lines): extract cli_output.py (~400 lines of _output_*), cli_editor.py (~200 lines of editor functions), then group commands (epic, project, deps, labels, etc.)
  - Document with investigation notes before starting - measure line counts, identify phases, estimate effort
  - After investigation: 3-phase plan created, can be done incrementally (Phase 1: ~400 lines, provides immediate value)
  - Related: PERF-007 (batch operations - also large refactor)
- [AUDIT-GAP-008@e5f6a7] 2025-12-27: **MCP (Model Context Protocol) is for external AI integration, not CLI tools**
  - During git module migration audit, discovered 26K of MCP tools were not migrated
  - MCP enables external AI systems to call tools via MCP server protocol (stdio, SSE)
  - dot-work is a CLI tool for developers, not an MCP server for external systems
  - Architectural decision: don't migrate MCP tools because they don't fit the architecture
  - Pattern: When auditing migrations, check if "missing" code fits the target architecture
  - Source code preserved in incoming/ for future reference if needed
  - Related: AUDIT-GIT-003 (git migration audit), AUDIT-GAP-009 (example code migration)
- [AUDIT-GAP-009@d6e7f8] 2025-12-27: **Example code becomes stale, tests provide better API documentation**
  - During git module migration audit, discovered 450 lines of examples were not migrated
  - Examples use programmatic API (not CLI) and become stale when imports change
  - For dot-work (CLI-focused tool), examples are less critical than for libraries
  - Tests provide better API examples: always current, demonstrate actual usage
  - CLI help text (--help) provides usage guidance for end users
  - Pattern: When auditing migrations, check if "missing" examples are actually needed
  - Source code preserved in incoming/ for reference if needed later
  - Related: AUDIT-GAP-008 (MCP tools - also documented exclusion)
- [PERF-008@h0c2d7] 2025-12-27: **Issues can be resolved by other fixes**
  - PERF-008 (string concatenation) was addressed by PERF-004 (streaming metrics)
  - When investigating issues, check if related fixes already resolved the concern
  - The issue description may reference old code that's since been refactored
  - Pattern: Verify current code state before implementing fixes
- [PERF-009@i1d3e8] 2025-12-27: **Micro-optimizations require profiling evidence**
  - PERF-009 (dict lookups) is technically valid but low value
  - Dictionary lookups are O(1) and very fast in CPython
  - Readability and maintainability often outweigh micro-optimizations
  - Only optimize when profiling shows actual bottleneck, not theoretical concerns
  - Pattern: Document "won't fix unless profiling shows need" for micro-optimizations
- [PERF-002@g2h3i4] 2025-12-27: **Pre-build lookups to avoid O(n²) nested loops**
  - O(n²) nested loops occur when outer loop contains repeated work for inner iterations
  - Git branch lookup was iterating all commits for each branch, for each commit analyzed
  - Solution: Build lookup table (dict) once, use O(1) lookups in inner loop
  - Pattern: `mapping = {key: value for key, value in expensive_generator()}` then `mapping.get(key)`
  - Trade-off: O(N×M) memory for cache vs O(N×M×C) CPU where C = commits analyzed
  - After fix: 83 git tests pass, branch lookup is O(1) cache.get() instead of nested loop
  - Related: PERF-001 (N+1 queries), PERF-003 (SQL filtering), PERF-004 (streaming aggregations)
- [CR-001@f8a2c1] 2025-12-27: **Never write secrets to disk, even in ephemeral containers**
  - Writing credentials to ~/.git-credentials is a security risk even in temporary containers
  - Image commits, container logs, debugging tools can all expose plaintext files
  - Solution: Use GIT_ASKPASS environment variable with helper script that echoes token
  - Pattern: `cat > /tmp/askpass.sh << 'EOF'` then `export GIT_ASKPASS=/tmp/askpass.sh`
  - Git calls the askpass script when credentials needed instead of reading from disk
  - After fix: 21 container tests pass, no credentials written to filesystem
  - Related: SEC-001 (command injection), SEC-008 (temp file permissions), SEC-009 (audit logging)
- [CR-002@b3d5e7] 2025-12-27: **Test coverage starts with validation functions (low-hanging fruit)**
  - Complex modules often have simple validation functions that are easy to test
  - Start with validation functions for quick coverage wins (100% possible)
  - Pattern: Test valid cases, invalid cases, edge cases (empty, None, boundaries)
  - For `validate_docker_image()`: 14 tests covering all format variations
  - For `validate_dockerfile_path()`: 7 tests covering path traversal scenarios
  - After fix: Coverage improved from ~0% to 33% for core.py (+13 percentage points)
  - Remaining work: `_resolve_config()` (172 lines) needs extensive mocking/fixtures
  - Related: CR-003 (logging), CR-004 (global state)
- [CR-003@c4f8a2] 2025-12-27: **Logging is essential for production debugging**
  - Start with module-level logger: `logger = logging.getLogger(__name__)`
  - Log at appropriate levels: INFO for milestones, DEBUG for details, ERROR for failures
  - Always mask sensitive values: show presence as boolean, not actual tokens
  - Pattern: `logger.info()` for user-visible events, `logger.debug()` for diagnostics
  - After fix: Logging added throughout core.py (INFO at milestones, DEBUG for details)
  - Sensitive masking: `has_github_token={bool(token)}` not `github_token={token}`
  - Related: CR-002 (testing), CR-004 (global state)
