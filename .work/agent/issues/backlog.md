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
