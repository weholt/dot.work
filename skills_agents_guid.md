# Skills and Subagents Getting Started Guide

This guide provides comprehensive documentation for the Skills and Subagents systems implemented in dot-work. It covers architecture, implementation details, practical usage, and maintenance considerations.

---

## IMPORTANT: Architecture Re-Evaluation

> **Status:** The current skills and subagents implementation differs significantly from how prompts work. This section documents the gaps and the target architecture to align all three systems.

### Current State vs Target State

| Aspect | Prompts (Reference) | Skills (Current) | Subagents (Current) | Target State |
|--------|---------------------|------------------|---------------------|--------------|
| **Bundled with package** | Yes (`src/dot_work/prompts/`) | No | No | Yes - bundle in package |
| **Environment config** | `environments:` in frontmatter | None | `environments:` section | Add to skills |
| **Installation via** | `dot-work install` | Discovery only | `dot-work subagents sync` (separate) | Unified `dot-work install` |
| **Global defaults** | `global.yml` | None | None | Add `global.yml` for each |
| **Discovery source** | Package prompts dir | User dirs only | User dirs only | Package dir only |

### Key Architectural Gaps

1. **No bundled skills/subagents** - Prompts ship with pre-defined content; skills and subagents don't
2. **Separate installation workflows** - `dot-work install` only handles prompts, not skills/subagents
3. **Skills lack environment awareness** - No `environments:` section in SKILL.md frontmatter
4. **Discovery from wrong locations** - Current code discovers from user dirs, not package

### Target Architecture

The target is to align skills and subagents with how prompts work:

```
src/dot_work/
├── prompts/                    # Bundled prompts (existing)
│   ├── global.yml              # Default environment configs
│   └── *.md                    # Prompt files with environments: frontmatter
│
├── skills/                     # Code module (existing)
│   ├── __init__.py
│   ├── models.py
│   └── ...
│
├── bundled_skills/             # NEW: Bundled skills for installation
│   ├── global.yml              # Default environment configs for skills
│   └── <skill-name>/
│       └── SKILL.md            # With environments: frontmatter
│
├── subagents/                  # Code module (existing)
│   ├── __init__.py
│   └── ...
│
└── bundled_subagents/          # NEW: Bundled subagents for installation
    ├── global.yml              # Default environment configs
    └── *.md                    # Canonical subagent files
```

### Environment Support Matrix

Not all environments support all content types:

| Environment | Prompts | Skills | Subagents | Notes |
|-------------|---------|--------|-----------|-------|
| Claude Code | `.claude/commands/` | `.claude/skills/` | `.claude/agents/` | Full support |
| OpenCode | `.opencode/prompts/` | Skip | `.opencode/agent/` | No native skills |
| Cursor | `.cursor/rules/` | Skip | Treat as prompt | No native agents/skills |
| Copilot | `.github/prompts/` | Skip | `.github/agents/` (maybe) | Limited agent support |
| Windsurf | `.windsurf/rules/` | Skip | Treat as prompt | No native agents/skills |
| Others | Varies | Skip | Treat as prompt | Fall back to prompt behavior |

### Required Changes for Alignment

1. **Create `src/dot_work/bundled_skills/`** with pre-defined skills
2. **Create `src/dot_work/bundled_subagents/`** with pre-defined subagents
3. **Add `environments:` frontmatter to SKILL.md format** for environment-aware installation
4. **Extend `dot-work install`** to install skills and subagents alongside prompts
5. **Update discovery** to only find bundled content (not user directories)
6. **Add `global.yml`** for skills and subagents default configs
7. **Handle unsupported environments** by skipping or treating as prompts

### Example: Environment-Aware SKILL.md (Target Format)

```markdown
---
name: code-review
description: Expert code review guidelines and checklists.
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

### Example: Unified Installation Flow (Target)

```bash
$ dot-work install --env claude

Installing for Claude Code...

Prompts:
  ✓ Installed code-review.md -> .claude/commands/code-review.md
  ✓ Installed do-work.md -> .claude/commands/do-work.md

Skills:
  ✓ Installed code-review/ -> .claude/skills/code-review/SKILL.md
  ✓ Installed debugging/ -> .claude/skills/debugging/SKILL.md

Subagents:
  ✓ Installed code-reviewer.md -> .claude/agents/code-reviewer.md
  ✓ Installed architect.md -> .claude/agents/architect.md

