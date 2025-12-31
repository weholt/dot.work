# Medium Priority Issues (P2)

Enhancements, technical debt, code quality improvements.

---

---
id: "PERF-014@9c7e2b"
title: "Repeated regex compilation in ComplexityCalculator._get_pattern_weight()"
description: "File complexity patterns recompiled on every file categorization"
created: 2025-12-31
section: "git"
tags: [performance, regex, compilation]
type: performance
priority: medium
status: proposed
references:
  - src/dot_work/git/services/complexity.py
---

### Problem
In `complexity.py:138-143`, `_get_pattern_weight()` uses `re.search()` on patterns that are compiled on every call. The `file_complexity_patterns` list has ~15 regex patterns.

```python
def _get_pattern_weight(self, file_path: str) -> float:
    for pattern, weight in self.weights["file_complexity_patterns"]:
        if re.search(pattern, file_path, re.IGNORECASE):  # ← Compiles pattern every time
            return weight
    return 1.0
```

This is called for every file in every commit during complexity analysis.

### Affected Files
- `src/dot_work/git/services/complexity.py` (lines 47-58, 138-143)

### Impact
For analyzing 1000 file changes:
- Current: 1000 files × ~15 patterns = 15,000 regex compilations
- Optimized: 15 regex compilations once at initialization

### Proposed Solution
Pre-compile patterns in `__init__`:

```python
def __init__(self):
    # ... existing code ...

    # Pre-compile file complexity patterns
    self._compiled_complexity_patterns = [
        (re.compile(pattern, re.IGNORECASE), weight)
        for pattern, weight in self.weights["file_complexity_patterns"]
    ]

def _get_pattern_weight(self, file_path: str) -> float:
    for pattern, weight in self._compiled_complexity_patterns:
        if pattern.search(file_path):
            return weight
    return 1.0
```

### Acceptance Criteria
- [ ] File complexity patterns pre-compiled at initialization
- [ ] `_get_pattern_weight()` uses compiled patterns
- [ ] Existing tests pass
- [ ] No regression in complexity calculations

---

---
id: "PERF-015@2d8e5a"
title: "Inefficient string concatenation in risk factor detection"
description: "Any/any pattern in risk_factors creates intermediate lists"
created: 2025-12-31
section: "git"
tags: [performance, algorithm, complexity]
type: performance
priority: medium
status: proposed
references:
  - src/dot_work/git/services/complexity.py
---

### Problem
In `complexity.py:358-376`, the risk factor detection uses nested `any()` calls that create generator expressions and intermediate lists:

```python
for file_change in commit.files_changed:
    if any(
        pattern in file_change.path.lower()
        for pattern in [
            "migration", "schema", "database", "auth", "security",
            "permission", "role", "cert", "key", "secret"
        ]
    ):
        risk_factors.append(f"High-risk file modified: {file_change.path}")
```

The pattern list is created on every iteration, and `file_change.path.lower()` is called repeatedly.

### Affected Files
- `src/dot_work/git/services/complexity.py` (lines 358-376)

### Impact
- For F files and P patterns: F × P string comparisons
- Pattern list created F times instead of once
- `path.lower()` called P times per file instead of once

### Proposed Solution
Move pattern list to class constant and cache lowercased path:

```python
class ComplexityCalculator:
    _RISKY_PATH_PATTERNS = [
        "migration", "schema", "database", "auth", "security",
        "permission", "role", "cert", "key", "secret"
    ]

def identify_risk_factors(self, commit: ChangeAnalysis) -> list[str]:
    # ... existing code ...

    # Check for risky file patterns
    for file_change in commit.files_changed:
        path_lower = file_change.path.lower()
        if any(pattern in path_lower for pattern in self._RISKY_PATH_PATTERNS):
            risk_factors.append(f"High-risk file modified: {file_change.path}")
```

### Acceptance Criteria
- [ ] Risky patterns defined as class constant
- [ ] `path.lower()` called once per file
- [ ] Existing tests pass
- [ ] No functional regression

---

---
id: "PERF-016@4b9f7c"
title: "Potential memory leak in SQLAlchemy adapter without explicit disposal"
description: "UnitOfWork creates engine but lacks explicit cleanup method"
created: 2025-12-31
section: "database"
tags: [performance, memory, database]
type: performance
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/adapters/sqlite.py
---

### Problem
In `sqlite.py`, the `UnitOfWork` creates a SQLAlchemy engine but doesn't provide explicit disposal. While SQLAlchemy has connection pooling, long-running processes may accumulate connections.

```python
class UnitOfWork(SqlAlchemyUnitOfWork):
    def __init__(self, db_path: str) -> None:
        self._engine = create_engine(  # ← Engine created but never explicitly disposed
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
        self.session_factory = sessionmaker(bind=self._engine)
```

### Affected Files
- `src/dot_work/db_issues/adapters/sqlite.py` (entire class)

### Impact
- In long-running CLI sessions, connections may accumulate
- No explicit cleanup mechanism for resource disposal
- Potential file handle leaks on SQLite

### Proposed Solution
Add explicit disposal method and context manager support:

```python
class UnitOfWork(SqlAlchemyUnitOfWork):
    def __init__(self, db_path: str) -> None:
        # ... existing code ...

    def dispose(self) -> None:
        """Dispose of database engine and release resources."""
        if self._engine:
            self._engine.dispose()
            self._engine = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dispose()
```

### Acceptance Criteria
- [ ] `dispose()` method added
- [ ] Context manager support implemented
- [ ] CLI commands use context manager for long operations
- [ ] Existing tests pass

---

---
id: "CR-028@a4b6c8"
title: "Display functions in git/cli.py should be extracted to formatters module"
description: "260 lines of _display_* functions embedded in CLI module"
created: 2024-12-27
section: "git"
tags: [refactor, separation-of-concerns]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/git/cli.py
---

### Problem
Private display functions (`_display_table_results`, `_display_commit_analysis`, etc.) in `cli.py:269-527` total ~260 lines embedded in the CLI module. These should be in a separate `display.py` or `formatters.py` module to separate concerns.

### Affected Files
- `src/dot_work/git/cli.py` (lines 269-527)

### Importance
Separation of concerns improves testability and maintainability.

### Proposed Solution
1. Create `git/formatters.py` or `git/display.py`
2. Move all `_display_*` functions
3. Update imports in cli.py

### Acceptance Criteria
- [ ] Display functions extracted
- [ ] CLI module focused on command handling
- [ ] Tests continue to pass

---

---
id: "CR-029@b5c7d9"
title: "CacheManager class in git module is never used"
description: "Dead code that creates unnecessary abstraction"
created: 2024-12-27
section: "git"
tags: [dead-code, cleanup]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/git/services/cache.py
---

### Problem
`CacheManager` class in `cache.py:304-408` is never instantiated in the codebase. `GitAnalysisService` uses `AnalysisCache` directly.

### Affected Files
- `src/dot_work/git/services/cache.py`

### Importance
Dead code increases maintenance burden.

### Proposed Solution
Delete the `CacheManager` class. If multi-cache becomes needed, implement it then.

### Acceptance Criteria
- [ ] CacheManager class deleted
- [ ] No regressions
- [ ] Tests pass

---

---
id: "CR-030@c6d8e0"
title: "TagGenerator is over-engineered at 695 lines"
description: "Elaborate emoji mappings and priority systems for simple tag generation"
created: 2024-12-27
section: "git"
tags: [refactor, simplification]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/git/services/tag_generator.py
---

### Problem
`TagGenerator` (695 lines) has elaborate emoji-to-tag mappings, redundancy filtering, and priority systems. Consider if simpler keyword matching (50-100 lines) would suffice for commit tagging.

### Affected Files
- `src/dot_work/git/services/tag_generator.py`

### Importance
Complexity proportional to value delivered. Simpler code is easier to maintain.

### Proposed Solution
1. Evaluate if elaborate logic is actually needed
2. Consider simplifying to basic keyword matching
3. Remove unused sophistication

### Acceptance Criteria
- [ ] Complexity evaluated against requirements
- [ ] Unnecessary complexity removed
- [ ] Tag quality maintained or improved

---

---
id: "CR-031@d7e9f1"
title: "Dead code in utils.py - extract_emoji_indicators and calculate_commit_velocity"
description: "~100 lines of never-called functions"
created: 2024-12-27
section: "git"
tags: [dead-code, cleanup]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/git/utils.py
---

### Problem
In `utils.py`:
- `extract_emoji_indicators()` (lines 333-382) - never called
- `calculate_commit_velocity()` (lines 418-477) - never called
- `identify_commit_patterns()` - never called

~100 lines of dead code.

### Affected Files
- `src/dot_work/git/utils.py`

### Importance
Dead code increases maintenance burden and confusion.

### Proposed Solution
Delete unused functions.

### Acceptance Criteria
- [ ] Dead functions deleted
- [ ] No regressions
- [ ] Tests pass

---

---
id: "CR-032@e8f0a2"
title: "Unused type aliases in git/models.py"
description: "CommitHash, BranchName, TagName, FilePath defined but never used"
created: 2024-12-27
section: "git"
tags: [dead-code, cleanup]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/git/models.py
---

### Problem
Type aliases `CommitHash`, `BranchName`, `TagName`, `FilePath` (lines 240-244) are defined but never used anywhere in the codebase.

### Affected Files
- `src/dot_work/git/models.py`

### Importance
Unused definitions suggest incomplete implementation or abandoned design.

### Proposed Solution
1. Delete unused type aliases, or
2. Use them throughout the codebase for type safety

### Acceptance Criteria
- [ ] Dead code removed or utilized
- [ ] Consistent use of type aliases if kept

---

---
id: "CR-033@f9a1b3"
title: "Unused harness_app Typer instance in harness/__init__.py"
description: "Competing CLI entry points create confusion"
created: 2024-12-27
section: "harness"
tags: [dead-code, cleanup]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/harness/__init__.py
  - src/dot_work/harness/cli.py
---

### Problem
Two competing Typer app instances exist: `harness_app` in `__init__.py` and `app` in `cli.py`. Only `cli.py:app` is actually used (imported in `dot_work/cli.py`).

### Affected Files
- `src/dot_work/harness/__init__.py`
- `src/dot_work/harness/cli.py`

### Importance
Confusing about which is the canonical entry point.

### Proposed Solution
Delete `harness_app` from `__init__.py` or consolidate with `cli.py:app`.

### Acceptance Criteria
- [ ] Single CLI entry point
- [ ] No dead code

---

---
id: "CR-034@a0b2c4"
title: "Unused imports in harness/client.py"
description: "NotRequired and TypedDict imported but never used"
created: 2024-12-27
section: "harness"
tags: [dead-code, cleanup]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/harness/client.py
---

### Problem
`client.py:8` imports `NotRequired` and `TypedDict` but neither is used anywhere in the file.

### Affected Files
- `src/dot_work/harness/client.py`

### Importance
Dead imports indicate incomplete implementation or abandoned design.

### Proposed Solution
Delete unused imports.

### Acceptance Criteria
- [ ] Unused imports removed

---

---
id: "CR-035@b1c3d5"
title: "File read race condition in harness iteration loop"
description: "File read twice without locking could produce incorrect comparison"
created: 2024-12-27
section: "harness"
tags: [concurrency, reliability]
type: bug
priority: medium
status: proposed
references:
  - src/dot_work/harness/client.py
---

### Problem
In `client.py:165-168`, the task file is read twice in quick succession: once before iteration (`load_tasks`) and once after. If another process modifies the file between reads, comparison logic could produce incorrect results. No file locking or atomic read mechanism exists.

### Affected Files
- `src/dot_work/harness/client.py`

### Importance
Race condition could cause harness to exit prematurely or continue incorrectly.

### Proposed Solution
1. Add file locking, or
2. Use atomic operations, or
3. Document single-user assumption

### Acceptance Criteria
- [ ] Race condition addressed or documented
- [ ] Reliable comparison logic

---

---
id: "CR-036@c2d4e6"
title: "FTS5 query validation regex is scattered and fragile"
description: "Query validation patterns spread across search_fts.py"
created: 2024-12-27
section: "knowledge_graph"
tags: [maintainability, refactor]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/knowledge_graph/search_fts.py
---

### Problem
Query validation regex patterns (`_SIMPLE_QUERY_PATTERN`, `_FTS5_OPERATOR_PATTERN`, `_DANGEROUS_PATTERNS` in lines 20-24 and 173-231) are scattered across `search_fts.py`. If FTS5 syntax changes or new operators are added, multiple regex patterns must be updated.

### Affected Files
- `src/dot_work/knowledge_graph/search_fts.py`

### Importance
Fragile maintenance. Changes require updating multiple patterns.

### Proposed Solution
Centralize query validation logic in one place.

### Acceptance Criteria
- [ ] Validation logic centralized
- [ ] Easier to update for FTS5 changes

---

