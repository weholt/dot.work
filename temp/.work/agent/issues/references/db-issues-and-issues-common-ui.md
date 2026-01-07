# Unified Issues Interface Design

## Executive Summary

This document proposes a unified, pluggable storage backend system for issue management in dot-work. The goal is to provide a consistent CLI interface for managing issues regardless of whether they're stored in plain markdown files (`.work/agent/issues/`) or in a SQLite database (`db_issues` module), with support for future API-based backends.

## Current State Analysis

### File-Based Issues (`.work/agent/issues/`)

**Structure:**
- Priority-based files: `critical.md`, `high.md`, `medium.md`, `low.md`, `backlog.md`
- Special files: `shortlist.md` (user priorities), `history.md` (completed issues)
- Each issue in YAML frontmatter with markdown body

**Issue Schema:**
```yaml
---
id: "TYPE-###@HASH"          # e.g., "BUG-003@a9f3c2"
title: "Short descriptive title"
description: "One-line summary"
created: YYYY-MM-DD
section: "affected-area"
tags: [tag1, tag2, tag3]
type: bug|enhancement|refactor|test|docs|security
priority: critical|high|medium|low
status: proposed|in-progress|blocked|completed
references:
  - path/to/file1.py
---

### Problem
...

### Affected Files
...

### Importance
...

### Proposed Solution
...

### Acceptance Criteria
...
```

**Strengths:**
- Human-readable, version-controlled with git
- Supports structured sections (Problem, Acceptance Criteria, etc.)
- No external dependencies
- Easy to edit manually

**Weaknesses:**
- No full-text search
- No efficient filtering by multiple criteria
- No atomic operations (file locking issues)
- No support for comments, dependencies, epics
- Slow for large numbers of issues

### Database Issues (`db_issues` module)

**Structure:**
- SQLite database at `.work/db-issues/issues.db`
- Domain entities: Issue, Comment, Dependency, Epic, Label, Project
- Repository pattern with Unit of Work
- 50+ CLI commands organized in subgroups

**Issue Schema:**
```python
@dataclass
class Issue:
    id: str
    project_id: str
    title: str
    description: str
    status: IssueStatus          # Enum
    priority: IssuePriority        # IntEnum (0-4)
    type: IssueType             # Enum
    assignees: list[str]
    epic_id: str | None
    labels: list[str]
    blocked_reason: str | None
    source_url: str | None
    references: list[str]
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    deleted_at: datetime | None
```

**Strengths:**
- Efficient querying with indexes
- Full-text search (FTS5)
- Atomic transactions
- Rich relationships (comments, dependencies, epics, labels)
- 50+ CLI commands
- Bulk operations support

**Weaknesses:**
- Requires database knowledge to inspect
- Not as immediately human-readable
- Separate from file-based workflow
- No markdown body sections support

## Design Goals

1. **Unified CLI**: Single command interface works with any backend
2. **Pluggable Backends**: Easy to add File, Database, API storage options
3. **Common Prompts**: Use plain prompting for file-based workflows
4. **Bidirectional Sync**: Import/export between any backends
5. **Backward Compatible**: Existing file-based workflow still works
6. **Feature Parity**: Each backend supports core features
7. **Future-Proof**: Easy to add API backend (GitHub, Jira, etc.)

## Architecture

### Layered Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLI Layer                              │
│            (Typer commands, rich output)                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                Service Layer                             │
│        (Business logic, operations, workflows)               │
│  - IssueService                                         │
│  - SearchService                                       │
│  - ImportExportService                                  │
│  - MigrationService                                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│          Backend Abstraction Layer                       │
│         (Repository interfaces, protocols)                   │
│  - IssueRepository Protocol                               │
│  - CommentRepository Protocol                             │
│  - SearchRepository Protocol                              │
└──────┬────────────────────┬────────────────────┬────────┘
       │                    │                     │
┌──────▼────────┐   ┌─────▼─────────────┐   ┌──▼──────────┐
│ FileBackend   │   │ DatabaseBackend    │   │ APIBackend   │
│              │   │                  │   │             │
│ - Markdown   │   │ - SQLite         │   │ - REST      │
│ - YAML       │   │ - PostgreSQL     │   │ - GraphQL   │
│ - Frontmatter│   │ - MySQL          │   │ - GitHub    │
└──────────────┘   └──────────────────┘   └─────────────┘
```

## Backend Abstraction

### Protocols (Interfaces)

```python
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable
from dataclasses import dataclass
from datetime import datetime

