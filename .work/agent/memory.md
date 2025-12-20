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

## Lessons Learned
(To be populated after completing issues)
