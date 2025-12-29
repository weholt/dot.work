# Tooling Reference: dot-work CLI

**Generated:** 2024-12-28
**Source:** CLI `--help` output analysis

---

## Quick Command Index

| Command | Description | Type |
|---------|-------------|------|
| `install` | Install AI prompts to project | CLI |
| `list` | List supported environments | CLI |
| `detect` | Detect AI environment in project | CLI |
| `init` | Initialize project with prompts + tracking | CLI |
| `init-work` | Initialize .work/ directory | CLI |
| `review` | Interactive code review system | CLI group |
| `validate` | File validation | CLI group |
| `overview` | Generate codebase overview | CLI |
| `version` | Date-based versioning | CLI group |
| `kg` | Knowledge graph shredder | CLI group |
| `prompts` | Canonical prompt management | CLI group |
| `db-issues` | Database issue tracking | CLI group |
| `canonical` | Validate/install canonical prompts | CLI |
| `zip` | Zip folders respecting .gitignore | CLI |
| `container` | Container operations | CLI group |
| `python` | Python utilities | CLI group |
| `git` | Git analysis tools | CLI group |
| `harness` | Claude Agent SDK harness | CLI |

---

## Command Reference

### `install` – Install AI Prompts

Install AI coding agent prompts to project directory.

```bash
dot-work install [OPTIONS]
```

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--env` | `-e` | TEXT | (detect) | AI environment: copilot, claude, cursor, windsurf, aider, continue, amazon-q, zed, opencode, generic |
| `--target` | `-t` | PATH | `.` | Target project directory |
| `--force` | `-f` | flag | false | Overwrite existing files |
| `--dry-run` | `-n` | flag | false | Preview changes without writing |

**Examples:**
```bash
# Interactive mode
dot-work install

# Specific environment
dot-work install --env copilot

# Custom directory
dot-work install --env claude --target ../my-project

# Preview
dot-work install --dry-run
```

---

### `list` – List Supported Environments

List all supported AI coding environments.

```bash
dot-work list
```

**Output:** Table of environments with keys, names, and output locations.

---

### `detect` – Detect AI Environment

Detect the AI environment in a project directory.

```bash
dot-work detect [OPTIONS]
```

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--target` | `-t` | PATH | `.` | Target project directory |

**Example:**
```bash
dot-work detect --target ../existing-project
```

---

### `init` – Initialize Project

Initialize a new project with prompts and issue tracking structure.

```bash
dot-work init [OPTIONS]
```

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--env` | `-e` | TEXT | (detect) | AI environment to use |
| `--target` | `-t` | PATH | `.` | Target project directory |

**Example:**
```bash
dot-work init --env copilot --target ./new-project
```

---

### `init-work` – Initialize Issue Tracking

Initialize the `.work/` issue tracking directory structure.

```bash
dot-work init-work [OPTIONS]
```

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--target` | `-t` | PATH | `.` | Target project directory |
| `--force` | `-f` | flag | false | Overwrite existing .work/ |

**Creates:**
```
.work/
├── baseline.md
└── agent/
    ├── focus.md
    ├── memory.md
    ├── notes/
    └── issues/
        ├── critical.md
        ├── high.md
        ├── medium.md
        ├── low.md
        ├── backlog.md
        ├── shortlist.md
        ├── history.md
        └── references/
```

---

### `review` – Interactive Code Review

Interactive code review with AI-friendly export.

```bash
dot-work review [OPTIONS] COMMAND [ARGS]...
```

#### Subcommands

**`start`** – Start review server
```bash
dot-work review start [OPTIONS]
```

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--port` | `-p` | INTEGER | 8765 | Server port |
| `--base` | `-b` | TEXT | HEAD~1 | Base commit/branch to diff |
| `--head` | | TEXT | working tree | Head commit/branch |

**`export`** – Export review comments
```bash
dot-work review export [OPTIONS]
```

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--output` | `-o` | PATH | `.work/reviews/review.md` | Output file |
| `--review-id` | `-r` | TEXT | latest | Specific review ID |

