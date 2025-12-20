# Migration Plan: agent-review → dot-work review

Integration of incoming/review project as a `review` subcommand in dot-work.

---

---
id: "MIGRATE-001@a1b2c3"
title: "Create dot_work/review subpackage structure"
description: "Set up the review/ subpackage directory and __init__.py"
created: 2024-12-21
section: "src/dot_work/review"
tags: [migration, structure, review]
type: enhancement
priority: high
status: proposed
references:
  - incoming/review/src/agent_review/
  - src/dot_work/
---

### Problem
The agent-review project needs to be integrated as a subpackage under `src/dot_work/review/`. This is the foundational step for all other migration tasks.

### Affected Files
- `src/dot_work/review/__init__.py` (new)
- `src/dot_work/review/git.py` (from incoming)
- `src/dot_work/review/models.py` (from incoming)
- `src/dot_work/review/storage.py` (from incoming)
- `src/dot_work/review/exporter.py` (from incoming)
- `src/dot_work/review/server.py` (from incoming)
- `src/dot_work/review/config.py` (from incoming)

### Importance
Foundation for all other migration tasks. Without this structure, other issues cannot proceed.

### Proposed Solution
1. Create `src/dot_work/review/` directory
2. Copy core Python modules from `incoming/review/src/agent_review/`:
   - `git.py` (~300 lines) - Git operations
   - `models.py` (~50 lines) - Pydantic data models
   - `storage.py` (~100 lines) - Comment persistence
   - `exporter.py` (~60 lines) - Markdown export
   - `server.py` (~150 lines) - FastAPI web server
   - `config.py` (~30 lines) - Configuration
3. Create `__init__.py` with appropriate exports
4. Do NOT update imports yet (separate issue)

### Acceptance Criteria
- [ ] `src/dot_work/review/` directory exists with all modules
- [ ] All source files copied verbatim (imports fixed in MIGRATE-002)
- [ ] `__init__.py` created with basic structure
- [ ] No import errors in copied files (isolated)

### Notes
This is a copy operation only. Import path updates are handled in MIGRATE-002. Keep original files intact for reference.

---

---
id: "MIGRATE-002@b2c3d4"
title: "Update all import paths in review subpackage"
description: "Change agent_review imports to dot_work.review"
created: 2024-12-21
section: "src/dot_work/review"
tags: [migration, imports, review]
type: enhancement
priority: high
status: proposed
depends_on: ["MIGRATE-001@a1b2c3"]
references:
  - src/dot_work/review/git.py
  - src/dot_work/review/models.py
  - src/dot_work/review/storage.py
  - src/dot_work/review/exporter.py
  - src/dot_work/review/server.py
  - src/dot_work/review/config.py
---

### Problem
All copied files use `from agent_review.X import Y` which will fail. These need to be updated to `from dot_work.review.X import Y`.

### Affected Files
All files in `src/dot_work/review/`:
- `server.py` - imports git, models, storage, config
- `exporter.py` - imports storage, models
- `storage.py` - imports models, config
- `git.py` - imports models (minimal)

### Importance
Critical for the package to be importable. Without this, all review functionality fails.

### Proposed Solution
1. In each file, replace:
   ```python
   # Before
   from agent_review.models import ReviewComment
   from agent_review import git
   
   # After
   from dot_work.review.models import ReviewComment
   from dot_work.review import git
   ```
2. Verify imports work: `python -c "from dot_work.review import server"`
3. Run mypy on the review subpackage

### Acceptance Criteria
- [ ] All imports changed from `agent_review` to `dot_work.review`
- [ ] `python -c "from dot_work.review import server"` succeeds
- [ ] `uv run mypy src/dot_work/review/` passes
- [ ] No circular import issues

### Notes
Use grep to find all imports: `grep -r "from agent_review" src/dot_work/review/`

---

---
id: "MIGRATE-003@c3d4e5"
title: "Copy static assets and templates for review UI"
description: "Move templates/ and static/ directories to review subpackage"
created: 2024-12-21
section: "src/dot_work/review"
tags: [migration, assets, templates, review]
type: enhancement
priority: high
status: proposed
depends_on: ["MIGRATE-001@a1b2c3"]
references:
  - incoming/review/src/agent_review/templates/
  - incoming/review/src/agent_review/static/
---

### Problem
The review web UI requires HTML templates and static assets (CSS, JS). These must be copied and registered as package data.

