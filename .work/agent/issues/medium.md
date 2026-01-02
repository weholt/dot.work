# Medium Priority Issues (P2)

Enhancements, technical debt, code quality improvements.

---
id: "SPLIT-008@h8i9j0"
title: "Extract dot-container package from container submodule"
description: "Create standalone dot-container GitHub project for Docker provisioning"
created: 2026-01-02
section: "extraction/container"
tags: [feature, extraction, dot-container, has-deps]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/container/
  - tests/unit/container/
  - tests/integration/container/
  - split.md
---

### Problem
The container submodule needs to be extracted to a standalone package `dot-container`.

### Affected Files
Source files:
- `src/dot_work/container/__init__.py`
- `src/dot_work/container/provision/` (all files)

Test files:
- `tests/unit/container/provision/`
- `tests/integration/container/provision/`

### Importance
**MEDIUM**: Container module is smaller, recently developed, clean dependencies.

### Proposed Solution
1. Create new GitHub repository `dot-container`
2. Extract files following standard template
3. Create pyproject.toml:
   ```toml
   dependencies = [
       "typer>=0.12.0",
       "rich>=13.0.0",
       "python-frontmatter>=1.1.0",
   ]
   ```

### Acceptance Criteria
- [ ] Repository created with correct structure
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] `dot-container provision` works standalone
- [ ] `dot-work container provision` works as plugin

### Validation Plan
```bash
uv sync --dev
uv run pytest tests/ -v
uv run dot-container provision --help
```

### Dependencies
Blocked by: SPLIT-001, SPLIT-002, SPLIT-006
Blocks: None

### Clarifications Needed
None.

### Notes
Container module has active development (FEAT-027, FEAT-028 in shortlist). Coordinate timing.

---
id: "SPLIT-009@i9j0k1"
title: "Extract dot-git package from git submodule"
description: "Create standalone dot-git GitHub project for git history analysis"
created: 2026-01-02
section: "extraction/git"
tags: [feature, extraction, dot-git, has-deps]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/git/
  - tests/unit/git/
  - tests/integration/test_git_history.py
  - split.md
---

### Problem
The git submodule needs to be extracted to a standalone package `dot-git`.

### Affected Files
Source files:
- `src/dot_work/git/__init__.py`
- `src/dot_work/git/cli.py`
- `src/dot_work/git/complexity.py`
- `src/dot_work/git/file_analyzer.py`
- `src/dot_work/git/models.py`
- `src/dot_work/git/services.py`

Test files:
- `tests/unit/git/` (6 files)
- `tests/integration/test_git_history.py`

### Importance
**MEDIUM**: git module has LLM optional dependencies to handle.

### Proposed Solution
1. Create new GitHub repository `dot-git`
2. Create pyproject.toml:
   ```toml
   dependencies = [
       "typer>=0.12.0",
       "rich>=13.0.0",
       "GitPython>=3.1.0",
       "radon>=6.0.0",
       "tqdm>=4.66.0",
   ]
   
   [project.optional-dependencies]
   llm = [
       "openai>=1.0.0",
       "anthropic>=0.3.0",
   ]
   ```

### Acceptance Criteria
- [ ] Repository created
- [ ] All 6 unit tests pass
- [ ] Integration test passes
- [ ] LLM optional deps work
- [ ] `dot-git history` works standalone

### Validation Plan
```bash
uv sync --dev
uv run pytest tests/ -v
uv run dot-git history --help

# Test LLM
uv sync --extra llm
uv run dot-git history --from main --to HEAD --llm
```

### Dependencies
Blocked by: SPLIT-001, SPLIT-002, SPLIT-006
Blocks: None

### Clarifications Needed
None.

### Notes
None.

---
id: "SPLIT-010@j0k1l2"
title: "Extract dot-harness package from harness submodule"
description: "Create standalone dot-harness GitHub project for Claude Agent SDK integration"
created: 2026-01-02
section: "extraction/harness"
tags: [feature, extraction, dot-harness, has-deps]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/harness/
  - tests/unit/harness/
  - split.md
---

### Problem
The harness submodule needs to be extracted to a standalone package `dot-harness`.

### Affected Files
Source files:
- `src/dot_work/harness/__init__.py`
- `src/dot_work/harness/cli.py`
- `src/dot_work/harness/client.py`
- `src/dot_work/harness/tasks.py`

Test files:
- `tests/unit/harness/test_client.py`
- `tests/unit/harness/test_tasks.py`

### Importance
**MEDIUM**: harness is smallest submodule (2 test files), clean extraction.