---
id: "CR-037@d3e5f7"
title: "Unused validate_path function in knowledge_graph/config.py"
description: "Function defined but never called in production"
created: 2024-12-27
section: "knowledge_graph"
tags: [dead-code, cleanup]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/knowledge_graph/config.py
---

### Problem
`validate_path()` function (lines 54-78) is defined but never called from production code. It validates that paths have file extensions, but `get_db_path()` and `ensure_db_directory()` don't use it.

### Affected Files
- `src/dot_work/knowledge_graph/config.py`

### Importance
Dead code increases maintenance burden.

### Proposed Solution
Either use it or delete it.

### Acceptance Criteria
- [ ] Function used or deleted

---

---
id: "CR-038@e4f6a8"
title: "Unreachable fallback code in prompts/canonical.py"
description: "Default filename generation cannot be reached due to validation"
created: 2024-12-27
section: "prompts"
tags: [dead-code, clarity]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/prompts/canonical.py
---

### Problem
In `canonical.py:348-370`, `generate_environment_prompt` has a fallback path (lines 369-370) that generates a default filename when neither `filename` nor `filename_suffix` is set. However, `EnvironmentConfig.__post_init__` (lines 63-65) already enforces that one must be provided. The fallback is unreachable dead code.

### Affected Files
- `src/dot_work/prompts/canonical.py`

### Importance
Dead code creates confusion about actual contract.

### Proposed Solution
Delete unreachable fallback or relax validation if fallback is intended.

### Acceptance Criteria
- [ ] Dead code removed or validation relaxed

---

---
id: "CR-039@f5a7b9"
title: "Inconsistent filename generation between canonical.py and wizard.py"
description: "Different regex patterns for title-to-filename transformation"
created: 2024-12-27
section: "prompts"
tags: [consistency, bug-risk]
type: bug
priority: medium
status: proposed
references:
  - src/dot_work/prompts/canonical.py
  - src/dot_work/prompts/wizard.py
---

### Problem
Title-to-filename transformation in `canonical.py:366` uses a different regex pattern than `wizard.py:319-321`. This inconsistency makes reasoning about filename generation difficult and could produce different results.

### Affected Files
- `src/dot_work/prompts/canonical.py`
- `src/dot_work/prompts/wizard.py`

### Importance
Inconsistent behavior confuses users and developers.

### Proposed Solution
1. Extract shared filename generation function
2. Use consistently in both modules

### Acceptance Criteria
- [ ] Single source of truth for filename generation
- [ ] Consistent behavior

---

---
id: "CR-040@a6b8c0"
title: "Late import in wizard.py creates circular dependency risk"
description: "Import of get_prompts_dir inside method body"
created: 2024-12-27
section: "prompts"
tags: [architecture, imports]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/prompts/wizard.py
---

### Problem
In `wizard.py:344-346`, `get_prompts_dir` is imported from `dot_work.installer` inside `_create_prompt_file`. This creates circular dependency risk and makes the dependency graph harder to understand.

### Affected Files
- `src/dot_work/prompts/wizard.py`

### Importance
Circular dependencies cause hard-to-debug import errors.

### Proposed Solution
1. Move import to module level, or
2. Inject the dependency, or
3. Restructure to avoid circular imports

### Acceptance Criteria
- [ ] No late imports for core dependencies
- [ ] Import graph clear

---

---
id: "CR-041@b7c9d1"
title: "Dead code logic in version/config.py"
description: "Conditional that sets same value in both branches"
created: 2024-12-27
section: "version"
tags: [dead-code, cleanup]
type: bug
priority: medium
status: proposed
references:
  - src/dot_work/version/config.py
---

### Problem
In `config.py:48-54`, lines 50-53 check if `.work` exists, but both branches set `work_dir` to the same value (`Path.cwd() / ".work"`). The conditional serves no purpose.

### Affected Files
- `src/dot_work/version/config.py` (lines 48-54)

### Importance
Dead code indicates likely bug or incomplete implementation.

### Proposed Solution
1. Remove dead conditional, or
2. Fix the intended behavior

### Acceptance Criteria
- [ ] Dead code removed or fixed

---

---
id: "CR-042@c8d0e2"
title: "validate() mutates state in version/config.py"
description: "Validation method has side effect of converting strings to Paths"
created: 2024-12-27
section: "version"
tags: [side-effects, naming]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/version/config.py
---

### Problem
In `config.py:105-115`, `validate()` mutates `self.version_file` and `self.changelog_file` by converting strings to Paths. This side effect in a validation method violates the principle of least surprise.

### Affected Files
- `src/dot_work/version/config.py` (lines 105-115)

### Importance
Unexpected mutations make code harder to reason about.

### Proposed Solution
1. Rename to `normalize_and_validate()`, or
2. Don't mutate - do conversion at construction time

### Acceptance Criteria
- [ ] No surprising side effects
- [ ] Clear API contract

---

---
id: "CR-043@d9e1f3"
title: "append_to_changelog actually prepends entries"
description: "Method name is misleading"
created: 2024-12-27
section: "version"
tags: [naming, clarity]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/version/changelog.py
---

### Problem
`append_to_changelog()` (lines 225-240) actually PREPENDS new entries (line 235: `new_content = entry + "\n" + existing`). The method name is misleading.

### Affected Files
- `src/dot_work/version/changelog.py`

### Importance
Misleading names cause bugs when developers make assumptions.

### Proposed Solution
Rename to `prepend_to_changelog()` or `add_entry_to_changelog()`.

### Acceptance Criteria
- [ ] Method name reflects behavior

---

---
id: "CR-044@e0f2a4"
title: "tools/__init__.py claims zero-dependency but yaml_validator uses PyYAML"
description: "Incorrect documentation about dependencies"
created: 2024-12-27
section: "tools"
tags: [documentation, accuracy]
type: docs
priority: medium
status: proposed
references:
  - src/dot_work/tools/__init__.py
  - src/dot_work/tools/yaml_validator.py
---

### Problem
`tools/__init__.py:1-4` docstring claims "zero-dependency validation tools using only Python 3.11+ stdlib" but `yaml_validator.py` imports PyYAML (`import yaml`) which is NOT stdlib.

### Affected Files
- `src/dot_work/tools/__init__.py`
- `src/dot_work/tools/yaml_validator.py`

### Importance
Incorrect documentation misleads users and developers.

### Proposed Solution
1. Update documentation to reflect actual dependencies, or
2. Use stdlib-only YAML parsing if possible

### Acceptance Criteria
- [ ] Documentation accurate

---

---
id: "CR-045@f1a3b5"
title: "Incorrect return type annotation in yaml_validator.py"
description: "parse_yaml can return scalars but annotation says dict|list"
created: 2024-12-27
section: "tools"
tags: [type-hints, correctness]
type: bug
priority: medium
status: proposed
references:
  - src/dot_work/tools/yaml_validator.py
---

### Problem
`parse_yaml()` (lines 208-220) return type annotation is `dict[str, Any] | list[Any]`. YAML can parse scalars - `parse_yaml("42")` returns `42`, not a dict or list. Type annotation is incorrect.

### Affected Files
- `src/dot_work/tools/yaml_validator.py`

### Importance
Incorrect types cause mypy false positives and mislead developers.

### Proposed Solution
Fix return type to `Any` or appropriate union.

### Acceptance Criteria
- [ ] Type annotation accurate

---

---
id: "CR-046@a2b4c6"
title: "ProjectFile wrapper in overview/scanner.py adds no value"
description: "Thin wrapper around Path that could be eliminated"
created: 2024-12-27
section: "overview"
tags: [simplification, refactor]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/overview/scanner.py
---

### Problem
`ProjectFile` dataclass (lines 33-44) wraps `Path` but only adds `suffix` property and `read_text()`. This is a thin wrapper that doesn't justify its existence; direct `Path` usage would be simpler.

### Affected Files
- `src/dot_work/overview/scanner.py`

### Importance
Unnecessary abstractions increase cognitive load.

### Proposed Solution
Use `Path` directly instead of `ProjectFile`.

### Acceptance Criteria
- [ ] Unnecessary wrapper removed
- [ ] Code simplified

---

---
id: "CR-047@b3c5d7"
title: "Parallel dicts in overview/code_parser.py should be consolidated"
description: "_INTERFACE_DECORATOR_MARKERS and _INTERFACE_DOC_MARKERS have same keys"
created: 2024-12-27
section: "overview"
tags: [maintainability, refactor]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/overview/code_parser.py
---

### Problem
`_INTERFACE_DECORATOR_MARKERS` and `_INTERFACE_DOC_MARKERS` (lines 18-30) are parallel dictionaries with the same keys. They could become inconsistent if one is updated without the other.

### Affected Files
- `src/dot_work/overview/code_parser.py`

### Importance
Risk of inconsistency. Data structure should be unified.

### Proposed Solution
Consolidate into a single data structure (e.g., a dataclass or dict of dicts).

### Acceptance Criteria
- [ ] Single source of truth for interface markers
- [ ] No risk of drift

---

---
id: "CR-048@c4d6e8"
title: "Silent exception swallowing in overview/code_parser.py"
description: "Bare except Exception blocks return zeros without logging"
created: 2024-12-27
section: "overview"
tags: [error-handling, observability]
type: bug
priority: medium
status: proposed
references:
  - src/dot_work/overview/code_parser.py
---

### Problem
In `code_parser.py:56-57` and `70-71`, bare `except Exception` swallows all errors from radon metrics, returning zeros. Silent failures make debugging difficult when metrics are unexpectedly zero.

### Affected Files
- `src/dot_work/overview/code_parser.py`

### Importance
Silent failures mask problems and make debugging difficult.

### Proposed Solution
Log the exception before returning fallback value.

### Acceptance Criteria
- [ ] Exceptions logged
- [ ] Debugging possible

---

---
id: "CR-049@d5e7f9"
title: "Frontend CDN dependencies break offline usage"
description: "Review module depends on external CDNs for Tailwind and Highlight.js"
created: 2024-12-27
section: "review"
tags: [dependencies, reliability]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/review/templates/index.html
---

### Problem
The review template (index.html:8-12) depends on external CDNs (Tailwind, Highlight.js) which require internet access. This breaks offline usage and introduces version pinning concerns.

### Affected Files
- `src/dot_work/review/templates/index.html`

### Importance
Offline usage is a reasonable requirement for development tools.

### Proposed Solution
1. Bundle these assets locally, or
2. Provide fallbacks for offline mode

### Acceptance Criteria
- [ ] Works offline or fallback provided
- [ ] Dependencies version-pinned

---

---

id: "CR-051@f7a9b1"
title: "Inconsistent parameter naming include_unused vs unused_only"
description: "Parameter name suggests inclusion but filters exclusively"
created: 2024-12-27
section: "db_issues"
tags: [naming, clarity]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/services/label_service.py
---

### Problem
`list_labels(include_unused: bool = False)` (line 358-371) parameter name is misleading. When `True`, it only returns unused labels (not includes them). Should be `unused_only` or `filter_unused`.

### Affected Files
- `src/dot_work/db_issues/services/label_service.py`

### Importance
Misleading parameter names cause usage errors.

### Proposed Solution
Rename to `unused_only` to match behavior.

### Acceptance Criteria
- [ ] Parameter name reflects behavior

---

---
id: "CR-052@a8b0c2"
title: "Bulk service bypasses IssueService encapsulation"
description: "Direct repository access skips audit logging"
created: 2024-12-27
section: "db_issues"
tags: [architecture, encapsulation]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/services/bulk_service.py
---

### Problem
In `bulk_service.py:606` and `703`, `bulk_label_add` and `bulk_label_remove` bypass `IssueService` by calling `self.issue_service.uow.issues.save(updated_issue)` directly. This breaks encapsulation and may skip audit logging.

### Affected Files
- `src/dot_work/db_issues/services/bulk_service.py`

### Importance
Bypassing service layer can skip validation and audit.

### Proposed Solution
Use IssueService methods for updates.

### Acceptance Criteria
- [ ] All updates go through IssueService
- [ ] Audit logging consistent

---

---

id: "CR-054@c0d2e4"
title: "Bare gitignore parse failure in zip/zipper.py"
description: "Parse failure prints warning but continues, potentially exposing sensitive files"
created: 2024-12-27
section: "zip"
tags: [error-handling, security]
type: bug
priority: medium
status: proposed
references:
  - src/dot_work/zip/zipper.py
---

### Problem
In `zipper.py:70-74`, gitignore parse failure prints warning and continues. This may lead to including sensitive files that should be excluded.

### Affected Files
- `src/dot_work/zip/zipper.py`

### Importance
Security concern - sensitive files could be included in zip.

### Proposed Solution
1. Fail fast on gitignore parse error, or
2. Require explicit `--ignore-gitignore-errors` flag to continue

### Acceptance Criteria
- [ ] Safe default behavior
- [ ] Users aware of ignored gitignore

