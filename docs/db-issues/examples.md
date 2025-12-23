# db-issues Usage Examples

Practical examples for common workflows with db-issues.

## Personal Development Workflow

```bash
# Plan sprint work
dot-work db-issues create "Add user authentication" --type feature --priority high
dot-work db-issues create "Fix login bug" --type bug --priority critical
dot-work db-issues create "Write tests for auth" --type test --priority medium

# List your work
dot-work db-issues list --sort created

# Start working on first issue
ISSUE_ID=$(dot-work db-issues list --limit 1 --output json | jq -r '.[0].id')
dot-work db-issues update $ISSUE_ID --status in-progress

# Document progress
dot-work db-issues comment $ISSUE_ID "Started implementing OAuth2"

# Done with this task
dot-work db-issues close $ISSUE_ID
```

## Bug Tracking Workflow

```bash
# Report a new bug
BUG_ID=$(dot-work db-issues create "Crash on startup with config file X" \
  --type bug \
  --priority critical \
  --description "Application crashes immediately when starting
with config file X. Stack trace shows null pointer at line 42.")

# Investigate and add details
dot-work db-issues comment $BUG_ID "Root cause: Config parser doesn't
handle empty values in the database section."

# Start fix
dot-work db-issues update $BUG_ID --status in-progress

# Add blocking relationship to the config fix
dot-work db-issues deps add $BUG_ID $(dot-work db-issues list --type feature --limit 1 --output json | jq -r '.[0].id') --type blocks

# Fix verified
dot-work db-issues comment $BUG_ID "Fixed by adding null check in config parser."
dot-work db-issues close $BUG_ID
```

## Feature Development Workflow

```bash
# Create epic for feature
EPIC_ID=$(dot-work db-issues epic create "User Authentication" \
  --description "Implement login, signup, and password reset")

# Create child issues for the epic
dot-work db-issues create "Implement OAuth2 login" --epic $EPIC_ID --type feature
dot-work db-issues create "Add signup form" --epic $EPIC_ID --type feature
dot-work db-issues create "Implement password reset" --epic $EPIC_ID --type feature
dot-work db-issues create "Write auth tests" --epic $EPIC_ID --type test

# Create labels for tracking
dot-work db-issues labels create "backend" --color blue
dot-work db-issues labels create "frontend" --color green
dot-work db-issues labels create "testing" --color yellow

# List epic progress
dot-work db-issues epic show $EPIC_ID
dot-work db-issues child list $EPIC_ID

# Update epic status when done
dot-work db-issues epic update $EPIC_ID --status completed
```

## Label Management Workflow

```bash
# Setup labels for your project
dot-work db-issues labels create "bug" --color red --description "Bug reports"
dot-work db-issues labels create "feature" --color blue --description "Feature requests"
dot-work db-issues labels create "urgent" --color "#ff4444" --description "Urgent items"
dot-work db-issues labels create "enhancement" --color "#00aa00" --description "Improvements"

# Label issues during creation
dot-work db-issues create "Fix crash" --type bug --labels bug,urgent

# Add labels later
dot-work db-issues labels add <id> bug enhancement

# View issues by label
dot-work db-issues list --labels bug

# Show unused labels (labels not attached to any issue)
dot-work db-issues labels list --unused

# Update label color
dot-work db-issues labels update <label_id> --color darkred
```

## Dependency Management

```bash
# Create issues with dependencies
LOGIN_ID=$(dot-work db-issues create "Implement login" --type feature)
SESSION_ID=$(dot-work db-issues create "Implement session management" --type feature)
AUTH_ID=$(dot-work db-issues create "Add authentication middleware" --type feature)

# Setup dependency chain
dot-work db-issues deps add $SESSION_ID $LOGIN_ID --type depends-on
dot-work db-issues deps add $AUTH_ID $SESSION_ID --type blocks

# Check for circular dependencies
dot-work db-issues deps check-all

# Show what blocks an issue
dot-work db-issues deps blocked-by $LOGIN_ID

# Show impact tree
dot-work db-issues deps tree $LOGIN_ID --direction down
```