**`clear`** – Clear review comments
```bash
dot-work review clear [OPTIONS]
```

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--review-id` | | TEXT | (all) | Specific review to clear |
| `--force` | | flag | false | Skip confirmation |

**Examples:**
```bash
# Start review
dot-work review start --base main

# Custom port
dot-work review start --port 3000

# Export
dot-work review export --output my-review.md

# Clear specific review
dot-work review clear --review-id 20241221-143500
```

---

### `validate` – File Validation

Validate files for syntax and schema errors.

```bash
dot-work validate [OPTIONS] COMMAND [ARGS]...
```

#### Subcommands

**`json`** – Validate JSON
```bash
dot-work validate json [OPTIONS] FILE
```

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `file` | PATH | yes | Path to JSON file |

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--schema` | `-s` | PATH | | JSON Schema for validation |

**`yaml`** – Validate YAML
```bash
dot-work validate yaml FILE
```

**Examples:**
```bash
# Validate JSON
dot-work validate json config.json

# Validate with schema
dot-work validate json config.json --schema schema.json

# Validate YAML
dot-work validate yaml config.yaml
```

---

### `overview` – Generate Codebase Overview

Generate a bird's-eye overview of a codebase.

```bash
dot-work overview INPUT_DIR OUTPUT_DIR
```

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `input_dir` | PATH | yes | Folder to scan |
| `output_dir` | PATH | yes | Output directory |

**Generates:**
- `birdseye_overview.md` – Human-readable guide
- `features.json` – Structured data for LLMs
- `documents.json` – Cross-referenceable docs

---

### `version` – Version Management

Date-based version management with changelog generation.

```bash
dot-work version [OPTIONS] COMMAND [ARGS]...
```

#### Subcommands

**`init`** – Initialize version management
```bash
dot-work version init [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--version` | TEXT | (auto) | Initial version (e.g., 2025.10.001) |
| `--project-root` | PATH | current dir | Project root |

**`freeze`** – Freeze new version
```bash
dot-work version freeze
```

**`show`** – Show current version
```bash
dot-work version show
```

**`history`** – Show version history
```bash
dot-work version history
```

**`commits`** – Show commits since last version
```bash
dot-work version commits
```

**`config`** – Manage configuration
```bash
dot-work version config COMMAND [ARGS]...
```

---

### `kg` – Knowledge Graph Shredder

Knowledge-graph shredder for plain text/Markdown.

```bash
dot-work kg [OPTIONS] COMMAND [ARGS]...
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `ingest` | Ingest Markdown files |
| `stats` | Show database statistics |
| `outline` | Show document outline as tree |
| `search` | Search for nodes |
| `expand` | Show full content of node |
| `render` | Render document with filtering |
| `export` | Export nodes as JSON |
| `status` | Show database status |
| `project` | Manage projects (collections) |
| `topic` | Manage topics (reusable tags) |

---

### `prompts` – Canonical Prompt Management

Create and manage canonical prompt files.

```bash
dot-work prompts [OPTIONS] COMMAND [ARGS]...
```

#### Subcommands

**`create`** – Create canonical prompt (interactive wizard)
```bash
dot-work prompts create
```

---

### `db-issues` – Database Issue Tracking

SQLite-based issue tracking system.

```bash
dot-work db-issues [OPTIONS] COMMAND [ARGS]...
```

#### Core Commands

**`init`** – Initialize database
```bash
dot-work db-issues init
```
Creates `.work/db-issues/issues.db`

**`create`** – Create issue
```bash
dot-work db-issues create TITLE [OPTIONS]
```

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--type` | `-T` | TEXT | bug, feature, task, enhancement, refactor, docs, test, security, performance |
| `--priority` | `-p` | TEXT | critical, high, medium, low |
| `--description` | `-d` | TEXT | Issue description |
| `--assignee` | `-a` | TEXT | Assigned user |
| `--labels` | `-l` | TEXT | Comma-separated labels |
| `--epic` | `-e` | TEXT | Parent epic ID |

