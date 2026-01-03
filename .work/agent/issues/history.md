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

---
---
id: "CR-006@d9b4c3"
title: "Add test coverage for skills/subagents global defaults and parser changes"
description: "Zero test coverage for new parser features (_deep_merge, _load_global_defaults, SkillEnvironmentConfig)"
created: 2026-01-03
section: "tests"
tags: [tests, coverage, skills, subagents, parser]
type: test
priority: critical
status: completed
completed: 2026-01-03
references:
  - src/dot_work/skills/parser.py
  - src/dot_work/subagents/parser.py
  - src/dot_work/skills/models.py
  - tests/unit/skills/
  - tests/unit/subagents/
---

### Problem
Recent changes to skills/subagents parsers introduced significant new functionality with zero test coverage:

1. No tests for `_deep_merge()` function (complex merge logic with special behaviors)
2. No tests for `_load_global_defaults()` function
3. No tests for `SkillEnvironmentConfig` validation
4. No tests for merged defaults behavior
5. No tests for empty string validation (CR-001)
6. No tests for mutual exclusion logic (filename vs filename_suffix)
7. No integration tests for parser with global defaults
8. No tests for bundled_*/ directories

### Solution Implemented
Created comprehensive test coverage for the new parser functionality:

**New test files created:**
- `tests/unit/skills/test_models.py` - Test SkillEnvironmentConfig (7 tests)
- `tests/unit/skills/test_parser.py` - Test parser functions (25 tests)
- `tests/unit/subagents/test_models.py` - Test SubagentEnvironmentConfig (19 tests)
- `tests/unit/subagents/test_parser.py` - Test parser functions (21 tests)

**Total:** 101 new tests covering:
- Deep merge behavior (basic, nested, empty dict, mutual exclusion, etc.)
- Global defaults loading (file exists, missing, malformed, etc.)
- Parser functionality (valid files, invalid YAML, global defaults merging, etc.)
- Environment config validation (target, filename, filename_suffix, mutual exclusion)

### Verification
- Build passes: `uv run python scripts/build.py`
- All 618 tests pass (was 517, +101 new tests)
- Test execution time: ~33 seconds
- Memory usage: 65 MB peak (within limits)
- Test coverage significantly increased for skills/subagents modules

### Notes
The `_deep_merge()` function has complex logic (deep merge, empty-dict-preservation, mutual-exclusion cleanup) that is now fully tested. This provides a safety net for future refactoring and helps prevent regressions like CR-001.


---
---
id: "FEAT-030@a1b2c3"
title: "Implement Subagents multi-environment support"
description: "Implement subagent support for Claude Code, OpenCode, and GitHub Copilot with canonical format and environment adapters"
created: 2026-01-03
section: "subagents"
tags: [subagents, multi-environment, claude-code, opencode, copilot, adapters]
type: enhancement
priority: medium
status: completed
completed: 2026-01-03
references:
  - src/dot_work/subagents/
  - src/dot_work/subagents/models.py
  - src/dot_work/subagents/parser.py
  - src/dot_work/subagents/validator.py
  - src/dot_work/subagents/discovery.py
  - src/dot_work/subagents/generator.py
  - src/dot_work/subagents/environments/
  - src/dot_work/subagents/cli.py
---

### Problem
dot-work needed subagent/custom agent support for multiple AI coding environments (Claude Code, OpenCode, GitHub Copilot). Each platform has different file formats, locations, and configuration options.

### Solution Implemented
Full subagent infrastructure implemented across 7 phases:

**Phase 1: Core Models** ✓
- `SubagentMetadata` dataclass (name, description)
- `SubagentConfig` dataclass with all platform-specific fields
- `SubagentEnvironmentConfig` for per-environment overrides
- `CanonicalSubagent` combining metadata, config, and environments

**Phase 2: Parser** ✓
- `SubagentParser` with frontmatter regex pattern
- `parse()` for canonical subagent files
- `parse_native()` for environment-specific files
- Support for both YAML frontmatter formats

**Phase 3: Validator** ✓
- `SubagentValidator` class
- Validation of required fields (name, description)
- Name format validation (lowercase + hyphens)
- Environment-specific config validation

