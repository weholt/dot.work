# Medium Priority Issues (P2)

Enhancements, technical debt.

---


---
id: "FEAT-006@e6c3f9"
title: "Add Cline and Cody environments"
description: "Popular AI coding tools not currently supported"
created: 2024-12-20
section: "environments"
tags: [environments, cline, cody]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/environments.py
  - src/dot_work/installer.py
---

### Problem
Cline (VS Code extension) and Cody (Sourcegraph) are popular AI coding assistants not currently supported by dot-work.

### Affected Files
- `src/dot_work/environments.py` (add environment configs)
- `src/dot_work/installer.py` (add installer functions)

### Importance
Users of these tools cannot use dot-work to install prompts, limiting adoption.

### Proposed Solution
1. Research Cline and Cody prompt/rules file conventions:
   - Cline: likely `.cline/` or similar
   - Cody: likely `.cody/` or `.sourcegraph/`
2. Add Environment entries with appropriate detection markers
3. Add `install_for_cline()` and `install_for_cody()` functions
4. Add to INSTALLERS dispatch table
5. Add tests for new environments

### Acceptance Criteria
- [ ] `dot-work list` shows cline and cody environments
- [ ] `dot-work install --env cline` creates correct structure
- [ ] `dot-work install --env cody` creates correct structure
- [ ] `dot-work detect` recognizes cline/cody markers
- [ ] Tests cover new installer functions

### Notes
May need to verify exact conventions by checking official documentation or popular repos using these tools.

---

---
id: "REFACTOR-001@f7d4a1"
title: "Extract common installer logic to reduce duplication"
description: "10 install_for_* functions share ~80% identical code"
created: 2024-12-20
section: "installer"
tags: [refactor, dry, maintainability]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/installer.py
---

### Problem
The 10 `install_for_*` functions in installer.py contain ~200 lines of repetitive code. Each function:
1. Creates destination directory
2. Gets environment config
3. Iterates prompts, renders, writes
4. Prints status messages

Adding a new environment requires copying ~20 lines of near-duplicate code.

### Affected Files
- `src/dot_work/installer.py`

### Importance
Violates DRY principle. Bug fixes must be applied to 10 places. Adding new environments is error-prone. The `force` flag implementation will need to be duplicated 10 times without this refactor.

### Proposed Solution
1. Create generic `install_prompts_generic()` function
2. Define environment-specific behavior via configuration:
   - Destination path pattern
   - Whether to create auxiliary files (.cursorrules, etc.)
   - Auxiliary file content template
   - Console messaging
3. Keep simple dispatch: `INSTALLERS[env_key] = lambda: install_prompts_generic(config)`
4. Special cases (claude, aider combining into single file) handled via config flag

### Acceptance Criteria
- [ ] Single generic installer function handles all environments
- [ ] No more than 5 lines of environment-specific code per environment
- [ ] All existing tests pass
- [ ] Adding new environment requires only config, not code
- [ ] `force` flag implemented in one place

### Notes
Do this AFTER implementing the force flag to avoid conflicts. Consider config-as-data pattern using dataclass or dict.

---

---
id: "FEAT-007@a8e5b2"
title: "Add --dry-run flag to install command"
description: "Allow previewing changes before writing files"
created: 2024-12-20
section: "cli"
tags: [cli, install, ux]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/cli.py
  - src/dot_work/installer.py
---

### Problem
Users cannot preview what files will be created or modified before running `dot-work install`. This makes it difficult to understand the impact of installation, especially when files might be overwritten.

### Affected Files
- `src/dot_work/cli.py` (add --dry-run option)
- `src/dot_work/installer.py` (add dry_run parameter)

### Importance
Improves user confidence and reduces surprises. Useful for CI/CD integration where destructive changes should be previewed.

### Proposed Solution
1. Add `--dry-run` / `-n` flag to install command
2. Pass through to installer functions
3. When dry_run=True:
   - Print what would be created/modified
   - Show file paths and whether new/overwrite
   - Do not write any files
