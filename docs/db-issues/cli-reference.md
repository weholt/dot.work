# db-issues CLI Reference

Complete reference for all `dot-work db-issues` commands.

## Core Commands

### init

Initialize the database:

```bash
dot-work db-issues init
```

Creates `.work/db-issues/issues.db`.

### create

Create a new issue:

```bash
dot-work db-issues create TITLE [OPTIONS]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--type` | `-T` | Issue type (bug, feature, task, enhancement, refactor, docs, test, security, performance) |
| `--priority` | `-p` | Priority (critical, high, medium, low) |
| `--description` | `-d` | Issue description |
| `--assignee` | `-a` | Assigned user |
| `--labels` | `-l` | Comma-separated labels |
| `--epic` | `-e` | Parent epic ID |

### list

List issues with optional filtering:

```bash
dot-work db-issues list [OPTIONS]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--status` | `-s` | Filter by status |
| `--priority` | `-p` | Filter by priority |
| `--type` | `-t` | Filter by type |
| `--assignee` | `-a` | Filter by assignee |
| `--epic` | `-e` | Filter by epic |
| `--labels` | `-l` | Filter by labels (comma-separated) |
| `--limit` | | Limit results |
| `--sort` | | Sort by field (created, updated, priority, status) |
| `--output` | `-o` | Output format (table, json, yaml) |

### show

Show issue details:

```bash
dot-work db-issues show ISSUE_ID
```

### update

Update issue fields:

```bash
dot-work db-issues update ISSUE_ID [OPTIONS]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--title` | `-t` | New title |
| `--description` | `-d` | New description |
| `--priority` | `-p` | New priority |
| `--assignee` | `-a` | New assignee |
| `--status` | `-s` | New status (proposed, in-progress, blocked, completed, wont-fix) |
| `--type` | `-T` | New issue type |

### close

Close an issue:

```bash
dot-work db-issues close ISSUE_ID
```

Sets status to `completed`.

### delete

Delete an issue:

```bash
dot-work db-issues delete ISSUE_ID
```

### comment

Add a comment to an issue:

```bash
dot-work db-issues comment ISSUE_ID CONTENT
```

## Search Commands

### search

Search issues by text:

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

## Label Commands

### labels create

Create a label:

```bash
dot-work db-issues labels create NAME [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--color`, `-c` | Label color (named, hex, or RGB) |
| `--description`, `-d` | Label description |

Color formats:
- Named: `red`, `blue`, `green`, `yellow`, `orange`, `purple`, etc.
- Hex: `#ff0000`, `00ff00`
- RGB: `rgb(255, 0, 0)`

### labels list

List labels:

```bash
dot-work db-issues labels list [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--unused` | Show only unused labels |

### labels update

Update a label:

```bash
dot-work db-issues labels update LABEL_ID [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--color`, `-c` | New color |
| `--description`, `-d` | New description |

### labels rename

Rename a label:

```bash
dot-work db-issues labels rename LABEL_ID NEW_NAME
```

### labels delete

Delete a label:

```bash
dot-work db-issues labels delete LABEL_ID [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--force`, `-f` | Skip confirmation |

### labels add

Add label to issue:

```bash
dot-work db-issues labels add ISSUE_ID LABEL [LABEL...]
```

### labels remove

Remove label from issue:

```bash
dot-work db-issues labels remove ISSUE_ID LABEL [LABEL...]
```

## Dependency Commands

### deps add

Add dependency between issues:

```bash
dot-work db-issues deps add FROM_ID TO_ID [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--type` | Dependency type (blocks, depends-on, related-to, duplicates, parent-of, child-of) |

### deps remove

Remove dependency:

```bash
dot-work db-issues deps remove FROM_ID TO_ID
```

### deps check

Check specific dependency:

```bash
dot-work db-issues deps check ISSUE_ID
```

### deps check-all

Check all issues for circular dependencies:

```bash
dot-work db-issues deps check-all
```

### deps blocked-by

Show issues blocking this issue:

```bash
dot-work db-issues deps blocked-by ISSUE_ID
```

### deps impact

Show impact of an issue:

```bash
dot-work db-issues deps impact ISSUE_ID [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--include-transitive` | Include transitive dependencies |

### deps tree

Show dependency tree:

```bash
dot-work db-issues deps tree ISSUE_ID [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--direction` | Tree direction (down, up, both) |

## Epic Commands

### epic create

Create an epic:

```bash
dot-work db-issues epic create TITLE [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--description`, `-d` | Epic description |
| `--parent` | Parent epic ID |

### epic list

List epics:

```bash
dot-work db-issues epic list [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--status` | Filter by status |
| `--parent` | Filter by parent epic |

### epic show

Show epic details:

```bash
dot-work db-issues epic show EPIC_ID
```

### epic update

Update epic:

```bash
dot-work db-issues epic update EPIC_ID [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--title` | New title |
| `--description` | New description |
| `--status` | New status |

### epic delete

Delete epic:

```bash
dot-work db-issues epic delete EPIC_ID
```

### child add

Add child epic:

```bash
dot-work db-issues child add PARENT_ID CHILD_ID
```

### child remove

Remove child epic:

```bash
dot-work db-issues child remove CHILD_ID
```

### child list

List child epics:

```bash
dot-work db-issues child list PARENT_ID
```

## Editor Command

### edit

Edit issue in external editor:

```bash
dot-work db-issues edit ISSUE_ID [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--editor`, `-e` | Editor command (default: $EDITOR or vi) |

## Import/Export Commands

### io export

Export issues to JSONL:

```bash
dot-work db-issues io export [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--output`, `-o` | Output file path |
| `--status` | Filter by status |
| `--type` | Filter by type |
| `--include-completed` | Include completed issues |

### io import

Import issues from JSONL:

```bash
dot-work db-issues io import [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--input`, `-i` | Input file path |
| `--merge` | Merge with existing (default) |
| `--replace` | Replace all (clear first) |

### io sync

Commit changes to git:

```bash
dot-work db-issues io sync [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--message`, `-m` | Commit message |
| `--push` | Push to remote |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (issue not found, invalid input, etc.) |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DOT_WORK_DB_ISSUES_PATH` | Custom database path (default: `.work/db-issues/issues.db`) |
| `DOT_WORK_DB_ISSUES_DEBUG` | Enable debug mode (default: false) |
| `EDITOR` | Default editor for `edit` command |