Done! Installed 2 prompts, 2 skills, 2 subagents.
```

---

## Table of Contents

1. [Overview](#overview)
2. [Skills System](#skills-system)
   - [Architecture](#skills-architecture)
   - [File Format](#skills-file-format)
   - [Creating Skills](#creating-skills)
   - [CLI Commands](#skills-cli-commands)
   - [Programmatic API](#skills-programmatic-api)
3. [Subagents System](#subagents-system)
   - [Architecture](#subagents-architecture)
   - [Canonical vs Native Files](#canonical-vs-native-files)
   - [Environments](#supported-environments)
   - [File Formats](#subagents-file-formats)
   - [Creating Subagents](#creating-subagents)
   - [CLI Commands](#subagents-cli-commands)
   - [Programmatic API](#subagents-programmatic-api)
4. [Integration Guide](#integration-guide)
5. [Maintenance Reference](#maintenance-reference)

---

## Overview

dot-work provides two systems for extending AI coding assistants:

| System | Purpose | Specification |
|--------|---------|---------------|
| **Skills** | Reusable capability packages that agents can load on-demand | [Agent Skills Spec](https://agentskills.io/specification) |
| **Subagents** | Custom AI agents with specialized prompts and configurations | Internal specification |

Both systems support:
- YAML frontmatter + markdown content format
- Discovery from project-local and user-global locations
- Comprehensive validation
- CLI management commands
- Programmatic Python APIs

---

## Skills System

### Skills Architecture

The skills module implements the Agent Skills specification - a system for defining reusable agent capability packages.

**Module Structure:**

```
src/dot_work/skills/
├── __init__.py           # Public API exports
├── models.py             # Data models (Skill, SkillMetadata)
├── parser.py             # SKILL.md file parser
├── discovery.py          # Filesystem skill discovery
├── validator.py          # Validation logic
├── prompt_generator.py   # XML prompt generation
└── cli.py                # Typer CLI commands
```

**Component Flow:**

```
┌─────────────────────────────────────────────────────────────────┐
│                     Skill Discovery Flow                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  .skills/my-skill/SKILL.md   ──────►  SkillParser.parse()       │
│                                              │                   │
│                                              ▼                   │
│                                    SkillMetadata / Skill         │
│                                              │                   │
│                                              ▼                   │
│                              SkillValidator.validate()           │
│                                              │                   │
│                                              ▼                   │
│                          generate_skills_prompt() ──► XML output │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Skills File Format

Skills are stored as directories containing a `SKILL.md` file with YAML frontmatter.

**Directory Structure:**

```
.skills/
└── my-skill/
    ├── SKILL.md          # Required: frontmatter + content
    ├── scripts/          # Optional: executable scripts
    │   └── setup.sh
    ├── references/       # Optional: reference documents
    │   └── api-docs.md
    └── assets/           # Optional: static assets
        └── diagram.png
```

**Search Paths (in priority order):**

1. `.skills/` (project-local)
2. `~/.config/dot-work/skills/` (user-global)

**SKILL.md Format:**

```markdown
---
name: pdf-processing
description: Extracts text and tables from PDF files using Python libraries.
license: MIT
compatibility: Requires Python 3.9+ and pdfplumber package.
metadata:
  author: Your Name
  version: 1.0.0
allowed_tools:
  - Read
  - Write
  - Bash
---

# PDF Processing Skill

This skill enables extraction of text and tabular data from PDF documents.

## Usage

1. Install dependencies:
   ```bash
   pip install pdfplumber
   ```

2. Use the `extract_text()` function for plain text extraction.

3. Use the `extract_tables()` function for structured table data.

## Examples

[Your skill content here...]
```

**Frontmatter Fields:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | Yes | 1-64 chars, `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`, no consecutive hyphens |
| `description` | string | Yes | 1-1024 chars, non-empty |
| `license` | string | No | License identifier (e.g., MIT, Apache-2.0) |
| `compatibility` | string | No | Max 500 chars |
| `metadata` | dict | No | String-to-string key-value pairs |
| `allowed_tools` | list | No | Tool names this skill may use |

**Important:** The directory name must match the `name` field in frontmatter.

### Creating Skills

**Step 1: Create the directory structure**

```bash
mkdir -p .skills/my-skill
```

**Step 2: Create SKILL.md**

```bash
cat > .skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: A brief description of what this skill does.
license: MIT
---

# My Skill

Detailed instructions for using this skill...
EOF
```

**Step 3: Validate**

```bash
uv run dot-work skills validate .skills/my-skill
```

**Step 4: Test discovery**

```bash
uv run dot-work skills list
uv run dot-work skills show my-skill
```

### Skills CLI Commands

All commands are under `dot-work skills`:

| Command | Description | Example |
|---------|-------------|---------|
| `list` | List all discovered skills | `dot-work skills list` |
| `validate` | Validate a skill directory | `dot-work skills validate .skills/my-skill` |
| `show` | Display full skill content | `dot-work skills show pdf-processing` |
| `prompt` | Generate XML for system prompts | `dot-work skills prompt` |
| `install` | Install a skill to project | `dot-work skills install ~/my-skills/pdf` |

**Detailed Usage:**

```bash
# List skills with additional search paths
dot-work skills list --path ./custom-skills --path ~/more-skills

# Validate (accepts directory or SKILL.md file)
dot-work skills validate .skills/my-skill
dot-work skills validate .skills/my-skill/SKILL.md

# Generate prompt without file paths
dot-work skills prompt --no-paths

# Install to custom location
dot-work skills install ~/my-skills/pdf --target ./project-skills
```

### Skills Programmatic API

**Imports:**

```python
from dot_work.skills import (
    # Models
    Skill,
    SkillMetadata,
    
    # Parser
    SkillParser,
    SKILL_PARSER,
    SkillParserError,
    
    # Discovery
    SkillDiscovery,
    DEFAULT_DISCOVERY,
    
    # Validation
    SkillValidator,
    SKILL_VALIDATOR,
    ValidationResult,
    
    # Generation
    generate_skills_prompt,
    generate_skill_prompt,
)
```

**Common Operations:**

```python
from pathlib import Path
from dot_work.skills import (
    SkillDiscovery,
    SKILL_PARSER,
    SKILL_VALIDATOR,
    generate_skills_prompt,
)

# Discover all skills
discovery = SkillDiscovery()
skills = discovery.discover()  # Returns list[SkillMetadata]

# Load a specific skill with full content
skill = discovery.load_skill("pdf-processing")  # Returns Skill
print(skill.content)  # Markdown body
print(skill.scripts)  # list[Path] or None

# Parse a skill directly
skill = SKILL_PARSER.parse(Path(".skills/my-skill"))
metadata = SKILL_PARSER.parse_metadata_only(Path(".skills/my-skill"))

# Validate a skill
result = SKILL_VALIDATOR.validate_directory(Path(".skills/my-skill"))
if not result.valid:
    for error in result.errors:
        print(f"Error: {error}")
for warning in result.warnings:
    print(f"Warning: {warning}")

# Generate XML prompt for agent system prompts
xml = generate_skills_prompt(skills, include_paths=True)
```

**Generated XML Format:**

```xml
<available_skills>
  <skill>
    <name>pdf-processing</name>
    <description>Extracts text and tables from PDF files...</description>
    <location>.skills/pdf-processing/SKILL.md</location>
    <license>MIT</license>
  </skill>
</available_skills>
```

---

## Subagents System

### Subagents Architecture

The subagents module provides a "write once, deploy everywhere" approach where canonical subagent definitions can be automatically converted to environment-specific native formats.

**Module Structure:**

```
src/dot_work/subagents/
├── __init__.py           # Public API exports
├── models.py             # Data models
├── parser.py             # YAML frontmatter parser
├── discovery.py          # Subagent discovery
├── validator.py          # Validation rules
├── generator.py          # Environment-specific generation
├── cli.py                # CLI commands
└── environments/
    ├── __init__.py       # Environment registry
    ├── base.py           # Abstract base adapter
    ├── claude_code.py    # Claude Code adapter
    ├── opencode.py       # OpenCode adapter
    └── copilot.py        # GitHub Copilot adapter
```

**Component Flow:**

