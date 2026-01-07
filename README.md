# 🛠️ dot-work

**Portable AI coding prompts** for project scaffolding and issue tracking.

Works with: GitHub Copilot, Claude Code, Cursor, Windsurf, Aider, Continue.dev, Amazon Q, Zed AI, OpenCode, and more.

> **Note:** The dot-work project is migrating to a plugin architecture. The following submodules have been extracted to standalone packages:
> - **dot-issues**: SQLite-based issue tracking
> - **dot-kg**: Knowledge graph with FTS5 search
> - **dot-review**: Interactive code review with web UI
> - **dot-container**: Docker provisioning for AI agents
> - **dot-git**: Git history analysis and metrics
> - **dot-harness**: Claude Agent SDK integration
> - **dot-overview**: Codebase overview generation
> - **dot-python**: Python build and scan utilities
> - **dot-version**: Date-based version management
>
> See [docs/plugins.md](docs/plugins.md) for details on the plugin architecture.

## 🎯 What This Does

This tool provides **12 AI agent prompts** for:

- **Project scaffolding** - Turn discussions into production-ready projects
- **Workflow management** - Issue tracking, focus, and iteration loops
- **Quality assurance** - Baselines, code reviews, and delivery auditing
- **Version control** - Date-based versioning with changelog generation

The installer detects your AI coding environment and puts the prompts in the right place so they work as slash commands.

## 🚫 Non-Goals

dot-work is a **human-directed AI agent framework** for issue management and autonomous agent implementation. It does **NOT**:

- Replace full project management tools (Jira, Linear, GitHub Projects, etc.)
- Provide autonomous agents without human direction
- Host prompts or provide cloud services
- Manage dependencies or build systems
- Replace git workflow tools
- Provide CI/CD integration or deployment pipelines
- Replace code review platforms (GitHub PRs, GitLab MRs)
- Offer team collaboration features (comments, mentions, threads)
- Perform automated testing or quality assurance

### What dot-work Is

A **local development tool** for AI-assisted coding workflows with human oversight:

- Portable prompt templates for AI coding environments
- File-based issue tracking for agent-driven development
- Quality assurance workflows (baselines, reviews, audits)
- Version control integration (not replacement)

### What to Use Instead

| For... | Use... |
|--------|--------|
| Project management | Jira, Linear, GitHub Projects |
| CI/CD pipelines | GitHub Actions, GitLab CI, CircleCI |
| Code review | GitHub PRs, GitLab MRs, Phabricator |
| Automated testing | pytest, Jest, CI systems |
| Team collaboration | Slack, Discord, email |
| Dependency management | poetry, npm, cargo, pip-tools |

## 🚀 Quick Start

### Install with uv

```bash
# Install as a tool
uv tool install dot-work

# Or run directly without installing
uvx dot-work install --env copilot
```

### Usage

```bash
# Interactive mode - detects or asks for your environment
dot-work install

# Specify environment directly
dot-work install --env copilot
dot-work install --env claude
dot-work install --env opencode

# Install to a specific directory
dot-work install --env cursor --target /path/to/project

# With uvx (no installation needed)
uvx dot-work install --env copilot --target .
```

### Available Commands

```bash
dot-work install    # Install prompts to your project
dot-work list       # List supported AI environments
dot-work detect     # Detect environment in current directory
dot-work init work  # Initialize .work/ issue tracking directory
dot-work review     # Interactive code review with AI export
dot-work validate   # Validate JSON/YAML files
dot-work --help     # Show help
```

## 🔍 Code Review

The `review` command provides an interactive web interface for reviewing code changes and exporting comments for AI agents.

### Start a Review

```bash
# Start the review server (opens web UI)
dot-work review start

# Review against a specific base commit
dot-work review start --base main

# Use a custom port
dot-work review start --port 3000
```

The web interface shows:
- File tree with changed files highlighted
- Side-by-side and unified diff views
- Click any line to add comments or suggestions
- Syntax highlighting for common languages

### Export Comments

```bash
# Export review comments as markdown (for AI agents)
dot-work review export

# Export to a specific file
dot-work review export --output review-feedback.md

# Export a specific review
dot-work review export --review-id 20241221-143500
```

The exported markdown is formatted for AI consumption with:
- File paths and line numbers
- Comment text and suggestions
- Context for each comment

### Clear Reviews

```bash
# Clear all stored reviews
dot-work review clear --force

# Clear a specific review
dot-work review clear --review-id 20241221-143500
```

### Review Workflow

