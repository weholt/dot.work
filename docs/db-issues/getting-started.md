# Getting Started with db-issues

This guide will help you get started with the db-issues CLI for tracking your work.

## Installation

db-issues is part of dot-work. Install with `uv`:

```bash
pip install uv
uv pip install dot-work
```

## Initialize Database

Create the database file:

```bash
dot-work db-issues init
```

This creates `.work/db-issues/issues.db`.

## Create Your First Issue

```bash
dot-work db-issues create "Fix parser bug" \
  --type bug \
  --priority high
```

Required arguments:
- `title`: Issue title (positional argument)

Optional options:
- `--type`, `-T`: Issue type (bug, feature, task, enhancement, refactor, docs, test, security, performance)
- `--priority`, `-p`: Priority (critical, high, medium, low)
- `--description`, `-d`: Detailed description
- `--assignee`, `-a`: Assigned user
- `--labels`: Comma-separated labels
- `--epic`: Parent epic ID

## List and Filter Issues

```bash
# List all issues
dot-work db-issues list

# Filter by status
dot-work db-issues list --status in-progress
dot-work db-issues list --status proposed

# Filter by priority
dot-work db-issues list --priority critical

# Filter by type
dot-work db-issues list --type bug

# Limit results
dot-work db-issues list --limit 10

# Sort by field
dot-work db-issues list --sort created  # oldest first
dot-work db-issues list --sort -updated  # newest first
```

## Update Issues

```bash
# Change status
dot-work db-issues update <id> --status in-progress

# Change priority
dot-work db-issues update <id> --priority critical

# Update multiple fields
dot-work db-issues update <id> \
  --title "Updated title" \
  --status in-progress \
  --priority high

# Update description inline
dot-work db-issues update <id> --description "New description"

# Edit in external editor
dot-work db-issues edit <id>
```

## Add Comments

```bash
dot-work db-issues comment <id> "This needs more investigation"
```

## Close and Reopen

```bash
# Close an issue
dot-work db-issues close <id>

# Reopen a closed issue
dot-work db-issues reopen <id>
```

## Work with Labels

```bash
# Create labels with colors
dot-work db-issues labels create "bug" --color red
dot-work db-issues labels create "feature" --color blue
dot-work db-issues labels create "urgent" --color "#ff0000"

# List all labels
dot-work db-issues labels list

# Add labels to issue
dot-work db-issues labels add <id> "bug"
dot-work db-issues labels add <id> "urgent"

# Remove labels from issue
dot-work db-issues labels remove <id> "bug"

# Show issue's labels
dot-work db-issues labels list <id>
```

## Manage Dependencies

```bash
# Add dependency (issue blocks another)
dot-work db-issues deps add <id> <blocks-id> --type blocks

# Remove dependency
dot-work db-issues deps remove <id> <blocks-id>

# Check for circular dependencies
dot-work db-issues deps check-all

# Show blocked-by issues
dot-work db-issues deps blocked-by <id>

# Show dependency impact
dot-work db-issues deps impact <id>
```

## Work with Epics

```bash
# Create epic
dot-work db-issues epic create "User Authentication" \
  --description "Implement login and signup"

# List epics
dot-work db-issues epic list

# Add child epic
dot-work db-issues child add <parent-id> <child-id>

# Remove child epic
dot-work db-issues child remove <child-id>

# List children
dot-work db-issues child list <parent-id>
```

## Search Issues

```bash
# Search by text
dot-work db-issues search "parser bug"

# Search by title only
dot-work db-issues search "parser" --field title

# Search by description
dot-work db-issues search "crash" --field description

# Filter search results
dot-work db-issues search "bug" --type bug --status open
```

## Export and Import

```bash
# Export all issues
dot-work db-issues io export

# Export to specific file
dot-work db-issues io export --output backup.jsonl

# Export completed issues only
dot-work db-issues io export --status completed

# Import from file (merge strategy)
dot-work db-issues io import --input backup.jsonl

# Import with replacement (clears first)
dot-work db-issues io import --input backup.jsonl --replace

# Sync with git (commits changes)
dot-work db-issues io sync --message "Updated issues" --push
```

## Common Workflows

### Personal Workflow

```bash
# Plan work
dot-work db-issues create "Implement feature X" --type feature
dot-work db-issues create "Fix bug Y" --type bug --priority high

# Start working
dot-work db-issues update <id> --status in-progress

# Done
dot-work db-issues close <id>
```

### Team Workflow

```bash
# Assign work
dot-work db-issues update <id> --assignee alice

# Comment on progress
dot-work db-issues comment <id> "Investigating the root cause..."

# Request review
dot-work db-issues update <id> --labels "review"
```

### Bug Tracking Workflow

```bash
# Create bug report
dot-work db-issues create "Crash on startup" \
  --type bug \
  --priority critical \
  --description "Application crashes when starting with config file X"

# Add blocking dependency
dot-work db-issues deps add <crash-id> <fix-id> --type blocks

# Track progress
dot-work db-issues update <id> --status in-progress
dot-work db-issues comment <id> "Fixed the null pointer dereference"

# Verify fix
dot-work db-issues update <id> --status completed
```

## Next Steps

- See [CLI Reference](./cli-reference.md) for complete command documentation
- See [Examples](./examples.md) for more usage examples
- See [Architecture](./architecture.md) for module design details