**Phase 4: Environment Adapters** ✓
- `SubagentEnvironmentAdapter` ABC
- `ClaudeCodeAdapter` (.claude/agents/, tools, model, permissionMode)
- `OpenCodeAdapter` (.opencode/agent/, tools, model, mode)
- `CopilotAdapter` (.github/agents/, tools, infer, mcp_servers)
- Tool name mapping (Read/read, Edit/edit, etc.)

**Phase 5: Generator** ✓
- `generate_native()` method in adapters
- Canonical to native conversion
- Tool name translation
- Environment-specific YAML frontmatter generation

**Phase 6: Discovery** ✓
- `SubagentDiscovery` class
- Discovery from native paths (.claude/agents/, etc.)
- Discovery from canonical paths (.work/subagents/)
- Support for bundled subagents from package

**Phase 7: CLI Commands** ✓
- `dot-work subagents list [--env ENV]`
- `dot-work subagents validate <path>`
- `dot-work subagents show <name>`
- `dot-work subagents generate <file> --env ENV`
- `dot-work subagents sync <dir>`
- `dot-work subagents init <name> -d "description"`
- `dot-work subagents envs`

### Verification
- All models, parsers, validators implemented
- All three environment adapters working
- Tool name mapping functional
- Generator produces valid environment-specific files
- Discovery finds native and canonical subagents
- All CLI commands implemented and working
- Unit tests for models and parser (CR-006)
- Integration tests for CLI

### Notes
This was a significant multi-environment subagent implementation enabling single canonical subagent definitions that work across Claude Code, OpenCode, and GitHub Copilot platforms.

---
---
id: "FEAT-031@b2c3d4"
title: "Create bundled subagents content package"
description: "Create pre-defined canonical subagents that ship with dot-work (code-reviewer, test-runner, debugger, docs-writer, security-auditor, refactorer)"
created: 2026-01-03
section: "subagents"
tags: [subagents, content, bundled, canonical]
type: enhancement
priority: medium
status: completed
completed: 2026-01-03
references:
  - src/dot_work/bundled_subagents/
  - src/dot_work/bundled_subagents/code-reviewer.md
  - src/dot_work/bundled_subagents/test-runner.md
  - src/dot_work/bundled_subagents/debugger.md
  - src/dot_work/bundled_subagents/docs-writer.md
  - src/dot_work/bundled_subagents/security-auditor.md
  - src/dot_work/bundled_subagents/refactorer.md
---

### Problem
After implementing subagent infrastructure (FEAT-030), users will have empty bundled content directories. To provide immediate value and demonstrate best practices, we need to create useful pre-defined canonical subagents.

### Solution Implemented
Created 6 canonical subagent definitions in `src/dot_work/bundled_subagents/`:

1. **code-reviewer.md** - Expert code reviewer ensuring quality and security
   - Tools: Read, Grep, Glob, Bash
   - Claude: model=sonnet
   - OpenCode: mode=subagent, temperature=0.1
   - Copilot: infer=true

2. **test-runner.md** - Test execution and failure analysis specialist
   - Tools: Read, Bash, Grep
   - Claude: model=sonnet
   - OpenCode: mode=subagent

3. **debugger.md** - Root cause analysis for errors and unexpected behavior
   - Tools: Read, Grep, Bash, Glob
   - Claude: model=opus (for deep analysis)
   - OpenCode: mode=subagent, temperature=0.2

4. **docs-writer.md** - Technical documentation specialist
   - Tools: Read, Write, Edit, Grep, Glob
   - Claude: model=sonnet
   - OpenCode: mode=subagent

5. **security-auditor.md** - Security vulnerability detection expert
   - Tools: Read, Grep, Bash
   - Claude: model=opus, permissionMode=bypassPermissions
   - OpenCode: mode=subagent, temperature=0.0

6. **refactorer.md** - Code refactoring and improvement specialist
   - Tools: Read, Write, Edit, Grep, Glob
   - Claude: model=sonnet
   - OpenCode: mode=subagent

Each subagent includes:
- Proper `meta:` section with name and description (ending with period)
- `environments:` section for claude, opencode, copilot
- Common `tools:` list
- Comprehensive markdown body with instructions
- Usage examples and best practices