1. Make changes to your code
2. Run `dot-work review start` to open the review UI
3. Click lines to add comments and suggestions
4. Run `dot-work review export` to generate markdown
5. Pass the exported file to your AI agent for fixes

## 📦 Supported Environments

```bash
dot-work list
```

| Key | Environment | Prompt Location |
|-----|-------------|-----------------|
| `copilot` | GitHub Copilot (VS Code) | `.github/prompts/*.prompt.md` |
| `claude` | Claude Code | `CLAUDE.md` |
| `cursor` | Cursor | `.cursor/rules/*.mdc` |
| `windsurf` | Windsurf (Codeium) | `.windsurf/rules/*.md` |
| `aider` | Aider | `CONVENTIONS.md` |
| `continue` | Continue.dev | `.continue/prompts/*.md` |
| `amazon-q` | Amazon Q Developer | `.amazonq/rules.md` |
| `zed` | Zed AI | `.zed/prompts/*.md` |
| `opencode` | OpenCode | `.opencode/prompts/*.md` + `AGENTS.md` |
| `generic` | Generic / Manual | `prompts/*.md` + `AGENTS.md` |

## 🎮 How to Use Prompts

After installing, use the prompts in your AI environment:

| Environment | How to Use |
|-------------|------------|
| **GitHub Copilot** | `/project-from-discussion` or `/issue-tracker-setup` |
| **Claude Code** | Automatically reads `CLAUDE.md` |
| **Cursor** | Available in `@` menu from `.cursor/rules/` |
| **Windsurf** | Available from `.windsurf/rules/` |
| **Aider** | Reads `CONVENTIONS.md` automatically |
| **Continue.dev** | Slash commands in `.continue/prompts/` |
| **Amazon Q** | Reads `.amazonq/rules.md` |
| **Zed AI** | Available from `.zed/prompts/` |
| **OpenCode** | Reads `AGENTS.md` + `.opencode/prompts/` |
| **Generic** | Reference `prompts/*.md` manually |

## 📋 The Prompts

### 🏗️ Project Setup

| Prompt | Description |
|--------|-------------|
| **`python-project-from-discussion`** | Transform a project discussion into a complete Python project with `pyproject.toml`, `src/` layout, CLI, tests, and `AGENTS.md` |
| **`setup-issue-tracker`** | Initialize `.work/` directory with priority-based issue tracking, focus management, and agent memory |

### 🔄 Workflow & Iteration

| Prompt | Description |
|--------|-------------|
| **`do-work`** | Optimal iteration loop for AI agents: baseline → select → investigate → implement → validate → complete |
| **`new-issue`** | Create properly formatted issues with ID, priority, tags, and acceptance criteria |
| **`agent-prompts-reference`** | Quick reference for all available prompts and their trigger commands |

### ✅ Quality Assurance

| Prompt | Description |
|--------|-------------|
| **`establish-baseline`** | Capture current project state (tests, coverage, lint, types) before making changes |
| **`compare-baseline`** | Compare current state against baseline to detect regressions |
| **`critical-code-review`** | Deep code review focusing on correctness, security, and maintainability |
| **`spec-delivery-auditor`** | Verify implementation matches specification with gap analysis |
| **`improvement-discovery`** | Analyze codebase for justified improvements with cost/benefit analysis |

### 🔧 Utilities

| Prompt | Description |
|--------|-------------|
| **`bump-version`** | Date-based version bumping with safety checks and multi-file sync |
| **`api-export`** | Generate API documentation or export specifications |

---

### Usage Examples

**Start a new project:**
```
/python-project-from-discussion

Here's my project idea: [paste discussion]
```

**Set up issue tracking:**
```
/setup-issue-tracker
```

**Begin an iteration:**
```
/do-work
```

**Freeze version after changes:**
```bash
dot-work version freeze
```

This creates a new version, updates `version.json`, and appends to `CHANGELOG.md`.

---

## 🎯 Skills

**Skills** are reusable capability packages that AI agents can load on-demand. They provide specialized knowledge and workflows for specific tasks.

### What Skills Are

Skills are complementary to prompts and subagents:
- **Prompts** - One-time instructions for specific tasks (slash commands)
- **Skills** - Reusable capability packages with structured knowledge
- **Subagents** - AI personalities with specialized behaviors

### Bundled Skills

dot-work includes 3 pre-installed skills:

| Skill | Description |
|-------|-------------|
| **`code-review`** | Expert code review guidelines for quality, security, and maintainability |
| **`debugging`** | Systematic debugging approaches for isolating and fixing software defects |
| **`test-driven-development`** | TDD workflow for writing reliable, maintainable code |

