# Agent Memory

## Project Context
- Project: dot-work
- Description: Portable AI coding prompts for project scaffolding and issue tracking
- Primary language: Python 3.11+
- Package manager: uv
- Test framework: pytest
- Type checking: mypy
- Linting: ruff
- CLI framework: typer
- License: MIT
- Development status: Beta

## User Preferences
(To be populated as preferences are discovered)

## Architectural Decisions
(To be populated as decisions are made)

## Patterns & Conventions
- Use `uv run` for ALL Python commands
- Use memory-protected wrapper for pytest: `./scripts/pytest-with-cgroup.sh`
- Type hints on ALL functions, Google docstrings for public APIs
- Functions <15 lines, nesting <3 levels, classes <200 lines

## Known Constraints
- Python 3.11+ required
- No business logic in cli.py
- Use `logging` not `print()`
- No bare except clauses
- Test coverage >=75%

## Lessons Learned
- [CR-006@d9b4c3] 2026-01-03: Test coverage for parser functions
  - Testing `_deep_merge()` requires testing: basic merge, nested dicts, empty dict preservation, mutual exclusion (filename/filename_suffix), and non-mutation
  - Testing `_load_global_defaults()` requires: file exists, file missing, malformed YAML, missing defaults key, wrong type for defaults
  - Always test parser edge cases: invalid YAML, missing required fields, environment config validation
  - Memory-protected pytest wrapper (`./scripts/pytest-with-cgroup.sh`) is required to prevent system freezes