```
┌────────────────────────────────────────────────────────────────────────┐
│                     Canonical → Native Generation                       │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  .work/subagents/reviewer.md   ──────►  SubagentParser.parse()         │
│          (canonical)                           │                        │
│                                                ▼                        │
│                                       CanonicalSubagent                 │
│                                                │                        │
│                     ┌──────────────────────────┼──────────────────────┐ │
│                     ▼                          ▼                      ▼ │
│              ClaudeCodeAdapter          OpenCodeAdapter        CopilotAdapter
│                     │                          │                      │ │
│                     ▼                          ▼                      ▼ │
│           .claude/agents/           .opencode/agent/        .github/agents/
│           reviewer.md               reviewer.md             reviewer.md
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### Canonical vs Native Files

**Canonical Subagents:**
- Single source of truth stored in `.work/subagents/`
- Contains base configuration + per-environment overrides
- Used to generate environment-specific native files

**Native Subagents:**
- Environment-specific files in their respective directories
- Generated from canonical or written directly
- Format varies by environment

**Locations:**

| Type | Location |
|------|----------|
| Canonical (project) | `.work/subagents/` |
| Canonical (user) | `~/.config/dot-work/subagents/` |
| Claude Code native | `.claude/agents/` |
| OpenCode native | `.opencode/agent/` |
| Copilot native | `.github/agents/` |

### Supported Environments

| Environment | Target Directory | Key Features |
|-------------|------------------|--------------|
| `claude` | `.claude/agents/` | Permission modes, skills integration |
| `opencode` | `.opencode/agent/` | Temperature, max steps, granular permissions |
| `copilot` | `.github/agents/` | MCP servers, infer flag |

**Environment-Specific Features:**

| Feature | Claude | OpenCode | Copilot |
|---------|--------|----------|---------|
| `model` | sonnet/opus/haiku/inherit | provider/model-id | - |
| `permissionMode` | default/acceptEdits/bypassPermissions/plan | - | - |
| `mode` | - | primary/subagent/all | - |
| `temperature` | - | 0.0-2.0 | - |
| `maxSteps` | - | integer >= 1 | - |
| `skills` | list of skill names | - | - |
| `infer` | - | - | boolean |
| `target` | - | - | vscode/github-copilot |
| `mcpServers` | - | - | server config dict |

### Subagents File Formats

#### Canonical Format

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
    maxSteps: 100

  copilot:
    target: ".github/agents/"
    infer: true

# Common configuration (can be overridden per-environment)
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

You are a senior code reviewer ensuring high standards of code quality,
security, and maintainability.

## Review Guidelines

1. Focus on code correctness and logic errors
2. Check for security vulnerabilities
3. Evaluate performance implications
4. Ensure consistent code style

## Output Format

Provide structured feedback with:
- Summary of findings
- Critical issues (must fix)
- Suggestions (nice to have)
- Positive observations
```

**Canonical Frontmatter Fields:**

| Section | Field | Type | Description |
|---------|-------|------|-------------|
| `meta` | `name` | string | Required, 1-64 chars, lowercase+hyphens |
| `meta` | `description` | string | Required, 1-1024 chars |
| `environments.<env>` | `target` | string | Required, target directory |
| `environments.<env>` | `model` | string | Model override |
| `environments.<env>` | `permissionMode` | string | Claude only |
| `environments.<env>` | `mode` | string | OpenCode only |
| `environments.<env>` | `temperature` | float | OpenCode only |
| `environments.<env>` | `maxSteps` | int | OpenCode only |
| `environments.<env>` | `skills` | list | Claude only |
| `environments.<env>` | `infer` | bool | Copilot only |
| `environments.<env>` | `tools` | list | Environment-specific tools |
| (root) | `tools` | list | Base tools (overridden by env) |

#### Claude Code Native Format

```markdown
---
name: code-reviewer
description: Expert code reviewer for quality and security.
model: sonnet
permissionMode: default
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
skills:
  - code-review
---

Your system prompt here...
```

#### OpenCode Native Format

```markdown
---
name: code-reviewer
description: Expert code reviewer for quality and security.
mode: subagent
model: anthropic/claude-sonnet
temperature: 0.1
maxSteps: 100
tools:
  read: true
  write: true
  edit: true
  bash: true
  grep: true
permissions:
  bash:
    allow:
      - "npm test"
      - "npm run lint"
---

Your system prompt here...
```

#### Copilot Native Format

```markdown
---
name: code-reviewer
description: Expert code reviewer for quality and security.
target: vscode
infer: true
tools:
  - read
  - edit
  - search
mcpServers:
  my-server:
    url: https://example.com/mcp
---

Your system prompt here...
```

### Creating Subagents

#### Method 1: Using CLI Init (Recommended)

```bash
# Create a new canonical subagent template
uv run dot-work subagents init code-reviewer \
  --description "Expert code reviewer for quality and security"

# Specify target environments
uv run dot-work subagents init debugger \
  --description "Root cause analysis specialist" \
  --env claude \
  --env opencode

# Custom output path
uv run dot-work subagents init my-agent \
  --description "My custom agent" \
  -o ./custom/path/my-agent.md
```

This creates a template at `.work/subagents/<name>.md`.

#### Method 2: Manual Creation

**Step 1: Create the directory**

```bash
mkdir -p .work/subagents
```

**Step 2: Create the canonical file**

