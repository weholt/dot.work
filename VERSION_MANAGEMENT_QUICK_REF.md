# Version Management - Quick Reference

## What It Does
Automated date-based versioning (YYYY.MM.NNNNN format) with:
- Git tag creation
- Changelog generation from conventional commits
- Project metadata extraction from pyproject.toml
- Rich CLI interface with tables and colors

## File Inventory

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `version_manager.py` | 305 | Core orchestration | Production |
| `commit_parser.py` | 124 | Parse conventional commits | Production |
| `changelog_generator.py` | 230 | Generate markdown changelogs | Production |
| `project_parser.py` | 81 | Extract pyproject.toml metadata | Production |
| `cli.py` | 205 | Typer CLI interface | Production |
| `__init__.py` | 17 | Package exports | Production |
| `test_project_parser.py` | 101 | Unit tests (5 tests) | Production |

**Total:** ~1,063 lines of code, 101 lines of tests

## Dependencies

### Core (Required)
- **GitPython >= 3.1.0** - Git operations (tags, commits)
- **Jinja2 >= 3.1.0** - Changelog template rendering
- **Typer >= 0.9.0** - CLI framework (✓ already in dot-work)
- **Rich >= 13.0.0** - Console output (✓ already in dot-work)

### Conditional
- **tomli >= 2.0.0** - TOML parsing for Python < 3.11 (stdlib in 3.11+)

### Remove Before Migration
- ~~pydantic~~ - Listed but never used
- ~~python-dotenv~~ - Listed but never used

## Key Classes

### VersionInfo (dataclass)
```python
@dataclass
class VersionInfo:
    version: str                          # e.g., "2025.10.00042"
    build_date: str                       # ISO format datetime
    git_commit: str                       # Full commit hash
    git_tag: str                          # Tag name
    previous_version: str | None = None
    changelog_generated: bool = False
```

### VersionManager (main class)
Primary API - instantiate with project root path:
```python
manager = VersionManager(project_root=Path.cwd())
manager.init_version()                    # Initialize tracking
manager.freeze_version(use_llm=False)     # Create new version
manager.show_version()                    # Display current
manager.get_version_history(limit=10)     # Show history
```

### ConventionalCommitParser
Parses git commits matching `type(scope): subject` pattern:
- Types: feat, fix, docs, chore, test, refactor, perf, ci, build, style
- Breaking changes: BREAKING CHANGE or BREAKING-CHANGE or trailing !
- Fallback for non-conventional commits

### ChangelogGenerator
Renders markdown changelog with Jinja2 template:
- Groups commits by type
- Extracts highlights (keyword-based: breaking, security, performance, major, important)
- Generates summary (feat/fix counts or LLM)
- Counts contributor stats
- Supports custom templates

## CLI Commands

```bash
dot-work version init                    # Initialize version.json
dot-work version freeze                  # Create new version + changelog
dot-work version show                    # Display current version
dot-work version history [--limit N]     # Show last N versions
dot-work version commits [--since TAG]   # Show commits since tag
dot-work version config --show           # Display configuration
```

## Files Created/Modified

```
version.json              (created in project root)
CHANGELOG.md              (created/updated in project root)
.version-management.yaml  (optional config, loaded but unused)
```

## Critical Issues (6)

1. **Pydantic unused** - Remove from dependencies
2. **LLM incomplete** - `--llm` flag does nothing (TODO in code)
3. **Config ignored** - .version-management.yaml loaded but not used
4. **No git validation** - Crashes if project_root isn't git repo
5. **Circular imports** - Imports inside methods, not module-level
6. **Low test coverage** - Only 5 tests total, need ~50+ more

## Migration Path

### Before
```
incoming/crampus/version-management/
└── version_management/
    ├── __init__.py
    ├── version_manager.py
    ├── commit_parser.py
    ├── changelog_generator.py
    ├── project_parser.py
    └── cli.py
```

### After
```
src/dot_work/version/
├── __init__.py (updated imports)
├── version_manager.py (updated imports)
├── commit_parser.py
├── changelog_generator.py
├── project_parser.py
└── cli.py (integrated into dot-work CLI)

tests/unit/version/
├── __init__.py
├── test_project_parser.py (updated imports)
├── test_version_manager.py (NEW)
├── test_commit_parser.py (NEW)
├── test_changelog_generator.py (NEW)
└── test_cli.py (NEW)
```

## Import Changes

**Before:**
```python
from version_management.version_manager import VersionManager
```

**After:**
```python
from dot_work.version.version_manager import VersionManager
```

## Integration with dot-work CLI

In `src/dot_work/cli.py`:
```python
from dot_work.version.cli import app as version_app

# Register as subcommand group
app.add_typer(version_app, name="version")
```

## Effort Estimate

- File structure setup: 1 hour
- Import updates: 1 hour
- Dependency management: 0.5 hour
- CLI integration: 1.5 hours
- Test creation: 8-10 hours
- Code quality fixes: 2-3 hours
- Documentation: 2 hours
- Testing/QA: 2-3 hours

**Total: 20-25 hours**

## Configuration (Optional)

Create `.version-management.yaml` in project root:
```yaml
format: "YYYY.MM.build-number"
tag_prefix: "version-"
changelog:
  file: "CHANGELOG.md"
  include_authors: true
  group_by_type: true
```

**Note:** Config is currently loaded but not used. Implement config usage during migration.

## Version Format

- `YYYY` = 4-digit year
- `MM` = 2-digit month (01-12)
- `NNNNN` = 5-digit build number (00001-99999)

Examples:
- `2025.10.00001` = First build in October 2025
- `2025.10.00042` = 42nd build in October 2025
- `2025.11.00001` = Resets to 1 in November 2025

## Git Requirements

- Project must be a git repository
- Conventional commit messages recommended (fallback supported)
- Git user.name and user.email must be configured for tag creation

## Documentation

- Main README: `incoming/crampus/version-management/README.md` (238 lines)
- Vision/Design: `incoming/crampus/version-management/ideas.md`
- This project was designed to implement IDEA-019 in the codebase

## Key Strengths

✓ Well-structured with clear separation of concerns
✓ Type hints on all functions
✓ Comprehensive docstrings (Google format)
✓ Rich CLI with colored output
✓ Good conventional commit support
✓ Graceful error handling

## Key Weaknesses

✗ Incomplete test coverage (5 tests for ~1000 LOC)
✗ Unused imports and dependencies
✗ Incomplete LLM feature
✗ Config loaded but unused
✗ No git repository validation
✗ Circular import pattern

## Next Steps

1. Read `VERSION_MANAGEMENT_ANALYSIS.md` for comprehensive analysis
2. Read `MIGRATION_VISUAL_GUIDE.txt` for detailed migration plan
3. Review issues #1-6 above and plan fixes
4. Create test plan (target: 40+ tests, >80% coverage)
5. Follow migration checklist in visual guide
