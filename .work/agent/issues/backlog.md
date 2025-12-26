# Backlog

Untriaged ideas and future work.

---

---
id: "FEAT-023@a7b3c9"
title: "Implement Agent Skills support per agentskills.io specification"
description: "Add skills discovery, parsing, validation, and prompt generation for agent capabilities"
created: 2025-12-26
section: "skills"
tags: [feature, agent-skills, discovery, prompts, progressive-disclosure]
type: enhancement
priority: medium
status: proposed
references:
  - .work/agent/issues/references/skills_spec.md
  - src/dot_work/prompts/canonical.py
  - src/dot_work/harness/
---

### Problem
dot-work currently supports prompts for static instructions but lacks support for [Agent Skills](https://agentskills.io/specification) - reusable agent capability packages with structured metadata, progressive disclosure, and optional bundled resources (scripts, references, assets).

Skills complement prompts by providing:
- Dynamic capability discovery at runtime
- Lightweight metadata loading (~100 tokens per skill)
- Full content activation on-demand
- Support for scripts, references, and assets

### Affected Files
- NEW: `src/dot_work/skills/__init__.py`
- NEW: `src/dot_work/skills/models.py`
- NEW: `src/dot_work/skills/parser.py`
- NEW: `src/dot_work/skills/validator.py`
- NEW: `src/dot_work/skills/discovery.py`
- NEW: `src/dot_work/skills/prompt_generator.py`
- `src/dot_work/cli.py` (add `skills` subcommand group)
- `src/dot_work/harness/` (integration for skill injection)

### Importance
Agent Skills is an emerging standard for defining reusable agent capabilities. Supporting it in dot-work:
- Enables interoperability with other tools supporting the spec
- Provides progressive disclosure (metadata first, full content on activation)
- Allows bundling scripts and references with skills
- Complements the existing prompts feature

### Proposed Solution
Implementation per `skills_spec.md`:

**Phase 1: Core Models**
1. Create `SkillMetadata` dataclass (name, description, license, compatibility, metadata, allowed_tools)
2. Create `Skill` dataclass (meta, content, path, scripts, references, assets)
3. Add validation in `__post_init__` methods

**Phase 2: Parser**
1. Create `SkillParser` mirroring `CanonicalPromptParser` pattern
2. Support YAML frontmatter extraction from SKILL.md
3. Add `parse_metadata_only()` for lightweight discovery

**Phase 3: Validator**
1. Validate name: 1-64 chars, `[a-z0-9-]`, no leading/trailing/consecutive hyphens
2. Validate name matches parent directory
3. Validate description: 1-1024 chars
4. Validate compatibility: max 500 chars if provided

**Phase 4: Discovery**
1. Create `SkillDiscovery` class
2. Search paths: `.skills/` (project), `~/.config/dot-work/skills/` (user), bundled
3. Support `discover()` for metadata and `load_skill()` for full content

**Phase 5: Prompt Generation**
1. Generate `<available_skills>` XML format
2. Include name, description, and location
3. Support `include_paths` parameter

**Phase 6: CLI Commands**
```
dot-work skills list              # List discovered skills
dot-work skills validate <path>   # Validate a skill directory
dot-work skills show <name>       # Display full skill content
dot-work skills prompt            # Generate available_skills XML
dot-work skills install <source>  # Copy skill to project .skills/
```

**Phase 7: Harness Integration**
- Inject discovered skills into agent sessions via `generate_skills_prompt()`

### Acceptance Criteria
- [ ] `SkillMetadata` and `Skill` dataclasses with validation
- [ ] `SkillParser` parses SKILL.md with YAML frontmatter
- [ ] `SkillValidator` enforces Agent Skills spec constraints
- [ ] `SkillDiscovery` finds skills in configured paths
- [ ] `generate_skills_prompt()` produces valid XML
- [ ] CLI commands: list, validate, show, prompt, install
- [ ] Unit tests for all components
- [ ] Test fixtures with valid and invalid skill directories
- [ ] Integration with harness for skill injection

### Notes
- Specification: https://agentskills.io/specification
- Full design document: `.work/agent/issues/references/skills_spec.md`
- Skills are complementary to prompts (static instructions) and subagents (AI personalities)
- Progressive disclosure keeps initial context usage low

---

---
id: "FEAT-024@b8c4d0"
title: "Implement cross-environment Subagent/Custom Agent support"
description: "Add subagent definition, parsing, and deployment across Claude Code, OpenCode, and GitHub Copilot"
created: 2025-12-26
section: "subagents"
tags: [feature, subagents, custom-agents, claude-code, opencode, copilot, multi-environment]
type: enhancement
priority: medium
status: proposed
references:
  - .work/agent/issues/references/subagents_spec.md
  - src/dot_work/prompts/canonical.py
  - src/dot_work/environments.py
---

### Problem
AI coding environments (Claude Code, OpenCode, GitHub Copilot) each support custom agents/subagents with different file formats, tool configurations, and invocation patterns. Currently, users must manually maintain separate agent definitions for each environment.

**Platform Differences:**
| Aspect | Claude Code | OpenCode | GitHub Copilot |
|--------|-------------|----------|----------------|
| Location | `.claude/agents/` | `.opencode/agent/` | `.github/agents/` |
| Tools | Comma-separated | Boolean map/wildcards | String list with aliases |
| Model | `sonnet`, `opus`, `haiku` | `provider/model-id` | External config |
| Permissions | `permissionMode` | `permission` object | `infer` boolean |

### Affected Files
- NEW: `src/dot_work/subagents/__init__.py`
- NEW: `src/dot_work/subagents/models.py`
- NEW: `src/dot_work/subagents/parser.py`
- NEW: `src/dot_work/subagents/validator.py`
- NEW: `src/dot_work/subagents/discovery.py`
- NEW: `src/dot_work/subagents/generator.py`
- NEW: `src/dot_work/subagents/environments/base.py`
- NEW: `src/dot_work/subagents/environments/claude_code.py`
- NEW: `src/dot_work/subagents/environments/opencode.py`
- NEW: `src/dot_work/subagents/environments/copilot.py`
- `src/dot_work/cli.py` (add `subagents` subcommand group)

### Importance
Subagents are increasingly important in AI-assisted development:
- Claude Code uses subagents for isolated context and specialized tasks
- OpenCode distinguishes primary agents (Tab-switchable) from subagents (@-mentionable)
- GitHub Copilot supports custom agents at repository/org/enterprise levels

A unified canonical format enables:
- Write once, deploy to all environments
- Consistent agent definitions across tools
- Easier team collaboration on agent configurations

### Proposed Solution
Implementation per `subagents_spec.md`:

**Phase 1: Core Models (1-2 days)**
1. `SubagentMetadata` dataclass (name, description)
2. `SubagentConfig` dataclass with all platform fields:
   - Common: name, description, prompt, tools, model
   - Claude Code: permission_mode, skills
   - OpenCode: mode, temperature, max_steps, permissions
   - Copilot: target, infer, mcp_servers
3. `CanonicalSubagent` with environment-specific overrides

**Phase 2: Environment Adapters (2-3 days)**
1. `SubagentEnvironmentAdapter` base class with:
   - `get_target_path(project_root) -> Path`
   - `generate_native(config) -> str`
   - `parse_native(content) -> SubagentConfig`
   - `map_tools(tools) -> list | dict`
2. Claude Code adapter
3. OpenCode adapter
4. GitHub Copilot adapter
5. Tool name mapping table

**Phase 3: Generator (1-2 days)**
1. Canonical to native conversion
2. Tool name translation per environment
3. Model name translation
4. File generation with correct frontmatter

**Phase 4: CLI Commands (1-2 days)**
```
dot-work subagents list [--env ENV]           # List discovered subagents
dot-work subagents validate <path>            # Validate subagent file
dot-work subagents show <name>                # Display subagent details
dot-work subagents install <file> --env ENV   # Install canonical subagent
dot-work subagents generate <file> --env ENV  # Generate native file (stdout)
dot-work subagents sync <dir>                 # Sync canonical to all environments
```

**Phase 5: Bundled Subagents (1 day)**
Create canonical definitions for:
- code-reviewer - Code quality and security review
- test-runner - Run tests and fix failures
- debugger - Root cause analysis for errors
- docs-writer - Documentation specialist
- security-auditor - Security vulnerability detection
- refactorer - Code refactoring specialist

### Acceptance Criteria
- [ ] Data models support all three platforms' configurations
- [ ] Parser handles canonical format with environment overrides
- [ ] Validators enforce platform-specific constraints
- [ ] Environment adapters for Claude Code, OpenCode, Copilot
- [ ] Tool name mapping works correctly across platforms
- [ ] CLI commands: list, validate, show, install, generate, sync
- [ ] Bundled subagents work across all environments
- [ ] Unit tests for models, parser, validator, adapters
- [ ] Integration tests for end-to-end generation
- [ ] Test fixtures for canonical and native formats

### Notes
- Canonical format mirrors prompts feature (similar to `CanonicalPrompt`)
- Design document: `.work/agent/issues/references/subagents_spec.md`
- Subagents complement skills (capabilities) and prompts (instructions)
- Future: Cursor/Windsurf support (may share Copilot adapter)
- Future: MCP server integration in subagent configs