**`list`** – List issues
```bash
dot-work db-issues list [OPTIONS]
```

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--status` | `-s` | TEXT | Filter by status |
| `--priority` | `-p` | TEXT | Filter by priority |
| `--type` | `-t` | TEXT | Filter by type |
| `--assignee` | `-a` | TEXT | Filter by assignee |
| `--epic` | `-e` | TEXT | Filter by epic |
| `--labels` | `-l` | TEXT | Filter by labels |
| `--limit` | | INT | Limit results |
| `--sort` | | TEXT | Sort by (created, updated, priority, status) |
| `--output` | `-o` | TEXT | table, json, yaml |

**`show`** – Show issue details
```bash
dot-work db-issues show ISSUE_ID
```

**`update`** – Update issue
```bash
dot-work db-issues update ISSUE_ID [OPTIONS]
```

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--title` | `-t` | TEXT | New title |
| `--description` | `-d` | TEXT | New description |
| `--priority` | `-p` | TEXT | New priority |
| `--assignee` | `-a` | TEXT | New assignee |
| `--status` | `-s` | TEXT | proposed, in-progress, blocked, completed, wont-fix |
| `--type` | `-T` | TEXT | New issue type |

**`close`** – Close issue
```bash
dot-work db-issues close ISSUE_ID
```

**`reopen`** – Reopen issue
```bash
dot-work db-issues reopen ISSUE_ID
```

**`delete`** – Delete issue
```bash
dot-work db-issues delete ISSUE_ID
```

**`comment`** – Add comment
```bash
dot-work db-issues comment ISSUE_ID CONTENT
```

