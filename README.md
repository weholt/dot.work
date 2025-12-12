# 🛠️ dot-work

**Portable AI coding prompts** for project scaffolding and issue tracking.

Works with: GitHub Copilot, Claude Code, Cursor, Windsurf, Aider, Continue.dev, Amazon Q, Zed AI, OpenCode, and more.

## 🎯 What This Does

This tool contains two powerful prompts:

1. **`project-from-discussion`** - Turn a loose project discussion into a production-ready Python project with proper structure, tooling, and tests
2. **`issue-tracker-setup`** - Set up file-based issue tracking for AI agents working on your project

The installer detects your AI coding environment and puts the prompts in the right place so they work as slash commands.

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
dot-work --help     # Show help
```

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

### project-from-discussion.prompt.md

Transforms a project discussion (markdown file or pasted text) into a complete Python project:

- `pyproject.toml` with all dependencies and tool configs
- Proper `src/<package>/` structure
- CLI with `typer`
- `scripts/build.py` for linting, type-checking, and testing
- Test structure with `pytest`
- `AGENTS.md` for AI agent guidelines
- `.gitignore` with proper exclusions

**Usage:**
```
/project-from-discussion

Here's my project idea:
[paste your discussion or reference a file]
```

### issue-tracker-setup.prompt.md

Sets up a file-based issue tracking system in `.work/`:

- Priority-based issue files (critical, high, medium, low)
- Agent focus tracking (`focus.md`)
- Persistent memory across sessions (`memory.md`)
- User-assigned shortlist
- Issue history and archiving

**Usage:**
```
init work
```

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
   /project-from-discussion
   
   I want to build a CLI tool that...
   ```

4. **Set up issue tracking** (automatic with project prompt, or manually):
   ```
   init work
   ```

5. **Start building!** The AI agent now has:
   - Complete project structure
   - Issue tracking for tasks
   - Memory persistence across sessions

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