4. Output format: `[CREATE] .github/prompts/do-work.prompt.md` or `[OVERWRITE] .github/prompts/do-work.prompt.md`

### Acceptance Criteria
- [ ] `dot-work install --dry-run` shows planned changes without writing
- [ ] Output distinguishes between new files and overwrites
- [ ] Exit code 0 even in dry-run mode
- [ ] Tests verify no files written in dry-run mode

### Notes
Implement after force flag and ideally after refactor to avoid duplication.

---

---
id: "FEAT-008@f7d4a2"
title: "Add batch overwrite option when files exist during install"
description: "Provide 'overwrite all' choice instead of only file-by-file prompting"
created: 2024-12-20
section: "cli"
tags: [cli, install, ux, prompting]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/cli.py
  - src/dot_work/installer.py
---

### Problem
When running `dot-work install` without `--force` and files already exist, the user is prompted for each file individually. For projects with many prompt files (8+), this becomes tedious.

Current behavior:
```
  ⚠ File already exists: do-work.prompt.md
    Overwrite? [y/N]: y
  ⚠ File already exists: setup-issue-tracker.prompt.md
    Overwrite? [y/N]: y
  ... (repeated for each file)
```

### Affected Files
- `src/dot_work/installer.py` (modify `should_write_file()` and install functions)
- `src/dot_work/cli.py` (potentially add `--update-all` flag)
- `tests/unit/test_installer.py` (add tests for batch behavior)

### Importance
User experience improvement. Power users reinstalling/updating prompts shouldn't need to answer the same question 8+ times. This is especially painful when updating to a new version of dot-work.

### Proposed Solution
1. When first existing file is encountered, offer expanded choices:
   ```
   ⚠ Found existing prompt files. How should I proceed?
     [a] Overwrite ALL existing files
     [s] Skip ALL existing files
     [p] Prompt for each file individually
     [c] Cancel installation
   Choice [a/s/p/c]:
   ```
2. Store user's choice for the session
3. Apply consistently to remaining files
4. Alternative: Add `--update-all` / `--skip-existing` CLI flags

### Acceptance Criteria
- [ ] First conflict offers batch choice (all/skip/prompt/cancel)
- [ ] Choice "a" overwrites all remaining without further prompts
- [ ] Choice "s" skips all existing files without further prompts
- [ ] Choice "p" maintains current file-by-file behavior
- [ ] Choice "c" aborts installation cleanly
- [ ] `--force` still works as before (silent overwrite all)
- [ ] Tests verify each batch mode behavior

### Notes
Consider interaction with `--force` flag:
- `--force` = silent overwrite (no prompts at all)
- No flag + batch "a" = overwrite after single confirmation
- No flag + batch "p" = current behavior

This builds on FEAT-003 (--force implementation). Could be combined with FEAT-007 (--dry-run) for a complete UX.

---

## MIGRATE-034@d8e9f0

---
id: "MIGRATE-034@d8e9f0"
title: "Create db-issues module structure in dot-work"
description: "Create src/dot_work/db_issues/ module with core CRUD from issue-tracker"
created: 2024-12-21
section: "db_issues"
tags: [migration, issue-tracker, db-issues, module-structure]
type: enhancement
priority: medium
status: proposed
references:
  - incoming/glorious/src/glorious_agents/skills/issues/src/issue_tracker/
  - src/dot_work/db_issues/
---

### Problem
The issue-tracker project provides SQLite-backed issue management. To integrate as `dot-work db-issues`, we need to migrate the core CRUD functionality without the daemon/MCP/RPC features.

### Source Analysis
From `incoming/glorious/src/glorious_agents/skills/issues/src/issue_tracker/`:

