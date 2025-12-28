# High Priority Issues (P1)

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

---
id: "CR-005@e7f3a1"
title: "Duplicate generate_cache_key function in git module"
description: "Same function defined twice in utils.py and cache.py creates maintenance risk"
created: 2024-12-27
section: "git"
tags: [duplicate-code, maintainability, refactor]
type: refactor
priority: high
status: proposed
references:
  - src/dot_work/git/utils.py
  - src/dot_work/git/services/cache.py
---

### Problem
`generate_cache_key()` is defined TWICE with identical implementations - once in `utils.py` (lines 75-79) and once in `services/cache.py` (lines 410-426). This duplication creates maintenance risk and conceptual confusion.

### Affected Files
- `src/dot_work/git/utils.py` (lines 75-79)
- `src/dot_work/git/services/cache.py` (lines 410-426)

### Importance
Changes to caching behavior may only update one copy, leading to subtle bugs.

### Proposed Solution
1. Keep only one implementation in `utils.py`
2. Import from utils in cache.py
3. Verify all call sites use the single implementation

### Acceptance Criteria
- [ ] Only one `generate_cache_key()` exists
- [ ] All existing tests pass
- [ ] No regression in cache behavior

---

---
id: "CR-006@a2b4c8"
title: "Silent failure in git commit analysis loses errors"
description: "Errors during commit analysis are logged and skipped without indication to callers"
created: 2024-12-27
section: "git"
tags: [error-handling, observability]
type: bug
priority: high
status: proposed
references:
  - src/dot_work/git/services/git_service.py
---

### Problem
In `git_service.py:100-102`, commit analysis errors are logged and `continue`d silently. Failed commits are simply omitted from results with no indication to the caller that analysis was incomplete. A user seeing 100% progress has no idea if 50 commits failed silently.

### Affected Files
- `src/dot_work/git/services/git_service.py` (lines 100-102)

### Importance
Users may make decisions based on incomplete analysis data. Silent failures hide data quality issues.

### Proposed Solution
1. Add error aggregation to return failed commit count/details
2. Return a result object with `successful`, `failed`, and `errors` fields
3. Log summary of failures at end of analysis

### Acceptance Criteria
- [ ] Analysis returns failed commit count
- [ ] Failed commit IDs are available for debugging
- [ ] Summary logged at end of analysis
- [ ] No silent data loss

---

---
id: "CR-007@b5c9d3"
title: "Massive dead code in file_analyzer.py (500+ lines unused)"
description: "FileAnalyzer has 700+ lines of unused code for dependency extraction"
created: 2024-12-27
section: "git"
tags: [dead-code, cleanup, deletion-test]
type: refactor
priority: high
status: proposed
references:
  - src/dot_work/git/services/file_analyzer.py
---

### Problem
`FileAnalyzer` (752 lines) is massively over-engineered. Only `categorize_file()` (~40 lines of logic) is actually used. The file contains 700+ lines of unused code including:
- `get_file_dependencies()` - never called (~100 lines)
- `analyze_file_content()` - never called (~30 lines)
- Language detection for Python, Node, Go, Ruby, Java, Docker - all unused

### Affected Files
- `src/dot_work/git/services/file_analyzer.py`

### Importance
Dead code increases cognitive load, test surface, and maintenance burden. It suggests requirements were anticipated but never materialized.

### Proposed Solution
1. Delete unused methods: `get_file_dependencies()`, `analyze_file_content()`, all language-specific extraction
2. Keep only `categorize_file()` and its helpers
3. Reduce file to ~100 lines

### Acceptance Criteria
- [ ] Unused methods deleted
- [ ] Tests still pass
- [ ] File reduced to <150 lines
- [ ] Functionality preserved

---

---
id: "CR-008@c6d8e4"
title: "No unit tests for git_service.py core business logic"
description: "853-line core service has zero direct test coverage"
created: 2024-12-27
section: "git"
tags: [testing, quality]
type: test
priority: high
status: completed
completed: 2024-12-28
references:
  - src/dot_work/git/services/git_service.py
  - tests/unit/git/
---

### Problem
`git_service.py` (853 lines) is the core git analysis service. No tests exist for this service, `services/cache.py`, or `services/llm_summarizer.py`. Critical business logic is untested.

### Affected Files
- `src/dot_work/git/services/git_service.py`
- `tests/unit/git/` (missing test files)

### Importance
Core analysis logic is untested. Regressions cannot be caught before production.

### Proposed Solution
1. Create `tests/unit/git/test_git_service.py`
2. Test `compare_refs()`, `_get_commit_branch()`, key analysis methods
3. Mock gitpython and external dependencies

### Acceptance Criteria
- [x] Test file created (35 tests added)
- [x] Key methods have test coverage
- [x] Coverage 56% for git_service.py (complex integration logic uncovered)

### Solution
Created comprehensive unit test file `tests/unit/git/test_git_service.py` with 35 tests covering:
- Initialization and error handling
- Commit analysis logic
- Branch cache mapping (O(1) lookup optimization)
- Commit retrieval and filtering
- Message extraction
- Impact area identification
- Breaking change detection
- Security relevance detection
- Commit similarity calculation
- Summary generation
- File category aggregation
- Tag retrieval
- File diff analysis (added, deleted, modified, binary)
- Commit comparison helpers (differences, themes, impact, risk, migration notes)

**Bonus fix:** Fixed bug in `_find_common_themes()` where `extend()` was incorrectly used instead of `append()`, causing list corruption.

Coverage is 56% - remaining uncovered lines are primarily in the `compare_refs()` integration method which requires extensive mocking of GitPython, cache, and tag management. The unit tests provide solid coverage of all core helper methods.

---

---
id: "CR-009@d7e9f5"
title: "Harness module uses print() and SystemExit instead of logging and exceptions"
description: "Multiple AGENTS.md violations in harness module"
created: 2024-12-27
section: "harness"
tags: [standards, logging, error-handling]
type: bug
priority: high
status: proposed
references:
  - src/dot_work/harness/client.py
  - src/dot_work/harness/tasks.py
  - src/dot_work/harness/cli.py
---

### Problem
The harness module has multiple violations of AGENTS.md standards:
1. `client.py:160-181` uses `print()` instead of `logging`
2. `tasks.py:87-91` uses `SystemExit` for validation errors instead of custom exceptions
3. `cli.py:148-153` catches `SystemExit` broadly, masking actual error types

### Affected Files
- `src/dot_work/harness/client.py`
- `src/dot_work/harness/tasks.py`
- `src/dot_work/harness/cli.py`

### Importance
Using `print()` prevents log level control. `SystemExit` is a control flow exception that shouldn't be used for validation.

### Proposed Solution
1. Replace all `print()` with `logging`
2. Create `TaskFileError` exception for validation
3. Catch specific exceptions in CLI

### Acceptance Criteria
- [ ] No `print()` in harness module
- [ ] Custom exception for task file errors
- [ ] Specific exception handling in CLI

---

---
id: "CR-010@e8f0a6"
title: "Harness module has zero test coverage"
description: "No test files exist for harness module"
created: 2024-12-27
section: "harness"
tags: [testing, quality]
type: test
priority: high
status: completed
completed: 2024-12-28
references:
  - src/dot_work/harness/
  - tests/unit/harness/
