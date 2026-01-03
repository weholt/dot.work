# High Priority Issues (P1)

Core functionality broken or missing documented features.

---
id: "SPLIT-001@a1b2c3"
title: "Create plugin discovery system for dot-work ecosystem"
description: "Implement entry-point based plugin discovery to enable dynamic CLI registration of extracted submodules"
created: 2026-01-02
section: "core/plugins"
tags: [feature, infrastructure, plugins, split-prerequisite]
type: enhancement
priority: high
status: proposed
references:
  - src/dot_work/cli.py
  - split.md
---

### Problem
The current monolithic architecture requires all submodules to be bundled together. To enable the plugin-based architecture described in split.md, we need a plugin discovery system that can:
1. Discover installed plugins via Python entry points
2. Register plugin CLI commands dynamically
3. Provide graceful degradation when plugins are not installed

### Affected Files
- CREATE: `src/dot_work/plugins.py` (new plugin discovery module)
- MODIFY: `src/dot_work/cli.py` (add dynamic registration)
- MODIFY: `pyproject.toml` (add entry-points group)

### Importance
**HIGH**: This is the foundation for the entire split architecture. All 9 submodule extractions depend on this infrastructure being in place first.

### Proposed Solution
1. Create `src/dot_work/plugins.py` with:
   - `DotWorkPlugin` dataclass (name, module, cli_group, version)
   - `discover_plugins()` function using `importlib.metadata.entry_points(group="dot_work.plugins")`
   - `register_plugin_cli(app, plugin)` function to add Typer subcommands
   - Error handling for missing/broken plugins (log warning, continue)

2. Update `pyproject.toml`:
   - Add `[project.entry-points."dot_work.plugins"]` section
   - Document entry point format

3. Update `cli.py`:
   - Call `discover_plugins()` at module load
   - Call `register_plugin_cli()` for each discovered plugin
   - Add `dot-work plugins` command to list installed plugins

### Acceptance Criteria
- [ ] `src/dot_work/plugins.py` created with discover/register functions
- [ ] `discover_plugins()` returns empty list when no plugins installed
- [ ] `discover_plugins()` returns plugin info for installed plugins
- [ ] `register_plugin_cli()` adds Typer subcommand for plugin with CLI_GROUP
- [ ] Broken/missing plugins logged as warning, don't crash CLI
- [ ] `dot-work plugins` command shows installed plugins
- [ ] Unit tests cover discovery, registration, and error cases

### Validation Plan
```bash
# Unit tests
uv run pytest tests/unit/test_plugins.py -v

# Manual validation
uv run dot-work plugins  # Shows "No plugins installed" or list

# After installing a plugin
pip install dot-issues
uv run dot-work plugins  # Shows dot-issues
uv run dot-work db-issues --help  # Plugin CLI works
```

### Dependencies
Blocked by: None
Blocks: SPLIT-002, SPLIT-003, SPLIT-004 through SPLIT-010 (all extractions)

### Clarifications Needed
None.

### Notes
Entry point group name `dot_work.plugins` chosen to match package naming convention.

---
id: "SPLIT-002@b2c3d4"
title: "Refactor cli.py to separate core commands from submodule commands"
description: "Extract submodule-specific CLI code from cli.py (40KB) to prepare for plugin architecture"
created: 2026-01-02
section: "core/cli"
tags: [refactor, cli, split-prerequisite, has-deps]
type: refactor
priority: high
status: proposed
references:
  - src/dot_work/cli.py
  - split.md
---

### Problem
Current `cli.py` is 40KB and contains:
- Core commands (install, list, detect, init, validate, canonical, prompt)
- Submodule commands that will move to plugins (container, db-issues, git, harness, kg, overview, python, review, version, zip)

These must be separated so submodule commands can be moved to their respective plugin packages.

### Affected Files
- MODIFY: `src/dot_work/cli.py` (remove submodule imports, keep core commands)
- No new files created (submodule CLIs already exist in their modules)

### Importance
**HIGH**: Without this refactor, extracted submodules will have circular import issues and cli.py will fail when plugins are not installed.

### Proposed Solution
1. Identify core commands to keep in cli.py:
   - `install`, `list`, `detect`, `init`, `init-work`
   - `validate` (json, yaml, frontmatter)
   - `canonical`, `prompt`
   - `zip` (retained in core per split.md)