### Affected Files
- `src/dot_work/review/templates/index.html` (new, ~600 lines)
- `src/dot_work/review/static/app.css` (new, ~200 lines)
- `src/dot_work/review/static/app.js` (new, ~100 lines)
- `pyproject.toml` (update package data)

### Importance
Without templates and static files, the web UI cannot render. These are essential for the review command.

### Proposed Solution
1. Create directories:
   ```
   src/dot_work/review/templates/
   src/dot_work/review/static/
   ```
2. Copy files:
   - `incoming/review/src/agent_review/templates/index.html` → `src/dot_work/review/templates/`
   - `incoming/review/src/agent_review/static/app.css` → `src/dot_work/review/static/`
   - `incoming/review/src/agent_review/static/app.js` → `src/dot_work/review/static/`
3. Update `pyproject.toml` to include package data:
   ```toml
   [tool.hatch.build.targets.wheel]
   packages = ["src/dot_work"]
   artifacts = [
       "src/dot_work/prompts/*",
       "src/dot_work/review/templates/*",
       "src/dot_work/review/static/*",
   ]
   ```

### Acceptance Criteria
- [ ] Templates directory exists with index.html
- [ ] Static directory exists with app.css and app.js
- [ ] `pyproject.toml` includes review assets in package data
- [ ] `pip install .` includes the assets in the wheel

### Notes
Web UI uses CDN for Tailwind CSS and highlight.js. No need to bundle these locally unless offline support is required.

---

---
id: "MIGRATE-004@d4e5f6"
title: "Add new dependencies for review functionality"
description: "Add fastapi, uvicorn, and pydantic to pyproject.toml"
created: 2024-12-21
section: "config"
tags: [migration, dependencies, review]
type: enhancement
priority: high
status: proposed
references:
  - pyproject.toml
  - incoming/review/pyproject.toml
---

### Problem
The review functionality requires FastAPI for the web server, uvicorn as ASGI server, and pydantic for data models. These are not currently in dot-work's dependencies.

### Current Dependencies (dot-work)
```toml
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "pyyaml>=6.0.0",
    "jinja2>=3.1.0",
]
```

### New Dependencies Required
```toml
dependencies = [
    # ... existing ...
    "fastapi>=0.115.0",
    "uvicorn>=0.32.0",
    "pydantic>=2.6.0",
]
```

### Affected Files
- `pyproject.toml`

### Importance
Without these dependencies, the review command cannot function. FastAPI is the web framework, uvicorn runs the server, pydantic provides data validation.

### Proposed Solution
1. Add to `[project.dependencies]`:
   ```toml
   "fastapi>=0.115.0",
   "uvicorn>=0.32.0",
   "pydantic>=2.6.0",
   ```
2. Add dev dependencies for async testing:
   ```toml
   "pytest-asyncio>=0.24.0",
   "httpx>=0.27.0",
   ```
3. Run `uv sync` to update lockfile
4. Verify: `uv run python -c "import fastapi, uvicorn, pydantic"`

### Acceptance Criteria
- [ ] fastapi, uvicorn, pydantic in dependencies
- [ ] pytest-asyncio, httpx in dev dependencies
- [ ] `uv sync` succeeds
- [ ] No dependency conflicts with existing packages

### Notes
Version constraints chosen for Python 3.10+ compatibility:
- fastapi 0.115+ has Python 3.10 improvements
- pydantic 2.6+ is stable v2 with good performance

---

---
id: "MIGRATE-005@e5f6a7"
title: "Integrate review command into dot-work CLI"
description: "Add 'review' subcommand with 'export' nested command"
created: 2024-12-21
section: "cli"
tags: [migration, cli, review]
type: enhancement
priority: high
status: proposed
depends_on: ["MIGRATE-001@a1b2c3", "MIGRATE-002@b2c3d4", "MIGRATE-003@c3d4e5", "MIGRATE-004@d4e5f6"]
references:
  - src/dot_work/cli.py
  - incoming/review/src/agent_review/cli.py
---

### Problem
The main dot-work CLI needs a `review` subcommand that launches the web UI, with a nested `review export` command for generating agent bundles.

### Target CLI Interface
```bash
# Launch review UI
dot-work review [--base HEAD] [--host 127.0.0.1] [--port 0]

# Export comments
dot-work review export [--latest] [--id REVIEW_ID] [--format agent-md]
```

### Affected Files
- `src/dot_work/cli.py`

