# Shortlist (User-Directed Priority)

This file represents **explicit user intent**. Agent may only modify when explicitly instructed.

---

## MIGRATE-064@8f2a1b

---
id: "MIGRATE-064@8f2a1b"
title: "Create git history module structure"
description: "Set up the module structure for git history analysis under src/dot_work/git/"
created: 2024-12-21
section: "src/dot_work/git"
tags: [migration, git-analysis, module-structure]
type: migration
priority: medium
status: proposed
source: "incoming/crampus/git-analysis"
references:
  - incoming/crampus/git-analysis/src/git_analysis/
---

### Problem

Migrate git-analysis functionality as `dot-work git history`. Need to create the module structure first.

### Source Files
```
incoming/crampus/git-analysis/src/git_analysis/
├── __init__.py
├── cli.py
├── models.py
├── utils.py
└── services/
    ├── __init__.py
    ├── cache.py
    ├── complexity.py
    ├── file_analyzer.py
    ├── git_service.py
    ├── llm_summarizer.py
    └── tag_generator.py
```

### Target Structure
```
src/dot_work/git/
├── __init__.py
├── models.py
├── utils.py
└── services/
    ├── __init__.py
    ├── cache.py
    ├── complexity.py
    ├── file_analyzer.py
    ├── git_service.py
    ├── llm_summarizer.py
    └── tag_generator.py
```

### Tasks
1. Create `src/dot_work/git/` directory
2. Copy models.py with import updates (`from dot_work.git.models import ...`)
3. Copy utils.py with import updates
4. Create services/ subdirectory
5. Copy all service files with import updates
6. Omit `mcp/` directory (not needed)

### Acceptance Criteria
- [ ] Module structure created
- [ ] All source files copied
- [ ] Imports updated to `dot_work.git.*`
- [ ] No MCP dependencies

### Notes
First step of git history migration. MCP server omitted per user decision. LLM integration preserved.

**⚠️ MINIMAL ALTERATION PRINCIPLE:** Copy source files verbatim. Only change:
1. Import paths (relative → `dot_work.git.*`)
2. Nothing else in the source logic

Do NOT refactor, rename variables, restructure classes, or "improve" the code. The goal is to preserve original functionality exactly.

---

## MIGRATE-065@9c3b2d

---
id: "MIGRATE-065@9c3b2d"
title: "Update git history imports and dependencies"
description: "Update all imports in git module and add required dependencies to pyproject.toml"
created: 2024-12-21
section: "src/dot_work/git"
tags: [migration, git-analysis, imports, dependencies]
type: migration
priority: medium
status: proposed
source: "incoming/crampus/git-analysis"
references:
  - incoming/crampus/git-analysis/pyproject.toml
  - pyproject.toml
---

### Problem

After copying files, need to update all imports and add dependencies.

### Import Updates

All files in `src/dot_work/git/`:
```python
# OLD
from .models import AnalysisConfig, ChangeAnalysis, ComparisonResult
from .services import GitAnalysisService

# NEW
from dot_work.git.models import AnalysisConfig, ChangeAnalysis, ComparisonResult
from dot_work.git.services import GitAnalysisService
```

### Dependencies to Add

**Required (pyproject.toml):**
```toml
"gitpython>=3.1.0",
```

**Optional (LLM support):**
```toml
[project.optional-dependencies]
llm = [
    "openai>=1.0.0",
    "anthropic>=0.3.0",
]
```

### Tasks
1. Update imports in all git module files
2. Add `gitpython>=3.1.0` to main dependencies
3. Add optional `llm` extras group
4. Run `uv sync` to install

### Acceptance Criteria
- [ ] All imports use `dot_work.git.*` paths
- [ ] gitpython added to dependencies
- [ ] Optional llm extras defined
- [ ] `uv sync` succeeds

### Notes
Depends on: MIGRATE-064.

**⚠️ MINIMAL ALTERATION PRINCIPLE:** Import changes ONLY. Do not:
- Rename functions/classes/variables
- Change function signatures
- Restructure module organization beyond what's specified
- "Clean up" or "improve" existing code
- Add type hints that weren't there
- Change docstrings

Preserve the original code exactly as-is except for import paths.

---

## MIGRATE-066@a4d3e5