---

### Problem
No test files exist for the harness module. Zero test coverage for critical autonomous agent execution code. The module contains:
- `tasks.py` with pure functions that are trivially testable
- `client.py` with SDK integration requiring mocked tests

### Affected Files
- `src/dot_work/harness/` (all files)
- `tests/unit/harness/` (missing directory)

### Importance
Autonomous agent execution without tests is high risk. Bugs could cause unintended agent behavior.

### Proposed Solution
1. Create `tests/unit/harness/` directory
2. Add tests for `load_tasks`, `count_done`, `next_open_task`, `validate_task_file`
3. Add integration tests with mocked SDK client

### Acceptance Criteria
- [x] Test directory created (tests/unit/harness/)
- [x] Pure functions have unit tests (tasks.py: 100% coverage)
- [x] Client integration tested with mocks (client.py: 78% coverage)

### Solution
Created comprehensive test suite for the harness module:

**test_tasks.py** (25 tests):
- Task dataclass immutability
- Loading tasks from markdown files (checkboxes, indented, empty files)
- Handling special characters and uppercase X
- Counting completed tasks
- Finding next open task
- Validating task files (exists, has tasks, proper format)
- TaskFileError exception behavior

**test_client.py** (12 tests):
- SDK availability flag
- HarnessClient initialization (defaults and custom params)
- Error handling when SDK unavailable
- ClaudeAgentOptions creation
- run_iteration sends correct prompt
- run_harness_async with tasks and stopping when done
- Invalid task file raises TaskFileError
- run_harness synchronous wrapper
- PermissionMode type validation

**Coverage:**
- `tasks.py`: 100% coverage
- `client.py`: 78% coverage (uncovered lines are import/try-except wrappers)
- `__init__.py`: 100% coverage
- Overall: 49% (cli.py excluded - CLI modules typically tested via integration)

All tests pass, type checking and linting verified.

---

---
id: "CR-011@f9a1b7"
title: "Knowledge graph Database class is a god object with 50+ methods"
description: "db.py has 1800+ lines with mixing concerns"
created: 2024-12-27
section: "knowledge_graph"
tags: [architecture, refactor, maintainability]
type: refactor
priority: high
status: proposed
references:
  - src/dot_work/knowledge_graph/db.py
---

### Problem
The `Database` class in `db.py` has grown to 1800+ lines with 50+ methods covering documents, nodes, edges, FTS, embeddings, collections, topics, and project settings. This violates SRP.

### Affected Files
- `src/dot_work/knowledge_graph/db.py`

### Importance
God classes are hard to test, maintain, and extend. Changes have high risk of unintended side effects.

### Proposed Solution
Consider splitting into focused repositories:
- `DocumentRepository`
- `NodeRepository`
- `EdgeRepository`
- `EmbeddingRepository`
- `CollectionRepository`

### Acceptance Criteria
- [ ] Database class responsibilities clearly defined
- [ ] Consider extraction of focused repositories
- [ ] Tests continue to pass after refactoring

---

---
id: "CR-012@a0b2c8"
title: "Duplicated scope filtering code in knowledge_graph search modules"
description: "ScopeFilter and _build_scope_sets duplicated in search_fts.py and search_semantic.py"
created: 2024-12-27
section: "knowledge_graph"
tags: [duplicate-code, refactor]
type: refactor
priority: high
status: completed
completed: 2024-12-28
references:
  - src/dot_work/knowledge_graph/scope.py
  - src/dot_work/knowledge_graph/search_fts.py
  - src/dot_work/knowledge_graph/search_semantic.py
---

### Problem
Both `search_fts.py` and `search_semantic.py` contain nearly identical `ScopeFilter` dataclass (lines 34-48 and 31-45) and `_build_scope_sets()` / `_node_matches_scope()` functions (90%+ code duplication).

### Affected Files
- `src/dot_work/knowledge_graph/search_fts.py`
- `src/dot_work/knowledge_graph/search_semantic.py`

### Importance
Duplicated code means changes must be made in two places. Risk of divergent behavior.

### Proposed Solution
Extract to a shared `scope.py` module:
1. Move `ScopeFilter` dataclass
2. Move `_build_scope_sets()` function
3. Move `_node_matches_scope()` function
4. Import in both search modules

### Acceptance Criteria
- [x] Shared scope.py created
- [x] No duplication between search modules
- [x] All tests pass (378 knowledge graph tests)

### Solution
Created `src/dot_work/knowledge_graph/scope.py` with:
- `ScopeFilter` dataclass (for project/topic/shared filtering)
- `build_scope_sets()` function (pre-computes scope membership sets)
- `node_matches_scope()` function (checks if node matches scope)

Updated both `search_fts.py` and `search_semantic.py` to:
- Import from shared module
- Remove local duplicates
- Use shared functions

**Lines removed:** 112 lines of duplicated code eliminated

---

---
id: "CR-013@b1c3d9"
title: "Mutable dimensions state in embedders causes unpredictable behavior"
description: "Embedding dimension mutated during embed() calls can cause race conditions"
created: 2024-12-27
section: "knowledge_graph"
tags: [bug, state-management, concurrency]
type: bug
priority: high
status: completed
completed: 2024-12-28
references:
  - src/dot_work/knowledge_graph/embed/ollama.py
  - src/dot_work/knowledge_graph/embed/openai.py
---

### Problem
In `ollama.py:36` and `openai.py:63-64`, `dimensions` is set from config but then mutated during `embed()` calls (ollama.py:61-62, openai.py:165-166). This mutation of presumably-immutable config state can cause race conditions in concurrent usage.

### Affected Files
- `src/dot_work/knowledge_graph/embed/ollama.py`
- `src/dot_work/knowledge_graph/embed/openai.py`

### Importance
Race conditions in embedders could cause incorrect vector dimensions, corrupting the embedding database.

### Proposed Solution
1. Don't mutate `self.dimensions` after initialization
2. Validate dimensions at initialization time
3. Or make dimension discovery a one-time operation with locking

### Acceptance Criteria
- [x] No mutation of config state after init
- [x] Thread-safe embedding operations
- [x] Tests verify dimension consistency (38 embedder tests pass)

### Solution
Made `dimensions` a private property with thread-safe lazy initialization:

**Changes to both embedders:**
- Made `dimensions` a read-only property accessing private `_dimensions`
- Added `threading.Lock()` for thread-safe dimension discovery
- Added `_dimensions_discovered` flag to ensure one-time initialization
- Double-checked locking pattern prevents race conditions

**Thread-safe pattern:**
```python
if not self._dimensions_discovered and self._dimensions is None:
    with self._dimensions_lock:
        if not self._dimensions_discovered and self._dimensions is None:
            self._dimensions = len(embedding)
            self._dimensions_discovered = True
```

---

---
id: "CR-014@c2d4e0"
title: "No logging in knowledge_graph graph.py and db.py"
description: "Graph building and database operations are invisible without logging"
created: 2024-12-27
section: "knowledge_graph"
tags: [observability, logging]
type: enhancement
priority: high
status: completed
completed: 2024-12-28
references:
  - src/dot_work/knowledge_graph/graph.py
  - src/dot_work/knowledge_graph/db.py