### Skills Support

| Environment | Skills Support |
|-------------|----------------|
| Claude Code | ✅ Full support (`.claude/skills/`) |
| Other environments | ❌ Not supported (skills are Claude Code specific) |

### Creating Custom Skills

Skills use YAML frontmatter + markdown format:

```markdown
---
name: my-skill
description: A brief description of what this skill does
license: MIT
environments:
  claude:
    target: ".claude/skills/"
    filename_suffix: "/my-skill/SKILL.md"
---

# My Skill

Detailed instructions and knowledge...
```

For detailed documentation, see [skills_agents_guid.md](skills_agents_guid.md).

---

## 🤖 Subagents

**Subagents** are custom AI agent personalities with specialized prompts and configurations for multi-environment deployment.

### What Subagents Are

Subagents define AI personalities that can be deployed across different AI coding environments. Each subagent has:
- Canonical definition with environment-specific configurations
- Specialized prompts and behaviors
- Tool mappings per environment

### Bundled Subagents

dot-work includes 6 pre-installed subagents:

| Subagent | Description |
|----------|-------------|
| **`code-reviewer`** | Senior code reviewer with security and performance focus |
| **`test-runner`** | Test engineering specialist |
| **`debugger`** | Systematic debugging specialist |
| **`docs-writer`** | Technical documentation specialist |
| **`security-auditor`** | Security-focused code reviewer |
| **`refactorer`** | Code restructuring and optimization specialist |

### Subagent Environments

| Environment | Subagent Support |
|-------------|------------------|
| Claude Code | ✅ Native agents (`.claude/agents/`) |
| OpenCode | ✅ Native agents (`.opencode/agent/`) |
| GitHub Copilot | ✅ GitHub agents (`.github/agents/`) |
| Cursor/Windsurf | Treated as prompts (`.cursor/rules/`) |

### Creating Custom Subagents

Subagents use canonical format with environment configs:

```markdown
---
meta:
  name: my-subagent
  description: A brief description
config:
  name: my-subagent
  description: A brief description

environments:
  claude:
    target: ".claude/agents/"
    model: claude-sonnet-4-5
  opencode:
    target: ".opencode/agent/"
    mode: planner
  copilot:
    target: ".github/agents/"
---

# My Subagent

Specialized instructions and personality...
```

For detailed documentation, see [skills_agents_guid.md](skills_agents_guid.md).

---

## 🔄 Workflow Example

1. **Create a new project directory**:
   ```bash
   mkdir my-project && cd my-project
   ```

2. **Install dot-work prompts**:
   ```bash
   uvx dot-work install --env copilot
   ```

3. **Use the project prompt** in your AI tool:
   ```
   /python-project-from-discussion
   
   I want to build a CLI tool that...
   ```

4. **Set up issue tracking**:
   ```
   /setup-issue-tracker
   ```

5. **Start iterating** with the workflow prompt:
   ```
   /do-work
   ```

6. **The AI agent now has:**
   - Complete project structure
   - Issue tracking for tasks
   - Memory persistence across sessions
   - Quality assurance workflows

## 📦 Version Format

dot-work uses **CalVer (Calendar Versioning)** format: `YYYY.MM.PATCH`

### Format Breakdown

- **`YYYY`** – 4-digit year (e.g., `2025`)
- **`MM`** – 2-digit month (e.g., `01` for January, `12` for December)
- **`PATCH`** – 5-digit sequence number (e.g., `00001`, `00002`)

### Example Versions

```
2025.01.001  # January 2025, 1st build
2025.01.002  # January 2025, 2nd build
2025.02.001  # February 2025, 1st build
2026.01.001  # January 2026, 1st build
```

### Rationale for CalVer

1. **Time-based ordering** – Versions naturally sort chronologically
2. **No SemVer conflicts** – Avoids debates about "breaking changes" vs "features"
3. **Release cadence** – Encourages frequent releases tied to time periods
4. **Simplicity** – Easy to determine version age and ordering

### Version Ordering

When comparing versions:
1. Compare year first (higher = newer)
2. Then compare month (higher = newer)
3. Then compare patch number (higher = newer)

Example: `2025.02.001` > `2025.01.999` > `2024.12.999`

## 🛠️ Development

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/dot-work.git
cd dot-work

# Install in development mode
uv sync

# Run locally
uv run dot-work --help

# Run tests
uv run pytest
```

## 📄 License

MIT License - Use freely in your projects.