### Importance
This is the user-facing integration point. Without CLI commands, users cannot access review functionality.

### Proposed Solution
Add to `cli.py`:

```python
from dot_work.review import server, exporter, storage, git

# Create review subcommand group
review_app = typer.Typer(help="Code review with AI export.")

@review_app.callback(invoke_without_command=True)
def review_main(
    ctx: typer.Context,
    base: str = typer.Option("HEAD", "--base", help="Base ref to diff against"),
    host: str = typer.Option("127.0.0.1", "--host", help="Server host"),
    port: int = typer.Option(0, "--port", help="Server port"),
) -> None:
    """Launch review UI for uncommitted changes."""
    if ctx.invoked_subcommand is None:
        # Launch the review server
        server.main(base_ref=base, host=host, port=port)

@review_app.command("export")
def review_export(
    latest: bool = typer.Option(True, "--latest", help="Export latest review"),
    review_id: str = typer.Option("", "--id", help="Specific review ID"),
    fmt: str = typer.Option("agent-md", "--format", help="Export format"),
) -> None:
    """Export review comments for AI consumption."""
    # ... export logic ...

# Register in main app
app.add_typer(review_app, name="review")
```

### Acceptance Criteria
- [ ] `dot-work review` launches web UI
- [ ] `dot-work review --help` shows options
- [ ] `dot-work review export` exports comments
- [ ] `dot-work review export --help` shows export options
- [ ] Exit codes match original: 0 (success), 1 (bad format), 2 (no reviews)

### Notes
The callback pattern with `invoke_without_command=True` allows `dot-work review` to launch the server while still supporting `dot-work review export` as a subcommand.

---

---
id: "MIGRATE-006@f6a7b8"
title: "Migrate review unit tests"
description: "Copy and adapt unit tests from agent-review to dot-work test suite"
created: 2024-12-21
section: "tests"
tags: [migration, tests, review]
type: test
priority: high
status: proposed
depends_on: ["MIGRATE-002@b2c3d4"]
references:
  - incoming/review/tests/unit/
  - tests/unit/
---

### Problem
The agent-review project has 56 unit tests that need to be migrated. These test the git, models, storage, exporter, and config modules.

### Source Tests
| File | Tests | Coverage |
|------|-------|----------|
| test_git.py | 17 | Git operations |
| test_models.py | 16 | Pydantic models |
| test_storage.py | 12 | Comment persistence |
| test_exporter.py | 6 | Agent export |
| test_config.py | 5 | Configuration |

### Affected Files
- `tests/unit/test_review_git.py` (new)
- `tests/unit/test_review_models.py` (new)
- `tests/unit/test_review_storage.py` (new)
- `tests/unit/test_review_exporter.py` (new)
- `tests/unit/test_review_config.py` (new)
- `tests/conftest.py` (add fixtures)

### Importance
Tests ensure the migrated code works correctly. Without tests, we cannot validate the integration.

### Proposed Solution
1. Copy test files with `test_review_` prefix
2. Update imports from `agent_review` to `dot_work.review`
3. Copy required fixtures from `incoming/review/tests/conftest.py`:
   - `tmp_git_repo` - creates temp Git repo
   - `sample_comments` - generates test data
4. Run tests: `uv run pytest tests/unit/test_review_*.py -v`

### Acceptance Criteria
- [ ] All 56 tests copied and passing
- [ ] Fixtures integrated into tests/conftest.py
- [ ] No test name conflicts with existing tests
- [ ] Coverage for review modules ≥ 75%

### Notes
May need to adjust paths in fixtures for Windows compatibility. Use `pathlib.Path` consistently.

---

---
id: "MIGRATE-007@a7b8c9"
title: "Add review integration tests"
description: "Migrate server integration tests with proper markers"
created: 2024-12-21
section: "tests"
tags: [migration, tests, integration, review]
type: test
priority: medium
status: proposed
depends_on: ["MIGRATE-006@f6a7b8"]
references:
  - incoming/review/tests/integration/
  - tests/integration/
---

### Problem
The agent-review project has ~10 integration tests for the FastAPI server. These require special handling with `pytest-asyncio` and `httpx`.

### Affected Files
- `tests/integration/test_review_server.py` (new)
- `tests/conftest.py` (add async fixtures)

### Importance
Integration tests verify the full review workflow including HTTP endpoints.

