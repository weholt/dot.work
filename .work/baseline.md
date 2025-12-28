# Project Baseline

**Captured:** 2025-12-28
**Commit:** 64201d9
**Branch:** closing-migration

---

## Scope Summary

### Modules
- **Total Python source files:** 118 (in src/)
- **Total source lines of code:** 38,079
- **Total test files:** 99 (in tests/)
- **Total test lines of code:** 23,483

### Entry Points
- **CLI:** `uv run dot-work` (via `src/dot_work/cli.py`)
- **Module execution:** `python -m dot_work.python.build`
- **Module execution:** `python -m dot_work.python.scan`

### Public Interfaces (CLI Commands)
- `work init` - Initialize work tracking directory
- `work install` - Install prompt files for various AI environments
- `work validate json` - Validate JSON files
- `work validate yaml` - Validate YAML files with frontmatter
- `work review` commands - Code review workflow
- `db-issues` - Issue tracking CLI (create, edit, list, dependencies, stats, etc.)
- `python-build` - Python project build runner
- `python-scan` - Python repository scanner
- `git-analysis` - Git repository analysis tools
- `kg` - Knowledge graph management

### Dependencies
- **Python:** 3.13.1
- **Package manager:** uv 0.5.4
- **Code quality:** ruff 0.14.9, mypy 1.19.1
- **Testing:** pytest 9.0.2
- **Key runtime deps:** SQLAlchemy, SQLModel, Pydantic, rich, typer, click, libcst, radon

---

## Observable Behaviors

### BEH-001: Configuration loading
- Config loads from YAML frontmatter in markdown files
- Environment variable override via `DOT_WORK_DB_ISSUES_PATH`
- Documented: Yes (in code)

### BEH-002: Path security validation
- Path traversal validation prevents `../` attacks
- Absolute paths rejected unless within CWD
- Resolves relative paths to absolute for security
- Documented: Yes (tests document security behavior)

### BEH-003: Issue tracking operations
- CRUD operations for issues (create, edit, delete, list)
- Dependency management (block, unblock, list dependencies)
- Bulk operations (bulk-create from JSON/YAML)
- Status transitions (new, in_progress, blocked, resolved, cancelled, stale)
- Documented: Yes (CLI help, docstrings)

### BEH-004: Knowledge graph operations
- Node and edge creation/management
- Semantic search with cosine similarity
- Full-text search (FTS5)
- Collection and topic management
- Documented: Yes (docstrings)

### BEH-005: Python project scanning
- AST-based feature and model extraction
- Complexity analysis (radon)
- Import graph generation
- Documented: Yes (code comments)

### BEH-006: Code review workflow
- Git-based review tracking
- Review export and clearing
- Documented: Yes (CLI help)

**Undocumented behaviors:** None significant

---

## Test Evidence

### Test Counts
- **Total tests:** 1467 collected
- **Execution time:** ~25-30 seconds
- **Coverage:** ≥70% (threshold met)

### Test Status
- **Unit tests:** All passing (1467 tests)
- **Integration tests:** Not run in this baseline
- **Test memory usage:** ~128.5 MB peak (within 4GB limit)

### Tested Behaviors
- BEH-001: Config loading → test_config.py
- BEH-002: Path security → test_config.py (path traversal tests)
- BEH-003: Issue operations → test_issue_service.py, test_cli.py
- BEH-004: Knowledge graph → test_db.py, test_search_*.py
- BEH-005: Python scanning → test_scanner.py
- BEH-006: Code review → test_review_*.py

### Untested Behaviors
- Edge cases in concurrent access to SQLite database
- Large file handling (>10GB files)
- Windows-specific path handling (CI only runs on Linux)

---

## Known Gaps

### GAP-001: Windows compatibility
- Windows path handling not thoroughly tested
- CI only runs on Linux
- **Location:** Throughout codebase
- **Impact:** Unknown

### GAP-002: Concurrent database access
- SQLite write concurrency not explicitly tested
- Potential for WAL mode issues under high load
- **Location:** src/dot_work/db_issues/adapters/sqlite.py
- **Impact:** Low (single-user tool)

### GAP-003: Memory enforcement on non-systemd systems
- cgroup v2 memory limiting requires systemd
- Fallback to ulimit may be less effective
- **Location:** scripts/pytest-with-cgroup.sh
- **Impact:** Medium (CI environments)

### GAP-004: Test coverage gaps
- Some error handling paths untested
- Edge cases in semantic search
- **Impact:** Low

**TODOs in code:** Not comprehensively inventoried

---

## Failure Modes

### FAIL-001: Missing config file
- **Handling:** FileNotFoundError raised
- **Documented:** Yes
- **User experience:** Clear error message