---

### Problem
`graph.py` has no logging statements in the graph building process. `db.py` (1800+ lines) also has no logging. When ingestion fails or produces unexpected results, there's no way to trace what happened.

### Affected Files
- `src/dot_work/knowledge_graph/graph.py`
- `src/dot_work/knowledge_graph/db.py`

### Importance
Without logging, failures are undebuggable. Large ingestion jobs provide no feedback.

### Proposed Solution
1. Add structured logging for key operations in graph.py
2. Add logging for schema migrations, connection lifecycle, errors in db.py
3. Use appropriate log levels (DEBUG for verbose, INFO for milestones)

### Acceptance Criteria
- [x] Logging added to graph building
- [x] Logging added to database operations
- [x] Error conditions logged at WARNING/ERROR

### Solution
Added structured logging throughout both modules:

**graph.py:**
- `build_graph()` - Logs document being processed, block count
- `build_graph_from_blocks()` - Progress updates, completion stats (nodes/edges)
- `_ensure_document()` - Document creation/replacement operations
- `get_node_tree()` - Tree building progress

**db.py:**
- `__init__()` - Database initialization
- `_get_connection()` - Connection lifecycle
- `_configure_pragmas()` - Database configuration
- `_load_vec_extension()` - Extension loading status
- `_ensure_schema()` - Schema version checking
- `_apply_migrations()` - Migration application with completion logging
- `transaction()` - Transaction rollback logging on errors
- `close()` - Connection closure

All logging uses appropriate levels:
- DEBUG for verbose operational details
- INFO for milestones (migration completion, graph building stats)
- WARNING for transaction rollbacks and error conditions

---

---
id: "CR-015@d3e5f1"
title: "overview/cli.py is dead code"
description: "The overview CLI module is never used - main CLI imports directly from pipeline"
created: 2024-12-27
section: "overview"
tags: [dead-code, cleanup]
type: refactor
priority: high
status: completed
completed: 2024-12-28
references:
  - src/dot_work/cli.py
---

### Problem
`overview/cli.py` defined its own Typer app, but `src/dot_work/cli.py` imports and uses `analyze_project` and `write_outputs` directly from the pipeline. The overview-specific CLI was never registered as a subcommand or used.

### Affected Files
- ~~`src/dot_work/overview/cli.py`~~ (deleted)
- `src/dot_work/cli.py`

### Importance
Dead code increases maintenance burden and cognitive load.

### Proposed Solution
1. Delete `src/dot_work/overview/cli.py`
2. Or integrate it properly as a subcommand if the functionality is needed

### Acceptance Criteria
- [x] Dead code removed or integrated
- [x] Existing functionality preserved

### Solution
Deleted `src/dot_work/overview/cli.py` (42 lines). The main CLI already has the `overview` command that provides the same functionality by importing `analyze_project` and `write_outputs` directly from `dot_work.overview.pipeline`.

All 54 overview tests still pass. No imports of the deleted file were found in the codebase.

---

---
id: "CR-016@e4f6a2"
title: "No logging in overview code_parser.py makes debugging impossible"
description: "Parse failures, metric calculations, and errors are silent"
created: 2024-12-27
section: "overview"
tags: [observability, logging]
type: enhancement
priority: high
status: completed
completed: 2024-12-28
references:
  - src/dot_work/overview/code_parser.py
  - src/dot_work/overview/pipeline.py
  - src/dot_work/overview/scanner.py
---

### Problem
`code_parser.py` has no logging. Parse failures (line 85-86), metric calculation errors (lines 56-57, 70-71), and other issues return empty/zero values silently. `pipeline.py` and `scanner.py` also lack logging.

### Affected Files
- `src/dot_work/overview/code_parser.py`
- `src/dot_work/overview/pipeline.py`
- `src/dot_work/overview/scanner.py`

### Importance
When parsing fails or metrics return zeros, there's no way to diagnose without adding print statements.

### Proposed Solution
1. Add structured logging for parse failures
2. Log metric calculation issues
3. Add progress logging for pipeline

### Acceptance Criteria
- [x] Parse failures logged
- [x] Metric errors logged
- [x] Progress visible during analysis

### Solution
Added structured logging to `code_parser.py`:

**`_calc_metrics()`:**
- Debug log for high complexity items (complexity > 10)
- Debug log for metrics calculation failures

**`parse_python_file()`:**
- Debug log when parsing starts
- Warning log for parse failures with file path and error
- Debug log with counts of features and models found

**`export_features_to_json()`:**
- Debug log for export start
- Info log for successful export with counts
- Error log for export failures

All 54 overview tests still pass.

---

---
id: "CR-017@f5a7b3"
title: "Bare exception handlers swallow errors in review/server.py"
description: "Multiple except Exception blocks silently return empty values"
created: 2024-12-27
section: "review"
tags: [error-handling, observability]
type: bug
priority: high
status: completed
completed: 2024-12-28
references:
  - src/dot_work/review/server.py
---

### Problem
In `server.py:90-93` and `server.py:131-135`, multiple `except Exception` blocks silently swallow errors and return empty values. AGENTS.md prohibits bare `except:`. These silent failures make debugging impossible when file reads fail.

### Affected Files
- `src/dot_work/review/server.py`

### Importance
Silent failures mask bugs. Users see empty results with no indication of errors.

### Proposed Solution
1. Catch specific exceptions (`FileNotFoundError`, `UnicodeDecodeError`)
2. Log errors before returning empty values
3. Consider returning error status to client

### Acceptance Criteria
- [x] Specific exceptions caught
- [x] Errors logged
- [x] No bare except Exception

### Solution
Fixed both bare exception handlers in `review/server.py`:

**`index()` function (lines 93-97):**
- Changed from `except Exception:` to `except (FileNotFoundError, PermissionError, OSError) as e:`
- Added `logger.warning("Failed to read file %s: %s", path, e)`

**`add_comment()` function (lines 135-140):**
- Changed from `except Exception:` to `except (FileNotFoundError, PermissionError, OSError) as e:`
- Added `logger.warning("Failed to read file %s for comment context: %s", inp.path, e)`

Both functions now catch specific I/O exceptions and log warnings before returning empty values, making debugging possible while maintaining graceful degradation.

---

---
id: "CR-018@a6b8c4"
title: "SearchService uses raw Session breaking architectural consistency"
description: "SearchService takes Session instead of UnitOfWork unlike all other services"
created: 2024-12-27
section: "db_issues"
tags: [architecture, consistency]
type: refactor
priority: high
status: completed
completed: 2024-12-28
references:
  - src/dot_work/db_issues/services/search_service.py
  - src/dot_work/db_issues/adapters/sqlite.py
---

### Problem
In `search_service.py:25-31`, `SearchService` takes a raw `Session` parameter while all other services use `UnitOfWork`. This breaks architectural consistency and makes composition difficult.

### Affected Files
- `src/dot_work/db_issues/services/search_service.py`
- `src/dot_work/db_issues/adapters/sqlite.py`

### Importance
Inconsistent interfaces make the codebase harder to understand and test.