### Proposed Solution
1. Create `tests/integration/` directory if not exists
2. Copy server integration tests
3. Add `@pytest.mark.integration` marker
4. Update imports
5. Add async fixtures for test client

### Acceptance Criteria
- [ ] Integration tests in `tests/integration/test_review_server.py`
- [ ] All tests marked with `@pytest.mark.integration`
- [ ] Tests pass with `uv run pytest -m integration`
- [ ] Tests skipped by default (require `--integration` flag)

### Notes
Integration tests may be slower. Consider adding `@pytest.mark.slow` for particularly long tests.

---

---
id: "MIGRATE-008@b8c9d0"
title: "Update Python version requirement to 3.11+"
description: "agent-review requires Python 3.11 for tomllib"
created: 2024-12-21
section: "config"
tags: [migration, python-version, breaking-change]
type: enhancement
priority: high
status: proposed
references:
  - pyproject.toml
  - incoming/review/pyproject.toml
---

### Problem
dot-work currently supports Python 3.10+, but agent-review requires Python 3.11+ because it uses `tomllib` (introduced in 3.11).

### Current State
- dot-work: `requires-python = ">=3.10"`
- agent-review: `requires-python = ">=3.11"`

### Affected Files
- `pyproject.toml`
- `.github/workflows/*.yml` (if exists - CI configuration)
- README.md (update requirements section)

### Importance
Without bumping to Python 3.11, the review module cannot be imported. This is a breaking change for users on Python 3.10.

### Proposed Solution
**Option A: Bump to Python 3.11 (Recommended)**
1. Update `requires-python = ">=3.11"`
2. Update ruff/mypy target versions
3. Update classifiers
4. Document breaking change in CHANGELOG

**Option B: Make tomllib optional**
1. Keep 3.10+ support
2. Use conditional import:
   ```python
   try:
       import tomllib
   except ImportError:
       import tomli as tomllib
   ```
3. Add `tomli>=2.0.0` as fallback dependency

### Acceptance Criteria
- [ ] Python version requirement consistent across project
- [ ] All tools (ruff, mypy) use matching Python version
- [ ] README updated with requirements
- [ ] Breaking change documented

### Notes
Recommend Option A (bump to 3.11) because:
- Python 3.10 EOL is October 2026
- Python 3.11 has significant performance improvements
- Simplifies maintenance

---

---
id: "MIGRATE-009@c9d0e1"
title: "Update storage path to .work/reviews/"
description: "Integrate review storage with .work/ directory structure"
created: 2024-12-21
section: "src/dot_work/review"
tags: [migration, config, storage, review]
type: enhancement
priority: medium
status: proposed
depends_on: ["MIGRATE-002@b2c3d4"]
references:
  - src/dot_work/review/config.py
  - src/dot_work/review/storage.py
---

### Problem
agent-review stores data in `.agent-review/` but dot-work uses `.work/` as its standard directory. For consistency, review data should go in `.work/reviews/`.

### Current Structure (agent-review)
```
.agent-review/
├── reviews/
│   └── 20251220-143052/
│       └── comments.jsonl
└── exports/
    └── 20251220-143052/
        └── agent-review.md
```

### Target Structure
```
.work/
├── agent/              # existing issue tracker
│   └── ...
└── reviews/            # new: review storage
    ├── 20251220-143052/
    │   └── comments.jsonl
    └── exports/
        └── 20251220-143052/
            └── review.md
```

### Affected Files
- `src/dot_work/review/config.py`
- `src/dot_work/review/storage.py`

### Importance
Consistent directory structure improves user experience. All dot-work artifacts live under `.work/`.

### Proposed Solution
1. Update `config.py`:
   ```python
   @dataclass
   class Config:
       storage_dir: str = ".work/reviews"  # Changed from ".agent-review"
   ```
2. Update environment variable:
   - `DOT_WORK_REVIEW_STORAGE_DIR` (was `AGENT_REVIEW_STORAGE_DIR`)
3. Rename export file: `review.md` (was `agent-review.md`)

### Acceptance Criteria
- [ ] Default storage in `.work/reviews/`
- [ ] Environment variable renamed to `DOT_WORK_REVIEW_*`
- [ ] Export file renamed to `review.md`
- [ ] Tests updated for new paths
- [ ] Migration guide for existing users (optional)

### Notes
Consider adding migration helper to move `.agent-review/` → `.work/reviews/` for existing users.

---