```bash
cat > .work/subagents/my-agent.md << 'EOF'
---
meta:
  name: my-agent
  description: Description of what this agent does.

environments:
  claude:
    target: ".claude/agents/"
    model: sonnet
  opencode:
    target: ".opencode/agent/"
    mode: subagent

tools:
  - Read
  - Grep
  - Glob
---

You are an AI assistant specialized in...

## Instructions

Add your detailed instructions here.
EOF
```

**Step 3: Validate**

```bash
uv run dot-work subagents validate .work/subagents/my-agent.md
```

**Step 4: Generate native files**

```bash
# Generate for a specific environment
uv run dot-work subagents generate .work/subagents/my-agent.md --env claude

# Sync to all configured environments
uv run dot-work subagents sync .work/subagents/my-agent.md
```

### Subagents CLI Commands

All commands are under `dot-work subagents`:

| Command | Description | Example |
|---------|-------------|---------|
| `list` | List discovered native subagents | `dot-work subagents list --env claude` |
| `validate` | Validate a subagent file | `dot-work subagents validate path/to/file.md` |
| `show` | Display subagent details | `dot-work subagents show code-reviewer` |
| `generate` | Generate native from canonical | `dot-work subagents generate path.md --env claude` |
| `sync` | Sync canonical to all environments | `dot-work subagents sync path.md` |
| `init` | Create new canonical template | `dot-work subagents init name -d "description"` |
| `envs` | List supported environments | `dot-work subagents envs` |

**Detailed Usage:**

```bash
# List subagents for different environments
dot-work subagents list                    # Default: claude
dot-work subagents list --env opencode
dot-work subagents list --env copilot

# Validate canonical or native files
dot-work subagents validate .work/subagents/code-reviewer.md  # canonical
dot-work subagents validate .claude/agents/code-reviewer.md   # native

# Show subagent details
dot-work subagents show code-reviewer --env claude
dot-work subagents show code-reviewer --env opencode

# Generate native file with output path
dot-work subagents generate .work/subagents/reviewer.md \
  --env opencode \
  -o .opencode/agent/reviewer.md

# Preview generated content (stdout)
dot-work subagents generate .work/subagents/reviewer.md --env claude
```

### Subagents Programmatic API

**Imports:**

```python
from dot_work.subagents import (
    # Models
    SubagentMetadata,
    SubagentConfig,
    SubagentEnvironmentConfig,
    CanonicalSubagent,
    
    # Parser
    SubagentParser,
    SUBAGENT_PARSER,
    
    # Validator
    SubagentValidator,
    SUBAGENT_VALIDATOR,
    
    # Discovery
    SubagentDiscovery,
    DEFAULT_DISCOVERY,
    
    # Generator
    SubagentGenerator,
    SUBAGENT_GENERATOR,
)

from dot_work.subagents.environments import (
    get_adapter,
    get_supported_environments,
    SubagentEnvironmentAdapter,
    ClaudeCodeAdapter,
    OpenCodeAdapter,
    CopilotAdapter,
)
```

**Common Operations:**

```python
from pathlib import Path
from dot_work.subagents import (
    SubagentDiscovery,
    SUBAGENT_PARSER,
    SUBAGENT_VALIDATOR,
    SUBAGENT_GENERATOR,
)

# Discover native subagents for an environment
discovery = SubagentDiscovery(project_root=".", environment="claude")
native_agents = discovery.discover_native()  # list[SubagentConfig]

# Discover canonical subagents
canonical_agents = discovery.discover_canonical()  # list[CanonicalSubagent]

# Load a specific native subagent
config = discovery.load_native("code-reviewer")
print(config.name)
print(config.description)
print(config.prompt)  # The markdown body

# Load a specific canonical subagent
canonical = discovery.load_canonical("code-reviewer")
print(canonical.meta.name)
print(canonical.environments)  # dict[str, SubagentEnvironmentConfig]

# Parse a canonical file directly
canonical = SUBAGENT_PARSER.parse(Path(".work/subagents/reviewer.md"))

# Validate a subagent
result = SUBAGENT_VALIDATOR.validate(Path(".work/subagents/reviewer.md"))
if not result.valid:
    for error in result.errors:
        print(f"Error: {error}")

# Generate native file content
content = SUBAGENT_GENERATOR.generate_native(canonical, "claude")
print(content)

# Generate and write native file
output_path = SUBAGENT_GENERATOR.generate_native_file(
    canonical,
    "claude",
    project_root=Path("."),
)
print(f"Generated: {output_path}")

# Generate for all environments
generated = SUBAGENT_GENERATOR.generate_all(canonical, Path("."))
for env, path in generated.items():
    print(f"{env}: {path}")

# Create a new canonical template
template = SUBAGENT_GENERATOR.generate_canonical_template(
    name="my-agent",
    description="My agent description",
    environments=["claude", "opencode"],
)
Path(".work/subagents/my-agent.md").write_text(template)
```

