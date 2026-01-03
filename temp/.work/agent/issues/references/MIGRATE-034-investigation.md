# MIGRATE-034 Investigation: Create db-issues module structure

**Issue:** MIGRATE-034@d8e9f0 – Create db-issues module structure in dot-work
**Started:** 2024-12-23T09:35:00Z
**Phase:** Investigation

## Goal

Create `src/dot_work/db_issues/` module with consolidated structure from:
- Source: `/home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/src/issue_tracker/`
- Excluding: `daemon/`, `adapters/mcp/`, `factories/`

## Target Structure (from shortlist.md)

```
src/dot_work/db_issues/
├── __init__.py
├── domain/
│   ├── __init__.py
│   └── entities.py        # Issue, Comment, Dependency, Epic, Label
├── services/
│   ├── __init__.py
│   ├── issue_service.py    # Core CRUD
│   └── search_service.py   # Search functionality
├── adapters/
│   ├── __init__.py
│   └── sqlite.py           # SQLite implementation
├── cli.py                   # Typer CLI commands
└── config.py                # Configuration
```

## Source Analysis

### Domain Entities (from source)

#### ✅ Issue Entity (`domain/entities/issue.py`)
**Status:** READ - 322 lines

Dataclass with:
- Fields: id, project_id, title, description, status, priority, type, assignee, epic_id, labels, created_at, updated_at, closed_at
- Enums: IssueStatus (OPEN, IN_PROGRESS, BLOCKED, RESOLVED, CLOSED, ARCHIVED)
- Enums: IssueType (BUG, FEATURE, TASK, EPIC, CHORE)
- Methods: transition(), add_label(), remove_label(), assign_to(), assign_to_epic()
- Pattern: Immutable (all methods return new Issue instance)

#### Remaining to Read:
- [ ] Comment entity
- [ ] Dependency entity
- [ ] Epic entity
- [ ] Label entity
- [ ] IssuePriority value object
- [ ] Repository interfaces (ports)
- [ ] Issue service
- [ ] Search service
- [ ] SQLite adapter

## Source Analysis - Complete

### ✅ All Entities Read

| Entity | Source File | Key Features |
|--------|-------------|--------------|
| **Issue** | `entities/issue.py` | 322 lines, status transitions, label methods, immutable pattern |
| **Comment** | `entities/comment.py` | Simple entity, id/issue_id/author/text/timestamps |
| **Dependency** | `entities/dependency.py` | DependencyType enum, self-dependency validation |
| **Epic** | `entities/epic.py` | EpicStatus enum, parent_epic_id for hierarchy |
| **Label** | `entities/label.py` | id/name/color/description |
| **IssuePriority** | `value_objects.py` | IntEnum (0-4): CRITICAL, HIGH, MEDIUM, LOW, BACKLOG |

### ✅ Domain Exceptions (`domain/exceptions.py`)

- `DomainError` (base)
- `InvariantViolationError` - domain invariant violations
- `InvalidTransitionError` - status transition errors
- `NotFoundError` - entity not found
- `ValidationError` - input validation
- `DatabaseError` - DB operations
- `CycleDetectedError` - dependency cycles

### ✅ Domain Ports (`domain/ports/__init__.py`)

- `Clock` protocol - time provider
- `IdentifierService` protocol - ID generation

### ✅ Services

| Service | File | Purpose |
|---------|------|---------|
| **IssueService** | `services/issue_service.py` | 597 lines - CRUD, transitions, comments, dependencies, bulk ops, epics |
| **SearchService** | `services/search_service.py` | FTS5 full-text search with BM25 ranking |
| **IssueStatsService** | `services/issue_stats_service.py` | Statistics and metrics (not yet read) |
| **IssueGraphService** | `services/issue_graph_service.py` | Dependency graph operations (not yet read) |

### ✅ Database Layer

| Component | File | Purpose |
|-----------|------|---------|
| **Engine** | `adapters/db/engine.py` | create_db_engine(), get_database_path() |
| **Models** | `adapters/db/models.py` | SQLModel tables: Issue, Label, IssueLabel, Comment, Dependency, Epic |
| **UnitOfWork** | `adapters/db/unit_of_work.py` | Transaction management |
| **Repositories** | `adapters/db/repositories/` | issue_repository, comment_repository, issue_graph_repository |

### Key Design Patterns

1. **Immutable entities** - methods return new instances
2. **Unit of Work** - transaction management via context manager
3. **Repository pattern** - abstract data access
4. **Service layer** - business logic coordination
5. **Dependency injection** - Clock, IdentifierService protocols

## Consolidation Plan for `src/dot_work/db_issues/`

### Target Structure

```
src/dot_work/db_issues/
├── __init__.py
├── domain/
│   ├── __init__.py
│   └── entities.py        # All entities + value objects + exceptions + utils
├── services/
│   ├── __init__.py
│   ├── issue_service.py    # Core CRUD
│   └── search_service.py   # FTS5 search
├── adapters/
│   ├── __init__.py
│   └── sqlite.py           # Models + UnitOfWork + Engine
├── cli.py                   # Typer commands
└── config.py                # Configuration
```

### Implementation Order

1. **domain/entities.py** - Consolidate all entities, enums, exceptions, utils
2. **adapters/sqlite.py** - Models, engine, repositories, unit_of_work
3. **services/issue_service.py** - Core CRUD operations
4. **services/search_service.py** - FTS5 search
5. **config.py** - Configuration management
6. **cli.py** - Typer CLI commands (basic ones for this issue)

## Notes

- Exclude `daemon/`, `adapters/mcp/`, `factories/` per requirements
- Use `dot_work` prefix instead of `issue_tracker` for imports
- Preserve all domain invariants and business rules
- Keep SQLModel/SQLAlchemy for persistence
