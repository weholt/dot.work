# DB-Issues Migration Investigation

**Investigation started:** 2024-12-22
**Issue reference:** MIGRATE-034 through MIGRATE-050+
**Goal:** 100% feature parity migration from glorious issue-tracker
**Source:** `/home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/src/issue_tracker/`

---

## Complete Feature Inventory (from source analysis)

### 1. Core Issue Operations
- `create` - Create new issue
- `list` - List issues with filtering
- `show` - Show issue details
- `update` - Update issue fields
- `close` - Close issue
- `reopen` - Reopen issue
- `delete` - Delete issue (with --force flag)
- `restore` - Restore deleted issue

### 2. Issue Status Management
- `ready` - Mark issue as ready
- `blocked` - Mark issue as blocked
- `stale` - Mark issue as stale

### 3. Bulk Operations (CRITICAL)
- `bulk-create` - Create multiple issues from CSV/json
- `bulk-close` - Bulk close multiple issues
- `bulk-update` - Bulk update issue properties
- `bulk-label-add` - Add labels to multiple issues
- `bulk-label-remove` - Remove labels from multiple issues

### 4. Dependency Management (ADVANCED)
- `dependencies add` - Add dependency between issues
- `dependencies remove` - Remove dependency
- `dependencies list` - List dependencies for issue
- `dependencies list-all` - List all dependencies globally
- `dependencies tree` - Show dependency tree with visualization
- `dependencies cycles` - Detect and show dependency cycles with fix suggestions

**Dependency Types:** blocks, depends-on, related-to, discovered-from

### 5. Epic Management
- `epics add` - Add issue to epic
- `epics remove` - Remove issue from epic
- `epics list` - List issues in epic
- `epics set` - Assign issue to epic (spec-compliant)
- `epics clear` - Remove issue from epic
- `epics all` - List all epics with counts
- `epics tree` - Show epic hierarchy tree

### 6. Label Management
- `labels add` - Add labels to issue
- `labels remove` - Remove labels from issue
- `labels set` - Set all labels on issue
- `labels list` - List labels (for issue or globally)
- `labels all` - List all unique labels
- `labels bulk-add` - Bulk add labels to multiple issues
- `labels bulk-remove` - Bulk remove labels from multiple issues

### 7. Comment Management
- `comments add` - Add comment to issue
- `comments list` - List comments on issue
- `comments delete` - Delete comment (with --force flag)

### 8. JSON Templates System
- `template save` - Save issue template
- `template list` - List available templates
- `template show` - Show template details
- `template delete` - Delete template

### 9. Instruction Templates (MARKDOWN-BASED - MAJOR FEATURE)
- `instructions list` - List instruction templates
- `instructions show` - Display instruction template
- `instructions apply` - Apply template to create multiple issues

**Instruction Template Features:**
- Complex task workflows from markdown
- Multi-issue creation from single template
- Task definitions with priorities, efforts, subtasks, acceptance criteria
- Hierarchical template support
- Epic integration with templates

### 10. Search and Stats
- `search` - Full-text search using FTS5
  - BM25 ranking algorithm
  - Snippet highlighting with `<mark>` tags
  - Field-specific searches (title:, description:)
  - Proximity searches (NEAR operator)
- `stats` - Show issue statistics and metrics
  - Issue counts by status and priority
  - Blocked issues analysis
  - Longest dependency chain calculation
  - Completion rate tracking
  - Resolution rate metrics

### 11. System Operations
- `init` - Initialize issue tracker
- `sync` - Sync with git (JSONL export/import)
- `export` - Export to JSONL format
- `import` - Import from JSONL format
- `rename-prefix` - Rename issue ID prefixes
- `cleanup` - Cleanup operations (archive old issues)
- `duplicates` - Find and manage duplicate issues
- `merge` - Merge duplicate issues
- `edit` - Edit issue in external editor
- `compact` - Compact database
- `info` - Show system information

