---
id: "REFACTOR-002@c7g4c2"
title: "Add environment support to SKILL.md frontmatter"
description: "Phase 2: Enable environment-aware skill installation like prompts"
created: 2025-01-02
section: "skills"
tags: [skills, environments, phase-2, frontmatter]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/skills/models.py
  - src/dot_work/skills/parser.py
  - src/dot_work/skills/validator.py
---

### Problem
Skills currently lack the `environments:` frontmatter field that prompts have. This means skills can't be installed in an environment-aware way. Each environment would need the same skill manually, defeating the "write once, deploy everywhere" pattern.

### Affected Files
- `src/dot_work/skills/models.py` (add `SkillEnvironmentConfig` and `environments` field)
- `src/dot_work/skills/parser.py` (parse `environments:` from frontmatter)
- `src/dot_work/skills/validator.py` (validate environment configs)

### Importance
Adding environment support to skills enables:
- Single skill definition that works across environments
- Consistent installation flow with prompts
- Skills to be installed via `dot-work install` command
- Per-environment configuration (target paths, naming)

### Proposed Solution
**Phase 2 Tasks:**

1. Update `SkillMetadata` model to include `environments` field
2. Update `SkillParser` to parse `environments:` from SKILL.md frontmatter
3. Add `SkillEnvironmentConfig` dataclass (similar to `EnvironmentConfig` for prompts)
4. Update `SkillValidator` to validate environment configs
5. Create `skill_installer.py` with installation logic

**Model changes (`skills/models.py`):**
```python
@dataclass
class SkillEnvironmentConfig:
    """Environment-specific skill installation config."""
    target: str  # Target directory for this environment

@dataclass
class SkillMetadata:
    name: str
    description: str
    license: str | None = None
    compatibility: str | None = None
    metadata: dict[str, str] | None = None
    allowed_tools: list[str] | None = None
    environments: dict[str, SkillEnvironmentConfig] | None = None  # NEW
```

**Target SKILL.md format:**
```markdown
---
name: code-review
description: Expert code review guidelines.
license: MIT

environments:
  claude:
    target: ".claude/skills/"
  # Other environments don't support skills - skipped automatically
---

# Code Review Skill
[Skill content...]
```

### Acceptance Criteria
- [ ] `SkillEnvironmentConfig` dataclass created
- [ ] `SkillMetadata.environments` field added
- [ ] `SkillParser` parses `environments:` from frontmatter
- [ ] `SkillValidator` validates environment configs
- [ ] Tests for new functionality added
- [ ] Existing tests still pass

### Notes
This is Phase 2 of 6 phases.
Estimated effort: 4-6 hours.
Dependencies: Phase 1 (bundled_skills directory must exist).

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
status: proposed
references:
  - src/dot_work/installer.py
  - src/dot_work/skills/
  - src/dot_work/subagents/
---

### Problem
Currently `dot-work install` only handles prompts. Skills and subagents have separate workflows (`dot-work skills install`, `dot-work subagents sync`). This creates inconsistent user experience and prevents unified content installation.

### Affected Files
- `src/dot_work/installer.py` (add skill/subagent installation functions)
- `src/dot_work/environments.py` (add skill/subagent support flags)

### Importance
Unified installation enables:
- Single `dot-work install` command for all content types
- Consistent experience across prompts, skills, subagents
- Simpler onboarding for new users
- Atomic updates to all project content

### Proposed Solution
**Phase 3 Tasks:**

1. Create `get_bundled_skills_dir()` and `get_bundled_subagents_dir()` functions
2. Create `install_skills_by_environment()` function
3. Create `install_subagents_by_environment()` function
4. Update `install_prompts()` to also call skill/subagent installers
5. Handle environments that don't support skills/subagents (skip gracefully)

**New installer functions:**
```python
SKILL_SUPPORTED_ENVIRONMENTS = {"claude"}
SUBAGENT_SUPPORTED_ENVIRONMENTS = {"claude", "opencode", "copilot"}

def install_skills_by_environment(
    env_name: str,
    target: Path,
    skills_dir: Path,
    console: Console,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> int:
    """Install bundled skills for an environment.

    Returns number of skills installed, or 0 if environment doesn't support skills.
    """
    if env_name not in SKILL_SUPPORTED_ENVIRONMENTS:
        console.print(f"[dim]Skills not supported for {env_name}, skipping...[/dim]")
        return 0
    # Install skills...

def install_subagents_by_environment(
    env_name: str,
    target: Path,
    subagents_dir: Path,
    console: Console,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> int:
    """Install bundled subagents for an environment.

    If environment doesn't support native agents, treats subagents as prompts.
    """
    if env_name in SUBAGENT_SUPPORTED_ENVIRONMENTS:
        # Install as native agents
        ...
    else:
        # Install as prompts (fallback)
        ...
```

**Target installation flow:**
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

### Acceptance Criteria
- [ ] `get_bundled_skills_dir()` function created and working
- [ ] `get_bundled_subagents_dir()` function created and working
- [ ] `install_skills_by_environment()` function implemented
- [ ] `install_subagents_by_environment()` function implemented
- [ ] `install_prompts()` updated to call skill/subagent installers
- [ ] Unsupported environments are skipped gracefully
- [ ] Tests for unified installation flow
- [ ] Integration tests pass

### Notes
This is Phase 3 of 6 phases.
Estimated effort: 6-8 hours.
Dependencies: Phase 2 (skills must have environment support).

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
status: proposed
references:
  - src/dot_work/bundled_skills/
  - src/dot_work/bundled_subagents/