2. Remove direct imports from:
   - `from dot_work.container.provision.cli import app as container_provision_app`
   - `from dot_work.git.cli import history_app`
   - `from dot_work.harness.cli import app as harness_app`
   - `from dot_work.knowledge_graph.cli import app as kg_app`
   - `from dot_work.python import python_app`
   - `from dot_work.version.cli import app as version_app`
   - `from dot_work.review.*` imports
   - `from dot_work.overview.*` imports

3. Replace with plugin discovery (after SPLIT-001):
   ```python
   for plugin in discover_plugins():
       register_plugin_cli(app, plugin)
   ```

4. Keep skills_app and subagents_app as they are retained in core.

### Acceptance Criteria
- [ ] cli.py reduced to <15KB (core commands only)
- [ ] All submodule imports removed from top of file
- [ ] Submodule CLIs registered via plugin discovery
- [ ] `dot-work --help` shows core commands
- [ ] `dot-work --help` shows plugin commands when plugins installed
- [ ] Core commands work without any plugins installed
- [ ] Existing tests pass (may need updates for mocking)

### Validation Plan
```bash
# Build with no plugins
uv sync
uv run dot-work --help  # Shows core commands only
uv run dot-work install --help  # Works

# Install one plugin
pip install dot-issues
uv run dot-work --help  # Shows db-issues
uv run dot-work db-issues --help  # Works

# Run existing tests
./scripts/pytest-with-cgroup.sh 30 tests/unit/test_cli.py -v
```

### Dependencies
Blocked by: SPLIT-001 (plugin discovery system)
Blocks: SPLIT-003 through SPLIT-010 (submodule extractions)

### Clarifications Needed
None.

### Notes
The `review` commands are currently inline in cli.py, not in a separate module. These need to be extracted to `src/dot_work/review/cli.py` first.

---
id: "SPLIT-003@c3d4e5"
title: "Extract dot-issues package from db_issues submodule"
description: "Create standalone dot-issues GitHub project with its own pyproject.toml and tests"
created: 2026-01-02
section: "extraction/db-issues"
tags: [feature, extraction, dot-issues, has-deps]
type: enhancement
priority: high
status: proposed
references:
  - src/dot_work/db_issues/
  - tests/unit/db_issues/
  - tests/integration/db_issues/
  - split.md
---

### Problem
The db_issues submodule needs to be extracted to a standalone package `dot-issues` so it can:
- Be installed independently
- Have its own versioning
- Reduce core dot-work size

### Affected Files
Source files to extract:
- `src/dot_work/db_issues/__init__.py`
- `src/dot_work/db_issues/adapters/` (all files)
- `src/dot_work/db_issues/cli.py`
- `src/dot_work/db_issues/config.py`
- `src/dot_work/db_issues/domain/` (all files)
- `src/dot_work/db_issues/services/` (all files)
- `src/dot_work/db_issues/templates/` (all files)

Test files to extract:
- `tests/unit/db_issues/` (17 files)
- `tests/integration/db_issues/` (6 files)

Target structure:
```
dot-issues/
├── src/dot_issues/
│   ├── __init__.py
│   ├── adapters/
│   ├── cli.py  # Add CLI_GROUP = "db-issues"
│   ├── config.py
│   ├── domain/
│   ├── services/
│   └── templates/
├── tests/
│   ├── unit/
│   └── integration/
├── pyproject.toml
├── README.md
└── LICENSE
```

### Importance
**HIGH**: db_issues is one of the largest submodules (17+ unit tests, complex domain model). Extracting it demonstrates the full pattern.

### Proposed Solution
1. Create new GitHub repository `dot-issues`
2. Run extraction script (from split.md Phase 4) for db_issues
3. Create pyproject.toml with dependencies:
   ```toml
   dependencies = [
       "typer>=0.12.0",
       "rich>=13.0.0",
       "sqlmodel>=0.0.22",
       "jinja2>=3.1.0",
       "pyyaml>=6.0.0",
   ]
   ```
4. Update all imports: `from dot_work.db_issues` → `from dot_issues`
5. Add CLI_GROUP = "db-issues" to cli.py
6. Add entry point:
   ```toml
   [project.entry-points."dot_work.plugins"]
   issues = "dot_issues"
   ```
7. Run tests in new package
8. Remove db_issues from dot-work (after plugin system works)

### Acceptance Criteria
- [ ] New repository `dot-issues` created
- [ ] All source files copied with correct structure
- [ ] All imports updated to `dot_issues`
- [ ] pyproject.toml with correct dependencies
- [ ] Entry point registered for dot_work.plugins
- [ ] All 17 unit tests pass in new package
- [ ] All 6 integration tests pass in new package
- [ ] `pip install dot-issues` works
- [ ] `dot-issues --help` works as standalone CLI
- [ ] `dot-work db-issues` works when plugin installed