@runtime_checkable
class IssueRepository(Protocol):
    """Protocol for issue storage backends."""

    @abstractmethod
    def get(self, issue_id: str) -> Issue | None:
        """Get issue by ID."""
        ...

    @abstractmethod
    def save(self, issue: Issue) -> Issue:
        """Save or update issue."""
        ...

    @abstractmethod
    def delete(self, issue_id: str) -> bool:
        """Delete issue (soft delete preferred)."""
        ...

    @abstractmethod
    def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: IssueFilters | None = None
    ) -> list[Issue]:
        """List issues with optional filters."""
        ...

    @abstractmethod
    def count(self, filters: IssueFilters | None = None) -> int:
        """Count issues matching filters."""
        ...

@runtime_checkable
class SearchRepository(Protocol):
    """Protocol for search operations."""

    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 20,
        include_closed: bool = False
    ) -> list[SearchResult]:
        """Full-text search."""
        ...

@runtime_checkable
class CommentRepository(Protocol):
    """Protocol for comment storage."""

    @abstractmethod
    def list_by_issue(self, issue_id: str) -> list[Comment]:
        """List comments for issue."""
        ...

    @abstractmethod
    def add(self, comment: Comment) -> Comment:
        """Add comment to issue."""
        ...

@runtime_checkable
class DependencyRepository(Protocol):
    """Protocol for dependency storage."""

    @abstractmethod
    def get_blockers(self, issue_id: str) -> list[str]:
        """Get issues blocking this issue."""
        ...

    @abstractmethod
    def get_blocked_by(self, issue_id: str) -> list[str]:
        """Get issues blocked by this issue."""
        ...
```

### Filter Models

```python
@dataclass
class IssueFilters:
    """Unified filter model for all backends."""

    priority: set[IssuePriority] | None = None
    status: set[IssueStatus] | None = None
    type: set[IssueType] | None = None
    assignees: set[str] | None = None
    labels: set[str] | None = None
    epic_id: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    updated_after: datetime | None = None
    updated_before: datetime | None = None
    include_deleted: bool = False
    include_backlog: bool = True
```

## Backend Implementations

### 1. FileBackend

```python
class FileBackend:
    """File-based issue storage backend.

    Stores issues in markdown files with YAML frontmatter.
    Maintains priority-based file structure.
    """

    def __init__(self, base_path: Path = Path(".work/agent/issues")):
        self.base_path = base_path
        self.files = {
            IssuePriority.CRITICAL: base_path / "critical.md",
            IssuePriority.HIGH: base_path / "high.md",
            IssuePriority.MEDIUM: base_path / "medium.md",
            IssuePriority.LOW: base_path / "low.md",
            IssuePriority.BACKLOG: base_path / "backlog.md",
        }
        self.shortlist_path = base_path / "shortlist.md"
        self.history_path = base_path / "history.md"

    def get(self, issue_id: str) -> Issue | None:
        """Parse all files to find issue by ID."""
        for file_path in self.files.values():
            issues = self._parse_file(file_path)
            for issue in issues:
                if issue.id == issue_id:
                    return issue
        return None

    def save(self, issue: Issue) -> Issue:
        """Save issue to appropriate priority file.

        Uses issue.priority to determine file.
        Updates existing issue or appends new one.
        """
        file_path = self.files[issue.priority]
        content = file_path.read_text()
        issues = self._parse_file(file_path)

        # Update existing or add new
        existing_idx = next(
            (i for i, iss in enumerate(issues) if iss.id == issue.id),
            None
        )
        if existing_idx is not None:
            issues[existing_idx] = issue
        else:
            issues.append(issue)

        # Write back to file
        markdown = self._issues_to_markdown(issues)
        file_path.write_text(markdown)
        return issue

    def _parse_file(self, file_path: Path) -> list[Issue]:
        """Parse markdown file with frontmatter."""
        import frontmatter
        import re

        content = file_path.read_text()
        # Split by issue delimiter
        parts = re.split(r'(?m)^---\s*$', content)
        issues = []

        for i in range(1, len(parts), 2):
            frontmatter_text = parts[i]
            body_text = parts[i+1] if i+1 < len(parts) else ""

            fm = frontmatter.loads(frontmatter_text)

            # Map to unified Issue model
            issue = Issue(
                id=fm.get('id', ''),
                title=fm.get('title', ''),
                description=self._extract_description(body_text),
                priority=self._map_priority(fm.get('priority', 'medium')),
                status=self._map_status(fm.get('status', 'proposed')),
                type=self._map_type(fm.get('type', 'task')),
                labels=fm.get('tags', []),
                assignees=[],
                created_at=datetime.fromisoformat(fm['created']) if 'created' in fm else datetime.now(),
                updated_at=datetime.now(),
                project_id='default',
            )
            issues.append(issue)

        return issues

    def _extract_description(self, body: str) -> str:
        """Extract description from markdown body sections."""
        # Look for Problem section
        import re
        match = re.search(r'### Problem\s*\n(.*?)(?=###|$)', body, re.DOTALL)
        if match:
            return match.group(1).strip()
        return body.strip()[:500]

    def _map_priority(self, priority: str) -> IssuePriority:
        """Map string priority to enum."""
        return {
            'critical': IssuePriority.CRITICAL,
            'high': IssuePriority.HIGH,
            'medium': IssuePriority.MEDIUM,
            'low': IssuePriority.LOW,
        }.get(priority.lower(), IssuePriority.MEDIUM)

    def _map_status(self, status: str) -> IssueStatus:
        """Map string status to enum."""
        return {
            'proposed': IssueStatus.PROPOSED,
            'in-progress': IssueStatus.IN_PROGRESS,
            'blocked': IssueStatus.BLOCKED,
            'completed': IssueStatus.COMPLETED,
        }.get(status.lower(), IssueStatus.PROPOSED)

    def _map_type(self, type_: str) -> IssueType:
        """Map string type to enum."""
        return {
            'bug': IssueType.BUG,
            'feature': IssueType.FEATURE,
            'enhancement': IssueType.ENHANCEMENT,
            'refactor': IssueType.REFACTOR,
            'test': IssueType.TEST,
            'docs': IssueType.DOCS,
            'security': IssueType.SECURITY,
        }.get(type_.lower(), IssueType.TASK)