---

### Problem
After establishing the infrastructure (Phases 1-3), users will have empty bundled content directories. To provide immediate value, we need to create useful pre-defined skills and subagents that ship with the package.

### Affected Files
- `src/dot_work/bundled_skills/` (new skill directories)
- `src/dot_work/bundled_subagents/` (new subagent files)

### Importance
Bundled content provides:
- Immediate value upon installation
- Examples of best practices
- Core functionality most users need
- Reduced time-to-first-value

### Proposed Solution
**Phase 4 Tasks:**

1. Create initial bundled skills (code-review, debugging, etc.)
2. Create initial bundled subagents (code-reviewer, architect, etc.)
3. Each with proper `environments:` frontmatter
4. Validate all bundled content in CI

**Example bundled skill structure:**
```
src/dot_work/bundled_skills/code-review/
└── SKILL.md
```

**Example bundled subagent:**
```
src/dot_work/bundled_subagents/code-reviewer.md
```

**Initial skills to create:**
- `code-review` - Comprehensive code review guidelines
- `debugging` - Systematic debugging approaches
- `test-driven-development` - TDD workflow

**Initial subagents to create:**
- `code-reviewer` - Expert code reviewer (quality + security)
- `architect` - Software architecture design
- `debugger` - Root cause analysis specialist

### Acceptance Criteria
- [ ] At least 3 bundled skills created
- [ ] At least 3 bundled subagents created
- [ ] All content has valid frontmatter
- [ ] All content has `environments:` section
- [ ] CI validates all bundled content
- [ ] Content is tested via install command

### Notes
This is Phase 4 of 6 phases.
Estimated effort: 4-8 hours.
Dependencies: Phase 3 (installer must support skills/subagents).

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
status: proposed
references:
  - src/dot_work/skills/discovery.py
  - src/dot_work/subagents/discovery.py
---

### Problem
Current skills and subagents discovery searches user directories (`.skills/`, `~/.config/dot-work/skills/`). This differs from how prompts work - prompts are discovered from the bundled package directory. The inconsistency creates confusion.

### Affected Files
- `src/dot_work/skills/discovery.py` (default paths)
- `src/dot_work/subagents/discovery.py` (default paths)

### Importance
Aligning discovery behavior ensures:
- Consistent mental model across all content types
- Predictable behavior for users
- Clear separation: bundled (installed) vs user-created (development)
- Simpler maintenance

### Proposed Solution
**Phase 5 Tasks:**

1. Update `SkillDiscovery` default paths to use `get_bundled_skills_dir()`
2. Update `SubagentDiscovery` default paths to use `get_bundled_subagents_dir()`
3. Remove user-global paths (`~/.config/dot-work/skills/` etc.) from defaults
4. Keep project-local discovery available via explicit `--path` arguments

**Discovery behavior changes:**
- **Before:** `.skills/`, `~/.config/dot-work/skills/`
- **After:** `<package>/bundled_skills/`

**User-created content:**
- Still discoverable via explicit `--path` argument
- Not part of default install flow
- Separated concern: bundled vs development

### Acceptance Criteria
- [ ] `SkillDiscovery` uses `get_bundled_skills_dir()` by default
- [ ] `SubagentDiscovery` uses `get_bundled_subagents_dir()` by default
- [ ] User-global paths removed from defaults
- [ ] `--path` argument still works for user-created content
- [ ] Tests updated for new discovery behavior
- [ ] Documentation updated

### Notes
This is Phase 5 of 6 phases.
Estimated effort: 2-4 hours.
Dependencies: Phase 3 (installer must be complete).

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
status: proposed
references:
  - src/dot_work/cli.py
  - README.md
---

### Problem
After implementing Phases 1-5, the CLI and documentation will still refer to the old separate workflows. Users won't know about the unified installation capability.

### Affected Files
- `src/dot_work/cli.py` (help text, command descriptions)
- `README.md` (installation instructions)
- `skills_agents_guid.md` (update to reflect completed changes)

### Importance
Updated documentation ensures:
- Users discover the unified installation feature
- Clear migration path from old workflows
- Accurate examples and tutorials
- Reduced confusion

### Proposed Solution
**Phase 6 Tasks:**

1. Update `dot-work install` help text to mention skills/subagents
2. Add `--skip-skills` and `--skip-subagents` flags if needed
3. Update `dot-work list` to show skill/subagent support per environment
4. Update README and documentation
5. Add migration guide for existing users

**New help text example:**
```
Install AI coding prompts, skills, and subagents for your environment.

Examples:
  dot-work install --env claude         # Install all content types
  dot-work install --env claude --skip-skills  # Skip skills
  dot-work install --env cursor         # Cursor doesn't support skills/subagents
```

**Environment support matrix in list command:**
```
$ dot-work list

Environment: claude
  Prompts: ✓ Supported
  Skills: ✓ Supported
  Subagents: ✓ Supported

Environment: cursor
  Prompts: ✓ Supported
  Skills: ✗ Not supported
  Subagents: ✗ Treated as prompts
```

### Acceptance Criteria
- [ ] `dot-work install` help text mentions skills/subagents
- [ ] `--skip-skills` and `--skip-subagents` flags added (if needed)
- [ ] `dot-work list` shows content type support per environment
- [ ] README updated with unified installation examples
- [ ] Migration guide added for existing users
- [ ] skills_agents_guid.md updated to reflect current state

### Notes
This is Phase 6 of 6 phases - final phase.
Estimated effort: 2-4 hours.
Dependencies: Phase 5 (all implementation must be complete).
