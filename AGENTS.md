# AI Agent Guidelines for dot-work

**MANDATORY: Use `uv run` for ALL Python commands** - NEVER run Python directly.
**MANDATORY: Never use rm command without explicit user confirmation**
## Issue Tracker Workflow

This project uses a file-based issue tracker in `.work/`.

**Key rules:**
- All work must be tracked as issues in `.work/agent/issues/`
- Only one active issue at a time (see `.work/agent/focus.md`)
- Do not change `shortlist.md` unless explicitly instructed by the user
- All completed issues must be appended to `history.md` (append-only)
- Never regress the baseline in `.work/baseline.md`

**Directory structure:**
```
.work/
	baseline.md
	agent/
		focus.md
		memory.md
		notes/
		issues/
			shortlist.md
			critical.md
			high.md
			medium.md
			low.md
			backlog.md
			history.md
			references/
```

**Key commands:**
- `init work` – Initialize the issue tracker
- `generate-baseline` – Generate `.work/baseline.md` before any code changes
- `continue` – Resume work on the current issue
- `focus on <topic>` – Create prioritized issues for a topic
- `status` – Show current focus and issue counts

For full workflow details, see `.github/prompts/setup-issue-tracker.prompt.md` and `.github/prompts/do-work.prompt.md`.

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
