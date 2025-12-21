# AGENTS.md — AI Agent Operating Guidelines

This document provides instructions for AI agents (GitHub Copilot, Claude, GPT, etc.) working on this codebase.
**Read this file before making any changes.**

---

## 🔒 Quality Gates

Before submitting any code, ensure:

1. **Run the build script**: `uv run python scripts/build.py`
2. **All checks must pass**: formatting, linting, type-checking, tests
3. **Coverage ≥75%**: Add tests for new functionality
4. **No new warnings**: Fix all mypy and ruff warnings

---

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

## 🏗️ Project Structure

```
kgtool-2/
├── src/kgshred/        # Main source code
│   ├── cli.py          # CLI entry point (THIN - no business logic)
│   ├── config.py       # Configuration management
│   └── *.py            # Core modules
├── tests/
│   ├── unit/           # Unit tests (fast, isolated)
│   └── integration/    # Integration tests (marked with @pytest.mark.integration)
├── scripts/
│   └── build.py        # Build pipeline - run this before committing
└── .work/              # Issue tracker (see below)
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
- ❌ `from src.kgshred import X` — use `from kgshred import X`
- ❌ Business logic in `cli.py` — delegate to service modules
- ❌ Hardcoded secrets, paths, or config values — use environment variables
- ❌ Bare `except:` blocks — always specify exception types
- ❌ `print()` for logging — use `logging` module
- ❌ Mutable default arguments — use `field(default_factory=...)`
- ❌ Global mutable state
- ❌ Functions >15 lines (excluding docstrings)
- ❌ Nesting >3 levels deep
- ❌ Classes >200 lines or >10 methods

---

## 🧪 Testing Requirements

### Unit Tests
- Test each public function
- Cover happy path AND edge cases
- Use `pytest` fixtures for common setup
- Mock external dependencies

### Test Naming
```python
def test_<function_name>_<scenario>_<expected_result>():
    # test_parse_config_missing_file_raises_error
    # test_process_items_empty_list_returns_empty
```

### Running Tests
```bash
uv run python scripts/build.py                    # Full build with tests
uv run python scripts/build.py --integration all  # Include integration tests
uv run pytest tests/unit -v                       # Unit tests only
```

---

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

---

## 🎯 Design Principles

| Principle | Application |
|-----------|-------------|
| **SRP** | One reason to change per module/function |
| **DRY** | Extract common logic into utilities |
| **KISS** | Simplest solution that works |
| **YAGNI** | Don't build features "just in case" |
| **Dependency Inversion** | Depend on abstractions, not concretions |

---

## 📦 Adding Dependencies

1. Add to `pyproject.toml` under `[project.dependencies]`
2. Run `uv sync` to install
3. Add type stubs if available (e.g., `types-PyYAML`)
4. Document why the dependency is needed

---

## 🚫 What NOT to Do

- Don't skip the build script
- Don't ignore type errors (fix them or use `# type: ignore` with comment)
- Don't add untested code
- Don't put logic in the CLI layer
- Don't use `os.path` (use `pathlib`)
- Don't commit with failing tests
- Don't decrease test coverage

---

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

## 📋 File-Based Issue Tracker

This repository uses a **file-based, baseline-gated issue tracker** for all AI agent work.

### Trigger Commands

| Command | Action |
|---------|--------|
| `init work` | Initialize `.work/` structure |
| `create issue` | Create issue with generated hash |
| `focus on <topic>` | Create issue(s) in shortlist |
| `add to shortlist X` | Add canonical issue entry |
| `remove from shortlist X` | Remove exact identifier |
| `continue` | Resume work deterministically |
| `status` | Report focus + issue counts |
| `what's next` | Recommend next issue (no state change) |
| `validate` | Run baseline-relative validation |
| `generate-baseline` | Full repo audit → `.work/baseline.md` |
| `housekeeping` | Cleanup (excluding shortlist) |

### Issue ID Format

```
<PREFIX>-<NUMBER>@<HASH>
```

Example: `BUG-003@a9f3c2`

### Prefixes

