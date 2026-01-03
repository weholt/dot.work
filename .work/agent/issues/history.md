# Issue History (Append-Only)

Completed and closed issues are archived here.

---
---
id: "CR-001@e7f3a2"
title: "Remove dead code duplicate error messages in installer.py"
description: "Unreachable duplicate error messages after ValueError raise at line 1521"
created: 2025-01-02
section: "installer"
tags: [deletion-test, dead-code, cleanup]
type: refactor
priority: critical
status: completed
completed: 2026-01-02
references:
  - src/dot_work/installer.py
---

### Problem
Lines 1522-1527 in `src/dot_work/installer.py` contained unreachable code that duplicated
error messages already provided at lines 1510-1516.

### Solution Implemented
Deleted lines 1522-1527 (6 lines of dead code).

### Verification
- Build passes: `uv run python scripts/build.py`
- All 517 tests pass
- No functionality changes (code was unreachable)

### Notes
The duplicate lines were likely introduced during a refactor where error handling
was moved but the old guidance print statements weren't cleaned up.

---
---
id: "CR-002@b4d8c1"
title: "Simplify dual-mode install_prompts function"
description: "Function has hidden control flow with canonical fallback logic"
created: 2025-01-02
section: "installer"
tags: [cognitive-load, hidden-control-flow, refactor]
type: refactor
priority: high
status: completed
completed: 2026-01-02
references:
  - src/dot_work/installer.py
---

### Problem
The `install_prompts` function had hidden dual-mode behavior - first tried
canonical installation, then fell back to legacy on specific ValueError.
This was not locally apparent from the function signature.

### Solution Implemented
Added explicit `fallback_to_legacy: bool = True` parameter to function signature.
Updated docstring to clearly document the dual-mode behavior. Made control flow
explicit with named variable `is_no_canonical`.

### Verification
- Build passes: `uv run python scripts/build.py`
- All 517 tests pass
- Behavior unchanged (default maintains backward compatibility)

### Notes
The default `fallback_to_legacy=True` maintains backward compatibility.
Callers can now explicitly disable fallback with `fallback_to_legacy=False`.

---
---
id: "CR-003@a9f2b3"
title: "Add tests for safe_path_join security function"
description: "Critical security function lacks test coverage"
created: 2025-01-02
section: "utils"
tags: [testing, security, coverage]
type: test
priority: medium
status: completed
completed: 2026-01-02
references:
  - src/dot_work/utils/path.py
  - tests/unit/utils/test_path.py
---

### Problem
Issue raised based on initial code review suggesting `safe_path_join` lacked test coverage.

### Resolution
Upon investigation, comprehensive tests already exist in `tests/unit/utils/test_path.py`:
- 18 tests covering all security-critical paths
- Symlink attacks (escaping and within-target)
- Path traversal attempts (`../`, absolute paths)
- Edge cases (empty strings, path separators, special characters)
- Target validation

### Verification
- All 18 tests pass
- Coverage for all error paths
- Security scenarios covered

### Notes
Issue was based on incomplete review. Tests were already in place and comprehensive.

---
---
id: "CR-004@c8e4d5"
title: "Reduce complexity of prompt_for_environment function"
description: "67-line function with nested conditionals exceeds cognitive load threshold"
created: 2025-01-02
section: "cli"
tags: [cognitive-load, complexity, refactor]
type: refactor
priority: medium
status: completed
completed: 2026-01-02
references:
  - src/dot_work/cli.py
---

### Problem
The `prompt_for_environment` function was 67 lines with deeply nested conditionals
that made it hard to reason about locally.

### Solution Implemented
Split into 4 smaller functions:
- `_build_environment_options()` - builds list of env keys (11 lines)
- `_display_environment_menu()` - displays the menu (27 lines)
- `_validate_environment_choice()` - validates user input (41 lines)
- `prompt_for_environment()` - orchestrates the flow (8 lines)

Main function is now just 8 lines and easy to understand.

### Verification
- Build passes: `uv run python scripts/build.py`
- All 517 tests pass
- Behavior unchanged
- Each helper function has single responsibility

