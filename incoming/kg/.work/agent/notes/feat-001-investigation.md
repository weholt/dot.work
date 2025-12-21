# Investigation: FEAT-001@c7a3b1 — Project Scaffolding

Investigation started: 2024-12-20

## Issue Summary
Create production-ready Python project structure with pyproject.toml, build script, and tooling.

## Source Documents Reviewed
- [python-project-from-discussion.prompt.md](.github/prompts/python-project-from-discussion.prompt.md) - Template for project structure
- [chat.md](chat.md) - Core architecture (dependencies: stdlib, typer, rich)
- [AGENTS.md](AGENTS.md) - Existing agent guidelines (already has uv run instructions)

## Key Decisions from Design Docs

### Package Name
- **Package**: `kgshred`
- **CLI entry point**: `kg`

### Dependencies (from chat.md)
Core:
- Python stdlib only (sqlite3, hashlib, json, re, pathlib)
- typer (CLI)
- rich (formatting)

Optional:
- httpx (for HTTP embedders)
- hnswlib (for ANN - optional extra)
- pyyaml (for frontmatter parsing)

Dev:
- pytest, pytest-cov, pytest-mock, pytest-timeout
- ruff, mypy
- types-PyYAML

### Project Structure
```
kgtool-2/
├── pyproject.toml
├── README.md
├── AGENTS.md (exists, needs update)
├── .gitignore (to create)
├── scripts/
│   └── build.py
├── src/
│   └── kgshred/
│       ├── __init__.py
│       ├── cli.py
│       └── config.py
└── tests/
    ├── conftest.py
    ├── unit/
    │   └── test_config.py
    └── integration/
        └── test_build_pipeline.py
```

## Files to Create

1. `pyproject.toml` - Full config with hatchling, ruff, mypy, pytest
2. `scripts/build.py` - Build pipeline from template
3. `src/kgshred/__init__.py` - Package exports
4. `src/kgshred/cli.py` - Thin CLI layer with typer
5. `src/kgshred/config.py` - Configuration management
6. `tests/conftest.py` - Pytest fixtures
7. `tests/unit/test_config.py` - Config tests
8. `.gitignore` - Standard Python gitignore
9. `README.md` - Project documentation

## Implementation Plan

1. Create directory structure
2. Create pyproject.toml with all dependencies and tool configs
3. Create scripts/build.py from template
4. Create src/kgshred/__init__.py
5. Create src/kgshred/cli.py with basic `kg` command
6. Create src/kgshred/config.py with DB path management
7. Create tests structure with conftest.py
8. Create basic test files
9. Create .gitignore
10. Create README.md

## Risks
- None significant - this is standard scaffolding
- AGENTS.md already exists and has good content

## Acceptance Criteria (from issue)
- [ ] `uv sync` installs all dependencies
- [ ] `uv run python scripts/build.py` runs full pipeline
- [ ] Package is importable as `from kgshred import ...`
- [ ] CLI entry point `kg` is registered
- [ ] All quality gates pass (ruff, mypy, pytest)