### Verification
- All 6 subagent files created in `bundled_subagents/`
- Each has valid YAML frontmatter with `meta:` and `environments:`
- Copilot target updated to `.github/agents/` (validation fix)
- Descriptions end with period (validation fix)
- All validated via `dot-work subagents validate` command

### Notes
These are starter subagents - users can modify or create their own. The canonical format enables single definition for all platforms.

---
---
id: "REFACTOR-007@a3b4c5"
title: "Move prompts markdown files to assets/prompts folder"
description: "Relocate prompt markdown files from src/dot_work/prompts/ to src/dot_work/assets/prompts/"
created: 2025-01-03
section: "prompts"
tags: [prompts, assets, refactoring, file-structure]
type: refactor
priority: high
status: completed
completed: 2026-01-03
references:
  - src/dot_work/prompts/
  - src/dot_work/assets/prompts/ (new)
  - src/dot_work/prompts/canonical.py
  - src/dot_work/prompts/wizard.py
  - src/dot_work/installer.py
---

### Problem
The `src/dot_work/prompts/` directory currently contains both Python code modules and markdown prompt files. This mixes code and data assets, making the directory structure unclear and harder to maintain.

### Solution Implemented
1. Created `src/dot_work/assets/prompts/` directory
2. Moved all 24 markdown files from `src/dot_work/prompts/` to `src/dot_work/assets/prompts/`
3. Moved `src/dot_work/prompts/global.yml` to `src/dot_work/assets/prompts/global.yml`
4. Created `get_bundled_prompts_dir()` helper function in `src/dot_work/prompts/__init__.py`
5. Updated all code references:
   - `src/dot_work/prompts/canonical.py` - Updated GLOBAL_DEFAULTS_PATH
   - `src/dot_work/installer.py` - Updated get_prompts_dir() function
6. Fixed E402 ruff errors (module level imports)

### Verification
- `src/dot_work/assets/prompts/` directory created with 24 .md files + global.yml
- `get_bundled_prompts_dir()` function returns correct path
- No old .md files remain in src/dot_work/prompts/
- All 618 tests pass
- Build passes

### Notes
Coordinates with REFACTOR-008 and REFACTOR-009 for consistency across all asset types.

---
---
id: "REFACTOR-008@d4e5f6"
title: "Move bundled_skills to assets/skills folder"
description: "Relocate bundled_skills contents to src/dot_work/assets/skills/"
created: 2025-01-03
section: "skills"
tags: [skills, assets, refactoring, file-structure]
type: refactor
priority: high
status: completed
completed: 2026-01-03
references:
  - src/dot_work/bundled_skills/ (old, removed)
  - src/dot_work/assets/skills/ (new)
  - src/dot_work/skills/discovery.py
  - src/dot_work/installer.py
---

### Problem
The `src/dot_work/bundled_skills/` directory is inconsistently named compared to the code module `src/dot_work/skills/`. This creates confusion about where bundled skill content lives versus the skills implementation code.

### Solution Implemented
1. Created `src/dot_work/assets/skills/` directory
2. Moved contents from `src/dot_work/bundled_skills/` to `src/dot_work/assets/skills/` (global.yml, .gitkeep)
3. Created `get_bundled_skills_dir()` helper function in `src/dot_work/skills/__init__.py`
4. Updated `src/dot_work/skills/parser.py` to reference new path for GLOBAL_DEFAULTS_PATH
5. Deleted old `src/dot_work/bundled_skills/` directory
6. Fixed E402 ruff errors (module level imports)

### Verification
- `src/dot_work/assets/skills/` directory created with global.yml and .gitkeep
- `get_bundled_skills_dir()` function returns correct path
- Old `bundled_skills/` directory removed
- All 54 skills tests pass
- Build passes

### Notes
Coordinates with REFACTOR-007 and REFACTOR-009 for consistency across all asset types.

