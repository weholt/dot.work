# Agent Instructions for agent-review

This document provides instructions for AI agents (GitHub Copilot, Claude, GPT, etc.) working on this codebase.
**Read this file before making any changes.**

## ⚠️ Mandatory Workflow

**All AI agents working in this repository MUST follow the workflow defined in:**

- [do-work.prompt.md](.github/prompts/do-work.prompt.md)

No code changes are permitted without following this workflow.

---

## 🔒 Quality Gates

Before submitting any code, ensure:

1. **Run the build script**: `uv run python scripts/build.py`
2. **All checks must pass**: formatting, linting, type-checking, tests
3. **Coverage ≥75%**: Add tests for new functionality
4. **No new warnings**: Fix all mypy and ruff warnings

## ⚠️ MANDATORY: Use `uv run` for ALL Python Commands

**NEVER run Python directly. ALWAYS use `uv run`.**

```bash
# ✅ CORRECT - Always use uv run
uv run python scripts/build.py
uv run python -m pytest
uv run mypy src/
uv run ruff check .

# ❌ WRONG - Never run Python directly
python scripts/build.py
python -m pytest
mypy src/
```

This ensures:
- Correct virtual environment is always used
- Dependencies are automatically synced
- Consistent behavior across all environments

---

## 🚀 Before Any Work

1. **Verify `.work/` exists** — If not, run `init work`
2. **Generate baseline** — Run `generate-baseline` before ANY code changes
3. **Check focus.md** — Review Previous/Current/Next state
4. **Check memory.md** — Review relevant context and lessons learned

---

## 🔑 Required Commands

| Command | When to Use |
|---------|-------------|
| `init work` | First time setup — creates `.work/` structure |
| `generate-baseline` | Before any code changes (mandatory) |
| `continue` | Resume work following the optimal iteration loop |
| `focus on <topic>` | Create prioritized issues for a specific topic |
| `status` | Report current focus and issue counts |
| `validate` | Run baseline-relative validation |

---

## 🏗️ Project Structure

```
agent-review/
├── src/agent_review/      # Main source code
│   ├── cli.py             # CLI entry point (THIN - no business logic)
│   ├── config.py          # Configuration management
│   ├── models.py          # Pydantic data models
│   ├── git.py             # Git operations and diff parsing
│   ├── storage.py         # Comment persistence
│   ├── exporter.py        # Agent export functionality
│   ├── server.py          # FastAPI web server
│   ├── templates/         # Jinja2 HTML templates
│   └── static/            # CSS and JavaScript
├── tests/
│   ├── unit/              # Unit tests (fast, isolated)
│   └── integration/       # Integration tests (marked with @pytest.mark.integration)
├── scripts/
│   └── build.py           # Build pipeline - run this before committing
└── .work/                 # Issue tracking (see workflow)
```

---

## 📏 Code Standards

### Mandatory Rules

1. **Type annotations on ALL functions**
   ```python
   def process_item(item: str, count: int = 1) -> list[str]:
   ```

2. **Google-style docstrings on public APIs**
   ```python
   def fetch_data(url: str) -> dict[str, Any]:
       """Fetch data from the specified URL.

       Args:
           url: The endpoint URL to fetch from.

       Returns:
           Parsed JSON response as a dictionary.

       Raises:
           ConnectionError: If the request fails.
       """
   ```

3. **Use `pathlib.Path` for all file operations**
   ```python
   from pathlib import Path
   config_path = Path("config") / "settings.yaml"
   ```

4. **Use Pydantic `BaseModel` for data structures**
   ```python
   from pydantic import BaseModel

   class ReviewComment(BaseModel):
       id: str
       message: str
   ```

### Forbidden Patterns

- ❌ Running Python directly — **ALWAYS use `uv run python ...`**
- ❌ `from src.agent_review import X` — use `from agent_review import X`
- ❌ Business logic in `cli.py` — delegate to service modules
- ❌ Hardcoded secrets, paths, or config values — use environment variables
- ❌ Bare `except:` blocks — always specify exception types
- ❌ `print()` for logging — use `logging` module
- ❌ Mutable default arguments — use `Field(default_factory=...)`
- ❌ Global mutable state
- ❌ Functions >15 lines (excluding docstrings)
- ❌ Nesting >3 levels deep

---

## 📋 Core Principles

1. **Baseline is the quality floor** — nothing may regress
2. **One active issue at a time** — no multitasking
3. **Shortlist has highest priority** — user intent overrides all
4. **All regressions block completion** — fix before moving on
5. **Issues are the only unit of work** — all work is tracked
6. **History is immutable** — append-only record
7. **Learn after validation** — update memory only after success

---

## 🔄 The Iteration Loop

```
BASELINE → SELECT → INVESTIGATE → IMPLEMENT → VALIDATE → COMPLETE → LEARN → NEXT
```

**Critical checkpoints:**
- ⚠️ NO CODE CHANGES until baseline is established
- ⚠️ CREATE ISSUES FIRST when regressions occur, then fix
- ⚠️ UPDATE focus.md immediately when state changes
- ⚠️ VALIDATE before marking any issue complete

---

## 🧪 Testing Requirements

### Unit Tests
- Test each public function
- Cover happy path AND edge cases
- Use `pytest` fixtures for common setup
- Mock external dependencies (git, filesystem)

### Test Naming
```python
def test_<function_name>_<scenario>_<expected_result>():
    # test_parse_unified_diff_empty_returns_no_hunks
    # test_load_comments_filter_by_path_returns_matching
```

### Running Tests
```bash
uv run python scripts/build.py                    # Full build with tests
uv run python scripts/build.py --integration all  # Include integration tests
uv run pytest tests/unit -v                       # Unit tests only
```

---

## ⛔ Anti-Patterns (DO NOT)

- ❌ Make code changes before generating baseline
- ❌ Switch issues mid-work without completing or parking
- ❌ Skip validation before marking complete
- ❌ Fix regressions without creating issues first
- ❌ Modify shortlist.md without explicit user instruction
- ❌ Regenerate baseline to pass failing validation
- ❌ Update memory.md before validation passes

---

## 📁 Directory Structure (.work/)

```
.work/
├── baseline.md               # Quality metrics snapshot
└── agent/
    ├── focus.md              # Current execution state (Previous/Current/Next)
    ├── memory.md             # Persistent cross-session knowledge
    ├── notes/                # Scratchpad, research, working notes
    └── issues/
        ├── shortlist.md      # USER-DIRECTED priorities (highest)
        ├── critical.md       # P0 – blockers, security, data loss
        ├── high.md           # P1 – broken core functionality
        ├── medium.md         # P2 – enhancements, tech debt
        ├── low.md            # P3 – minor improvements
        ├── backlog.md        # Untriaged ideas
        ├── history.md        # Completed issues (append-only)
        └── references/       # Specs, logs, large docs
```

---

## 📚 Full Documentation

For complete workflow details, see:
- [do-work.prompt.md](.github/prompts/do-work.prompt.md) — Full iteration workflow
- [setup-issue-tracker.prompt.md](.github/prompts/setup-issue-tracker.prompt.md) — Setup guide

---

**Remember**: Run `uv run python scripts/build.py` before every commit!