| Prefix | Meaning |
|--------|---------|
| BUG | Defect |
| FEAT | New feature |
| ENHANCE | Improve existing behavior |
| REFACTOR | Structural/code improvement |
| DOCS | Documentation |
| TEST | Testing |
| SEC | Security |
| PERF | Performance |
| DEBT | Technical debt |
| STRUCT | Architectural issue |
| DUPL | Duplication |

### Issue Tracker Directory Structure

```
.work/
├── agent/
│   ├── focus.md              # Current execution state
│   ├── memory.md             # Persistent cross-session knowledge
│   ├── notes/                # Working notes
│   └── issues/
│       ├── critical.md       # P0
│       ├── high.md           # P1
│       ├── medium.md         # P2
│       ├── low.md            # P3
│       ├── backlog.md        # Untriaged
│       ├── shortlist.md      # User-directed priorities
│       ├── history.md        # Completed (append-only)
│       └── references/       # Supporting documents
```

### Issue Tracker Rules

1. **Baseline is the quality floor** — nothing may regress
2. **One active issue at a time**
3. **User intent overrides agent autonomy**
4. **All regressions block completion**
5. **Validation is comparative, never absolute**
6. **Issues are the only unit of work**
7. **History is immutable**
8. **Shortlist changes require explicit user instruction**

---

## 🔄 Optimal Iteration Workflow

### Workflow Philosophy

1. **Baseline before anything** — No code changes until baseline is established
2. **One issue, complete focus** — No multitasking
3. **Validate before completing** — Every batch of work ends with validation
4. **Fix before moving on** — Regressions block progress, create issues first, then fix
5. **Learn at the end** — Extract lessons to memory/notes after validation passes
6. **Leave breadcrumbs** — Future sessions should resume seamlessly

### Pre-Work Checklist

Before starting any work, verify:

```
□ .work/ structure exists?
  └─ NO → Run `init work`

□ Working in correct branch / clean commit state?
  └─ UNCLEAR → Ask user: "Should I create a new branch or work from current commit?"
  
□ .work/baseline.md exists and is current for THIS iteration?
  └─ NO → Run `generate-baseline` BEFORE ANY CODE CHANGES
  ⚠️  NO CODE CHANGES ARE PERMITTED UNTIL BASELINE IS ESTABLISHED
  
□ focus.md has active work?
  └─ YES → Resume that work (do not switch)
  └─ NO → Ready to select new issue
  
□ memory.md reviewed for relevant context?
```

### The Optimal Iteration Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                    OPTIMAL ITERATION LOOP                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   BASELINE ──▶ SELECT ──▶ INVESTIGATE ──▶ IMPLEMENT              │
│       │                        │              │                  │
│       │                        ▼              ▼                  │
│       │                     NOTES         VALIDATE               │
│       │                                       │                  │
│       │                              ┌────────┴────────┐         │
│       │                            PASS              FAIL        │
│       │                              │                 │         │
│       │                              ▼                 ▼         │
│       │                          COMPLETE    CREATE ISSUES→FIX   │
│       │                              │                 │         │
│       │                              ▼                 │         │
│       │                           LEARN ←──────────────┘         │
│       │                              │                           │
│       │                              ▼                           │
│       └────────────────────────── NEXT                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Phase Details

#### Phase 1: BASELINE (Mandatory First Step)

⚠️ **NO CODE CHANGES ARE PERMITTED UNTIL BASELINE IS COMPLETE**

1. Verify `.work/` structure exists (run `init work` if not)
2. Confirm branch/commit state with user if unclear
3. Generate fresh baseline for this iteration
4. Read `focus.md` for context (previous/current/next)
5. Scan `memory.md` for relevant lessons

**Output:** `baseline.md` with full file-level detail

#### Phase 2: SELECT

**Selection Order (strict):**
1. First item in `shortlist.md` (USER PRIORITY - ALWAYS HIGHEST)
2. Resume `focus.md` current issue if exists and shortlist is empty
3. Start `focus.md` next issue if current is empty
4. Any item in `critical.md` (P0)
5. Any item in `high.md` (P1)
6. Any item in `medium.md` (P2)
7. Any item in `low.md` (P3)

