# Shortlist (User-Directed Priority)

This file represents **explicit user intent**. Agent may only modify when explicitly instructed.

---

## VERSION MODULE MIGRATION (Option 2)

Complete migration of version-management utility as dot-work version module.

---
id: "MIGRATE-041@e5f6a7"
title: "Create version module structure in dot-work"
description: "Create src/dot_work/version/ module from version-management project"
created: 2024-12-21
section: "version"
tags: [migration, version-management, versioning, changelog]
type: enhancement
priority: medium
status: proposed
references:
   - incoming/crampus/version-management/
   - src/dot_work/version/
---

### Problem
The version-management project in `incoming/crampus/version-management/` provides date-based versioning (`YYYY.MM.build`) with automatic changelog generation from conventional commits. To integrate as `dot-work version`, we need to migrate the module.

### Source Files to Migrate
From `incoming/crampus/version-management/version_management/`:
- `cli.py` - Typer CLI (init, freeze, show, history, commits, config)
- `version_manager.py` - Core version management logic
- `commit_parser.py` - Conventional commit parsing
- `changelog_generator.py` - Changelog generation with Jinja2
- `project_parser.py` - pyproject.toml parsing

### Target Structure
```
src/dot_work/version/
├── __init__.py           # Package exports
├── cli.py                # Typer CLI commands
├── manager.py            # Core version management
├── commit_parser.py      # Conventional commit parsing
├── changelog.py          # Changelog generation
└── config.py             # Configuration
```

### Proposed Solution
1. Create `src/dot_work/version/` directory
2. Copy and adapt version_manager.py → manager.py
3. Copy commit_parser.py (minimal changes)
4. Copy changelog_generator.py → changelog.py
5. Create config.py for dot-work patterns
6. Adapt cli.py for dot-work registration

### Acceptance Criteria
- [x] Directory `src/dot_work/version/` created
- [x] All core modules present
- [x] No syntax errors in module files
- [x] `__init__.py` exports main classes

### Notes
The original uses GitPython, Jinja2, rich, pydantic. These will be added as dependencies.

---

---
id: "MIGRATE-042@f6a7b8"
title: "Update version module imports and config"
description: "Refactor imports from version_management.* to dot_work.version.*"
created: 2024-12-21
section: "version"
tags: [migration, version, imports, refactor]
type: refactor
priority: medium
status: proposed
references:
   - src/dot_work/version/
---

### Problem
After copying files, imports reference `version_management.*` which doesn't exist.

### Import Changes Required

| Old Import | New Import |
|------------|------------|
| `from version_management.version_manager import VersionManager` | `from dot_work.version.manager import VersionManager` |
| `from version_management.commit_parser import CommitParser` | `from dot_work.version.commit_parser import CommitParser` |
| `from version_management.changelog_generator import ChangelogGenerator` | `from dot_work.version.changelog import ChangelogGenerator` |

### Config Updates
- Store version.json in `.work/version/version.json`
- Config file: `.work/version/config.yaml` or env vars
- Env var prefix: `DOT_WORK_VERSION_*`

### Proposed Solution
1. Update all internal imports
2. Create config.py with VersionConfig dataclass
3. Update storage paths to use `.work/version/`
4. Verify: `uv run python -c "from dot_work.version import VersionManager"`

### Acceptance Criteria
- [ ] All imports updated to `dot_work.version.*`
- [ ] Config uses `DOT_WORK_VERSION_*` env vars
- [ ] Storage in `.work/version/`
- [ ] Module imports work correctly

### Notes
Depends on MIGRATE-041 (files must exist first).

---

---
id: "MIGRATE-043@a7b8c9"
title: "Register version as subcommand in dot-work CLI"
description: "Add version commands as 'dot-work version <cmd>' CLI structure"
created: 2024-12-21
section: "cli"
tags: [migration, version, cli, integration]
type: enhancement
priority: medium
status: proposed
references:
   - src/dot_work/cli.py
   - src/dot_work/version/cli.py
---

### Problem
The version module needs CLI integration as `dot-work version <command>`.

### CLI Design
```bash
# Initialize versioning
dot-work version init
dot-work version init --version 2025.12.001

# Freeze new version with changelog
dot-work version freeze
dot-work version freeze --llm       # LLM-enhanced summary
dot-work version freeze --dry-run   # Preview
dot-work version freeze --push      # Push tags

# Show version info
dot-work version show

# Show version history
dot-work version history
dot-work version history --limit 20

# Show commits since last version
dot-work version commits
dot-work version commits --since v1.0.0

# Show/edit config
dot-work version config --show
```

### CLI Structure
```python
version_app = typer.Typer(help="Date-based version management with changelog generation.")

@version_app.command("init")
def version_init(version: str | None = None) -> None:
    """Initialize version management."""

@version_app.command("freeze")
def version_freeze(llm: bool = False, dry_run: bool = False, push: bool = False) -> None:
    """Freeze new version with changelog."""

@version_app.command("show")
def version_show() -> None:
    """Show current version."""

@version_app.command("history")
def version_history(limit: int = 10) -> None:
    """Show version history."""

@version_app.command("commits")
def version_commits(since: str | None = None) -> None:
    """Show commits since last version."""
```