---

---
id: "CR-055@d1e3f5"
title: "Bare except Exception in zip/zipper.py swallows errors"
description: "All gitignore matcher exceptions silently swallowed"
created: 2024-12-27
section: "zip"
tags: [error-handling]
type: bug
priority: medium
status: proposed
references:
  - src/dot_work/zip/zipper.py
---

### Problem
In `zipper.py:33-37`, bare `except Exception:` swallows all errors from the gitignore matcher, including `MemoryError`, `KeyboardInterrupt` (through exception chaining), etc.

### Affected Files
- `src/dot_work/zip/zipper.py`

### Importance
Swallowing all exceptions can mask serious problems.

### Proposed Solution
Catch specific exceptions from `gitignore_parser`.

### Acceptance Criteria
- [ ] Specific exceptions caught
- [ ] Serious errors not swallowed

---

---
id: "CR-056@e2f4a6"
title: "Installer function too long at 130+ lines"
description: "install_canonical_prompts_by_environment handles multiple responsibilities"
created: 2024-12-27
section: "installer"
tags: [code-quality, refactor]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/installer.py
---

### Problem
`install_canonical_prompts_by_environment` (lines 1274-1415) is 140+ lines handling scanning, batch prompting, and installation. This exceeds the <15 lines guideline.

### Affected Files
- `src/dot_work/installer.py`

### Importance
Long functions are hard to test and maintain.

### Proposed Solution
Decompose into smaller functions:
- `_scan_prompt_files()`
- `_prompt_for_batch_choice()`
- `_install_single_prompt()`

### Acceptance Criteria
- [ ] Function decomposed
- [ ] Individual parts testable

---

---
id: "CR-057@f3a5b7"
title: "JSONL file I/O lacks atomicity in review/storage.py"
description: "Crash mid-write could corrupt comment storage"
created: 2024-12-27
section: "review"
tags: [reliability, data-integrity]
type: bug
priority: medium
status: proposed
references:
  - src/dot_work/review/storage.py
---

### Problem
`append_comment` (lines 63-66) opens file, writes, and closes without atomic write semantics. A crash mid-write could corrupt the JSONL file.

### Affected Files
- `src/dot_work/review/storage.py`

### Importance
Data corruption risk during crashes.

### Proposed Solution
1. Write to temp file and rename, or
2. Use file locking

### Acceptance Criteria
- [ ] Atomic writes implemented
- [ ] No corruption on crash

---

---
id: "CR-079@f4a0b8"
title: "Subprocess Calls Without Explicit Shell=False"
description: "Multiple subprocess.run() calls lack explicit shell parameter creating maintenance risk"
created: 2024-12-27
section: "cli"
tags: [security, subprocess, maintainability, consistency]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/cli.py
  - src/dot_work/container/provision/core.py
---

### Problem
Multiple `subprocess.run()` calls don't explicitly set `shell=False`:

```python
# src/dot_work/db_issues/cli.py:1300
result = subprocess.run([editor_name, *editor_args, str(temp_path)])

# src/dot_work/db_issues/cli.py:1376
result = subprocess.run([editor_name, *editor_args, str(temp_path)])

# src/dot_work/container/provision/core.py:429
subprocess.run(build_cmd, check=True)
```

While `shell=False` is the default for list arguments, not being explicit:

1. **Unclear intent** - Future readers may not understand security posture
2. **Accidental shell=True** - Code reviews may miss missing shell parameter
3. **Inconsistent patterns** - Some calls may set shell=True later causing bugs
4. **Security review friction** - Need to verify default each time
5. **Best practice violation** - Security guidelines recommend explicit parameters

**Scope:**
- 40+ subprocess.run() calls without explicit shell parameter identified
- Inconsistent pattern across codebase modules

### Affected Files
- `src/dot_work/db_issues/cli.py` (multiple locations)
- `src/dot_work/container/provision/core.py`
- Other files using subprocess.run()

### Importance
**MEDIUM**: Missing explicit shell parameter creates:
- Maintenance burden during security reviews
- Risk of accidental shell invocation in future changes
- Inconsistent code patterns causing confusion
- Potential for subtle bugs if list arguments are converted to strings

While not an immediate vulnerability (default is safe), it violates explicit-is-better-than-implicit principle.

### Proposed Solution
1. Add explicit `shell=False` to all subprocess.run() calls
2. Create subprocess wrapper utility with security defaults
3. Add linter rule or pre-commit hook for missing shell parameter
4. Document subprocess security best practices in AGENTS.md
5. Consider using `subprocess.check_call()` or `check_output()` for simpler cases

### Acceptance Criteria
- [ ] All subprocess.run() calls have explicit shell=False
- [ ] Subprocess wrapper utility created with security defaults
- [ ] Linter rule or pre-commit hook for subprocess validation
- [ ] Subprocess security documented in AGENTS.md
- [ ] Code review checklist includes subprocess security

### Notes
This is related to CR-075 (EDITOR command injection). Both issues would benefit from a subprocess utility wrapper that enforces security defaults across the codebase.

---

---
id: "CR-080@a5b1c9"
title: "Temporary File Permissions Not Always Enforced"
description: "Race condition between file creation and chmod exposes data"
created: 2024-12-27
section: "db_issues"
tags: [security, file-permissions, race-condition]
type: bug
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/cli.py
---

### Problem
In `cli.py:1285-1295`, temporary file is created then permissions are set:

```python
# Create temp file with delete=False
temp_file = tempfile.NamedTemporaryFile(
    mode='w',
    prefix=None,
    suffix=None,
    delete=False
)
temp_path = Path(temp_file.name)

# Write content
temp_path.write_text(issue_json)

# Set restrictive permissions (owner read/write only) for security
temp_path.chmod(0o600)
```

**Security issue:**
1. File is created with default umask (world-readable on many systems)
2. Race condition window between creation and chmod
3. Not all temp file creation points enforce permissions
4. If process crashes between creation and chmod, file remains with insecure permissions

**Additional concerns:**
- Inconsistent permission enforcement across codebase
- Multiple tempfile creation sites without controls
- No atomic permission setting mechanism

### Affected Files
- `src/dot_work/db_issues/cli.py` (lines 1285-1295)

### Importance
**MEDIUM**: Permission race condition creates:
- Short window of file exposure to other users on multi-user systems
- Potential data leakage if crash occurs before chmod
- Security audit failures
- Inconsistent security posture across codebase

While unlikely to be exploited in typical single-user dev environment, it's a real risk in:
- CI/CD environments with multiple users
- Shared development servers
- Production deployments

### Proposed Solution
1. Use `tempfile.NamedTemporaryFile` with `mode=0o600` on supported systems
2. Set umask temporarily before file creation
3. Create temp files with atomic permission setting (create, set permissions atomically)
4. Audit all tempfile usage for permission enforcement
5. Consider using file descriptor-based operations that close race window
6. Add tests for permission security

### Acceptance Criteria
- [ ] Temp files created with atomic secure permissions
- [ ] Race window eliminated or documented
- [ ] All tempfile sites enforce secure permissions
- [ ] Tests verify file permissions are secure
- [ ] Permission enforcement documented

### Notes
Platform-specific behavior: Linux supports `mode` parameter, Windows may not. Need platform-specific implementation or cross-platform solution.

---

---
id: "CR-081@b6c2d0"
title: "Docker Image Regex Over-Permissive"
description: "Image validation allows malformed formats causing Docker errors"
created: 2024-12-27
section: "container"
tags: [validation, regex, docker]
type: bug
priority: medium
status: proposed
references:
  - src/dot_work/container/provision/core.py
---

### Problem
In `core.py:48-55`, `DOCKER_IMAGE_PATTERN` regex is over-permissive:

```python
DOCKER_IMAGE_PATTERN = re.compile(
    r'^('
    r'(localhost/|[^/]+/|)'  # optional registry (localhost/ or registry.io/)
    r'[a-z0-9]+([._-][a-z0-9]+)*'  # first component (namespace or image)
    r'(/[a-z0-9]+([._-][a-z0-9]+)*)*'  # optional additional components
    r'(:[a-zA-Z0-9]+([._-][a-zA-Z0-9]+)*)?'  # optional tag
    r')$'
)
```

**Issues:**
1. **Inconsistent case** - Allows uppercase in tags but not namespaces
2. **Unlimited nesting** - No limit on `/` components (could accept `a/b/c/d/e/f/g/h/i/j`)
3. **Missing digest support** - Doesn't validate `@sha256:...` format
4. **Over-permissive chars** - Allows `.` and `_` in all positions (Docker spec is more restrictive)
5. **No length limits** - Could accept extremely long image names causing Docker errors
6. **No semantic versioning** - Tags like `:v1.2.3` not explicitly supported

**Evidence:**
- Accepts malformed images like `a.b.c/d/e/f:tag` which cause Docker errors
- Missing length limits could cause command-line truncation
- No validation of actual Docker image reference spec

### Affected Files
- `src/dot_work/container/provision/core.py` (lines 48-55)

### Importance
**MEDIUM**: Over-permissive validation causes:
- Poor user experience (image accepted then fails at Docker level)
- Cryptic error messages from Docker CLI
- Potential image spoofing via complex namespaces
- Inconsistent behavior across tools

While not a security issue, it creates friction and confusion for users.

### Proposed Solution
1. Add length limits (max 255 chars total, max 64 per component)
2. Validate digest format separately: `@sha256:[a-f0-9]{64}`
3. Limit nesting depth (max 4 path components)
4. Use official Docker image reference specification
5. Add explicit support for semantic versioning tags
6. Add tests for edge cases and malformed images
7. Improve error messages for rejected images

### Acceptance Criteria
- [ ] Length limits enforced (255 total, 64 per component)
- [ ] Digest format validated correctly
- [ ] Nesting depth limited to 4 components
- [ ] Tests for edge cases (malformed, too long, etc.)
- [ ] Clear error messages for rejected images
- [ ] Compliance with Docker image reference spec

### Notes
Reference: Docker distribution spec https://github.com/distribution/distribution/blob/main/reference/reference.go

---

---
id: "CR-082@c7d3e1"
title: "Missing Input Validation for CLI File Paths"
description: "CLI commands accept Path parameters with minimal validation enabling symlink attacks"
created: 2024-12-27
section: "cli"
tags: [security, validation, symlink, path-traversal]
type: bug
priority: medium
status: proposed
references:
  - src/dot_work/cli.py
---

### Problem
Multiple CLI commands accept `Path` parameters with only `.resolve()` and existence checks:

```python
# Line 98-101
if not target.exists():
    console.print(f"[red]❌ Target directory does not exist:[/red] {target}")
    raise typer.Exit(1)

# Line 416-420
file = file.resolve()
if not file.exists():
    console.print(f"[red]❌ File not found:[/red] {file}")
    raise typer.Exit(1)
```

**Missing validations:**
1. No check for symlinks to sensitive locations
2. No restriction on path traversal beyond project boundary
3. No validation of file type (directory vs file)
4. No size limits on file inputs
5. No validation that resolved path is within allowed directory

**Attack scenarios:**
- Symlink to `/etc/passwd` or `/etc/shadow` for disclosure
- Symlink to `/root/.ssh/` for SSH key theft
- Path traversal via `../../../` sequences
- Large file uploads causing DoS
- Directory symlink causing confusion

**Locations affected:**
- Lines 98, 184, 250, 416, 487, 643, 773

### Affected Files
- `src/dot_work/cli.py` (multiple commands)

### Importance
**MEDIUM**: Insufficient path validation enables:
- Information disclosure via symlink attacks
- Path traversal to access files outside project
- Confusion about actual file location
- Potential DoS via large files

While not critical in typical single-user development environment, it's a security concern in:
- Multi-user systems
- CI/CD with user-submitted files
- Production deployments with CLI access

### Proposed Solution
1. Create path validation helper function with:
   - Symlink detection and handling
   - Path boundary checking (within project or allowed dirs)
   - File type validation
   - Size limits for file inputs
2. Reject or validate paths with `..` sequences
3. Check for symlinks and resolve real path before validation
4. Validate path is within allowed directories
5. Add file type and size validation for input files
6. Add tests for symlink and path traversal attempts

### Acceptance Criteria
- [ ] Path validation helper created
- [ ] Symlinks detected and handled
- [ ] Path traversal prevented
- [ ] File type and size validated
- [ ] Tests for security scenarios
- [ ] All CLI commands use validation

### Notes
Consider using `Path.resolve().is_relative_to()` (Python 3.9+) or manual relative path checking to enforce boundaries.

---

---
id: "CR-083@d8e4f2"
title: "Review Module File Lists Computed Once at Startup"
description: "Stale file state shown in UI during long-running review sessions"
created: 2024-12-27
section: "review"
tags: [state-management, reliability, user-experience]
type: bug
priority: medium
status: proposed
references:
  - src/dot_work/review/server.py