### Proposed Solution
1. Change SearchService to accept UnitOfWork
2. Update all call sites
3. Maintain consistent service interface

### Acceptance Criteria
- [x] SearchService uses UnitOfWork
- [x] All services have consistent constructor signature

### Solution
Fixed architectural inconsistency by:

1. **Added `session` property to `UnitOfWork`** (`src/dot_work/db_issues/adapters/sqlite.py`):
   - Renamed internal `self.session` to `self._session`
   - Added `@property session()` that returns `self._session`
   - Provides access for services that need direct SQL execution
   - Updated all internal references to use `self._session`

2. **Refactored `SearchService`** (`src/dot_work/db_issues/services/search_service.py`):
   - Changed `__init__(self, session: Session)` to `__init__(self, uow: UnitOfWork)`
   - Updated all `self.session.exec()` calls to `self.uow.session.exec()`
   - Updated all `self.session.commit()` calls to `self.uow.session.commit()`

3. **Updated tests** (`tests/unit/db_issues/test_search_service.py`):
   - Added `db_uow_with_fts5` fixture that wraps `db_session_with_fts5` in `UnitOfWork`
   - Updated all test methods to use `db_uow_with_fts5: UnitOfWork`
   - All 313 db_issues tests pass

---

---
id: "CR-019@b7c9d5"
title: "IssueService merge_issues method is 148 lines"
description: "Single method handles too many responsibilities, violates <15 lines guideline"
created: 2024-12-27
section: "db_issues"
tags: [code-quality, refactor]
type: refactor
priority: high
status: completed
completed: 2025-12-28
references:
  - src/dot_work/db_issues/services/issue_service.py
---

### Problem
`merge_issues` method (lines 843-991) is 148 lines long, handling labels, descriptions, dependencies, comments, and source issue disposal. This violates the "Functions <15 lines" standard from AGENTS.md.

### Affected Files
- `src/dot_work/db_issues/services/issue_service.py`

### Importance
Long methods are hard to test, understand, and maintain.

### Solution Implemented
Extracted 5 private helper methods:
- `_merge_labels()` - Union of labels, preserve order
- `_merge_descriptions()` - Combine with separator
- `_merge_dependencies()` - Remap all relationships
- `_copy_comments()` - Copy with merge prefix
- `_handle_source_disposal()` - Close or delete source

Main method reduced from 148 to 38 lines (74% reduction).

### Acceptance Criteria
- [x] Method decomposed into focused helper functions
- [x] All 39 unit tests pass
- [x] Type checking and linting pass
- [x] Improved readability

---

---
id: "CR-020@c8d0e6"
title: "Missing tests for StatsService and SearchService"
description: "Services with raw SQL queries have no test coverage"
created: 2024-12-27
section: "db_issues"
tags: [testing, quality]
type: test
priority: high
status: completed
completed: 2025-12-28
references:
  - src/dot_work/db_issues/services/stats_service.py
  - src/dot_work/db_issues/services/search_service.py
  - tests/unit/db_issues/
---

### Problem
No tests found for `StatsService` or `SearchService`. Given these contain raw SQL queries, this is a high-risk area that needs test coverage.

### Affected Files
- `src/dot_work/db_issues/services/stats_service.py`
- `src/dot_work/db_issues/services/search_service.py`
- `tests/unit/db_issues/test_stats_service.py` - NEW
- `tests/unit/db_issues/test_search_service.py` - Already had comprehensive FTS5 injection tests

### Importance
Raw SQL without tests is high risk. FTS5 behavior varies and needs verification.

### Solution Implemented
1. Created `test_stats_service.py` with 14 comprehensive tests
2. Tests cover: status/priority/type grouping, metrics calculations, edge cases
3. SearchService already had 18 comprehensive FTS5 tests from CR-018
4. All 327 db_issues tests pass

### Acceptance Criteria
- [x] StatsService has test coverage (14 tests added)
- [x] SearchService has test coverage (18 tests already existed)
- [x] FTS5 edge cases tested (injection, DoS, syntax validation)

---

---
id: "CR-021@d9e1f7"
title: "Epic and label services load all issues into memory"
description: "Methods use limit=1000000 causing potential OOM on large datasets"
created: 2024-12-27
section: "db_issues"
tags: [performance, memory]
type: bug
priority: high
status: completed
completed: 2025-12-28
references:
  - src/dot_work/db_issues/services/epic_service.py
  - src/dot_work/db_issues/services/label_service.py
  - src/dot_work/db_issues/adapters/sqlite.py
---

### Problem
`get_all_epics_with_counts`, `get_epic_issues`, `get_epic_tree` (epic_service.py lines 346-373, 397-399, 427-429) and `get_all_labels_with_counts` (label_service.py line 410) all load ALL issues into memory with `limit=1000000`. For large datasets, this will cause memory issues.

### Affected Files
- `src/dot_work/db_issues/services/epic_service.py` - Updated 4 methods
- `src/dot_work/db_issues/services/label_service.py` - Updated 1 method
- `src/dot_work/db_issues/adapters/sqlite.py` - Added `get_epic_counts()` method

### Importance
Memory exhaustion on large projects. Silent degradation as project grows.

### Solution Implemented
1. Added `get_epic_counts()` to IssueRepository with SQL GROUP BY aggregation
2. Replaced `list_all(limit=1000000)` with `list_by_epic(epic_id)` for SQL filtering
3. Added SAFE_LIMIT (50000) for label counting with warning log
4. Fixed `get_epic_issues`, `get_epic_tree`, `get_all_epics_with_counts`, `_clear_epic_references`

### Acceptance Criteria
- [x] Counts computed at SQL level (get_epic_counts with GROUP BY)
- [x] No unbounded memory allocations (replaced with SQL filtering)
- [x] All 327 db_issues tests pass

---

---
id: "CR-022@e0f2a8"
title: "Uncaught exception on malformed version string in version/manager.py"
description: "calculate_next_version uses int(parts[X]) without validation"
created: 2024-12-27
section: "version"
tags: [error-handling, robustness]
type: bug
priority: high
status: completed
completed: 2025-12-28
references:
  - src/dot_work/version/manager.py
  - tests/unit/version/test_manager.py
---

### Problem
In `manager.py:80-83`, `calculate_next_version()` uses `int(parts[X])` without validation. If `current.version` is malformed (e.g., "1.2" instead of "2025.01.00001"), this raises an uncaught `IndexError` or `ValueError` with no helpful message.

### Affected Files
- `src/dot_work/version/manager.py` - Added validation with helpful error messages
- `tests/unit/version/test_manager.py` - Added 6 new validation tests

### Importance
Users with custom or legacy version strings will get cryptic errors.

### Solution Implemented
1. Validate version has exactly 3 parts before parsing
2. Validate all parts are valid integers
3. Validate year (2000-2100), month (1-12), build (1-99999) ranges
4. Added 6 comprehensive tests for all edge cases

### Acceptance Criteria
- [x] Invalid versions raise clear error with format specification
- [x] Format documented in error messages
- [x] Tests for edge cases (too few/too many parts, non-integers, out of range)

---