### Proposed Solution
1. Create `version_app = typer.Typer()` in version/cli.py
2. Implement commands: init, freeze, show, history, commits, config
3. Register: `app.add_typer(version_app, name="version")`

### Acceptance Criteria
- [ ] `dot-work version --help` shows commands
- [ ] `dot-work version init` creates version.json
- [ ] `dot-work version freeze` creates version + changelog
- [ ] `dot-work version show` displays current version
- [ ] `dot-work version history` shows git tag history

### Notes
Depends on MIGRATE-042 (imports must work first).

---

---
id: "MIGRATE-044@b8c9d0"
title: "Add version dependencies to pyproject.toml"
description: "Add GitPython, Jinja2, pydantic for version management"
created: 2024-12-21
section: "dependencies"
tags: [migration, version, dependencies, pyproject]
type: enhancement
priority: medium
status: proposed
references:
   - pyproject.toml
---

### Problem
The version module requires external dependencies.

### Dependencies from version-management
```toml
dependencies = [
    "GitPython>=3.1.0",   # Git operations
    "Jinja2>=3.1.0",      # Changelog templates
    "pydantic>=2.0.0",    # Data models
    "tomli>=2.0.0; python_version < '3.11'",  # pyproject.toml parsing
]

[project.optional-dependencies]
version-llm = ["httpx>=0.24.0"]  # For Ollama integration
```

### Proposed Solution
1. Add core dependencies to pyproject.toml
2. Add `version-llm` optional group for LLM features
3. Run `uv sync` to install
4. Verify imports work

### Acceptance Criteria
- [ ] `GitPython`, `Jinja2`, `pydantic` in core deps
- [ ] `httpx` in optional `version-llm` group
- [ ] `uv sync` succeeds
- [ ] Version module imports work

### Notes
Some deps may already exist (rich, typer). GitPython may conflict with kg module - verify.

Depends on MIGRATE-041 (module must exist).

---

---
id: "MIGRATE-045@c9d0e1"
title: "Add tests for version module"
description: "Create unit tests for version management functionality"
created: 2024-12-21
section: "tests"
tags: [migration, version, tests]
type: test
priority: medium
status: proposed
references:
   - tests/unit/version/
   - src/dot_work/version/
---

### Problem
The version module needs tests to ensure correct behavior.

### Test Structure
```
tests/unit/version/
├── __init__.py
├── conftest.py          # Fixtures (mock git repo)
├── test_manager.py      # VersionManager tests
├── test_commit_parser.py # Commit parsing tests
├── test_changelog.py    # Changelog generation tests
├── test_config.py       # Config tests
└── test_cli.py          # CLI command tests
```

### Key Test Cases

**test_manager.py:**
- `test_init_creates_version_file`
- `test_freeze_increments_build_number`
- `test_freeze_resets_on_new_month`
- `test_read_version_returns_current`

**test_commit_parser.py:**
- `test_parse_conventional_commit`
- `test_parse_with_scope`
- `test_parse_breaking_change`
- `test_parse_non_conventional`

**test_changelog.py:**
- `test_generate_changelog_groups_by_type`
- `test_changelog_includes_authors`

### Acceptance Criteria
- [ ] Tests in `tests/unit/version/`
- [ ] Coverage ≥ 80% for version module
- [ ] All tests pass
- [ ] Mock git operations (no real repos)

### Notes
Depends on MIGRATE-042 (module must be functional).

---

---
id: "MIGRATE-046@d0e1f2"
title: "Verify version migration with full build"
description: "Run complete build pipeline and verify version functionality"
created: 2024-12-21
section: "version"
tags: [migration, version, verification, qa]
type: test
priority: medium
status: proposed
references:
   - scripts/build.py
---

### Problem
After completing all migration steps, verify the version migration works correctly.

### Verification Checklist

**Build Pipeline:**
```bash
uv run python scripts/build.py
```
- [ ] Formatting passes
- [ ] Linting passes
- [ ] Type checking passes
- [ ] All tests pass
- [ ] Coverage ≥75%

**CLI Verification:**
```bash
# Initialize versioning
dot-work version init
# Should create .work/version/version.json

# Show current version
dot-work version show
# Should display current version

# Show version history
dot-work version history
# Should show git tags
```

**Functionality Test:**
- [ ] Version format is YYYY.MM.build
- [ ] Freeze increments build number
- [ ] Freeze resets on new month
- [ ] Changelog generated correctly
- [ ] Conventional commits parsed

### Acceptance Criteria
- [ ] `uv run python scripts/build.py` passes
- [ ] `dot-work version init` works
- [ ] `dot-work version show` displays version
- [ ] No regressions in existing dot-work functionality

### Notes
Final verification step. Only mark migration complete when all checks pass.

Depends on: MIGRATE-041 through MIGRATE-045.

---
