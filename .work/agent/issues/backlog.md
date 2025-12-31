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

---
id: "FEAT-027@e1f7g3"
title: "Runtime URL-based context injection for OpenCode containers"
description: "Add support for injecting context files, directories, and archives from remote URLs into running containers"
created: 2025-12-30
section: "container/docker/context"
tags: [feature, docker, containerization, opencode, context-injection, urls, remote-content]
type: enhancement
priority: medium
status: proposed
references:
  - .work/agent/issues/backlog.md:FEAT-026@d0e6f2
  - README.md
  - src/dot_work/container/
---

### Problem
FEAT-026 adds build-time URL context injection, but runtime containers also need to:
1. Fetch updated documentation from remote URLs
2. Pull latest configuration files from internal servers
3. Download context archives from CI/CD pipelines
4. Fetch prompts/skills from shared repositories
5. Update context without rebuilding or restarting container

Runtime URL injection enables live updates to container context without rebuilding images.

### Affected Files
- MODIFIED: `src/dot_work/container/opencode/entrypoint.sh` (add URL download logic)
- MODIFIED: `src/dot_work/container/opencode/.env.example` (add URL env vars)
- MODIFIED: `src/dot_work/cli.py` (add --context-url to run command)
- NEW: `src/dot_work/container/opencode/url-downloader.py` (downloader utility)
- MODIFIED: `src/dot_work/container/opencode/README.md` (add URL examples)

### Importance
**MEDIUM**: Runtime URL injection enables:
- Live context updates without container restart
- CI/CD integration (inject build artifacts, test results)
- Centralized context management (fetch from shared servers)
- Dynamic prompt/skill distribution
- Zero-downtime context refresh
- Multi-environment consistency (dev/stage/prod from same source)

### Proposed Solution

**Phase 1: URL Download Utility (1-2 days)**
Create `url-downloader.py` script:

1. Supported URL schemes:
   - HTTP/HTTPS: `https://example.com/file.txt`
   - Raw GitHub: `gh://org/repo/path/file.md`
   - GitLab: `gl://org/project/path/file.md`
   - S3: `s3://bucket/path/file.txt` (optional, with boto3)
   - Local file: `file:///path/to/file`

2. Download with validation:
   ```python
   def download_url(url, dest_dir, validate=True):
     """Download URL to destination directory."""
     parsed = urlparse(url)

     if parsed.scheme in ('http', 'https'):
       return download_http(url, dest_dir)
     elif parsed.netloc == 'github.com' or url.startswith('gh://'):
       return download_github(url, dest_dir)
     elif parsed.scheme == 'file':
       return copy_local(url, dest_dir)
     else:
       raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
   ```

3. Validation options:
   - File size limits (e.g., max 100MB)
   - Content type validation (e.g., only text/markdown)
   - Checksum verification (SHA256)
   - SSL certificate validation for HTTPS
   - Auth token injection from env vars

**Phase 2: Runtime URL CLI Flags (1 day)**
Add `--context-url` to `dot-work container opencode run`:

```bash
# Download single file
dot-work container opencode run \
  --context-url https://example.com/api-spec.md \
  --context-dest docs/

# Download manifest from URL
dot-work container opencode run \
  --context-url https://raw.githubusercontent.com/org/repo/main/context.yaml \
  --context-type manifest

# Download archive from URL
dot-work container opencode run \
  --context-url https://releases.example.com/context.tar.gz \
  --context-type archive

# Multiple URLs
dot-work container opencode run \
  --context-url https://example.com/docs/api.md \
  --context-url https://example.com/configs/providers.yaml \
  --context-url gh://org/skills/code-review
```

URL formats:
- `--context-url URL[:DEST][:TYPE]`
  - `URL`: Source URL
  - `DEST`: Destination in context (default: auto-detect)
  - `TYPE`: File type (manifest, archive, file, dir) (default: auto-detect)

**Phase 3: Entrypoint URL Handling (1-2 days)**
Extend `entrypoint.sh` to download URLs on startup:

```bash
# Download context URLs
if [ -n "$CONTEXT_URLS" ]; then
  echo "Downloading context URLs..."
  IFS=';' read -ra URLS <<< "$CONTEXT_URLS"
  for url_spec in "${URLS[@]}"; do
    python3 /usr/local/bin/url-downloader.py download \
      --url "$url_spec" \
      --dest /workspace/context
  done
fi
```

Environment variables:
- `CONTEXT_URLS`: Semicolon-separated URL specs
- `CONTEXT_URL_TIMEOUT`: Download timeout (default: 30s)
- `CONTEXT_URL_MAX_SIZE`: Max file size (default: 100MB)
- `GITHUB_TOKEN`: For private GitHub repos
- `HTTP_AUTH_TOKEN`: Generic HTTP auth token

**Phase 4: Runtime Context Update Command (1-2 days)**
Add CLI command to update context in running container:

```bash
# Update context from URLs
dot-work container opencode context update CONTAINER \
  --url https://example.com/docs/api.md \
  --url https://example.com/config.yaml

# Update from manifest URL
dot-work container opencode context update CONTAINER \
  --manifest-url https://raw.githubusercontent.com/org/repo/main/context.yaml

# Update with force (overwrite existing files)
dot-work container opencode context update CONTAINER \
  --url https://example.com/docs/new.md \
  --force

# Dry run (preview changes)
dot-work container opencode context update CONTAINER \
  --url https://example.com/docs/updated.md \
  --dry-run
```

Update workflow:
1. Download files to temporary location
2. Validate and verify checksums
3. Show diff vs existing files
4. Apply changes (unless dry-run)
5. Trigger OpenCode context reload (if supported)

**Phase 5: URL Authentication Support (1 day)**
Support authenticated URLs:

1. GitHub tokens:
   - Use `GITHUB_TOKEN` env var
   - Inject into GitHub raw content URLs
   - Support private repos

2. HTTP auth:
   - Use `HTTP_AUTH_TOKEN` env var
   - Basic auth via `HTTP_AUTH_USER:HTTP_AUTH_PASS`
   - Bearer token via `HTTP_AUTH_BEARER`

3. Custom headers:
   - `CONTEXT_URL_HEADERS: Authorization=Bearer token,X-Custom=value`
   - Inject into HTTP requests

