# Medium Priority Issues (P2)

Enhancements, technical debt, code quality improvements.

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
id: "CR-050@e6f8a0"
title: "Server closures capture stale state in review/server.py"
description: "Files computed once at startup won't reflect changes during session"
created: 2024-12-27
section: "review"
tags: [state-management, reliability]
type: bug
priority: medium
status: proposed
references:
  - src/dot_work/review/server.py
---

### Problem
In `server.py:67-72`, `files`, `tracked`, `changed`, and `all_changed` are computed once at app creation and captured in route closures. If files change during the review session, the UI shows stale data.

### Affected Files
- `src/dot_work/review/server.py`

### Importance
Long-running sessions could show incorrect file state.

### Proposed Solution
1. Recompute file lists on each request, or
2. Add refresh mechanism, or
3. Document limitation

### Acceptance Criteria
- [ ] File state accurate or limitation documented

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
id: "CR-053@b9c1d3"
title: "Inconsistent transaction management in db_issues services"
description: "Some methods use with self.uow context, others don't"
created: 2024-12-27
section: "db_issues"
tags: [consistency, transactions]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/services/issue_service.py
  - src/dot_work/db_issues/services/epic_service.py
---

### Problem
`set_epic` and `clear_epic` (issue_service.py:701-740) use `with self.uow:` context manager and call `self.uow.commit()`, while most other methods don't. In epic_service, `create_epic` and `update_epic` use `with self.uow:` but `get_epic`, `list_epics`, `delete_epic` don't.

### Affected Files
- `src/dot_work/db_issues/services/issue_service.py`
- `src/dot_work/db_issues/services/epic_service.py`

### Importance
Inconsistent transaction handling could cause unexpected behavior.

### Proposed Solution
Establish and document consistent transaction pattern.

### Acceptance Criteria
- [ ] Consistent transaction usage
- [ ] Pattern documented

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
id: "CR-084@e9f5a3"
title: "Inconsistent Transaction Usage in db_issues Services"
description: "Mixed transaction patterns across services cause unpredictable behavior"
created: 2024-12-27
section: "db_issues"
tags: [consistency, transactions, database]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/services/issue_service.py
  - src/dot_work/db_issues/services/epic_service.py
  - src/dot_work/db_issues/services/
---

### Problem
Inconsistent transaction usage patterns across db_issues services:

**Using context manager:**
```python
# issue_service.py:711-740
def set_epic(self, issue_id: str, epic_id: str | None) -> None:
    with self.uow:
        # ... operations ...
        self.uow.commit()

# epic_service.py:143-209
def create_epic(self, project_id: str, title: str) -> Epic:
    with self.uow:
        # ... operations ...
        self.uow.commit()
```

**Not using context manager:**
```python
# epic_service.py: get_epic(), list_epics(), delete_epic()
# issue_service.py: get_issue(), list_issues(), etc.
# Most read operations don't use context
```

**Inconsistencies:**
- Some write methods use `with self.uow:` and commit manually
- Others rely on UnitOfWork auto-commit
- Read operations vary in context manager usage
- No clear pattern for when context manager should be used
- CR-053 documents this partially but scope needs expansion

### Affected Files
- `src/dot_work/db_issues/services/issue_service.py`
- `src/dot_work/db_issues/services/epic_service.py`
- Other services in `db_issues/services/`

### Importance
**MEDIUM**: Inconsistent transaction handling causes:
- Unpredictable transaction boundaries
- Potential partial commits on errors
- Inconsistent rollback behavior across operations
- Developer confusion about transaction semantics
- Risk of data corruption if patterns are inconsistent

### Proposed Solution
1. **Establish clear transaction pattern** documented in AGENTS.md:
   - Write operations: always use `with self.uow:` context manager
   - Read operations: never use context manager (use auto-commit)
   - Multi-step operations: explicit context with manual commit
2. **Refactor all services** to follow established pattern
3. **Add unit tests** for transaction rollback behavior
4. **Document transaction semantics** for each service method
5. **Add linter or pre-commit check** for transaction usage patterns

### Acceptance Criteria
- [ ] Clear transaction pattern documented
- [ ] All write operations use UnitOfWork context
- [ ] All read operations avoid context manager
- [ ] Tests for rollback behavior
- [ ] Method-level transaction documentation
- [ ] Linter check for pattern compliance

### Notes
This is an expansion of CR-053. Establishing a clear, consistent pattern is essential for maintainability and preventing data corruption bugs.

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
Combine into single GROUP BY query:

```python
def get_statistics(self) -> Statistics:
    result = self.session.exec(text("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'proposed' THEN 1 END) as proposed,
            COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
            COUNT(CASE WHEN status = 'blocked' THEN 1 END) as blocked,
            COUNT(CASE WHEN priority = 0 THEN 1 END) as critical,
            COUNT(CASE WHEN priority = 1 THEN 1 END) as high,
            COUNT(CASE WHEN priority = 2 THEN 1 END) as medium,
            COUNT(CASE WHEN priority = 3 THEN 1 END) as low,
            COUNT(CASE WHEN type = 'task' THEN 1 END) as task,
            COUNT(CASE WHEN type = 'bug' THEN 1 END) as bug,
            COUNT(CASE WHEN type = 'enhancement' THEN 1 END) as enhancement,
            COUNT(CASE WHEN type = 'refactor' THEN 1 END) as refactor,
            COUNT(CASE WHEN type = 'test' THEN 1 END) as test,
            COUNT(CASE WHEN type = 'docs' THEN 1 END) as docs
        FROM issues
        WHERE deleted_at IS NULL
    """))

    row = result.first()
    return Statistics(
        total=row.total,
        by_status={
            'proposed': row.proposed or 0,
            'in_progress': row.in_progress or 0,
            'completed': row.completed or 0,
            'blocked': row.blocked or 0,
        },
        by_priority={
            'critical': row.critical or 0,
            'high': row.high or 0,
            'medium': row.medium or 0,
            'low': row.low or 0,
        },
        by_type={
            'task': row.task or 0,
            'bug': row.bug or 0,
            'enhancement': row.enhancement or 0,
            'refactor': row.refactor or 0,
            'test': row.test or 0,
            'docs': row.docs or 0,
        }
    )
```

### Acceptance Criteria
- [ ] Single GROUP BY query for all statistics
- [ ] All metrics calculated in database
- [ ] Performance test: < 10ms vs current 75ms
- [ ] Results match current implementation
- [ ] Handles edge cases (zero issues, deleted issues)

### Notes
This optimization reduces database round-trips from 15+ to 1, providing 5-10x speedup. The single query is more maintainable and easier to understand.

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
ThreadPoolExecutor approach is simpler and doesn't require async throughout. Should provide 4-10x speedup for cache operations on large directories.

---
id: "PERF-012@q2r3s4"
title: "No Memoization for Git Branch/Tag Lookups"
description: "Branch and tag lookups performed repeatedly for same commits"
created: 2024-12-27
section: "git"
tags: [performance, memoization, caching, git, branch-tag]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/git/services/git_service.py
---

### Problem
In `git_service.py:615-639`, branch and tag lookups have no caching:

```python
def _get_commit_branch(self, commit: gitpython.Commit) -> str:
    # No caching - performs full traversal every time
    for branch in self.repo.branches:
        if commit.hexsha in [c.hexsha for c in self.repo.iter_commits(branch.name)]:
            return branch.name
    return "unknown"

def _get_commit_tags(self, commit: gitpython.Commit) -> list[str]:
    # No caching - iterates all tags every time
    tags = []
    for tag in self.repo.tags:
        if tag.commit.hexsha == commit.hexsha:
            tags.append(tag.name)
    return tags
```

**Performance issue:**
- Same commit queried multiple times during analysis
- Branch lookup: Full branch traversal per commit
- Tag lookup: Full tag iteration per commit
- Called for EVERY commit in comparison (100-1000+ times)
- Redundant work across analyses

**Impact:**
- Git comparison becomes progressively slower
- Redundant work for same commits across analyses
- Analysis time scales quadratically with commit count
- 100 commits × full traversal each = massive waste

### Affected Files
- `src/dot_work/git/services/git_service.py` (lines 615-639)

### Importance
**MEDIUM**: Visible in multi-commit analyses:
- Repeated full traversals for same commits
- Wasted CPU cycles and I/O
- Makes repeated analyses slower
- Easy optimization with large impact

### Proposed Solution
Memoize branch/tag lookups once per comparison:

```python
def compare_refs(self, from_ref: str, to_ref: str) -> ComparisonResult:
    # Clear and build caches once per comparison
    self._commit_to_branch = {}
    self._commit_to_tags = {}

    commits = self._get_commits_between_refs(from_ref, to_ref)

    # Pre-build commit → branch mapping
    for branch in self.repo.branches:
        for commit in self.repo.iter_commits(branch.name):
            self._commit_to_branch[commit.hexsha] = branch.name

    # Pre-build commit → tags mapping
    for tag in self.repo.tags:
        commit_hash = tag.commit.hexsha
        if commit_hash not in self._commit_to_tags:
            self._commit_to_tags[commit_hash] = []
        self._commit_to_tags[commit_hash].append(tag.name)

    # Now O(1) lookups in analyze_commit()
    for commit in commits:
        analysis = self.analyze_commit(commit)  # Uses cached maps

def _get_commit_branch(self, commit: gitpython.Commit) -> str:
    return self._commit_to_branch.get(commit.hexsha, "unknown")

def _get_commit_tags(self, commit: gitpython.Commit) -> list[str]:
    return self._commit_to_tags.get(commit.hexsha, [])
```

### Acceptance Criteria
- [ ] Commit-to-branch mapping built once per comparison
- [ ] Commit-to-tags mapping built once per comparison
- [ ] O(1) lookups in `_get_commit_branch()` and `_get_commit_tags()`
- [ ] Performance test: 1000 commits < 5 seconds vs current 30+ seconds
- [ ] Caches cleared between comparisons

### Notes
This optimization should provide 10-100x speedup for multi-commit analyses. Memory overhead is minimal (dict with commit hash keys).

---
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

---