---
id: "MIGRATE-066@a4d3e5"
title: "Register git history CLI commands"
description: "Create git command group with history subcommand containing all analysis commands"
created: 2024-12-21
section: "src/dot_work/cli.py"
tags: [migration, git-analysis, cli, typer]
type: migration
priority: medium
status: proposed
source: "incoming/crampus/git-analysis"
references:
  - incoming/crampus/git-analysis/src/git_analysis/cli.py
  - src/dot_work/cli.py
---

### Problem

Need to register git-analysis commands under `dot-work git history <subcommand>`.

### CLI Structure

```
dot-work git history compare <from_ref> <to_ref>
dot-work git history analyze <commit_hash>
dot-work git history diff-commits <commit_a> <commit_b>
dot-work git history contributors <from_ref> <to_ref>
dot-work git history complexity <from_ref> <to_ref>
dot-work git history releases
```

### Implementation

**src/dot_work/git/cli.py** (new file):
```python
"""CLI commands for git history analysis."""

import typer

from dot_work.git.models import AnalysisConfig
from dot_work.git.services import GitAnalysisService

history_app = typer.Typer(
    name="history",
    help="Analyze git history between refs",
    no_args_is_help=True,
)

@history_app.command()
def compare(...): ...

@history_app.command()
def analyze(...): ...

# ... other commands
```

**src/dot_work/cli.py** (update):
```python
from dot_work.git.cli import history_app

git_app = typer.Typer(name="git", help="Git analysis tools")
git_app.add_typer(history_app, name="history")
app.add_typer(git_app, name="git")
```

### Tasks
1. Create `src/dot_work/git/cli.py` with history_app
2. Copy command implementations from source cli.py
3. Update main cli.py to register git command group
4. Add history subgroup under git

### Acceptance Criteria
- [ ] `dot-work git --help` shows history subcommand
- [ ] `dot-work git history --help` shows 6 commands
- [ ] Commands delegate to GitAnalysisService

### Notes
Depends on: MIGRATE-064, MIGRATE-065.

**⚠️ MINIMAL ALTERATION PRINCIPLE:** The CLI commands must be copied from the source `cli.py` with minimal changes:
- Keep all original command names, arguments, options, and help text
- Keep all display helper functions (`_display_table_results`, etc.) exactly as-is
- Only change: (1) imports, (2) Typer app registration to nest under `history_app`
- Do NOT rename `compare` to `compare-refs`, do NOT change `--verbose` to `-v` only, etc.

The CLI should behave identically to the original, just under `dot-work git history` prefix.

---

## MIGRATE-067@b5e4f6

---
id: "MIGRATE-067@b5e4f6"
title: "Add tests for git history module"
description: "Create unit tests for git history models, services, and CLI commands"
created: 2024-12-21
section: "tests/unit"
tags: [migration, git-analysis, testing]
type: migration
priority: medium
status: proposed
source: "incoming/crampus/git-analysis"
references:
  - incoming/crampus/git-analysis/tests/
  - tests/unit/
---

### Problem

Need comprehensive tests for the migrated git history functionality.

### Test Files

```
tests/unit/git/
├── __init__.py
├── test_models.py
├── test_complexity.py
├── test_file_analyzer.py
├── test_tag_generator.py
└── test_cli.py
```

### Test Coverage

**test_models.py:**
- ChangeType enum values
- FileCategory classification
- AnalysisConfig defaults
- ComparisonResult structure

**test_complexity.py:**
- Complexity score calculation
- Threshold comparisons
- Risk level assignment

**test_file_analyzer.py:**
- File category detection (code, tests, config, docs)
- Binary file detection
- Path parsing

**test_cli.py:**
- Command invocation (mocked GitAnalysisService)
- Output format handling (table, json, yaml)
- Error handling

### Tasks
1. Create tests/unit/git/ directory
2. Copy and adapt tests from source
3. Add new tests for CLI commands
4. Mock git repository for unit tests

### Acceptance Criteria
- [ ] All test files created
- [ ] Tests pass with `uv run pytest tests/unit/git/`
- [ ] Coverage >=75% for git module
- [ ] No external git repo required for unit tests

### Notes
Depends on: MIGRATE-064, MIGRATE-065, MIGRATE-066.

