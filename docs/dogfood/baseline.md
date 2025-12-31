# Baseline: What is dot-work?

**Generated:** 2024-12-28
**Source:** Documentation and CLI help text analysis (no code inspection)

---

## 1. Mission Statement (Proclaimed)

dot-work is a portable CLI tool that provides **12 AI coding agent prompts** and utilities for project scaffolding and file-based issue tracking. It enables developers to use AI coding assistants (GitHub Copilot, Claude Code, Cursor, Windsurf, Aider, Continue.dev, Amazon Q, Zed AI, OpenCode, and more) with standardized workflows for:

- **Project scaffolding** – Transforming discussions into production-ready Python projects
- **Workflow management** – File-based issue tracking with focus management and iteration loops
- **Quality assurance** – Baseline capturing, code review, and delivery auditing
- **Version control** – Semantic versioning with safety checks

The tool installs prompts into the appropriate locations for each AI coding environment, allowing developers to use slash commands or automatic instructions to guide AI agents.

---

## 2. Problem Statement and Non-Goals

### Problems It Claims to Solve

1. **Inconsistent AI agent behavior** – Different AI coding tools have different interfaces and conventions
2. **No standardized workflow** – AI agents lack clear processes for iteration, quality checks, and task tracking
3. **Project scaffolding friction** – Turning a project discussion into a structured codebase requires manual work
4. **Quality regression** – No easy way to establish a quality baseline and detect regressions
5. **Fragmented prompt management** – Prompts drift between environments when manually copied

### Non-Goals / Out of Scope

(Not explicitly stated in documentation – this is a **gap**)

### Stated Constraints/Assumptions

- Python 3.11+ required
- Uses `uv` package manager (or pip for installation)
- File-based issue tracking in `.work/` directory (Git-tracked)
- Prompts are installed to tool-specific locations (`.github/prompts/`, `.claude/`, `.cursor/rules/`, etc.)

---

## 3. Conceptual Model / Core Nouns

| Term | Definition |
|------|------------|
| **Prompt** | An AI agent instruction file (markdown with YAML frontmatter) |
| **Environment** | The target AI coding tool (copilot, claude, cursor, windsurf, aider, continue, amazon-q, zed, opencode, generic) |
| **Canonical prompt** | Single-source-of-truth prompt file (`.canon.md`) that generates environment-specific outputs |
| **Issue** | A tracked unit of work with ID, title, type, priority, status, and metadata |
| **Issue ID** | Format: `<PREFIX>-<NUMBER>@<HASH>` (e.g., `BUG-003@a9f3c2`) |
| **Priority file** | Markdown file organizing issues by priority (critical.md, high.md, medium.md, low.md, shortlist.md, backlog.md) |
| **Focus** | The `.work/agent/focus.md` file tracking Previous/Current/Next work state |
| **Baseline** | A snapshot of project quality metrics (tests, coverage, lint, types) for regression detection |
| **Memory** | The `.work/agent/memory.md` file storing cross-session knowledge and lessons |
| **Review** | Interactive code change comments exported as AI-friendly markdown |
| **db-issues** | Alternative SQLite-based issue tracking system (separate from file-based) |

---

## 4. Minimum Viable Workflow (Happy Path)

### Prerequisites

1. Install `uv` package manager OR use `pip`
2. Install dot-work: `uv tool install dot-work` (or `uvx dot-work` for one-time use)
3. Have an AI coding tool installed (Copilot, Claude Code, Cursor, etc.)

### First Success: Installing Prompts and Creating a Project

```bash
# 1. Install prompts to your project (detects or asks for environment)
dot-work install --env copilot

# 2. Use your AI tool's slash command
# In GitHub Copilot, type:
/python-project-from-discussion

I want to build a CLI tool that...
```

### First Success: File-Based Issue Tracking

```bash
# 1. Initialize .work/ directory structure
dot-work init-tracking

# 2. Generate baseline before any code changes
# (This is done via AI agent prompt, not CLI command)
# Trigger: /generate-baseline prompt

# 3. Start working
# Trigger: /do-work prompt
```

### First Success: Interactive Code Review

