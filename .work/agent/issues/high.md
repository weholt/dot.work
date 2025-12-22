# High Priority Issues (P1)

Core functionality broken or missing documented features.

---

---
id: "TEST-001@c4a9f6"
title: "Add installer integration tests"
description: "Installer install_for_* functions lack comprehensive tests"
created: 2024-12-20
section: "tests"
tags: [testing, coverage, installer]
type: test
priority: high
status: completed
references:
  - tests/unit/test_installer.py
  - src/dot_work/installer.py
---

### Problem
The installer module has 41% coverage. The 10 `install_for_*` functions are not individually tested. CLI command tests (TEST-002) now cover the entry points, but installer internals need more coverage.

### Remaining Work
(CLI tests completed in TEST-002@d8c4e1)

1. Add tests for each `install_for_*` function:
   - Verify correct directories created per environment
   - Verify files have expected content
   - Verify template variables substituted correctly
2. Add parametrized tests across environments
3. Test edge cases (missing prompts, permission errors)

### Acceptance Criteria
- [ ] Each `install_for_*` function has at least one test
- [ ] Coverage for installer.py ≥ 80% (currently 41%)
- [ ] Parametrized tests for all 10 environments

### Notes
CLI tests in TEST-002 now cover:
- ✅ CLI commands (80% coverage)
- ✅ `detect_environment()`
- ✅ `initialize_work_directory()`

Focus remaining effort on `install_for_*` functions.

---



---
id: "MIGRATE-013@a7f3b2"
title: "Create knowledge_graph module structure in dot-work"
description: "Copy kgshred source files to src/dot_work/knowledge_graph/ with proper organization"
created: 2024-12-21
completed: 2024-12-21
section: "knowledge_graph"
tags: [migration, kg, module-structure]
type: enhancement
priority: high
status: completed
references:
  - incoming/kg/src/kgshred/
  - src/dot_work/knowledge_graph/
---

### Problem
The kg (kgshred) project exists as a standalone package in `incoming/kg/`. To integrate it as a dot-work command, we need to create the module structure within dot-work's source tree.

### Source Files to Copy
From `incoming/kg/src/kgshred/`:

| Source File | Destination | Purpose |
|-------------|-------------|---------|
| `__init__.py` | `src/dot_work/knowledge_graph/__init__.py` | Package init, exports |
| `cli.py` | `src/dot_work/knowledge_graph/cli.py` | 18 CLI commands |
| `config.py` | `src/dot_work/knowledge_graph/config.py` | Database path config |
| `db.py` | `src/dot_work/knowledge_graph/db.py` | SQLite with FTS5, schema migrations |
| `graph.py` | `src/dot_work/knowledge_graph/graph.py` | Graph builder from Markdown |
| `parse_md.py` | `src/dot_work/knowledge_graph/parse_md.py` | Markdown parser |
| `render.py` | `src/dot_work/knowledge_graph/render.py` | Document/node renderer |
| `search_fts.py` | `src/dot_work/knowledge_graph/search_fts.py` | FTS5 search functions |
| `search_semantic.py` | `src/dot_work/knowledge_graph/search_semantic.py` | Semantic search with embeddings |
| `ids.py` | `src/dot_work/knowledge_graph/ids.py` | 4-char short ID generation |
| `embed/__init__.py` | `src/dot_work/knowledge_graph/embed/__init__.py` | Embedding subpackage |
| `embed/base.py` | `src/dot_work/knowledge_graph/embed/base.py` | Base embedding class |
| `embed/factory.py` | `src/dot_work/knowledge_graph/embed/factory.py` | Embedding backend factory |
| `embed/ollama.py` | `src/dot_work/knowledge_graph/embed/ollama.py` | Ollama backend |
| `embed/openai.py` | `src/dot_work/knowledge_graph/embed/openai.py` | OpenAI backend |

### Proposed Solution
1. Create directory `src/dot_work/knowledge_graph/`
2. Create subdirectory `src/dot_work/knowledge_graph/embed/`
3. Copy all Python files preserving structure
4. Verify all files are present

### Acceptance Criteria
- [ ] Directory `src/dot_work/knowledge_graph/` created
- [ ] All 10 root module files copied
- [ ] Directory `src/dot_work/knowledge_graph/embed/` created
- [ ] All 4 embed submodule files copied
- [ ] No syntax errors in copied files

### Notes
Do NOT modify imports yet - that's MIGRATE-014. This is pure file copying.

---

---
id: "MIGRATE-014@b8c4d3"
title: "Update all imports in knowledge_graph module from kgshred to dot_work.knowledge_graph"
description: "Refactor all internal imports to use new package path"
created: 2024-12-21
completed: 2024-12-21
section: "knowledge_graph"
tags: [migration, kg, imports, refactor]
type: refactor
priority: high
status: completed
references:
  - src/dot_work/knowledge_graph/
---

### Problem
After copying files from kgshred, all internal imports reference `kgshred.*` which won't resolve. Every import must be updated to `dot_work.knowledge_graph.*`.

### Import Changes Required