**`edit`** – Edit in external editor
```bash
dot-work db-issues edit ISSUE_ID [OPTIONS]
```

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--editor` | `-e` | TEXT | $EDITOR or vi | Editor command |

#### Search

**`search`** – Search issues
```bash
dot-work db-issues search QUERY [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--field` | Search field (title, description, all) |
| `--status` | Filter by status |
| `--priority` | Filter by priority |
| `--type` | Filter by type |
| `--limit` | Limit results |

#### Labels

**`labels create`** – Create label
```bash
dot-work db-issues labels create NAME [OPTIONS]
```

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--color` | `-c` | TEXT | Label color (named, hex, rgb()) |
| `--description` | `-d` | TEXT | Label description |

**`labels list`** – List labels
```bash
dot-work db-issues labels list [--unused]
```

**`labels update`** – Update label
```bash
dot-work db-issues labels update LABEL_ID [OPTIONS]
```

**`labels rename`** – Rename label
```bash
dot-work db-issues labels rename LABEL_ID NEW_NAME
```

**`labels delete`** – Delete label
```bash
dot-work db-issues labels delete LABEL_ID [--force]
```

**`labels add`** – Add label to issue
```bash
dot-work db-issues labels add ISSUE_ID LABEL [LABEL...]
```

**`labels remove`** – Remove label from issue
```bash
dot-work db-issues labels remove ISSUE_ID LABEL [LABEL...]
```

#### Dependencies

**`deps add`** – Add dependency
```bash
dot-work db-issues deps add FROM_ID TO_ID [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--type` | Dependency type (blocks, depends-on, related-to, duplicates, parent-of, child-of) |

**`deps remove`** – Remove dependency
```bash
dot-work db-issues deps remove FROM_ID TO_ID
```

**`deps check`** – Check dependency
```bash
dot-work db-issues deps check ISSUE_ID
```

**`deps check-all`** – Check for circular dependencies
```bash
dot-work db-issues deps check-all
```

**`deps blocked-by`** – Show blocking issues
```bash
dot-work db-issues deps blocked-by ISSUE_ID
```

**`deps impact`** – Show impact
```bash
dot-work db-issues deps impact ISSUE_ID [--include-transitive]
```

**`deps tree`** – Show dependency tree
```bash
dot-work db-issues deps tree ISSUE_ID [--direction DIR]
```

| Option | Values |
|--------|--------|
| `--direction` | down, up, both |

#### Epics

**`epic create`** – Create epic
```bash
dot-work db-issues epic create TITLE [OPTIONS]
```

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--description` | `-d` | TEXT | Epic description |
| `--parent` | | TEXT | Parent epic ID |

**`epic list`** – List epics
```bash
dot-work db-issues epic list [--status] [--parent]
```

**`epic show`** – Show epic
```bash
dot-work db-issues epic show EPIC_ID
```

**`epic update`** – Update epic
```bash
dot-work db-issues epic update EPIC_ID [OPTIONS]
```

**`epic delete`** – Delete epic
```bash
dot-work db-issues epic delete EPIC_ID
```

**`child add`** – Add child epic
```bash
dot-work db-issues child add PARENT_ID CHILD_ID
```

**`child remove`** – Remove child epic
```bash
dot-work db-issues child remove CHILD_ID
```

**`child list`** – List children
```bash
dot-work db-issues child list PARENT_ID
```

#### Import/Export

**`io export`** – Export issues
```bash
dot-work db-issues io export [OPTIONS]
```

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--output` | `-o` | PATH | Output file |
| `--status` | | TEXT | Filter by status |
| `--type` | | TEXT | Filter by type |
| `--include-completed` | | flag | Include completed |

**`io import`** – Import issues
```bash
dot-work db-issues io import [OPTIONS]
```

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--input` | `-i` | PATH | Input file |
| `--merge` | | flag | Merge with existing (default) |
| `--replace` | | flag | Replace all |

**`io sync`** – Commit to git
```bash
dot-work db-issues io sync [OPTIONS]
```

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--message` | `-m` | TEXT | Commit message |
| `--push` | | flag | Push to remote |

#### Environment Variables

| Variable | Description |
|----------|-------------|
| `DOT_WORK_DB_ISSUES_PATH` | Custom database path |
| `DOT_WORK_DB_ISSUES_DEBUG` | Enable debug mode |
| `EDITOR` | Default editor |

---

### Environment Keys Reference

| Key | Environment | Output Location | File Pattern |
|-----|-------------|-----------------|--------------|
| `copilot` | GitHub Copilot | `.github/prompts/` | `*.prompt.md` |
| `claude` | Claude Code | `.claude/` or project root | `CLAUDE.md` |
| `cursor` | Cursor | `.cursor/rules/` | `*.mdc` |
| `windsurf` | Windsurf | `.windsurf/rules/` | `*.md` |
| `aider` | Aider | project root | `CONVENTIONS.md` |
| `continue` | Continue.dev | `.continue/prompts/` | `*.md` |
| `amazon-q` | Amazon Q | project root | `.amazonq/rules.md` |
| `zed` | Zed AI | `.zed/prompts/` | `*.md` |
| `opencode` | OpenCode | `.opencode/prompts/` + root | `*.md` + `AGENTS.md` |
| `generic` | Generic/Manual | `prompts/` + root | `*.md` + `AGENTS.md` |

---

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (invalid input, not found, etc.) |

---

### Global Options

Available on all commands:

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | `-v` | Show version and exit |
| `--help` | | Show help message |
| `--install-completion` | | Install shell completion |
| `--show-completion` | | Show completion script |

---

## Undocumented Commands

The following commands are shown in main help but not fully documented:

| Command | Description | Status |
|---------|-------------|--------|
| `canonical` | Validate/install canonical prompts | Partially documented |
| `zip` | Zip folders respecting .gitignore | Not documented |
| `container` | Container operations | Not documented |
| `python` | Python utilities | Not documented |
| `git` | Git analysis tools | Not documented |
| `harness` | Claude Agent SDK harness | Not documented |

---

## AI Prompt Triggers

The following are NOT CLI commands but AI prompt triggers (used after `dot-work install`):

| Trigger | Description | Source |
|---------|-------------|--------|
| `/generate-baseline` | Capture quality snapshot | AI prompt |
| `/do-work` | Iteration loop | AI prompt |
| `/continue` | Resume work | AI prompt (should be CLI per review) |
| `/status` | Report focus + counts | AI prompt (should be CLI per review) |
| `/focus on <topic>` | Create prioritized issues | AI prompt (should be CLI per review) |
| `/new-issue` | Create formatted issue | AI prompt |
| `/python-project-from-discussion` | Create Python project | AI prompt |
| `/setup-issue-tracker` | Initialize .work/ | AI prompt |
| `/bump-version` | Semantic version | AI prompt |

*Note: Per user review, some of these should be implemented as CLI commands.*
