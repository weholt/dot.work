# Project Baseline

**Captured:** 2025-12-31
**Commit:** d2a83d3
**Branch:** closing-migration

---

## Scope Summary

### Modules
- **Total Python source files:** 121 (in src/)
- **Total source lines of code:** ~39,000
- **Total test files:** 87 (in tests/)
- **Total test lines of code:** ~26,500
- **Total test functions:** 1,679

### Entry Points
- **CLI:** `uv run dot-work` (via `src/dot_work/cli.py`)
- **Module execution:** `python -m dot_work.python.build`
- **Module execution:** `python -m dot_work.python.scan`
- **Review Server:** FastAPI server via `src/dot_work/review/server.py`

### Public Interfaces (CLI Commands)
- `work init` - Initialize work tracking directory
- `work install` - Install prompt files for various AI environments
- `work validate json` - Validate JSON files
- `work validate yaml` - Validate YAML files with frontmatter
- `work review` - Code review workflow
- `db-issues` - Issue tracking CLI (create, edit, list, dependencies, stats)
- `python-build` - Python project build runner
- `kg` - Knowledge graph CLI

### Dependencies
- **Total dependencies:** 40+ (see pyproject.toml)
- **Key dependencies:** typer, rich, fastapi, uvicorn, sqlmodel, pyyaml

## Observable Behaviors

### Core Features
- **BEH-001:** Issue tracking via file-based system in `.work/agent/issues/`
- **BEH-002:** Git commit analysis and tag generation
- **BEH-003:** Knowledge graph with FTS5 search
- **BEH-004:** Code review server with authentication (Bearer token)
- **BEH-005:** Path traversal protection on file access
- **BEH-006:** Rate limiting on comment submission (60 req/min)
- **BEH-007:** Python project scaffolding and build

## Test Evidence

### Test Counts (as of baseline)
- **Total tests:** 1,679+
- **Unit tests:** ~1,500
- **Integration tests:** ~180
- **Recent test runs:** All passing (45/45 on modified modules)

### Coverage
- **Coverage target:** ≥75%
- **Recent tests passing:**
  - test_sqlite.py: 16 passed
  - test_tag_generator.py: 11 passed
  - test_server.py: 18 passed

### Test Coverage by File
- `src/dot_work/review/server.py`: Full security test coverage (auth, path traversal, rate limiting)
- `src/dot_work/db_issues/adapters/sqlite.py`: SQL injection safety tests
- `src/dot_work/git/services/tag_generator.py`: Tag generation tests

## Known Gaps

### Security (Recently Addressed)
- ~~SEC-001~~: ~~Subprocess shell=True in provision.py~~ (addressed with explicit shell=False)
- ~~SEC-002~~: ~~Review server lacks authentication~~ (completed: Bearer token auth added)
- ~~SEC-003~~: ~~SQL injection audit needed~~ (completed: all text() calls verified safe)

### Known Issues (Remaining)
- 10 proposed issues remain (8 medium, 2 low)
- Ruff linting warnings in test files (B009, B904) - expected patterns
- S603 subprocess warnings - expected (SEC-001 addressed with shell=False)

### TODOs in Code
- Various modules have inline TODOs for future enhancements
- See issue tracking system for prioritized work

## Failure Modes

### Known Failure Behaviors
- **FAIL-001:** HTTP 401 raised when auth token missing/invalid (review server)
- **FAIL-002:** HTTP 403 raised for path traversal attempts (review server)
- **FAIL-003:** HTTP 429 raised when rate limit exceeded (review server)
- **FAIL-004:** ValueError raised for invalid FTS5 search queries (knowledge graph)

### Error Handling Summary
- **Explicit errors:** HTTPException (401, 403, 429), ValueError
- **Logged errors:** File read failures, git operation failures
- **Silent failures:** None (all errors are explicit or logged)

## Structure

### Code Organization
- **Total files:** 200+ (src + tests)
- **Max abstraction depth:** 4-5 layers
- **Cyclic dependencies:** None detected

### Linting/Type Checking Status
- **Ruff (src/):** All checks passed ✓
- **Ruff (tests/):** 131 warnings (expected B009, B904 patterns)
- **Mypy:** Configured, warn_unused_ignores enabled
- **Type hint coverage:** High (most public APIs typed)

## Documentation Status

### Current Documentation
- **README.md:** Present and maintained
- **CLAUDE.md:** Project-specific AI instructions
- **GitHub prompts:** Workflow documentation in `.github/prompts/`
- **Module docstrings:** Present in most modules

### Recently Added Documentation
- **SQL Injection Safety** section in `sqlite.py`
- Security test documentation in test files

## Unknowns

### UNK-001: Full test suite execution time
- **Reason:** Full test suite takes significant time and may hit memory limits
- **Impact:** Partial test runs used for validation
- **Mitigation:** Modified file tests verified, critical paths tested

### UNK-002: Production deployment configuration
- **Reason:** REVIEW_AUTH_TOKEN environment variable optional for development
- **Impact:** Production deployment requires token configuration
- **Documentation:** Documented in SEC-002 completion

### UNK-003: Windows compatibility
- **Reason:** CI may only run on Linux
- **Impact:** Windows-specific path handling not verified
- **Note:** Path.resolve() should handle cross-platform paths

## Baseline Invariants

Statements that must not regress:
1. All modified module tests pass (45/45 verified)
2. Source code (src/) passes ruff checks with no errors
3. No security vulnerabilities in modified code (SEC-002, SEC-003 addressed)
4. Authentication, path validation, and rate limiting functional (SEC-002)
5. SQL injection prevention verified (SEC-003)

## Recent Changes (Since Last Baseline)

### Security Enhancements
- **SEC-002:** Added Bearer token authentication to review server
- **SEC-002:** Added path traversal protection
- **SEC-002:** Added rate limiting (60 req/min per IP)
- **SEC-003:** Audited all SQL text() usage - verified safe
- **SEC-003:** Added SQL injection safety tests

### Bug Fixes
- **CR-065:** Fixed scroll position preservation on comment submission
- Fixed test failures after CR-101 dead code removal
- Added ruff JavaScript exclusion

### Test Additions
- 8 new security tests for review server
- 4 SQL injection safety tests for SQLite adapter
