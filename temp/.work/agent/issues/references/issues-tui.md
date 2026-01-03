# Issues TUI (Text User Interface) Design

## Overview

A terminal-based interactive UI for managing issues across both the file-based issue tracker (`.work/agent/issues/`) and the database-backed system (`db_issues` module).

## Design Goals

1. **Fast filtering**: Narrow down issues by priority, status, type, labels, assignees
2. **Persistent selection**: Select issues across multiple filtering sessions
3. **Quick shortlist addition**: Add selected issues to `shortlist.md` in minimal keystrokes
4. **Dual-system support**: Work with both file-based and database issues
5. **Keyboard-driven**: Efficient navigation with vim-like keybindings
6. **Real-time preview**: See issue details without leaving the interface

## Technical Stack

- **Framework**: `textual` (modern Python TUI framework with async support)
- **Database**: SQLite (via existing db_issues adapters)
- **File parsing**: Frontmatter parsing for markdown files
- **Display**: Rich tables, syntax highlighting, color coding

## Screen Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ dot-work Issues TUI                            [Quit: q] [Help: ?]        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Filters: [All ▼] [Priorities: CRITICAL, HIGH] [Search: _____________]   │
│ Selected: 3 issues                                           [Clear: C]   │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┬───────────────────┤ │
│ │ Issues List (42 matching)                          │  Issue Preview     │ │
│ │                                                     │                   │ │
│ │ ● CR-001@a9f3c2 [P0]    Plaintext credentials     │  ID: CR-001@a9f3c2│ │
│ │   Security issue in container provision              │  Type: bug        │ │
│ │   Source: file-based                                │  Priority: CRITICAL│ │
│ │   Status: proposed                                 │  Status: proposed  │ │
│ │   Tags: security, container                         │                   │ │
│ │                                                     │  Title:           │ │
│ │   FEAT-012@b2c3d4 [P1]   Add TUI for issues       │  Plaintext git     │ │
│ │   Enhancement request                              │  credentials...    │ │
│ │   Source: db-issues                                │                   │ │
│ │   Status: in_progress                             │  Description:      │ │
│ │   Assignees: alice, bob                            │  Embedded bash...  │ │
│ │                                                     │                   │ │
│ │   BUG-008@e5f6a7 [P2]    Fix typo in error       │  Affected Files:   │ │
│ │   Type in CLI output message                        │  - core.py:591    │ │
│ │   Source: file-based                                │                   │ │
│ │   Status: proposed                                 │  References:      │ │
│ │                                                     │  - src/dot_w...  │ │
│ │ [Load more...]                                     │                   │ │
│ │                                                     │  Actions:         │ │
│ │                                                     │  [v] View details│ │
│ │                                                     │  [e] Edit        │ │
│ │                                                     │  [d] Delete      │ │
│ │                                                     │  [s] Select      │ │
│ └─────────────────────────────────────────────────────┴───────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ Status: Ready | Mode: Browse | System: file-based, db-issues              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. IssueListPanel (Left Panel)

**Purpose**: Display filtered list of issues

**Features**:
- Color-coded priority badges (CRITICAL=red, HIGH=yellow, MEDIUM=blue, LOW=green, BACKLOG=gray)
- Status icons (●=selected, ○=unselected)
- Source indicator (file-based vs db-issues)
- Truncated title and first line of description
- Keyboard navigation (j/k, Up/Down, PageUp/PageDown)
- Multi-select with Space or s key
- Infinite scroll with virtual scrolling for performance

**Data Structure**:
```python
@dataclass
class IssueSummary:
    id: str
    title: str
    description: str
    priority: IssuePriority
    status: IssueStatus
    issue_type: IssueType
    source: Literal["file", "db"]
    tags: list[str]
    assignees: list[str]
    created_at: datetime
    updated_at: datetime
    is_selected: bool
```

### 2. IssuePreviewPanel (Right Panel)

**Purpose**: Show details of currently selected issue

**Features**:
- Full metadata display
- Expandable sections (description, acceptance criteria, references)
- Syntax highlighting for code snippets
- Quick action buttons (View, Edit, Delete, Select)
- Markdown rendering for rich content
- Links clickable (open in browser/editor)

