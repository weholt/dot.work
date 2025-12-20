# High Priority Issues (P1)

Core functionality broken or missing documented features.

---

---
id: "FEAT-003@a3f7c2"
title: "Implement --force flag behavior in install command"
description: "The --force flag is documented but not implemented"
created: 2024-12-20
completed: 2024-12-20
section: "cli"
tags: [cli, install, dead-code]
type: bug
priority: high
status: completed
references:
  - src/dot_work/cli.py
  - src/dot_work/installer.py
---

### Problem
The `--force` flag is documented as "Overwrite existing files without asking" but the parameter is never read. Files are always overwritten without prompting, regardless of the flag value.

### Solution Implemented
1. Added `should_write_file(dest_path, force, console)` helper function in installer.py
2. Updated `install_prompts()` signature to accept `force: bool = False` keyword argument
3. Updated all 10 `install_for_*` functions to accept and use `force` parameter
4. Updated CLI to pass `force` parameter from command to `install_prompts()`
5. Added 9 new tests covering force behavior

### Changes
- `src/dot_work/installer.py`: Added `should_write_file()` helper, updated signatures
- `src/dot_work/cli.py`: Pass force parameter to `install_prompts()`
- `tests/unit/test_installer.py`: Added `TestShouldWriteFile`, `TestInstallPrompts`, `TestInstallForCopilotWithForce` test classes

### Verification
- 165 tests passing (was 156)
- 42% coverage (up from 41%)
- All quality checks pass

---

---
id: "FEAT-004@b8e1d4"
title: "Implement dot-work init-work CLI command"
description: "Add command to initialize .work/ issue tracker structure"
created: 2024-12-20
completed: 2024-12-20
section: "cli"
tags: [cli, workflow, issue-tracker]
type: enhancement
priority: high
status: completed
references:
  - src/dot_work/cli.py
  - src/dot_work/installer.py
  - src/dot_work/prompts/setup-issue-tracker.prompt.md
---

### Problem
The prompts document `init work` as a trigger command to create the `.work/` issue tracking structure, but no CLI command implements this functionality.

### Solution Implemented
1. Added `dot-work init-work` command to CLI with `--target` and `--force` options
2. Created `initialize_work_directory()` function in installer.py
3. Created `detect_project_context()` function to auto-detect language/framework
4. Full `.work/` structure is created with proper templates
5. Added 15 new tests (TestDetectProjectContext: 7, TestInitializeWorkDirectory: 8)

### Changes
- `src/dot_work/cli.py`: Added `init-work` command, imported `initialize_work_directory`
- `src/dot_work/installer.py`: Added template constants, `detect_project_context()`, `initialize_work_directory()`
- `tests/unit/test_installer.py`: Added `TestDetectProjectContext` and `TestInitializeWorkDirectory` classes

### Acceptance Criteria
- [x] `dot-work init-work` creates complete `.work/` structure
- [x] `dot-work init-work --target ./other` works for non-current directories
- [x] Command is idempotent (doesn't overwrite existing files unless --force)
- [x] Initial file content matches setup-issue-tracker.prompt.md templates
- [x] Tests verify directory creation and file content
- [x] Project context (language, framework) detected for memory.md

### Verification
- 180 tests passing (was 165, +15)
- 46% coverage (was 42%, +4%)
- All quality checks pass

---

---
id: "TEST-001@c4a9f6"
title: "Add installer and CLI integration tests"
description: "No tests exist for install_for_* functions or CLI commands"
created: 2024-12-20
section: "tests"
tags: [testing, coverage, cli]
type: test
priority: high
status: proposed
references:
  - tests/unit/test_installer.py
  - src/dot_work/cli.py
  - src/dot_work/installer.py
---

### Problem
The core functionality (file installation) is not unit tested. CLI commands (`install`, `detect`, `list`, `init`) have no tests. Only template rendering is tested.

### Affected Files
- `tests/unit/test_installer.py` (expand)
- `tests/unit/test_cli.py` (create new)
- `tests/conftest.py` (add fixtures)

### Importance
Without tests, regressions in installation logic go undetected. The installer functions and CLI are the primary user-facing features.

### Proposed Solution
1. Create `tests/unit/test_cli.py` using `typer.testing.CliRunner`
2. Add tests for each CLI command:
   - `test_install_creates_files_for_each_environment`
   - `test_install_detects_environment_correctly`
   - `test_list_shows_all_environments`
   - `test_detect_finds_environment_markers`
3. Add installer tests for each `install_for_*` function:
   - Verify correct directories created
   - Verify files have expected content
   - Verify template variables substituted
4. Add fixtures for temporary project directories with various environment markers

### Acceptance Criteria
- [ ] Each `install_for_*` function has at least one test
- [ ] Each CLI command has happy-path and error-path tests
- [ ] `detect_environment()` tested with fixture directories
- [ ] Coverage for installer.py ≥ 80%
- [ ] Coverage for cli.py ≥ 70%

### Notes
Use parametrized tests to avoid repetition across environments.

---

---
id: "BUG-001@c5e8f1"
title: "Version mismatch between pyproject.toml and __init__.py"
description: "Version strings are out of sync: 0.1.0 vs 0.1.1"
created: 2024-12-20
completed: 2024-12-20
section: "versioning"
tags: [bug, versioning, config, sync]
type: bug
priority: high
status: completed
references:
  - pyproject.toml
  - src/dot_work/__init__.py
---

### Problem
The project has two version definitions that are out of sync:
- `pyproject.toml` line 3: `version = "0.1.0"`
- `src/dot_work/__init__.py` line 3: `__version__ = "0.1.1"`

This causes confusion about the actual version and can lead to incorrect version reporting.

### Solution Implemented
1. Set correct version to `0.1.1` in `pyproject.toml`
2. Removed `__version__` from `src/dot_work/__init__.py` entirely
3. Established `pyproject.toml` as single source of truth (no sync needed)
4. Updated memory.md with version management rules
5. Created language-agnostic bump-version.prompt.md
6. Updated CLI to use `importlib.metadata.version()` instead of `__version__`

### Changes
- `pyproject.toml`: Updated to `version = "0.1.1"`
- `src/dot_work/__init__.py`: Removed `__version__` line
- `src/dot_work/cli.py`: Changed version display to use `importlib.metadata.version("dot-work")`
- `.work/agent/memory.md`: Updated Version Management section
- `.github/prompts/bump-version.prompt.md`: Complete rewrite, now language-agnostic

### Acceptance Criteria
- [x] Single source of truth established (pyproject.toml)
- [x] No duplicate version definitions to get out of sync
- [x] Memory.md documents version management rules
- [x] bump-version.prompt.md created with investigation-first workflow
- [x] CLI uses importlib.metadata for version (no __version__ import)

