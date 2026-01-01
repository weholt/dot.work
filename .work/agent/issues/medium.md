# Medium Priority Issues (P2)

Enhancements, technical debt, code quality improvements.

(All completed issues moved to history.md)

---
---
id: "RES-001@e4f7a2"
title: "Investigate and fix SQLite database connection resource leaks"
description: "ResourceWarnings for unclosed database connections in integration tests"
created: 2026-01-01
section: "db_issues"
tags: [resource-leak, sqlite, database, tests, cleanup]
type: bug
priority: medium
status: proposed
references:
  - tests/integration/db_issues/conftest.py
  - tests/integration/db_issues/test_advanced_filtering.py
  - tests/integration/db_issues/test_agent_workflows.py
  - tests/integration/db_issues/test_bulk_operations.py
  - tests/integration/db_issues/test_dependency_model.py
  - src/dot_work/db_issues/adapters/sqlite.py
  - tests/conftest.py
---

### Problem
Integration tests are generating ResourceWarnings for unclosed SQLite database connections:
- 50+ warnings across multiple test files
- Warnings occur during `gc.collect()` in test teardown (conftest.py:206)
- Pattern: `ResourceWarning: unclosed database in <sqlite3.Connection object at 0x...>`

Affected tests:
- `test_advanced_filtering.py::TestAdvancedFiltering::test_filter_by_date_range`
- `test_agent_workflows.py::TestAgentWorkflow` (all tests)
- `test_bulk_operations.py` (all tests)
- `test_dependency_model.py::TestDependencyDataModel` (all tests)

### Affected Files
- `tests/integration/db_issues/conftest.py` (session/fixture management)
- `src/dot_work/db_issues/adapters/sqlite.py` (create_db_engine, Session usage)
- `tests/conftest.py` (gc.collect calls at line 206, pytest_sessionfinish)

### Importance
While tests pass, resource leaks indicate:
1. Potential memory growth in long-running processes
2. File descriptor leaks (SQLite keeps files open)
3. Poor resource hygiene (connections not properly closed)
4. CI noise (warnings clutter test output)
5. Possible production issue if same patterns exist in application code

### Root Cause Analysis Needed
1. **Session lifecycle**: Are Sessions created but not closed?
2. **Engine disposal**: Is `engine.dispose()` called consistently?
3. **StaticPool behavior**: Does StaticPool keep connections alive longer than expected?
4. **Fixture scope**: Is session-scoped engine conflicting with function-scoped sessions?
5. **Integration test runner**: The `integration_cli_runner` fixture creates a local engine but may not dispose it

### Proposed Solution
1. **Phase 1: Investigation**
   - Enable `tracemalloc` to get stack traces of where connections are allocated
   - Add explicit logging in `create_db_engine()` and Session creation
   - Verify connection count before/after each test fixture
   - Check if Session context manager (`with Session()`) is used everywhere

2. **Phase 2: Fix identified leaks**
   - Ensure all Session objects use context manager or explicit `close()`
   - Add `engine.dispose()` to any fixture that creates an engine
   - Review StaticPool usage - consider QueuePool with max_overflow=0
   - Add connection counting to verify leaks are fixed

3. **Phase 3: Prevention**
   - Add pytest warning filter to turn ResourceWarnings into errors
   - Add pre-commit hook to run tests with `-W error::ResourceWarning`
   - Document Session/Engine lifecycle patterns

### Acceptance Criteria
- [ ] Investigation report identifies exact source of leaks (with stack traces)
- [ ] All ResourceWarnings eliminated from integration test runs
- [ ] Connection count verified to be 0 after test session finishes
- [ ] Documentation updated for Session/Engine lifecycle
- [ ] Pre-commit hook prevents future resource leaks
- [ ] No regression in test performance or functionality

### Notes
The `integration_cli_runner` fixture (conftest.py:169-198) creates an engine and calls `SQLModel.metadata.create_all()` but only disposes in finally block - the yielded CliRunner may spawn subprocesses that keep connections open. Check if subprocess tests are the source.

Session-scoped `test_engine` fixture properly disposes, but the autouse `_reset_database_state` fixture creates new Sessions each test - verify those are closed (they use `with Session()` which should be safe).

---