**Working with Environment Adapters:**

```python
from dot_work.subagents.environments import get_adapter, get_supported_environments

# List supported environments
envs = get_supported_environments()  # ["claude", "opencode", "copilot"]

# Get an adapter
adapter = get_adapter("claude")
print(adapter.DEFAULT_TARGET)  # ".claude/agents/"

# Get target path for a project
target = adapter.get_target_path(Path("."))  # Path(".claude/agents/")

# Map tool names
tools = adapter.map_tools(["Read", "Write", "Bash"])

# Generate native content from SubagentConfig
native_content = adapter.generate_native(config)
```

---

## Integration Guide

### Adding Skills to Agent Prompts

To make skills available to agents, inject the generated XML into the system prompt:

```python
from dot_work.skills import DEFAULT_DISCOVERY, generate_skills_prompt

def build_system_prompt():
    # Discover available skills
    skills = DEFAULT_DISCOVERY.discover()
    
    # Generate XML block
    skills_xml = generate_skills_prompt(skills, include_paths=True)
    
    # Inject into system prompt
    return f"""
You are a helpful AI assistant.

{skills_xml}

When a task matches an available skill, load it for detailed instructions.
"""
```

### Deploying Subagents to Multiple Environments

Use the sync workflow for consistent multi-environment deployment:

```python
from pathlib import Path
from dot_work.subagents import SUBAGENT_PARSER, SUBAGENT_GENERATOR

def deploy_subagent(canonical_path: Path) -> dict[str, Path]:
    """Deploy a canonical subagent to all configured environments."""
    # Parse canonical
    canonical = SUBAGENT_PARSER.parse(canonical_path)
    
    # Generate for all environments
    return SUBAGENT_GENERATOR.generate_all(canonical, Path("."))
```

### Custom Environment Adapter

To support a new AI environment:

```python
from dot_work.subagents.environments.base import SubagentEnvironmentAdapter
from dot_work.subagents import SubagentConfig

class MyEnvironmentAdapter(SubagentEnvironmentAdapter):
    TOOL_MAP = {
        "Read": "read_file",
        "Write": "write_file",
        "Bash": "run_command",
    }
    DEFAULT_TARGET = ".myenv/agents/"
    
    def get_target_path(self, project_root: Path) -> Path:
        return project_root / self.DEFAULT_TARGET
    
    def generate_native(self, config: SubagentConfig) -> str:
        # Generate environment-specific format
        ...
    
    def parse_native(self, content: str) -> SubagentConfig:
        # Parse native format back to config
        ...

# Register the adapter (would need to modify environments/__init__.py)
```

---

## Maintenance Reference

### Key Files to Understand

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `skills/models.py` | Data structures | `Skill`, `SkillMetadata` |
| `skills/parser.py` | YAML/markdown parsing | `SkillParser`, `SKILL_PARSER` |
| `skills/discovery.py` | Filesystem discovery | `SkillDiscovery`, `DEFAULT_DISCOVERY` |
| `skills/validator.py` | Validation rules | `SkillValidator`, `ValidationResult` |
| `skills/prompt_generator.py` | XML generation | `generate_skills_prompt()` |
| `subagents/models.py` | Data structures | `SubagentConfig`, `CanonicalSubagent` |
| `subagents/parser.py` | YAML/markdown parsing | `SubagentParser`, `SUBAGENT_PARSER` |
| `subagents/discovery.py` | Filesystem discovery | `SubagentDiscovery` |
| `subagents/validator.py` | Validation rules | `SubagentValidator` |
| `subagents/generator.py` | Native file generation | `SubagentGenerator` |
| `subagents/environments/base.py` | Adapter interface | `SubagentEnvironmentAdapter` |

### Validation Rules

**Skills:**

| Rule | Level | Description |
|------|-------|-------------|
| Name format | Error | Must match `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$` |
| Name length | Error | 1-64 characters |
| Description required | Error | Cannot be empty |
| Description length | Error | 1-1024 characters |
| Directory name match | Error | Directory name must equal `meta.name` |
| SKILL.md exists | Error | Required file |
| Reserved names | Warning | "test", "example", "sample" |
| Short description | Warning | Less than 3 words |
| Long content | Warning | Over 20,000 characters |

**Subagents:**