**⚠️ MINIMAL ALTERATION PRINCIPLE:** Copy existing tests from source first, then adapt:
- Keep original test structure and assertions
- Only update imports to `dot_work.git.*`
- Add new tests for CLI wiring, but don't rewrite existing test logic
- If source tests pass, migrated tests should pass with same assertions

---

## MIGRATE-068@c6f5a7

---
id: "MIGRATE-068@c6f5a7"
title: "Add integration tests for git history"
description: "Create integration tests that use a real git repository for end-to-end validation"
created: 2024-12-21
section: "tests/integration"
tags: [migration, git-analysis, testing, integration]
type: migration
priority: medium
status: proposed
source: "incoming/crampus/git-analysis"
references:
  - tests/integration/
---

### Problem

Need integration tests that validate git history commands against a real repository.

### Test File

**tests/integration/test_git_history.py:**
```python
"""Integration tests for git history commands."""

import pytest
from typer.testing import CliRunner

from dot_work.cli import app

runner = CliRunner()

@pytest.mark.integration
class TestGitHistoryIntegration:
    """Integration tests using the dot-work repo itself."""

    def test_compare_refs(self):
        """Test comparing HEAD~5 to HEAD."""
        result = runner.invoke(app, ["git", "history", "compare", "HEAD~5", "HEAD"])
        assert result.exit_code == 0
        assert "Commits:" in result.output

    def test_analyze_commit(self):
        """Test analyzing HEAD commit."""
        result = runner.invoke(app, ["git", "history", "analyze", "HEAD"])
        assert result.exit_code == 0

    def test_complexity_analysis(self):
        """Test complexity analysis."""
        result = runner.invoke(app, ["git", "history", "complexity", "HEAD~10", "HEAD"])
        assert result.exit_code == 0
```

### Tasks
1. Create tests/integration/test_git_history.py
2. Use dot-work repo itself for testing
3. Mark all tests with `@pytest.mark.integration`
4. Test each of the 6 subcommands

### Acceptance Criteria
- [ ] Integration tests created
- [ ] Tests use real git history
- [ ] All 6 commands have integration tests
- [ ] Tests pass with `uv run python scripts/build.py --integration all`

### Notes
Depends on: MIGRATE-067. Uses dot-work's own git history for testing.

**⚠️ MINIMAL ALTERATION PRINCIPLE:** Integration tests validate that the migrated code behaves identically to the original. If any behavior differs, investigate whether the migration introduced unintended changes.

---

## MIGRATE-069@d7a6b8

---
id: "MIGRATE-069@d7a6b8"
title: "Verify git history migration"
description: "Final verification that git history commands work correctly end-to-end"
created: 2024-12-21
section: "src/dot_work/git"
tags: [migration, git-analysis, verification]
type: migration
priority: medium
status: proposed
source: "incoming/crampus/git-analysis"
references:
  - src/dot_work/git/
---

### Problem

Final verification that the git history migration is complete and functional.

### Verification Steps

**Build Pipeline:**
```bash
uv run python scripts/build.py
```

**CLI Verification:**
```bash
# Compare branches/refs
dot-work git history compare HEAD~10 HEAD

# Analyze single commit
dot-work git history analyze HEAD

# Diff two commits
dot-work git history diff-commits HEAD~2 HEAD~1

# Show contributors
dot-work git history contributors HEAD~20 HEAD

# Complexity analysis
dot-work git history complexity HEAD~15 HEAD --threshold 30

# Recent releases (if tags exist)
dot-work git history releases --count 5

# JSON output
dot-work git history compare HEAD~5 HEAD --format json

# With LLM (if configured)
dot-work git history compare HEAD~5 HEAD --llm --llm-provider openai
```

### Acceptance Criteria
- [ ] Build passes
- [ ] All 6 subcommands work
- [ ] Output formats (table, json, yaml) work
- [ ] Complexity scoring produces valid scores
- [ ] LLM flag accepted (may fail without API key)
- [ ] Help text accurate

### Notes
Final verification. Depends on: MIGRATE-064 through MIGRATE-068.

**⚠️ MINIMAL ALTERATION PRINCIPLE:** Verification should confirm:
1. Output format matches original `git-analysis` tool exactly
2. Complexity scores calculated identically
3. All CLI flags and options work as documented in original README
4. No functionality was lost or changed during migration

If any behavior differs from the original, it's a bug in the migration, not an "improvement."

---