### Validation Plan
```bash
# In dot-issues repository
uv sync --dev
uv run pytest tests/ -v
uv run dot-issues --help

# Test plugin integration
pip install -e .
pip install dot-work
dot-work plugins  # Shows dot-issues
dot-work db-issues --help  # Works
```

### Dependencies
Blocked by: SPLIT-001, SPLIT-002
Blocks: None (can be done in parallel with other extractions after prerequisites)

### Decisions
- **GitHub organization**: Use same user account as dot-work repository

### Notes
db_issues has no cross-module dependencies (doesn't import from other submodules), making it ideal for first extraction.

---
id: "SPLIT-004@d4e5f6"
title: "Extract dot-kg package from knowledge_graph submodule"
description: "Create standalone dot-kg GitHub project with its own pyproject.toml and tests"
created: 2026-01-02
section: "extraction/knowledge-graph"
tags: [feature, extraction, dot-kg, has-deps]
type: enhancement
priority: high
status: proposed
references:
  - src/dot_work/knowledge_graph/
  - tests/unit/knowledge_graph/
  - tests/integration/knowledge_graph/
  - split.md
---

### Problem
The knowledge_graph submodule needs to be extracted to a standalone package `dot-kg`.

### Affected Files
Source files to extract:
- `src/dot_work/knowledge_graph/` (12+ files including embed/ subdirectory)

Test files to extract:
- `tests/unit/knowledge_graph/` (14 files)
- `tests/integration/knowledge_graph/` (2 files)

### Importance
**HIGH**: knowledge_graph has the most optional dependencies and is the second-largest test suite (16 files). Already has standalone `kg` CLI script.

### Proposed Solution
1. Create new GitHub repository `dot-kg`
2. Extract files following split.md template
3. Create pyproject.toml:
   ```toml
   dependencies = [
       "typer>=0.12.0",
       "rich>=13.0.0",
       "numpy>=1.24.0",
   ]
   
   [project.optional-dependencies]
   http = ["httpx>=0.27.0"]
   ann = ["hnswlib>=0.8.0"]
   vec = ["sqlite-vec>=0.1.0"]
   all = ["httpx>=0.27.0", "hnswlib>=0.8.0", "sqlite-vec>=0.1.0"]
   ```
4. Register both standalone and plugin scripts:
   ```toml
   [project.scripts]
   dot-kg = "dot_kg.cli:app"
   kg = "dot_kg.cli:app"
   
   [project.entry-points."dot_work.plugins"]
   kg = "dot_kg"
   ```

### Acceptance Criteria
- [ ] New repository `dot-kg` created
- [ ] All 14 unit tests pass
- [ ] All 2 integration tests pass
- [ ] `kg` command works standalone
- [ ] `dot-work kg` works when plugin installed
- [ ] Optional dependencies work (http, ann, vec)

### Validation Plan
```bash
# In dot-kg repository
uv sync --dev
uv run pytest tests/ -v
uv run kg --help
uv run dot-kg --help

# Test optional deps
uv sync --extra all
uv run pytest tests/unit/test_embed.py -v
```

### Dependencies
Blocked by: SPLIT-001, SPLIT-002
Blocks: None

### Clarifications Needed
None. All decisions resolved in split.md.

### Notes
The `kg` standalone command is already registered in current pyproject.toml - preserve this for backward compatibility.

---
id: "SPLIT-005@e5f6g7"
title: "Extract dot-review package from review submodule"
description: "Create standalone dot-review GitHub project with FastAPI server and static assets"
created: 2026-01-02
section: "extraction/review"
tags: [feature, extraction, dot-review, has-deps]
type: enhancement
priority: high
status: proposed
references:
  - src/dot_work/review/
  - tests/unit/review/
  - tests/unit/test_review_*.py
  - tests/integration/test_server.py
  - split.md
---

### Problem
The review submodule needs special handling because:
1. It has static assets (JS/CSS) and Jinja2 templates that must be included in package
2. Some review CLI commands are currently inline in cli.py, not in review/cli.py
3. Has 8 unit test files split between `tests/unit/review/` and `tests/unit/test_review_*.py`

### Affected Files
Source files to extract:
- `src/dot_work/review/__init__.py`
- `src/dot_work/review/cli.py` (may need to create/consolidate)
- `src/dot_work/review/config.py`
- `src/dot_work/review/exporter.py`
- `src/dot_work/review/git.py`
- `src/dot_work/review/models.py`
- `src/dot_work/review/server.py`
- `src/dot_work/review/storage.py`
- `src/dot_work/review/static/` (all files)
- `src/dot_work/review/templates/` (all files)

Test files to extract:
- `tests/unit/review/test_git.py`
- `tests/unit/review/test_server.py`
- `tests/unit/review/test_storage.py`
- `tests/unit/test_review_config.py`
- `tests/unit/test_review_exporter.py`
- `tests/unit/test_review_git.py`
- `tests/unit/test_review_models.py`
- `tests/unit/test_review_storage.py`
- `tests/integration/test_server.py`

### Importance
**HIGH**: Review module has web server and asset packaging complexity.

### Proposed Solution
1. First, extract inline CLI commands from `cli.py` to `src/dot_work/review/cli.py`:
   - `review start` command
   - `review export` command
   - Review-related helper functions
2. Create new GitHub repository `dot-review`
3. Create pyproject.toml with hatch configuration for static files:
   ```toml
   [tool.hatch.build.targets.wheel]
   packages = ["src/dot_review"]
   artifacts = [
       "src/dot_review/templates/*",
       "src/dot_review/static/*",
   ]
   ```
4. Consolidate duplicate test files

### Acceptance Criteria
- [ ] Review CLI extracted from main cli.py to review/cli.py
- [ ] New repository `dot-review` created
- [ ] Static assets included in wheel package
- [ ] Templates included in wheel package
- [ ] All 9 test files pass
- [ ] `dot-review start` works standalone
- [ ] `dot-work review start` works when plugin installed
- [ ] Review UI loads in browser with CSS/JS

### Validation Plan
```bash
# Test package includes assets
uv build
unzip -l dist/dot_review-*.whl | grep -E "(static|templates)"

# Run server
uv run dot-review start --port 8888
curl http://localhost:8888/  # Returns HTML with CSS

# Run tests
uv run pytest tests/ -v
```

### Dependencies
Blocked by: SPLIT-001, SPLIT-002
Blocks: None

### Decisions
- **Duplicate test files**: VERIFIED - Tests in `tests/unit/review/` and `tests/unit/test_review_*.py` test different aspects:
  - `test_git.py`: Security validation (ref/path validation, injection prevention)
  - `test_review_git.py`: Git operations (changed_files, repo_root, etc.)
  - `test_storage.py`: Mock-based detailed tests with `get_config` patching
  - `test_review_storage.py`: Simpler fixture-based tests
  - **Action**: Keep both sets - they provide complementary coverage

### Notes
Must verify static assets are correctly included in wheel build before publishing.

---
id: "SPLIT-006@f6g7h8"
title: "Create extraction automation script"
description: "Implement Python script to automate submodule extraction with import rewriting and test migration"
created: 2026-01-02
section: "infrastructure/automation"
tags: [feature, automation, tooling]
type: enhancement
priority: high
status: proposed
references:
  - split.md
  - scripts/
---

### Problem
Manual extraction of 9 submodules is error-prone. Need an automation script that:
1. Copies source files to new package structure
2. Copies and renames test files
3. Rewrites imports (`dot_work.X` → `dot_X`)
4. Generates pyproject.toml from template
5. Generates README.md, LICENSE, CI workflow

### Affected Files
- CREATE: `scripts/extract_plugin.py`

### Importance
**HIGH**: Automation ensures consistency across all 9 extractions and reduces manual errors.

### Proposed Solution
Create `scripts/extract_plugin.py` with:

```python
#!/usr/bin/env python3
"""Extract a dot-work submodule to a standalone package."""

import argparse
import re
import shutil
from pathlib import Path

PLUGIN_CONFIG = {
    "dot-issues": {
        "source_module": "db_issues",
        "target_module": "dot_issues",
        "cli_group": "db-issues",
        "description": "SQLite-based issue tracking",
        "dependencies": [
            "typer>=0.12.0",
            "rich>=13.0.0",
            "sqlmodel>=0.0.22",
            "jinja2>=3.1.0",
            "pyyaml>=6.0.0",
        ],
        "optional_deps": {},
    },
    # ... other plugins
}

def rewrite_imports(content: str, old_module: str, new_module: str) -> str:
    """Rewrite imports from dot_work.X to dot_X."""
    # Handle various import patterns
    patterns = [
        (rf"from dot_work\.{old_module}", f"from {new_module}"),
        (rf"import dot_work\.{old_module}", f"import {new_module}"),
    ]
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    return content

def extract_plugin(name: str, target_dir: Path) -> None:
    """Extract a plugin to target directory."""
    config = PLUGIN_CONFIG[name]
    # ... implementation
```

### Acceptance Criteria
- [ ] Script extracts source files to correct structure
- [ ] Script copies unit and integration tests
- [ ] Script rewrites all imports correctly
- [ ] Script generates pyproject.toml with correct deps
- [ ] Script generates .github/workflows/ci.yml
- [ ] Script generates README.md with usage examples
- [ ] Script handles nested subdirectories (e.g., embed/, provision/)
- [ ] Dry-run mode shows what would be done

### Validation Plan
```bash
# Dry run
uv run python scripts/extract_plugin.py dot-issues --dry-run

# Actual extraction
uv run python scripts/extract_plugin.py dot-issues --output ../dot-issues

# Verify
cd ../dot-issues
uv sync --dev
uv run pytest tests/ -v
```

### Dependencies
Blocked by: None (can be developed in parallel)
Blocks: All extraction issues benefit from this

### Clarifications Needed
None.

### Notes
Consider using AST-based import rewriting for robustness, but regex is sufficient for this codebase.

---
id: "SPLIT-007@g7h8i9"
title: "Update pyproject.toml for plugin-based architecture"
description: "Refactor pyproject.toml to remove submodule dependencies and add optional plugin groups"
created: 2026-01-02
section: "core/packaging"
tags: [refactor, packaging, dependencies, has-deps]
type: refactor
priority: high
status: proposed
references:
  - pyproject.toml
  - split.md
---

### Problem
Current pyproject.toml includes all submodule dependencies in the base package. After extraction:
1. Base dependencies should be minimal (typer, rich, pyyaml, jinja2, gitignore-parser)
2. Plugin packages should be optional dependencies
3. `dot-work[all]` should install everything for backward compatibility

### Affected Files
- MODIFY: `pyproject.toml`

### Importance
**HIGH**: Package size reduction and proper dependency management are primary goals of the split.

### Proposed Solution
Update pyproject.toml:

```toml
[project]
name = "dot-work"
version = "0.2.0"
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "pyyaml>=6.0.0",
    "jinja2>=3.1.0",
    "gitignore-parser>=0.1.0",  # for zip module
]

[project.optional-dependencies]
# Individual plugins
container = ["dot-container>=0.1.0"]
issues = ["dot-issues>=0.1.0"]
git = ["dot-git>=0.1.0"]
harness = ["dot-harness>=0.1.0"]
kg = ["dot-kg>=0.1.0"]
overview = ["dot-overview>=0.1.0"]
python = ["dot-python>=0.1.0"]
review = ["dot-review>=0.1.0"]
version = ["dot-version>=0.1.0"]

# Convenience groups
all = [
    "dot-container>=0.1.0",
    "dot-issues>=0.1.0",
    "dot-git>=0.1.0",
    "dot-harness>=0.1.0",
    "dot-kg>=0.1.0",
    "dot-overview>=0.1.0",
    "dot-python>=0.1.0",
    "dot-review>=0.1.0",
    "dot-version>=0.1.0",
]

dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.6.0",
    "mypy>=1.11.0",
]
```

### Acceptance Criteria
- [ ] Base dependencies reduced to 5 packages
- [ ] All 9 plugins available as optional deps
- [ ] `pip install dot-work` installs minimal package
- [ ] `pip install dot-work[all]` installs everything
- [ ] `pip install dot-work[issues,review]` installs subset
- [ ] Dev dependencies preserved
- [ ] Wheel size reduced by >50%

### Validation Plan
```bash
# Build minimal package
uv build
ls -la dist/dot_work-*.whl  # Check size

# Install minimal
pip install dist/dot_work-*.whl
dot-work --help  # Works
dot-work db-issues --help  # Error: plugin not installed

# Install with all
pip install "dist/dot_work-*.whl[all]"
dot-work db-issues --help  # Works
```

### Dependencies
Blocked by: All 9 extraction issues (SPLIT-003 through SPLIT-011)
Blocks: None (this is final integration step)

### Clarifications Needed
None.

### Notes
This is one of the final steps - can only be completed after all plugins are published to PyPI (or using local paths for testing).