### Proposed Solution
1. Create new GitHub repository `dot-harness`
2. Create pyproject.toml:
   ```toml
   dependencies = [
       "typer>=0.12.0",
       "rich>=13.0.0",
   ]
   
   [project.optional-dependencies]
   sdk = [
       "claude-agent-sdk>=0.1.0",
       "anyio>=4.0.0",
   ]
   ```

### Acceptance Criteria
- [ ] Repository created
- [ ] Both unit tests pass
- [ ] `dot-harness` works standalone
- [ ] SDK optional dep works

### Validation Plan
```bash
uv sync --dev
uv run pytest tests/ -v
uv run dot-harness --help
```

### Dependencies
Blocked by: SPLIT-001, SPLIT-002, SPLIT-006
Blocks: None

### Clarifications Needed
None.

### Notes
Consider if harness is even needed as separate package given its small size.

---
id: "SPLIT-011@k1l2m3"
title: "Extract dot-overview package from overview submodule"
description: "Create standalone dot-overview GitHub project for codebase overview generation"
created: 2026-01-02
section: "extraction/overview"
tags: [feature, extraction, dot-overview, has-deps]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/overview/
  - tests/unit/overview/
  - split.md
---

### Problem
The overview submodule needs to be extracted to a standalone package `dot-overview`.

### Affected Files
Source files:
- `src/dot_work/overview/__init__.py`
- `src/dot_work/overview/cli.py`
- `src/dot_work/overview/code_parser.py`
- `src/dot_work/overview/markdown_parser.py`
- `src/dot_work/overview/models.py`
- `src/dot_work/overview/pipeline.py`
- `src/dot_work/overview/reporter.py`
- `src/dot_work/overview/scanner.py`

Test files:
- `tests/unit/overview/` (5 files)

### Importance
**MEDIUM**: overview has libcst dependency (heavy) that should be isolated.

### Proposed Solution
1. Create new GitHub repository `dot-overview`
2. Create pyproject.toml:
   ```toml
   dependencies = [
       "typer>=0.12.0",
       "rich>=13.0.0",
       "libcst>=1.1.0",
   ]
   ```

### Acceptance Criteria
- [ ] Repository created
- [ ] All 5 unit tests pass
- [ ] `dot-overview` works standalone
- [ ] Outputs match current behavior

### Validation Plan
```bash
uv sync --dev
uv run pytest tests/ -v
uv run dot-overview . docs/
```

### Dependencies
Blocked by: SPLIT-001, SPLIT-002, SPLIT-006
Blocks: None

### Clarifications Needed
None.

### Notes
libcst is ~50MB, isolating it significantly reduces core package size.

---
id: "SPLIT-012@l2m3n4"
title: "Extract dot-python package from python submodule"
description: "Create standalone dot-python GitHub project for Python build/scan utilities"
created: 2026-01-02
section: "extraction/python"
tags: [feature, extraction, dot-python, has-deps]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/python/
  - tests/unit/python/
  - split.md
---

### Problem
The python submodule needs to be extracted to a standalone package `dot-python`.

### Affected Files
Source files:
- `src/dot_work/python/__init__.py`
- `src/dot_work/python/build/` (all files)
- `src/dot_work/python/scan/` (all files)

Test files:
- `tests/unit/python/build/`
- `tests/unit/python/scan/`

### Importance
**MEDIUM**: python module has pybuilder alias to preserve.

### Proposed Solution
1. Create new GitHub repository `dot-python`
2. Create pyproject.toml:
   ```toml
   dependencies = [
       "typer>=0.12.0",
       "rich>=13.0.0",
   ]
   
   [project.optional-dependencies]
   scan-graph = ["networkx>=3.0", "pyvis>=0.3.0"]
   
   [project.scripts]
   dot-python = "dot_python.cli:app"
   pybuilder = "dot_python.build.cli:main"
   ```

### Acceptance Criteria
- [ ] Repository created
- [ ] All unit tests pass
- [ ] `dot-python build` works standalone
- [ ] `pybuilder` alias works
- [ ] scan-graph optional deps work

### Validation Plan
```bash
uv sync --dev
uv run pytest tests/ -v
uv run dot-python build --help
uv run pybuilder --help
```

### Dependencies
Blocked by: SPLIT-001, SPLIT-002, SPLIT-006
Blocks: None

### Clarifications Needed
None.

### Notes
None.

---
id: "SPLIT-013@m3n4o5"
title: "Extract dot-version package from version submodule"
description: "Create standalone dot-version GitHub project for date-based version management"
created: 2026-01-02
section: "extraction/version"
tags: [feature, extraction, dot-version, has-deps]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/version/
  - tests/unit/version/
  - split.md
---

### Problem
The version submodule needs to be extracted to a standalone package `dot-version`.