| Rule | Level | Description |
|------|-------|-------------|
| Name format | Error | Must match `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$` |
| Prompt required | Error | Cannot be empty |
| Tools must be list | Error | If provided |
| Temperature range | Error | Must be 0.0-2.0 if provided |
| max_steps positive | Error | Must be >= 1 if provided |
| Environment has target | Error | Target directory required |
| Short description | Warning | Less than 20 characters |
| Short prompt | Warning | Less than 50 characters |
| Unknown permission_mode | Warning | Not in valid values |
| Unknown environment | Warning | Not in supported list |

### Extending the System

**Adding a new skill field:**

1. Update `SkillMetadata` in `skills/models.py`
2. Update `SkillParser._parse_frontmatter()` in `skills/parser.py`
3. Add validation in `SkillValidator` if needed
4. Update `generate_skill_prompt()` if XML output should include it

**Adding a new subagent environment:**

1. Create `environments/my_env.py` with adapter class
2. Register in `environments/__init__.py` `_ADAPTERS` dict
3. Add validation rules in `validator.py`
4. Update CLI help text in `cli.py`

**Adding new validation rules:**

1. Skills: Update `SkillValidator.validate()` in `skills/validator.py`
2. Subagents: Update `SubagentValidator._validate_*()` methods

### Common Maintenance Tasks

**Adding tool mappings for a new tool:**

```python
# In each environment adapter, update TOOL_MAP:

# claude_code.py
TOOL_MAP = {
    ...
    "NewTool": "NewTool",  # Claude uses same names
}

# opencode.py
TOOL_MAP = {
    ...
    "NewTool": "newtool",  # OpenCode uses lowercase
}

# copilot.py
TOOL_MAP = {
    ...
    "NewTool": "new_tool",  # Copilot uses snake_case
}
```

**Updating frontmatter field names:**

The parser supports both camelCase and snake_case for compatibility. When adding new fields, add normalization in `SubagentParser._extract_config()`:

```python
# Support both camelCase and snake_case
my_field = frontmatter.get("myField") or frontmatter.get("my_field")
```

### Testing

Run tests with memory protection:

```bash
# Run all skill/subagent tests
./scripts/pytest-with-cgroup.sh 30 tests/unit/ -v -k "skill or subagent"

# Run specific test file
./scripts/pytest-with-cgroup.sh 30 tests/unit/test_skills.py -v
```

---

## Quick Reference

### Skills Cheat Sheet

```bash
# Create skill
mkdir -p .skills/my-skill
# Edit .skills/my-skill/SKILL.md

# Validate
dot-work skills validate .skills/my-skill

# List all
dot-work skills list

# Show details
dot-work skills show my-skill

# Generate XML prompt
dot-work skills prompt
```

### Subagents Cheat Sheet

```bash
# Create subagent
dot-work subagents init my-agent -d "Description"

# Validate
dot-work subagents validate .work/subagents/my-agent.md

# Generate for one environment
dot-work subagents generate .work/subagents/my-agent.md --env claude

# Sync to all environments
dot-work subagents sync .work/subagents/my-agent.md

# List native subagents
dot-work subagents list --env claude

# Show details
dot-work subagents show my-agent --env claude

# List environments
dot-work subagents envs
```

---

## Implementation Roadmap

This section outlines the changes needed to align skills and subagents with the prompts installation pattern.

### Phase 1: Create Bundled Content Directories

**Goal:** Establish the package structure for bundled skills and subagents.

**Tasks:**

1. Create `src/dot_work/bundled_skills/` directory
2. Create `src/dot_work/bundled_subagents/` directory
3. Create `global.yml` for each with default environment configs
4. Update `pyproject.toml` to include these directories in the wheel

**Files to create:**

```
src/dot_work/bundled_skills/
├── global.yml
└── .gitkeep

src/dot_work/bundled_subagents/
├── global.yml
└── .gitkeep
```

**global.yml for skills:**

```yaml
defaults:
  environments:
    claude:
      target: ".claude/skills/"
      # Skills are directories, so filename handling differs
```

**global.yml for subagents:**

```yaml
defaults:
  environments:
    claude:
      target: ".claude/agents/"
      filename_suffix: ".md"
    
    opencode:
      target: ".opencode/agent/"
      filename_suffix: ".md"
```

### Phase 2: Add Environment Support to Skills

**Goal:** Enable skills to have environment-aware installation like prompts.

**Tasks:**

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

### Phase 3: Extend Installer for Skills and Subagents

**Goal:** Make `dot-work install` handle all content types.

**Tasks:**