```

### 2. DatabaseBackend

```python
class DatabaseBackend:
    """Database-backed issue storage.

    Wraps existing db_issues module with unified interface.
    """

    def __init__(self, db_url: str | None = None):
        from dot_work.db_issues.adapters import create_db_engine, UnitOfWork

        self.engine = create_db_engine(db_url)
        self.uow = UnitOfWork(self.engine)

    def get(self, issue_id: str) -> Issue | None:
        """Delegate to IssueRepository."""
        return self.uow.issues.get(issue_id)

    def save(self, issue: Issue) -> Issue:
        """Delegate to IssueRepository."""
        return self.uow.issues.save(issue)

    def delete(self, issue_id: str) -> bool:
        """Delegate to IssueRepository."""
        return self.uow.issues.delete(issue_id)

    def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: IssueFilters | None = None
    ) -> list[Issue]:
        """List issues with optional filters."""
        # Map unified filters to repository methods
        if filters and filters.status and len(filters.status) == 1:
            status = next(iter(filters.status))
            return self.uow.issues.list_by_status(status, limit, offset)
        elif filters and filters.priority and len(filters.priority) == 1:
            priority = next(iter(filters.priority))
            return self.uow.issues.list_by_priority(priority, limit, offset)
        elif filters and filters.assignees:
            assignee = next(iter(filters.assignees))
            return self.uow.issues.list_by_assignee(assignee, limit, offset)
        else:
            return self.uow.issues.list_all(limit, offset)

    def count(self, filters: IssueFilters | None = None) -> int:
        """Count issues matching filters."""
        issues = self.list_all(limit=100000, filters=filters)
        return len(issues)
```

### 3. APIBackend (Future)

```python
class APIBackend:
    """API-based issue storage (GitHub, Jira, etc.).

    Design allows adding new API providers without changing core code.
    """

    def __init__(self, api_url: str, auth_token: str):
        self.api_url = api_url
        self.auth_token = auth_token
        self._client = self._create_client()

    def _create_client(self):
        """Create API client based on provider."""
        # GitHub client, Jira client, etc.
        pass

    def get(self, issue_id: str) -> Issue | None:
        """Fetch issue from API."""
        response = self._client.get_issue(issue_id)
        return self._api_to_issue(response)

    def save(self, issue: Issue) -> Issue:
        """Create or update issue via API."""
        if self._issue_exists(issue.id):
            response = self._client.update_issue(issue.id, self._issue_to_api(issue))
        else:
            response = self._client.create_issue(self._issue_to_api(issue))
        return self._api_to_issue(response)

    def _api_to_issue(self, api_response) -> Issue:
        """Convert API response to unified Issue model."""
        # Provider-specific mapping
        pass

    def _issue_to_api(self, issue: Issue) -> dict:
        """Convert unified Issue to API payload."""
        # Provider-specific mapping
        pass
