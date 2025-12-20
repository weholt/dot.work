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
