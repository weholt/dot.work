# Feature Inventory: dot-work

**Generated:** 2024-12-28
**Source:** Documentation and CLI help text analysis (no code inspection)

---

## 1. High-Level Inventory Table

| Name | Type | Purpose (Proclaimed) | Primary Persona | Inputs → Outputs | Dependencies/Prereqs | Evidence |
|------|------|---------------------|-----------------|-----------------|---------------------|----------|
| **install** | CLI command | Install AI prompts to project directory | Developer using AI tools | env flag, target path → prompt files in correct location | uv or pip installed | README.md, `install --help` |
| **list** | CLI command | List all supported AI environments | Developer discovering options | (none) → table of environments | dot-work installed | README.md, `list --help` |
| **detect** | CLI command | Detect AI environment in project directory | Developer with existing project | target path → environment name | dot-work installed | `detect --help` |
| **init** | CLI command | Initialize new project with prompts + issue tracking | Developer starting project | env, target path → .work/ structure + prompts | dot-work installed | `init --help` |
| **init-work** | CLI command | Initialize .work/ issue tracking directory | Developer setting up workflow | target path → .work/ directory structure | dot-work installed | `init-work --help` |
| **review** | CLI command group | Interactive code review with AI export | Developer reviewing changes | git diff → comments + markdown export | git repo, browser | README.md, `review --help` |
| **validate** | CLI command group | Validate JSON/YAML files | Developer checking config | file path → validation result | dot-work installed | `validate --help` |
| **overview** | CLI command | Generate codebase overview (birdseye) | Developer understanding new codebase | input_dir, output_dir → markdown + JSON | Python files, docs | `overview --help` |
| **version** | CLI command group | Date-based versioning with changelog | Developer managing releases | version flag → git tags + CHANGELOG | git repo | `version --help` |
| **kg** | CLI command group | Knowledge-graph shredder for markdown | Developer organizing documentation | markdown files → searchable graph | SQLite | docs/db-issues/ |
| **prompts** | CLI command group | Create/manage canonical prompt files | Prompt author | .canon.md → generated prompts | dot-work installed | `prompts --help`, docs/prompt-authoring.md |
| **canonical** | CLI command | Validate/install canonical prompt files | Prompt author | .canon.md path → validation/install | dot-work installed | README.md |
| **zip** | CLI command | Zip folders respecting .gitignore | Developer packaging code | directory → zip file | dot-work installed | README.md |
| **container** | CLI command group | Container-based operations | Developer using containers | (varies) → (varies) | Docker | README.md |
| **python** | CLI command group | Python development utilities | Python developer | (varies) → (varies) | Python 3.11+ | README.md |
| **git** | CLI command group | Git analysis tools | Developer using git | git repo → analysis data | git repo | README.md |
| **harness** | CLI command | Claude Agent SDK autonomous agent harness | Agent developer | (varies) → (varies) | Claude Agent SDK | README.md |
| **File-based issue tracking** | System | Track work in .work/ with priority files | AI agent + developer | issues → markdown files in .work/ | .work/ directory | .github/prompts/setup-issue-tracker.prompt.md |
| **db-issues** | CLI command group | SQLite-based issue tracking | Developer needing database | issues → SQLite database | .work/db-issues/ | docs/db-issues/ |
| **12 AI Prompts** | Prompts | Guide AI agents through workflows | AI agent user | trigger → agent behavior | AI coding tool | README.md, .github/prompts/ |
| **Canonical prompts** | File format | Single-source prompts for multiple environments | Prompt author | .canon.md → env-specific files | YAML frontmatter | docs/prompt-authoring.md |

---

## 2. Feature Cards (Deep Dive)

### A. Prompt Installation System

**What it solves:**
- Problem: AI coding tools expect prompts in different locations/formats
- Problem: Manual prompt copying causes drift and maintenance burden
- Benefits: One canonical source generates all environment-specific outputs

**How to use:**

```bash
# Interactive mode - detects or asks for environment
dot-work install

# Specify environment directly
dot-work install --env copilot
dot-work install --env claude
dot-work install --env cursor

# Install to specific directory
dot-work install --env copilot --target /path/to/project

# Preview without writing
dot-work install --dry-run

# Force overwrite existing
dot-work install --force
```