```

## Service Layer

### UnifiedIssueService

```python
class UnifiedIssueService:
    """Unified issue service that works with any backend."""

    def __init__(
        self,
        backend: IssueRepository,
        id_service: IdentifierService,
        clock: Clock,
        audit_log: AuditLog | None = None
    ):
        self.backend = backend
        self.id_service = id_service
        self.clock = clock
        self.audit_log = audit_log or AuditLog()

    def create_issue(
        self,
        title: str,
        description: str = "",
        priority: IssuePriority = IssuePriority.MEDIUM,
        issue_type: IssueType = IssueType.TASK,
        assignees: list[str] | None = None,
        epic_id: str | None = None,
        labels: list[str] | None = None,
        project_id: str = "default",
        custom_id: str | None = None
    ) -> Issue:
        """Create issue in configured backend.

        Works identically for File, Database, or API backends.
        """
        issue = Issue(
            id=custom_id or self.id_service.generate("issue"),
            project_id=project_id,
            title=title,
            description=description,
            status=IssueStatus.PROPOSED,
            priority=priority,
            type=issue_type,
            assignees=assignees or [],
            epic_id=epic_id,
            labels=labels or [],
            created_at=self.clock.now(),
            updated_at=self.clock.now(),
        )

        saved_issue = self.backend.save(issue)
        self.audit_log.log(
            action="create",
            entity_type="issue",
            entity_id=saved_issue.id,
            user=None,  # TODO: from git config
            timestamp_field=self.clock.now,
            details=f"Created issue: {saved_issue.title}"
        )
        return saved_issue

    def update_issue(
        self,
        issue_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: IssuePriority | None = None,
        status: IssueStatus | None = None,
        type: IssueType | None = None,
        assignees: list[str] | None = None,
        labels: list[str] | None = None
    ) -> Issue | None:
        """Update issue fields.

        Backend-agnostic update logic.
        """
        issue = self.backend.get(issue_id)
        if not issue:
            return None

        if title is not None:
            issue.title = title
        if description is not None:
            issue.description = description
        if priority is not None:
            issue.priority = priority
        if status is not None:
            if not issue.status.can_transition_to(status):
                raise InvalidTransitionError(
                    f"Cannot transition from {issue.status.value} to {status.value}",
                    entity_id=issue.id,
                    current_state=issue.status.value,
                    target_state=status.value,
                )
            issue.status = status
        if type is not None:
            issue.type = type
        if assignees is not None:
            issue.assignees = assignees
        if labels is not None:
            issue.labels = labels

        issue.updated_at = self.clock.now()
        return self.backend.save(issue)

    def list_issues(
        self,
        priority: IssuePriority | None = None,
        status: IssueStatus | None = None,
        type: IssueType | None = None,
        assignee: str | None = None,
        epic_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
        exclude_backlog: bool = True
    ) -> list[Issue]:
        """List issues with optional filtering.

        Transforms filters to IssueFilters and delegates to backend.
        """
        filters = IssueFilters()
        if priority:
            filters.priority = {priority}
        if status:
            filters.status = {status}
        if type:
            filters.type = {type}
        if assignee:
            filters.assignees = {assignee}
        if epic_id:
            filters.epic_id = epic_id
        filters.include_backlog = not exclude_backlog

        return self.backend.list_all(limit=limit, offset=offset, filters=filters)