---
id: "CR-023@f1a3b9"
title: "freeze_version is 72 lines with multiple responsibilities"
description: "Method handles reading, parsing, changelog, git tagging, file writing"
created: 2024-12-27
section: "version"
tags: [code-quality, refactor]
type: refactor
priority: high
status: completed
completed: 2025-12-28
references:
  - src/dot_work/version/manager.py
---

### Problem
`freeze_version()` in `manager.py:140-212` is 72 lines long with multiple responsibilities: reading current version, parsing commits, generating changelog, creating git tags, writing files, committing. This violates the "Functions <15 lines" standard from AGENTS.md and makes it hard to test individual steps.

### Affected Files
- `src/dot_work/version/manager.py` - Refactored freeze_version and added 6 helper methods

### Importance
Long methods are hard to test and maintain. Changes have high risk.

### Solution Implemented
Decomposed into smaller helper methods:
- `_get_commits_since_last_tag()` - Parse commits since last tag
- `_generate_changelog_entry()` - Generate changelog markdown
- `_create_git_tag()` - Create git tag with error handling
- `_write_version_files()` - Write version.json and CHANGELOG.md
- `_commit_version_changes()` - Commit changes to git
- `_finalize_version_release()` - Orchestrate release finalization

Main method reduced from 72 to 36 lines (50% reduction).

### Acceptance Criteria
- [x] Method decomposed into focused helpers
- [x] Individual steps testable
- [x] All 56 version tests pass

---

---
id: "CR-024@a2b4c0"
title: "Git operations in freeze_version have no transaction/rollback"
description: "Failed tag creation followed by successful file write leaves inconsistent state"
created: 2024-12-27
section: "version"
tags: [error-handling, consistency]
type: bug
priority: high
status: proposed
references:
  - src/dot_work/version/manager.py
---

### Problem
Git operations in `manager.py:177-199` (`create_tag`, `index.add`, `index.commit`) can all fail but have no error handling. A failed `create_tag` followed by a successful `write_version` leaves the system in an inconsistent state.

### Affected Files
- `src/dot_work/version/manager.py` (lines 177-199)

### Importance
Partial failures can corrupt version state, requiring manual recovery.

### Proposed Solution
1. Wrap in transaction pattern
2. Add rollback logic for partial failures
3. Or fail fast before any writes

### Acceptance Criteria
- [ ] All-or-nothing semantics
- [ ] Clear error messages on failure
- [ ] Recovery path documented

---
id: "CR-024@a2b4c0"
title: "Git operations in freeze_version have no transaction/rollback"
description: "Failed tag creation followed by successful file write leaves inconsistent state"
created: 2024-12-27
section: "version"
tags: [error-handling, consistency]
type: bug
priority: high
status: completed
completed: 2025-12-28
references:
  - src/dot_work/version/manager.py
---

### Problem
Git operations in `manager.py:177-199` (`create_tag`, `index.add`, `index.commit`) can all fail but have no error handling. A failed `create_tag` followed by a successful `write_version` leaves the system in an inconsistent state.

### Affected Files
- `src/dot_work/version/manager.py` - Added transaction-like rollback semantics

### Importance
Partial failures can corrupt version state, requiring manual recovery.

### Solution Implemented
Added transaction-like semantics with rollback:
- Track completion state of each operation (created_tag, wrote_version, appended_changelog)
- On exception: delete created tag, restore previous version file, log warnings
- Raise RuntimeError with original exception as cause
- Added logging import to manager.py

### Acceptance Criteria
- [x] All-or-nothing semantics with rollback
- [x] Clear error messages on failure
- [x] All 56 version tests pass

---


---
id: "CR-025@b3c5d1"
title: "Off-by-one error in yaml_validator frontmatter parsing"
description: "Frontmatter content slicing may cut off content incorrectly"
created: 2024-12-27
section: "tools"
tags: [bug, parsing]
type: bug
priority: high
status: proposed
references:
  - src/dot_work/tools/yaml_validator.py
---

### Problem
In `yaml_validator.py:184`, `fm_content = "\n".join(lines[1 : end_idx - 1])` - the slicing appears off by one. For frontmatter `---\nkey: val\n---`, this would get lines 2 to `end_idx-2`, potentially cutting off content. This appears to be a bug.

### Affected Files
- `src/dot_work/tools/yaml_validator.py` (line 184)

### Importance
Incorrect parsing could lose frontmatter data silently.

### Proposed Solution
1. Verify the slice boundaries with test cases
2. Fix off-by-one if confirmed
3. Add tests for edge cases (empty frontmatter, single line, etc.)

### Acceptance Criteria
- [ ] Parsing verified correct
- [ ] Edge cases tested
- [ ] No data loss

---

---
id: "CR-026@c4d6e2"
title: "Empty init method says CanonicalPromptParser is stateless but uses class"
description: "Classes with empty __init__ should be functions or use @staticmethod"
created: 2024-12-27
section: "prompts"
tags: [architecture, simplification]
type: refactor
priority: high
status: proposed
references:
  - src/dot_work/prompts/canonical.py
---

### Problem
`CanonicalPromptParser.__init__` (lines 119-121) is an empty method (`pass`). Same for `CanonicalPromptValidator.__init__` (lines 201-203). The classes hold no state and could be implemented as pure functions or `@staticmethod`.

### Affected Files
- `src/dot_work/prompts/canonical.py`

### Importance
Unnecessary class instantiation adds overhead and complexity.

### Proposed Solution
1. Convert to module-level functions, or
2. Use `@staticmethod` for methods, or
3. Create module-level singletons to avoid repeated instantiation

### Acceptance Criteria
- [ ] Simplified API
- [ ] No unnecessary instantiation
- [ ] Existing functionality preserved

---

---
id: "CR-027@d5e7f3"
title: "Inline bash script in container/provision prevents independent versioning"
description: "175-line bash script embedded as string literal requires Python release to change"
created: 2024-12-27
section: "container/provision"
tags: [architecture, maintainability]
type: refactor
priority: high
status: proposed
references:
  - src/dot_work/container/provision/core.py
---

### Problem
The inline bash script in `core.py:535-726` (~175 lines) is a string literal. Any change requires a Python release. This makes iteration on the script difficult and prevents independent testing.

### Affected Files
- `src/dot_work/container/provision/core.py` (lines 535-726)

### Importance
Changes to container behavior require full release cycle. Script cannot be tested in isolation.

### Proposed Solution
1. Load script from a separate `.sh` file
2. Or use a Jinja template for customization
3. Consider moving more logic to Python for testability

### Acceptance Criteria
- [ ] Script can be modified independently
- [ ] Script is testable
- [ ] Existing functionality preserved

---

---
id: "CR-075@c0d6e4"
title: "Command Injection Risk via EDITOR Environment Variable"
description: "Subprocess calls execute user-supplied editor arguments without sanitization"
created: 2024-12-27
section: "db_issues"
tags: [security, command-injection, subprocess, editor]
type: security
priority: high
status: proposed
references:
  - src/dot_work/db_issues/cli.py
---

### Problem
In `cli.py:1272-1300, 1370-1376`, multiple CLI commands execute user-supplied `$EDITOR` via `subprocess.run()`:

