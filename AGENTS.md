# AI Agent Guidelines for dot-work

**MANDATORY: Use `uv run` for ALL Python commands** - NEVER run Python directly.

## Commands
```bash
uv run python scripts/build.py              # Full build/format/lint/test
uv run python scripts/build.py --fix        # Auto-fix formatting
uv run pytest tests/unit/test_name.py -v    # Single test
uv run python -m pytest tests/unit -v       # Unit tests only
uv run mypy src/ && uv run ruff check .     # Type check + lint
```

## Code Standards
- Type hints on ALL functions, Google docstrings for public APIs
- Use `pathlib.Path`, `@dataclass` for structures, `from dot_work import X` (not src.)
- No business logic in cli.py, use `logging` not `print()`, no bare except:
- Functions <15 lines, nesting <3 levels, classes <200 lines

## Testing
- Test naming: `test_function_scenario_expected_result()`
- Coverage ≥75%, unit tests for each public function
- Mock external deps, use pytest fixtures

## Workflow
1. Run `uv run python scripts/build.py` before changes
2. Write tests alongside implementation  
3. Run `uv run python scripts/build.py --fix` before commit
4. NEVER commit with failing tests or decreased coverage

## Forbidden
- Running Python directly, hardcoded secrets, mutable defaults, global state
