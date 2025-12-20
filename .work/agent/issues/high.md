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
section: "cli"
tags: [cli, workflow, issue-tracker]
type: enhancement
priority: high
status: proposed
references:
  - src/dot_work/cli.py
  - src/dot_work/prompts/setup-issue-tracker.prompt.md
---

### Problem
The prompts document `init work` as a trigger command to create the `.work/` issue tracking structure, but no CLI command implements this functionality.

### Affected Files
- `src/dot_work/cli.py` (add new command)
- `src/dot_work/installer.py` (add initialization logic)

### Importance
Users following the workflow documentation cannot initialize the issue tracker without manually creating the directory structure. This is a gap between documented and actual functionality.

### Proposed Solution
1. Add `dot-work init-work` command to CLI
2. Create function `initialize_work_directory(target: Path, console: Console)` in installer.py
3. Create the full `.work/` structure as defined in setup-issue-tracker.prompt.md:
   - `.work/baseline.md` (placeholder)
   - `.work/agent/focus.md`
   - `.work/agent/memory.md`
   - `.work/agent/notes/.gitkeep`
   - `.work/agent/issues/{critical,high,medium,low,backlog,shortlist,history}.md`
   - `.work/agent/issues/references/.gitkeep`
4. Populate files with initial content from the prompt template

### Acceptance Criteria
- [ ] `dot-work init-work` creates complete `.work/` structure
- [ ] `dot-work init-work --target ./other` works for non-current directories
- [ ] Command is idempotent (doesn't overwrite existing files unless --force)
- [ ] Initial file content matches setup-issue-tracker.prompt.md templates
- [ ] Tests verify directory creation and file content

### Notes
Consider detecting project context (language, framework) to populate memory.md.

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
