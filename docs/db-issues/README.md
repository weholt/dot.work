# dot-work db-issues

Database-backed issue tracking for dot-work.

## What is db-issues?

`db-issues` is a SQLite-based issue tracking system that provides:
- Fast local issue storage and querying
- Full-featured CLI for issue management
- Issue relationships (dependencies, epics, parent-child)
- Label management with colors
- JSONL export/import for backup and migration
- Git integration for commit tracking

## Quick Start

```bash
# Initialize database (creates .work/db-issues/issues.db)
dot-work db-issues init

# Create an issue
dot-work db-issues create "Fix parser bug" \
  --type bug \
  --priority high \
  --description "The parser fails on nested quotes"

# List issues
dot-work db-issues list
dot-work db-issues list --status proposed

# Update an issue
dot-work db-issues update <id> --status in-progress
dot-work db-issues update <id> --priority critical

# Close an issue
dot-work db-issues close <id>

# Show issue details
dot-work db-issues show <id>
```

## Configuration

The database is stored at `.work/db-issues/issues.db` by default.

Override via environment variable:
```bash
export DOT_WORK_DB_ISSUES_PATH=/custom/path/issues.db
```

Enable debug mode:
```bash
export DOT_WORK_DB_ISSUES_DEBUG=true
```

## Database Schema

### Issues
- `id`: Unique identifier (e.g., `bd-a1b2c3`)
- `title`: Issue title
- `description`: Detailed description
- `status`: proposed, in-progress, blocked, completed, wont-fix
- `priority`: critical, high, medium, low
- `type`: bug, feature, task, enhancement, refactor, docs, test, security, performance
- `assignee`: Assigned user (optional)
- `epic_id`: Parent epic (optional)
- `labels`: List of label names
- `created_at`, `updated_at`, `closed_at`: Timestamps

### Labels
- `id`: Unique identifier
- `name`: Label name (unique)
- `color`: Hex color code
- `description`: Label description (optional)

### Comments
- `id`: Unique identifier
- `issue_id`: Parent issue
- `content`: Comment text
- `created_at`: Timestamp

### Dependencies
- `id`: Unique identifier
- `from_issue_id`: Source issue
- `to_issue_id`: Target issue
- `type`: blocks, depends-on, related-to, duplicates, parent-of, child-of

### Epics
- `id`: Unique identifier
- `title`: Epic title
- `description`: Epic description
- `status`: open, in-progress, completed, closed
- `parent_epic_id`: Parent epic (for nesting)

## Migration from Other Tools

### From GitHub Issues
```bash
# Export from GitHub (using gh CLI)
gh issue list --json number,title,state,body > issues.json
# Convert and import (requires conversion script)
```

### From GitLab Issues
```bash
# Export from GitLab
# Import using JSONL export/import
```

### From Jira
```bash
# Export to CSV/JSON
# Convert to JSONL format
# Import with dot-work db-issues io import
```

## Backup and Restore

```bash
# Export all issues to JSONL
dot-work db-issues io export --output backup.jsonl

# Import from backup
dot-work db-issues io import --input backup.jsonl --merge

# Export completed issues
dot-work db-issues io export --status completed --output done.jsonl
```

## Architecture

The db-issues module follows Domain-Driven Design (DDD) patterns:

- **Domain Layer**: Entities (Issue, Label, Comment, Epic, Dependency)
- **Service Layer**: Business logic (IssueService, LabelService, EpicService, etc.)
- **Adapter Layer**: Database persistence (SQLModel repositories)
- **CLI Layer**: Typer-based command interface

```
src/dot_work/db_issues/
├── domain/
│   └── entities.py     # Domain entities
├── services/
│   ├── issue_service.py
│   ├── label_service.py
│   ├── epic_service.py
│   └── ...
├── adapters/
│   └── sqlite.py        # SQLModel repositories
├── config.py            # Configuration
└── cli.py               # CLI commands
```

## Contributing

See [Contributing Guide](./contributing.md) for development setup and guidelines.