---

### Problem
In `server.py:67-72`, file lists are computed once at app creation and captured in route closures:

```python
files = list_all_files(root)
tracked = set(list_tracked_files(root))
changed = changed_files(root, base=base_ref)
untracked = {f for f in files if f not in tracked}
all_changed = changed | untracked
```

These lists are captured in closure scope and never updated during the review session.

**Issue:**
If files change during a review session:
1. New files created/committed won't appear in UI
2. Deleted files still show in file tree
3. Changed files show stale diff/old content
4. User sees incorrect file state
5. Comments may be added to already-removed files

**User experience impact:**
- Confusing UI showing wrong state
- Wasted time reviewing files that no longer exist
- Missed new files that should be reviewed
- Invalid comments on deleted files

### Affected Files
- `src/dot_work/review/server.py` (lines 67-72)

### Importance
**MEDIUM**: Stale file state causes:
- Confusing user experience during active development
- Inaccurate review of changes
- Wasted time on nonexistent files
- Potential for invalid review comments

This is documented in CR-050 but warrants a more detailed issue with specific user impact analysis and solution options.

### Proposed Solution
1. **Recompute on each request** - Simple but potentially slower
2. **Add `/api/refresh` endpoint** - Manual refresh button in UI
3. **Auto-refresh with polling** - Periodic recompute (e.g., every 30 seconds)
4. **WebSocket-based updates** - Push notifications on file changes (most complex)
5. **Document limitation** - Warn users to restart review after making changes

**Recommended approach:**
- Add `/api/refresh` endpoint for manual refresh
- Add refresh button in UI
- Document that sessions should be restarted after significant changes

### Acceptance Criteria
- [ ] `/api/refresh` endpoint added
- [ ] Refresh button added to UI
- [ ] File state accurately reflects changes
- [ ] Limitation documented in help text
- [ ] Tests for refresh functionality
- [ ] Good user experience with manual refresh

### Notes
For production use, consider implementing file system watching (e.g., `watchdog` library) for automatic detection of changes. However, this adds complexity and should be evaluated against actual use patterns.

---

---

id: "PERF-007@l7m8n9"
title: "Multiple Statistics Queries in StatsService"
description: "Statistics aggregation executes 15+ separate queries instead of single GROUP BY"
created: 2024-12-27
section: "db_issues"
tags: [performance, database, statistics, query-consolidation]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/services/stats_service.py
---

### Problem
In `stats_service.py:73-100`, `get_statistics()` executes multiple separate queries:

```python
def get_statistics(self) -> Statistics:
    total = self._get_total_count()        # Query 1
    by_status = self._get_by_status(total)  # Query 2, 3, 4, 5
    by_priority = self._get_by_priority(total)  # Query 6, 7, 8, 9, 10
    by_type = self._get_by_type(total)  # Query 11, 12, 13
    metrics = self._get_metrics()  # Query 14, 15, 16...
```

Each metric group executes multiple separate database round-trips.

**Performance issue:**
- Each metric group executes multiple separate queries
- Could be combined into single query with GROUP BY
- Database round-trip latency multiplied by query count
- Called frequently on dashboard/statistics pages
- 15+ database queries per statistics refresh

**Impact:**
- Statistics page load time grows with query count
- 15+ queries × 5ms latency each = 75ms minimum
- Network overhead multiplies
- Database connection underutilized

### Affected Files
- `src/dot_work/db_issues/services/stats_service.py` (lines 73-100)

### Importance
**MEDIUM**: Affects dashboard and statistics page performance:
- Slower dashboard load times
- Poor user experience on statistics pages
- Wasted database round-trips
- Latency accumulates across the application

### Proposed Solution
1. Benchmark current implementation to measure actual performance
2. If benchmark shows > 20ms, implement single GROUP BY query consolidation
3. If benchmark shows < 20ms, current implementation is acceptable

**User decision:** Benchmark first, then decide on consolidation

### Acceptance Criteria
- [ ] Benchmark results documented with current performance
- [ ] If > 20ms: Single GROUP BY query implemented
- [ ] If < 20ms: Current implementation kept as-is
- [ ] Results match current implementation
- [ ] Handles edge cases (zero issues, deleted issues)

### Validation Plan
1. Add timing test to measure current `get_statistics()` performance
2. Run benchmark 100 times and record average/median/p95
3. If > 20ms: implement GROUP BY consolidation
4. Re-run benchmark after implementation
5. Verify results match current implementation exactly

### Dependencies
None.

### Clarifications Needed
None. Decision received: Benchmark first, consolidate only if needed.

### Notes
Original issue proposed consolidation without benchmark. User correctly identified need to measure first. If current performance is acceptable (< 20ms), optimization may not be worth the complexity.

---

---
id: "PERF-008@m8n9o0"
title: "O(n²) Nested Loops in Tag Matching"
description: "Tag list concatenated and iterated multiple times for same checks"
created: 2024-12-27
section: "git"
tags: [performance, algorithm, tag-matching, optimization]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/git/services/git_service.py
---

### Problem
In `git_service.py:843-849`, tag matching creates new lists repeatedly:

```python
# Called multiple times per comparison
if any("migration" in tag for tag in a.tags + b.tags):
    # Concatenate + iterate for each pattern
if any("api" in tag for tag in a.tags + b.tags):
    # Re-concatenate + iterate again
if any("security" in tag for tag in a.tags + b.tags):
    # Re-concatenate + iterate again
```

**Performance issue:**
- List concatenation creates new list each time (O(N))
- Iterates through concatenated list for each check (O(N))
- Multiple checks cause redundant iterations
- Called in `_find_common_themes()` for every commit pair

**Impact:**
- Commit comparison slows down with tag count
- 100 tags × 3 checks × 100 comparisons = 30,000 redundant iterations
- Noticeable latency in large repos with many tags
- Wasted CPU cycles on repeated work

### Affected Files
- `src/dot_work/git/services/git_service.py` (lines 843-849)

### Importance
**MEDIUM**: Degrades git analysis performance with tagged commits:
- Redundant work on every commit comparison
- Linear slowdown with tag count
- Makes tagged commits slower to analyze
- Easy fix with large impact

### Proposed Solution
Cache concatenated list once or use sets for O(1) membership:

```python
def _find_common_themes(self, analysis_a, analysis_b):
    # Concatenate once
    all_tags = a.tags + b.tags

    # Use cached list for all checks
    if any("migration" in tag for tag in all_tags):
        return True
    if any("api" in tag for tag in all_tags):
        return True
    if any("security" in tag for tag in all_tags):
        return True
    if any("refactor" in tag for tag in all_tags):
        return True
    # ... other checks
```

Or use sets for O(1) membership:

```python
def _find_common_themes(self, analysis_a, analysis_b):
    tags_set = set(a.tags + b.tags)

    # O(1) membership checks
    if "migration" in tags_set:
        return True
    if "api" in tags_set:
        return True
    if "security" in tags_set:
        return True
    if "refactor" in tags_set:
        return True
    # ... other checks
```

### Acceptance Criteria
- [ ] Tag list computed once (not per check)
- [ ] O(1) membership tests using sets preferred
- [ ] Performance test: 100 tags < 1ms vs current 10ms
- [ ] Results match current implementation

### Notes
Using sets provides O(1) membership and eliminates the need for iteration entirely. This is a simple fix with 2-3x speedup for tagged commits.

---
id: "PERF-009@n9o0p1"
title: "CST Memory Leaks Despite Explicit Cleanup"
description: "LibCST parsing creates massive memory overhead even with cleanup"
created: 2024-12-27
section: "overview"
tags: [performance, memory, cst, parsing, code-analysis]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/overview/code_parser.py
---

### Problem
In `code_parser.py:74-102`, CST parsing creates memory leaks despite cleanup:

```python
def parse_python_file(path: Path, code: str, module_path: str) -> dict[str, list[Any]]:
    try:
        module = cst.parse_module(code)  # CST tree: 10-50× file size in memory
    except Exception:
        return {"features": [], "models": []}

    module.visit(collector)
    result = {"features": collector.features, "models": collector.models}

    # Explicit cleanup attempt
    del module
    del collector
    gc.collect()  # Explicit GC call

    return result
```

**Performance issue:**
- LibCST trees consume massive memory (10-50× file size)
- Explicit `del` doesn't break circular references in visitor patterns
- `gc.collect()` helps but doesn't guarantee collection
- Parsing multiple files in loop accumulates memory
- Called for EVERY file in codebase during analysis

**Impact:**
- Code analysis becomes progressively slower
- Large codebases (1000+ files) consume GBs of memory
- OOM crashes during project analysis
- Memory not released until process exit
- Limits codebase size that can be analyzed

### Affected Files
- `src/dot_work/overview/code_parser.py` (lines 74-102)

### Importance
**MEDIUM**: Limits codebase size that can be analyzed:
- Large projects cause OOM crashes
- Progressive memory degradation during analysis
- Makes overview feature unusable for large codebases
- Forces users to break projects into smaller chunks

### Proposed Solution
Parse with tree-sitter instead (lower memory) or worker process isolation:

```python
# Use tree-sitter instead of libcst
import tree_sitter_python as tsp

def parse_python_file(path: Path, code: str, module_path: str):
    parser = tsp.Parser()
    tree = parser.parse(code)

    # Tree-sitter uses less memory and doesn't create visitor objects
    # Process tree directly without intermediate objects
    root = tree.root_node
    result = {"features": [], "models": []}

    # Simple traversal
    def find_nodes(node, node_types):
        if node.type in node_types:
            yield node
        for child in node.children:
            yield from find_nodes(child, node_types)

    # Process nodes directly
    for node in find_nodes(root, ["class_definition", "function_definition"]):
        # Extract features...
        pass

    return result
```

Or implement worker process isolation:

```python
def parse_python_file(path: Path, code: str, module_path: str):
    # Parse in subprocess to guarantee memory cleanup
    with multiprocessing.Pool(1) as pool:
        result = pool.apply(_parse_in_subprocess, (code, module_path))
    return result

def _parse_in_subprocess(code: str, module_path: str) -> dict:
    # Worker process - memory freed on exit
    module = cst.parse_module(code)
    collector = _Collector(module_path)
    module.visit(collector)
    return {"features": collector.features, "models": collector.models}
```

### Acceptance Criteria
- [ ] Memory usage < 5× file size (vs 10-50×)
- [ ] No memory accumulation across file parsing
- [ ] 1000+ file analysis succeeds without OOM
- [ ] Performance test: memory < 500MB for 1000 files

### Notes
Tree-sitter is significantly more memory-efficient than LibCST. Worker process isolation guarantees memory cleanup even with LibCST. Both approaches enable analysis of larger codebases.

---
id: "PERF-010@o0p1q2"
title: "Multiple fetchall() Without Size Limits"
description: "Knowledge graph queries load unlimited results causing unbounded memory"
created: 2024-12-27
section: "knowledge_graph"
tags: [performance, memory, database, fetchall, limits]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/knowledge_graph/db.py
---

### Problem
In `db.py` (multiple locations), methods use `fetchall()` without LIMIT:

```python
# Line 528: Load all nodes
node_pks = [row["node_pk"] for row in cur.fetchall()]

# Line 584: Load all node counts
nodes_by_kind = {row["kind"]: row["cnt"] for row in cur.fetchall()}

# Line 799: Load all nodes for parent
return [self._row_to_node(row) for row in cur.fetchall()]

# Lines 859, 882, 904, 963, 1075, 1240, 1360, 1526, 1599, 1714, 1751:
# 17+ total locations with fetchall() without limits
```

**Performance issue:**
- 17+ methods use `fetchall()` without LIMIT
- No memory bounding for large result sets
- Knowledge graphs with 10k+ nodes cause issues
- Called during graph building and search operations
- Unbounded memory allocation

**Impact:**
- Graph operations consume unbounded memory
- Large knowledge bases become unusable
- Server crashes during peak usage
- Memory pressure affects other operations
- No predictable memory usage

### Affected Files
- `src/dot_work/knowledge_graph/db.py` (17+ locations)

### Importance
**MEDIUM**: Affects scalability of knowledge graph:
- Prevents creation of large knowledge bases
- Unpredictable memory usage
- Server crashes under load
- Makes feature unusable at scale

### Proposed Solution
Add DEFAULT_LIMIT constant and use streaming for large results:

```python
DEFAULT_QUERY_LIMIT = 10000

def get_all_nodes(self, limit: int = DEFAULT_QUERY_LIMIT) -> list[Node]:
    """Get nodes with optional limit.

    Use iter_nodes() for unlimited results without memory issues.
    """
    cur = conn.execute("SELECT ... LIMIT ?", (limit,))
    return [self._row_to_node(row) for row in cur.fetchall()]

def iter_nodes(self, batch_size: int = 1000) -> Iterator[list[Node]]:
    """Iterate over nodes in batches to avoid memory issues."""
    offset = 0
    while True:
        cur = conn.execute("SELECT ... LIMIT ? OFFSET ?", (batch_size, offset))
        batch = [self._row_to_node(row) for row in cur.fetchall()]
        if not batch:
            break
        yield batch
        offset += batch_size
```

