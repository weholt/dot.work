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
- [MIGRATE-019@a3b9c8] 2025-12-21: Test migration efficiency - use automated search/replace for import updates but verify API compatibility manually. The kgshred tests expect 'backend' field not 'provider' in EmbedderConfig - adjust migrated code accordingly.
- [MIGRATE-042@f6a7b8] 2024-12-23: Import updates sometimes done in previous steps
  - Always verify if import/config tasks are already complete before starting
  - Investigation phase crucial to avoid duplicate work
  - Version module already had dot-work patterns configured in MIGRATE-041
- [TEST-001@c4a9f6] 2025-12-22: Installation functions follow consistent patterns per environment - each creates specific directory structure (copilot: .github/prompts, claude: CLAUDE.md, cursor: .cursor/rules, etc.). All generator functions use render_prompt() for template substitution. Mock console needed for testing to avoid output during tests.
- [TEST-001@c4a9f6] 2025-12-22: Parametrized pytest tests excellent for testing same functionality across multiple variants. Use test_all_environments_create_target_directories pattern: parametrize with (installer_function, expected_path_str, path_type) for clean multi-environment validation.
- [FEAT-005@d5b2e8] 2025-12-22: Template variables enable true multi-environment support. Hardcoded paths like `[text](filename.prompt.md)` are fragile and fail silently when content moves locations. Use `{{ prompt_path }}` which is provided by `build_template_context()` during rendering.
- [FEAT-005@d5b2e8] 2025-12-22: For regex pattern detection of hardcoded references, use negative lookahead: `\[([^\]]+)\]\((?!.*\{\{)([^)]*\.prompt\.md)\)` matches markdown links to .prompt.md that don't contain `{{` - catches `[text](file.prompt.md)` but not `[text]({{ prompt_path }}/file.prompt.md)`.
- [FEAT-005@d5b2e8] 2025-12-22: Regression tests for pattern detection prevent silent failures. Added `TestPromptTemplateization.test_no_hardcoded_prompt_references()` to detect hardcoded links at source time, not at render time. This catches problems before installation.
- [MIGRATE-034@d8e9f0] 2024-12-23: SQLModel's `table=True` argument triggers mypy `call-arg` error. Use `# type: ignore[call-arg]` on model class definitions. The error code must match exactly - `[misc]` won't suppress `[call-arg]`.
- [MIGRATE-034@d8e9f0] 2024-12-23: mypy's import resolution for sqlmodel is inconsistent across scopes. First import in file may error with `[import-not-found]` but subsequent identical imports don't. Solution: Add `# type: ignore[import-not-found]` only to first import that mypy complains about.
- [MIGRATE-034@d8e9f0] 2024-12-23: String-based transitions map for `IssueStatus.can_transition_to()` avoids mypy issues with enum keys. Using `IssueStatus.OPEN` as dict key causes mypy errors - use string keys like `"open"` instead.
- [MIGRATE-034@d8e9f0] 2024-12-23: CLI command named `list` shadows built-in `list()`. Rename to `list_cmd` to avoid shadowing and prevent mypy errors.
- [MIGRATE-034@d8e9f0] 2024-12-23: Consolidating multiple source files into single modules (entities.py, sqlite.py) works well for migration. Reduces import complexity while maintaining functionality.