```python
editor_name, editor_args = _validate_editor(os.environ.get("EDITOR"))

result = subprocess.run([editor_name, *editor_args, str(temp_path)])
```

The `_validate_editor()` function (lines 1243-1269) only checks against a whitelist but doesn't:

1. **Sanitize editor arguments** - user can supply `vim -c "exec system('rm -rf /')"` if editor config is compromised
2. **Prevent shell metacharacters** - if shell is ever invoked accidentally
3. **Validate temp file path** before passing to editor
4. **Use explicit `shell=False`** - relies on default but not explicit

**Specific risks:**
- Editor whitelist bypass through environment variable manipulation
- Malicious editor arguments if user config is compromised
- Shell metacharacters in editor paths/arguments

### Affected Files
- `src/dot_work/db_issues/cli.py` (lines 1243-1300, 1370-1376)

### Importance
**HIGH**: Command injection enables:
- Arbitrary code execution with user privileges
- File system manipulation via editor commands
- Potential privilege escalation
- Data destruction if malicious commands executed

While editor validation exists, argument sanitization is missing.

### Proposed Solution
1. Use `shlex.quote()` to sanitize all editor arguments
2. Set `shell=False` explicitly in all subprocess.run() calls
3. Validate no shell metacharacters in editor configuration
4. Consider using `subprocess.Popen()` with controlled args
5. Add unit tests with malicious editor arguments
6. Review all subprocess.run() calls across codebase for consistent sanitization

### Acceptance Criteria
- [ ] All editor arguments sanitized with `shlex.quote()`
- [ ] Explicit `shell=False` in all subprocess calls
- [ ] No shell metacharacters accepted in editor config
- [ ] Unit tests for injection attempts
- [ ] Security review of all subprocess usage

### Notes
This is related to CR-032 and should be addressed together. A subprocess wrapper utility could ensure consistent security defaults across the codebase.

---

---
id: "CR-076@d1e7f5"
title: "Missing Transaction Rollback in SearchService.rebuild_index()"
description: "FTS index rebuild commits without error handling causing data loss on failure"
created: 2024-12-27
section: "db_issues"
tags: [database, transaction-safety, rollback, fts]
type: bug
priority: high
status: proposed
references:
  - src/dot_work/db_issues/services/search_service.py
---

### Problem
In `search_service.py:89-111`, `rebuild_index()` commits changes without error handling or rollback:

```python
def rebuild_index(self) -> int:
    # Clear existing FTS data
    self.session.exec(text("DELETE FROM issues_fts;"))

    # Rebuild from issues table
    self.session.exec(text("""
    INSERT INTO issues_fts(rowid, id, title, description)
    SELECT rowid, id, title, COALESCE(description, '')
    FROM issues;
    """))

    self.session.commit()  # LINE 107 - No try/except, no rollback on error

    # Count indexed issues
    count_result = self.session.exec(text("SELECT COUNT(*) as cnt FROM issues_fts;"))
    return count_result.first().cnt if count_result else 0
```

**Failure scenarios:**
- If INSERT fails (constraint violation, disk full, etc.) after DELETE is committed
- If COUNT fails after INSERT succeeds
- If exception occurs between commit and return

**Result:**
- FTS index is cleared but not rebuilt
- All searches return zero results
- No transaction rollback to restore previous state
- Search functionality permanently broken until manual intervention

### Affected Files
- `src/dot_work/db_issues/services/search_service.py` (lines 89-111)

### Importance
**HIGH**: Missing transaction rollback causes:
- Complete loss of search functionality on partial failures
- Silent data corruption (FTS empty but no error message)
- Production incidents requiring manual database recovery
- No all-or-nothing semantics for critical operation

This is related to CR-053 (inconsistent transaction management) and should be addressed together.

### Proposed Solution
1. Wrap entire operation in try/except with explicit rollback on error
2. Use UnitOfWork context manager for consistent transaction handling
3. Log all failures before rollback with context
4. Verify index integrity after rebuild (count matches issues table)
5. Add unit tests for failure scenarios
6. Consider atomic FTS rebuild using temporary table and rename

### Acceptance Criteria
- [ ] Operation wrapped in try/except with rollback
- [ ] Consistent transaction pattern with UnitOfWork
- [ ] Failures logged before rollback
- [ ] Index integrity verified after successful rebuild
- [ ] Unit tests for INSERT failure, COUNT failure scenarios
- [ ] No silent data loss

### Notes
Current implementation risks leaving search in broken state. Consider using SQLite's SAVEPOINT for partial transaction support or atomic rebuild pattern (build in temp table, DELETE, rename).

---

---
id: "CR-077@e2f8a6"
title: "OpenAI API Key Leaked in Error Messages"
description: "API key may be exposed in logs, exceptions, and error responses"
created: 2024-12-27
section: "knowledge_graph"
tags: [security, credentials, logging, api-keys]
type: security
priority: high
status: proposed
references:
  - src/dot_work/knowledge_graph/embed/openai.py
---

### Problem
In `openai.py:50-52`, API key is stored and used without proper secret handling:

```python
self.api_key = config.api_key or os.environ.get("OPENAI_API_KEY")

# Error message
msg = "OpenAI API key required (set OPENAI_API_KEY or pass api_key)"
```

While this specific error message doesn't leak the key, there are risks throughout the module and calling code:

1. **Exception context** - If OpenAI client raises exceptions with config context, key may be included
2. **Debug logging** - If logger is configured to log exception info, key appears in logs
3. **Error reporting systems** - Stack traces sent to monitoring services include key
4. **String formatting** - f-strings or str() on config objects may expose key
5. **No constant-time comparison** - Timing attacks on key validation (less critical but still best practice)

**Missing protections:**
- Key masking/redaction in all error paths
- Secure logging of API-related errors
- Never include raw key in exception context or logs

### Affected Files
- `src/dot_work/knowledge_graph/embed/openai.py`

### Importance
**HIGH**: API key leakage enables:
- Unauthorized access to OpenAI account
- Billing fraud if key used for malicious API calls
- Key revocation and service disruption
- Security audit failures

Once leaked, keys must be rotated immediately. Detection of leakage is difficult.

### Proposed Solution
1. Implement key masking utility function (`sk-****...<last4>`)
2. Redact API key in all error messages and logging
3. Use constant-time string comparison for key validation
4. Implement safe repr() for config objects
5. Review all error handling paths for key exposure
6. Add integration tests that verify key never appears in logs/exceptions
7. Document key handling security requirements

### Acceptance Criteria
- [ ] Key masking function implemented
- [ ] All error messages redact API key
- [ ] Logs never contain raw API key
- [ ] Exception context redacts API key
- [ ] Tests verify key not in logs/exceptions
- [ ] Documentation updated with security requirements

### Notes
This is similar to CR-001 (plaintext git credentials) - both involve secrets handling. A unified secrets management approach across the codebase would prevent similar issues.

---

---
id: "CR-078@f3a9b7"
title: "Test Collection Failures Masking Real Issues"
description: "103 test collection errors prevent test suite execution, hiding bugs"
created: 2024-12-27
section: "testing"
tags: [testing, infrastructure, quality]
type: bug
priority: high
status: proposed
references:
  - incoming/kg/tests/unit/
  - tests/