**Include (Core CRUD):**
- `domain/entities/` - Issue, Comment, Dependency, Epic, Label
- `domain/value_objects.py` - Value objects
- `domain/ports/` - Repository interfaces
- `services/issue_service.py` - Core business logic
- `services/search_service.py` - Search functionality
- `adapters/db/` - SQLite/SQLModel implementation
- `config/settings.py` - Configuration
- `cli/` - CLI commands (simplified)

**Exclude (Daemon/MCP/RPC):**
- `daemon/` - Background daemon with IPC/RPC
- `adapters/mcp/` - MCP server for Claude
- `factories/` - Complex DI for daemon
- CLI commands: daemon-*, rpc-*, mcp-*

### Target Structure
```
src/dot_work/db_issues/
├── __init__.py           # Package exports
├── cli.py                # Typer CLI commands (simplified)
├── config.py             # Configuration
├── domain/
│   ├── __init__.py
│   ├── entities.py       # Issue, Comment, Dependency, Epic, Label
│   └── ports.py          # Repository interfaces
├── services/
│   ├── __init__.py
│   ├── issue_service.py  # Core CRUD operations
│   └── search_service.py # Search functionality
└── adapters/
    ├── __init__.py
    └── sqlite.py         # SQLite implementation
```

### Proposed Solution
1. Create `src/dot_work/db_issues/` directory
2. Create subdirectories: domain/, services/, adapters/
3. Copy and consolidate domain entities into single `entities.py`
4. Copy issue_service.py and search_service.py
5. Simplify adapter to single sqlite.py
6. Create simplified cli.py without daemon commands
7. Add config.py for database path configuration

### Acceptance Criteria
- [ ] Directory `src/dot_work/db_issues/` created
- [ ] Core entities in `domain/entities.py`
- [ ] Services in `services/`
- [ ] SQLite adapter in `adapters/sqlite.py`
- [ ] No daemon/MCP/RPC files included
- [ ] No syntax errors in module files

### Notes
This is a significant simplification from the original ~50+ file structure.
Focus on CRUD operations: create, list, show, update, close, reopen, delete.

**Important**: Preserve the hash-based ID system from the original:
- Issue IDs like `bd-a1b2` (prefix + 4-char hash)
- Child/hierarchical IDs like `bd-a1b2.1`, `bd-a1b2.2`
- IdentifierService for ID generation

---

## MIGRATE-035@e9f0a1

---
id: "MIGRATE-035@e9f0a1"
title: "Update db-issues imports to use dot-work patterns"
description: "Refactor imports from issue_tracker.* to dot_work.db_issues.*"
created: 2024-12-21
section: "db_issues"
tags: [migration, db-issues, imports, refactor]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/
---

### Problem
After copying/creating files, all imports reference `issue_tracker.*` which doesn't exist.

### Import Changes Required

| Old Import | New Import |
|------------|------------|
| `from issue_tracker.domain.entities.issue import Issue` | `from dot_work.db_issues.domain.entities import Issue` |
| `from issue_tracker.services.issue_service import IssueService` | `from dot_work.db_issues.services.issue_service import IssueService` |
| `from issue_tracker.adapters.db.unit_of_work import UnitOfWork` | `from dot_work.db_issues.adapters.sqlite import UnitOfWork` |
| `from issue_tracker.config.settings import Settings` | `from dot_work.db_issues.config import DbIssuesConfig` |

### Simplification Opportunities
- Consolidate multiple entity files into single `entities.py`
- Remove complex DI factory patterns
- Simplify to direct instantiation
- Remove daemon/MCP-related imports entirely

### Proposed Solution
1. Update all internal imports to `dot_work.db_issues.*`
2. Remove references to excluded modules (daemon, mcp, factories)
3. Simplify dependency injection to direct construction
4. Verify: `uv run python -c "from dot_work.db_issues import IssueService"`

### Acceptance Criteria
- [ ] All `issue_tracker.*` imports updated to `dot_work.db_issues.*`
- [ ] No references to daemon/mcp/factories
- [ ] Import statement works: `from dot_work.db_issues import IssueService`
- [ ] Type checking passes on db_issues module