```

### UnifiedSearchService

```python
class UnifiedSearchService:
    """Unified search service with backend detection."""

    def __init__(self, backend: IssueRepository | SearchRepository):
        self.backend = backend
        # Check if backend supports search protocol
        self._has_search = isinstance(backend, SearchRepository)

    def search(
        self,
        query: str,
        limit: int = 20,
        include_closed: bool = False
    ) -> list[SearchResult]:
        """Search issues.

        For DatabaseBackend: Uses FTS5 (fast, accurate)
        For FileBackend: Uses grep/regex (slower, but works)
        For APIBackend: Uses API search
        """
        if self._has_search:
            # Backend supports search protocol
            return self.backend.search(query, limit, include_closed)
        else:
            # Fallback: list and filter
            issues = self.backend.list_all(limit=100000)
            return self._search_issues_in_memory(issues, query, limit)

    def _search_issues_in_memory(
        self,
        issues: list[Issue],
        query: str,
        limit: int
    ) -> list[SearchResult]:
        """Fallback search for backends without search protocol."""
        import re
        from dataclasses import dataclass

        @dataclass
        class SearchResult:
            issue_id: str
            rank: float
            snippet: str

        results = []
        query_lower = query.lower()
        words = query_lower.split()

        for issue in issues:
            score = 0.0
            title_lower = issue.title.lower()
            desc_lower = issue.description.lower()

            # Simple BM25-like scoring
            for word in words:
                if word in title_lower:
                    score += 2.0
                if word in desc_lower:
                    score += 1.0

            if score > 0:
                # Generate snippet
                snippet = self._generate_snippet(issue, query)
                results.append(
                    SearchResult(issue_id=issue.id, rank=score, snippet=snippet)
                )

        # Sort by rank and limit
        results.sort(key=lambda r: r.rank, reverse=True)
        return results[:limit]

    def _generate_snippet(self, issue: Issue, query: str) -> str:
        """Generate search snippet."""
        # Find query in description
        import re
        match = re.search(f'({re.escape(query)})', issue.description, re.IGNORECASE)
        if match:
            # Return context around match
            start = max(0, match.start() - 20)
            end = min(len(issue.description), match.end() + 20)
            return issue.description[start:end]
        return issue.title[:100]
```

## CLI Design

### Unified CLI Entry Point

```bash
# Main issue command
dot-work issues <command> [options]

# Backend selection (via config or flag)
dot-work issues --backend file <command>
dot-work issues --backend db <command>
dot-work issues --backend api <command>
```

### Configuration

**File**: `.work/issues-config.yml`

```yaml
# Storage backend configuration
backend:
  # Which backend to use: file, database, api
  type: file  # file | database | api

  # Backend-specific settings
  file:
    base_path: ".work/agent/issues"
  database:
    db_url: "sqlite:///.work/db-issues.db"
  api:
    url: "https://api.github.com"
    token: "${GITHUB_TOKEN}"  # Use env var

# CLI preferences
ui:
  default_format: table  # table | json | yaml
  default_sort: priority
  show_metadata: true

# Search settings
search:
  backend_specific: true  # Use native search if available
  include_closed: false
```

### CLI Commands

```bash
# Issue CRUD
dot-work issues create "Fix bug in authentication"
dot-work issues create "Add new feature" \
  --type feature \
  --priority high \
  --tags feature,api \
  --description "Detailed description..."

dot-work issues list --priority critical,high --status proposed
dot-work issues show ISSUE-001@abc123
dot-work issues edit ISSUE-001@abc123 --status in-progress
dot-work issues delete ISSUE-001@abc123

# Filtering
dot-work issues list --type bug --assignee alice
dot-work issues list --tag security,performance
dot-work issues list --created-after 2024-01-01

# Search
dot-work issues search "authentication error"
dot-work issues search "api timeout" --priority high

# Bulk operations
dot-work issues bulk set-status completed \
  --priority low \
  --created-before 2024-01-01

# Import/Export
dot-work issues export --format jsonl --output issues.jsonl
dot-work issues export --format markdown --output issues.md
dot-work issues import --format jsonl --input issues.jsonl

# Sync between backends
dot-work issues sync --from file --to database
dot-work issues sync --from database --to api

# Work with shortlist (file-backend only)
dot-work issues shortlist add ISSUE-001@abc123
dot-work issues shortlist remove ISSUE-001@abc123
dot-work issues shortlist show
```

### Prompt Integration

**For file-based workflow**, use prompts:

```bash
# Create issue with prompting
dot-work issues create --prompt