### FAIL-002: Invalid YAML in frontmatter
- **Handling:** YAMLError caught, validation error raised
- **Documented:** Yes
- **User experience:** Detailed validation error with line numbers

### FAIL-003: Path traversal attempts
- **Handling:** ValueError raised with security message
- **Documented:** Yes
- **User experience:** Clear security warning

### FAIL-004: Database lock (SQLite)
- **Handling:** DatabaseError propagated
- **Documented:** No
- **User experience:** Generic database error

### FAIL-005: Out of memory during tests
- **Handling:** Killed by cgroup v2 MemoryMax
- **Documented:** Yes (script comments)
- **User experience:** Process terminated, no output

**Summary:** 3 explicit, 1 silent (FAIL-004), 1 logged (FAIL-005)

---

## Structure

### Files
- **Total source files:** 118 Python files
- **Total source lines:** 38,079
- **Total test files:** 99 Python files
- **Total test lines:** 23,483

### Module Organization
```
src/dot_work/
├── __init__.py
├── cli.py                    # Main CLI entry point
├── db_issues/                # Issue tracking system
│   ├── adapters/             # SQLite adapter
│   ├── services/             # Business logic
│   └── cli.py                # db-issues CLI
├── knowledge_graph/          # Knowledge graph
│   ├── db.py                 # Graph database
│   ├── embed.py              # Embedding service
│   └── search_*.py           # Search implementations
├── overview/                 # Code overview
│   ├── pipeline.py           # Scanning pipeline
│   └── code_parser.py        # AST parsing
├── python/                   # Python tools
│   ├── build/                # Build runner
│   └── scan/                 # Repository scanner
├── git/                      # Git analysis
├── review/                   # Code review
└── zip/                      # Zip operations
```

### Abstraction Depth
- **Max depth:** 3-4 layers (CLI → Service → Repository → Model)
- **Cyclic dependencies:** None detected

### Code Quality Signals
- **Linting:** 0 errors (ruff)
- **Type checking:** 0 errors (mypy)
- **Security:** 0 warnings (ruff security check)

---

## Documentation Status

### Current Documentation
- **README:** Up to date
- **CLAUDE.md:** Current (developer instructions)
- **CLI help:** Current (typer auto-generated)

### Missing/Stale Documentation
- **API documentation:** Not generated
- **Changelog:** Not maintained
- **Architecture docs:** Partial (in code comments)

### Type Hint Coverage
- **Estimated:** 85-90%
- **Missing in:** Some legacy code, test fixtures

---

## Unknowns

### UNK-001: Runtime behavior under load
- **Reason:** No load testing environment
- **Impact:** Unknown
- **Cannot verify:** Memory usage under sustained high load

### UNK-002: Windows compatibility
- **Reason:** CI only runs on Linux
- **Impact:** Unknown
- **Cannot verify:** Windows-specific path handling

### UNK-003: Large file handling
- **Reason:** No test files >10GB available
- **Impact:** Unknown (but unlikely use case)
- **Cannot verify:** Memory usage with >10GB files

### UNK-004: Semantic search quality
- **Reason:** Subjective measure
- **Impact:** Unknown
- **Cannot verify:** Search result relevance without human evaluation

---

## Baseline Invariants

**Statements that must not regress:**

1. **Type checking:** 0 errors in src/ (mypy must pass)
2. **Linting:** 0 errors in src/ (ruff must pass)
3. **Tests:** All 1467 unit tests must pass
4. **Security:** 0 security warnings in src/
5. **Memory:** Test execution must remain under 4GB limit

---

## Notes

### Recent Changes (since previous baseline)

**Previous Baseline:** 2024-12-26, Commit 95b0765

| Metric | Previous | Current | Change |
|--------|----------|---------|--------|
| Commit | 95b0765 | 64201d9 | +14 commits |
| Tests | 1434 | 1467 | +33 tests |
| Type Errors | 0 | 0 | CLEAN |
| Lint Errors | 0 | 0 | CLEAN |
| Security Warnings | 0 | 0 | CLEAN |

### Key Changes Between Baselines

**Migration Cleanup Complete:**
1. **CODE-Q-001 resolution (commits 5eb9212, 5115f37, 64201d9):**
   - Fixed 63 type checking errors
   - Fixed 30 linting errors
   - Fixed 4 test failures
   - Removed non-existent cli_utils imports
   - Fixed variable naming issues (assignee/assignees, issue_type/type)
   - Fixed repository method calls (list_all, get_dependencies, etc.)

2. **Code Quality Status:**
   - All source code passes type checking and linting
   - Ready for feature development
   - All critical migration issues resolved

### Next Steps

1. **All critical and code quality issues COMPLETE**
2. **Source code is clean** - Ready for feature development
3. **Resume PERF-002 investigation** - File scanner performance optimization (from shortlist)
