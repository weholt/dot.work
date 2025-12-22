# Project Baseline

**Captured:** 2025-12-23T06:00:00Z
**Commit:** 81e235aa1ca3e72bbb3b0d37972aa13a96e8450b
**Branch:** migrating-using-opencode

---

## Build Status
- Status: Partial (4/8 steps passing)
- Execution time: ~12s

## Pre-existing Issues (Before Git History Migration)

### Linting (Ruff)
- Status: ✅ PASSING
- Total errors: 0

### Type Checking (Mypy)
- Status: ⚠️ 4 errors (pre-existing)
- Files affected:
  - `src/dot_work/zip/zipper.py`: unused type: ignore, gitignore_parser untyped
  - `src/dot_work/container/provision/core.py`: frontmatter untyped
  - `src/dot_work/container/provision/validation.py`: frontmatter untyped

### Security Checks
- Status: ⚠️ 1 warning (pre-existing)
- S603: subprocess call in container/provision/core.py (untrusted input check)

### Unit Tests
- Status: ⚠️ 38 failing, 896 passing, 1 error (pre-existing version module issues)
- All failing tests are in: `tests/unit/version/`

**Failing test files:**
- `test_cli.py`: 7 failures (CLI output assertions, exit codes)
- `test_commit_parser.py`: 6 failures (unexpected keyword argument 'hash')
- `test_config.py`: 4 failures (VersionConfig missing 'load_config' attribute)
- `test_manager.py`: 21 failures (git repository errors in tests)

**Note:** These are pre-existing issues from the version module migration (MIGRATE-043 through MIGRATE-057). They should be addressed separately from the git history migration.

### Files with Pre-existing Issues
| File | Issues |
|------|--------|
| src/dot_work/zip/zipper.py | mypy: unused type: ignore, untyped import |
| src/dot_work/container/provision/core.py | mypy: untyped import, security: S603 |
| src/dot_work/container/provision/validation.py | mypy: untyped import |
| tests/unit/version/* | 38 failing tests |

### Clean Files (No Issues)
All other files are clean (formatting, linting, type-wise).

---

## Scope Summary

### Modules & Structure
- **Total Python files:** 76
- **Main modules:**
  - `dot_work` - Core CLI and scaffolding functionality
  - `dot_work.container` - Container build/provision
  - `dot_work.git` - **TO BE CREATED** (this migration)
  - `dot_work.knowledge_graph` - Knowledge graph management
  - `dot_work.overview` - Code overview generation (newly added)
  - `dot_work.prompts` - AI prompt templates and workflows
  - `dot_work.python` - Python tooling utilities
  - `dot_work.review` - Code review server and tools
  - `dot_work.tools` - JSON/YAML validation utilities
  - `dot_work.version` - Version management system
  - `dot_work.zip` - Module packaging and distribution

### Entry Points
- **Primary CLI:** `dot-work` - Main project scaffolding and issue tracking
- **Secondary:** `kg` - Knowledge graph management

---

## Invariant for Git History Migration

During MIGRATE-064 through MIGRATE-069:
- Do NOT introduce new issues in clean files
- Do NOT increase mypy errors beyond 4
- Do NOT break the 896 passing tests
- Create new issues only in `src/dot_work/git/` (new module)
