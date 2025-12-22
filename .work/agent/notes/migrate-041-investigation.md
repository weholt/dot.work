# MIGRATE-041 Investigation Notes

**Investigation Started:** 2025-12-22T23:25:00Z  
**Source:** incoming/crampus/version-management/version_management/  
**Target:** src/dot_work/version/  

## Issue Overview

Create version module structure in dot-work by migrating the version-management project.

**Purpose:** Date-based versioning (YYYY.MM.NNNNN) with changelog generation from conventional commits

## Source Analysis

### Files to Migrate (956 total lines)
```
version_manager.py      (305 lines) - Core orchestration + versioning logic
changelog_generator.py  (230 lines) - Markdown changelog from commits
cli.py                  (205 lines) - Typer CLI interface
commit_parser.py        (124 lines) - Conventional commit parsing
project_parser.py       (81 lines)  - pyproject.toml reading
__init__.py             (17 lines)  - Package exports
test_project_parser.py  (101 lines) - Basic tests (5% coverage only)
```

### Key Classes & Functions

**VersionManager (main orchestrator)**
- `init(version_str, project_path)` - Initialize version.json
- `freeze(publish=False)` - Create new version + changelog
- `get_version()` - Current version
- `get_version_history()` - All versions
- `get_commits()` - Since last tag

**ChangelogGenerator**
- `generate_markdown()` - Creates CHANGELOG.md
- Uses Jinja2 templates
- Groups commits by type (feat, fix, etc.)

**CommitParser**
- `parse()` - Parses conventional commits
- Extracts type, scope, subject, body
- Detects breaking changes

**ProjectParser**
- `get_metadata()` - Reads pyproject.toml
- Extracts project name, version, authors

## Dependencies Required

### Core (Add to pyproject.toml)
- `GitPython >= 3.1.0` - Git operations
- `Jinja2 >= 3.1.0` - Changelog templates
- Already present: Typer, Rich

### To Remove
- pydantic (unused - only dataclass)
- python-dotenv (unused - manual config)

### Conditional
- tomli >= 2.0.0 (Python < 3.11 only for TOML parsing)

## Target Structure

```
src/dot_work/version/
├── __init__.py           # Package exports
├── cli.py                # Typer CLI commands (adapted)
├── manager.py            # VersionManager (renamed from version_manager.py)
├── commit_parser.py      # CommitParser (copied as-is, minimal changes)
├── changelog.py          # ChangelogGenerator (renamed from changelog_generator.py)
├── project_parser.py     # ProjectParser (copied as-is, minimal changes)
└── config.py             # NEW - VersionConfig for dot-work patterns
```

## Implementation Strategy

### Phase 1: Create Directory & Copy Files
1. Create src/dot_work/version/
2. Copy files with minimal changes:
   - version_manager.py → manager.py
   - changelog_generator.py → changelog.py
   - commit_parser.py (copy as-is)
   - project_parser.py (copy as-is)
   - cli.py (for review, minimal adapt needed)
   - __init__.py (update exports)

### Phase 2: Update Imports (MIGRATE-042)
- Update all `from version_management.*` to `from dot_work.version.*`
- Create config.py with VersionConfig dataclass
- Set storage path to `.work/version/version.json`
- Use `DOT_WORK_VERSION_*` env var pattern

### Phase 3: Register CLI (MIGRATE-043)
- Create version_app in cli.py
- Register in main src/dot_work/cli.py
- Implement: init, freeze, show, history, commits

### Phase 4: Add Dependencies (MIGRATE-044)
- Add GitPython, Jinja2 to core
- Optional: httpx for LLM (if keeping LLM feature)

### Phase 5: Tests (MIGRATE-045)
- Expand from 5 tests to target 80%+ coverage
- Mock git operations (no real repos)
- Test all CLI commands

### Phase 6: Full Build (MIGRATE-046)
- Verify 8/8 checks pass
- All 762+ tests pass
- Coverage ≥ 80% for version module

## Known Issues to Address

1. **Low Test Coverage** (5%)
   - Only test_project_parser.py exists (101 lines)
   - Need comprehensive test suite (target: 40-50 tests)

2. **Unused Imports**
   - pydantic imported but not used (uses dataclass instead)
   - python-dotenv imported but not used (manual config)
   - Remove these from dependencies

3. **Config Not Used**
   - config.json mentioned but not loaded
   - Implement config loading in dot-work patterns or document why unused

4. **LLM Feature Incomplete**
   - llm parameter exists but not functional
   - Implement or remove for MVP

5. **No Git Validation**
   - Should validate git repo exists before operations
   - Add validation in manager.py

6. **Import Pattern**
   - Some imports inside functions (circular import workaround)
   - Should refactor if possible, but low priority

## Acceptance Criteria (MIGRATE-041)

- [x] Directory `src/dot_work/version/` exists
- [x] Core modules present (6 files)
- [x] No syntax errors
- [x] Imports work from dot_work.version
- [ ] (Will verify during implementation)

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| GitPython conflicts with other modules | Low | Check imports, version constraints |
| Jinja2 template issues | Low | Test with sample changelog |
| Config path issues on Windows | Medium | Use pathlib.Path throughout |
| Git operations fail without repo | Medium | Add git repo validation |
| Import refactoring introduces bugs | Medium | Comprehensive test suite needed |

## Next Steps (After MIGRATE-041)

1. MIGRATE-042: Update imports and config
2. MIGRATE-043: Register CLI subcommand
3. MIGRATE-044: Add dependencies
4. MIGRATE-045: Add tests (most effort: 8-12 hours)
5. MIGRATE-046: Full build verification

## Estimated Timeline

- MIGRATE-041: 1-2 hours (file copying + basic structure)
- MIGRATE-042: 1-1.5 hours (import updates)
- MIGRATE-043: 1-1.5 hours (CLI integration)
- MIGRATE-044: 0.5-1 hour (dependencies)
- MIGRATE-045: 8-12 hours (comprehensive tests)
- MIGRATE-046: 1-2 hours (verification)

**Total: 13-20 hours (1-2 focused sessions)**

## Investigation Complete ✅

Ready to proceed with Phase 1 implementation.