```bash
# 1. Make code changes
git commit -am "WIP changes"

# 2. Start review server
dot-work review start --base HEAD~1

# 3. Add comments in web UI at http://localhost:8765

# 4. Export for AI agent
dot-work review export --output review-feedback.md

# 5. Pass to AI agent for fixes
```

### First Success: Knowledge Graph Shredding

```bash
# Ingest markdown documents
dot-work kg ingest docs/*.md

# Search for content
dot-work kg search "authentication"

# Show outline
dot-work kg outline <document-id>
```

---

## 5. Supported Environments (Detection & Installation)

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

---

## 6. The 12 AI Agent Prompts

### Project Setup
| Prompt | Description |
|--------|-------------|
| `python-project-from-discussion` | Transform discussion into complete Python project with pyproject.toml, src/ layout, CLI, tests |
| `setup-issue-tracker` | Initialize `.work/` directory with priority-based issue tracking |

### Workflow & Iteration
| Prompt | Description |
|--------|-------------|
| `do-work` | Optimal iteration loop: baseline → select → investigate → implement → validate → complete |
| `new-issue` | Create properly formatted issues with ID, priority, tags, acceptance criteria |
| `agent-prompts-reference` | Quick reference for all prompts and trigger commands |

### Quality Assurance
| Prompt | Description |
|--------|-------------|
| `establish-baseline` | Capture current state (tests, coverage, lint, types) before changes |
| `compare-baseline` | Compare current state against baseline to detect regressions |
| `critical-code-review` | Deep code review: correctness, security, maintainability |
| `spec-delivery-auditor` | Verify implementation matches specification |
| `improvement-discovery` | Analyze codebase for justified improvements |

### Utilities
| Prompt | Description |
|--------|-------------|
| `bump-version` | Semantic version bumping with safety checks |
| `api-export` | Generate API documentation or export specifications |

(Additional prompts exist for code review, performance review, security review, Pythonic code, etc.)

---

## 7. Open Questions & Gaps

1. **Non-goals** – What does dot-work explicitly NOT do? (Not stated in docs)
2. **`init` vs `init-tracking`** – What's the difference between `dot-work init` and `dot-work init-tracking`?
3. **`generate-baseline` command** – Referenced in prompts but not listed in `--help`. Is it a CLI command or only an AI prompt?
4. **`continue` command** – Referenced in prompts but not shown in CLI help. Is it a real command or a prompt instruction?
5. **`status` command** – Referenced in prompts but not shown in CLI help.
6. **`focus on` command** – Referenced in prompts but not shown in CLI help.
7. **Trigger command availability** – Which commands are actual CLI commands vs. prompt-only instructions?
8. **Integration testing** – How to verify prompts work across different AI tools?
9. **Priority file editing** – Are users expected to edit priority files manually, or are there commands?
10. **Migration path** – How to migrate from file-based issues to db-issues or vice versa?

---

## 8. Human Review Checklist

Please review and approve/deny each statement:

- [x] **Mission understanding**: dot-work provides AI coding prompts and utilities for scaffolding, issue tracking, QA, and versioning
- [x] **Primary users**: Developers using AI coding assistants (Copilot, Claude, Cursor, etc.)
- [x] **Core workflows**: Prompt installation, project scaffolding, file-based issue tracking, code review
- [x] **Key terms**: Environment, prompt, canonical prompt, issue, baseline, focus, memory
- [x] **Happy path**: Install → Use AI prompt → Initialize issue tracking → Generate baseline → Iterate
- [x] **Gaps acknowledged**: See section 7 – please clarify or confirm these are actual gaps

**Approval Decision:** _______________

**Comments/Corrections:**
1. Not termined
2. Investigate and clarfify the difference by looking at the implementation
3. It should only be a slash command/prompt
4. prompt instruction, but should be implemented as a cli command reading the prompt and printing *
5. similar as point 4.
6. similar as point | 
7. This should be clearified, if possible using the same instructions in point 4-6 within the cli command would be nice
8. This would require human validation
9. The tools and ai should edit the issue files, not humans.
10. There should be an issue for making a unified interface for the issue handling with file-based, database or api as optional, pluggable storage options

