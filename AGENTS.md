# AI Agent Guidelines for dot-work

This document provides instructions for AI agents (GitHub Copilot, Claude, GPT, etc.) working on this codebase.
**Read this file before making any changes.**

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

## 🏗️ Project Structure

```
dot-work/
├── src/dot_work/       # Main source code
│   ├── cli.py          # CLI entry point (typer-based)
│   ├── environments.py # Environment configurations
│   ├── installer.py    # Prompt installation logic
│   └── prompts/        # Bundled prompt templates (Jinja2)
├── tests/
│   ├── unit/           # Unit tests (fast, isolated)
│   └── integration/    # Integration tests (marked with @pytest.mark.integration)
└── scripts/
    └── build.py        # Build pipeline - run this before committing
```

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

4. **Use `@dataclass` for data structures**
   ```python
   from dataclasses import dataclass

   @dataclass
   class Task:
       id: str
       title: str
       completed: bool = False
   ```

### Forbidden Patterns

- ❌ Running Python directly — **ALWAYS use `uv run python ...`**, never `python ...`
- ❌ `from src.dot_work import X` — use `from dot_work import X`
- ❌ Business logic in `cli.py` — delegate to service modules
- ❌ Hardcoded secrets, paths, or config values — use environment variables
- ❌ Bare `except:` blocks — always specify exception types
- ❌ `print()` for logging — use `logging` module (except in CLI output)
- ❌ Mutable default arguments — use `field(default_factory=...)`
- ❌ Global mutable state
- ❌ Functions >15 lines (excluding docstrings)
- ❌ Nesting >3 levels deep
- ❌ Classes >200 lines or >10 methods

## 🧪 Testing Requirements

### Unit Tests
- Test each public function
- Cover happy path AND edge cases
- Use `pytest` fixtures for common setup
- Mock external dependencies

### Test Naming
```python
def test_<function_name>_<scenario>_<expected_result>():
    # test_install_for_copilot_creates_prompt_files
    # test_render_prompt_missing_template_raises_error
```

### Running Tests
```bash
uv run python scripts/build.py                    # Full build with tests
uv run python scripts/build.py --integration all  # Include integration tests
uv run pytest tests/unit -v                       # Unit tests only
```

## 🔄 Workflow

### Before Making Changes
1. Run `uv run python scripts/build.py` to verify clean state
2. Understand the existing architecture
3. Check for similar patterns in the codebase

### When Making Changes
1. Keep functions small and focused (SRP)
2. Add type hints immediately
3. Write tests alongside implementation
4. Use dependency injection for testability

### Before Committing
1. Run `uv run python scripts/build.py --fix` to auto-fix formatting
2. Run `uv run python scripts/build.py` to verify all checks pass
3. Ensure no decrease in test coverage
4. Update docstrings if API changed

## 🎯 Design Principles

| Principle | Application |
|-----------|-------------|
| **SRP** | One reason to change per module/function |
| **DRY** | Extract common logic into utilities |
| **KISS** | Simplest solution that works |
| **YAGNI** | Don't build features "just in case" |
| **Dependency Inversion** | Depend on abstractions, not concretions |

## 📦 Adding Dependencies

1. Add to `pyproject.toml` under `[project.dependencies]`
2. Run `uv sync` to install
3. Add type stubs if available (e.g., `types-PyYAML`)
4. Document why the dependency is needed

## 🔧 Jinja2 Templates

This project uses Jinja2 templates for prompt files. When installing prompts:

1. Templates in `src/dot_work/prompts/` contain `{{ variable }}` placeholders
2. The `render_prompt()` function in `installer.py` substitutes environment-specific values
3. Available template variables:
   - `{{ prompt_path }}` - Path to prompt files for the target environment
   - `{{ ai_tool }}` - AI tool key (e.g., `copilot`, `claude`)
   - `{{ ai_tool_name }}` - Human-readable tool name
   - `{{ prompt_extension }}` - File extension for prompts

## 🚫 What NOT to Do

- Don't skip the build script
- Don't ignore type errors (fix them or use `# type: ignore` with comment)
- Don't add untested code
- Don't put logic in the CLI layer
- Don't use `os.path` (use `pathlib`)
- Don't commit with failing tests
- Don't decrease test coverage

## 📝 Commit Messages

Follow conventional commits:
```
feat: add user authentication
fix: handle empty config file
refactor: extract validation logic
test: add edge cases for parser
docs: update API documentation
```

---

**Remember**: Run `uv run python scripts/build.py` before every commit!