## Backup and Restore

```bash
# Daily backup
DATE=$(date +%Y%m%d)
dot-work db-issues io export --output backups/issues-$DATE.jsonl

# Restore from backup
dot-work db-issues io import --input backups/issues-20241223.jsonl

# Export only completed work
dot-work db-issues io export --status completed --output done.jsonl

# Git sync for version control
dot-work db-issues io sync --message "Daily backup" --push
```

## Git Integration

```bash
# Commit after closing issues
dot-work db-issues close <id>
dot-work db-issues io sync --message "Closed $(dot-work db-issues show <id> --output json | jq -r '.title')"

# Link issues to commits
dot-work db-issues comment <id> "Implemented in commit abc123"
```

## Team Collaboration

```bash
# Assign work to team members
dot-work db-issues update <id> --assignee alice
dot-work db-issues update <id> --assignee bob

# Request review
dot-work db-issues labels add <id> review
dot-work db-issues comment <id> "@alice Please review this fix"

# Track review status
dot-work db-issues list --assignee alice
dot-work db-issues list --labels review
```

## Search Examples

```bash
# Find all open bugs
dot-work db-issues search "crash" --type bug --status proposed

# Search in titles only
dot-work db-issues search "auth" --field title

# Search in descriptions
dot-work db-issues search "config" --field description

# Search with multiple filters
dot-work db-issues search "parser" --type bug --priority critical
```

## Advanced Filtering

```bash
# Show critical bugs
dot-work db-issues list --type bug --priority critical

# Show my assigned work
dot-work db-issues list --assignee $USER

# Show proposed issues
dot-work db-issues list --status proposed

# Sort by most recently updated
dot-work db-issues list --sort -updated --limit 10

# Show high-priority in-progress items
dot-work db-issues list --status in-progress --priority critical,high
```

## Status Workflow

```bash
# Standard status progression
dot-work db-issues update <id> --status in-progress  # Start work
dot-work db-issues update <id> --status blocked       # Waiting on dependency
dot-work db-issues update <id> --status in-progress  # Unblocked
dot-work db-issues close <id>                         # Complete (sets to completed)

# Reopen closed issue
dot-work db-issues reopen <id>  # Sets back to proposed
```

## Multi-Field Updates

```bash
# Update multiple fields at once
dot-work db-issues update <id> \
  --title "Updated title: more specific" \
  --priority critical \
  --status in-progress \
  --type bug \
  --assignee alice
```

## Editor Workflow

```bash
# Edit with default editor ($EDITOR or vi)
dot-work db-issues edit <id>

# Edit with specific editor
dot-work db-issues edit <id> --editor vim
dot-work db-issues edit <id> --editor nano
dot-work db-issues edit <id> --editor code

# The editor opens a YAML template:
# # dot-work db-issues edit
# id: bd-a1b2
# title: Fix parser bug
# description: |
#   The parser fails when...
# priority: high
# type: bug
# status: in-progress

# Make your changes, save, and exit to apply
```

## Output Formats

```bash
# Table output (default)
dot-work db-issues list

# JSON output (for scripting)
dot-work db-issues list --output json | jq '.[] | {id, title, status}'

# YAML output
dot-work db-issues list --output yaml

# Pipe to other tools
dot-work db-issues list --output json | jq -r '.[].id' | xargs -I {} dot-work db-issues show {}
```

## Batch Operations

```bash
# Close all completed issues in an epic
EPIC_ID="bd-epic123"
dot-work db-issues list --epic $EPIC_ID --status in-progress --output json | \
  jq -r '.[].id' | \
  xargs -I {} dot-work db-issues close {}

# Add label to all bugs
dot-work db-issues list --type bug --output json | \
  jq -r '.[].id' | \
  xargs -I {} dot-work db-issues labels add {} backend
```