Apply pattern to all 17+ methods:
- `get_all_nodes()` → add limit, provide `iter_nodes()`
- `get_edges_by_type()` → add limit, provide `iter_edges_by_type()`
- `get_all_embeddings_for_model()` → add limit, provide `stream_embeddings_for_model()` (exists)
- etc.

### Acceptance Criteria
- [ ] DEFAULT_QUERY_LIMIT constant defined
- [ ] All fetchall() methods have limit parameter
- [ ] Streaming methods provided for unlimited results
- [ ] Documentation explains when to use limit vs streaming
- [ ] Performance test: 100k nodes with limit succeeds

### Notes
Streaming methods already exist for embeddings (PERF-005). Apply same pattern consistently across all database methods to enable large-scale usage with bounded memory.

---
id: "PERF-011@p1q2r3"
title: "Synchronous Cache File Operations"
description: "Cache cleanup and stats use blocking file I/O"
created: 2024-12-27
section: "git"
tags: [performance, io, async, cache, file-operations]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/git/services/cache.py
---

### Problem
In `cache.py:195, 217, 258`, cache operations are synchronous and blocking:

```python
def clear(self) -> bool:
    # Synchronous file iteration and deletion
    for cache_file in self.cache_dir.glob("*.json"):  # Blocking I/O
        cache_file.unlink()  # Blocking I/O

def cleanup_expired(self) -> int:
    # Synchronous file open/read/close for each file
    for cache_file in self.cache_dir.glob("*.json"):  # Blocking
        with open(cache_file, encoding="utf-8") as f:  # Blocking
            cache_data = json.load(f)
        cache_file.unlink()  # Blocking

def get_cache_stats(self) -> dict[str, Any]:
    # Synchronous stat() and read() for each file
    for cache_file in cache_files:
        total_size += f.stat().st_size  # Blocking I/O
```

**Performance issue:**
- Cache operations are synchronous and blocking
- Multiple file I/O operations without batching
- Large cache directories (1000+ files) cause delays
- Called during cleanup and maintenance operations
- Single-threaded file operations

**Impact:**
- Cache cleanup blocks UI
- Large caches (10,000+ files) take seconds to clean
- Affects startup time and maintenance operations
- Poor user experience during cache operations

### Affected Files
- `src/dot_work/git/services/cache.py` (lines 195, 217, 258)

### Importance
**MEDIUM**: Degrades user experience during maintenance:
- Blocking operations freeze UI
- Large cache cleanup takes noticeable time
- Poor performance on networked filesystems
- Affects perceived application responsiveness

### Proposed Solution
Use asyncio for concurrent I/O:

```python
import asyncio
import aiofiles

async def clear_async(self) -> bool:
    """Clear cache asynchronously."""
    try:
        tasks = []
        for cache_file in self.cache_dir.glob("*.json"):
            tasks.append(asyncio.to_thread(cache_file.unlink))
        await asyncio.gather(*tasks, return_exceptions=True)
        self.logger.debug(f"Cache cleared: {len(tasks)} files deleted")
        return True
    except Exception as e:
        self.logger.error(f"Failed to clear cache: {e}")
        return False

async def cleanup_expired_async(self) -> int:
    """Clean up expired cache entries asynchronously."""
    count = 0
    tasks = []

    for cache_file in self.cache_dir.glob("*.json"):
        tasks.append(asyncio.to_thread(self._check_and_delete, cache_file))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    count = sum(1 for r in results if r)
    return count
```

Or limit concurrent operations with ThreadPoolExecutor:

```python
from concurrent.futures import ThreadPoolExecutor

def cleanup_expired(self, max_workers: int = 4) -> int:
    """Clean up expired cache entries with concurrent I/O."""
    files = list(self.cache_dir.glob("*.json"))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(self._check_and_delete, f) for f in files]
        count = 0
        for future in futures:
            if future.result():
                count += 1

    self.logger.debug(f"Cleaned up {count} expired cache files")
    return count
```

### Acceptance Criteria
- [ ] Async or concurrent I/O for cache operations
- [ ] Performance test: 10k files < 2 seconds vs current 10+ seconds
- [ ] Thread/concurrency limits to avoid overwhelming filesystem
- [ ] Error handling for concurrent operations

### Notes

id: "PERF-013@r3s4t5"
title: "Redundant Scope Set Computations"
description: "Search scope sets recomputed for every search operation"
created: 2024-12-27
section: "knowledge_graph"
tags: [performance, caching, search, scope, knowledge-graph]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/knowledge_graph/search_fts.py
  - src/dot_work/knowledge_graph/search_semantic.py
---

### Problem
In `search_fts.py:100-109` and `search_semantic.py:128-137`, scope sets computed for EVERY search:

```python
# search_fts.py - Called for EVERY search
if scope:
    scope_members, scope_topics, exclude_topic_ids, shared_topic_id = _build_scope_sets(
        db, scope
    )

# _build_scope_sets() performs multiple queries:
def _build_scope_sets(db, scope):
    # Query 1: Get collection members
    # Query 2: Get topic links
    # Query 3: Build exclusion sets
    # Query 4: Get shared topic
```

**Performance issue:**
- Scope sets computed for EVERY search operation
- Scope doesn't change between searches in same session
- Multiple database queries for set building
- Called in both FTS and semantic search (high frequency)
- Repeated work for identical scope parameters

**Impact:**
- Repeated searches incur same overhead
- 100 searches = 400 redundant database queries
- Noticeable latency on search-heavy workflows
- Wasted database round-trips

### Affected Files
- `src/dot_work/knowledge_graph/search_fts.py` (lines 100-109)
- `src/dot_work/knowledge_graph/search_semantic.py` (lines 128-137)

### Importance
**MEDIUM**: Affects search performance:
- Repeated searches slow down unnecessarily
- Database overhead for each search
- Poor user experience in search-heavy workflows
- Easy optimization with caching

### Proposed Solution
Cache scope sets with TTL or session-level caching:

```python
from functools import lru_cache
import hashlib
import time

@lru_cache(maxsize=32)
def _build_scope_sets_cached(db_id: int, scope_hash: str, time_bucket: int):
    """Cached version of _build_scope_sets."""
    # This still needs to build real sets - just cached by parameters
    # Need to pass actual db reference somehow
    pass

# Better: Scope object-level caching
class SearchSession:
    def __init__(self, db):
        self.db = db
        self._scope_cache = {}

    def search(self, query, scope):
        if scope is None:
            return self._search_unscoped(query)

        scope_key = (scope.project, tuple(scope.topics), tuple(scope.exclude_topics))
        if scope_key not in self._scope_cache:
            self._scope_cache[scope_key] = _build_scope_sets(self.db, scope)

        # Use cached sets
        scope_members, scope_topics, exclude_topic_ids, shared_topic_id = self._scope_cache[scope_key]

        # ... rest of search
```

Or time-based caching with TTL:

```python
# In search functions
_scope_cache = {}
_cache_ttl = 300  # 5 minutes

def search(db, query, scope, ttl_seconds=_cache_ttl):
    if scope:
        scope_hash = hashlib.sha256(repr(scope).encode()).hexdigest()
        time_bucket = int(time.time() // ttl_seconds)

        cache_key = (id(db), scope_hash, time_bucket)
        if cache_key not in _scope_cache:
            _scope_cache[cache_key] = _build_scope_sets(db, scope)

        scope_members, scope_topics, exclude_topic_ids, shared_topic_id = _scope_cache[cache_key]
```

### Acceptance Criteria
- [ ] Scope sets cached across searches
- [ ] Cache invalidation when data changes
- [ ] Performance test: 100 searches with same scope < 2 seconds vs current 5+ seconds
- [ ] TTL or manual invalidation implemented

### Notes
Search scope rarely changes within a session. Caching should provide 3-5x speedup for repeated searches with identical scope parameters.

---
id: "PERF-014@s4t5u6"
title: "Sequential Commit Processing"
description: "Git commits analyzed sequentially without parallelization"
created: 2024-12-27
section: "git"
tags: [performance, parallelism, git, commit-analysis, cpu]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/git/services/git_service.py
---

### Problem
In `git_service.py:94-102`, commits analyzed sequentially:

```python
# compare_refs() - Process commits sequentially
analyzed_commits = []
for commit in tqdm(commits, desc="Analyzing commits"):
    try:
        analysis = self.analyze_commit(commit)  # Blocking per commit
        analyzed_commits.append(analysis)
    except Exception as e:
        self.logger.error(f"Failed to analyze commit {commit.hexsha}: {e}")
        continue
```

**Performance issue:**
- Commits analyzed sequentially (one at a time)
- Each commit requires file diff parsing, complexity calculation
- CPU-bound operations not parallelized
- Analysis time scales linearly with commit count
- With LLM summarization: each commit = 1-2 seconds

**Impact:**
- Large comparisons (100+ commits) take minutes
- CPU underutilized (single core at 100%, others idle)
- Blocking UI during analysis
- 8-core machine using only 12.5% of capacity

### Affected Files
- `src/dot_work/git/services/git_service.py` (lines 94-102)

### Importance
**MEDIUM**: Limits throughput of git analysis:
- Makes large comparisons slow
- Wastes CPU resources
- Poor user experience on multi-core machines
- Easy optimization with large speedup

### Proposed Solution
Parallelize commit analysis with ProcessPoolExecutor:

```python
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

def compare_refs(self, from_ref: str, to_ref: str) -> ComparisonResult:
    commits = self._get_commits_between_refs(from_ref, to_ref)

    # Parallelize CPU-bound commit analysis
    analyzed_commits = []
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {
            executor.submit(_analyze_commit_impl, commit.hexsha, self.config.repo_path)
            for commit in commits
        }

        for future in tqdm(as_completed(futures), total=len(commits), desc="Analyzing"):
            try:
                analysis = future.result()
                analyzed_commits.append(analysis)
            except Exception as e:
                self.logger.error(f"Failed to analyze commit: {e}")

    # Sort by original commit order
    commit_order = {c.hexsha: i for i, c in enumerate(commits)}
    analyzed_commits.sort(key=lambda a: commit_order.get(a.commit_hash, float('inf')))

    # ... rest of comparison

# Top-level function for picklability
def _analyze_commit_impl(commit_hash: str, repo_path: str) -> ChangeAnalysis:
    """Standalone function for parallel execution."""
    config = AnalysisConfig(repo_path=repo_path, use_llm=False, cache_enabled=True)
    service = GitAnalysisService(config)
    return service.analyze_commit(commit_hash)
```

### Acceptance Criteria
- [ ] Commit analysis parallelized with ProcessPoolExecutor
- [ ] CPU utilization increased to 80%+ on multi-core
- [ ] Performance test: 100 commits on 8-core < 30 seconds vs current 200+ seconds
- [ ] Error handling preserves all successful analyses
- [ ] Results sorted by original commit order

### Notes
This optimization should provide 4-8x speedup on multi-core machines (linear speedup with core count for CPU-bound analysis). Memory usage increases with worker count but is manageable.

------

id: "DOGFOOD-009@foa1hu"
title: "Add non-goals section to main documentation"
description: "dot-work documentation lacks explicit statement of what it does NOT do"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, clarity, dogfooding]
type: docs
priority: medium
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - README.md
  - docs/dogfood/baseline.md
---

### Problem
Documentation has no section on non-goals. Users may have incorrect expectations about what dot-work can do.

**Missing:**
- What problems are out of scope?
- What won't dot-work help with?
- What tools should be used instead for those problems?

### Affected Files
- `README.md`
- `docs/dogfood/baseline.md`

### Importance
**MEDIUM**: Clear non-goals prevent user disappointment:
- Sets proper expectations
- Avoids feature requests outside scope
- Helps users choose right tool

### Proposed Solution
Add non-goals section to README documenting that dot-work is a human-directed AI agent framework for issue management and autonomous agent implementation:
```markdown
## Non-Goals

dot-work is a human-directed AI agent framework for issue management and autonomous agent implementation. It does NOT:

- Replace full project management tools (Jira, Linear, etc.)
- Provide autonomous agents without human direction
- Host prompts or provide cloud services
- Manage dependencies or build systems
- Replace git workflow tools
- Provide CI/CD integration

It is a local development tool for AI-assisted coding workflows with human oversight.
```

**User decision:** dot-work is a human-directed AI agent framework for issue management and autonomous agent implementation

### Acceptance Criteria
- [ ] Non-goals section added to README
- [ ] Defines dot-work as human-directed AI agent framework
- [ ] Clear scope boundaries defined
- [ ] Alternative tools suggested where appropriate