### 3. FilterPanel (Top Bar)

**Purpose**: Configure issue filters

**Controls**:
- **Priority Filter**: Multi-select dropdown (CRITICAL, HIGH, MEDIUM, LOW, BACKLOG)
- **Status Filter**: Multi-select dropdown (proposed, in_progress, blocked, completed, etc.)
- **Type Filter**: Multi-select dropdown (bug, feature, task, enhancement, etc.)
- **Source Filter**: Toggle between [file], [db], [both]
- **Search**: Text input with autocomplete
- **Tag Filter**: Type-ahead tag selection
- **Assignee Filter**: Multi-select from available assignees

**State Management**:
```python
@dataclass
class FilterState:
    priorities: set[IssuePriority]
    statuses: set[IssueStatus]
    types: set[IssueType]
    sources: set[Literal["file", "db"]]
    search_query: str
    tags: set[str]
    assignees: set[str]
    date_range: tuple[datetime, datetime] | None
```

### 4. SelectionManager

**Purpose**: Track selected issues across filtering sessions

**Features**:
- Persistent selection storage (saved to `.work/agent/issues/.selection.json`)
- Selection count badge
- Bulk actions on selected issues
- Clear all selections
- Export selections to shortlist.md
- Import selections from file

**Data Structure**:
```python
@dataclass
class SelectionState:
    selected_ids: set[str]
    last_updated: datetime
    source_file: str  # Path to selection file
```

## Key Workflows

### Workflow 1: Quick Priority Filter → Select → Add to Shortlist

```
1. User presses 'p' to open priority filter
2. Selects "CRITICAL" and "HIGH" (Ctrl+Space for multi-select)
3. Presses Enter to apply filter
4. Navigates to issues with 'j'/'k'
5. Presses 's' or Space to select issues (● appears)
6. Presses 'a' to add all selected to shortlist.md
7. Confirmation: "3 issues added to shortlist.md"
```

**Key Commands**:
- `p` - Open priority filter
- `Ctrl+Space` - Toggle multi-select
- `Enter` - Apply filter
- `s` or `Space` - Select/deselect issue
- `a` - Add selected to shortlist
- `Esc` - Close filter/clear selection

### Workflow 2: Create New Issue

```
1. User presses 'n' for new issue
2. Form overlay appears:
   ┌─────────────────────────────────────────────────┐
   │ Create New Issue                                │
   ├─────────────────────────────────────────────────┤
   │ Type: [bug ▼]  Priority: [MEDIUM ▼]         │
   │ Source: [db-issues ▼]                          │
   │                                                 │
   │ Title: ______________________________________  │
   │                                                 │
   │ Description:                                    │
   │ ┌─────────────────────────────────────────────┐ │
   │ │                                             │ │
   │ │                                             │ │
   │ │ (Markdown editor with live preview)          │ │
   │ └─────────────────────────────────────────────┘ │
   │                                                 │
   │ Tags: [Add...]                                │
   │ Assignees: [Add...]                            │
   │                                                 │
   │ [Save] [Cancel]                                │
   └─────────────────────────────────────────────────┘
3. User fills in fields with tab/enter navigation
4. Markdown editor supports live preview (Ctrl+P)
5. Presses 'Save' to create issue
6. Issue appears in list, cursor moves to it
```