### Notes
Depends on MIGRATE-034 (files must exist first).

---

## MIGRATE-036@f0a1b2

---
id: "MIGRATE-036@f0a1b2"
title: "Register db-issues as subcommand in dot-work CLI"
description: "Add db-issues commands as 'dot-work db-issues <cmd>' CLI structure"
created: 2024-12-21
section: "cli"
tags: [migration, db-issues, cli, integration]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/cli.py
  - src/dot_work/db_issues/cli.py
---

### Problem
The db-issues module needs CLI integration as `dot-work db-issues <command>`.

### CLI Design (Core CRUD Only)
```bash
# Initialize database
dot-work db-issues init

# Create issue
dot-work db-issues create "Fix bug in parser"
dot-work db-issues create "Add feature" --priority high --type feature

# List issues
dot-work db-issues list
dot-work db-issues list --status open
dot-work db-issues list --priority high

# Show issue details
dot-work db-issues show <id>

# Update issue
dot-work db-issues update <id> --title "New title"
dot-work db-issues update <id> --priority critical

# Status changes
dot-work db-issues close <id>
dot-work db-issues reopen <id>

# Delete
dot-work db-issues delete <id>

# Search
dot-work db-issues search "parser bug"

# Dependencies (subgroup)
dot-work db-issues deps add <from_id> <to_id> --type blocks
dot-work db-issues deps list <id>
dot-work db-issues deps remove <from_id> <to_id>

# Labels (subgroup)
dot-work db-issues labels add <id> "bug"
dot-work db-issues labels remove <id> "bug"
dot-work db-issues labels list

# Comments (subgroup)
dot-work db-issues comments add <id> "This is a comment"
dot-work db-issues comments list <id>
```

### CLI Structure
```python
db_issues_app = typer.Typer(help="SQLite-backed issue tracking.")

@db_issues_app.command("init")
def init() -> None:
    """Initialize issue database."""

@db_issues_app.command("create")
def create(title: str, priority: str = "medium", issue_type: str = "task") -> None:
    """Create a new issue."""

@db_issues_app.command("list")
def list_issues(status: str | None = None, priority: str | None = None) -> None:
    """List issues with optional filters."""

# ... etc for show, update, close, reopen, delete, search

# Subgroups
deps_app = typer.Typer(help="Manage issue dependencies.")
labels_app = typer.Typer(help="Manage issue labels.")
comments_app = typer.Typer(help="Manage issue comments.")

db_issues_app.add_typer(deps_app, name="deps")
db_issues_app.add_typer(labels_app, name="labels")
db_issues_app.add_typer(comments_app, name="comments")
```

### Commands NOT Included
- daemon-* commands (no daemon)
- rpc-* commands (no RPC)
- mcp-* commands (no MCP server)
- sync, export, import (future enhancement)

### Proposed Solution
1. Create `db_issues_app = typer.Typer()` in cli.py
2. Implement core CRUD commands
3. Add deps, labels, comments subgroups
4. Register: `app.add_typer(db_issues_app, name="db-issues")`

### Acceptance Criteria
- [ ] `dot-work db-issues --help` shows commands
- [ ] CRUD commands work: create, list, show, update, close, reopen, delete
- [ ] Dependencies subgroup works
- [ ] Labels subgroup works
- [ ] Comments subgroup works
- [ ] Search command works

### Notes
Depends on MIGRATE-035 (imports must work first).

---

## MIGRATE-037@a1b2c3

---
id: "MIGRATE-037@a1b2c3"
title: "Add db-issues dependencies to pyproject.toml"
description: "Add sqlmodel and gitpython as dependencies for db-issues"
created: 2024-12-21
section: "dependencies"
tags: [migration, db-issues, dependencies, pyproject]
type: enhancement
priority: medium
status: proposed
references:
  - pyproject.toml
---

### Problem
The db-issues module requires external dependencies for SQLite ORM.