**Actions:**
1. Update `focus.md` with: Previous, Current, Next
2. Update issue status in source file

#### Phase 3: INVESTIGATE

1. Create notes file: `notes/<issue-id>-investigation.md`
2. Read all affected files mentioned in issue
3. Reproduce the problem if applicable
4. Document findings in notes
5. Determine implementation approach

**Investigation Checklist:**
- [ ] Can I reproduce the issue?
- [ ] Do I understand the root cause?
- [ ] Do I know which files need changes?
- [ ] Are there edge cases to consider?
- [ ] Does `memory.md` have relevant lessons?

#### Phase 4: IMPLEMENT

1. Update `focus.md` phase to "Implementation"
2. Make code changes as planned
3. Add/update tests as needed
4. Update documentation if affected
5. Check baseline for existing warnings in files you're modifying

**Implementation Principles:**
- Small, focused changes
- Tests accompany code changes
- Follow patterns from `memory.md`

#### Phase 5: VALIDATE

1. Run full validation suite: `uv run python scripts/build.py`
2. Compare all metrics to `baseline.md` at FILE LEVEL
3. Document results with specific file references

**Validation Checks:**
- [ ] Build passes
- [ ] All tests pass
- [ ] Coverage ≥ baseline
- [ ] No new lint errors (compare by file)
- [ ] No new type errors (compare by file)
- [ ] Previously clean files remain clean

#### Phase 6: COMPLETE (on validation pass)

1. Update issue status to "completed"
2. Move issue block to `history.md` (append)
3. Remove issue from source file
4. Update `focus.md`: Current → Previous, Next → Current
5. Archive notes to `references/` (if valuable)
6. Update `memory.md` with learnings

#### Phase 7: FIX (on validation failure)

⚠️ **CREATE ISSUES FIRST, THEN FIX**

1. Analyze validation failures at FILE LEVEL
2. **FIRST:** Create issues for ALL regressions found
3. **THEN:** Fix each regression issue
4. Re-run validation after fixes
5. Repeat until all regressions resolved

#### Phase 8: LEARN (Memory & Notes)

**Happens ONLY after validation succeeds:**

1. What problem was solved? How?
2. What patterns should be documented?
3. Update `memory.md` with dated entries
4. Archive useful notes, delete temporary ones

### Focus State Management

`focus.md` MUST always contain three sections:

```markdown
## Previous
The last completed issue (provides context)

## Current  
The issue actively being worked on

## Next
The anticipated next issue
```

### Common Flows

#### Flow: User Says "continue"
1. Check baseline current? → NO: Generate baseline first
2. Check `shortlist.md` FIRST (user priority always wins)
3. If shortlist empty, read `focus.md` (Previous/Current/Next)
4. If Current has active issue → Resume it
5. If Current empty, Next exists → Promote Next to Current
6. Update `focus.md` with all three values

#### Flow: Completing an Issue
1. Run validation
2. All pass → Mark completed, move to `history.md`
3. Update `focus.md`: Current → Previous, Next → Current
4. LEARN: Update `memory.md`
5. Report completion

#### Flow: Validation Fails
1. Analyze failures at FILE LEVEL
2. **CREATE ISSUES FIRST** for all regressions
3. Update `focus.md` status to "fixing-regressions"
4. Fix each regression issue
5. Re-validate until passing

### Anti-Patterns to Avoid

| Anti-Pattern | Correct Behavior |
|--------------|------------------|
| Making code changes before baseline | Generate baseline FIRST |
| Switching issues mid-work | Complete or park current issue |
| Skipping validation | Always validate before completion |
| Not updating `focus.md` | Update all three sections immediately |
| Regenerating baseline to pass | Fix regressions instead |
| Fixing regressions without issues first | CREATE ISSUES FIRST, then fix |
| Updating memory before validation | LEARN phase comes after validation |
| Modifying shortlist autonomously | Only on explicit user instruction |

### Full Specification

See [.github/prompts/do-work.prompt.md](.github/prompts/do-work.prompt.md) for the complete workflow specification.

---

**Remember**: Run `uv run python scripts/build.py` before every commit!