| File | Old Import | New Import |
|------|-----------|------------|
| `cli.py` | `from kgshred import db, graph, ...` | `from dot_work.knowledge_graph import db, graph, ...` |
| `cli.py` | `from kgshred.config import ...` | `from dot_work.knowledge_graph.config import ...` |
| `graph.py` | `from kgshred.parse_md import ...` | `from dot_work.knowledge_graph.parse_md import ...` |
| `graph.py` | `from kgshred.ids import ...` | `from dot_work.knowledge_graph.ids import ...` |
| `search_semantic.py` | `from kgshred.embed import ...` | `from dot_work.knowledge_graph.embed import ...` |
| `embed/factory.py` | `from kgshred.embed.base import ...` | `from dot_work.knowledge_graph.embed.base import ...` |
| `embed/factory.py` | `from kgshred.embed.ollama import ...` | `from dot_work.knowledge_graph.embed.ollama import ...` |
| `embed/factory.py` | `from kgshred.embed.openai import ...` | `from dot_work.knowledge_graph.embed.openai import ...` |
| `embed/ollama.py` | `from kgshred.embed.base import ...` | `from dot_work.knowledge_graph.embed.base import ...` |
| `embed/openai.py` | `from kgshred.embed.base import ...` | `from dot_work.knowledge_graph.embed.base import ...` |
| `__init__.py` | Any `kgshred` references | `dot_work.knowledge_graph` references |

### Proposed Solution
1. Use search-and-replace: `from kgshred` → `from dot_work.knowledge_graph`
2. Update any `import kgshred` statements
3. Check for string references like `"kgshred"` in error messages
4. Run `uv run python -c "from dot_work.knowledge_graph import cli"` to verify imports

### Acceptance Criteria
- [ ] No `kgshred` imports remain in `src/dot_work/knowledge_graph/`
- [ ] All modules importable: `from dot_work.knowledge_graph import cli, db, graph, ...`
- [ ] `uv run python -m py_compile src/dot_work/knowledge_graph/*.py` succeeds
- [ ] Type checker passes on knowledge_graph module

### Notes
Depends on MIGRATE-013 (files must exist first).

---

---
id: "MIGRATE-015@c9d5e4"
title: "Update knowledge_graph config to use .work/kg/ for per-project storage"
description: "Change default database path from ~/.kgshred/ to .work/kg/"
created: 2024-12-21
completed: 2024-12-21
section: "knowledge_graph"
tags: [migration, kg, config, storage]
type: enhancement
priority: high
status: completed
references:
  - src/dot_work/knowledge_graph/config.py
---

### Outcome
- Changed `DEFAULT_DB_PATH` from `~/.kgshred/db.sqlite` to `.work/kg/db.sqlite`
- Renamed env var from `KG_DB_PATH` to `DOT_WORK_KG_DB_PATH`
- Added `.expanduser()` for tilde expansion in env var paths
- Directory auto-creation already handled by `Database._ensure_directory()`

---

---
id: "MIGRATE-016@d0e6f5"
title: "Register kg as subcommand group in dot-work CLI"
description: "Add knowledge_graph commands as 'dot-work kg <command>' subcommand group"
created: 2024-12-21
completed: 2024-12-21
section: "cli"
tags: [migration, kg, cli, integration]
type: enhancement
priority: high
status: completed
references:
  - src/dot_work/cli.py
  - src/dot_work/knowledge_graph/cli.py
---

### Outcome
- Added `from dot_work.knowledge_graph.cli import app as kg_app` to imports
- Added `app.add_typer(kg_app, name="kg")` to register subcommand group
- All 18 kg commands accessible via `dot-work kg <cmd>`
- Verified: `dot-work kg --help`, `dot-work kg project --help`, `dot-work kg ingest --help`

---

---
id: "MIGRATE-017@e1f7a6"
title: "Add standalone 'kg' command entry point alongside 'dot-work kg'"
description: "Allow both 'kg' and 'dot-work kg' to invoke knowledge graph commands"
created: 2024-12-21
completed: 2024-12-21
section: "cli"
tags: [migration, kg, cli, entry-points]
type: enhancement
priority: high
status: completed
references:
  - pyproject.toml
  - src/dot_work/knowledge_graph/cli.py
---

### Outcome
- Added `kg = "dot_work.knowledge_graph.cli:app"` to `[project.scripts]`
- Both `kg` and `dot-work kg` now invoke the same CLI
- Verified: `kg --help`, `kg ingest --help` work identically to `dot-work kg`

---

---
id: "MIGRATE-018@f2a8b7"
title: "Add kg optional dependencies to pyproject.toml"
description: "Add httpx, hnswlib, pyyaml as optional dependency groups for kg features"
created: 2024-12-21
completed: 2024-12-21
section: "dependencies"
tags: [migration, kg, dependencies, pyproject]
type: enhancement
priority: high
status: completed
references:
  - pyproject.toml
  - incoming/kg/pyproject.toml
---

### Outcome
- Added `kg-http = ["httpx>=0.27.0"]` optional dependency group
- Added `kg-ann = ["hnswlib>=0.8.0"]` optional dependency group
- Added `kg-all` meta-group combining both
- PyYAML already in core dependencies (not added again)
- Verified: `kg --help` works without optional deps installed
- Embedding modules use stdlib `urllib.request`, work without httpx