**Parameters and configuration:**

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--env` | `-e` | TEXT | (detect) | AI environment: copilot, claude, cursor, windsurf, aider, continue, amazon-q, zed, opencode, generic |
| `--target` | `-t` | PATH | `.` | Target project directory |
| `--force` | `-f` | flag | false | Overwrite existing files without asking |
| `--dry-run` | `-n` | flag | false | Preview changes without writing |

**Supported environments** (from `dot-work list`):
| Key | Environment | Output Location |
|-----|-------------|-----------------|
| `copilot` | GitHub Copilot | `.github/prompts/*.prompt.md` |
| `claude` | Claude Code | `CLAUDE.md` |
| `cursor` | Cursor | `.cursor/rules/*.mdc` |
| `windsurf` | Windsurf | `.windsurf/rules/*.md` |
| `aider` | Aider | `CONVENTIONS.md` |
| `continue` | Continue.dev | `.continue/prompts/*.md` |
| `amazon-q` | Amazon Q | `.amazonq/rules.md` |
| `zed` | Zed AI | `.zed/prompts/*.md` |
| `opencode` | OpenCode | `.opencode/prompts/*.md` + `AGENTS.md` |
| `generic` | Generic/Manual | `prompts/*.md` + `AGENTS.md` |

**Outputs and artifacts:**
- Environment-specific prompt files in configured locations
- Files are generated from canonical `.canon.md` source

**Operational notes:**
- Run from project root or specify `--target`
- Use `--dry-run` to preview changes
- Generated files should be git-ignored (recommended)

**Gaps:**
- What happens if environment is not detected? (default behavior unclear)
- Can install multiple environments at once? (not documented)
- How to uninstall/remove installed prompts? (not documented)

---

### B. Environment Detection

**What it solves:**
- Problem: Uncertain which AI coding environment is active in a project
- Benefits: Automatic environment detection for install command

**How to use:**

```bash
# Detect in current directory
dot-work detect

# Detect in specific directory
dot-work detect --target /path/to/project
```

**Parameters and configuration:**

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--target` | `-t` | PATH | `.` | Target project directory to scan |

**Outputs and artifacts:**
- Prints detected environment name

**Gaps:**
- How detection works? (what files/signals are checked)
- What if multiple environments detected?
- What if none detected?

---

### C. File-Based Issue Tracking System (.work/)

**What it solves:**
- Problem: AI agents need persistent state across sessions
- Problem: Quality regression tracking requires baseline
- Problem: Task prioritization needs structure
- Benefits: Git-tracked, human-readable, AI-parseable

**How to use:**

```bash
# Initialize .work/ directory structure
dot-work init-work

# Initialize with prompts + issue tracking
dot-work init --env copilot

# Use AI prompts for workflow (after initialization)
# /generate-baseline    - Capture quality snapshot
# /do-work             - Start iteration loop
# /new-issue           - Create formatted issue
# /focus on <topic>    - Create prioritized issues
```

**Directory structure created:**

```
.work/
├── baseline.md               # Quality metrics snapshot
└── agent/
    ├── focus.md              # Previous/Current/Next state
    ├── memory.md             # Cross-session knowledge
    ├── notes/                # Scratchpad, research
    └── issues/
        ├── critical.md       # P0 - blockers, security
        ├── high.md           # P1 - broken functionality
        ├── medium.md         # P2 - enhancements
        ├── low.md            # P3 - minor improvements
        ├── backlog.md        # Untriaged ideas
        ├── shortlist.md      # USER priority (highest)
        ├── history.md        # Completed issues (append-only)
        └── references/       # Specs, large docs
```

**Parameters and configuration:**

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--target` | `-t` | PATH | `.` | Target project directory |
| `--force` | `-f` | flag | false | Overwrite existing .work/ |

**Issue ID format:**
```
<PREFIX>-<NUMBER>@<HASH>
```
- Example: `BUG-003@a9f3c2`
- Prefixes: BUG, FEAT, ENHANCE, REFACTOR, DOCS, TEST, SEC, PERF, DEBT, STRUCT

**Priority levels:**
1. **shortlist.md** – User-directed priority (HIGHEST)
2. **critical.md** – P0: blockers, security, data loss
3. **high.md** – P1: core functionality broken
4. **medium.md** – P2: enhancements, tech debt
5. **low.md** – P3: minor improvements
6. **backlog.md** – untriaged

**Outputs and artifacts:**
- `.work/baseline.md` – Quality snapshot (tests, coverage, lint, types)
- `.work/agent/focus.md` – Three-value state (Previous/Current/Next)
- `.work/agent/memory.md` – Dated lessons, patterns, preferences
- `.work/agent/issues/*.md` – Issues by priority
- `.work/agent/notes/*.md` – Working notes
- `.work/agent/issues/references/*.md` – Archived valuable docs

**Operational notes:**
- `history.md` is append-only (never modify entries)
- `shortlist.md` is read-only for agents (user explicit only)
- Generate baseline before ANY code changes
- Selection order: shortlist → critical → high → medium → low

**Gaps:**
- `generate-baseline` referenced but not in CLI – AI prompt only?
- `continue`, `status`, `focus on` – CLI commands or prompt instructions?
- How to edit issues manually? (direct file edit vs commands)
- How to move issues between priority files?

---

### D. Interactive Code Review System

**What it solves:**
- Problem: AI agents need structured feedback on code changes
- Problem: Review comments must be exportable for AI consumption
- Benefits: Web UI for adding comments, markdown export for agents

**How to use:**

```bash
# Start review server (opens web UI)
dot-work review start

# Review against specific base
dot-work review start --base main

# Custom port
dot-work review start --port 3000

# Export comments as markdown
dot-work review export

# Export to specific file
dot-work review export --output review.md

# Export specific review
dot-work review export --review-id 20241221-143500

# Clear reviews
dot-work review clear --force
dot-work review clear --review-id 20241221-143500
```

**Parameters and configuration:**

**`review start`:**

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--port` | `-p` | INTEGER | 8765 | Server port |
| `--base` | `-b` | TEXT | HEAD~1 | Base commit/branch to diff against |
| `--head` | | TEXT | working tree | Head commit/branch to diff |

**`review export`:**

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--output` | `-o` | PATH | `.work/reviews/review.md` | Output file path |
| `--review-id` | `-r` | TEXT | latest | Specific review ID to export |

**`review clear`:**

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--review-id` | | TEXT | (all) | Specific review to clear |
| `--force` | | flag | false | Skip confirmation |

**Outputs and artifacts:**
- Web UI at `http://localhost:8765`
- Review storage location: (not explicitly documented)
- Exported markdown with file paths, line numbers, comments

**Operational notes:**
- Web UI shows file tree with changes
- Side-by-side and unified diff views
- Click any line to add comment
- Export formatted for AI consumption

**Gaps:**
- Where are reviews stored? (path not documented)
- Review ID format? (shown as timestamp but not confirmed)
- Can review be saved and resumed?
- How to list all available reviews?

---

### E. File Validation (validate)

**What it solves:**
- Problem: JSON/YAML syntax errors break workflows
- Problem: Need to verify config files before use
- Benefits: Quick syntax checking, optional schema validation

**How to use:**

```bash
# Validate JSON
dot-work validate json config.json

# Validate JSON against schema
dot-work validate json config.json --schema schema.json

# Validate YAML
dot-work validate yaml config.yaml
```

**Parameters and configuration:**

**`validate json`:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `file` | PATH | yes | Path to JSON file |
| `--schema` | `-s` | PATH | Optional JSON Schema for validation |

**`validate yaml`:**
(Documented, help text not captured)

**Outputs and artifacts:**
- Validation result (pass/fail)
- Error messages with line/column numbers

**Gaps:**
- What output format? (human-readable, JSON?)
- Exit codes for scripting?
- Does YAML validate against schema too?

---

### F. Codebase Overview Generator (overview)

**What it solves:**
- Problem: Understanding new/complex codebases takes time
- Problem: AI agents need structured project context
- Benefits: Human-readable overview + structured JSON for LLMs

**How to use:**

```bash
# Generate overview
dot-work overview input_dir output_dir
```

**Parameters and configuration:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `input_dir` | PATH | yes | Folder containing project to scan |
| `output_dir` | PATH | yes | Where to store generated files |

**Outputs and artifacts:**
- `birdseye_overview.md` – Human-readable project guide
- `features.json` – Structured feature data for LLMs
- `documents.json` – Cross-referenceable documentation sections

**Operational notes:**
- Scans Python files and markdown documentation
- Generates both human and machine-readable outputs

**Gaps:**
- What file types are scanned? (Python only?)
- How does it identify "features"?
- Can it scan other languages?

---

### G. Knowledge Graph Shredder (kg)

**What it solves:**
- Problem: Large documentation is hard to search and navigate
- Problem: Need cross-references between documents
- Benefits: Searchable graph, document outlines, node expansion

**How to use:**

```bash
# Ingest markdown files
dot-work kg ingest docs/*.md

# Show database statistics
dot-work kg stats

# Show document outline
dot-work kg outline <document-id>

# Search for content
dot-work kg search "authentication"

# Expand/show specific node
dot-work kg expand <node-id>

# Render document with filtering
dot-work kg render <document-id>

# Export nodes as JSON
dot-work kg export

# Show database status
dot-work kg status

# Manage projects (collections)
dot-work kg project list
dot-work kg project create <name>

# Manage topics (reusable tags)
dot-work kg topic list
dot-work kg topic create <name>
```

**Parameters and configuration:**
(Individual command options not fully captured)

**Outputs and artifacts:**
- SQLite database: (location not documented, likely `.work/kg/` or similar)
- JSON exports
- Tree outlines
- Search results

**Gaps:**
- Database location not documented
- Full command options not captured
- How to delete/update ingested documents?

---

### H. Version Management (version)

**What it solves:**
- Problem: Manual version bumping is error-prone
- Problem: Changelog generation is tedious
- Benefits: Date-based versioning with automatic changelog

**How to use:**

```bash
# Initialize version management
dot-work version init --version 2025.10.001

# Freeze new version with changelog
dot-work version freeze

# Show current version
dot-work version show

# Show version history
dot-work version history

# Show commits since last version
dot-work version commits

# Manage configuration
dot-work version config get <key>
dot-work version config set <key> <value>
```

**Parameters and configuration:**

**`version init`:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--version` | TEXT | (auto) | Initial version (e.g., 2025.10.001) |
| `--project-root` | PATH | current dir | Project root directory |

**Outputs and artifacts:**
- Git tags for versions
- CHANGELOG file (format not specified)
- Configuration file (location/format not documented)

**Gaps:**
- Version format conventions?
- How does changelog generation work?
- Where is config stored?

---

### I. Database Issue Tracking (db-issues)

**What it solves:**
- Problem: File-based issues don't scale for large teams
- Problem: Need relational queries (dependencies, epics, labels)
- Benefits: SQLite-backed, full CRUD, search, dependencies

**How to use:**

```bash
# Initialize database
dot-work db-issues init

# Create issue
dot-work db-issues create "Fix parser bug" --type bug --priority high

# List issues
dot-work db-issues list
dot-work db-issues list --status in-progress
dot-work db-issues list --priority critical --type bug

# Update issue
dot-work db-issues update <id> --status in-progress
dot-work db-issues update <id> --priority critical --title "New title"

# Show issue
dot-work db-issues show <id>

# Add comment
dot-work db-issues comment <id> "Progress update"

# Close/reopen
dot-work db-issues close <id>
dot-work db-issues reopen <id>

# Delete issue
dot-work db-issues delete <id>
```

**Parameters and configuration:**

**Create:**
| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--type` | `-T` | TEXT | bug, feature, task, enhancement, refactor, docs, test, security, performance |
| `--priority` | `-p` | TEXT | critical, high, medium, low |
| `--description` | `-d` | TEXT | Issue description |
| `--assignee` | `-a` | TEXT | Assigned user |
| `--labels` | `-l` | TEXT | Comma-separated labels |
| `--epic` | `-e` | TEXT | Parent epic ID |

**List/Filter:**
| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--status` | `-s` | TEXT | Filter by status |
| `--priority` | `-p` | TEXT | Filter by priority |
| `--type` | `-t` | TEXT | Filter by type |
| `--assignee` | `-a` | TEXT | Filter by assignee |
| `--epic` | `-e` | TEXT | Filter by epic |
| `--labels` | `-l` | TEXT | Filter by labels |
| `--limit` | | INT | Limit results |
| `--sort` | | TEXT | Sort by field (created, updated, priority, status) |
| `--output` | `-o` | TEXT | table, json, yaml |

**Update:**
| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--title` | `-t` | TEXT | New title |
| `--description` | `-d` | TEXT | New description |
| `--priority` | `-p` | TEXT | New priority |
| `--assignee` | `-a` | TEXT | New assignee |
| `--status` | `-s` | TEXT | proposed, in-progress, blocked, completed, wont-fix |
| `--type` | `-T` | TEXT | New issue type |

**Labels:**
| Command | Description |
|---------|-------------|
| `labels create NAME --color COLOR` | Create label with color |
| `labels list [--unused]` | List labels |
| `labels update ID --color COLOR` | Update label |
| `labels rename ID NEW_NAME` | Rename label |
| `labels delete ID [--force]` | Delete label |
| `labels add ISSUE_ID LABEL...` | Add label to issue |
| `labels remove ISSUE_ID LABEL...` | Remove label from issue |

**Dependencies:**
| Command | Description |
|---------|-------------|
| `deps add FROM_ID TO_ID --type TYPE` | Add dependency |
| `deps remove FROM_ID TO_ID` | Remove dependency |
| `deps check ISSUE_ID` | Check specific dependency |
| `deps check-all` | Check for circular dependencies |
| `deps blocked-by ISSUE_ID` | Show blocking issues |
| `deps impact ISSUE_ID [--include-transitive]` | Show impact tree |
| `deps tree ISSUE_ID [--direction DIR]` | Show dependency tree (down, up, both) |

**Dependency types:** blocks, depends-on, related-to, duplicates, parent-of, child-of

**Epics:**
| Command | Description |
|---------|-------------|
| `epic create TITLE [--desc] [--parent]` | Create epic |
| `epic list [--status] [--parent]` | List epics |
| `epic show EPIC_ID` | Show epic details |
| `epic update EPIC_ID` | Update epic |
| `epic delete EPIC_ID` | Delete epic |
| `child add PARENT_ID CHILD_ID` | Add child epic |
| `child remove CHILD_ID` | Remove child epic |
| `child list PARENT_ID` | List children |

**Search:**
| Command | Options |
|---------|---------|
| `search QUERY [--field FIELD] [--status] [--priority] [--type] [--limit]` | Search by text |

**Import/Export:**
| Command | Description |
|---------|-------------|
| `io export [--output] [--status] [--type] [--include-completed]` | Export to JSONL |
| `io import [--input] [--merge] [--replace]` | Import from JSONL |
| `io sync [--message] [--push]` | Commit to git |

**Edit:**
| Command | Description |
|---------|-------------|
| `edit ISSUE_ID [--editor]` | Edit in external editor |

**Outputs and artifacts:**
- Database: `.work/db-issues/issues.db` (default)
- JSONL exports
- Git commits (via `io sync`)

**Environment variables:**
| Variable | Description |
|----------|-------------|
| `DOT_WORK_DB_ISSUES_PATH` | Custom database path |
| `DOT_WORK_DB_ISSUES_DEBUG` | Enable debug mode |
| `EDITOR` | Default editor for `edit` command |

**Gaps:**
- Migration path from file-based to db-issues?
- Can both coexist?

---

### J. Canonical Prompt System

**What it solves:**
- Problem: Prompt drift across environments
- Problem: Maintenance burden of duplicate prompts
- Benefits: Single `.canon.md` generates all environment-specific files

**How to use:**

```bash
# Create canonical prompt (interactive wizard)
dot-work prompts create

# Install canonical prompt to environment
dot-work prompts install my-prompt.canon.md --target copilot
dot-work prompts install my-prompt.canon.md --all-environments
```

**Canonical file format:**

```markdown
---
meta:
  title: "Prompt Title"
  description: "What this prompt does"
  version: "1.0.0"

environments:
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"
  claude:
    target: ".claude/"
    filename: "instructions.md"

---

# Prompt Content

Your prompt here...
```

**Filename options:**
- `filename: "specific-name.md"` – Fixed name per environment
- `filename_suffix: ".prompt.md"` – Auto-generated from meta.title

**Title transformation:** `"Code Review Agent"` → `code-review-agent`

**Outputs and artifacts:**
- Generated files in configured target locations
- Generated frontmatter includes only selected environment

**Operational notes:**
- Use `--dry-run` to preview
- Generated files are disposable (regenerate from source)
- Git-ignore generated files

**Gaps:**
- How to validate canonical file without installing?
- What environments are supported? (same as install?)

---

### K. The 12 AI Agent Prompts

**What it solves:**
- Problem: AI agents need structured workflows
- Problem: Inconsistent behavior across sessions
- Benefits: Repeatable, documented patterns

**How to use:**
Via AI tool slash commands after `dot-work install`:

| Prompt | Trigger | Description |
|--------|---------|-------------|
| python-project-from-discussion | `/python-project-from-discussion` | Transform discussion into Python project |
| setup-issue-tracker | `/setup-issue-tracker` | Initialize .work/ issue tracking |
| do-work | `/do-work` | Iteration loop: baseline → select → investigate → implement → validate → complete |
| new-issue | `/new-issue` | Create formatted issue with ID, tags, criteria |
| agent-prompts-reference | `/agent-prompts-reference` | Quick reference for all prompts |
| establish-baseline | `/generate-baseline` | Capture quality snapshot |
| compare-baseline | `/compare-baseline` | Compare current to baseline |
| critical-code-review | `/critical-code-review` | Deep code review |
| spec-delivery-auditor | `/spec-delivery-auditor` | Verify implementation matches spec |
| improvement-discovery | `/improvement-discovery` | Analyze for justified improvements |
| bump-version | `/bump-version patch` | Semantic version bump |
| api-export | `/api-export` | Generate API documentation |

**Outputs and artifacts:**
- AI agent follows documented workflow
- Creates/updates files in `.work/`
- Generates code, tests, documentation

**Gaps:**
- Are all 12 documented? (count may vary)
- Which are slash commands vs automatic behaviors?

---

## 3. Symbiosis Map: Feature Composition

### Small Compositions (2 components)

**1. Install + Detect**
```bash
# Detect environment, then install appropriate prompts
dot-work detect
dot-work install --env <detected>
```
*Workflow: Auto-configure prompts for detected environment*

**2. init-work + generate-baseline**
```bash
# Setup tracking, then capture quality floor
dot-work init-work
/generate-baseline  # AI prompt
```
*Workflow: Prepare project for AI-assisted development*

**3. review start + review export**
```bash
# Review changes, then export for AI
dot-work review start --base main
# (add comments in browser)
dot-work review export
```
*Workflow: Human review → AI fixes*

### Medium Compositions (3-4 components)

**1. New Project Scaffolding**
```bash
# 1. Install prompts
dot-work install --env copilot

# 2. Create project from discussion
/python-project-from-discussion
I want to build a CLI tool that...

# 3. Setup issue tracking
/setup-issue-tracker

# 4. Generate baseline
/generate-baseline
```
*Workflow: New project with full AI workflow support*

**2. Iteration Loop (do-work)**
```bash
# 1. Generate baseline
/generate-baseline

# 2. Select issue (from .work/agent/issues/)
# (AI reads focus.md, selects from priority order)

# 3. Investigate
# (AI creates notes in .work/agent/notes/)

# 4. Implement
# (AI makes code changes)

# 5. Validate
/compare-baseline

# 6. Complete (if pass) or Fix (if fail)
```
*Workflow: Full quality-controlled iteration*

### Large Composition (5+ components)

**1. Complete Development Workflow**
```bash
# SETUP (one-time)
dot-work install --env claude
dot-work init-work
/generate-baseline

# ITERATION
/do-work
# → selects issue
# → investigates
# → implements
# → validates
# → completes

# REVIEW (manual trigger)
dot-work review start --base main
# → add comments in browser
dot-work review export
# → pass to AI for fixes

# VERSION (on release)
dot-work version freeze
dot-work version show
```
*Workflow: End-to-end AI-assisted development*

---

## 4. Decision Guides

| If you want... | Choose... |
|---------------|-----------|
| AI prompts in your project | `dot-work install --env <your-tool>` |
| Track work with AI agent | `dot-work init-work` + `/do-work` |
| Review code changes | `dot-work review start` |
| Manage versions | `dot-work version init` + `dot-work version freeze` |
| Create custom prompt | `dot-work prompts create` |
| Validate config files | `dot-work validate json/yaml` |
| Database issue tracking | `dot-work db-issues init` |
| Understand codebase | `dot-work overview input_dir output_dir` |
| Organize documentation | `dot-work kg ingest docs/*.md` |

---

## 5. Gaps Summary

See `gaps-and-questions.md` for complete gap tracking.

Key high-priority gaps:
1. CLI commands vs AI prompt instructions (generate-baseline, continue, status, focus on)
2. init vs init-work difference
3. Migration between file-based and db-issues
4. Review storage location and management
5. kg database location