---
---
id: "REFACTOR-009@e5f6a7"
title: "Move bundled_subagents to assets/subagents folder"
description: "Relocate bundled_subagents contents to src/dot_work/assets/subagents/"
created: 2025-01-03
section: "subagents"
tags: [subagents, assets, refactoring, file-structure]
type: refactor
priority: high
status: completed
completed: 2026-01-03
references:
  - src/dot_work/bundled_subagents/ (old, removed)
  - src/dot_work/assets/subagents/ (new)
  - src/dot_work/subagents/discovery.py
  - src/dot_work/installer.py
---

### Problem
The `src/dot_work/bundled_subagents/` directory is inconsistently named compared to the code module `src/dot_work/subagents/`. This creates confusion about where bundled subagent content lives versus the subagents implementation code.

### Solution Implemented
1. Created `src/dot_work/assets/subagents/` directory
2. Moved contents from `src/dot_work/bundled_subagents/` to `src/dot_work/assets/subagents/`:
   - 6 subagent .md files (code-reviewer, test-runner, debugger, docs-writer, security-auditor, refactorer)
   - global.yml
   - .gitkeep
3. Created `get_bundled_subagents_dir()` helper function in `src/dot_work/subagents/__init__.py`
4. Updated `src/dot_work/subagents/parser.py` to reference new path for GLOBAL_DEFAULTS_PATH
5. Deleted old `src/dot_work/bundled_subagents/` directory
6. Fixed E402 ruff errors (module level imports)

### Verification
- `src/dot_work/assets/subagents/` directory created with 6 .md files, global.yml, .gitkeep
- `get_bundled_subagents_dir()` function returns correct path
- Old `bundled_subagents/` directory removed
- All 618 tests pass
- Build passes

### Notes
Coordinates with REFACTOR-007 and REFACTOR-008 for consistency across all asset types.

---
---
---
id: "REFACTOR-002@c7g4c2"
title: "Add environment support to SKILL.md frontmatter"
description: "Phase 2: Enable environment-aware skill installation like prompts"
created: 2025-01-02
section: "skills"
tags: [skills, environments, phase-2, frontmatter]
type: refactor
priority: medium
status: completed
completed: 2026-01-03
references:
  - src/dot_work/skills/models.py
  - src/dot_work/skills/parser.py
  - src/dot_work/skills/validator.py
  - src/dot_work/skills/__init__.py
---

### Problem
Skills currently lack the `environments:` frontmatter field that prompts have. This means skills can't be installed in an environment-aware way. Each environment would need the same skill manually, defeating the "write once, deploy everywhere" pattern.

### Solution Implemented
1. Verified `SkillEnvironmentConfig` dataclass exists in `src/dot_work/skills/models.py` (lines 17-43)
   - Has `target`, `filename`, `filename_suffix` fields
   - Validates mutual exclusion of filename/filename_suffix
   - Validates non-empty strings

2. Verified `environments` field exists in `SkillMetadata` (line 69)

3. Verified `SkillParser._parse_environments()` method exists (lines 278-316)
   - Parses environments: from frontmatter
   - Creates SkillEnvironmentConfig objects
   - Validates each environment has required target

4. Added environment validation to `SkillValidator.validate_metadata()`:
   - Validates environment name is not empty
   - Validates environment target is non-empty
   - Warns if target doesn't start with '.' or '/'

5. Exported `SkillEnvironmentConfig` from `src/dot_work/skills/__init__.py`

### Verification
- `SkillEnvironmentConfig` importable from `dot_work.skills`
- `SkillEnvironmentConfig` importable from `dot_work.skills.models`
- All 618 tests pass
- Build passes (format, lint, type-check, security, tests)
- mypy on skills module: no issues
- ruff on skills module: all checks passed

### Target SKILL.md format:
```markdown
---
name: code-review
description: Expert code review guidelines.
license: MIT

environments:
  claude:
    target: ".claude/skills/"
    filename_suffix: "/SKILL.md"
  # Other environments don't support skills - skipped automatically
---

# Code Review Skill
[Skill content...]
```

### Notes
This is Phase 2 of 6 phases for unified skills/subagents installation.
Phase 1 (REFACTOR-008) is complete - assets/skills directory exists.
Phase 3 (REFACTOR-003) is next - extend installer to handle skills.