### Dependencies Required (Simplified)

Original issue-tracker had heavy deps for daemon/MCP. Simplified list:
```toml
dependencies = [
    # Existing...
    "sqlmodel>=0.0.16",    # SQLite ORM (SQLAlchemy + Pydantic)
    "gitpython>=3.1.0",    # Git integration for JSONL storage (optional)
]
```

### Dependencies NOT Needed (Excluded)
- `fastapi` - Only for MCP server
- `uvicorn` - Only for MCP server
- `aiohttp` - Only for daemon RPC
- `psutil` - Only for daemon management
- `redis` - Only for agentmail
- `pywin32` - Only for Windows daemon

### Proposed Solution
1. Add `sqlmodel>=0.0.16` to core dependencies
2. Consider `gitpython` as optional for git-backed storage
3. Run `uv sync` to install
4. Verify: `uv run python -c "from sqlmodel import SQLModel"`

### Acceptance Criteria
- [ ] `sqlmodel` in core dependencies
- [ ] `gitpython` in optional group or core (decide)
- [ ] `uv sync` succeeds
- [ ] No daemon-related dependencies added
- [ ] db_issues module imports work

### Notes
SQLModel brings SQLAlchemy + Pydantic as transitive deps.
Consider making gitpython optional if JSONL sync not needed initially.

Depends on MIGRATE-034 (module must exist).

---

## MIGRATE-038@b2c3d4

---
id: "MIGRATE-038@b2c3d4"
title: "Configure db-issues storage in .work/db-issues/"
description: "Update db-issues to store database in .work/db-issues/ directory"
created: 2024-12-21
section: "db_issues"
tags: [migration, db-issues, config, storage]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/config.py
  - src/dot_work/db_issues/adapters/sqlite.py
---

### Problem
The db-issues module needs configuration for database storage location.

### Storage Design
```
.work/db-issues/
├── issues.db       # SQLite database
└── issues.jsonl    # Optional JSONL export for git
```

### Environment Variable Support
```python
# Default: .work/db-issues/
# Override: DOT_WORK_DB_ISSUES_PATH=/custom/path
```

### Config Dataclass
```python
@dataclass
class DbIssuesConfig:
    base_path: Path = field(default_factory=lambda: Path(".work/db-issues"))
    db_file: str = "issues.db"

    @classmethod
    def from_env(cls) -> DbIssuesConfig:
        base = os.getenv("DOT_WORK_DB_ISSUES_PATH")
        return cls(base_path=Path(base) if base else Path(".work/db-issues"))

    @property
    def db_path(self) -> Path:
        return self.base_path / self.db_file

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.db_path}"
```

### Proposed Solution
1. Create `src/dot_work/db_issues/config.py` with DbIssuesConfig
2. Update sqlite adapter to use config.db_url
3. Ensure .work/db-issues/ created on init
4. Add .work/db-issues/ to .gitignore template

### Acceptance Criteria
- [ ] Database at `.work/db-issues/issues.db`
- [ ] `DOT_WORK_DB_ISSUES_PATH` env var override works
- [ ] Directory created on `dot-work db-issues init`
- [ ] `.gitignore` updated to ignore `.work/db-issues/`

### Notes
Depends on MIGRATE-035 (imports must work).

---

## MIGRATE-039@c3d4e5

---
id: "MIGRATE-039@c3d4e5"
title: "Add tests for db-issues module"
description: "Create unit tests for db-issues functionality"
created: 2024-12-21
section: "tests"
tags: [migration, db-issues, tests]
type: test
priority: medium
status: proposed
references:
  - tests/unit/db_issues/
  - src/dot_work/db_issues/
---

### Problem
The db-issues module needs tests to ensure correct CRUD behavior.

### Test Structure
```
tests/unit/db_issues/
├── __init__.py
├── conftest.py          # Fixtures (in-memory SQLite)
├── test_entities.py     # Domain entity tests
├── test_issue_service.py # Service layer tests
├── test_sqlite.py       # Adapter tests
├── test_config.py       # Config tests
└── test_cli.py          # CLI command tests
```

