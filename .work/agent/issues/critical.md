# Critical Issues (P0)

Blockers, security issues, data loss risks.

---
id: "MEM-001@8f3a2c"
title: "Memory Leak: SQLAlchemy engine accumulation during test suite"
description: "Each test creates new SQLAlchemy engine without proper metadata cleanup, causing 5-10GB memory growth"
created: 2025-12-26
section: "tests"
tags: [memory-leak, sqlalchemy, testing, critical]
type: bug
priority: critical
status: proposed
references:
  - tests/unit/db_issues/conftest.py
  - src/dot_work/db_issues/adapters/sqlite.py
  - memory_leak.md
---

### Problem
The test suite consumes 30-40GB of memory during full test runs. A primary contributor is SQLAlchemy engine accumulation in `tests/unit/db_issues/conftest.py`.

**Root Cause Analysis:**

At `tests/unit/db_issues/conftest.py:98-127`, each test creates a new SQLAlchemy engine:

```python
@pytest.fixture
def in_memory_db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)  # Registers tables globally
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

**Why this leaks memory:**
1. `SQLModel.metadata` is a **global singleton** that maintains internal references to all registered tables
2. Each `create_all()` call adds entries to internal reflection caches
3. `engine.dispose()` closes connections but does NOT clear metadata-level caches
4. The `StaticPool` used for `:memory:` databases holds the connection until explicit disposal
5. Over hundreds of tests, this accumulates ~50-100MB per test module

**Evidence:** Running memory profiler shows steady memory growth throughout db_issues test execution, with no release between tests.

### Affected Files
- `tests/unit/db_issues/conftest.py` (lines 98-127: in_memory_db fixture)
- `tests/unit/db_issues/conftest.py` (lines 157-184, 187-214, 217-241, 279-305: service fixtures creating UnitOfWork)
- `src/dot_work/db_issues/adapters/sqlite.py` (UnitOfWork holds session reference)

### Importance
**CRITICAL:** The test suite cannot run on machines with <32GB RAM without OOM kills. This blocks:
- CI/CD pipelines with memory constraints
- Developer machines with limited RAM
- Docker-based test execution

**Memory Impact:** ~5-10GB over full test suite due to metadata accumulation alone.

### Proposed Solution
1. **Use session-scoped engine** (single engine shared across all tests):
   ```python
   @pytest.fixture(scope="session")
   def db_engine():
       engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
       SQLModel.metadata.create_all(engine)
       yield engine
       engine.dispose()
       SQLModel.metadata.clear()  # Critical: clear global metadata cache

   @pytest.fixture
   def in_memory_db(db_engine) -> Generator[Session, None, None]:
       with Session(db_engine) as session:
           yield session
           session.rollback()  # Reset state between tests
   ```

2. **Add metadata cleanup at session end** (in tests/conftest.py):
   ```python
   def pytest_sessionfinish(session, exitstatus):
       SQLModel.metadata.clear()
   ```

3. **Single UnitOfWork per session** instead of multiple per test

### Acceptance Criteria
- [ ] Single engine used across all db_issues tests
- [ ] `SQLModel.metadata.clear()` called at session cleanup
- [ ] Memory growth during test run < 2GB
- [ ] All 277 db_issues tests still pass
- [ ] Test isolation maintained (rollback between tests)

### Notes
- Full investigation documented in `memory_leak.md`
- This is the largest single contributor to the 30-40GB memory issue
- Related issues: MEM-002 (libcst), MEM-003 (embeddings)

---
---
id: "MEM-002@9c4b3d"
title: "Memory Leak: LibCST CST trees not released after parsing"
description: "Code parser holds large CST trees in memory without explicit cleanup, causing 5-15GB growth"
created: 2025-12-26
section: "overview"
tags: [memory-leak, libcst, parsing, critical]
type: bug
priority: critical
status: proposed
references:
  - src/dot_work/overview/code_parser.py
  - tests/unit/overview/test_pipeline.py
  - memory_leak.md
---

### Problem
The overview module's code parser creates libcst Concrete Syntax Trees that consume 10-50x the file size in memory and are not explicitly released.

**Root Cause at `src/dot_work/overview/code_parser.py:73-89`:**

```python
def parse_python_file(path: Path, code: str, module_path: str) -> dict[str, list[Any]]:
    file_metrics, item_metrics = _calc_metrics(code)
    try:
        module = cst.parse_module(code)  # Creates large CST tree
    except Exception:
        return {"features": [], "models": []}

    collector = _Collector(...)
    module.visit(collector)  # Visitor holds references to CST nodes
    return {"features": collector.features, "models": collector.models}
    # module and collector go out of scope but may not be GC'd immediately
