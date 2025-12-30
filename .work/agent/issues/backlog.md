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
- Canonical format mirrors prompts feature (similar to `CanonicalPrompt`)
- Design document: `.work/agent/issues/references/subagents_spec.md`
- Subagents complement skills (capabilities) and prompts (instructions)
- Future: Cursor/Windsurf support (may share Copilot adapter)
- Future: MCP server integration in subagent configs

---
id: "DOCS-001@a1b2c3"
title: "Missing examples for knowledge-graph (kg) subcommands"
description: "8 kg subcommands documented but no usage examples in README"
created: 2024-12-27
section: "docs/knowledge-graph"
tags: [documentation, examples, knowledge-graph, missing-docs]
type: docs
priority: high
status: proposed
references:
  - README.md
  - src/dot_work/knowledge_graph/
---

### Problem
The README lists `kg` command but provides no examples for any of its 8 subcommands:
- ingest - Ingest Markdown files into knowledge graph
- stats - Show database statistics
- outline - Show document outline as a tree
- search - Search for nodes matching a query
- expand - Show full content of a specific node
- render - Render a document with optional filtering
- export - Export document nodes as JSON
- status - Show database status
- project - Manage projects (collections of documents)
- topic - Manage topics (reusable tags for content)

Users must rely on `--help` output to understand how to use these features, which is poor user experience.

### Affected Files
- `README.md` (no kg usage examples)

### Importance
**HIGH**: Knowledge graph is a major feature (advertised in README) but lacks examples for any subcommands:
- Users cannot discover kg workflows without trial-and-error
- Hidden functionality reduces value of the tool
- Poor first-run experience for a key feature

### Proposed Solution
Add "Knowledge Graph" section to README.md with examples:

```markdown
## Knowledge Graph

### Ingest Documents
```bash
# Ingest markdown files
dot-work kg ingest docs/*.md

# Ingest from stdin
cat document.md | dot-work kg ingest -

# Force replace existing documents
dot-work kg ingest --force docs/*.md
```

### Search Documents
```bash
# Search for text
dot-work kg search --query "machine learning"

# Limit results
dot-work kg search --query "API" --k 5
```

### Show Document Statistics
```bash
# Show database stats
dot-work kg stats
```

### Manage Projects
```bash
# Create project
dot-work kg project create "My Research"

# Add document to project
dot-work kg project add "My Research" document-id
```
```

### Acceptance Criteria
- [ ] "Knowledge Graph" section added to README.md
- [ ] Examples for ingest, search, stats, project, topic subcommands
- [ ] Each example shows required arguments and common options
- [ ] Examples include use cases for each subcommand
- [ ] Link to detailed kg documentation if available

### Notes
Knowledge graph appears to be a major feature with 10+ subcommands but is completely undocumented in main README. This should be prioritized alongside other major features.

---
id: "DOCS-002@b2c3d4"
title: "Missing examples for git, container, harness, python, zip, canonical, prompt, init-work commands"
description: "7 commands listed in --help but no usage examples in README"
created: 2024-12-27
section: "docs/commands"
tags: [documentation, examples, missing-docs, cli]
type: docs
priority: high
status: proposed
references:
  - README.md
---

### Problem
The README lists these commands in "Available Commands" section but provides no usage examples:

```bash
dot-work init        # Initialize a new project with prompts and issue tracking
dot-work init-work   # Initialize .work/ issue tracking directory structure
dot-work overview    # Generate a bird's-eye overview of a codebase
dot-work canonical   # Validate and install canonical prompt files
dot-work prompt      # Create and manage canonical prompt files
dot-work python      # Python development utilities
dot-work git         # Git analysis tools
dot-work harness     # Claude Agent SDK autonomous agent harness
dot-work zip         # Zip folders respecting .gitignore
dot-work container   # Container-based operations
```

Only `install`, `list`, `detect`, `init`, `review`, and `validate` have examples. Users must run `--help` to discover these features.

### Affected Files
- `README.md` (missing examples for 7 commands)

### Importance
**HIGH**: 7 commands (58% of CLI surface) have zero examples:
- Users cannot discover these features without reading --help
- Poor discoverability of valuable tools (git analysis, code overview, etc.)
- Hidden functionality reduces tool value
- Inconsistent documentation quality across commands

### Proposed Solution
Add sections to README.md for each command with examples:

```markdown
## Git Analysis
```bash
# Analyze commits between two refs
dot-work git history --from main --to feature-branch

# Analyze commits since last tag
dot-work git history --from $(git describe --tags --abbrev=0)
```

## Code Overview
```bash
# Generate overview of current project
dot-work overview . docs/

# Include complexity metrics
dot-work overview --with-metrics . docs/
```

## Zip Packaging
```bash
# Create zip respecting .gitignore
dot-work zip package source/ output.zip

# Include hidden files
dot-work zip --include-hidden source/ output.zip
```

## Canonical Prompts
```bash
# Validate canonical prompt
dot-work canonical validate my-prompt.md

# Install canonical prompt to environment
dot-work canonical install my-prompt.md --env claude
```

## Project Initialization
```bash
# Initialize full project structure
dot-work init --with-tests my-project/

# Initialize only issue tracking
dot-work init-work
```
```

### Acceptance Criteria
- [ ] README.md includes examples for git, overview, zip, canonical commands
- [ ] Each command has "how to use" section with 2-3 examples
- [ ] Common use cases covered for each command
- [ ] Examples show required arguments and useful options
- [ ] Consistent documentation style across all commands

### Notes
With 7 commands missing examples, this represents significant documentation debt. Prioritize based on command usage/popularity if metrics available.

---
id: "DOCS-003@c3d4e5"
title: "Missing troubleshooting documentation for all features"
description: "No troubleshooting or FAQ section in README or docs"
created: 2024-12-27
section: "docs/troubleshooting"
tags: [documentation, troubleshooting, faq, missing-docs]
type: docs
priority: medium
status: proposed
references:
  - README.md
  - docs/
---

### Problem
No troubleshooting documentation exists anywhere in the project:
- No FAQ section in README.md
- No "Common Issues" section
- No troubleshooting guides in docs/
- No error message explanations
- No recovery procedures for failures

Users encountering errors must debug without guidance.

### Affected Files
- `README.md` (missing troubleshooting)
- `docs/` (missing troubleshooting)

### Importance
**MEDIUM**: Lack of troubleshooting documentation causes:
- Poor user experience when errors occur
- Higher support burden
- Users abandon tool when hitting roadblocks
- Difficulty diagnosing common issues

### Proposed Solution
Add "Troubleshooting" section to README.md or create docs/troubleshooting.md:

```markdown
## Troubleshooting

### Common Issues

**Q: Prompt installation fails with "permission denied"**
A: Try running with `--force` flag or check file permissions on target directory.

**Q: Database locked error when using db-issues**
A: Only one process can access SQLite database at a time. Close other db-issues instances.

**Q: Review server doesn't start**
A: Check if port 8765 is already in use. Use `dot-work review start --port 3000`.

**Q: Knowledge graph ingest fails on large files**
A: Try ingesting files in smaller batches or increase database timeout.

**Q: Version freeze fails with "uncommitted changes"**
A: Commit or stash changes before running `dot-work version freeze`.

### Getting Help
- Run command with `--help` for detailed options
- Check issue tracker at [GitHub Issues]
- Review AGENTS.md for development workflow
```

### Acceptance Criteria
- [ ] Troubleshooting section added (in README or docs/troubleshooting.md)
- [ ] Covers 5+ common error scenarios
- [ ] Each issue has clear cause and resolution
- [ ] Includes link to GitHub issues or support
- [ ] References relevant commands or configuration

### Notes
Start with errors from GitHub issues, CI logs, and known user-reported problems. Expand based on user feedback.

---
id: "DOCS-004@d4e5f6"
title: "Missing integration workflows between features"
description: "No examples showing how prompts, issue tracking, and review work together"
created: 2024-12-27
section: "docs/workflows"
tags: [documentation, workflows, integration, examples]
type: docs
priority: high
status: proposed
references:
  - README.md
  - AGENTS.md
  - docs/db-issues/getting-started.md
---

### Problem
README.md describes features in isolation but doesn't show how they integrate:

**Missing workflow examples:**
- How to use AI prompts WITH issue tracking
- How to do code review and export comments TO issue tracker
- How to use version management WITH issue dependencies
- How to set up prompts → work → review → commit loop
- How knowledge graph integrates with project documentation

Each feature is documented separately but integration paths are unclear.

### Affected Files
- `README.md` (missing workflow section)
- `AGENTS.md` (mentions issue tracker but not integration)

### Importance
**HIGH**: Missing integration documentation prevents users from realizing full value:
- Users may use features in isolation instead of together
- "Workflow Example" section in README (lines 215-248) is only for project setup, not ongoing work
- Synergies between features are undocumented
- Best practices for combined workflows unknown

### Proposed Solution
Add "Integrated Workflows" section to README.md:

```markdown
## Integrated Workflows

### Development Iteration Loop
```bash
# 1. Check focus in issue tracker
cat .work/agent/focus.md

# 2. Start work with AI prompt (in Claude Code)
# The prompt will read AGENTS.md and current focus issue

# 3. Make code changes
git add .
git commit -m "Implement feature"

# 4. Run code review
dot-work review start --base main
# Add comments in browser, then:
dot-work review export --output review.md

# 5. Pass review to AI agent
# Paste review.md content into AI agent prompt

# 6. Complete issue in tracker
dot-work db-issues close <issue-id>

# 7. Update version if needed
dot-work version freeze
```

### Bug Fix Workflow with Tracking
```bash
# 1. Create bug in issue tracker
dot-work db-issues create "Fix parser error" --type bug --priority critical

# 2. Use AI prompt to investigate
# /do-work prompt will read the issue from focus.md

# 3. Implement fix (agent will create tests)

# 4. Run tests
uv run pytest tests/unit/test_parser.py -v

# 5. Review changes
dot-work review start --base main
dot-work review export

# 6. Close issue if tests pass
dot-work db-issues close <issue-id>
```

### Documentation Generation Workflow
```bash
# 1. Ingest documentation into knowledge graph
dot-work kg ingest docs/*.md

# 2. Search for relevant context
dot-work kg search --query "API endpoints" --k 5

# 3. Use context in AI prompt
# Copy search results to prompt
```

### Release Workflow with Issue Tracking
```bash
# 1. Check completed issues
dot-work db-issues list --status completed

# 2. Generate changelog
dot-work version freeze --llm

# 3. Tag release
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```
```

### Acceptance Criteria
- [ ] "Integrated Workflows" section added to README.md
- [ ] 3+ end-to-end workflow examples
- [ ] Shows integration between prompts, issue tracking, review, version management
- [ ] Each workflow has step-by-step commands
- [ ] Workflows reflect actual user stories from issue tracker

### Notes
The existing "Workflow Example" section (lines 215-248) only covers project setup. Need ongoing workflows for daily development.

---
id: "DOCS-005@e5f6g7"
title: "Incomplete environment variable configuration reference"
description: "Only DOT_WORK_DB_ISSUES_PATH documented; other env vars undocumented"
created: 2024-12-27
section: "docs/configuration"
tags: [documentation, configuration, environment-variables]
type: docs
priority: medium
status: proposed
references:
  - README.md
  - docs/db-issues/README.md
---

### Problem
Environment variables are mentioned only for db-issues:
- `DOT_WORK_DB_ISSUES_PATH` - documented in docs/db-issues/README.md:48
- `DOT_WORK_DB_ISSUES_DEBUG` - documented in docs/db-issues/README.md:53

**Missing documentation for:**
- Environment variables for version management
- Environment variables for review module
- Environment variables for knowledge graph
- Environment variables for git analysis
- Environment variables for container operations
- Environment variables for Python utilities

Users must read code or help output to discover configuration options.

### Affected Files
- `README.md` (missing env var reference)
- `docs/` (no configuration reference)

### Importance
**MEDIUM**: Incomplete environment variable documentation causes:
- Users cannot configure features without reading code
- Hidden configuration options
- Difficulty customizing behavior
- Inconsistent configuration approach across features

### Proposed Solution
Add "Configuration" section to README.md with environment variable reference:

```markdown
## Configuration

dot-work behavior can be customized via environment variables.

### Database (db-issues)
```bash
# Custom database path
export DOT_WORK_DB_ISSUES_PATH=/custom/path/issues.db

# Enable debug logging
export DOT_WORK_DB_ISSUES_DEBUG=true
```

### Version Management
```bash
# Custom version file location (if implemented)
# See `dot-work version --help` for options
```

### Code Review
```bash
# Custom review storage path (if supported)
# See `dot-work review --help` for options
```

### Knowledge Graph
```bash
# Custom database path
dot-work kg --db /custom/path/kg.db

# Enable debug mode (if supported)
# See `dot-work kg --help` for options
```

### Git Analysis
```bash
# Custom cache location (if supported)
# See `dot-work git --help` for options
```

### Python Utilities
```bash
# Custom configuration (if supported)
# See `dot-work python --help` for options
```
```

### Acceptance Criteria
- [ ] "Configuration" section added to README.md
- [ ] Lists all environment variables for each major feature
- [ ] Includes default values and descriptions
- [ ] Links to feature-specific docs for detailed options
- [ ] Examples show setting variables in shell

### Notes
Need to verify all available environment variables by checking `--help` output for each command. This is foundational documentation that should exist before examples.

---
id: "DOCS-006@f6g7h8"
title: "Missing configuration reference for version management"
description: "version freeze command has options but no config file documented"
created: 2024-12-27
section: "docs/version"
tags: [documentation, configuration, version-management]
type: docs
priority: medium
status: proposed
references:
  - README.md
---

### Problem
`dot-work version freeze` command has several options but configuration reference is missing:

```bash
dot-work version freeze [OPTIONS]

Options:
  --llm                       Use LLM for enhanced summaries
  --dry-run                   Preview without making changes
  --push                      Push tags to remote after freeze
  --project-root        PATH  Project root directory
```

**Missing documentation:**
- What `--llm` does and how to configure LLM API keys
- What version configuration file format is
- How to customize version numbering scheme
- What `--push` does and authentication requirements
- Where to configure remote repository

Users must infer configuration from code or trial-and-error.

### Affected Files
- `README.md` (no version config reference)

### Importance
**MEDIUM**: Missing version configuration documentation causes:
- Users cannot configure automated versioning
- Unclear how `--llm` option works
- Difficulty setting up release workflow
- Risk of incorrect configuration

### Proposed Solution
Add "Version Management Configuration" section to README.md:

```markdown
## Version Management Configuration

### Version Configuration File
dot-work uses version.json in project root (created by `dot-work version init`).

Format:
```json
{
  "current": "2025.01.00001",
  "format": "YYYY.MM.PATCH",
  "changelog_file": "CHANGELOG.md",
  "version_file": "VERSION.txt"
}
```

### LLM Integration

Use LLM for enhanced changelog generation:

```bash
# With LLM (requires OPENAI_API_KEY)
export OPENAI_API_KEY=sk-...
dot-work version freeze --llm

# Or Anthropic Claude
export ANTHROPIC_API_KEY=sk-ant-...
dot-work version freeze --llm
```

### Git Integration

```bash
# Auto-push tags to remote
dot-work version freeze --push

# Requires git remote configured and authentication
git remote -v  # Verify remote is set
```

### Dry Run

```bash
# Preview changes without writing
dot-work version freeze --dry-run
```
```

### Acceptance Criteria
- [ ] Version configuration section added to README.md
- [ ] Documents version.json format and options
- [ ] Explains --llm option and API key requirements
- [ ] Documents --push and git requirements
- [ ] Shows dry-run usage
- [ ] Includes complete configuration reference

### Notes
Version management is a key feature (advertised in README line 14). Users need clear documentation to adopt it successfully.

---
id: "DOCS-007@g7h8i9"
title: "Missing parameter defaults and constraints documentation"
description: "Commands have parameters but default values not documented"
created: 2024-12-27
section: "docs/parameters"
tags: [documentation, parameters, defaults, constraints]
type: docs
priority: medium
status: proposed
references:
  - README.md
---

### Problem
Many command options have default values and constraints but these are not documented:

**Examples of missing documentation:**
- `dot-work review start --port 8765` - what is default port?
- `dot-work kg search --k 20` - what is max limit? what affects results?
- `dot-work overview` - what file formats are supported? what are outputs?
- `dot-work validate json` - what error formats are reported?
- `dot-work version init` - what files are created? what config options?

Users must run `--help` to discover defaults, which is poor documentation practice.

### Affected Files
- `README.md` (missing parameter reference)

### Importance
**MEDIUM**: Missing parameter documentation causes:
- Users cannot predict command behavior
- Trial-and-error to discover defaults
- Unclear constraints and valid ranges
- Poor scriptability (unknown defaults in automation)

### Proposed Solution
Add "Parameter Reference" section to README.md or create docs/parameters.md:

```markdown
## Parameter Reference

### Review
```bash
dot-work review start [OPTIONS]
```

| Parameter | Default | Description | Constraints |
|-----------|---------|-------------|--------------|
| `--port`, `-p` | 8765 | Server port | 1024-65535 |
| `--base`, `-b` | HEAD~1 | Base commit for diff | Valid commit/branch |
| `--head` | working tree | Head commit/branch | Valid commit/branch |

### Knowledge Graph Search
```bash
dot-work kg search --q QUERY [OPTIONS]
```

| Parameter | Default | Description | Constraints |
|-----------|---------|-------------|--------------|
| `--query`, `-q` | (required) | Search query | 1-1000 chars |
| `--limit`, `-k` | 20 | Max results | 1-1000 |
| `--db` | .work/kg/kg.db | Database path | Valid file path |

### Overview
```bash
dot-work overview INPUT_DIR OUTPUT_DIR
```

| Parameter | Description | Constraints |
|-----------|-------------|--------------|
| `INPUT_DIR` | Directory to scan | Must exist, readable |
| `OUTPUT_DIR` | Output directory | Must exist, writable |

**Supported formats:**
- Python files: `.py`
- Documentation: `.md`
- **Outputs:**
  - `birdseye_overview.md` - Human-readable guide
  - `features.json` - Structured data for LLMs
  - `documents.json` - Cross-referenced docs
```

### Acceptance Criteria
- [ ] Parameter reference table added
- [ ] Covers all major commands with options
- [ ] Includes defaults, descriptions, and constraints
- [ ] Documents output formats and files
- [ ] Links to detailed --help output for full options

### Notes
This should be generated from `--help` output to ensure completeness. Keep it in sync with CLI changes.

---
id: "DOCS-008@h8i9j0"
title: "Missing CLI subcommand reference"
description: "CLI has 15 subcommands but no comprehensive CLI reference"
created: 2024-12-27
section: "docs/cli"
tags: [documentation, cli-reference, completeness]
type: docs
priority: low
status: proposed
references:
  - README.md
  - docs/db-issues/cli-reference.md
---

### Problem
README.md only provides brief usage examples for 6 commands:
- install
- list
- detect
- init
- review
- validate

**Missing documentation for 9 commands:**
- init-work
- overview
- canonical
- prompt
- kg (8 subcommands)
- version (6 subcommands)
- git
- container
- python
- harness
- zip

The only CLI reference is for db-issues (`docs/db-issues/cli-reference.md`), not the main CLI.

### Affected Files
- `README.md` (incomplete CLI coverage)
- Missing: docs/cli-reference.md or similar

### Importance
**LOW**: Users must rely on `--help` for most commands:
- Poor discoverability of 60% of CLI surface
- Inconsistent documentation (db-issues has ref, others don't)
- Navigation difficulty for power users
- Harder to script without full reference

### Proposed Solution
Create comprehensive CLI reference at docs/cli-reference.md:

```markdown
# dot-work CLI Reference

Complete reference for all dot-work commands.

## Command Index

- [install](#install) - Install AI prompts
- [list](#list) - List supported environments
- [detect](#detect) - Detect AI environment
- [init](#init) - Initialize new project
- [init-work](#init-work) - Initialize issue tracking
- [overview](#overview) - Generate code overview
- [canonical](#canonical) - Validate/install canonical prompts
- [prompt](#prompt) - Manage canonical prompts
- [kg](#kg) - Knowledge graph operations
- [version](#version) - Version management
- [git](#git) - Git analysis
- [container](#container) - Container operations
- [python](#python) - Python utilities
- [harness](#harness) - Agent harness
- [zip](#zip) - Zip packaging
- [validate](#validate) - Validate files
- [review](#review) - Code review

## install
... (full documentation for each command)

## kg
### ingest
... (full documentation for all 8 subcommands)
```

### Acceptance Criteria
- [ ] docs/cli-reference.md created
- [ ] Documents all top-level commands
- [ ] Documents all subcommands (kg: 8, version: 6)
- [ ] Includes syntax, options, examples for each
- [ ] Cross-linked from README.md
- [ ] Keep in sync with CLI changes

### Notes
db-issues/cli-reference.md exists and can serve as template. Auto-generating from --help output would ensure completeness.

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

---
id: "FEAT-025@c9d5e1"
title: "Docker image provisioning with OpenCode webui and dynamic port assignment"
description: "Create containerized OpenCode environment with pre-registered providers, safe credential handling, dynamic ports, and optional GitHub repo cloning"
created: 2025-12-30
section: "container/docker"
tags: [feature, docker, containerization, opencode, webui, security, dynamic-ports]
type: enhancement
priority: high
status: proposed
references:
  - README.md
  - src/dot_work/container/
---

### Problem
Developers need a self-contained OpenCode environment that:
1. Runs as a Docker container with webui accessible
2. Has providers pre-registered without exposing credentials in image
3. Uses dynamic port assignment to avoid conflicts
4. Optionally clones a GitHub repo on startup
5. Is secure and reusable across sessions

Current approach requires manual setup of providers, fixed port allocation, and lacks easy container distribution.

### Affected Files
- NEW: `src/dot_work/container/opencode/Dockerfile`
- NEW: `src/dot_work/container/opencode/docker-compose.yml`
- NEW: `src/dot_work/container/opencode/entrypoint.sh`
- NEW: `src/dot_work/container/opencode/.env.example`
- NEW: `src/dot_work/container/opencode/README.md`
- `src/dot_work/container/__init__.py` (add opencode commands)
- `src/dot_work/cli.py` (add container opencode subcommand)

### Importance
**HIGH**: Containerized OpenCode enables:
- Zero-setup environment for new contributors
- Consistent development environments across teams
- Safe credential management (never baked into images)
- Easy distribution of pre-configured OpenCode setups
- Dynamic port assignment prevents conflicts on shared hosts
- Rapid onboarding for new projects via repo cloning

### Proposed Solution

**Phase 1: Docker Infrastructure (2-3 days)**
1. `Dockerfile`:
   - Base: `python:3.11-slim` or official opencode base image if available
   - Install OpenCode via pip/uv from PyPI or from local wheel
   - Copy entrypoint script
   - Set up working directory `/workspace`
   - Expose range of ports (e.g., 8000-9000) for dynamic assignment
   - Configure user permissions (non-root)
   - Add git for repo cloning

2. `entrypoint.sh`:
   - Parse environment variables for provider credentials
   - Dynamically select available port from range (e.g., 8000-9000)
   - Start OpenCode webui with selected port
   - If `GITHUB_REPO_URL` set, clone repo to `/workspace`
   - Health check on startup
   - Graceful shutdown handling

3. `docker-compose.yml`:
   - Service definition for opencode container
   - Volume mounts for workspace persistence
   - Environment variable template
   - Port mapping (dynamic via `--publish` or `8000-9000:8000-9000`)
   - Restart policy (unless-stopped)

**Phase 2: Provider Configuration (2 days)**
1. Provider registration strategy:
   - Create `providers.yaml` template in image
   - Configure provider metadata (name, base_url, models) without secrets
   - Use environment variables for API keys:
     - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
   - Entrypoint reads env vars and injects into OpenCode config
   - Never bake credentials into image layers

2. Config generation in entrypoint:
   ```bash
   # Example: Write OpenCode config file
   cat > ~/.config/opencode/config.yaml <<EOF
   providers:
     openai:
       base_url: https://api.openai.com/v1
       api_key: ${OPENAI_API_KEY}
     anthropic:
       base_url: https://api.anthropic.com
       api_key: ${ANTHROPIC_API_KEY}
   EOF
   ```

3. Validation:
   - Warn if no API keys provided (webui will prompt)
   - Validate API key format before starting
   - Support provider enable/disable via env vars

**Phase 3: Dynamic Port Assignment (1-2 days)**
1. Port selection logic in entrypoint:
   ```bash
   # Find available port in range
   PORT=8000
   while [ $PORT -le 9000 ]; do
     if ! nc -z localhost $PORT 2>/dev/null; then
       break
     fi
     PORT=$((PORT + 1))
   done

   if [ $PORT -gt 9000 ]; then
     echo "Error: No available ports in range 8000-9000"
     exit 1
   fi

   echo "Using port: $PORT" > /tmp/port.txt
   ```

2. Port publishing options:
   - Option A: Publish entire range `docker run -p 8000-9000:8000-9000`
   - Option B: Publish single dynamic port via docker-compose
   - Option C: Use host port specified via `PORT` env var

3. Output port info:
   - Log assigned port to stdout
   - Write port to `/tmp/port.txt` for scripts to read
   - Provide URL: `http://localhost:<PORT>`

**Phase 4: GitHub Repo Cloning (1 day)**
1. Repo cloning in entrypoint:
   ```bash
   if [ -n "$GITHUB_REPO_URL" ]; then
     echo "Cloning repository: $GITHUB_REPO_URL"
     git clone "$GITHUB_REPO_URL" /workspace/repo
     cd /workspace/repo

     if [ -n "$GITHUB_REPO_BRANCH" ]; then
       git checkout "$GITHUB_REPO_BRANCH"
     fi

     # Set as working directory for OpenCode
     ln -sf /workspace/repo /workspace/project
   fi
   ```

2. Authentication options:
   - Public repos: no auth required
   - Private repos: support `GITHUB_TOKEN` env var
   - SSH-based: support `GIT_SSH_COMMAND` or mount SSH keys

3. Environment variables:
   - `GITHUB_REPO_URL`: URL to clone (required for cloning)
   - `GITHUB_REPO_BRANCH`: Branch/commit to checkout (optional)
   - `GITHUB_TOKEN`: Personal access token for private repos

**Phase 5: CLI Integration (1-2 days)**
Add `dot-work container opencode` commands:
```bash
dot-work container opencode build [--tag TAG]           # Build Docker image
dot-work container opencode run [OPTIONS]              # Start container
dot-work container opencode stop [CONTAINER]           # Stop container
dot-work container opencode logs [CONTAINER]           # View logs
dot-work container opencode shell [CONTAINER]          # Open shell in container
```

Run command options:
- `--provider PROVIDER:KEY`: Set provider API key (repeatable)
- `--repo URL`: GitHub repo URL to clone
- `--branch BRANCH`: Branch to checkout
- `--port PORT`: Specific port (overrides dynamic)
- `--volume HOST:CONTAINER`: Additional volume mount
- `--env KEY=VALUE`: Additional environment variables
- `--detach`: Run in background
- `--rm`: Remove container on exit

**Phase 6: Documentation (1 day)**
1. `container/opencode/README.md`:
   - Prerequisites (Docker, Docker Compose)
   - Quick start examples
   - Provider configuration guide
   - GitHub repo cloning guide
   - Troubleshooting common issues
   - Security best practices

2. Examples in README:
   ```bash
   # Basic usage
   dot-work container opencode run

   # With provider keys
   dot-work container opencode run \
     --provider openai:$OPENAI_API_KEY \
     --provider anthropic:$ANTHROPIC_API_KEY

   # Clone GitHub repo
   dot-work container opencode run \
     --repo https://github.com/user/repo

   # Detached mode
   dot-work container opencode run --detach

   # Check logs
   dot-work container opencode logs <container-id>

   # Get assigned port
   docker exec <container-id> cat /tmp/port.txt
   ```

**Phase 7: Security Hardening (1-2 days)**
1. Container security:
   - Run as non-root user
   - Read-only root filesystem (except necessary paths)
   - Drop capabilities (--cap-drop ALL)
   - Use seccomp profiles if available
   - No privileged mode

2. Credential handling:
   - Never log API keys
   - Use Docker secrets or env files for sensitive data
   - Support credential injection via volumes
   - Clear credentials from environment in child processes

3. Network security:
   - Bind to localhost only by default
   - Support `--host 0.0.0.0` for external access with warning
   - Rate limiting suggestions for webui

**Phase 8: Testing (2-3 days)**
1. Unit tests:
   - Port selection logic
   - Provider config generation
   - Repo cloning with various auth methods
   - Entrypoint script validation

2. Integration tests:
   - Build image from Dockerfile
   - Start container and verify webui accessible
   - Test dynamic port assignment
   - Test provider registration with real keys (test only)
   - Test GitHub repo cloning (public and private)
   - Test volume persistence

3. Security tests:
   - Verify no credentials in image layers
   - Verify non-root user
   - Verify read-only paths

### Acceptance Criteria
- [ ] Dockerfile builds successfully
- [ ] Container starts OpenCode webui on dynamic port
- [ ] Provider registration works without hardcoding credentials
- [ ] GitHub repo cloning works with public URLs
- [ ] GitHub repo cloning works with private repos via token
- [ ] Port assignment is dynamic and conflict-free
- [ ] CLI commands: build, run, stop, logs, shell
- [ ] Security: no credentials in image, non-root user
- [ ] Documentation with examples
- [ ] Unit tests for port selection, config gen, cloning
- [ ] Integration tests for container lifecycle
- [ ] .env.example with all supported environment variables

### Notes
- Consider supporting OpenCode webui configuration via env vars (model, temperature, etc.)
- Future: Support MCP server configuration in container
- Future: Support hot-reload of provider credentials without restart
- Future: Multi-container setup with database for persistence
- Consider using Docker secrets for production deployments
- Dynamic port range should be configurable via env var

---
id: "FEAT-026@d0e6f2"
title: "Context and file injection for Dockerized OpenCode containers"
description: "Add support for injecting additional context, files, documentation, and configuration into OpenCode containers at runtime or build time"
created: 2025-12-30
section: "container/docker/context"
tags: [feature, docker, containerization, opencode, context-injection, volumes, configuration]
type: enhancement
priority: medium
status: proposed
references:
  - .work/agent/issues/backlog.md:FEAT-025@c9d5e1
  - README.md
  - src/dot_work/container/
---

### Problem
After provisioning an OpenCode container (FEAT-025), users need a way to:
1. Add project-specific documentation and context
2. Inject configuration files for tools/providers
3. Supply custom prompts, templates, or skills
4. Load knowledge graph databases or indexes
5. Attach multiple codebases or reference materials
6. Provide working examples or test data

The base Docker image only provides OpenCode itself. Users need flexible mechanisms to add context without rebuilding the image.

### Affected Files
- NEW: `src/dot_work/container/opencode/context-injector.py` (utility script)
- NEW: `src/dot_work/container/opencode/context-layout.md` (directory structure reference)
- MODIFIED: `src/dot_work/container/opencode/entrypoint.sh` (add context loading)
- MODIFIED: `src/dot_work/container/opencode/.env.example` (add context variables)
- MODIFIED: `src/dot_work/container/opencode/README.md` (add context examples)
- `src/dot_work/cli.py` (extend container opencode commands)

### Importance
**MEDIUM**: Context injection enables:
- Tailored OpenCode environments for specific projects
- Pre-loaded knowledge and reference materials
- Multi-repo workspaces
- Consistent context across team containers
- Faster onboarding with pre-baked context
- Template/boilerplate distribution

### Proposed Solution

**Phase 1: Context Directory Structure (1-2 days)**
Define standard context layout in container:
```
/workspace/context/
├── docs/              # Documentation files (.md, .txt, .pdf)
├── prompts/           # Canonical prompt files
├── skills/            # Agent skills directories
├── configs/           # Configuration files (.yaml, .json, .toml)
├── data/              # Data files (CSV, JSON, databases)
├── repos/             # Additional git repositories
├── templates/         # Code templates or snippets
└── manifest.yaml      # Context metadata and loading order
```

`manifest.yaml` format:
```yaml
version: "1.0"
name: "Project Context"
description: "Context for XYZ project"

docs:
  - path: "docs/api-guide.md"
    description: "API documentation"
  - path: "docs/architecture.md"
    description: "System architecture"

prompts:
  - path: "prompts/code-review.md"
    name: "code-review"

configs:
  - path: "configs/providers.yaml"
    target: "~/.config/opencode/providers.yaml"

repos:
  - url: "https://github.com/example/reference-impl"
    path: "repos/reference-impl"
    branch: "main"
```

**Phase 2: Build-Time Context Injection (1-2 days)**
Add `dot-work container opencode build` enhancements:

1. `--context-dir DIR` flag:
   - Copy entire directory to `/workspace/context/`
   - Run context validation
   - Bake context into image layers

2. `--context-file FILE` flag (repeatable):
   - Copy specific files to `/workspace/context/`
   - Auto-detect type based on extension/location

3. `--context-url URL` flag (repeatable):
   - Download file from URL to context directory
   - Support HTTP/HTTPS and raw GitHub URLs

4. `--context-manifest FILE` flag:
   - Load manifest.yaml and follow instructions
   - Clone repos, copy files, apply configs

Examples:
```bash
# Build with context directory
dot-work container opencode build \
  --context-dir ./project-context \
  --tag opencode:my-project

# Build with specific files
dot-work container opencode build \
  --context-file ./docs/api.md \
  --context-file ./prompts/review.md \
  --tag opencode:with-docs

# Build with manifest
dot-work container opencode build \
  --context-manifest ./context-manifest.yaml \
  --tag opencode:full-context

# Build with URL
dot-work container opencode build \
  --context-url https://raw.githubusercontent.com/org/repo/main/docs/spec.md \
  --tag opencode:remote-context
```

**Phase 3: Runtime Context Injection (2-3 days)**
Add `dot-work container opencode run` enhancements:

1. `--context-volume HOST:CONTAINER` flag (repeatable):
   - Mount host directories as read-only volumes
   - Auto-detect context structure

2. `--context-file FILE:DEST` flag (repeatable):
   - Copy files from host to container on startup
   - Use entrypoint script for copying

3. `--context-git URL` flag (repeatable):
   - Clone additional git repos on container startup
   - Support `URL[:DEST[:BRANCH]]` format

4. `--context-archive FILE` flag:
   - Extract tar/zip archive to `/workspace/context/`
   - Support `.tar`, `.tar.gz`, `.zip`

Examples:
```bash
# Run with context volume
dot-work container opencode run \
  --context-volume ./docs:/workspace/context/docs \
  --context-volume ./prompts:/workspace/context/prompts

# Run with file copy
dot-work container opencode run \
  --context-file ./config.yaml:/workspace/context/configs/config.yaml

# Run with additional repo
dot-work container opencode run \
  --context-git https://github.com/example/reference:/workspace/context/repos/ref

# Run with context archive
dot-work container opencode run \
  --context-archive ./context.tar.gz
```

**Phase 4: Context Loading Logic in Entrypoint (1-2 days)**
Extend `entrypoint.sh` to handle context:

1. Context directory setup:
   ```bash
   # Ensure context directory exists
   mkdir -p /workspace/context/{docs,prompts,skills,configs,data,repos,templates}

   # Load manifest if present
   if [ -f /workspace/context/manifest.yaml ]; then
     echo "Loading context manifest..."
     python3 /usr/local/bin/context-injector.py load \
       --manifest /workspace/context/manifest.yaml
   fi
   ```

2. Repo cloning from manifest:
   ```python
   # context-injector.py
   import yaml
   import subprocess

   def load_manifest(manifest_path):
     with open(manifest_path) as f:
       manifest = yaml.safe_load(f)

     for repo in manifest.get('repos', []):
       subprocess.run(['git', 'clone', '-b', repo['branch'],
                       repo['url'], repo['path']])

     for config in manifest.get('configs', []):
       subprocess.run(['cp', config['path'], config['target']])
   ```

3. Integration with OpenCode:
   - Copy prompts to `.work/prompts/`
   - Copy skills to `.skills/`
   - Load configs into OpenCode config dir
   - Index documentation files (optional)

**Phase 5: Context Management CLI (1-2 days)**
Add context-specific commands:

```bash
# List context in running container
dot-work container opencode context list [CONTAINER]

# Show context manifest
dot-work container opencode context show [CONTAINER]

# Add context to running container
dot-work container opencode context add CONTAINER \
  --file ./new-doc.md \
  --git https://github.com/example/repo

# Export context from container
dot-work container opencode context export CONTAINER \
  --output context-export.tar.gz

# Validate context directory
dot-work container opencode context validate [--dir DIR]
```

**Phase 6: Context Packaging and Distribution (1-2 days)**
1. Create context packages:
   - `dot-work container opencode context package DIR output.context`
   - Includes manifest and all referenced files
   - Compressed tarball with metadata

2. Context registry (simple file-based):
   ```bash
   # List available contexts
   dot-work container context list-registry

   # Download and apply context
   dot-work container opencode run \
     --context-registry my-project-context
   ```

3. Shareable context examples:
   - `web-dev.context` - Web development prompts and templates
   - `python-backend.context` - Python backend patterns
   - `ml-project.context` - ML/DS specific prompts and docs
   - `api-design.context` - API design guidelines

**Phase 7: Documentation (1 day)**
1. `container/opencode/context-layout.md`:
   - Directory structure reference
   - Manifest schema reference
   - Best practices for organizing context

2. Extend `container/opencode/README.md`:
   - Context injection examples
   - Build-time vs runtime comparison
   - Context package creation guide
   - Common use cases (multi-repo, docs, templates)

Examples in README:
```bash
# Quick start: Build with context
mkdir my-context
echo "# Project Docs" > my-context/docs/overview.md
dot-work container opencode build --context-dir my-context

# Multi-repo workspace
dot-work container opencode run \
  --context-git https://github.com/user/frontend:/workspace/context/frontend \
  --context-git https://github.com/user/backend:/workspace/context/backend

# Add prompts to existing container
dot-work container opencode context add my-container \
  --file ./prompts/code-review.md

# Export context for sharing
dot-work container opencode context export my-container \
  --output team-context.context

# Validate context before build
dot-work container opencode context validate --dir ./project-context
```

**Phase 8: Testing (2-3 days)**
1. Unit tests:
   - Manifest parsing and validation
   - Context loading logic
   - File copying and repo cloning
   - Archive extraction

2. Integration tests:
   - Build image with context directory
   - Verify files are in container
   - Test runtime context injection
   - Test context export/import
   - Test multi-repo cloning

3. Edge case tests:
   - Invalid manifest formats
   - Missing files in manifest
   - Git clone failures
   - Permission issues
   - Large file handling

### Acceptance Criteria
- [ ] Context directory structure defined and documented
- [ ] `manifest.yaml` schema with validation
- [ ] Build-time context injection: `--context-dir`, `--context-file`, `--context-url`, `--context-manifest`
- [ ] Runtime context injection: `--context-volume`, `--context-file`, `--context-git`, `--context-archive`
- [ ] Entrypoint loads context and applies manifest
- [ ] Context management CLI: list, show, add, export, validate
- [ ] Context packaging: create and distribute `.context` files
- [ ] Documentation: context-layout.md, extended README
- [ ] Integration with prompts, skills, configs
- [ ] Unit tests for context loading and validation
- [ ] Integration tests for build and runtime injection

### Notes
- Context should be optional (container works without it)
- Consider supporting context hot-reload (via webui or signal)
- Future: Context versioning and dependency management
- Future: Context inheritance (base context + overrides)
- Future: Integration with knowledge graph ingestion
- Future: Remote context URLs with authentication
- Consider context size limits and optimization
- Security: Validate file paths (no path traversal attacks)