### Affected Files
Source files:
- `src/dot_work/version/__init__.py`
- `src/dot_work/version/changelog.py`
- `src/dot_work/version/cli.py`
- `src/dot_work/version/commit_parser.py`
- `src/dot_work/version/config.py`
- `src/dot_work/version/manager.py`
- `src/dot_work/version/project_parser.py`

Test files:
- `tests/unit/version/` (6 files)

### Importance
**MEDIUM**: version module is standalone with clean LLM optional dep.

### Proposed Solution
1. Create new GitHub repository `dot-version`
2. Create pyproject.toml:
   ```toml
   dependencies = [
       "typer>=0.12.0",
       "rich>=13.0.0",
       "GitPython>=3.1.0",
       "python-dotenv>=1.0.0",
   ]
   
   [project.optional-dependencies]
   llm = ["httpx>=0.24.0"]
   ```

### Acceptance Criteria
- [ ] Repository created
- [ ] All 6 unit tests pass
- [ ] `dot-version freeze` works standalone
- [ ] LLM changelog generation works

### Validation Plan
```bash
uv sync --dev
uv run pytest tests/ -v
uv run dot-version freeze --dry-run
```

### Dependencies
Blocked by: SPLIT-001, SPLIT-002, SPLIT-006
Blocks: None

### Clarifications Needed
None.

### Notes
None.

---
id: "SPLIT-014@n4o5p6"
title: "Create integration test suite for plugin ecosystem"
description: "Add tests that verify plugins work correctly with dot-work core after all extractions"
created: 2026-01-02
section: "testing/integration"
tags: [test, integration, plugins, has-deps]
type: test
priority: medium
status: proposed
references:
  - tests/integration/
  - split.md
---

### Problem
After extracting 9 submodules, need integration tests that verify:
1. Core dot-work works without any plugins
2. Each plugin registers correctly
3. `dot-work[all]` provides full functionality
4. No import errors when mixing installed/not-installed plugins

### Affected Files
- CREATE: `tests/integration/test_plugin_ecosystem.py`

### Importance
**MEDIUM**: Critical for release confidence but can be done after extractions.

### Proposed Solution
Create test suite that:
1. Tests core CLI with no plugins installed (mock entry_points)
2. Tests plugin discovery with mocked plugins
3. Tests graceful degradation (plugin command shows helpful error)
4. Tests full ecosystem with all plugins

### Acceptance Criteria
- [ ] Test core works without plugins
- [ ] Test plugin discovery
- [ ] Test plugin CLI registration
- [ ] Test mixed plugin scenarios
- [ ] All tests pass in CI

### Validation Plan
```bash
./scripts/pytest-with-cgroup.sh 30 tests/integration/test_plugin_ecosystem.py -v
```

### Dependencies
Blocked by: SPLIT-001, SPLIT-002, and at least one extraction (SPLIT-003)
Blocks: None

### Clarifications Needed
None.

### Notes
Consider using pytest fixtures to simulate different plugin installation states.

---
id: "SPLIT-015@o5p6q7"
title: "Update documentation for plugin-based architecture"
description: "Rewrite README and docs to reflect new plugin installation patterns"
created: 2026-01-02
section: "docs/readme"
tags: [docs, readme, plugins, has-deps]
type: docs
priority: medium
status: proposed
references:
  - README.md
  - docs/
  - split.md
---

### Problem
After splitting, documentation must explain:
1. Core vs plugin installation
2. How to install specific plugins
3. How to install all plugins
4. Plugin discovery command
5. Migration from monolithic to plugin-based

### Affected Files
- MODIFY: `README.md`
- CREATE: `docs/plugins.md`
- CREATE: `docs/migration-to-plugins.md`

### Importance
**MEDIUM**: Documentation is essential for adoption but can be done near end.

### Proposed Solution
1. Update README.md installation section:
   ```markdown
   ## Installation
   
   ### Core Only (Minimal)
   pip install dot-work
   
   ### With All Plugins
   pip install dot-work[all]
   
   ### Selective Installation
   pip install dot-work[issues,review,version]
   ```

2. Create docs/plugins.md explaining:
   - Available plugins
   - How to install
   - How plugins work
   - How to create new plugins

3. Create migration guide for existing users

### Acceptance Criteria
- [ ] README reflects plugin architecture
- [ ] Installation examples for all patterns
- [ ] docs/plugins.md created
- [ ] Migration guide created
- [ ] All doc links work

### Validation Plan
```bash
# Link check
uv run python -c "import pathlib; [print(l) for l in pathlib.Path('README.md').read_text().split('\n') if '](/docs/' in l]"

# Manual review of docs
```

### Dependencies
Blocked by: SPLIT-007 (pyproject.toml updates)
Blocks: None

### Clarifications Needed
None.

### Notes
None.

---