# Opens interactive prompt that:
# 1. Asks for title, description, type, priority
# 2. Suggests tags based on existing issues
# 3. Generates ID using TYPE-###@HASH format
# 4. Writes to appropriate .md file (critical.md, high.md, etc.)
# 5. Shows created issue summary
```

**Prompt template** (reuses `new-issue.prompt.md`):

```
Using new-issue.prompt.md for issue creation:
- Generates proper ID format (TYPE-###@HASH)
- Validates required fields
- Maps priority to correct file location
- Creates markdown body with sections
```

## Import/Export Service

### Bidirectional Sync

```python
class ImportExportService:
    """Import/export issues between backends."""

    def __init__(
        self,
        source_backend: IssueRepository,
        target_backend: IssueRepository,
        conflict_resolution: str = "skip"
    ):
        self.source = source_backend
        self.target = target_backend
        self.conflict_resolution = conflict_resolution
        # Options: skip, overwrite, merge

    def sync_all(
        self,
        dry_run: bool = False
    ) -> SyncResult:
        """Sync all issues from source to target.

        Handles:
        - New issues (import)
        - Existing issues (skip/update based on conflict_resolution)
        - ID conflicts (preserve source)
        """
        source_issues = self.source.list_all(limit=100000)
        sync_result = SyncResult(
            imported=0,
            updated=0,
            skipped=0,
            conflicts=0
        )

        for issue in source_issues:
            existing = self.target.get(issue.id)

            if existing is None:
                # New issue
                if not dry_run:
                    self.target.save(issue)
                sync_result.imported += 1

            elif self.conflict_resolution == "skip":
                sync_result.skipped += 1

            elif self.conflict_resolution == "overwrite":
                if not dry_run:
                    self.target.save(issue)
                sync_result.updated += 1

            elif self.conflict_resolution == "merge":
                merged = self._merge_issues(existing, issue)
                if not dry_run:
                    self.target.save(merged)
                sync_result.updated += 1

            else:
                sync_result.conflicts += 1

        return sync_result

    def _merge_issues(self, existing: Issue, incoming: Issue) -> Issue:
        """Merge two issues.

        Strategy:
        - Keep most recent timestamps
        - Merge labels (union)
        - Merge assignees (union)
        - Concatenate descriptions
        """
        # Take whichever has more recent update
        if existing.updated_at > incoming.updated_at:
            base = existing
            other = incoming
        else:
            base = incoming
            other = existing

        # Merge labels
        merged_labels = list(set(base.labels) | set(other.labels))

        # Merge assignees
        merged_assignees = list(set(base.assignees) | set(other.assignees))

        # Merge descriptions
        merged_description = base.description
        if other.description not in merged_description:
            merged_description += f"\n\n---\n\n{other.description}"

        return Issue(
            id=base.id,
            title=base.title,  # Keep base title
            description=merged_description,
            status=base.status,  # Keep base status
            priority=base.priority,  # Keep base priority
            type=base.type,
            assignees=merged_assignees,
            labels=merged_labels,
            epic_id=base.epic_id or other.epic_id,
            created_at=base.created_at,
            updated_at=self.clock.now(),
            project_id=base.project_id,
        )

    def export_to_markdown(
        self,
        output_path: Path,
        group_by_priority: bool = True
    ) -> ExportResult:
        """Export issues to markdown files.

        Can export to single file or priority-grouped files.
        """
        issues = self.source.list_all(limit=100000)

        if group_by_priority:
            # Create priority files
            for priority in IssuePriority:
                priority_issues = [
                    i for i in issues if i.priority == priority
                ]
                if priority_issues:
                    output_file = output_path / f"{priority.value}.md"
                    self._write_markdown_file(output_file, priority_issues)
        else:
            # Single file export
            self._write_markdown_file(output_path, issues)

        return ExportResult(total=len(issues), files_written=len(list(output_path.glob("*.md"))))

    def import_from_markdown(
        self,
        input_path: Path,
        merge_strategy: str = "skip"
    ) -> ImportResult:
        """Import issues from markdown files.

        Supports both single-file and multi-file formats.
        """
        if input_path.is_file():
            files = [input_path]
        else:
            files = list(input_path.glob("*.md"))

        imported = 0
        failed = 0

        for file_path in files:
            try:
                # Use FileBackend to parse
                file_backend = FileBackend(base_path=file_path.parent)
                issues = file_backend._parse_file(file_path)

                for issue in issues:
                    # Check for conflicts
                    existing = self.target.get(issue.id)
                    if existing:
                        if merge_strategy == "merge":
                            merged = self._merge_issues(existing, issue)
                            self.target.save(merged)
                            imported += 1
                        else:
                            failed += 1
                    else:
                        self.target.save(issue)
                        imported += 1

            except Exception as e:
                logger.error(f"Failed to import {file_path}: {e}")
                failed += 1

        return ImportResult(imported=imported, failed=failed)
```

## Migration Path

### Phase 1: Abstraction Layer (Week 1)

1. Define protocol interfaces for repositories
2. Implement DatabaseBackend wrapper for existing db_issues
3. Implement FileBackend for markdown files
4. Create UnifiedIssueService

**Deliverables:**
- `src/dot_work/issues/unified/protocols.py`
- `src/dot_work/issues/unified/file_backend.py`
- `src/dot_work/issues/unified/database_backend.py`
- `src/dot_work/issues/unified/service.py`

### Phase 2: Unified CLI (Week 2)

1. Create unified CLI command group
2. Implement CRUD operations
3. Add filtering and search
4. Add import/export commands
5. Maintain backward compatibility with existing CLI

**Deliverables:**
- `src/dot_work/issues/cli.py` (new unified CLI)
- Update `src/dot_work/cli.py` to add unified issues command
- Keep `src/dot_work/db_issues/cli.py` for backward compatibility

### Phase 3: Import/Export (Week 3)

1. Implement ImportExportService
2. Add sync commands
3. Add markdown export
4. Add markdown import
5. Handle conflicts and merging

**Deliverables:**
- `src/dot_work/issues/unified/import_export.py`
- CLI commands: `dot-work issues sync`, `export`, `import`

### Phase 4: API Backend (Week 4)

1. Design API backend interface
2. Implement GitHub API backend
3. Add auth and token management
4. Test sync with GitHub issues

**Deliverables:**
- `src/dot_work/issues/unified/api_backend.py`
- GitHub provider implementation
- Documentation for adding new API providers

### Phase 5: Prompt Integration (Week 5)

1. Integrate with `new-issue.prompt.md`
2. Add interactive prompting
3. Add file-based workflow support
4. Add shortlist integration

**Deliverables:**
- Interactive prompt system
- Prompt templates for issue creation
- Shortlist management commands

## File Structure

```
src/dot_work/issues/
├── __init__.py
├── unified/
│   ├── __init__.py
│   ├── protocols.py              # Repository protocols
│   ├── models.py                # Unified models (IssueFilters, etc.)
│   ├── file_backend.py          # FileBackend implementation
│   ├── database_backend.py      # DatabaseBackend wrapper
│   ├── api_backend.py           # APIBackend interface
│   ├── service.py               # UnifiedIssueService
│   ├── search.py                # UnifiedSearchService
│   └── import_export.py         # Import/Export service
├── providers/
│   ├── github.py               # GitHub API provider
│   ├── jira.py                 # Jira API provider (future)
│   └── gitlab.py               # GitLab API provider (future)
└── cli.py                       # Unified CLI

# Existing modules (unchanged)
src/dot_work/db_issues/           # Database implementation
.work/agent/issues/               # File-based storage
```

## Configuration Management

### Backend Detection

```python
def detect_backend() -> str:
    """Auto-detect backend based on available data.

    Priority:
    1. Config file explicit setting
    2. Database file exists -> database
    3. Issue files exist -> file
    4. Default -> file
    """
    config_path = Path(".work/issues-config.yml")
    if config_path.exists():
        config = yaml.safe_load(config_path.read_text())
        backend_type = config.get('backend', {}).get('type')
        if backend_type:
            return backend_type

    # Auto-detect
    db_path = Path(".work/db-issues/issues.db")
    if db_path.exists():
        return "database"

    issues_path = Path(".work/agent/issues/critical.md")
    if issues_path.exists():
        return "file"

    # Default
    return "file"


def create_backend(backend_type: str | None = None) -> IssueRepository:
    """Factory function to create backend instance.

    Args:
        backend_type: Explicit backend type, or None for auto-detect

    Returns:
        Configured backend instance
    """
    if backend_type is None:
        backend_type = detect_backend()

    if backend_type == "database":
        return DatabaseBackend()
    elif backend_type == "file":
        return FileBackend()
    elif backend_type == "api":
        config = load_config()
        return APIBackend(
            api_url=config['backend']['api']['url'],
            auth_token=os.path.expandvars(config['backend']['api']['token'])
        )
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")
```

## Testing Strategy

### Unit Tests

```python
# tests/unit/issues/test_file_backend.py
def test_parse_markdown_with_frontmatter():
    backend = FileBackend()
    issues = backend._parse_file(Path("fixtures/critical.md"))
    assert len(issues) > 0
    assert issues[0].id == "CR-001@abc123"
    assert issues[0].priority == IssuePriority.CRITICAL

def test_save_creates_new_issue():
    backend = FileBackend(tmp_path)
    issue = Issue(id="TEST-001", title="Test", priority=IssuePriority.HIGH)
    saved = backend.save(issue)
    assert saved.id == "TEST-001"
    content = (tmp_path / "high.md").read_text()
    assert "TEST-001" in content

# tests/unit/issues/test_database_backend.py
def test_backend_wraps_db_issues():
    backend = DatabaseBackend(db_url="sqlite:///:memory:")
    service = UnifiedIssueService(backend=backend, ...)
    issue = service.create_issue(title="Test")
    assert issue.id is not None
    retrieved = backend.get(issue.id)
    assert retrieved.title == "Test"
```

### Integration Tests

```python
# tests/integration/test_sync_backends.py
def test_sync_from_file_to_database():
    file_backend = FileBackend(Path("fixtures/issues"))
    db_backend = DatabaseBackend(db_url="sqlite:///:memory:")

    sync_service = ImportExportService(
        source_backend=file_backend,
        target_backend=db_backend,
        conflict_resolution="skip"
    )

    result = sync_service.sync_all()
    assert result.imported > 0
    assert result.conflicts == 0

    # Verify issues in database
    db_issues = db_backend.list_all(limit=1000)
    assert len(db_issues) == result.imported
```

## Backward Compatibility

### Existing CLI Commands

Keep all existing `dot-work db-issues` commands for backward compatibility:

```bash
# Still works
dot-work db-issues create "Fix bug"
dot-work db-issues list
dot-work db-issues show ISSUE-001

# New unified interface
dot-work issues create "Fix bug" --backend database
dot-work issues list --backend database
dot-work issues show ISSUE-001 --backend database
```

### File-Based Workflow

Maintain existing prompt-based workflow:

```bash
# Agent creates issues using new-issue.prompt.md
# Still works exactly as before
# Issues written to .work/agent/issues/*.md

# New: Can sync to database if desired
dot-work issues sync --from file --to database
```

## Future Extensibility

### Adding New Backends

To add a new backend (e.g., Jira):

1. Implement protocols:
```python
class JiraBackend:
    def get(self, issue_id: str) -> Issue | None:
        # Fetch from Jira API
        ...

    def save(self, issue: Issue) -> Issue:
        # Create/update in Jira
        ...
```

2. Register in config:
```yaml
backend:
  type: jira
  jira:
    url: "https://company.atlassian.net"
    token: "${JIRA_TOKEN}"
    project: "PROJ"
```

3. CLI works automatically:
```bash
dot-work issues create "New issue"  # Uses Jira backend
dot-work issues list                 # Lists from Jira
dot-work issues sync --from file --to jira  # Sync to Jira
```

### Adding New API Providers

```python
# src/dot_work/issues/providers/gitlab.py
class GitLabProvider(APIBackend):
    """GitLab API provider."""

    def _create_client(self):
        from gitlab import Gitlab
        return Gitlab(self.auth_token, url=self.api_url)

    def _api_to_issue(self, api_response) -> Issue:
        # Map GitLab issue format to unified Issue
        return Issue(
            id=f"GL-{api_response.iid}",
            title=api_response.title,
            description=api_response.description,
            ...
        )
```

## Benefits

1. **Flexibility**: Switch storage backends without changing workflow
2. **Migration Path**: Gradual migration from files to database
3. **API Integration**: Future support for GitHub, Jira, GitLab
4. **Consistent UX**: Same commands work everywhere
5. **Backward Compatible**: Existing workflows continue to work
6. **Testable**: Protocol-based design enables easy testing
7. **Scalable**: Database for large repos, files for small ones

## Risks and Mitigations

### Risk: Data Loss During Sync

**Mitigation**:
- Always dry-run first (`--dry-run`)
- Conflict detection and resolution strategies
- Backup before sync (`--backup` flag)
- Transactional imports (all or nothing)

### Risk: Schema Mismatch

**Mitigation**:
- Unified Issue model with flexible fields
- Lossless conversion where possible
- Warnings for unsupported features
- Manual review prompts for conflicts

### Risk: Performance with FileBackend

**Mitigation**:
- Lazy loading and caching
- Recommend database for large repos (>1000 issues)
- Index files for faster lookups
- Background sync with API backends

## Summary

This design provides:

1. **Unified CLI**: Single interface for all operations
2. **Pluggable Backends**: File, Database, API with protocol-based design
3. **Import/Export**: Bidirectional sync between any backends
4. **Backward Compatible**: Existing workflows preserved
5. **Future-Proof**: Easy to add new backends and providers

The architecture enables gradual adoption:
- Start with file-based (existing)
- Add database for advanced features (FTS5, relationships)
- Sync between backends as needed
- Add API backends for external integrations

All while maintaining the prompt-based workflow and supporting the full feature set of the existing db_issues module.