### Validation Plan
1. Add "Non-Goals" section to README.md
2. Explicitly state "human-directed AI agent framework"
3. List out-of-scope features
4. Verify with user that definition is accurate

### Dependencies
None.

### Clarifications Needed
None. Definition provided by user.

### Notes
This is gap #3 in gaps-and-questions.md (Medium Priority).

---

---

id: "DOGFOOD-010@foa1hu"
title: "Document issue editing workflow (AI-only)"
description: "Clarify that AI tools should edit issue files, not humans"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, workflow, dogfooding]
type: docs
priority: medium
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - .work/agent/issues/
  - .github/prompts/
---

### Problem
How do users/edit-AI tools edit issues? User feedback: "The tools and AI should edit the issue files, not humans"

**Unclear:**
- Are there CLI commands to add/edit/move issues?
- Should humans ever edit `.work/agent/issues/*.md` directly?
- How to move issues between priority files?
- How to update issue status without AI?

### Affected Files
- Documentation files
- `.work/agent/issues/` (readme or guide)

### Importance
**MEDIUM**: Users need to understand proper workflow:
- Prevents manual file editing mistakes
- Ensures issues are managed correctly
- Maintains issue file format consistency

### Proposed Solution
Add documentation section:
```markdown
## Editing Issues

Issues are edited by AI agents via prompts:

- `/new-issue` – Create issue with generated ID
- `/do-work` – Move issue through workflow states
- `/focus on <topic>` – Create issues in shortlist.md

Direct file editing is NOT recommended. The AI manages issue state.
```

### Acceptance Criteria
- [ ] Issue editing workflow documented
- [ ] AI-only policy clearly stated
- [ ] Prompt commands listed for issue management
- [ ] Warning about manual editing

### Notes
This is gap #4 in gaps-and-questions.md (Medium Priority). User explicitly provided feedback on this.

---

---

id: "DOGFOOD-011@foa1hu"
title: "Document prompt trigger format by environment"
description: "How to use installed prompts varies by AI environment - undocumented"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, prompts, dogfooding]
type: docs
priority: medium
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - README.md
  - src/dot_work/prompts/
---

### Problem
How to use prompts after install? Are all prompts slash commands? How does Claude Code use prompts (no slash commands)?

**Unclear:**
- Are all prompts slash commands?
- How does Claude Code use prompts (no slash commands)?
- What about Cursor, Windsurf, Aider, etc.?

### Affected Files
- `README.md`
- Documentation files

### Importance
**MEDIUM**: Users can't use installed prompts without knowing how:
- Prompts installed but unusable
- Environment-specific differences confusing
- Poor first-time user experience

### Proposed Solution
Add documentation section:
```markdown
## Using Installed Prompts

| Environment | How to Use |
|-------------|------------|
| GitHub Copilot | Type `/prompt-name` in chat |
| Claude Code | Automatically reads CLAUDE.md |
| Cursor | Select from `@` menu |
| Windsurf | Automatically reads .windsurf/rules/ |
| Aider | Automatically reads CONVENTIONS.md |
| Continue.dev | Type `/prompt-name` |
| Amazon Q | Automatically reads .amazonq/rules.md |
| Zed AI | Select from prompts menu |
| OpenCode | Automatically reads AGENTS.md |
| Generic | Manually reference prompt files |
```

### Acceptance Criteria
- [ ] Prompt usage table added
- [ ] All 10+ environments documented
- [ ] Clear examples for each environment
- [ ] Slash command vs automatic read distinction clear

### Notes
This is gap #9 in gaps-and-questions.md (Medium Priority).

---

---

id: "DOGFOOD-012@foa1hu"
title: "Document all undocumented CLI commands"
description: "Some commands in --help have no documentation: canonical, zip, container, python, git, harness"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, cli, dogfooding]
type: docs
priority: medium
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - docs/dogfood/tooling-reference.md
  - src/dot_work/cli.py
---

### Problem
Some commands in `--help` have no documentation. From tooling-reference.md:

**Commands needing docs:**
| Command | Description | Priority |
|---------|-------------|----------|
| `canonical` | Validate/install canonical prompts | HIGH |
| `zip` | Zip folders respecting .gitignore | LOW |
| `container` | Container operations | MEDIUM |
| `python` | Python utilities | MEDIUM |
| `git` | Git analysis tools | MEDIUM |
| `harness` | Claude Agent SDK harness | LOW |

### Affected Files
- Documentation files
- Each command's implementation

### Importance
**MEDIUM**: Undocumented commands are unused:
- Commands exist but users don't know about them
- Missing features go undiscovered
- Tool appears less capable

### Proposed Solution
For each command, add:
1. Brief description
2. Usage examples
3. When to use the command
4. Links to implementation if advanced

### Acceptance Criteria
- [ ] `canonical` command documented (HIGH priority)
- [ ] `container` operations documented
- [ ] `python` utilities documented
- [ ] `git` analysis tools documented
- [ ] All commands have at least basic documentation

### Notes
This is gap #10 in gaps-and-questions.md (Medium Priority).

---

---

id: "DOGFOOD-013@foa1hu"
title: "Add canonical prompt validation documentation"
description: "How to validate .canon.md without installing - undocumented"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, prompts, validation, dogfooding]
type: docs
priority: medium
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - docs/prompt-authoring.md
  - src/dot_work/prompts/canonical.py
---

### Problem
How to validate .canon.md without installing? What validation is performed?

**Unclear:**
- Is there a `validate` command for canonical prompts?
- What validation is performed?
- How to test before installing?

### Affected Files
- `docs/prompt-authoring.md`
- Tooling reference

### Importance
**MEDIUM**: Prompt authors need to validate before distributing:
- Invalid prompts cause installation failures
- No way to test prompts locally
- Poor prompt authoring experience

### Proposed Solution
Add documentation section:
```markdown
## Validating Canonical Prompts

# Validate without installing
dot-work canonical validate my-prompt.canon.md

# Or check during install
dot-work prompts install my-prompt.canon.md --target copilot --dry-run
```

### Acceptance Criteria
- [ ] Validation command documented (if exists)
- [ ] Validation rules documented
- [ ] Dry-run mode documented
- [ ] Error examples with fixes

### Notes
This is gap #8 in gaps-and-questions.md (Medium Priority).

---

---
id: "TEST-040@7a277f"
title: "db-issues integration tests need CLI interface updates"
description: "Integration tests use non-existent --json flag and wrong output format"
created: 2025-12-29
section: "db_issues"
tags: [tests, integration, cli-compatibility]
type: test
priority: medium
status: proposed
references:
  - tests/integration/db_issues/test_bulk_operations.py
  - tests/integration/db_issues/test_team_collaboration.py
  - tests/integration/db_issues/test_agent_workflows.py
  - tests/integration/db_issues/test_dependency_model.py
  - tests/integration/db_issues/test_advanced_filtering.py
  - src/dot_work/db_issues/cli.py
---

### Problem
Integration tests in `tests/integration/db_issues/` were migrated from another project and don't match the current CLI interface:

1. **Non-existent `--json` flag**: Tests use `--json` on commands that don't support it (e.g., `create --json`)
2. **Wrong output format**: Tests expect `json.loads(result.stdout)` to return arrays directly, but the CLI returns wrapped objects like `{"command": "list", "issues": [...], "total": N}`
3. **Issue ID parsing**: Tests use `split()[0]` to parse issue IDs, but Rich-formatted output breaks this