```

**Why this leaks memory:**
1. LibCST creates a **complete Concrete Syntax Tree** with full whitespace/formatting preservation
2. For large Python files, CST can consume 10-50x the file size (a 50KB file → 500KB-2.5MB CST)
3. The `_Collector` visitor stores references to CST nodes in Feature/Model objects
4. The module-level `_MODULE_TEMPLATE = cst.Module([])` holds a singleton reference
5. Python's GC may not immediately collect circular references in CST structures

**Additional Issue at line 31:**
```python
_MODULE_TEMPLATE = cst.Module([])  # Global singleton - never released
```

This template is used for `code_for_node()` rendering and holds internal caches.

### Affected Files
- `src/dot_work/overview/code_parser.py` (lines 31, 73-89)
- `tests/unit/overview/test_pipeline.py` (triggers parsing in each test)

### Importance
**CRITICAL:** Each overview test parses Python files, creating large CST trees that accumulate:
- ~50-200MB per large Python file parsed
- Tests run multiple files per test case
- Combined with other leaks, contributes to 30-40GB total

### Proposed Solution
1. **Explicit cleanup after parsing:**
   ```python
   def parse_python_file(path: Path, code: str, module_path: str) -> dict[str, list[Any]]:
       file_metrics, item_metrics = _calc_metrics(code)
       try:
           module = cst.parse_module(code)
           collector = _Collector(...)
           module.visit(collector)
           result = {"features": collector.features, "models": collector.models}

           # Explicit cleanup to help GC
           del module
           del collector
           gc.collect()  # Force collection of CST structures

           return result
       except Exception:
           return {"features": [], "models": []}
   ```

2. **Avoid storing CST node references in results** - extract primitive data instead

3. **Clear module template cache periodically** (if needed)

### Acceptance Criteria
- [ ] CST trees explicitly deleted after parsing
- [ ] No CST node references stored in Feature/Model objects
- [ ] Memory usage per file parse bounded to 2x file size
- [ ] All overview tests still pass
- [ ] `gc.collect()` called after batch parsing operations

### Notes
- LibCST is known for high memory usage - this is documented behavior
- Consider lazy parsing (parse on demand) for large codebases
- Full investigation in `memory_leak.md`
- Related: MEM-001 (SQLAlchemy), MEM-003 (embeddings)

---
---
id: "BUG-001@fe313e"
title: "Installed dot-work tool missing python.build module"
description: "UV tool installation outdated - missing build/ submodule that exists in source"
created: 2025-12-26
section: "installation"
tags: [installation, uv-tool, module-not-found, python]
type: bug
priority: critical
status: proposed
references:
  - src/dot_work/python/__init__.py
  - src/dot_work/python/build/cli.py
  - src/dot_work/python/build/runner.py
---

### Problem
When running `dot-work install` (or any dot-work command), the installed tool fails with:

```
ModuleNotFoundError: No module named 'dot_work.python.build'
```

The import occurs at `dot_work/python/__init__.py:12`:
```python
from dot_work.python.build.cli import run_build
```

### Root Cause Analysis

**Source Code State (Current Repository):**
- The `build/` module EXISTS at `src/dot_work/python/build/`
- Files present: `cli.py`, `runner.py`, `__init__.py`
- Git shows recent commits: "Build clean", "Fucking agents ...."
- Working tree is clean - build module is tracked

**Installed Package State:**
- Location: `~/.local/share/uv/tools/dot-work/lib/python3.13/site-packages/dot_work/python/`
- Directories present: `__pycache__`, `scan`
- **MISSING:** `build/` directory
- Install timestamp: Dec 26 02:36 (likely outdated)

**Conclusion:** The installed uv tool version predates the addition of the `build/` module to the codebase.

### Affected Files
- Installed package: `~/.local/share/uv/tools/dot-work/lib/python3.13/site-packages/dot_work/python/` (missing build/)
- Source import: `src/dot_work/python/__init__.py` (line 12)

### Importance
**CRITICAL:** The `dot-work` command is completely broken. All commands fail with `ModuleNotFoundError` because the top-level `__init__.py` imports the missing module during package initialization.

This blocks all dot-work functionality until resolved.

### Error / Exception Details
```
Traceback (most recent call last):
  File "/home/thomas/.local/bin/dot-work", line 4, in <module>
    from dot_work.cli import app
  File "/home/thomas/.local/share/uv/tools/dot-work/lib/python3.13/site-packages/dot_work/cli.py", line 16, in <module>
    from dot_work.python import python_app
  File "/home/thomas/.local/share/uv/tools/dot-work/lib/python3.13/site-packages/dot_work/python/__init__.py", line 12, in <module>
    from dot_work.python.build.cli import run_build
ModuleNotFoundError: No module named 'dot_work.python.build'
```

### Proposed Solution
1. **Reinstall the tool from current source:**
   ```bash
   cd /home/thomas/Workspace/dot.work
   uv tool uninstall dot-work
   uv tool install .
   ```

2. **Alternatively, use `uv tool upgrade` if supported:**
   ```bash
   uv tool upgrade dot-work
   ```

3. **Prevent future issues:** Consider adding a post-commit hook or CI check to verify tool installation is up-to-date after commits that add new submodules.

### Acceptance Criteria
- [ ] Tool reinstalled from current source code
- [ ] `dot-work --help` runs without ModuleNotFoundError
- [ ] `dot-work python build` command works (build module functional)
- [ ] All existing subcommands (scan, etc.) still work
- [ ] Note added to README about reinstalling after major updates

### Notes
- This issue highlights a gap: no automated verification that installed tool matches source
- Consider adding `uv tool install . --reinstall` to development workflow
- The branch `migrating-using-opencode` is 13 commits ahead of origin - these new features aren't in the installed version

Investigation completed using systematic debugging process:
- Phase 1: Root cause identified (outdated installation vs current source)
- Evidence: Git history shows build module exists; installed package missing it
- No code fix needed - reinstallation required

---
---
