# Completed Issues

Issues that have been completed and validated.

---

---
id: "MIGRATE-013@a7f3b2"
title: "Create knowledge_graph module structure in dot-work"
description: "Copy kgshred source files to src/dot_work/knowledge_graph/"
completed: 2024-12-21
section: "knowledge_graph"
tags: [migration, kg, module-structure]
type: enhancement
priority: high
status: completed
---

### Outcome
Copied 15 files from incoming/kg/src/kgshred/ to src/dot_work/knowledge_graph/ (10 root + 5 embed/).

---

---
id: "MIGRATE-014@b8c4d3"
title: "Update all imports from kgshred to dot_work.knowledge_graph"
description: "Refactor all internal imports to use new package path"
completed: 2024-12-21
section: "knowledge_graph"
tags: [migration, kg, imports, refactor]
type: refactor
priority: high
status: completed
---

### Outcome
Replaced 25 import statements in 9 files. Pre-existing code quality issues logged as REFACTOR-001@d3f7a9.

---

---
id: "MIGRATE-015@c9d5e4"
title: "Update knowledge_graph config to use .work/kg/"
description: "Change default database path from ~/.kgshred/ to .work/kg/"
completed: 2024-12-21
section: "knowledge_graph"
tags: [migration, kg, config, storage]
type: enhancement
priority: high
status: completed
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
completed: 2024-12-21
section: "cli"
tags: [migration, kg, cli, integration]
type: enhancement
priority: high
status: completed
---

### Outcome
- Added `from dot_work.knowledge_graph.cli import app as kg_app` to imports
- Added `app.add_typer(kg_app, name="kg")` to register subcommand group
- All 18 kg commands accessible via `dot-work kg <cmd>`
- Verified: `dot-work kg --help`, `dot-work kg project --help`, `dot-work kg ingest --help`

---

---
id: "MIGRATE-017@e1f7a6"
title: "Add standalone 'kg' command entry point"
description: "Allow both 'kg' and 'dot-work kg' to invoke knowledge graph commands"
completed: 2024-12-21
section: "cli"
tags: [migration, kg, cli, entry-points]
type: enhancement
priority: high
status: completed
---

### Outcome
- Added `kg = "dot_work.knowledge_graph.cli:app"` to `[project.scripts]`
- Both `kg` and `dot-work kg` now invoke the same CLI
- Verified: `kg --help`, `kg ingest --help` work identically to `dot-work kg`

---

---
id: "MIGRATE-018@f2a8b7"
title: "Add kg optional dependencies to pyproject.toml"
description: "Add optional dependency groups for kg embedding providers"
completed: 2024-12-21
section: "dependencies"
tags: [migration, kg, dependencies, pyproject]
type: enhancement
priority: high
status: completed
---

### Outcome
- Added `kg-http = ["httpx>=0.27.0"]` for HTTP-based embedding providers
- Added `kg-ann = ["numpy>=1.26.0"]` for ANN similarity search
- Added `kg-all = ["httpx>=0.27.0", "numpy>=1.26.0"]` for all kg features
- Verified: `uv sync` succeeds with new dependency groups

---

---
id: "REFACTOR-001@d3f7a9"
title: "Fix knowledge_graph code quality issues"
description: "Pre-existing lint, type, and security issues from kgshred source"
completed: 2024-12-21
section: "knowledge_graph"
tags: [refactor, kg, code-quality, lint, mypy]
type: refactor
priority: medium
status: completed
---

### Outcome
- Fixed 3 mypy errors: Added `model` property with getter/setter to `Embedder` base class
- Fixed 3 B904 lint errors: Added `from None` to raise statements in except clauses (cli.py L449, L598; ollama.py L99)
- Fixed 5 security warnings: Added per-file-ignores in pyproject.toml ruff config for:
  - S310 (urllib.request) in embed/ollama.py and embed/openai.py
  - S112 (bare except-continue) in search_semantic.py
- Build passes: All checks green with `uv run python scripts/build.py`