**Affected tests:**
- `test_bulk_operations.py` - Uses `--json` flag on create command (doesn't exist)
- `test_team_collaboration.py` - Uses `--json` flag, expects direct array output
- `test_agent_workflows.py` - Uses `--json` flag, expects direct array output
- `test_dependency_model.py` - Uses `--json` flag, expects direct array output
- `test_advanced_filtering.py` - PARTIALLY FIXED: One test updated, others still need fixes

### Affected Files
- `tests/integration/db_issues/test_bulk_operations.py`
- `tests/integration/db_issues/test_team_collaboration.py`
- `tests/integration/db_issues/test_agent_workflows.py`
- `tests/integration/db_issues/test_dependency_model.py`
- `tests/integration/db_issues/test_advanced_filtering.py` (partially fixed)
- `src/dot_work/db_issues/cli.py` (may need --json flag added)

### Importance
**MEDIUM**: Integration tests provide valuable coverage but are currently blocked:
- Tests can't run without fixes
- No integration test coverage for db-issues module
- Core bugs already fixed (SQLite URL format, session.commit()), but tests can't verify them

### Proposed Solution
**Option A: Update tests to match current CLI**
1. Remove `--json` flag usage (doesn't exist)
2. Parse wrapped output: `data = json.loads(result.stdout); issues = data["issues"]`
3. Use regex for issue ID parsing: `re.search(r"issue-[\w]+", result.stdout)`
4. Update all affected test files

**Option B: Add --json flag to CLI commands**
1. Add `--json` option to create, edit, and other commands
2. Return issue objects directly in JSON format
3. Update tests to use new flag

**Recommendation**: Option A (update tests) is faster and matches current CLI design.

### Acceptance Criteria
- [ ] All db_issues integration tests pass
- [ ] Tests parse CLI output correctly
- [ ] Issue IDs extracted with regex instead of split()
- [ ] JSON output wrapper handled correctly
- [ ] No reliance on non-existent --json flag

### Notes
**Core bugs already fixed in commit a28f145:**
- SQLite URL format for absolute paths (config.py)
- Missing session.commit() in create command (cli.py)
- Integration test fixture database initialization (conftest.py)

**Already fixed:**
- `test_advanced_filtering.py::test_filter_by_date_range` - Updated with regex and correct JSON parsing

**Remaining work:** Update 4 more test files with same pattern.

---
id: "CR-085@e3f1g2"
title: "Missing Type Annotation for FileAnalyzer config Parameter"
description: "Parameter named 'config' but type is AnalysisConfig without annotation"
created: 2024-12-31
section: "git"
tags: [type-hints, naming, clarity]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/git/services/file_analyzer.py
---

### Problem
In `file_analyzer.py:24-25`, `FileAnalyzer.__init__` parameter is named `config` but the actual type is `AnalysisConfig`. No type annotation exists, making it unclear what configuration is expected.

### Affected Files
- `src/dot_work/git/services/file_analyzer.py` (lines 24-25)

### Importance
**MEDIUM**: Missing type annotations reduce IDE support and make refactoring harder:
- No autocomplete for config properties
- mypy cannot catch type mismatches
- Unclear what configuration object is required

### Proposed Solution
Add proper type annotation:
```python
from dot_work.git.models import AnalysisConfig

class FileAnalyzer:
    def __init__(self, config: AnalysisConfig):
        self.config = config
```

### Acceptance Criteria
- [ ] Type annotation added to `__init__` parameter
- [ ] Import of `AnalysisConfig` added
- [ ] mypy passes without new errors
- [ ] Documentation reflects typed parameter

---

---
id: "CR-086@f4g2h3"
title: "Excessive Use of Any in Cache Service Type Hints"
description: "Cache system uses Any return types despite having specific cached types"
created: 2024-12-31
section: "git"
tags: [type-safety, type-hints, abstraction]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/git/services/cache.py
---

### Problem
In `cache.py`, methods use `Any` return types extensively despite knowing specific types like `ChangeAnalysis`:
- `get(self, key: str) -> Any | None`
- `_serialize_data(self, data: Any) -> Any`
- `_deserialize_data(self, data: Any) -> Any`

This defeats the purpose of type checking. The cache knows it stores `ChangeAnalysis` but still returns `Any`.

### Affected Files
- `src/dot_work/git/services/cache.py` (lines 37-45, 81-99, 101-129)

### Importance
**MEDIUM**: Type safety issues reduce value of static typing:
- Callers must cast or use `type: ignore`
- mypy cannot catch type mismatches
- Changes to cached types not caught by tests

### Proposed Solution
Introduce generic type parameter for cache:
```python
from typing import TypeVar, Generic

T = TypeVar('T')

class AnalysisCache(Generic[T]):
    def get(self, key: str) -> T | None:
        ...

    def _serialize_data(self, data: T) -> Any:
        ...

    def _deserialize_data(self, data: Any, expected_type: type[T]) -> T:
        ...
```

Or use TypedDict/Protocol for specific cached types.

### Acceptance Criteria
- [ ] Cache type hints use generics or specific types
- [ ] Callers get proper type inference
- [ ] No `type: ignore` needed for cache usage
- [ ] Tests verify type correctness

---

---
id: "CR-087@g5h3i4"
title: "Magic Numbers in Search Service Without Named Constants"
description: "Query limits 500 and 10 appear without explanation"
created: 2024-12-31
section: "db_issues"
tags: [magic-values, maintainability, constants]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/services/search_service.py
---

### Problem
In `search_service.py:240-241, 279-282, 335-336`, magic numbers appear:
- `len(query) > 500` - maximum query length
- `query.count(" OR ") > 10` - maximum OR conditions

These appear multiple times but are not defined as module-level constants.

### Affected Files
- `src/dot_work/db_issues/services/search_service.py` (lines 240-241, 279-282, 335-336)

### Importance
**MEDIUM**: Magic numbers without names make code harder to maintain:
- Unclear why 500 and 10 were chosen
- Can't easily adjust limits
- Must search/replace to change values
- No single source of truth

### Proposed Solution
Define named constants:
```python
MAX_QUERY_LENGTH = 500
MAX_OR_CONDITIONS = 10

def _validate_query(query: str) -> str:
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError(f"Query too long (maximum {MAX_QUERY_LENGTH} characters)")

    if query.count(" OR ") > MAX_OR_CONDITIONS:
        raise ValueError(f"Too many OR conditions (maximum {MAX_OR_CONDITIONS})")
```

### Acceptance Criteria
- [ ] Named constants defined at module level
- [ ] All usages reference constants
- [ ] Constants documented with rationale
- [ ] Tests reference constants for edge cases

---

---
id: "CR-088@h6i4j5"
title: "Silent Exception in Scanner Config Loading"
description: "Bare except Exception swallows pyproject.toml parse errors without logging"
created: 2024-12-31
section: "overview"
tags: [error-handling, observability]
type: bug
priority: medium
status: proposed
references:
  - src/dot_work/overview/scanner.py
---

### Problem
In `scanner.py:74-88`, `load_scanner_config` has a bare `except Exception:` on line 81 that silently catches all exceptions when reading `pyproject.toml`:

```python
try:
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
except Exception:
    data = {}
```

No logging of what went wrong. Users can't diagnose malformed config files.

### Affected Files
- `src/dot_work/overview/scanner.py` (lines 74-88)

### Importance
**MEDIUM**: Silent failures make debugging difficult:
- Can't tell if pyproject.toml was malformed
- Can't tell if file was unreadable
- Silent fallback to default config
- User unaware of configuration problems

### Proposed Solution
Add specific exception handling with logging:
```python
import logging
import tomllib.TOMLDecodeError

logger = logging.getLogger(__name__)

try:
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
except tomllib.TOMLDecodeError as e:
    logger.warning("Invalid TOML in %s: %s", pyproject, e)
    data = {}
except OSError as e:
    logger.warning("Could not read %s: %s", pyproject, e)
    data = {}
```

### Acceptance Criteria
- [ ] Specific exceptions caught (TOMLDecodeError, OSError)
- [ ] All exceptions logged with context
- [ ] Generic Exception not used
- [ ] Tests verify error handling

---

---
id: "CR-089@i7j5k6"
title: "Cache Type Deserialization Inconsistency Causes Data Loss"
description: "Dataclass types serialized with data but deserialized as empty dict"
created: 2024-12-31
section: "git"
tags: [bug, data-loss, serialization]
type: bug
priority: medium
status: proposed
references:
  - src/dot_work/git/services/cache.py
---

### Problem
In `cache.py:88, 96-97`, inconsistent handling of dataclass types:

**Serialization (line 88):**
```python
"data": asdict(data) if not isinstance(data, type) else asdict(data()),
```
This calls `asdict(data())` for types, serializing an **instance** with data.

**Deserialization (lines 96-97):**
```python
elif isinstance(data, type):
    return {"__dataclass__": data.__name__, "__module__": data.__module__, "data": {}}
```
This returns `data: {}`, an **empty dict**.

Deserialized types lose all their data. The special case for `ChangeAnalysis` (lines 110-115) suggests this is a known workaround.

### Affected Files
- `src/dot_work/git/services/cache.py` (lines 88, 96-97, 110-115)

### Importance
**MEDIUM**: Data loss bug in cache serialization:
- Cached dataclass types corrupted on deserialization
- Workaround for `ChangeAnalysis` indicates known issue
- Other types would lose data silently
- Cache cannot reliably store dataclass types

### Proposed Solution
Fix deserialization to reconstruct with data:
```python
# Remove the empty dict case
# Instead, reconstruct the instance using __init__ or factory
```

Or document that only instances (not types) should be cached.

### Acceptance Criteria
- [ ] Deserialization reconstructs instances correctly
- [ ] `ChangeAnalysis` workaround no longer needed
- [ ] Tests verify round-trip for cached types
- [ ] Documentation clarifies cache contract

---

---
id: "CR-090@j8k6l7"
title: "Git Ref Regex Over-Permissive on Special Characters"
description: "Validation allows ^ and @ anywhere in ref, not just in valid positions"
created: 2024-12-31
section: "review"
tags: [validation, regex, correctness]
type: bug
priority: medium
status: proposed
references:
  - src/dot_work/review/git.py
---

### Problem
In `git.py:17-22`, the ref validation regex is over-permissive:

```python
_REF_PATTERN = re.compile(
    r"^[a-zA-Z0-9_\-./~^:@]+$"  # Standard ref characters
    r"|^[a-fA-F0-9]{40,64}$"  # Full commit hash
    r"|^HEAD$"  # HEAD reference
    r"|^@\{-[0-9]+\}$"  # @annotation syntax (e.g., @{-1})
)
```

The first alternative `^[a-zA-Z0-9_\-./~^:@]+$` allows `^` and `@` anywhere, not just in specific positions. Strings like `test@value` or `foo^bar` would pass validation even though they're not valid git refs.

Git ref specs restrict these characters to specific positions:
- `^` only at end for dereference (e.g., `HEAD^`)
- `@` only in `@{u}`, `@{-1}` contexts

### Affected Files
- `src/dot_work/review/git.py` (lines 17-22)

### Importance
**MEDIUM**: Validation accepts invalid refs:
- False positives in validation
- Errors passed to git commands instead of caught early
- Poor error messages for invalid input

### Proposed Solution
Tighten regex to restrict special characters to valid positions:
```python
_REF_PATTERN = re.compile(
    r"^[a-zA-Z0-9_\-./~]+$"  # Standard ref characters (no ^, @)
    r"|^[a-zA-Z0-9_\-./~]+(\^[0-9]*)?$"  # Ref with optional ^ dereference
    r"|^[a-fA-F0-9]{40,64}$"  # Full commit hash
    r"|^HEAD$"  # HEAD reference
    r"|^@\{-[0-9]+\}$"  # @annotation syntax (e.g., @{-1})
    r"|^[a-zA-Z0-9_\-./~]+@\{[uU]\}$"  # @{u} upstream syntax
)
```

### Acceptance Criteria
- [ ] Regex restricts ^ to end-of-ref position
- [ ] Regex restricts @ to @{n} or @{u} syntax
- [ ] Invalid refs like `test@value` rejected
- [ ] Tests cover edge cases

---

---
id: "CR-091@k9l7m8"
title: "Deduplication Pattern Repeated 3 Times in Dependency Service"
description: "Exact deduplication logic duplicated across methods"
created: 2024-12-31
section: "db_issues"
tags: [code-duplication, maintainability]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/services/dependency_service.py
---

### Problem
In `dependency_service.py:246-253, 301-308`, the exact deduplication pattern appears multiple times:

```python
# Deduplicate while preserving order
seen: set[tuple[str, str]] = set()
unique_impact: list[Dependency] = []
for dep in all_impact:
    key = (dep.from_issue_id, dep.to_issue_id)
    if key not in seen:
        seen.add(key)
        unique_impact.append(dep)
```

This exact logic appears 3 times in the same file. Violates DRY principle.

### Affected Files
- `src/dot_work/db_issues/services/dependency_service.py` (lines 246-253, 301-308)

### Importance
**MEDIUM**: Code duplication creates maintenance burden:
- Bug fixes must be applied 3 times
- Inconsistent behavior if one instance missed
- Harder to understand intent
- Violates DRY principle

### Proposed Solution
Extract to helper function:
```python
def _deduplicate_dependencies(
    dependencies: list[Dependency]
) -> list[Dependency]:
    """Deduplicate dependencies by (from_issue_id, to_issue_id)."""
    seen: set[tuple[str, str]] = set()
    unique: list[Dependency] = []
    for dep in dependencies:
        key = (dep.from_issue_id, dep.to_issue_id)
        if key not in seen:
            seen.add(key)
            unique.append(dep)
    return unique
```

### Acceptance Criteria
- [ ] Helper function extracted
- [ ] All 3 usages replaced
- [ ] Tests verify deduplication works
- [ ] Type hints added to helper

---

---
id: "CR-092@l0m8n9"
title: "O(n) path.index() in Cycle Detection Algorithm"
description: "Cycle detection uses linear search in visited path for each node"
created: 2024-12-31
section: "db_issues"
tags: [performance, algorithm]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/services/dependency_service.py
---

### Problem
In `dependency_service.py:94-156`, cycle detection uses `path.index(current)` which is O(n):

```python
def find_cycle(current: str) -> list[str] | None:
    if current in path:
        # Found a cycle - extract the cycle portion
        cycle_start = path.index(current)  # O(n) search
        return path[cycle_start:] + [current]
```

In large dependency graphs with many nodes, this repeated O(n) search makes the algorithm O(n²).

### Affected Files
- `src/dot_work/db_issues/services/dependency_service.py` (lines 94-156)

### Importance
**MEDIUM**: Performance issue for large graphs:
- Cycle detection slows with graph size
- O(n²) worst-case complexity
- Could block operations on projects with many issues
- Easy fix with large improvement

### Proposed Solution
Track node positions in a dict for O(1) lookup:
```python
def check_circular(self, issue_id: str) -> CycleResult:
    visited: set[str] = set()
    path: list[str] = []
    path_index: dict[str, int] = {}  # Track positions

    def find_cycle(current: str) -> list[str] | None:
        if current in path_index:  # O(1) lookup
            cycle_start = path_index[current]
            return path[cycle_start:] + [current]

        if current in visited:
            return None

        visited.add(current)
        path_index[current] = len(path)  # Track position
        path.append(current)
        # ... rest of DFS
```

### Acceptance Criteria
- [ ] Cycle detection uses O(1) position lookup
- [ ] Performance test: 1000 issues < 100ms vs current 1+ seconds
- [ ] Tests verify cycle detection correctness
- [ ] Algorithm documented

---

---
id: "CR-093@m1n9o0"
title: "Generic Exception Catching in Code Parser"
description: "CST parsing catches all Exceptions instead of specific parse errors"
created: 2024-12-31
section: "overview"
tags: [error-handling, specificity]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/overview/code_parser.py
---

### Problem
In `code_parser.py:94-98`, generic `Exception` catch without logging specific error type:

```python
try:
    module = cst.parse_module(code)
except Exception as e:
    logger.warning("Failed to parse %s: %s", path, e)
    return {"features": [], "models": []}
```

CST throws specific exceptions like `cst.ParserSyntaxError` that would be more useful to log. Generic catch may also hide unexpected errors.

### Affected Files
- `src/dot_work/overview/code_parser.py` (lines 94-98)

### Importance
**MEDIUM**: Overly broad exception catching:
- Can't distinguish parse errors from other failures
- Specific error types not logged for debugging
- May hide unexpected errors (OSError, MemoryError, etc.)
- Poor diagnostic information

### Proposed Solution
Catch specific CST exceptions:
```python
try:
    module = cst.parse_module(code)
except cst.ParserSyntaxError as e:
    logger.warning("Syntax error in %s: %s", path, e)
    return {"features": [], "models": []}
except Exception as e:
    logger.error("Unexpected error parsing %s: %s", path, e)
    raise  # Re-raise unexpected errors
```

### Acceptance Criteria
- [ ] Specific CST exceptions caught
- [ ] Unexpected exceptions re-raised
- [ ] Error types logged for debugging
- [ ] Tests verify error handling

---

---
id: "CR-094@n2o0p1"
title: "Module-Level Singleton Instantiation at Import Time"
description: "CANONICAL_PARSER and CANONICAL_VALIDATOR instantiated on module import"
created: 2024-12-31
section: "prompts"
tags: [hidden-control-flow, side-effects]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/prompts/canonical.py
---

### Problem
In `canonical.py:428-430`, module-level singletons instantiated at import time:

```python
# Module-level singletons for efficient reuse (classes have no state)
CANONICAL_PARSER = CanonicalPromptParser()
CANONICAL_VALIDATOR = CanonicalPromptValidator()
```

While documented as "stateless", these are instantiated at import time. If `__init__` methods become non-trivial, this causes import-time side effects.

### Affected Files
- `src/dot_work/prompts/canonical.py` (lines 428-430)

### Importance
**LOW**: Potential issue if initialization becomes complex:
- Import-time initialization can be slow
- Hard to test with different configurations
- Hidden control flow - code runs "just because"
- If __init__ gains side effects, affects all imports

### Proposed Solution
Use lazy initialization or module-level functions:
```python
# Option 1: Lazy initialization
_CANONICAL_PARSER: CanonicalPromptParser | None = None

def get_canonical_parser() -> CanonicalPromptParser:
    global _CANONICAL_PARSER
    if _CANONICAL_PARSER is None:
        _CANONICAL_PARSER = CanonicalPromptParser()
    return _CANONICAL_PARSER

# Option 2: Just use class directly (no instances needed)
# Call CanonicalPromptParser().parse() instead of CANONICAL_PARSER.parse()
```

### Acceptance Criteria
- [ ] Singletons not instantiated at import time
- [ ] Lazy initialization or direct class usage
- [ ] Tests verify initialization behavior
- [ ] No performance regression

---

---
id: "CR-095@o3p1q2"
title: "TODO Comment for LLM Integration Not Addressed"
description: "Unimplemented LLM integration in changelog module"
created: 2024-12-31
section: "version"
tags: [technical-debt, incomplete-feature]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/version/changelog.py
---

### Problem
In `changelog.py:194`, TODO comment for unimplemented feature:

```python
# TODO: Implement LLM integration
```

This technical debt marker has not been addressed. Unclear if this is still planned or should be removed.

### Affected Files
- `src/dot_work/version/changelog.py` (line 194)

### Importance
**LOW**: Technical debt marker needs resolution:
- Unclear if feature is still planned
- TODO comments accumulate and become noise
- No indication of priority or ownership
- May indicate incomplete feature

### Proposed Solution
1. Implement the LLM integration if still needed
2. Remove TODO if feature is no longer planned
3. Convert TODO to a tracked issue if desired
4. Add GitHub issue reference if appropriate

### Acceptance Criteria
- [ ] TODO addressed (implemented, removed, or tracked)
- [ ] No orphaned TODO comments
- [ ] Feature documented if implemented
- [ ] Issue linked if deferred

---

---
id: "CR-096@p4q2r3"
title: "Exit Code Constants Not Encapsulated"
description: "EXIT_CODE_* constants defined as module-level globals"
created: 2024-12-31
section: "container"
tags: [constants, encapsulation]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/container/provision/cli.py
---

### Problem
In `cli.py:22-23`, exit codes as module-level constants:

```python
EXIT_CODE_ERROR = 1
EXIT_CODE_KEYBOARD_INTERRUPT = 130
```

Not encapsulated in Enum or class, making them harder to discover and reuse consistently.

### Affected Files
- `src/dot_work/container/provision/cli.py` (lines 22-23)

### Importance
**LOW**: Constants could be better organized:
- Harder to discover all valid exit codes
- No namespace/grouping
- Inconsistent with other constants in codebase
- Could conflict with other imports

### Proposed Solution
Encapsulate in Enum or class:
```python
from enum import IntEnum

class ExitCode(IntEnum):
    ERROR = 1
    KEYBOARD_INTERRUPT = 130
    SUCCESS = 0
```

### Acceptance Criteria
- [ ] Exit codes encapsulated in Enum or class
- [ ] All usages updated to reference Enum
- [ ] Tests verify exit codes
- [ ] Documented in module docstring

---

---
id: "CR-097@q5r3s4"
title: "Hardcoded Editor Allowlist May Be Overly Restrictive"
description: "Editor validation uses hardcoded list without extension mechanism"
created: 2024-12-31
section: "db_issues"
tags: [validation, usability, magic-values]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/db_issues/cli.py
---

### Problem
In `cli.py:1248-1257`, hardcoded editor allowlist:

```python
_ALLOWED_EDITORS = {
    "vi", "vim", "nvim", "nano", "emacs", "pico", "micro", "kak",
    "code", "code-server", "codium", "subl", "mate", "bbedit",
    "hx", "neovide", "lvim", "astrovim", "nvim-qt", "gvim",
}
```

Validation at line 1322 rejects any editor not in this list. No way to extend or bypass this validation.

### Affected Files
- `src/dot_work/db_issues/cli.py` (lines 1248-1257, 1322)

### Importance
**LOW**: Usability concern for users with other editors:
- Legitimate editors rejected
- No way to add custom editors
- Must modify source code to use different editor
- Poor user experience for non-standard editors

### Proposed Solution
1. Add `--allow-any-editor` flag to bypass validation
2. Allow config file extension of allowed editors
3. Document how to request adding editors
4. Consider removing validation entirely (what's the risk?)

### Acceptance Criteria
- [ ] Way to bypass validation exists
- [ ] Config file can extend allowed editors
- [ ] Documentation explains editor validation
- [ ] Tests cover validation bypass

---

---
id: "CR-098@r6s4t5"
title: "Review Server Closure Pattern Captures Startup State"
description: "Route handlers close over variables computed once at app creation"
created: 2024-12-31
section: "review"
tags: [hidden-control-flow, state-management]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/review/server.py
---

### Problem
In `server.py:70-76, 78-119`, route handlers close over variables from `create_app`:

```python
files = list_all_files(root)
tracked = set(list_tracked_files(root))
changed = changed_files(root, base=base_ref)
untracked = {f for f in files if f not in tracked}
all_changed = changed | untracked

@app.get("/", response_class=HTMLResponse)
def index(request: Request, path: str | None = None) -> HTMLResponse:
    if not path and files:  # Closes over files
        path = next((p for p in files if p in all_changed), files[0])
```

State computed once at startup, captured in closures. Related to CR-050 and CR-083 but this is about the closure pattern itself.

### Affected Files
- `src/dot_work/review/server.py` (lines 70-76, 78-119)

### Importance
**LOW**: Closure pattern could be confusing:
- State looks local but is effectively module-level
- Multiple app creations don't work as expected
- Harder to test with different file states
- Closures obscure data flow

### Proposed Solution
Use request-scoped state or FastAPI dependencies:
```python
from fastapi import Depends

def get_file_state():
    # Recompute on each request
    files = list_all_files(root)
    tracked = set(list_tracked_files(root))
    changed = changed_files(root, base=base_ref)
    untracked = {f for f in files if f not in tracked}
    return {"files": files, "all_changed": changed | untracked}

@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    path: str | None = None,
    state: dict = Depends(get_file_state)
) -> HTMLResponse:
    files = state["files"]
    all_changed = state["all_changed"]
    # ...
```

### Acceptance Criteria
- [ ] State not captured in closures
- [ ] FastAPI dependencies used for shared state
- [ ] File state recomputed per request (or cached with TTL)
- [ ] Tests can inject different file states

---
---

id: "CR-103@y1z2a3"
title: "Installer Module Compound Extension Logic Has Hidden Complexity"
description: "Compound extension handling in installer.py has unclear edge cases and insufficient documentation"
created: 2024-12-31
section: "installer"
tags: [complexity, hidden-control-flow, cognitive-load]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/installer.py
  - tests/unit/test_installer.py
---

### Problem
In `installer.py`, compound extension handling (handling compound prompts like "base+python") has hidden complexity:

**Observed issues:**
1. **Complex string parsing**: Extensions like `.base+python.md` parsed with unclear rules
2. **Hidden precedence**: When both single and compound extensions exist, behavior is unclear
3. **Edge cases unclear**: What happens with `base+python+review.md`?
4. **No validation**: Invalid compound formats may fail silently

The fix in "857535c" addressed some issues, but the logic remains complex and hard to follow.

### Affected Files
- `src/dot_work/installer.py` (compound extension handling)
- `tests/unit/test_installer.py` (test coverage for compound extensions)

### Importance
**MEDIUM**: Cognitive load and maintainability concern:
- Complex parsing logic hard to understand
- Edge cases may produce unexpected behavior
- Adding new extension types requires understanding hidden rules
- Tests cover basic cases but edge cases undocumented

### Proposed Solution
1. Extract compound extension parsing to separate class
2. Document all edge cases and precedence rules
3. Add validation for invalid compound formats
4. Use regex or formal grammar for parsing

```python
class CompoundExtension:
    """Handles compound prompt extensions like 'base+python'."""

    PART_SEPARATOR = "+"
    MAX_PARTS = 3

    def __init__(self, extension: str):
        parts = extension.rstrip(".md").split(self.PART_SEPARATOR)
        if len(parts) > self.MAX_PARTS:
            raise ValueError(
                f"Compound extension has {len(parts)} parts, "
                f"maximum {self.MAX_PARTS} allowed"
            )
        self.parts = parts
        self.base = parts[0]
        self.modifiers = parts[1:]

    def __str__(self) -> str:
        return f".{self.PART_SEPARATOR.join(self.parts)}.md"
```

### Acceptance Criteria
- [ ] Compound extension parsing extracted to class
- [ ] All edge cases documented
- [ ] Invalid formats raise clear errors
- [ ] Tests cover all edge cases

---
---

id: "CR-104@z2a3b4"
title: "Canonical Prompt Parser Has Unclear Purpose for Multiple Parsing Methods"
description: "Multiple parsing methods in canonical.py without clear differentiation of use cases"
created: 2024-12-31
section: "prompts"
tags: [abstraction-clarity, api-design]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/prompts/canonical.py
  - tests/unit/test_canonical.py
---

### Problem
In `canonical.py`, the `CanonicalPromptParser` class has multiple parsing methods with unclear purpose:

**Methods observed:**
1. `parse()` - Main parsing method
2. `parse_frontmatter()` - Extracts frontmatter only
3. `parse_content()` - Parses content sections
4. `parse_sections()` - Parses individual sections

**Issues:**
1. **Unclear responsibility**: Which method should be called externally?
2. **Hidden dependencies**: Methods call each other in non-obvious ways
3. **Public vs private**: All methods public but some seem internal
4. **No use case documentation**: When to use `parse_frontmatter()` vs `parse()`?

The `@dataclass` classes and parser lack clear guidance on which methods form the public API.

### Affected Files
- `src/dot_work/prompts/canonical.py` (parser class, lines 200-400)
- Tests for canonical prompts

### Importance
**MEDIUM**: API clarity and usage guidance concern:
- Users don't know which parsing method to use
- Unclear what the "public API" is
- Hard to add new features without breaking existing usage
- Tests cover implementation but not use cases

### Proposed Solution
1. Clarify public vs private API with `_` prefix for internal methods
2. Add use case documentation to each public method
3. Consider splitting into separate classes for different use cases
4. Add usage examples in docstrings

```python
class CanonicalPromptParser:
    """Parse canonical prompt files.

    Public API:
    - parse() : Parse entire file (most common use case)
    - parse_frontmatter() : Extract metadata only

    Internal methods (prefixed with _):
    - _parse_content() : Parse content sections
    - _parse_sections() : Parse individual sections
    """
```

### Acceptance Criteria
- [ ] Public API clearly documented
- [ ] Internal methods prefixed with `_`
- [ ] Use cases documented for each public method
- [ ] Usage examples in docstrings

---
---

id: "CR-105@a3b4c5"
title: "Prompt Installer Discovery Logic Has Unclear Contract"
description: "discover_available_environments() has unclear contract with callers about environment handling"
created: 2024-12-31
section: "installer"
tags: [abstraction-clarity, api-design]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/installer.py
  - src/dot_work/cli.py (lines 115-146)
---

### Problem
In `installer.py`, `discover_available_environments()` has an unclear contract:

**Observed issues:**
1. **Unclear return type**: Returns dict but what if no environments found?
2. **Error handling**: What happens if prompts_dir doesn't exist?
3. **Caller confusion**: `cli.py:115-146` shows complex interaction

From `cli.py:138-146`:
```python
if env_key not in discovered_envs:
    console.print(
        f"[yellow]⚠ Environment '{env_key}' not found in any prompt frontmatter.[/yellow]"
    )
    if not typer.confirm("Continue with legacy installation?", default=False):
        raise typer.Exit(0)
```

This implies the function's contract is unclear - what's "legacy installation"?

### Affected Files
- `src/dot_work/installer.py` (`discover_available_environments`)
- `src/dot_work/cli.py` (lines 115-146, caller logic)

### Importance
**MEDIUM**: API clarity concern:
- Caller doesn't know what to expect from the function
- "Legacy installation" concept unclear
- No documented error handling behavior
- Function's purpose unclear from name alone

### Proposed Solution
1. Document function contract explicitly
2. Return a result object with success/failure status
3. Clarify "legacy installation" concept
4. Add tests for edge cases

```python
@dataclass
class DiscoveryResult:
    """Result of environment discovery."""
    environments: dict[str, str]  # env_key -> prompt_count
    has_prompts: bool
    prompts_dir: Path

def discover_available_environments(
    prompts_dir: Path
) -> DiscoveryResult:
    """Discover environments from prompt frontmatter.

    Returns:
        DiscoveryResult with discovered environments and metadata.

    Raises:
        FileNotFoundError: If prompts_dir doesn't exist
    """
```

### Acceptance Criteria
- [ ] Function contract documented
- [ ] Return type changed to result object
- [ ] Error handling documented
- [ ] Tests cover edge cases

---


---