---
id: "MIGRATE-010@d0e1f2"
title: "Add review command documentation to README"
description: "Document the new review command and workflow"
created: 2024-12-21
section: "docs"
tags: [migration, docs, review]
type: docs
priority: medium
status: proposed
depends_on: ["MIGRATE-005@e5f6a7"]
references:
  - README.md
  - incoming/review/README.md
---

### Problem
The README needs to document the new `review` command, its purpose, usage, and workflow.

### Affected Files
- `README.md`

### Importance
Users need to know about the new feature and how to use it.

### Proposed Solution
Add a new section to README:

```markdown
## Code Review for AI Agents

The `review` command provides a local web UI for reviewing Git changes and exporting feedback for AI coding assistants.

### Quick Start

```bash
# Launch review UI
dot-work review

# Review against a specific branch
dot-work review --base main

# Export comments for AI
dot-work review export
```

### Workflow

1. **Make changes** - Edit files in your repository
2. **Launch review** - `dot-work review` opens browser
3. **Add comments** - Click lines to add feedback
4. **Export** - `dot-work review export` creates markdown bundle
5. **Feed to AI** - Give the export to your AI coding assistant
```

### Acceptance Criteria
- [ ] README includes review command documentation
- [ ] Workflow diagram or steps explained
- [ ] Command reference table updated
- [ ] Example usage shown

### Notes
Keep documentation concise. Link to detailed docs if needed.

---

---
id: "MIGRATE-011@e1f2a3"
title: "Add review CLI tests"
description: "Test the review command integration with CLI"
created: 2024-12-21
section: "tests"
tags: [migration, tests, cli, review]
type: test
priority: high
status: proposed
depends_on: ["MIGRATE-005@e5f6a7"]
references:
  - tests/unit/test_cli.py
  - src/dot_work/cli.py
---

### Problem
The new `review` and `review export` commands need CLI tests similar to existing commands.

### Affected Files
- `tests/unit/test_cli.py` (add test classes)

### Importance
Ensures the CLI integration works correctly and catches regressions.

### Proposed Solution
Add test classes to `test_cli.py`:

```python
class TestReviewCommand:
    """Tests for 'dot-work review' command."""
    
    def test_review_help(self, cli_runner):
        result = cli_runner.invoke(app, ["review", "--help"])
        assert result.exit_code == 0
        assert "review" in result.output

    def test_review_export_help(self, cli_runner):
        result = cli_runner.invoke(app, ["review", "export", "--help"])
        assert result.exit_code == 0

    def test_review_export_no_reviews(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Init git repo
        ...
        result = cli_runner.invoke(app, ["review", "export"])
        assert result.exit_code == 2
        assert "no reviews" in result.output.lower()
```

### Acceptance Criteria
- [ ] TestReviewCommand class with ≥5 tests
- [ ] TestReviewExportCommand class with ≥5 tests
- [ ] Tests cover help, success, and error paths
- [ ] All tests pass

### Notes
Some tests may need a mock Git repo. Use existing `tmp_git_repo` fixture.

---

---
id: "MIGRATE-012@f2a3b4"
title: "Clean up incoming/review after successful migration"
description: "Remove incoming/review directory after integration complete"
created: 2024-12-21
section: "cleanup"
tags: [migration, cleanup, review]
type: enhancement
priority: low
status: proposed
depends_on: ["MIGRATE-001@a1b2c3", "MIGRATE-002@b2c3d4", "MIGRATE-003@c3d4e5", "MIGRATE-004@d4e5f6", "MIGRATE-005@e5f6a7", "MIGRATE-006@f6a7b8", "MIGRATE-011@e1f2a3"]
references:
  - incoming/review/
---

### Problem
After successful migration, the `incoming/review/` directory is redundant and should be removed.

### Affected Files
- `incoming/review/` (entire directory)
- `.gitignore` (if incoming/ was added)

### Importance
Reduces confusion and codebase size. Clean repo structure.

### Proposed Solution
1. Verify all migration issues are complete
2. Verify all tests pass: `uv run python scripts/build.py`
3. Remove `incoming/review/` directory
4. Remove `incoming/` if empty
5. Commit with message: `cleanup: remove incoming/review after migration`

### Acceptance Criteria
- [ ] All MIGRATE-* issues completed
- [ ] All 280+ tests passing
- [ ] `incoming/review/` removed
- [ ] No references to `agent_review` remain

### Notes
This is the final migration task. Do not execute until all others complete.

---

