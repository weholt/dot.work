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
