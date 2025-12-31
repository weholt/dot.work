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
| `init-tracking` | Initialize .work/ directory | CLI |
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

### `init-tracking` – Initialize Issue Tracking

Initialize the `.work/` issue tracking directory structure.

```bash
dot-work init-tracking [OPTIONS]
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

#### Review Storage

Reviews are stored in the `.work/reviews/` directory with the following structure:

```
.work/reviews/
├── reviews/           # Individual review data
│   ├── 20241221-143500/    # Review ID (YYYYMMDD-HHMMSS)
│   │   └── comments.jsonl  # Review comments (JSONL format)
│   ├── 20241222-100000/
│   │   └── comments.jsonl
│   └── ...
└── exports/           # Exported review files
    └── review.md
```

**Review ID Format:** `YYYYMMDD-HHMMSS` (timestamp when review was started)

**Configuration:**
- Default storage directory: `.work/reviews/`
- Can be overridden via `DOT_WORK_REVIEW_STORAGE_DIR` environment variable
- Server host: `127.0.0.1` (configurable via `DOT_WORK_REVIEW_HOST`)
- Server port: `0` (auto-pick, configurable via `DOT_WORK_REVIEW_PORT`)

**Listing Reviews:**
```bash
# List all review directories
ls -la .work/reviews/reviews/

# Get the latest review ID
cat .work/reviews/reviews/$(ls -t .work/reviews/reviews/ | head -1)/comments.jsonl | jq -r '.review_id' | head -1
```

**Cleaning Up Old Reviews:**
```bash
# Remove a specific review
rm -rf .work/reviews/reviews/YYYYMMDD-HHMMSS/

# Remove all reviews (use with caution)
rm -rf .work/reviews/reviews/*
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

#### Database Storage

The knowledge graph database is stored in SQLite with the following structure:

**Default Location:** `.work/kg/db.sqlite`

**Configuration:**
- Can be overridden via `DOT_WORK_KG_DB_PATH` environment variable
- For global knowledge base: `export DOT_WORK_KG_DB_PATH=~/.kg/db.sqlite`

**Database Schema:**

The database contains the following tables:

| Table | Description |
|-------|-------------|
| `documents` | Source documents (doc_id, path, sha256, raw content) |
| `nodes` | Parsed content blocks (headers, paragraphs, code, lists) |
| `edges` | Relationships between nodes (parent-child, references) |
| `fts_nodes` | Full-text search index for node content |
| `embeddings` | Vector embeddings for semantic search |
| `collections` | Projects/knowledgebases/workspaces |
| `collection_members` | Links collections to docs/nodes |
| `topics` | Reusable tags/categories |
| `topic_links` | Links topics to docs/nodes |
| `project_settings` | Per-collection defaults |

**Key Indexes:**
- `idx_nodes_doc_id` - Fast document lookups
- `idx_nodes_short_id` - Node ID lookups
- `idx_edges_type_src_dst` - Composite index for type-filtered edge queries
- `idx_edges_type` - Edge type filtering
- `idx_embeddings_full_id` - Embedding lookups by node ID

**Backing Up:**
```bash
# Simple file copy
cp .work/kg/db.sqlite backup/kg-backup-$(date +%Y%m%d).sqlite

# Or use SQLite backup command
sqlite3 .work/kg/db.sqlite ".backup backup/kg-backup.sqlite"
```

**Migrating Between Projects:**
```bash
# Copy database to new project
cp /path/to/old/project/.work/kg/db.sqlite .work/kg/db.sqlite

# Export and re-import (for schema migration)
dot-work kg export --format json > kg-export.json
# (In new project)
dot-work kg ingest --import kg-export.json
```

**Database Status:**
```bash
# Check if database exists and location
dot-work kg status

# Show database statistics
dot-work kg stats
```

#### Searching the Knowledge Graph

The knowledge graph supports multiple search methods:

**1. Full-Text Search (FTS)**

Search for nodes by title and content:
```bash
# Simple search
dot-work kg search "authentication flow"

# Search in specific scope
dot-work kg search "API" --scope src/

# Limit results
dot-work kg search "database" --limit 10

# FTS5 query syntax (advanced)
dot-work kg search "user NEAR/5 password"  # words within 5 positions
dot-work kg search "auth*"  # prefix match
dot-work kg search '"login system"'  # exact phrase
```

**2. Semantic Search**

Search by meaning using vector embeddings:
```bash
# Semantic search (requires embeddings to be generated)
dot-work kg search --semantic "how to handle errors"

# Specify embedding model
dot-work kg search --semantic --model openai "authentication methods"

# Combine with scope
dot-work kg search --semantic "database design" --scope docs/
```

**3. Scope Filtering**

Limit search to specific files or directories:
```bash
# Single file
dot-work kg search "function" --scope src/main.py

# Directory pattern
dot-work kg search "class" --scope src/models/

# Multiple scopes
dot-work kg search "import" --scope src/ --scope tests/

# Exclude paths
dot-work kg search "TODO" --exclude-scope vendor/
```

**4. Output Formats**

```bash
# Table format (default)
dot-work kg search "API"

# JSON output
dot-work kg search "database" --format json

# Include full content
dot-work kg search "config" --full-content

# Show as outline tree
dot-work kg search "security" --outline
```

**Search Examples:**

```bash
# Find all documentation about authentication
dot-work kg search "authentication" --scope docs/

# Search for code comments mentioning TODO or FIXME
dot-work kg search "TODO OR FIXME" --scope src/

# Semantic search for error handling patterns
dot-work kg search --semantic "error handling best practices"

# Combine semantic search with scope
dot-work kg search --semantic "API endpoints" --scope api/
```

**Note:** Semantic search requires embeddings to be generated. Use `dot-work kg ingest` with an embedding model to create vector embeddings for your documents.

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

#### Database Storage

The db-issues database is stored in SQLite with the following structure:

**Default Location:** `.work/db-issues/issues.db`

**Configuration:**
- Can be overridden via `DOT_WORK_DB_ISSUES_PATH` environment variable
- Example: `export DOT_WORK_DB_ISSUES_PATH=/custom/path/issues.db`
- Path security validated to prevent directory traversal attacks

**Database Schema:**

The database contains the following tables:

| Table | Description |
|-------|-------------|
| `projects` | Project settings and metadata |
| `issues` | Issue records with status, priority, type |
| `epics` | Epic parent records for grouping issues |
| `dependencies` | Issue dependency relationships (blocks/blocked-by) |
| `labels` | Issue labels/categories |
| `issue_labels` | Junction table for issue-label relationships |
| `assignees` | Issue assignees |
| `issue_assignees` | Junction table for issue-assignee relationships |
| `references` | External issue references |
| `issue_references` | Junction table for issue-reference relationships |
| `comments` | Issue comments and discussion history |
| `fts_issues` | Full-text search index for issues |
| `schema_version` | Database migration version tracking |

**Backing Up:**
```bash
# Simple file copy
cp .work/db-issues/issues.db backup/db-issues-$(date +%Y%m%d).db

# Export to JSONL (portable format)
dot-work db-issues export --output backup/issues-$(date +%Y%m%d).jsonl

# Import from JSONL
dot-work db-issues import --input backup/issues-YYYYMMDD.jsonl
```

**Migrating Between Projects:**
```bash
# Copy database directly
cp /path/to/old/project/.work/db-issues/issues.db .work/db-issues/issues.db

# Or use JSONL export/import for cleaner migration
dot-work db-issues export --output all-issues.jsonl
# (In new project)
dot-work db-issues import --input all-issues.jsonl
```

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
