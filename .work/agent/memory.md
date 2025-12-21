# Agent Memory

## Project Context
- Primary language: Python
- Framework: Typer (CLI)
- Package manager: uv
- Test framework: pytest

## User Preferences
- No external dependencies for validation tools (Python 3.11+ stdlib only)
- Follow AGENTS.md guidelines

## Architectural Decisions
- Jinja2 templates for prompt file processing
- Dataclass-based environment configurations

## Patterns & Conventions
- Google-style docstrings
- Type annotations on all functions
- pathlib.Path for file operations

## Known Constraints
- Must use `uv run` for all Python commands
- Coverage minimum: 15% (growing)

## Version Management (MANDATORY)
- **Scheme:** SemVer (MAJOR.MINOR.PATCH)
- **Source of truth:** `pyproject.toml`
- **Sync locations:** none (removed `__version__` from `__init__.py`)
- **Default bump:** patch (no argument = increment patch)
- **Added:** 2024-12-20

## Lessons Learned
- [BUG-001@c5e8f1] 2024-12-20: Use `importlib.metadata.version()` to get package version at runtime instead of maintaining `__version__` in code. Single source of truth = pyproject.toml
- [FEAT-004@b8e1d4] 2024-12-20: Project context detection can auto-populate memory.md by scanning pyproject.toml, package.json, Cargo.toml, go.mod etc.
- [TEST-002@d8c4e1] 2024-12-20: typer.testing.CliRunner is excellent for CLI testing. When typer uses `no_args_is_help=True`, exit code is 2 not 0. Check `result.output` not just `result.stdout` for full output.
- [TEST-002@d8c4e1] 2024-12-20: Environment detection markers in ENVIRONMENTS dict - always verify actual detection patterns before writing tests (e.g., copilot uses `.github/prompts` not `copilot-instructions.md`).
- [MIGRATE-013@a7f3b2] 2024-12-21: MINIMAL ALTERATION PRINCIPLE for migrations - copy files verbatim first, then update imports in separate issue. This makes each step verifiable and reversible.
- [MIGRATE-013@a7f3b2] 2024-12-21: When copying Python modules, use `py_compile` to verify syntax without running imports. Mypy/lint errors for unresolved imports are expected during staged migration.
- [MIGRATE-013@a7f3b2] 2024-12-21: kgshred module structure: 10 root files + embed/ subpackage with 5 files. Uses Typer for CLI, SQLite with FTS5 for search, embeddings for semantic search.
- [MIGRATE-018@f2a8b7] 2024-12-21: For optional dependencies, check if they're already in dev deps (httpx was). PyYAML was already a core dep so no need to add to kg-yaml. Embedding modules use stdlib urllib.request, not httpx - optional httpx group is for potential future refactor.
- [MIGRATE-018@f2a8b7] 2024-12-21: Compare validation against EXACT baseline numbers to detect regressions. Pre-existing issues (lint=3, mypy=3, security=5) are acceptable if unchanged, but any NEW issues are regressions.