### Notes
The refactor improves testability and local reasoning. Each function can now
be tested independently.

---
---
id: "CR-005@d7e6f4"
title: "Rename init_project to clarify it's an alias"
description: "Function name misleading - doesn't create project structure"
created: 2025-01-02
section: "cli"
tags: [naming, semantic-precision]
type: refactor
priority: medium
status: completed
completed: 2026-01-02
references:
  - src/dot_work/cli.py
---

### Problem
The `init_project` command was named to suggest creating a new project, but it's
actually just an alias that calls `install()`. The help text claimed to "initialize
a new project" which was misleading.

### Solution Implemented
Updated the command's docstring to clarify:
- It's an alias for 'install' command
- Installs AI prompts to existing projects
- References 'init-tracking' for issue tracking setup
- References 'install' for more control

Kept the command name as-is for backward compatibility.

### Verification
- Build passes: `uv run python scripts/build.py`
- All 517 tests pass
- Help text now accurately describes behavior

### Notes
The command name remains `init` for backward compatibility, but the help text
now makes it clear this is for adding prompts to existing projects.

---
---
id: "CR-001@e8a3b2"
title: "Fix validation conflict - empty strings in global.yml will crash parser"
description: "SkillEnvironmentConfig validation rejects empty strings but global.yml uses them"
created: 2026-01-03
section: "skills"
tags: [validation, bug, critical, skills, subagents]
type: bug
priority: critical
status: completed
completed: 2026-01-03
references:
  - src/dot_work/skills/models.py
  - src/dot_work/skills/global.yml
  - src/dot_work/bundled_skills/global.yml
  - src/dot_work/bundled_subagents/global.yml
---

### Problem
The `SkillEnvironmentConfig.__post_init__()` validation explicitly rejected empty strings, but the global.yml files used empty strings as values. This would cause ValueError when parsing skills/subagents with global defaults.

### Solution Implemented
Changed all global.yml files to remove empty string values:
- `src/dot_work/skills/global.yml` - removed `filename_suffix: ""`
- `src/dot_work/subagents/global.yml` - removed `filename: ""`
- `src/dot_work/bundled_skills/global.yml` - removed `filename_suffix: ""`
- `src/dot_work/bundled_subagents/global.yml` - removed `filename: ""`

When a field is not needed, it's now simply omitted from YAML (becomes None in Python).

### Verification
- Build passes: `uv run python scripts/build.py`
- All 517 tests pass
- Parser no longer crashes with ValueError
- Global defaults loaded successfully

### Notes
This was a regression introduced by REFACTOR-001 implementation. The validation was added but the configuration files were not updated to match.


---
---
id: "REFACTOR-001@a4f2b1"
title: "Create bundled_skills and bundled_subagents directories"
description: "Phase 1: Establish package structure for bundled skills and subagents"
created: 2025-01-02
section: "architecture"
tags: [skills, subagents, architecture, phase-1]
type: refactor
priority: medium
status: completed
completed: 2026-01-03
references:
  - src/dot_work/
  - skills_agents_guid.md
---

### Problem
Current skills and subagents are not bundled with the package. Prompts ship with pre-defined content in `src/dot_work/prompts/`, but skills and subagents must be manually created by users. This creates inconsistency in the user experience.

### Solution Implemented
Created `src/dot_work/bundled_skills/` and `src/dot_work/bundled_subagents/` directories with:
- `global.yml` files for default environment configs
- `.gitkeep` files with documentation
- Updated `pyproject.toml` to include directories in wheel artifacts

### Verification
- [x] `src/dot_work/bundled_skills/` directory created
- [x] `src/dot_work/bundled_subagents/` directory created
- [x] `global.yml` files created with proper structure
- [x] `pyproject.toml` updated to include package data
- [x] Build successfully includes the new directories
- [x] `importlib.resources` can access the new directories

### Notes
This is Phase 1 of 6 phases to align skills/subagents with prompts architecture.
Fixed CR-001@e8a3b2 (validation conflict with empty strings) as part of code review validation.