1. Create `get_bundled_skills_dir()` and `get_bundled_subagents_dir()` functions
2. Create `install_skills_by_environment()` function
3. Create `install_subagents_by_environment()` function
4. Update `install_prompts()` to also call skill/subagent installers
5. Handle environments that don't support skills/subagents (skip gracefully)

**New installer functions:**

```python
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
    # Check if environment supports skills
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

### Phase 4: Create Bundled Content

**Goal:** Ship pre-defined skills and subagents with dot-work.

**Tasks:**

1. Create initial bundled skills (code-review, debugging, etc.)
2. Create initial bundled subagents (code-reviewer, architect, etc.)
3. Each with proper `environments:` frontmatter
4. Validate all bundled content in CI

**Example bundled skill:**

```
src/dot_work/bundled_skills/code-review/
└── SKILL.md
```

```markdown
---
name: code-review
description: Comprehensive code review guidelines and checklists.
license: MIT

environments:
  claude:
    target: ".claude/skills/"
---

# Code Review Skill

This skill provides structured guidance for performing thorough code reviews.

## Review Categories

### Security Review
- Check for injection vulnerabilities
- Verify authentication/authorization
- Review sensitive data handling

### Performance Review
- Identify inefficient algorithms
- Check for memory leaks
- Review database query patterns

[...]
```

**Example bundled subagent:**

```
src/dot_work/bundled_subagents/code-reviewer.md
```

```markdown
---
meta:
  name: code-reviewer
  description: Expert code reviewer for quality and security.

environments:
  claude:
    target: ".claude/agents/"
    filename_suffix: ".md"
    model: sonnet
    permissionMode: default
  
  opencode:
    target: ".opencode/agent/"
    filename_suffix: ".md"
    mode: subagent
---

You are a senior code reviewer ensuring high standards...
```

### Phase 5: Update Discovery to Use Bundled Content Only

**Goal:** Skills and subagents discovery should only find bundled content.

**Tasks:**

1. Update `SkillDiscovery` default paths to use `get_bundled_skills_dir()`
2. Update `SubagentDiscovery` default paths to use `get_bundled_subagents_dir()`
3. Remove user-global paths (`~/.config/dot-work/skills/` etc.)
4. Keep project-local discovery for user-created content separate

**Note:** User-created skills/subagents in project directories should still be discoverable via explicit `--path` arguments, but are not part of the install flow.

### Phase 6: Update CLI and Documentation

**Goal:** Unified user experience.

**Tasks:**

1. Update `dot-work install` help text to mention skills/subagents
2. Add `--skip-skills` and `--skip-subagents` flags if needed
3. Update `dot-work list` to show skill/subagent support per environment
4. Update README and documentation

### Implementation Priority

| Phase | Priority | Estimated Effort | Dependencies |
|-------|----------|------------------|--------------|
| Phase 1 | High | 2-4 hours | None |
| Phase 2 | High | 4-6 hours | Phase 1 |
| Phase 3 | High | 6-8 hours | Phase 2 |
| Phase 4 | Medium | 4-8 hours | Phase 3 |
| Phase 5 | Medium | 2-4 hours | Phase 3 |
| Phase 6 | Low | 2-4 hours | Phase 4-5 |

### Code Location Reference

| Component | Current Location | Changes Needed |
|-----------|------------------|----------------|
| Prompt installation | `installer.py` | Extend to call skill/subagent installers |
| Prompt global.yml | `prompts/global.yml` | Reference pattern |
| Skill models | `skills/models.py` | Add `environments` field |
| Skill parser | `skills/parser.py` | Parse environments from frontmatter |
| Skill discovery | `skills/discovery.py` | Change default paths |
| Subagent models | `subagents/models.py` | Already has environments |
| Subagent parser | `subagents/parser.py` | Already parses environments |
| Subagent discovery | `subagents/discovery.py` | Change default paths |
| Environment config | `environments.py` | Add skill/subagent support flags |

---

## Summary

The current skills and subagents implementation provides the building blocks (models, parsers, validators, CLI) but lacks integration with the main `dot-work install` flow. The target architecture aligns all three content types (prompts, skills, subagents) with a consistent pattern:

1. **Bundled in package** - Ship pre-defined content
2. **Environment-aware** - Use `environments:` frontmatter for per-environment config
3. **Unified installation** - Single `dot-work install` command handles all
4. **Graceful fallbacks** - Skip unsupported content types or treat as prompts

The existing code modules (`skills/`, `subagents/`) provide solid foundations for validation, parsing, and generation. The main work is:
- Creating bundled content directories
- Adding environment support to skills
- Extending the installer to handle all content types
- Shipping useful pre-defined skills and subagents