### 12. Advanced Features
- **Ready Queue Calculation**: Issues with no open blockers
- **Blocker Tracking**: Identify what blocks what
- **Stale Detection**: Automatic stale issue identification
- **Duplicate Detection**: Automatic duplicate finding
- **Visualization**: ASCII tree rendering, Mermaid diagrams
- **Advanced Querying**: Complex filtering, sorting, pagination

### 13. Data Model
- **Status Values**: open, closed, resolved, blocked, in_progress
- **Priority Levels**: critical (0), high (1), medium (2), low (3), backlog (4)
- **Issue Types**: task, bug, feature, epic, story
- **Assignee Support**: Multi-assignee tracking
- **Project Support**: Multi-project issue tracking
- **Time Tracking**: Created, updated, closed timestamps
- **Hash-based IDs**: bd-a1b2 format with child IDs (bd-a1b2.1)

### 14. Database Features
- SQLite with proper indexing
- Unit of Work pattern
- Transaction management
- FTS5 virtual table for search
- Schema migrations
- Data integrity constraints

---

## What is EXCLUDED (by user request)

- **daemon/**: Background daemon with IPC/RPC
- **adapters/mcp/**: MCP server for Claude
- **factories/**: Complex DI for daemon
- CLI commands: daemon-*, rpc-*, mcp-*

---

## Migration Issues Analysis

### Current Issues (MIGRATE-034 through MIGRATE-040)
Coverage: ~30% of feature parity

Cover:
- Basic module structure
- Import refactoring
- Basic CLI integration
- Core dependencies
- Basic storage configuration
- Unit tests
- Build verification

### Additional Issues (MIGRATE-041 through MIGRATE-050)
Coverage: ~60% of feature parity

Cover:
- Enums definition
- Basic epic commands
- JSONL export/import
- Output formats
- Enhanced search
- Status transitions
- Circular dependency detection
- Label management
- Enhanced update
- Documentation

### STILL MISSING for 100% Parity

The following features are NOT covered by MIGRATE-034 through MIGRATE-050:

1. **Instruction Templates Subsystem** (MAJOR - entire system)
   - templates/instruction_template.py - Markdown parser
   - templates/template_manager.py - Template manager
   - cli/commands/instructions.py - list, show, apply commands
   - Complex task workflows, subtasks, acceptance criteria

2. **JSON Template Management**
   - template save, list, show, delete commands
   - Predefined issue configurations

3. **Bulk Operations** (CRITICAL)
   - bulk-create from CSV/JSON
   - bulk-close, bulk-update
   - bulk-label-add, bulk-label-remove

4. **Advanced Dependency Features**
   - dependencies list-all (global view)
   - dependencies tree (visualization)
   - dependencies cycles (cycle detection with fix suggestions)
   - Ready queue calculation

5. **Advanced Epic Features**
   - epics set, clear commands
   - epics all (list all with counts)
   - epics tree (hierarchical visualization)

6. **Advanced Label Features**
   - labels set (replace all labels)
   - labels all (list unique globally)
   - labels bulk-add, bulk-remove

7. **Comment System** (COMPLETE)
   - comments add, list, delete
   - Comment entity with timestamps

8. **Issue Status Management**
   - ready, blocked, stale commands
   - Additional status values: resolved, in_progress

9. **System Operations**
   - init (initialize tracker)
   - sync (git integration)
   - rename-prefix
   - cleanup
   - duplicates detection
   - merge issues
   - edit in external editor
   - compact database
   - info command

10. **Statistics and Analytics**
    - stats command with comprehensive metrics
    - Historical trend analysis
    - Dependency chain analysis

11. **Advanced Search (FTS5)**
    - Full BM25 ranking
    - Snippet highlighting
    - Field-specific searches
    - Proximity operators

12. **Visualization**
    - ASCII tree rendering
    - Mermaid diagram generation
    - Rich console output

13. **Assignee Management**
    - Assignee tracking
    - Assignee filtering
    - Multi-assignee support

14. **Project Support**
    - Multi-project tracking
    - Project-based isolation

15. **Advanced Output Formats**
    - JSON output for programmatic access
    - Multiple format support across all commands

---

## Required Additional Issues for 100% Parity

Based on the comprehensive gap analysis, the following issues are REQUIRED:

### Phase 1: Core Missing Features (MIGRATE-051 to MIGRATE-060)
- MIGRATE-051: Implement Comment System (add, list, delete)
- MIGRATE-052: Implement Instruction Templates Subsystem
- MIGRATE-053: Implement JSON Template Management
- MIGRATE-054: Implement Bulk Operations (create, close, update)
- MIGRATE-055: Implement Bulk Label Operations
- MIGRATE-056: Implement Advanced Dependency Features (list-all, tree, cycles)
- MIGRATE-057: Implement Ready Queue Calculation
- MIGRATE-058: Implement Advanced Epic Features (set, clear, all, tree)
- MIGRATE-059: Implement Advanced Label Features (set, all, bulk)
- MIGRATE-060: Implement Issue Status Commands (ready, blocked, stale)

### Phase 2: System Operations (MIGRATE-061 to MIGRATE-070)
- MIGRATE-061: Implement System Commands (init, info, compact)
- MIGRATE-062: Implement Sync Command with Git Integration
- MIGRATE-063: Implement Rename-Prefix Command
- MIGRATE-064: Implement Cleanup Command
- MIGRATE-065: Implement Duplicates Detection
- MIGRATE-066: Implement Merge Command
- MIGRATE-067: Implement Edit Command ($EDITOR integration)
- MIGRATE-068: Implement Restore Command
- MIGRATE-069: Implement Delete with --force Flag
- MIGRATE-070: Implement FTS5 Full-Text Search

### Phase 3: Advanced Features (MIGRATE-071 to MIGRATE-075)
- MIGRATE-071: Implement Statistics and Analytics
- MIGRATE-072: Implement Visualization (ASCII trees, Mermaid)
- MIGRATE-073: Implement Assignee Management
- MIGRATE-074: Implement Project Support
- MIGRATE-075: Implement Advanced Output Formats (JSON, etc.)

### Phase 4: Data Model Completion (MIGRATE-076 to MIGRATE-080)
- MIGRATE-076: Implement Additional Status Values (resolved, in_progress)
- MIGRATE-077: Implement Additional Priority Values (backlog)
- MIGRATE-078: Implement Additional Issue Types (story)
- MIGRATE-079: Implement Time Tracking (created, updated, closed)
- MIGRATE-080: Implement Hash-based ID System with Child IDs

### Phase 5: Database and Infrastructure (MIGRATE-081 to MIGRATE-085)
- MIGRATE-081: Implement Unit of Work Pattern
- MIGRATE-082: Implement Transaction Management
- MIGRATE-083: Implement Schema Migrations
- MIGRATE-084: Implement Database Indexing Strategy
- MIGRATE-085: Implement Data Integrity Constraints

---

## Summary

**Total Issues Required for 100% Feature Parity: 52 issues**
- Original: MIGRATE-034 through MIGRATE-040 (7 issues)
- Previously identified: MIGRATE-041 through MIGRATE-050 (10 issues)
- Now identified: MIGRATE-051 through MIGRATE-085 (35 issues)

**Coverage:**
- Current 7 issues: ~30%
- With MIGRATE-041-050: ~60%
- With MIGRATE-051-085: 100%

---

## Recommendation

**COMPLETED**: All 52 issues (MIGRATE-034 through MIGRATE-085) have been created and added to `.work/agent/issues/shortlist.md`.

The migration will preserve the feature set "as-is" with only daemon/MCP/factories excluded.

---

## Completion Status

**Total Issues Created: 52**
- Original: MIGRATE-034 through MIGRATE-040 (7 issues)
- Previously identified: MIGRATE-041 through MIGRATE-050 (10 issues)
- Now identified: MIGRATE-051 through MIGRATE-085 (35 issues)

**Coverage: 100% feature parity** (excluding daemon/MCP/factories)

### Files Updated
- `.work/agent/issues/shortlist.md` - Contains all 52 migration issues
- `.work/agent/notes/migrate-db-issues-investigation.md` - Complete investigation document
- `.work/agent/issues/medium.md` - Truncated (MIGRATE-034 through MIGRATE-040 removed)
