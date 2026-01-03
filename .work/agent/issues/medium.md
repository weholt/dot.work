# Medium Priority Issues (P2)

Enhancements, technical debt.

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
status: proposed
references:
  - src/dot_work/subagents/ (new)
  - src/dot_work/subagents/models.py (new)
  - src/dot_work/subagents/parser.py (new)
  - src/dot_work/subagents/validator.py (new)
  - src/dot_work/subagents/discovery.py (new)
  - src/dot_work/subagents/generator.py (new)
  - src/dot_work/subagents/environments/ (new)
---

### Problem
dot-work needs subagent/custom agent support for multiple AI coding environments (Claude Code, OpenCode, GitHub Copilot). Each platform has different file formats, locations, and configuration options for custom agents. Currently there is no unified way to define and deploy subagents across these environments.

### Affected Files
- **New directory**: `src/dot_work/subagents/`
- **New files**: models.py, parser.py, validator.py, discovery.py, generator.py
- **New subdirectory**: environments/ (base.py, claude_code.py, opencode.py, copilot.py)
- **Modify**: src/dot_work/cli.py (add subagents commands)
- **Modify**: src/dot_work/installer.py (subagent installation)

### Importance
Multi-environment subagent support enables:
- Single canonical subagent definition that works across platforms
- Consistent subagent deployment workflow
- Tool name and model translation between environments
- Per-environment configuration (permissions, model selection)
- Reduced duplication when supporting multiple AI coding tools

### Proposed Solution

**Phase 1: Core Models (1-2 days)**
1. Create `SubagentMetadata` dataclass (name, description)
2. Create `SubagentConfig` dataclass with all platform-specific fields:
   - tools, model, permission_mode, permissions
   - OpenCode: mode, temperature, max_steps
   - Claude Code: skills
   - Copilot: target, infer, mcp_servers
3. Implement validation in `__post_init__`

**Phase 2: Parser (1 day)**
1. Create `SubagentParser` with frontmatter regex pattern
2. Implement `parse()` for canonical subagent files
3. Implement `parse_native()` for environment-specific files
4. Support both YAML frontmatter formats

**Phase 3: Validator (1 day)**
1. Create `SubagentValidator` class
2. Validate required fields (name, description)
3. Validate name format (lowercase + hyphens)
4. Validate environment-specific configs

**Phase 4: Environment Adapters (2-3 days)**
1. Create `SubagentEnvironmentAdapter` ABC
2. Implement `ClaudeCodeAdapter`:
   - Target: `.claude/agents/`
   - Tools: comma-separated list
   - Model: sonnet/opus/haiku/inherit
   - Permission modes: default/acceptEdits/bypassPermissions/plan
3. Implement `OpenCodeAdapter`:
   - Target: `.opencode/agent/`
   - Tools: boolean map or wildcards
   - Model: provider/model-id format
   - Modes: primary/subagent/all
4. Implement `CopilotAdapter`:
   - Target: `.github/agents/`
   - Tools: string list with aliases
   - Support: infer, mcp_servers
5. Implement tool name mapping (Read/read, Edit/edit, etc.)

**Phase 5: Generator (1-2 days)**
1. Create `generate_native()` method in adapters
2. Implement canonical to native conversion
3. Handle tool name translation
4. Generate environment-specific YAML frontmatter

**Phase 6: Discovery (1 day)**
1. Create `SubagentDiscovery` class
2. Discover from native paths (`.claude/agents/`, etc.)
3. Discover from canonical paths (`.work/subagents/`)
4. Support bundled subagents from package

**Phase 7: CLI Commands (1-2 days)**
Add `subagents` subcommand group:
- `dot-work subagents list [--env ENV]`
- `dot-work subagents validate <path>`
- `dot-work subagents show <name>`
- `dot-work subagents install <file> --env ENV`
- `dot-work subagents generate <file> --env ENV`
- `dot-work subagents sync <dir>`
- `dot-work subagents init <name> -d "description"`
- `dot-work subagents envs`

**Canonical format example:**
```markdown
---
meta:
  name: code-reviewer
  description: Expert code reviewer for quality and security.

environments:
  claude:
    target: ".claude/agents/"
    model: sonnet
    permissionMode: default
    skills:
      - code-review

  opencode:
    target: ".opencode/agent/"
    mode: subagent
    temperature: 0.1

  copilot:
    target: ".github/agents/"
    infer: true

tools:
  - Read
  - Grep
  - Glob
  - Bash
---

You are a senior code reviewer...
```

### Acceptance Criteria
- [ ] `SubagentMetadata` and `SubagentConfig` dataclasses created
- [ ] `SubagentParser` parses canonical and native formats
- [ ] `SubagentValidator` validates all field types
- [ ] Three environment adapters implemented (Claude, OpenCode, Copilot)
- [ ] Tool name mapping works correctly for all environments
- [ ] `generate_native()` produces valid environment-specific files
- [ ] `SubagentDiscovery` finds native and canonical subagents
- [ ] All CLI commands implemented and working
- [ ] Unit tests for all modules (≥75% coverage)
- [ ] Integration tests for cross-platform generation
- [ ] Test fixtures for valid/invalid subagents

### Notes
- Skills and subagents are complementary features
- Skills: reusable capability packages (instructions + scripts + references)
- Subagents: AI personalities with tool/permission configurations
- Claude Code supports auto-loading skills in subagents via `skills` field
- Estimated total effort: 8-12 days
- Dependencies: None (can be implemented independently)

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
status: proposed
references:
  - src/dot_work/bundled_subagents/ (new)
  - src/dot_work/subagents/discovery.py
---

### Problem
After implementing subagent infrastructure (FEAT-030), users will have empty bundled content directories. To provide immediate value and demonstrate best practices, we need to create useful pre-defined canonical subagents.