**Features**:
- Type-ahead for existing tags
- Git-based user detection for assignees
- Auto-generate ID (TYPE-###@hash)
- Validation before save
- Support for frontmatter template from `new-issue.prompt.md`

### Workflow 3: Edit Existing Issue

```
1. User navigates to issue and presses 'e'
2. Edit form opens with current values
3. User modifies fields
4. On save, issue is updated in:
   - File: Updates the markdown file directly
   - DB: Uses IssueService.update_issue()
5. Preview panel reflects changes immediately
```

**Synchronization**:
- File-based issues: Parse frontmatter, update YAML fields
- DB issues: Use transaction-safe update via UnitOfWork
- Conflict detection: If both file and DB exist, warn and ask which to update

### Workflow 4: Bulk Actions on Selected Issues

```
1. User selects multiple issues (Ctrl+Space or 's' on each)
2. Presses 'b' to open bulk actions menu
3. Options:
   - [s] Set status...
   - [p] Set priority...
   - [a] Assign to...
   - [l] Add labels...
   - [x] Add to shortlist
   - [d] Delete (with confirmation)
   - [m] Merge into one issue...
4. User selects action and provides value
5. Progress bar shows bulk operation progress
6. Summary: "12 of 12 issues updated successfully"
```

**Bulk Operations**:
- Use existing `IssueService.bulk_update_status()`, `bulk_update_priority()`, `bulk_assign()`
- Parallel processing for performance
- Error handling: Continue on failure, report failures at end

### Workflow 5: Search and Filter Navigation

```
1. User presses '/' to open search
2. Types "security container"
3. Real-time filtering with debouncing (300ms)
4. Presses Tab to cycle through matches
5. Shift+Tab to cycle backwards
6. Esc to clear search

Or:
1. Press 'f' to open filter panel
2. Navigate filters with Tab/Shift+Tab
3. Use Space to toggle multi-select
4. Enter to apply all filters
5. 'r' to reset all filters
```

**Advanced Search**:
- FTS5 full-text search for DB issues
- Regex search for file-based issues
- Search in: title, description, tags, references
- Operator support: `priority:critical status:open tag:security`

## Integration with Existing Systems

### File-Based Issues (`.work/agent/issues/*.md`)

**Parsing**:
```python
class FileIssueParser:
    """Parse markdown files with YAML frontmatter."""

    def parse_file(self, path: Path) -> list[Issue]:
        """Parse issue file and return list of issues.

        Format:
        ---
        id: "TYPE-###@hash"
        title: "Title"
        ...
        ---

        ### Problem
        ...

        ### Acceptance Criteria
        ...
        """
        content = path.read_text()
        parts = re.split(r'(?m)^---\s*$', content)
        issues = []

        for i in range(1, len(parts), 2):
            frontmatter_text = parts[i]
            body_text = parts[i+1] if i+1 < len(parts) else ""

            frontmatter = yaml.safe_load(frontmatter_text)
            issue = Issue(
                id=frontmatter['id'],
                title=frontmatter['title'],
                description=self._extract_description(body_text),
                priority=self._parse_priority(frontmatter['priority']),
                status=self._parse_status(frontmatter['status']),
                type=self._parse_type(frontmatter['type']),
                tags=frontmatter.get('tags', []),
                created_at=datetime.fromisoformat(frontmatter['created']),
                source='file',
                source_file=str(path)
            )
            issues.append(issue)

        return issues
```

**Writing**:
- Preserve frontmatter format exactly
- Maintain order of existing fields
- Update timestamps on modification
- Keep markdown body formatting intact

### Database Issues (`db_issues` module)

**Integration Points**:
```python
class DatabaseIssueProvider:
    """Bridge between TUI and db_issues module."""

    def __init__(self):
        self.engine = create_db_engine(get_db_url())
        self.uow = UnitOfWork(self.engine)
        self.issue_service = IssueService(
            uow=self.uow,
            id_service=IdentifierService(),
            clock=SystemClock(),
            audit_log=AuditLog()
        )

    def list_issues(self, filters: FilterState) -> list[Issue]:
        """List issues with filters."""
        return self.issue_service.list_issues(
            priority=filters.priorities,
            status=filters.statuses,
            issue_type=filters.types,
            limit=1000  # TUI handles pagination
        )

    def search_issues(self, query: str) -> list[Issue]:
        """Full-text search."""
        search_service = SearchService(self.uow.session)
        results = search_service.search(query, limit=20)
        return [self.issue_service.get_issue(r.issue_id) for r in results]
```

### Shortlist Integration

**Adding to Shortlist**:
```python
class ShortlistManager:
    """Manage shortlist.md file."""

    def add_issues(self, issue_ids: list[str]) -> int:
        """Add issues to shortlist.md.

        Preserves existing content, appends new issues at the end.
        Uses issue format from new-issue.prompt.md.
        """
        shortlist_path = Path(".work/agent/issues/shortlist.md")
        content = shortlist_path.read_text()

        for issue_id in issue_ids:
            issue = self._get_issue(issue_id)
            markdown = self._issue_to_markdown(issue)
            content += f"\n\n{markdown}"

        shortlist_path.write_text(content)
        return len(issue_ids)

    def _issue_to_markdown(self, issue: Issue) -> str:
        """Convert issue to markdown format for shortlist."""
        return f"""---
id: "{issue.id}"
title: "{issue.title}"
description: "{issue.description[:100]}..."
created: {issue.created_at.strftime('%Y-%m-%d')}
section: "shortlist"
tags: {issue.tags}
type: {issue.type.value}
priority: {issue.priority.name.lower()}
status: {issue.status.value}
references: []
---

### Problem
{issue.description}

### Importance
Issue added to shortlist for prioritization.

### Acceptance Criteria
- [ ] Issue investigated
- [ ] Resolution proposed
"""
```

## Keyboard Shortcuts

### Global Shortcuts

| Key | Action | Mode |
|-----|--------|------|
| `q` | Quit | All |
| `?` | Show help | All |
| `Esc` | Cancel/Close dialog | All |
| `Ctrl+c` | Force quit | All |
| `Ctrl+r` | Refresh issue list | All |

### Navigation

| Key | Action | Mode |
|-----|--------|------|
| `j` / `↓` | Next issue | List |
| `k` / `↑` | Previous issue | List |
| `g` | Go to top | List |
| `G` | Go to bottom | List |
| `/` | Search | List |
| `n` | Next search match | List |
| `N` | Previous search match | List |
| `Tab` | Next panel | All |
| `Shift+Tab` | Previous panel | All |

### Filtering

| Key | Action | Mode |
|-----|--------|------|
| `f` | Open filter panel | All |
| `p` | Filter by priority | All |
| `s` | Filter by status | All |
| `t` | Filter by type | All |
| `r` | Reset filters | All |
| `Ctrl+Space` | Toggle multi-select | Filter |
| `Enter` | Apply filter | Filter |

### Selection

| Key | Action | Mode |
|-----|--------|------|
| `Space` / `s` | Toggle selection | List |
| `Ctrl+a` | Select all visible | List |
| `Ctrl+d` | Deselect all | List |
| `Ctrl+i` | Invert selection | List |
| `a` | Add selected to shortlist | List |
| `C` | Clear selections | List |
| `b` | Bulk actions | List |

### Issue Actions

| Key | Action | Mode |
|-----|--------|------|
| `Enter` | View details | List |
| `e` | Edit issue | List |
| `d` | Delete issue | List |
| `c` | Add comment | List |
| `l` | Manage labels | List |
| `v` | View in editor | List |
| `o` | Open references | List |

### Creation

| Key | Action | Mode |
|-----|--------|------|
| `n` | New issue | All |
| `Ctrl+n` | Quick new issue | All (skip prompts, defaults) |

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)