### Key Test Cases

**test_entities.py:**
- `test_issue_creation` - Issue entity created
- `test_issue_status_transitions` - Status changes valid
- `test_comment_attached_to_issue` - Comment linking
- `test_dependency_types` - All dependency types work

**test_issue_service.py:**
- `test_create_issue_returns_issue` - CRUD create
- `test_list_issues_returns_all` - CRUD list
- `test_update_issue_modifies_fields` - CRUD update
- `test_close_issue_sets_status` - Status change
- `test_search_finds_matching` - Search works
- `test_add_dependency_links_issues` - Dependencies

**test_sqlite.py:**
- `test_init_creates_tables` - Database initialization
- `test_repository_persists_issue` - Persistence
- `test_in_memory_database` - Test mode

**test_cli.py:**
- `test_create_command` - CLI create
- `test_list_command` - CLI list
- `test_show_command` - CLI show

### Fixtures
```python
@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite for testing."""
    config = DbIssuesConfig(db_url="sqlite:///:memory:")
    # Setup and return session
```

### Proposed Solution
1. Create `tests/unit/db_issues/` directory
2. Add conftest.py with in-memory database fixture
3. Write tests for entities, services, adapters
4. Run: `uv run pytest tests/unit/db_issues/ -v`

### Acceptance Criteria
- [ ] Tests in `tests/unit/db_issues/`
- [ ] Coverage ≥ 80% for db_issues module
- [ ] All tests pass
- [ ] Uses in-memory SQLite for fast tests

### Notes
Depends on MIGRATE-035 (module must be functional).

---

## MIGRATE-040@d4e5f6

---
id: "MIGRATE-040@d4e5f6"
title: "Verify db-issues migration with full build"
description: "Run complete build pipeline and verify all db-issues functionality"
created: 2024-12-21
section: "db_issues"
tags: [migration, db-issues, verification, qa]
type: test
priority: medium
status: proposed
references:
  - scripts/build.py
---

### Problem
After completing all migration steps, verify the db-issues migration works correctly.

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
# Initialize database
dot-work db-issues init

# Create issues (returns hash-based ID like bd-a1b2)
dot-work db-issues create "First issue"
dot-work db-issues create "Second issue" --priority high --type bug

# List and show (using hash IDs)
dot-work db-issues list
dot-work db-issues show bd-a1b2

# Update and status
dot-work db-issues update bd-a1b2 --title "Updated title"
dot-work db-issues close bd-a1b2
dot-work db-issues reopen bd-a1b2

# Dependencies
dot-work db-issues deps add bd-a1b2 bd-c3d4 --type blocks
dot-work db-issues deps list bd-a1b2

# Labels
dot-work db-issues labels add bd-a1b2 "bug"
dot-work db-issues labels list

# Comments
dot-work db-issues comments add bd-a1b2 "Test comment"
dot-work db-issues comments list bd-a1b2

# Search
dot-work db-issues search "first"

# Delete
dot-work db-issues delete bd-a1b2

# Cleanup
rm -rf .work/db-issues/
```

**Database Verification:**
- [ ] Database created at `.work/db-issues/issues.db`
- [ ] Tables created correctly
- [ ] Data persists between commands
- [ ] Hash-based IDs generated correctly (e.g., `bd-a1b2`)
- [ ] Child IDs work (e.g., `bd-a1b2.1`)

### Acceptance Criteria
- [ ] `uv run python scripts/build.py` passes
- [ ] All db-issues commands work correctly
- [ ] Database stored in `.work/db-issues/`
- [ ] CRUD operations persist data
- [ ] Hash-based ID system works correctly
- [ ] No regressions in existing dot-work functionality

### Notes
Final verification step. Only mark migration complete when all checks pass.

Depends on: MIGRATE-034 through MIGRATE-039.