### Affected Files
- **New directory**: `src/dot_work/bundled_subagents/`
- **New files**: code-reviewer.md, test-runner.md, debugger.md, docs-writer.md, security-auditor.md, refactorer.md

### Importance
Bundled subagents provide:
- Immediate value upon installation
- Examples of canonical format best practices
- Core functionality most users need
- Reduced time-to-first-value
- Multi-environment deployment examples

### Proposed Solution
Create 6 canonical subagent definitions with `environments:` frontmatter for all supported platforms:

1. **code-reviewer.md**
   - Description: Expert code reviewer ensuring quality and security
   - Tools: Read, Grep, Glob, Bash
   - Claude: model=sonnet, skills=[code-review]
   - OpenCode: mode=subagent, temperature=0.1
   - Copilot: infer=true
   - Focus: Clarity, security vulnerabilities, performance, test coverage

2. **test-runner.md**
   - Description: Test execution and failure analysis specialist
   - Tools: Read, Bash, Grep
   - Claude: model=sonnet
   - OpenCode: mode=subagent
   - Focus: Run tests, analyze failures, suggest fixes

3. **debugger.md**
   - Description: Root cause analysis for errors and unexpected behavior
   - Tools: Read, Grep, Bash, Glob
   - Claude: model=opus (for deep analysis)
   - OpenCode: mode=subagent, temperature=0.2
   - Focus: Systematic debugging, log analysis, reproduction steps

4. **docs-writer.md**
   - Description: Technical documentation specialist
   - Tools: Read, Write, Edit
   - Claude: model=sonnet
   - OpenCode: mode=subagent
   - Focus: Clear, comprehensive documentation, API docs, guides

5. **security-auditor.md**
   - Description: Security vulnerability detection expert
   - Tools: Read, Grep, Bash
   - Claude: model=opus, permissionMode=bypassPermissions
   - OpenCode: mode=subagent, temperature=0.0
   - Focus: OWASP top 10, input validation, authentication, authorization

6. **refactorer.md**
   - Description: Code refactoring and improvement specialist
   - Tools: Read, Write, Edit, Grep, Glob
   - Claude: model=sonnet
   - OpenCode: mode=subagent
   - Focus: Code clarity, deduplication, patterns, maintainability

Each subagent should include:
- Proper `meta:` section with name and description
- `environments:` section for claude, opencode, copilot
- Common `tools:` list
- Markdown body with clear instructions
- Usage examples

### Acceptance Criteria
- [ ] 6 canonical subagent files created in `bundled_subagents/`
- [ ] Each has valid YAML frontmatter with `meta:` and `environments:`
- [ ] Each has clear markdown body with instructions
- [ ] Claude Code environment configured for all
- [ ] OpenCode environment configured for all
- [ ] Copilot environment configured for all
- [ ] Tool lists are appropriate for each subagent's purpose
- [ ] CI validation passes for all bundled subagents
- [ ] Tested via `dot-work subagents install` command

### Notes
- These are starter subagents - users can modify or create their own
- Canonical format enables single definition for all platforms
- Estimated effort: 4-6 hours
- Dependencies: FEAT-030 (subagent infrastructure must be complete)

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
status: proposed
references:
  - skills_agents_guid.md (update)
  - README.md (update)
  - docs/ (potential new directory)
---

### Problem
After implementing skills and subagents (FEAT-023, FEAT-030, FEAT-031), there needs to be comprehensive documentation explaining:
- What skills and subagents are
- How they differ from each other and from prompts
- How to create and use them
- Multi-environment support
- Best practices and examples

### Affected Files
- `skills_agents_guid.md` (update with current implementation state)
- `README.md` (add skills/subagents sections)
- Potential new: `docs/skills.md`, `docs/subagents.md`

### Importance
Good documentation ensures:
- Users understand when to use skills vs subagents vs prompts
- Clear mental model for the three content types
- Successful adoption of features
- Reduced support burden
- Community contributions

### Proposed Solution

**1. Update skills_agents_guid.md**
- Remove "proposed" language, features are implemented
- Add current architecture documentation
- Document actual file paths and module structure
- Add examples from bundled content
- Document CLI commands with real output
- Add troubleshooting section

**2. Update README.md**
- Add "Skills" section explaining:
  - What skills are (capability packages)
  - How to use bundled skills
  - How to create custom skills
- Add "Subagents" section explaining:
  - What subagents are (AI personalities)
  - Multi-environment support
  - How to use bundled subagents
  - How to create custom subagents
- Add comparison table: Prompts vs Skills vs Subagents

**3. Create detailed guides (if needed)**
- `docs/skills.md` - Complete skills guide
- `docs/subagents.md` - Complete subagents guide
- `docs/multi-env.md` - Multi-environment deployment

**Content to cover:**
- Architecture diagrams (text-based)
- File structure examples
- YAML frontmatter reference
- CLI command reference
- Environment-specific behaviors
- Tool name mappings
- Best practices
- Common patterns

### Acceptance Criteria
- [ ] skills_agents_guid.md updated to reflect implementation
- [ ] README.md has skills and subagents sections
- [ ] Clear comparison of prompts/skills/subagents
- [ ] CLI commands documented with examples
- [ ] Multi-environment support explained
- [ ] Environment-specific behaviors documented
- [ ] Best practices and examples included
- [ ] Troubleshooting section added

### Notes
- Skills and subagents are complementary, not competing features
- Documentation should match actual implementation, not the spec
- Use real examples from bundled content
- Estimated effort: 4-6 hours
- Dependencies: FEAT-023, FEAT-030, FEAT-031 (features should be implemented first)

---