1. **Project Setup**
   - Create `src/dot_work/issues_tui/` module
   - Add dependencies: `textual`, `python-frontmatter`
   - Set up basic TUI app structure

2. **Data Models**
   - `IssueSummary`, `FilterState`, `SelectionState`
   - Unified issue model that works with both file and DB sources

3. **Issue Providers**
   - `FileIssueProvider` - Parse markdown files
   - `DatabaseIssueProvider` - Integrate with db_issues
   - `UnifiedIssueProvider` - Combine both sources

4. **Selection Manager**
   - Persistent selection storage
   - Load/save from `.selection.json`
   - Selection operations (add, remove, clear, bulk)

### Phase 2: UI Components (Week 2)

1. **IssueListPanel**
   - Virtual scrolling for performance
   - Selection indicators
   - Color coding
   - Search highlighting

2. **IssuePreviewPanel**
   - Markdown rendering
   - Metadata display
   - Action buttons
   - Expandable sections

3. **FilterPanel**
   - Multi-select dropdowns
   - Search with autocomplete
   - Filter state management
   - Real-time filtering

4. **Status Bar**
   - Selection count
   - Current filter summary
   - System status

### Phase 3: Workflows (Week 3)

1. **Create/Edit/Delete Issues**
   - Form overlay with validation
   - Markdown editor with live preview
   - Sync between file and DB sources