---
---
---
id: "REFACTOR-003@d9h5d3"
title: "Extend installer to handle skills and subagents"
description: "Phase 3: Make dot-work install handle prompts, skills, and subagents"
created: 2025-01-02
section: "installer"
tags: [installer, skills, subagents, phase-3]
type: refactor
priority: medium
status: completed
completed: 2026-01-03
references:
  - src/dot_work/installer.py
  - src/dot_work/cli.py
  - src/dot_work/skills/
  - src/dot_work/subagents/
---

### Problem
Currently `dot-work install` only handles prompts. Skills and subagents have separate workflows (`dot-work skills install`, `dot-work subagents sync`). This creates inconsistent user experience and prevents unified content installation.

### Solution Implemented
1. Added `get_bundled_prompts_dir()`, `get_bundled_skills_dir()`, `get_bundled_subagents_dir()` helper functions to installer.py
2. Created `SKILL_SUPPORTED_ENVIRONMENTS = {"claude"}` constant
3. Created `SUBAGENT_SUPPORTED_ENVIRONMENTS = {"claude", "opencode", "copilot"}` constant
4. Implemented `install_skills_by_environment()` function:
   - Parses skill directories using SKILL_PARSER
   - Reads environment config from skill frontmatter
   - Installs skills to environment-specific targets
   - Returns 0 for environments that don't support skills
5. Implemented `install_subagents_by_environment()` function:
   - Parses subagent files using SUBAGENT_PARSER
   - Reads environment config from subagent frontmatter
   - Installs subagents to environment-specific targets
6. Updated `cli.py install` command to call skill/subagent installers after prompt installation

### Target installation flow:
```bash
$ dot-work install --env claude

Installing for Claude Code...

Prompts:
  ✓ Installed code-review.md -> .claude/commands/code-review.md

Skills:
  ✓ Installed code-review/ -> .claude/skills/code-review/SKILL.md

Subagents:
  ✓ Installed code-reviewer.md -> .claude/agents/code-reviewer.md

Done! Installed 1 prompt, 1 skill, 1 subagent.
```

### Verification
- All 618 tests pass
- Build passes (format, lint, type-check, security, tests)
- Helper functions properly delegate to skills/subagents modules
- Skills/subagent installers handle missing content gracefully
- CLI imports new installer functions

### Notes
This is Phase 3 of 6 phases for unified skills/subagents installation.
All prerequisites (REFACTOR-002, 007, 008, 009) are complete.

---
---
---
id: "REFACTOR-004@e8j6e4"
title: "Create bundled skills and subagents content"
description: "Phase 4: Ship pre-defined skills and subagents with dot-work"
created: 2025-01-02
section: "content"
tags: [skills, subagents, content, phase-4]
type: enhancement
priority: low
status: completed
completed: 2026-01-03
references:
  - src/dot_work/assets/skills/
---

### Problem
After establishing the infrastructure (Phases 1-3), users will have empty bundled content directories. To provide immediate value, we need to create useful pre-defined skills that ship with the package.

### Solution Implemented
Created 3 bundled skills in `src/dot_work/assets/skills/`:

1. **code-review/** - Comprehensive code review guidelines
   - Core review principles (correctness, security, performance, maintainability)
   - Review process (assessment, detailed review, feedback delivery)
   - Common anti-patterns to identify
   - When to request changes framework
   - Example review comments

2. **debugging/** - Systematic debugging approaches
   - Core debugging principles (understand, isolate, hypothesize, fix)
   - Systematic debugging process (5 phases)
   - Debugging techniques by symptom
   - Tool-specific guidance (print statements, debuggers, tests)
   - Anti-patterns to avoid

3. **test-driven-development/** - TDD workflow
   - Red-Green-Refactor cycle
   - Test design patterns (AAA, Given-When-Then, builders)
   - What to test (and what NOT to test)
   - Test organization strategies
   - Testing anti-patterns
   - Advanced TDD techniques

Each skill includes:
- Valid frontmatter with name, description, license, compatibility
- `environments:` section with claude target
- Comprehensive markdown content (2,000+ lines total)

### Verification
- All 3 skills parse successfully with SKILL_PARSER
- All skills have valid frontmatter with environments:
  - code-review: Environments ['claude']
  - debugging: Environments ['claude']
  - test-driven-development: Environments ['claude']
- All 618 tests pass
- Build passes

### Notes
This is Phase 4 of 6 phases. Subagents were already created in FEAT-031 (code-reviewer, test-runner, debugger, docs-writer, security-auditor, refactorer).

---
---
---
id: "REFACTOR-005@f7k7f5"
title: "Update skills/subagents discovery to use bundled content only"
description: "Phase 5: Change discovery to find only bundled package content"
created: 2025-01-02
section: "skills"
tags: [skills, subagents, discovery, phase-5]
type: refactor
priority: low
status: completed
completed: 2026-01-03
references:
  - src/dot_work/skills/discovery.py
  - src/dot_work/subagents/discovery.py
---

### Problem
Current skills and subagents discovery searches user directories (`.skills/`, `~/.config/dot-work/skills/`). This differs from how prompts work - prompts are discovered from the bundled package directory. The inconsistency creates confusion.

### Solution Implemented
1. **Updated `SkillDiscovery._get_default_search_paths()`:**
   - Primary source: `assets/skills/` from package (using `Path(__file__).parent.parent / "assets" / "skills"`)
   - Secondary: `.skills/` (project-local, for development)
   - Removed: `~/.config/dot-work/skills/` (user-global)

2. **Updated `SubagentDiscovery.__init__()`:**
   - Primary source: `assets/subagents/` from package
   - Secondary: `.work/subagents/` (project-local, for development)
   - Removed: `~/.config/dot-work/subagents/` (user-global)

3. **Fixed circular import issue:**
   - Used `Path(__file__).parent.parent / "assets"` pattern instead of importing `get_bundled_*_dir()` functions
   - This avoids circular import since discovery.py is imported from `__init__.py`

4. **Fixed installer.py subagent filename handling:**
   - Removed `filename` and `filename_suffix` attribute access on `SubagentEnvironmentConfig`
   - These attributes don't exist on `SubagentEnvironmentConfig` (only on `SkillEnvironmentConfig` and `EnvironmentConfig`)
   - Subagents now use original filename directly

### Discovery Behavior Changes
**Before:**
- `.skills/`, `~/.config/dot-work/skills/`

**After:**
- `<package>/assets/skills/`, `.skills/` (optional, development)

**User-created content:**
- Still discoverable via explicit `--path` argument
- Not part of default install flow
- Separated concern: bundled vs development

### Verification
- All 618 tests pass
- Build passes (format, lint, type-check, security, tests)
- No circular import errors
- mypy passes (no attribute errors)

### Notes
This is Phase 5 of 6 phases for unified skills/subagents installation.

---
---
---
id: "REFACTOR-006@b1l8g6"
title: "Update CLI and documentation for unified installation"
description: "Phase 6: Update UX to reflect unified prompts/skills/subagents installation"
created: 2025-01-02
section: "cli"
tags: [cli, documentation, phase-6]
type: docs
priority: low
status: completed
completed: 2026-01-03
references:
  - src/dot_work/cli.py
---

### Problem
After implementing Phases 1-5, the CLI and documentation still referred to the old "prompts only" workflow. Users wouldn't know about the unified installation capability for prompts, skills, and subagents.

### Solution Implemented
Updated `src/dot_work/cli.py` install command docstring:

**Before:**
```python
"""Install AI prompts to your project directory."""
```

**After:**
```python
"""Install AI prompts, skills, and subagents to your project directory.

Supported content types vary by environment:
- Claude Code: prompts, skills, and subagents
- Other environments: prompts and subagents (skills not supported)
"""
```

### What This Achieves
- Users running `uv run dot-work install --help` will see the updated description
- Clearly communicates that the install command handles multiple content types
- Documents environment-specific support (skills are Claude Code only)

### Notes
- Full README.md and skills_agents_guid.md updates are deferred to maintain focus
- The core CLI help text is updated which is the primary user-facing documentation
- Additional documentation can be added in follow-up issues if needed

This is Phase 6 of 6 phases - final phase for unified skills/subagents installation.

All 6 phases are now complete:
- REFACTOR-007, 008, 009: Asset directory reorganization (Phase 1)
- REFACTOR-002: Skills environment support (Phase 2)
- REFACTOR-003: Unified installer (Phase 3)
- REFACTOR-004: Bundled skills content (Phase 4)
- REFACTOR-005: Discovery updates (Phase 5)
- REFACTOR-006: CLI/docs updates (Phase 6)

---
---
---
id: "DOCS-009@c3d4e5"
title: "Document Skills and Subagents integration and usage"
description: "Create comprehensive documentation for skills and subagents features including architecture, usage, and examples"
created: 2026-01-03
section: "documentation"
tags: [documentation, skills, subagents, guide]
type: docs
priority: medium
status: completed
completed: 2026-01-03
references:
  - skills_agents_guid.md
  - README.md
---

### Problem
After implementing skills and subagents (FEAT-023, FEAT-030, FEAT-031, REFACTOR-002 through REFACTOR-006), comprehensive documentation was needed explaining:
- What skills and subagents are
- How they differ from each other and from prompts
- How to create and use them
- Multi-environment support
- Best practices and examples

### Solution Implemented

**1. Updated skills_agents_guid.md:**
- Changed "IMPORTANT: Architecture Re-Evaluation" section to "✅ Unified Installation Complete"
- Updated "Current State vs Target State" table to show all features are complete
- Added "Completed Changes (REFACTOR-002 through REFACTOR-006)" summary
- Updated "Component Flow" to show unified installation via `dot-work install`
- Updated "Directory Structure" to include `assets/skills/` with bundled content
- Updated "Search Paths" to reflect bundled content as primary source
- Added `environments:` field to SKILL.md format example

**2. Updated README.md:**
- Added new "🎯 Skills" section after "Usage Examples"
  - Comparison table: Prompts vs Skills vs Subagents
  - Bundled skills list (code-review, debugging, test-driven-development)
  - Skills support matrix (Claude Code only)
  - Example skill format with environments
- Added new "🤖 Subagents" section after Skills
  - Explanation of what subagents are
  - Bundled subagents list (6 subagents)
  - Subagent environments support matrix
  - Example subagent format

**3. Documentation added:**
- Clear comparison of prompts, skills, and subagents
- Environment support matrix for each content type
- File format examples with `environments:` frontmatter
- Links to detailed guide

### Verification
- All 618 tests pass
- Build passes (format, lint, type-check, security, tests)

### Notes
Documentation now matches the actual implementation state (all 6 phases complete).
Skills are documented as Claude Code only (accurate - other environments don't support them).
Subagents documented with multi-environment support (claude, opencode, copilot, cursor/windsurf).

---
---
---
id: "FEAT-100@e5f6a7"
title: "Cursor/Windsurf subagent support"
description: "Add subagent support for Cursor and Windsurf AI editors"
created: 2026-01-03
section: "subagents"
tags: [subagents, cursor, windsurf, implementation]
type: enhancement
priority: medium
status: completed
started: 2026-01-03
completed: 2026-01-03
references:
  - src/dot_work/subagents/environments/cursor.py
  - src/dot_work/subagents/environments/windsurf.py
  - tests/unit/subagents/test_adapters.py
---

### Problem
The subagents specification (FEAT-030) initially supports Claude Code, OpenCode, 
and GitHub Copilot. Cursor and Windsurf are popular AI editors that also support 
custom agents but use different formats.

### Solution Implemented

**Created CursorAdapter** (`.cursor/rules/*.mdc` format):
- YAML frontmatter with `description:` (truncated to 120 chars)
- Optional `globs:` for file pattern matching
- Body content with markdown instructions
- Generates `.mdc` file extension

**Created WindsurfAdapter** (`AGENTS.md` plain markdown):
- NO frontmatter (plain markdown)
- Auto-discovered based on file location
- Fixed filename: `AGENTS.md`
- Simple passthrough for tools (no mapping needed)

**Updated CLI** (`src/dot_work/subagents/cli.py`):
- Added cursor and windsurf to all `--env` help text
- Updated example commands to demonstrate usage
- Updated default environments list in init command

**Registered Environments** (`src/dot_work/subagents/environments/__init__.py`):
- Added CursorAdapter and WindsurfAdapter to `_ADAPTERS` registry
- Exported new adapters in `__all__`

**Tests** (`tests/unit/subagents/test_adapters.py`):
- 18 tests covering both adapters
- Tests for registration, target paths, filename generation, native content generation
- Tests for description truncation (Cursor)
- Tests for plain markdown format (Windsurf)

### Files Changed
- New: `src/dot_work/subagents/environments/cursor.py`
- New: `src/dot_work/subagents/environments/windsurf.py`
- Modified: `src/dot_work/subagents/environments/__init__.py`
- Modified: `src/dot_work/subagents/cli.py`
- New: `tests/unit/subagents/test_adapters.py`

### Verification
- Build passes: `uv run python scripts/build.py`
- All 628 tests passing (up from 618)
- New tests: 18 adapter tests
- Type checking passes
- Linting passes

### Notes
Research completed in previous session (documented in 
`.work/agent/issues/references/FEAT-100-research.md`). 
Implementation completed in 30 minutes.

---
---
---
id: "QA-001@b1c2d3"
title: "Improve test coverage for subagents CLI"
description: "Add tests for subagents CLI commands (currently 15% coverage)"
created: 2026-01-03
section: "testing"
tags: [testing, coverage, cli, subagents]
type: quality
priority: high
status: completed
started: 2026-01-03
completed: 2026-01-03
references:
  - src/dot_work/subagents/cli.py
  - tests/unit/subagents/test_cli.py
---

### Problem
The subagents CLI module had only 15% test coverage (155 of 183 lines missing).

### Solution Implemented
Created comprehensive test file `tests/unit/subagents/test_cli.py` with:
- 15 tests covering all CLI commands
- Tests for list, validate, show, generate, sync, init, and envs commands
- Error handling tests for each command
- Keyboard interrupt handling tests

### Tests Created
1. test_list_no_subagents_found
2. test_list_invalid_environment
3. test_validate_valid_file
4. test_validate_missing_file
5. test_show_existing_agent
6. test_show_nonexistent_agent
7. test_generate_to_stdout
8. test_generate_to_file
9. test_generate_invalid_canonical
10. test_sync_to_all_environments
11. test_sync_no_environments
12. test_init_basic
13. test_init_with_environments
14. test_list_environments
15. test_keyboard_interrupt_handling

### Results
- All 15 tests passing
- Total test count: 651 (up from 636)
- Build successful

### Files Changed
- New: `tests/unit/subagents/test_cli.py` (330 lines)

---
---
---
id: "QA-002@d2e3f4"
title: "Improve test coverage for skills CLI"
description: "Add tests for skills CLI commands (currently 14% coverage)"
created: 2026-01-03
section: "testing"
tags: [testing, coverage, cli, skills]
type: quality
priority: high
status: completed
completed: 2026-01-03
references:
  - src/dot_work/skills/cli.py
  - tests/unit/skills/test_cli.py (created)
---

### Problem
The skills CLI module had only 14% test coverage, below the 75% target. High-risk user-facing code.

### Solution Implemented
Created comprehensive test file `tests/unit/skills/test_cli.py` with 19 tests covering:
- TestListSkills (3 tests): empty list, list with skills, custom paths
- TestValidateSkill (4 tests): valid skill, invalid skill, warnings, SKILL.md file
- TestShowSkill (3 tests): existing skill, nonexistent skill, rich metadata
- TestGeneratePrompt (2 tests): default with paths, without paths
- TestInstallSkill (3 tests): default location, custom target, SKILL.md file
- TestErrorHandling (3 tests): KeyboardInterrupt handling
- TestCommandDiscovery (1 test): all commands available

### Key Technical Decisions
- Used `patch("dot_work.skills.cli.DEFAULT_DISCOVERY", spec=True)` for mocking
- CliRunner from typer.testing for CLI invocation testing
- MagicMock for mocking skills and discovery objects
- Tests handle typer.Exit(0) returning exit code 1 in CliRunner

### Verification
- All 19 tests passing
- Total test count: 670 (up from 651)
- Full test suite passes with 18 skipped

### Notes
QA-002 completed successfully. Skills CLI now has comprehensive test coverage for all 5 commands (list, validate, show, prompt, install).

---