---

### Problem
The test suite has 103 collection errors during `pytest --collect-only`:

```
!!!!!!!!!!!!!!!!!! Interrupted: 103 errors during collection !!!!!!!!!!!!!!!!!!
================== 1555 tests collected, 103 errors in 2.63s ===================
```

**Implications:**
1. Tests cannot even be executed (1555 collected but 103 errors)
2. Test infrastructure issues mask real bugs in code
3. False confidence in test coverage metrics
4. CI may pass or fail unpredictably depending on test execution order
5. Broken test references prevent catching regressions

**Root causes identified:**
- Tests from `incoming/kg/tests/unit/` are causing import/collection errors
- 75 test files exist but collection failures prevent execution
- References to modules/packages that no longer exist or moved

### Affected Files
- `incoming/kg/tests/unit/` (multiple files with errors)
- `tests/` (indirectly affected by infrastructure issues)

### Importance
**HIGH**: Broken test suite causes:
- Inability to verify code correctness
- Undetected bugs reaching production
- False sense of security from "1555 tests"
- CI/CD pipeline unreliability
- Developer time wasted investigating why tests fail

A test suite that cannot run provides zero value and hides real problems.

### Proposed Solution
1. Fix all 103 test collection errors in knowledge_graph tests
2. Remove or update broken test references (`incoming/kg`)
3. Fix import errors in test files
4. Add CI gate to fail fast on collection errors
5. Ensure all tests can be collected and executed before running full suite
6. Add pre-commit hook to validate test collection
7. Document test infrastructure requirements

### Acceptance Criteria
- [ ] All 103 collection errors resolved
- [ ] `pytest --collect-only` completes with 0 errors
- [ ] All tests can execute successfully
- [ ] CI gate fails on collection errors
- [ ] Pre-commit hook validates test collection
- [ ] Test infrastructure documented

### Notes
This is a critical quality issue. The existence of 103 collection errors suggests significant technical debt in the test infrastructure. Addressing this should be a priority before adding new features.

---
id: "PERF-003@h3i4j5"
title: "Missing Database Indexes on Edge Type Column"
description: "FTS edge queries perform full table scans due to missing index"
created: 2024-12-27
section: "knowledge_graph"
tags: [performance, database, index, query-optimization]
type: refactor
priority: high
status: proposed
references:
  - src/dot_work/knowledge_graph/db.py
---

### Problem
In `db.py:842-859`, `get_edges_by_type()` queries edges table without index on type column:

```python
def get_edges_by_type(self, edge_type: str) -> list[Edge]:
    # No index on 'type' column
    cur = conn.execute("""
        SELECT src_node_pk, dst_node_pk, type, weight, meta_json
        FROM edges WHERE type = ?
        """, (edge_type,))
```

**Performance issue:**
- `edges` table has index on `src_node_pk` and `dst_node_pk`
- **No index on `type` column** despite filtering by type
- Query performs full table scan on every `get_edges_by_type()` call
- Called frequently during graph traversal and search operations

**Impact:**
- Graph operations slow down as node count increases
- 10,000 edges without type index = full table scan (~10ms)
- 100,000 edges = noticeable latency (100ms+) in graph queries
- Scales poorly with knowledge base size

### Affected Files
- `src/dot_work/knowledge_graph/db.py` (lines 842-859)

### Importance
**HIGH**: Affects all knowledge graph operations and user experience:
- Full table scans for every edge type query
- Latency grows linearly with edge count
- Makes large knowledge graphs slow to search and navigate
- Simple database fix with massive performance impact

### Proposed Solution
Add composite index on `(type, src_node_pk, dst_node_pk)`:

```sql
CREATE INDEX IF NOT EXISTS idx_edges_type_src_dst
ON edges(type, src_node_pk, dst_node_pk);
```

Index creation in migration:
```python
def migrate_add_edge_type_index(self):
    conn = self.get_connection()
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_edges_type_src_dst
        ON edges(type, src_node_pk, dst_node_pk)
    """)
    conn.commit()
```

### Acceptance Criteria
- [ ] Composite index on (type, src_node_pk, dst_node_pk) created
- [ ] Migration script adds index to existing databases
- [ ] Performance test: 100k edges query < 10ms
- [ ] Index included in schema initialization

### Notes
This is a low-effort, high-impact optimization. Adding the index should provide 10-100x speedup for edge type queries. Consider adding similar indexes for other frequently filtered columns.

---
id: "PERF-004@i4j5k6"
title: "Inefficient Bulk Operations in IssueRepository.save()"
description: "Labels/assignees saved one-by-one causing M+1 database queries"
created: 2024-12-27
section: "db_issues"
tags: [performance, database, bulk-operations, n-plus-one]
type: refactor
priority: high
status: proposed
references:
  - src/dot_work/db_issues/adapters/sqlite.py
---

### Problem
In `sqlite.py:371-425`, `save()` performs individual DELETE/INSERT queries for labels/assignees:

```python
def save(self, issue: Issue) -> Issue:
    # Labels: Individual DELETE queries
    statement = select(IssueLabelModel).where(IssueLabelModel.issue_id == issue.id)
    existing_labels = self.session.exec(statement).all()
    for label_model in existing_labels:
        self.session.delete(label_model)  # N queries
    self.session.flush()
    
    # Labels: Individual INSERT queries
    for label_name in issue.labels:
        label_model = IssueLabelModel(issue_id=issue.id, label_name=label_name, ...)
        self.session.add(label_model)  # N queries
    self.session.flush()
    
    # Same pattern for assignees (N+1) and references (K+1)
```

**Performance issue:**
- Deleting/inserting labels/assignees one-by-one
- M+1 database round-trips for M labels
- Same pattern repeated for assignees (N+1) and references (K+1)
- Total queries per issue save = 1 (issue) + 2M (labels) + 2N (assignees) + 2K (references)

**Impact:**
- Issue creation/editing slows down with more labels/assignees
- Bulk issue operations (import/export) become prohibitively slow
- 10 labels + 3 assignees + 5 refs = ~47 database round-trips per issue
- 1000 issues with avg 5 labels = 5000+ extra queries

### Affected Files
- `src/dot_work/db_issues/adapters/sqlite.py` (lines 371-425)

### Importance
**HIGH**: Severely impacts bulk operations and performance:
- Issue operations become slow as metadata grows
- Makes large-scale issue management impractical
- Import/export operations take minutes instead of seconds
- Wastes database connection pool capacity

### Proposed Solution
Use bulk DELETE and bulk INSERT operations:

```python
def save(self, issue: Issue) -> Issue:
    # ... issue save ...

    # Bulk delete all labels for issue
    if existing_labels:
        self.session.exec(
            text("DELETE FROM issue_labels WHERE issue_id = :issue_id"),
            {"issue_id": issue.id}
        )
    
    # Bulk insert all labels
    if issue.labels:
        now = datetime.now(timezone.utc)
        label_values = [(issue.id, label, now) for label in issue.labels]
        self.session.exec(
            text("""
                INSERT INTO issue_labels (issue_id, label_name, created_at)
                VALUES :values
            """),
            {"values": label_values}
        )
    
    # Same pattern for assignees and references
```