2. **Bulk Operations**
   - Bulk status/priority update
   - Bulk assignment
   - Bulk add to shortlist
   - Progress tracking

3. **Shortlist Integration**
   - Add selected to shortlist.md
   - Format according to new-issue.prompt.md
   - Preserve existing content

4. **Search**
   - FTS5 search for DB issues
   - Regex search for file issues
   - Result highlighting
   - Quick navigation

### Phase 4: Polish (Week 4)

1. **Performance**
   - Lazy loading for large issue lists
   - Caching for repeated queries
   - Debouncing for search/filter

2. **Testing**
   - Unit tests for providers
   - Integration tests for workflows
   - E2E tests with textual mock

3. **Documentation**
   - User guide
   - Key reference card
   - Troubleshooting guide

4. **CLI Integration**
   - Add `dot-work issues tui` command
   - Add `dot-work issues list` for basic view
   - Add `dot-work issues create` for CLI creation

## File Structure

```
src/dot_work/issues_tui/
├── __init__.py
├── app.py                 # Main TUI application
├── components/
│   ├── __init__.py
│   ├── issue_list.py      # IssueListPanel
│   ├── issue_preview.py   # IssuePreviewPanel
│   ├── filter_panel.py     # FilterPanel
│   └── status_bar.py      # Status bar
├── providers/
│   ├── __init__.py
│   ├── base.py            # Abstract IssueProvider
│   ├── file_provider.py    # FileIssueProvider
│   ├── db_provider.py     # DatabaseIssueProvider
│   └── unified_provider.py # UnifiedIssueProvider
├── models.py              # Data models
├── selection.py           # SelectionManager
├── shortlist.py           # ShortlistManager
├── workflows/
│   ├── __init__.py
│   ├── create_edit.py     # Create/edit workflows
│   ├── bulk_actions.py    # Bulk operations
│   └── shortlist.py       # Shortlist workflows
└── utils/
    ├── __init__.py
    ├── markdown.py         # Markdown rendering
    ├── colors.py          # Color schemes
    └── validators.py      # Input validation
```

## Configuration

**Config File**: `.work/issues-tui/config.yml`

```yaml
# UI Preferences
ui:
  theme: dark  # dark, light, solarized
  font_size: 14
  line_numbers: true
  syntax_highlighting: true

# Issue Display
display:
  max_title_length: 60
  max_description_length: 80
  show_created_date: true
  show_updated_date: false
  show_assignees: true

# Filtering
filters:
  default_priorities: [CRITICAL, HIGH, MEDIUM]
  default_status: []
  default_types: []
  include_backlog: false

# Selection
selection:
  auto_save: true
  max_selected: 100
  persist_across_sessions: true

# Shortlist
shortlist:
  format: full  # full, minimal, custom
  add_metadata: true
  preserve_order: true
```

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_file_provider.py
def test_parse_issue_frontmatter():
    provider = FileIssueProvider()
    issues = provider.parse_file(Path("fixtures/critical.md"))
    assert len(issues) > 0
    assert issues[0].id == "CR-001@a9f3c2"
    assert issues[0].priority == IssuePriority.CRITICAL

# tests/unit/test_db_provider.py
def test_list_issues_with_filters():
    provider = DatabaseIssueProvider()
    filters = FilterState(priorities={IssuePriority.CRITICAL})
    issues = provider.list_issues(filters)
    assert all(i.priority == IssuePriority.CRITICAL for i in issues)
```

### Integration Tests

```python
# tests/integration/test_shortlist_workflow.py
def test_add_issues_to_shortlist(tmp_path):
    shortlist_mgr = ShortlistManager()
    shortlist_mgr.shortlist_path = tmp_path / "shortlist.md"

    shortlist_mgr.add_issues(["CR-001@a9f3c2", "FEAT-012@b2c3d4"])

    content = shortlist_mgr.shortlist_path.read_text()
    assert "CR-001@a9f3c2" in content
    assert "FEAT-012@b2c3d4" in content