4. SSH keys for git URLs:
   - Mount SSH key into container
   - Use for git-based URLs (gh://, gl://)

**Phase 6: URL Caching and Versioning (1-2 days)**
Implement caching to avoid redundant downloads:

1. Cache directory:
   - `/workspace/context/.cache/`
   - Store downloaded files by URL hash
   - Cache TTL (configurable via env var)

2. Versioning support:
   ```yaml
   # URL in manifest with version
   urls:
     - url: https://example.com/docs/api-v2.md
       version: "2.1.0"
       checksum: "sha256:abc123..."
       cache_ttl: 3600  # 1 hour
   ```

3. Conditional download:
   - Check if cached file exists
   - Verify checksum matches
   - Skip download if valid and within TTL

**Phase 7: URL Monitoring and Auto-Refresh (2-3 days)**
Optional background monitoring:

1. Watch mode:
   ```bash
   dot-work container opencode context watch CONTAINER \
     --url https://example.com/docs/api.md \
     --interval 300  # check every 5 minutes
   ```

2. Webhook support:
   - Expose endpoint for webhook notifications
   - Trigger context update on webhook call
   - Support GitHub webhooks, CI/CD pipelines

3. Inotify integration:
   - Monitor downloaded files for changes
   - Trigger OpenCode context reload on change

**Phase 8: Documentation and Examples (1 day)**
Extend `container/opencode/README.md`:

```bash
# Quick examples
## Download single file
dot-work container opencode run \
  --context-url https://example.com/api-spec.md

## Download from GitHub
dot-work container opencode run \
  --context-url gh://org/repo/docs/architecture.md

## Download manifest
dot-work container opencode run \
  --context-url https://raw.githubusercontent.com/org/repo/main/context.yaml \
  --context-type manifest

## Multiple URLs with auth
export GITHUB_TOKEN=ghp_xxx
dot-work container opencode run \
  --context-url https://raw.githubusercontent.com/org/repo/main/docs/api.md \
  --context-url https://raw.githubusercontent.com/org/repo/main/configs/providers.yaml

## Update running container
dot-work container opencode context update my-container \
  --url https://example.com/docs/updated-api.md

## Watch for updates
dot-work container opencode context watch my-container \
  --url https://example.com/docs/api.md \
  --interval 600
```

### Acceptance Criteria
- [ ] `url-downloader.py` supports HTTP/HTTPS, GitHub, GitLab URLs
- [ ] Runtime `--context-url` flag works in run command
- [ ] Entrypoint downloads URLs on startup
- [ ] `dot-work container opencode context update` command works
- [ ] URL authentication via env vars (GitHub token, HTTP auth)
- [ ] URL caching with TTL support
- [ ] Dry-run mode for updates
- [ ] Documentation with examples
- [ ] Unit tests for download, validation, caching
- [ ] Integration tests for runtime URL injection
- [ ] Error handling for network failures, invalid URLs, auth failures

### Notes
- URL downloads should be optional (container works without URLs)
- Security: Validate URLs (no SSRF attacks), limit file sizes
- Consider rate limiting for frequent downloads
- Future: Support custom URL handlers via plugins
- Future: URL signing and verification
- Future: Proxy support for corporate environments
- Monitor download sizes to prevent disk exhaustion

---
id: "FEAT-028@f2g8h4"
title: "File upload/download utilities for OpenCode containers"
description: "Add optional file transfer utilities for easy uploading and downloading files to and from running containers"
created: 2025-12-30
section: "container/docker/file-transfer"
tags: [feature, docker, containerization, opencode, file-transfer, upload, download]
type: enhancement
priority: medium
status: proposed
references:
  - .work/agent/issues/backlog.md:FEAT-025@c9d5e1
  - README.md
  - src/dot_work/container/
---

### Problem
Users working with OpenCode containers need convenient ways to:
1. Upload generated files (code, docs, configs) from container to host
2. Download reference files, datasets, or prompts from host to container
3. Transfer files between containers
4. Bulk upload/download operations
5. Resume interrupted transfers
6. Track transfer history and status

Current approach requires manual `docker cp` commands or volume mounts, which are inconvenient for ad-hoc transfers.

### Affected Files
- NEW: `src/dot_work/container/opencode/file-server.py` (simple HTTP file server)
- NEW: `src/dot_work/container/opencode/file-transfer.sh` (transfer utilities)
- MODIFIED: `src/dot_work/container/opencode/entrypoint.sh` (optional file server)
- MODIFIED: `src/dot_work/container/opencode/Dockerfile` (add curl, transfer tools)
- `src/dot_work/cli.py` (add file transfer commands)
- MODIFIED: `src/dot_work/container/opencode/.env.example` (add file server vars)

### Importance
**MEDIUM**: File transfer utilities enable:
- Ad-hoc file sharing without volume mounts
- Easy backup of container work artifacts
- Transfer files between containers and host
- Integration with CI/CD pipelines
- User-friendly alternative to `docker cp`
- Progress tracking for large transfers

### Proposed Solution

**Phase 1: Simple HTTP File Server (2-3 days)**
Create optional HTTP file server in container:

1. `file-server.py`:
   - Lightweight HTTP server using Flask or FastAPI
   - Endpoints: `/upload`, `/download`, `/list`, `/delete`
   - Authentication (optional token-based)
   - CORS support
   - Chunked upload for large files
   - Progress tracking

2. API design:
   ```python
   # Upload file
   POST /upload
   Query: ?dest=/workspace/uploads/
   Body: multipart/form-data with file

   # Download file
   GET /download
   Query: ?path=/workspace/path/file.txt

   # List files
   GET /list
   Query: ?path=/workspace/

   # Delete file
   DELETE /delete
   Query: ?path=/workspace/path/file.txt

   # Transfer status
   GET /status/:transfer_id
   ```

3. Optional activation via env var:
   - `FILE_SERVER_ENABLED=true`
   - `FILE_SERVER_PORT=9000` (different from webui port)
   - `FILE_SERVER_AUTH_TOKEN=secret` (optional)
   - `FILE_SERVER_MAX_SIZE=1GB` (default)

**Phase 2: File Transfer CLI Commands (2-3 days)**
Add `dot-work container opencode transfer` commands:

```bash
# Upload file to container
dot-work container opencode transfer upload CONTAINER \
  /path/on/host/file.txt \
  --dest /workspace/uploads/

# Upload directory (recursive)
dot-work container opencode transfer upload CONTAINER \
  /path/on/host/dir/ \
  --dest /workspace/context/docs/ \
  --recursive

# Download file from container
dot-work container opencode transfer download CONTAINER \
  /workspace/workspace/generated-code.py \
  --dest ./downloads/

# Download directory
dot-work container opencode transfer download CONTAINER \
  /workspace/context/ \
  --dest ./context-backup/ \
  --recursive

# List files in container
dot-work container opencode transfer list CONTAINER \
  --path /workspace/

# Delete file in container
dot-work container opencode transfer delete CONTAINER \
  /workspace/workspace/temp-file.txt

# Show transfer history
dot-work container opencode transfer status
```

Transfer features:
- Progress bars for large files
- Resume capability (skip if exists and checksum matches)
- Dry-run mode
- Verbose logging
- Checksum verification (SHA256)
- Compression for transfers (`--compress`)
- Parallel transfers (`--jobs 4`)

**Phase 3: Web-Based File Manager (Optional, 2-3 days)**
Simple web UI for file transfers:

1. File upload form:
   - Drag and drop
   - Progress indicators
   - Batch upload
   - Destination selection

2. File browser:
   - Tree view of container files
   - Download buttons
   - Delete confirmation
   - Search/filter

3. Web UI access:
   - `http://localhost:FILE_SERVER_PORT/files/`
   - Authentication via token
   - Responsive design

**Phase 4: Transfer History and Tracking (1-2 days)**
Track file transfers:

1. Transfer log:
   ```yaml
   # /workspace/.transfer-log.yaml
   transfers:
     - id: "tx_001"
       type: "upload"
       timestamp: "2025-12-30T10:00:00Z"
       source: "/host/file.txt"
       dest: "/workspace/uploads/file.txt"
       size: 12345
       checksum: "sha256:abc123..."
       status: "completed"

     - id: "tx_002"
       type: "download"
       timestamp: "2025-12-30T10:05:00Z"
       source: "/workspace/output.txt"
       dest: "/host/downloads/output.txt"
       size: 67890
       status: "failed"
       error: "timeout"
   ```

2. Status command:
   ```bash
   # Show recent transfers
   dot-work container opencode transfer status --recent 10

   # Show specific transfer
   dot-work container opencode transfer status tx_001

   # Filter by status
   dot-work container opencode transfer status --status failed

   # Retry failed transfer
   dot-work container opencode transfer retry tx_002
   ```

**Phase 5: Alternative: SCP/SFTP Mode (Optional, 2 days)**
Enable SCP/SFTP transfers for SSH users:

1. Install OpenSSH server in container (optional)
2. User configuration:
   - `SSH_ENABLED=true` (disabled by default for security)
   - `SSH_USER=opencode`
   - `SSH_KEY_MOUNT=/ssh/keys`

3. SCP usage:
   ```bash
   # Upload via SCP
   scp file.txt opencode@container:/workspace/uploads/

   # Download via SCP
   scp opencode@container:/workspace/output.txt ./downloads/
   ```

**Phase 6: rsync Integration (1-2 days)**
Add rsync for efficient sync:

```bash
# Sync directory (incremental)
dot-work container opencode transfer sync CONTAINER \
  /host/dir/ \
  --dest /workspace/context/ \
  --direction push

# Sync from container
dot-work container opencode transfer sync CONTAINER \
  /workspace/context/ \
  --dest /host/backup/ \
  --direction pull

# Dry-run sync
dot-work container opencode transfer sync CONTAINER \
  /host/dir/ \
  --dest /workspace/ \
  --dry-run
```

Sync features:
- Only transfer changed files (based on checksum)
- Delete extraneous files (`--delete`)
- Exclude patterns (`--exclude .git`)
- Compression (`--compress`)
- Bandwidth limit (`--bwlimit 1M`)

**Phase 7: Entrypoint Integration (1 day)**
Optional file server startup in entrypoint:

```bash
# Start file server if enabled
if [ "$FILE_SERVER_ENABLED" = "true" ]; then
  echo "Starting file server on port $FILE_SERVER_PORT..."
  python3 /usr/local/bin/file-server.py \
    --port "$FILE_SERVER_PORT" \
    --auth-token "$FILE_SERVER_AUTH_TOKEN" \
    --max-size "$FILE_SERVER_MAX_SIZE" \
    --path /workspace \
    &

  echo "File server running on port $FILE_SERVER_PORT"
  echo "Access: http://localhost:$FILE_SERVER_PORT/files/"
fi
```

**Phase 8: Security Hardening (1-2 days)**
1. Authentication:
   - Required auth token for file server
   - Token rotation support
   - HTTPS/TLS (optional, via reverse proxy)

2. Access control:
   - Allowed paths whitelist (e.g., only `/workspace/`)
   - File size limits
   - User-specific permissions

3. Auditing:
   - Log all transfer operations
   - Include source/destination IP
   - Include user/token ID
   - Timestamp and file metadata

**Phase 9: Documentation and Examples (1 day)**
Extend `container/opencode/README.md`:

```bash
# Quick start: Enable file server
export FILE_SERVER_ENABLED=true
export FILE_SERVER_AUTH_TOKEN=my-secret-token
dot-work container opencode run

# Upload file
dot-work container opencode transfer upload my-container \
  ./local-file.txt \
  --dest /workspace/uploads/

# Download generated code
dot-work container opencode transfer download my-container \
  /workspace/workspace/generated.py \
  --dest ./downloads/

# Sync directory
dot-work container opencode transfer sync my-container \
  ./docs/ \
  --dest /workspace/context/docs/ \
  --direction push

# Web UI access
# Open http://localhost:9000/files/
# Enter token: my-secret-token
# Drag and drop files to upload

# Show transfer history
dot-work container opencode transfer status --recent 5
```

### Acceptance Criteria
- [ ] `file-server.py` with upload/download/list/delete endpoints
- [ ] File server optional activation via env vars
- [ ] CLI transfer commands: upload, download, list, delete, sync
- [ ] Progress bars for large file transfers
- [ ] Resume capability and checksum verification
- [ ] Transfer history tracking
- [ ] Optional web UI for file manager
- [ ] Security: auth token, path restrictions, size limits
- [ ] rsync integration for efficient sync
- [ ] Documentation with examples
- [ ] Unit tests for file server and transfer logic
- [ ] Integration tests for file transfers

### Notes
- File server should be optional (disabled by default)
- Security: Never enable file server in production without auth
- Consider rate limiting for transfers
- Future: S3 bucket integration for cloud storage
- Future: Transfer scheduling (upload at specific time)
- Future: Webhook notifications on transfer completion
- Monitor disk usage during transfers

---
id: "INFRA-001@g3h9i5"
title: "Issue file size management and automatic splitting"
description: "Implement token limit enforcement and automatic splitting for issue files to maintain them below 25,000 tokens"
created: 2025-12-30
section: "infrastructure/issue-tracker"
tags: [infrastructure, issue-tracker, token-management, file-splitting, data-integrity]
type: maintenance
priority: high
status: proposed
references:
  - .work/agent/issues/backlog.md
  - .work/agent/issues/references/issue-file-format.md
---

### Problem
Issue tracker files (`backlog.md`, `doing.md`, `done.md`, etc.) grow indefinitely as issues are added. Problems:

1. **Token overflow**: Files exceed 25,000 tokens, causing context truncation
2. **Performance**: Reading large files slows down AI agents
3. **Memory**: Large files consume more memory and tokens
4. **Maintenance**: Hard to navigate and manage large files
5. **Risk**: Data loss if manual splitting fails

Current state: `backlog.md` has 2245+ lines and growing.

### Affected Files
- NEW: `src/dot_work/db_issues/token_counter.py` (token estimation utility)
- NEW: `src/dot_work/db_issues/issue_splitter.py` (file splitting tool)
- NEW: `src/dot_work/db_issues/issue_indexer.py` (index maintenance)
- MODIFIED: `src/dot_work/db_issues/parser.py` (handle split files)
- MODIFIED: `src/dot_work/db_issues/__init__.py` (add split commands)
- `src/dot_work/cli.py` (add issue file management commands)

### Importance
**HIGH**: File size management ensures:
- AI agents can read complete issue files without truncation
- Consistent performance regardless of file size
- Data integrity during splits (no lost issues)
- Automatic maintenance (no manual intervention)
- Scalability to hundreds/thousands of issues
- Reduced token usage and costs

### Proposed Solution

**Phase 1: Token Estimation (1 day)**
Create token counter utility:

1. Token estimation strategies:
   - Word-based: ~0.75 tokens per word (rough estimate)
   - Character-based: ~4 characters per token
   - Exact tokenization: Use tiktoken or similar library

2. `token_counter.py`:
   ```python
   def estimate_tokens(text: str, method: str = "word") -> int:
     """Estimate token count for text."""
     if method == "word":
       return len(text.split()) * 0.75
     elif method == "char":
       return len(text) / 4
     elif method == "exact":
       import tiktoken
       enc = tiktoken.encoding_for_model("gpt-4")
       return len(enc.encode(text))

   def count_file_tokens(path: Path) -> int:
     """Count tokens in issue file."""
     content = path.read_text()
     return estimate_tokens(content)

   def count_issue_tokens(issue_yaml: str) -> int:
     """Count tokens in single issue block."""
     return estimate_tokens(issue_yaml)
   ```

3. CLI command:
   ```bash
   # Check file token count
   dot-work db-issues tokens backlog.md

   # Check all issue files
   dot-work db-issues tokens --all

   # Show detailed breakdown
   dot-work db-issues tokens backlog.md --verbose
   ```

**Phase 2: Issue Parser Enhancement (2 days)**
Enhance parser to handle split files:

1. Multi-file parsing:
   ```python
   def parse_issues_dir(dir_path: Path) -> List[Issue]:
     """Parse all issue files in directory."""
     issues = []
     for file_path in dir_path.glob("*.md"):
       issues.extend(parse_issues_file(file_path))
     return sorted(issues, key=lambda i: i.created, reverse=True)
   ```

2. Issue file discovery:
   - Support patterns: `backlog-001.md`, `backlog-002.md`, etc.
   - Support dates: `backlog-2025-12-30.md`
   - Support alphabetical: `backlog-a.md`, `backlog-b.md`

3. Index file:
   ```yaml
   # .work/agent/issues/index.yaml
   files:
     - path: "backlog-001.md"
       issues: 50
       tokens: 23456
       date_range: ["2025-12-26", "2025-12-28"]
     - path: "backlog-002.md"
       issues: 30
       tokens: 18900
       date_range: ["2025-12-29", "2025-12-30"]
   total_issues: 80
   total_tokens: 42356
   ```

**Phase 3: Automatic Splitting Strategy (2-3 days)**
Create splitting tool:

1. Split triggers:
   - Token limit exceeded (default: 25,000 tokens)
   - Issue count threshold (default: 50 issues)
   - Manual split command
   - Time-based (e.g., monthly splits)

2. Split strategies:
   - **By issue count**: N issues per file
   - **By date**: All issues within time range
   - **By section**: Group by section/tags
   - **Balanced**: Equal token distribution

3. `issue_splitter.py`:
   ```python
   def split_file(
     source_path: Path,
     output_dir: Path,
     max_tokens: int = 25000,
     strategy: str = "balanced"
   ) -> List[Path]:
     """Split issue file into multiple files."""
     issues = parse_issues_file(source_path)

     if strategy == "balanced":
       return split_balanced(issues, output_dir, max_tokens)
     elif strategy == "date":
       return split_by_date(issues, output_dir, max_tokens)
     elif strategy == "count":
       return split_by_count(issues, output_dir, max_tokens)
     elif strategy == "section":
       return split_by_section(issues, output_dir, max_tokens)

   def split_balanced(issues, output_dir, max_tokens):
     """Split into files with balanced token counts."""
     files = []
     current_issues = []
     current_tokens = 0
     file_num = 1

     for issue in issues:
       issue_tokens = estimate_tokens(issue.content)

       if current_tokens + issue_tokens > max_tokens and current_issues:
         # Flush current file
         out_path = output_dir / f"{source_path.stem}-{file_num:03d}.md"
         write_issues_file(out_path, current_issues)
         files.append(out_path)
         current_issues = []
         current_tokens = 0
         file_num += 1

       current_issues.append(issue)
       current_tokens += issue_tokens

     # Write remaining issues
     if current_issues:
       out_path = output_dir / f"{source_path.stem}-{file_num:03d}.md"
       write_issues_file(out_path, current_issues)
       files.append(out_path)

     return files
   ```

4. Validation before split:
   - Verify all issues parsed successfully
   - Count total issues
   - Estimate tokens
   - Preview split plan
   - Require confirmation (unless `--force`)

**Phase 4: Split CLI Commands (2 days)**
Add splitting commands:

```bash
# Check if file needs splitting
dot-work db-issues check-split backlog.md

# Show split preview
dot-work db-issues split backlog.md --preview

# Perform split
dot-work db-issues split backlog.md \
  --max-tokens 25000 \
  --strategy balanced \
  --output-dir .work/agent/issues/

# Split with confirmation
dot-work db-issues split backlog.md --interactive

# Force split (no confirmation)
dot-work db-issues split backlog.md --force

# Split all files
dot-work db-issues split --all --max-tokens 25000

# Merge split files (reverse operation)
dot-work db-issues merge \
  --pattern "backlog-*.md" \
  --output backlog-merged.md
```

**Phase 5: Index Maintenance (1-2 days)**
Create index management:

1. Auto-update index:
   - Update on split/merge operations
   - Update on issue creation/closure
   - Validate index consistency

2. Index commands:
   ```bash
   # Build/update index
   dot-work db-issues index build

   # Validate index
   dot-work db-issues index validate

   # Show index
   dot-work db-issues index show

   # Rebuild from scratch
   dot-work db-issues index rebuild
   ```

3. Index format:
   ```yaml
   version: "1.0"
   updated: "2025-12-30T12:00:00Z"
   files:
     backlog:
       - path: "backlog-001.md"
         issues: 50
         tokens: 24500
         date_range: ["2025-12-26", "2025-12-28"]
         sections: ["skills", "docker", "context"]
       - path: "backlog-002.md"
         issues: 30
         tokens: 18900
         date_range: ["2025-12-29", "2025-12-30"]
         sections: ["file-transfer", "url-injection"]
     doing:
       - path: "doing.md"
         issues: 5
         tokens: 3200
     done:
       - path: "done.md"
         issues: 20
         tokens: 15000
   totals:
     issues: 105
     tokens: 61600
   ```

**Phase 6: Safe Splitting with Rollback (1-2 days)**
Ensure data integrity:

1. Atomic split operation:
   - Create temporary directory for split files
   - Write split files to temp location
   - Validate split files contain all issues
   - Rename original to backup
   - Move split files to final location
   - Delete backup on success

2. Rollback on failure:
   - If validation fails, restore backup
   - Log failure reason
   - Keep backup for manual recovery

3. Validation checks:
   - Issue count: total after split == total before split
   - Issue IDs: all unique, no duplicates
   - Issue content: YAML frontmatter preserved
   - Token counts: within limits
   - File format: valid markdown

**Phase 7: Automatic Splitting (1-2 days)**
Automatic split on threshold:

1. Auto-split triggers:
   - On issue creation if file exceeds limit
   - Scheduled check (e.g., daily via cron)
   - CLI command: `dot-work db-issues check --auto-split`

2. Auto-split workflow:
   ```python
   def auto_split_if_needed(file_path: Path, max_tokens: int):
     """Check and auto-split if file exceeds limit."""
     tokens = count_file_tokens(file_path)

     if tokens > max_tokens:
       log.info(f"File {file_path} exceeds {max_tokens} tokens, splitting...")
       split_file(file_path, max_tokens=max_tokens, strategy="balanced")
       return True
     return False
   ```

3. Configuration:
   ```yaml
   # .work/agent/issues/config.yaml
   splitting:
     max_tokens: 25000
     max_issues: 50
     strategy: balanced
     auto_split: true
     backup_enabled: true
     backup_retention: 30d
   ```

**Phase 8: Merge and Consolidation (1 day)**
Reverse operation to merge split files:

```bash
# Merge split files back
dot-work db-issues merge \
  --pattern "backlog-*.md" \
  --output backlog-merged.md \
  --sort date  # or name, priority

# Merge specific files
dot-work db-issues merge \
  --files backlog-001.md,backlog-002.md \
  --output backlog.md

# Merge and sort by priority
dot-work db-issues merge \
  --pattern "backlog-*.md" \
  --output backlog.md \
  --sort priority
```

Merge features:
- Deduplicate issues (by ID)
- Preserve original order or re-sort
- Update index
- Validate merged file

**Phase 9: Documentation (1 day)**
Create documentation:

1. Splitting guide:
   - When to split (token limits, issue count)
   - How to split (preview, interactive, force)
   - Split strategies (balanced, date, count, section)
   - Troubleshooting common issues

2. Reference docs:
   - File naming conventions
   - Index format reference
   - Configuration options
   - Best practices

3. Examples in README:
   ```bash
   # Check file size
   dot-work db-issues tokens backlog.md
   # Output: File: backlog.md, Issues: 80, Tokens: 42356

   # Preview split
   dot-work db-issues split backlog.md --preview
   # Output:
   # Will split into 2 files:
   #   backlog-001.md: 50 issues, 23456 tokens
   #   backlog-002.md: 30 issues, 18900 tokens

   # Perform split
   dot-work db-issues split backlog.md --strategy balanced
   # Output: Created backlog-001.md, backlog-002.md

   # Auto-split all files
   dot-work db-issues split --all --auto-split

   # Merge files back
   dot-work db-issues merge --pattern "backlog-*.md" --output backlog.md
   ```

**Phase 10: Testing (2 days)**
Comprehensive testing:

1. Unit tests:
   - Token estimation accuracy
   - Issue parsing from split files
   - Split strategies (balanced, date, count, section)
   - Index building and validation

2. Integration tests:
   - End-to-end split operation
   - Rollback on validation failure
   - Merge operation
   - Auto-split triggers
   - Index updates

3. Edge case tests:
   - Single issue larger than token limit
   - Empty files
   - Invalid YAML frontmatter
   - Duplicate issue IDs
   - Concurrent splits (file locking)

### Acceptance Criteria
- [ ] `token_counter.py` with word/char/exact token estimation
- [ ] CLI command to check file tokens
- [ ] Parser handles multiple issue files
- [ ] `issue_splitter.py` with 4 split strategies
- [ ] Split CLI commands: check, preview, split, merge
- [ ] Atomic split with rollback
- [ ] Index file maintenance
- [ ] Auto-split on threshold exceedance
- [ ] Configuration via config.yaml
- [ ] Validation checks (issue count, IDs, content)
- [ ] Documentation with examples
- [ ] Unit tests for all components
- [ ] Integration tests for split/merge workflows

### Notes
- Token estimation doesn't need to be exact (±10% acceptable)
- Splitting should preserve issue order and metadata
- Consider adding file locking for concurrent access
- Future: Support splitting by status (backlog/doing/done)
- Future: Support splitting by priority (high/medium/low)
- Future: GUI tool for visual splitting
- Monitor split file sizes in production
- Keep backups for configurable retention period
- Consider compression for large issue files

---
id: "REFACTOR-001@h4i0j6"
title: "Merge redundant code review prompts into unified review framework"
description: "Consolidate code-review.md, critical-code-review.md, and review-related sections into a single configurable review prompt with severity modes"
created: 2025-12-30
section: "prompts/reviews"
tags: [refactor, prompts, code-review, consolidation, token-efficiency]
type: refactor
priority: high
status: proposed
references:
  - src/dot_work/prompts/code-review.md
  - src/dot_work/prompts/critical-code-review.md
  - src/dot_work/prompts/security-review.md
  - src/dot_work/prompts/performance-review.md
---

### Problem
There are **4 separate review prompts** with significant overlap:
1. `code-review.md` (76 lines) - Generic checklist-style review
2. `critical-code-review.md` (368 lines) - Detailed 12-axis review with issue output
3. `security-review.md` (109 lines) - OWASP-focused security checklist
4. `performance-review.md` (119 lines) - Performance-focused checklist

**Issues:**
- `code-review.md` is 80% redundant with `critical-code-review.md`
- Security and performance axes exist in both `critical-code-review.md` AND separate files
- Agents must load multiple prompts for comprehensive review
- Token waste: ~672 lines across 4 files when ~400 lines could cover all cases
- No clear guidance on when to use which prompt
- `agent-loop.md` step 8 calls all 4 separately, wasting tokens

### Affected Files
- `src/dot_work/prompts/code-review.md` (to be deprecated/merged)
- `src/dot_work/prompts/critical-code-review.md` (becomes base)
- `src/dot_work/prompts/security-review.md` (merged in)
- `src/dot_work/prompts/performance-review.md` (merged in)
- NEW: `src/dot_work/prompts/unified-review.md`

### Importance
**HIGH**: This consolidation:
- Reduces total review prompt tokens by ~40%
- Eliminates confusion about which prompt to use
- Enables single invocation for comprehensive reviews
- Simplifies agent-loop.md step 8 from 4 calls to 1
- Improves agent autonomy (no decision about which review to run)

### Proposed Solution
Create `unified-review.md` with configurable modes:

```yaml
# Usage modes
mode: quick | standard | critical | security | performance | full
default: standard
```

**Architecture:**
1. Core review engine (from critical-code-review.md)
2. Mode-specific axis activation:
   - `quick`: Problem Fit, Error Handling, Test Strategy only
   - `standard`: All 12 axes from critical-code-review
   - `security`: Standard + expanded OWASP (from security-review.md)
   - `performance`: Standard + expanded perf (from performance-review.md)
   - `full`: All axes from all prompts
3. Single output format supporting all modes
4. Deprecate the 3 redundant files

**Migration:**
- `code-review.md` → deprecated, reference `unified-review.md mode:quick`
- `security-review.md` → deprecated, reference `unified-review.md mode:security`
- `performance-review.md` → deprecated, reference `unified-review.md mode:performance`

### Acceptance Criteria
- [ ] `unified-review.md` supports all 5 modes
- [ ] All axes from all 4 prompts preserved in appropriate modes
- [ ] Output format compatible with issue tracker
- [ ] Token count reduced by >30% for equivalent functionality
- [ ] Documentation explains mode selection
- [ ] agent-loop.md updated to use single unified prompt
- [ ] Old prompts marked deprecated with redirect

### Notes
- Consider making mode selection automatic based on changed file types
- Keep security-review.md for standalone security audits (rare)
- The 12 axes in critical-code-review are already comprehensive

---
id: "REFACTOR-002@i5j1k7"
title: "Merge establish-baseline.md and compare-baseline.md into unified baseline system"
description: "Consolidate baseline prompts into single prompt with establish/compare modes and shared schema"
created: 2025-12-30
section: "prompts/baseline"
tags: [refactor, prompts, baseline, consolidation, workflow]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/prompts/establish-baseline.md
  - src/dot_work/prompts/compare-baseline.md
  - src/dot_work/prompts/do-work.md
---

### Problem
Baseline functionality is split across 2 prompts:
1. `establish-baseline.md` (331 lines) - Captures project snapshot
2. `compare-baseline.md` (464 lines) - Detects regressions

**Issues:**
- Baseline schema defined twice (drift risk)
- 795 total lines when ~500 could suffice
- `do-work.md` references both but duplicates schema examples
- No shared constants for baseline sections
- Comparison axes in compare-baseline must match establish-baseline sections

### Affected Files
- `src/dot_work/prompts/establish-baseline.md`
- `src/dot_work/prompts/compare-baseline.md`
- NEW: `src/dot_work/prompts/baseline.md` (unified)

### Importance
**MEDIUM**: Consolidation:
- Single source of truth for baseline schema
- Reduces tokens by ~35%
- Eliminates schema drift risk
- Simplifies do-work.md references

### Proposed Solution
Create `baseline.md` with modes:

```yaml
mode: establish | compare
default: establish
```

**Architecture:**
1. Shared baseline schema definition (single source)
2. Mode: establish
   - All 8 axes from establish-baseline.md
   - Output to .work/baseline.md
3. Mode: compare
   - All 8 comparison axes
   - Reference baseline.md file
   - Output regression report + issues

### Acceptance Criteria
- [ ] Single baseline schema definition
- [ ] Both establish and compare modes work
- [ ] Output formats preserved
- [ ] do-work.md updated to reference single prompt
- [ ] Token reduction >30%

### Notes
- Consider adding `baseline mode:diff` for side-by-side comparison

---
id: "FEAT-029@j6k2l8"
title: "Create agent-loop orchestrator prompt for infinite autonomous operation"
description: "Add dedicated orchestrator prompt that manages the full agent-loop.md cycle with state persistence and recovery"
created: 2025-12-30
section: "prompts/orchestration"
tags: [feature, prompts, agent-loop, orchestration, autonomy, state-machine]
type: enhancement
priority: critical
status: proposed
references:
  - agent-loop.md
  - src/dot_work/prompts/do-work.md
  - src/dot_work/prompts/housekeeping.md
---

### Problem
The current `agent-loop.md` is a **human-readable document**, not a **machine-optimized orchestration prompt**. Issues:

1. **Not a prompt**: agent-loop.md describes the loop but isn't structured for autonomous execution
2. **State loss**: No mechanism for persisting loop state across session boundaries
3. **No recovery**: If agent fails mid-loop, no resume mechanism
4. **Manual decisions**: Step 10 says "If ANYTHING at all to do without human intervention - go to step 1" but agents can't evaluate this
5. **Unclear exit**: "AGENT DONE" is undefined behavior
6. **Token inefficiency**: do-work.md is 1256 lines but includes examples not needed every iteration

**Critical gap for infinite agent harness:**
- No state machine definition
- No checkpoint mechanism
- No error recovery strategy
- No resource limit awareness

### Affected Files
- NEW: `src/dot_work/prompts/orchestrator.md` (main orchestrator)
- NEW: `src/dot_work/prompts/orchestrator-state.md` (state schema)
- MODIFIED: `agent-loop.md` (reference orchestrator)
- MODIFIED: `src/dot_work/prompts/do-work.md` (extract minimal iteration logic)

### Importance
**CRITICAL**: This enables:
- True infinite agent operation without human intervention
- Session-resilient autonomous workflows
- Crash recovery and state restoration
- Resource-aware operation (token/time limits)
- Clear termination conditions and reporting

### Proposed Solution

**1. Orchestrator State Schema (.work/agent/orchestrator-state.yaml)**
```yaml
version: "1.0"
session_id: "uuid"
started: "ISO8601"
last_checkpoint: "ISO8601"

loop_state:
  current_phase: baseline | select | investigate | implement | validate | complete | learn | housekeeping
  iteration_count: 42
  issues_completed_this_session: 5
  
current_work:
  issue_id: "BUG-003@a9f3c2"
  phase: implement
  progress:
    - investigation: completed
    - implementation: in_progress (60%)
    - validation: pending

resource_tracking:
  tokens_used_estimate: 150000
  time_elapsed_minutes: 45
  issues_since_baseline: 3

exit_conditions:
  no_actionable_issues: false
  resource_limit_reached: false
  human_intervention_needed: false
  critical_error: null

checkpoints:
  - timestamp: "ISO8601"
    phase: investigate
    issue_id: "BUG-003"
    snapshot: "checkpoint-001.json"
```

**2. Orchestrator Prompt Structure**

```markdown
# Agent Orchestrator

## Role
You are the Loop Controller responsible for:
1. Managing iteration state
2. Checkpointing progress
3. Recovering from failures
4. Enforcing exit conditions
5. Delegating to specialized prompts

## State Management
- Read state from .work/agent/orchestrator-state.yaml
- Update state after each phase transition
- Create checkpoints at configurable intervals

## Recovery Protocol
On session start:
1. Check for existing state file
2. If found, verify integrity
3. Resume from last checkpoint
4. If corrupted, attempt last-known-good

## Exit Conditions (MANDATORY CHECK)
Before each iteration:
- Token budget remaining?
- Time limit reached?
- No actionable issues AND clean build?
- Critical error requiring human?

## Phase Delegation
| Phase | Delegate To |
|-------|-------------|
| baseline | baseline.md mode:establish |
| select | (inline logic) |
| investigate | (inline logic) |
| implement | (inline logic) |
| validate | baseline.md mode:compare + unified-review.md |
| complete | (inline logic) |
| learn | (inline logic) |
| housekeeping | housekeeping.md |
```

**3. Minimal Iteration Extraction from do-work.md**
Extract ~200 lines of core iteration logic into `iteration-core.md`, removing:
- Examples (move to examples.md)
- ASCII diagrams
- Detailed explanations (reference docs)

### Acceptance Criteria
- [ ] orchestrator-state.yaml schema defined
- [ ] Orchestrator prompt handles all loop phases
- [ ] State persisted after each phase transition
- [ ] Recovery from last checkpoint works
- [ ] Exit conditions evaluated each iteration
- [ ] Resource tracking (tokens, time) implemented
- [ ] Clean integration with do-work.md
- [ ] agent-loop.md updated to reference orchestrator
- [ ] Test: simulate session crash and recovery

### Notes
- Consider YAML vs JSON for state (YAML more human-readable for debugging)
- Checkpoint frequency configurable (every phase vs every N issues)
- Exit condition "no actionable issues" must check ALL issue files
- Resource limits should be configurable via environment or config

---
id: "FEAT-030@k7l3m9"
title: "Create pre-flight check prompt for autonomous operation readiness"
description: "Add prompt that validates environment, dependencies, and configuration before autonomous agent operation begins"
created: 2025-12-30
section: "prompts/orchestration"
tags: [feature, prompts, pre-flight, validation, autonomy, safety]
type: enhancement
priority: high
status: proposed
references:
  - agent-loop.md
  - src/dot_work/prompts/do-work.md
  - src/dot_work/prompts/establish-baseline.md
---

### Problem
Agent-loop.md assumes environment is ready, but autonomous operation can fail due to:

1. **Missing prerequisites**:
   - .work/ structure not initialized
   - No baseline exists
   - Build system broken
   - Tests failing before work starts

2. **Configuration issues**:
   - Missing API keys for LLM features
   - Incorrect paths in config
   - Memory.md missing project context

3. **State corruption**:
   - Orphaned issues in wrong state
   - focus.md inconsistent with issue files
   - Baseline stale or missing

4. **Resource constraints**:
   - Insufficient disk space
   - Rate limits on APIs

**Current gap**: Agent discovers these mid-loop, wasting tokens and creating confusing error states.

### Affected Files
- NEW: `src/dot_work/prompts/pre-flight.md`
- MODIFIED: `agent-loop.md` (add step 0: pre-flight)

### Importance
**HIGH**: Pre-flight checks:
- Fail fast before wasting tokens
- Provide clear remediation steps
- Ensure reproducible starting state
- Required for reliable infinite operation

### Proposed Solution

**Pre-flight Check Categories:**

```markdown
# Pre-Flight Checklist

## 1. Structure Validation
- [ ] .work/ directory exists
- [ ] All required issue files exist
- [ ] focus.md has valid structure
- [ ] memory.md exists and readable

## 2. Build System
- [ ] Build command runs without error
- [ ] All tests pass
- [ ] No lint errors (warnings OK)
- [ ] Type checking passes

## 3. Baseline Status
- [ ] baseline.md exists
- [ ] baseline.md age < threshold (configurable)
- [ ] Baseline matches current commit

## 4. Issue State Consistency
- [ ] No completed issues in active files
- [ ] focus.md.current matches issue status
- [ ] No duplicate issue IDs
- [ ] All references resolve

## 5. Configuration
- [ ] Project context in memory.md
- [ ] Build commands documented
- [ ] Test commands documented

## 6. Resources (if autonomous)
- [ ] Token budget configured
- [ ] Time limit configured
- [ ] API keys available (if needed)
```

**Output:**
```yaml
pre_flight:
  status: ready | blocked | needs_action
  blockers:
    - category: build
      issue: "Tests failing (3 failures)"
      remediation: "Fix failing tests before autonomous operation"
  warnings:
    - category: baseline
      issue: "Baseline 3 days old"
      remediation: "Consider regenerating baseline"
  ready_at: "ISO8601"
```

### Acceptance Criteria
- [ ] Pre-flight prompt covers all 6 categories
- [ ] Clear pass/fail for each check
- [ ] Remediation steps for all failures
- [ ] Output format parseable
- [ ] Integration with orchestrator
- [ ] Can auto-fix some issues (init structure, move completed)

### Notes
- Some checks can auto-remediate (housekeeping before starting)
- Consider `--fix` mode that attempts auto-remediation
- Baseline age threshold should be configurable

---
id: "REFACTOR-003@l8m4n0"
title: "Consolidate API-related prompts into unified API prompt"
description: "Merge api-export.md and production-ready-apis.md into single comprehensive API prompt with modes"
created: 2025-12-30
section: "prompts/api"
tags: [refactor, prompts, api, consolidation, token-efficiency]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/prompts/api-export.md
  - src/dot_work/prompts/production-ready-apis.md
---

### Problem
Two API prompts with significant overlap:
1. `api-export.md` (362 lines) - API audit with OpenAPI alignment
2. `production-ready-apis.md` (281 lines) - Production checklist

**Issues:**
- Overlapping sections: security, validation, error handling, testing
- ~643 total lines when ~400 could suffice
- api-export has 10 detailed axes already covering production concerns
- production-ready-apis is a checklist format, not audit format
- No clear guidance on when to use which

### Affected Files
- `src/dot_work/prompts/api-export.md`
- `src/dot_work/prompts/production-ready-apis.md`
- NEW: `src/dot_work/prompts/api-review.md` (unified)

### Importance
**MEDIUM**: Consolidation:
- Reduces tokens by ~35%
- Single comprehensive API review
- Consistent output format

### Proposed Solution
Create `api-review.md` with modes:

```yaml
mode: audit | checklist | full
default: audit
```

- `audit`: Deep 10-axis analysis (from api-export.md)
- `checklist`: Quick pass/fail (from production-ready-apis.md)
- `full`: Both

### Acceptance Criteria
- [ ] Single unified API prompt
- [ ] All axes preserved
- [ ] Both output formats supported
- [ ] Token reduction >30%

### Notes
- api-export.md name is confusing (it's audit, not export)

---
id: "FEAT-031@m9n5o1"
title: "Create error-recovery prompt for autonomous operation failures"
description: "Add prompt specialized in diagnosing and recovering from errors during autonomous agent operation"
created: 2025-12-30
section: "prompts/orchestration"
tags: [feature, prompts, error-recovery, autonomy, resilience]
type: enhancement
priority: high
status: proposed
references:
  - agent-loop.md
  - src/dot_work/prompts/do-work.md
---

### Problem
When errors occur during autonomous operation, agents have no systematic recovery process:

1. **Build failures**: Agent may loop trying same fix
2. **Test failures**: No strategy for isolating cause
3. **Validation failures**: May create duplicate issues
4. **State corruption**: No recovery mechanism
5. **Resource exhaustion**: No graceful degradation

**Current behavior**: Errors create issues and continue, potentially cascading failures.

### Affected Files
- NEW: `src/dot_work/prompts/error-recovery.md`
- MODIFIED: `src/dot_work/prompts/do-work.md` (reference recovery prompt)

### Importance
**HIGH**: Error recovery enables:
- Autonomous operation without human intervention on recoverable errors
- Reduced cascading failures
- Clear escalation path for unrecoverable errors
- Session continuity despite issues

### Proposed Solution

**Error Classification:**
```yaml
error_types:
  recoverable:
    - build_failure
    - test_failure
    - validation_regression
    - lint_error
    - type_error
  
  needs_context:
    - ambiguous_error
    - dependency_failure
    - configuration_issue
  
  unrecoverable:
    - critical_data_loss
    - security_breach_detected
    - infinite_loop_detected
    - state_corruption
```

**Recovery Strategies:**
```markdown
## Build Failure Recovery
1. Parse error message
2. Identify affected file(s)
3. Check if recently modified (our change)
4. If our change: revert and create issue
5. If not our change: create issue, mark blocked

## Test Failure Recovery
1. Identify failing test(s)
2. Check if new tests (we added)
3. If new test fails: review test logic
4. If existing test fails: regression, create issue
5. Isolate: run single test to confirm

## Infinite Loop Detection
- Track: same error > 3 times in N minutes
- Action: checkpoint state, create meta-issue, STOP
```

### Acceptance Criteria
- [ ] Error classification schema
- [ ] Recovery strategy for each recoverable type
- [ ] Escalation path for unrecoverable
- [ ] Integration with orchestrator
- [ ] Loop detection mechanism
- [ ] State checkpoint before risky recovery

### Notes
- Consider "confidence score" for recovery attempts
- Max recovery attempts configurable
- Recovery actions should be logged for debugging

---
id: "REFACTOR-004@n0o6p2"
title: "Deprecate and archive redundant prompts"
description: "Remove or archive prompts that are fully superseded by unified prompts or no longer needed"
created: 2025-12-30
section: "prompts/cleanup"
tags: [refactor, prompts, deprecation, cleanup, maintenance]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/prompts/
---

### Problem
After consolidation efforts (REFACTOR-001, 002, 003), several prompts will be redundant:

**Candidates for deprecation:**
1. `code-review.md` - Superseded by unified-review.md
2. `security-review.md` - Merged into unified-review.md
3. `performance-review.md` - Merged into unified-review.md
4. `production-ready-apis.md` - Merged into api-review.md

**Candidates for archive:**
1. `pythonic-code.md` - Niche use, not part of agent-loop
2. `python-project-from-discussion.md` - Project creation, not iteration
3. `agent-prompts-reference.md` - Documentation, not operational

### Affected Files
- Multiple prompts in src/dot_work/prompts/

### Importance
**MEDIUM**: Cleanup:
- Reduces maintenance burden
- Clears confusion about which prompt to use
- Reduces token waste from loading deprecated prompts

### Proposed Solution
1. **Deprecate**: Add deprecation notice pointing to replacement
2. **Archive**: Move to `src/dot_work/prompts/archive/` 
3. **Update references**: Find all references and update

**Deprecation notice format:**
```markdown
---
meta:
  deprecated: true
  superseded_by: unified-review.md
  deprecation_date: 2025-12-30
---

> ⚠️ **DEPRECATED**: This prompt has been superseded by `unified-review.md`.
> Use `unified-review.md mode:quick` for equivalent functionality.
```

### Acceptance Criteria
- [ ] All redundant prompts identified
- [ ] Deprecation notices added
- [ ] Archive folder created
- [ ] References updated
- [ ] Documentation updated

### Notes
- Keep deprecated prompts for 2 releases before removal
- Archive should be clearly marked as not maintained

---
id: "FEAT-032@o1p7q3"
title: "Create issue-to-implementation prompt for zero-ambiguity task execution"
description: "Add prompt that transforms any issue into explicit, deterministic implementation steps with validation"
created: 2025-12-30
section: "prompts/execution"
tags: [feature, prompts, implementation, determinism, autonomy]
type: enhancement
priority: high
status: proposed
references:
  - src/dot_work/prompts/do-work.md
  - src/dot_work/prompts/issue-readiness.md
---

### Problem
`do-work.md` defines the iteration loop but implementation phase is vague:

```markdown
### Phase 4: IMPLEMENT
Actions:
  1. Update focus.md phase to "Implementation"
  2. Make code changes as planned
  3. Add/update tests as needed
  ...
```

**Issues:**
- "Make code changes as planned" is not deterministic
- No structured approach to transforming issue into code
- Agents may interpret issues differently
- No verification that implementation matches issue intent

**Gap**: Issues are well-specified (via issue-readiness.md) but translation to code is undefined.

### Affected Files
- NEW: `src/dot_work/prompts/implement.md`
- MODIFIED: `src/dot_work/prompts/do-work.md` (reference implement.md)

### Importance
**HIGH**: Deterministic implementation:
- Reduces variation in agent behavior
- Ensures issue acceptance criteria are met
- Provides traceability from issue to code
- Enables validation against original intent

### Proposed Solution

**Implementation Protocol:**

```markdown
# Implementation Protocol

## Input
- Issue with acceptance criteria
- Investigation notes
- Baseline state of affected files

## Step 1: Decompose into atomic changes
For each acceptance criterion:
1. Identify required code change
2. Identify required test change
3. Identify required doc change
4. Map to specific file:line

## Step 2: Sequence changes
Order changes to maintain working state:
- Dependencies first
- Tests before implementation (TDD optional)
- Docs last

## Step 3: For each atomic change
1. State the change in plain language
2. Identify the exact location
3. Write the minimal diff
4. Verify no unintended effects

## Step 4: Trace to acceptance criteria
| Criterion | Change | File:Line | Test |
|-----------|--------|-----------|------|
| AC-1 | Add validation | src/x.py:45 | test_x.py:23 |

## Step 5: Checkpoint
After each atomic change:
- Run relevant tests
- Check lint
- Update progress in focus.md
```

### Acceptance Criteria
- [ ] Implementation decomposition protocol
- [ ] Change sequencing rules
- [ ] Traceability matrix template
- [ ] Checkpoint requirements
- [ ] Integration with do-work.md

### Notes
- Consider TDD mode where tests written first
- Atomic changes enable easier rollback
- Traceability enables spec-delivery-auditor validation

---
id: "FEAT-033@p2q8r4"
title: "Add resource-aware prompt loading for token optimization"
description: "Implement progressive prompt loading based on available context window and task requirements"
created: 2025-12-30
section: "prompts/optimization"
tags: [feature, prompts, tokens, optimization, progressive-loading]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/prompts/
  - agent-loop.md
---

### Problem
Current approach loads full prompts regardless of:
- Available context window
- Specific task requirements
- Already-known information

**Token waste examples:**
- `do-work.md` (1256 lines) loaded every iteration
- Examples in prompts not needed after first use
- ASCII diagrams repeated unnecessarily
- Schema definitions duplicated across prompts

### Affected Files
- ALL prompts in src/dot_work/prompts/
- NEW: `src/dot_work/prompts/manifest.yaml` (prompt metadata)

### Importance
**MEDIUM**: Token optimization:
- Extends effective context window
- Reduces cost
- Enables more complex operations
- Supports smaller models

### Proposed Solution

**1. Prompt Manifest:**
```yaml
# manifest.yaml
prompts:
  do-work:
    full_path: do-work.md
    tokens: ~3000
    sections:
      core: [philosophy, checklist, loop-diagram]
      examples: [transcript-1, transcript-2]
      reference: [baseline-content, focus-template]
    
    loading_strategy:
      first_iteration: full
      subsequent: core_only
      on_error: core + relevant_reference
```

**2. Section Markers in Prompts:**
```markdown
<!-- @section:core -->
## 🎯 Workflow Philosophy
...
<!-- @end:core -->

<!-- @section:examples -->
## 🎬 Example: Complete Iteration Transcript
...
<!-- @end:examples -->
```

**3. Loader Logic:**
```python
def load_prompt(name: str, context: LoadContext) -> str:
    manifest = load_manifest()
    prompt_meta = manifest.prompts[name]
    
    if context.first_iteration:
        return load_full(prompt_meta.full_path)
    elif context.error_recovery:
        return load_sections(prompt_meta, ['core', 'reference'])
    else:
        return load_sections(prompt_meta, ['core'])
```

### Acceptance Criteria
- [ ] Prompt manifest with section metadata
- [ ] Section markers in prompts
- [ ] Progressive loader implementation
- [ ] Token savings >40% for subsequent iterations
- [ ] Examples loadable on-demand

### Notes
- Start with do-work.md (biggest savings)
- Consider caching computed prompts
- Section markers should be invisible in normal rendering

---
id: "FEAT-034@q3r9s5"
title: "Create symbiosis map for prompt composition and workflow optimization"
description: "Document how prompts work together and optimal composition patterns for different workflows"
created: 2025-12-30
section: "prompts/documentation"
tags: [feature, prompts, documentation, symbiosis, workflows]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/prompts/
  - agent-loop.md
  - src/dot_work/prompts/agent-prompts-reference.md
---

### Problem
`agent-prompts-reference.md` lists prompts but doesn't explain:
- Which prompts work together
- Optimal ordering for combined use
- Input/output compatibility
- When to use compositions vs single prompts

**Missing guidance:**
- Can spec-delivery-auditor use baseline for comparison?
- Does critical-code-review output feed into issue-readiness?
- What's the optimal review sequence?

### Affected Files
- MODIFIED: `src/dot_work/prompts/agent-prompts-reference.md`
- NEW: `src/dot_work/prompts/symbiosis-map.md`

### Importance
**MEDIUM**: Symbiosis documentation:
- Enables effective prompt composition
- Reduces trial-and-error
- Improves autonomous decision-making
- Documents architectural intent

### Proposed Solution

**Symbiosis Map Structure:**

```markdown
# Prompt Symbiosis Map

## Workflow Compositions

### Code Review + Issue Creation
```
unified-review.md mode:critical
    ↓ (findings)
new-issue.md
    ↓ (issues)
issue-readiness.md
```

### Full Validation Pipeline
```
baseline.md mode:compare
    + unified-review.md mode:full
    + spec-delivery-auditor.md
    ↓ (all findings merged)
new-issue.md (if failures)
```

## Input/Output Compatibility Matrix

| Producer | Output | Consumer | Input Match |
|----------|--------|----------|-------------|
| unified-review | findings | new-issue | ✓ direct |
| baseline:compare | regressions | new-issue | ✓ direct |
| spec-delivery | gaps | new-issue | ✓ direct |
| issue-readiness | refined issues | do-work | ✓ direct |

## Anti-Patterns
- Don't run all 4 reviews separately (use unified mode:full)
- Don't establish baseline after changes (defeats purpose)
```

### Acceptance Criteria
- [ ] Workflow compositions documented
- [ ] Input/output compatibility matrix
- [ ] Anti-patterns listed
- [ ] Integration with agent-prompts-reference.md
- [ ] Mermaid diagrams for visual workflows

### Notes
- This documents the intended architecture
- Should be updated when prompts change
- Consider auto-generating from prompt metadata