### Acceptance Criteria
- [ ] Bulk DELETE for labels/assignees/references
- [ ] Bulk INSERT for labels/assignees/references
- [ ] Performance test: 10 labels < 5ms vs current 50ms
- [ ] Bulk operations tested with 100+ labels

### Notes
This is a classic bulk operations anti-pattern. The fix should provide 10-50x speedup for issues with multiple labels/assignees and dramatically improve bulk import/export performance.

---
id: "PERF-005@j5k6l7"
title: "Unbounded Embedding Loading in get_all_embeddings_for_model()"
description: "Loads ALL embeddings into memory without limit causing OOM crashes"
created: 2024-12-27
section: "knowledge_graph"
tags: [performance, memory, embeddings, oom, scaling]
type: refactor
priority: high
status: proposed
references:
  - src/dot_work/knowledge_graph/db.py
---

### Problem
In `db.py:1056-1075`, `get_all_embeddings_for_model()` loads all embeddings without limit:

```python
def get_all_embeddings_for_model(self, model: str) -> list[Embedding]:
    cur = conn.execute("""
        SELECT embedding_pk, full_id, model, dimensions, vector, created_at
        FROM embeddings WHERE model = ?
        """, (model,))
    
    # Load ALL embeddings into memory at once
    return [self._row_to_embedding(row) for row in cur.fetchall()]
```

**Performance issue:**
- Loads ALL embeddings for a model without limit
- Embeddings are large (1536 floats × 4 bytes = 6KB per vector)
- 10,000 embeddings = 60MB memory
- 100,000 embeddings = 600MB memory
- While streaming methods exist (lines 1107-1132), this method bypasses them

**Impact:**
- Large knowledge bases cause OOM crashes
- Semantic search operations fail on large datasets
- Server restarts during indexing operations
- Memory pressure affects other operations
- Prevents scaling beyond ~10k nodes

### Affected Files
- `src/dot_work/knowledge_graph/db.py` (lines 1056-1075)

### Importance
**HIGH**: Blocks scaling and causes crashes:
- Prevents users from creating large knowledge bases
- OOM crashes lose work and require restart
- Memory exhaustion affects system stability
- Makes semantic search unusable at scale

### Proposed Solution
Add safety limit and redirect to streaming method:

```python
def get_all_embeddings_for_model(self, model: str, limit: int = 10000) -> list[Embedding]:
    """Get embeddings for a model with safety limit.

    For large datasets, use stream_embeddings_for_model() instead to avoid OOM.
    """
    if limit == 0:
        logger.warning(
            f"get_all_embeddings_for_model() loading all embeddings for model {model} "
            "- may cause OOM for large datasets"
        )
    cur = conn.execute("""
        SELECT ... FROM embeddings WHERE model = ? LIMIT ?
        """, (model, limit))
    return [self._row_to_embedding(row) for row in cur.fetchall()]
```

Or redirect to streaming:
```python
def get_all_embeddings_for_model(self, model: str) -> list[Embedding]:
    logger.warning("get_all_embeddings_for_model() unbounded - use stream_embeddings_for_model()")
    return list(self.stream_embeddings_for_model(model, batch_size=1000))
```

### Acceptance Criteria
- [ ] Safety limit parameter added (default 10000)
- [ ] Warning logged when limit exceeded or bypassed
- [ ] Documentation updated to recommend streaming
- [ ] Performance test: 100k embeddings with limit succeeds

### Notes
The streaming method already exists. This fix prevents accidental OOM by default while still allowing power users to load all embeddings if needed with explicit parameter.

---
id: "PERF-006@k6l7m8"
title: "Unbounded JSONL Export/Import"
description: "Exports/imports load ALL issues into memory causing OOM on large datasets"
created: 2024-12-27
section: "db_issues"
tags: [performance, memory, jsonl, export-import, scaling]
type: refactor
priority: high
status: proposed
references:
  - src/dot_work/db_issues/services/jsonl_service.py
---

### Problem
In `jsonl_service.py:54-102`, `export()` loads ALL issues into memory first:

```python
def export(self, output_path: Path, ...):
    # Load ALL issues into memory first
    if status_filter:
        issues = self.uow.issues.list_by_status(status_filter, limit=1000000, offset=0)
    else:
        issues = self.uow.issues.list_all(limit=1000000, offset=0)
    
    # Filter in-memory
    if not include_completed:
        issues = [i for i in issues if i.status != IssueStatus.COMPLETED]
    
    # Write to file (still holding all issues in memory)
    with output_path.open("w", encoding="utf-8") as f:
        for issue in issues:
            f.write(jsonl_line + "\n")
```

**Performance issue:**
- Exports load ALL issues into memory first
- No streaming for large datasets
- `limit=1000000` loads up to 1M issues
- Issues can be large (description + labels + comments + assignees)
- Same issue in `import_()` method (line 134)

**Impact:**
- Export/import fails with OOM on large issue trackers
- 10,000 issues × 10KB each = 100MB+ in memory
- 100,000 issues = 1GB+ memory required
- Server crashes during backup/restore operations
- Blocks backup/restore for large projects

### Affected Files
- `src/dot_work/db_issues/services/jsonl_service.py` (lines 54-102, 134+)

### Importance
**HIGH**: Blocks backup/restore and large-scale operations:
- Cannot export large issue trackers
- Backup/restore fails with OOM
- Prevents moving large datasets between systems
- Makes import/export unusable for production datasets

### Proposed Solution
Stream issues directly to file:

```python
def export(self, output_path: Path, ...):
    with output_path.open("w", encoding="utf-8") as f:
        # Use generator to stream issues
        for issue in self._stream_issues(status_filter):
            if include_completed or issue.status != IssueStatus.COMPLETED:
                jsonl_line = self._issue_to_jsonl(issue)
                f.write(jsonl_line + "\n")

def _stream_issues(self, status_filter: IssueStatus | None) -> Iterator[Issue]:
    """Stream issues in batches to avoid loading all into memory."""
    offset = 0
    batch_size = 1000
    while True:
        if status_filter:
            issues = self.uow.issues.list_by_status(
                status_filter, limit=batch_size, offset=offset
            )
        else:
            issues = self.uow.issues.list_all(limit=batch_size, offset=offset)
        
        if not issues:
            break
        yield from issues
        offset += len(issues)
```

Same pattern for import:

```python
def import_(self, input_path: Path, ...):
    with input_path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            issue_data = json.loads(line)
            # Process and save one issue at a time
            issue = self._jsonl_to_issue(issue_data)
            self.uow.issues.save(issue)
            # Flush periodically
            if line_num % 100 == 0:
                self.uow.commit()
    self.uow.commit()
```

### Acceptance Criteria
- [ ] Export streams issues to file (batch_size 1000)
- [ ] Import processes issues one-by-one or in small batches
- [ ] Memory usage constant regardless of dataset size
- [ ] Performance test: 100k issues export with < 100MB memory
- [ ] Import/export preserve all data

### Notes
This fix enables export/import of unlimited datasets with constant memory usage. The streaming pattern is essential for large-scale data operations.

---