```

### E2E Tests

```python
# tests/e2e/test_tui_workflows.py
def test_filter_select_add_to_shortlist():
    app = IssuesTUIApp()
    async with app.run_test() as pilot:
        # Open priority filter
        await pilot.press("p")
        # Select CRITICAL
        await pilot.press("enter")
        # Navigate to first issue
        await pilot.press("s")  # Select
        await pilot.press("j")  # Next
        await pilot.press("s")  # Select
        # Add to shortlist
        await pilot.press("a")
        # Check confirmation
        assert "2 issues added to shortlist.md" in app.status_bar.text
```

## Performance Considerations

1. **Lazy Loading**: Load issues in chunks (50 at a time) for large repositories
2. **Virtual Scrolling**: Render only visible items in list
3. **Debouncing**: 300ms debounce for search/filter inputs
4. **Caching**: Cache parsed files, DB queries for 5 minutes
5. **Parallel Loading**: Parse files in parallel using `concurrent.futures`
6. **Indexed Search**: Use FTS5 for DB issues, build inverted index for files

## Security Considerations

1. **Input Validation**: Sanitize all user inputs, especially search queries
2. **Path Traversal**: Validate file paths when writing shortlist
3. **SQL Injection**: Use parameterized queries for DB operations
4. **Git Credentials**: Never log or display git tokens
5. **File Permissions**: Ensure proper permissions on selection files

## Future Enhancements

1. **Multi-Project Support**: Switch between different projects
2. **Issue Dependencies**: Visualize dependency graph
3. **Kanban Board**: Drag-and-drop status management
4. **Git Integration**: Create commits from issues, link issues to commits
5. **Collaboration**: Sync with external issue trackers (GitHub, Jira)
6. **Reports**: Generate issue statistics, burn-down charts
7. **Time Tracking**: Track time spent on issues
8. **Templates**: Save and reuse issue templates

## Migration Path

### From File-Based to Database

```python
class MigrationWizard:
    """Migrate file-based issues to database."""

    def migrate(self, dry_run: bool = True) -> MigrationResult:
        """Migrate all file-based issues to database.

        Args:
            dry_run: If True, simulate migration without writing

        Returns:
            MigrationResult with statistics
        """
        file_provider = FileIssueProvider()
        db_provider = DatabaseIssueProvider()

        issues = []
        for file_path in self._get_issue_files():
            file_issues = file_provider.parse_file(file_path)
            issues.extend(file_issues)

        result = MigrationResult(
            total=len(issues),
            migrated=0,
            failed=0,
            conflicts=0
        )

        for issue in issues:
            # Check for conflicts (ID already exists in DB)
            existing = db_provider.get_issue(issue.id)
            if existing:
                result.conflicts += 1
                continue

            # Create in DB
            if not dry_run:
                db_provider.create_issue(
                    title=issue.title,
                    description=issue.description,
                    priority=issue.priority,
                    type=issue.type,
                    custom_id=issue.id
                )
            result.migrated += 1

        return result
```

## Usage Examples

### CLI Entry Point

```bash
# Launch TUI
dot-work issues tui

# Open with specific filter
dot-work issues tui --filter priority=CRITICAL,HIGH

# Open specific issue
dot-work issues tui --issue CR-001@a9f3c2

# Quick list (non-interactive)
dot-work issues list --priority CRITICAL --status proposed
```

### Python API

```python
from dot_work.issues_tui import IssuesTUIApp

# Launch TUI programmatically
app = IssuesTUIApp()
app.run()

# With custom filters
app = IssuesTUIApp(
    initial_filters=FilterState(
        priorities={IssuePriority.CRITICAL}
    )
)
app.run()
```

## Summary

The Issues TUI provides a unified interface for managing both file-based and database-backed issues. Key features include:

- **Fast filtering** by priority, status, type, tags, assignees
- **Persistent selection** across filtering sessions
- **Quick shortlist addition** in minimal keystrokes
- **Keyboard-driven** workflow with vim-like bindings
- **Dual-system support** for file and DB issues
- **Real-time preview** without leaving the interface

The design leverages existing infrastructure (`db_issues` module, file-based tracker) while providing an efficient, developer-friendly interface for issue management.
