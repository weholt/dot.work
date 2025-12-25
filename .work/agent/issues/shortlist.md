# Shortlist (User-Directed Priority)

This file represents **explicit user intent**. Agent may only modify when explicitly instructed.

---

## Active Work

---

(No active issues - FEAT-008 was completed and moved to history.md)

---

## Migration Validation Audits

**Purpose:** Deep source-destination comparison before removing incoming/ folder.

---

### AUDIT-KG-001: Knowledge Graph Module Migration Validation

**Source:** `incoming/kg/src/kgshred/`
**Destination:** `src/dot_work/knowledge_graph/`
**Migration Range:** MIGRATE-013 through MIGRATE-020
**Priority:** CRITICAL

#### Audit Scope
1. **Feature Parity Analysis**
   - Compare all public APIs between kgshred and knowledge_graph
   - CLI commands: `kg` vs knowledge graph commands
   - Database operations: CRUD, FTS5, semantic search, embeddings
   - Graph building: parse_md.py → graph.py flow
   - Embedding support: ollama, openai, openrouter backends

2. **Documentation Migration**
   - README.md from kgshred → dot-work documentation
   - AGENTS.md guidelines
   - API docs for embed, db, graph, search modules
   - Usage examples and tutorials

3. **Test Coverage**
   - Unit tests: kgshred tests/ → knowledge_graph tests/
   - Integration tests: verify all scenarios covered
   - Edge cases: empty corpus, large documents, malformed markdown
   - Performance tests: embedding batch processing, search latency

4. **Configuration & CLI**
   - CLI subcommands: all kg commands available?
   - Config options: .work/kg/ configuration handling
   - Environment variables: all env vars migrated?

5. **Dependencies**
   - pyproject.toml: all kg dependencies in dot-work?
   - Optional dependencies: kg-http, kg-ann, kg-vec

6. **Code Quality**
   - Type annotations coverage
   - Linting status
   - Code organization and structure

#### Specific Checks
- [ ] `cli.py` (23KB) → knowledge_graph CLI - all commands?
- [ ] `db.py` (49KB) → knowledge_graph/db.py - all features?
- [ ] `graph.py` → knowledge_graph/graph.py - all graph operations?
- [ ] `search_fts.py` (11KB) → search_fts.py - complete?
- [ ] `search_semantic.py` (10KB) → search_semantic.py - complete?
- [ ] `embed/` directory - all backends supported?
- [ ] `parse_md.py`, `render.py` - migrated/consolidated?

#### Acceptance Criteria
- [ ] 100% feature parity documented
- [ ] All tests migrated and passing
- [ ] All documentation migrated
- [ ] No regressions identified
- [ ] Gaps documented (if any)

---

### AUDIT-REVIEW-002: Review Module Migration Validation

**Source:** `incoming/crampus/repo-agent/`
**Destination:** `src/dot_work/review/`
**Migration Range:** MIGRATE-001 through MIGRATE-012
**Priority:** CRITICAL

#### Audit Scope
1. **Feature Parity Analysis**
   - repo-agent CLI → review CLI commands
   - Core functionality: init, validate, run
   - Template system: templates.py handling
   - Docker integration: container-based agent execution
   - Validation rules: validation.py logic
   - Git operations: PR creation, patch application

2. **Documentation Migration**
   - README from repo-agent
   - Docker usage docs
   - Template format specifications
   - Agent configuration guides

3. **Test Coverage**
   - Unit tests: repo-agent tests/ → review tests/
   - Integration tests: Docker scenarios
   - Template tests: various instruction formats
   - Validation tests: rule checking

4. **Configuration & Assets**
   - Static files: static/ migrated?
   - Templates: templates/ migrated?
   - Server functionality: server.py

5. **Dependencies**
   - FastAPI, uvicorn, pydantic dependencies
   - Docker-related dependencies
   - Template processing libraries

#### Specific Checks
- [ ] `cli.py` (6KB) → review CLI - all commands?
- [ ] `core.py` (29KB) → review core - all features?
- [ ] `templates.py` → review templates?
- [ ] `validation.py` → review validation?
- [ ] Docker integration: container provision module
- [ ] FastAPI server: server.py - all endpoints?
- [ ] Git operations: git.py - all PR operations?

#### Acceptance Criteria
- [ ] 100% feature parity documented
- [ ] All tests migrated and passing
- [ ] All documentation migrated
- [ ] Docker workflows verified
- [ ] Gaps documented (if any)

---

### AUDIT-GIT-003: Git Module Migration Validation

**Source:** `incoming/crampus/git-analysis/`
**Destination:** `src/dot_work/git/`
**Migration Range:** MIGRATE-064 through MIGRATE-069
**Priority:** CRITICAL

#### Audit Scope
1. **Feature Parity Analysis**
   - git-analysis CLI → git CLI commands
   - Core services: cache, complexity, file_analyzer, git_service, llm_summarizer, tag_generator
   - MCP tools integration
   - Git history parsing and analysis
   - Complexity scoring algorithms
   - Tag generation logic

2. **Documentation Migration**
   - git-analysis README/docs
   - MCP integration docs
   - Algorithm documentation

3. **Test Coverage**
   - Unit tests: git-analysis tests/ → git tests/
   - Integration tests: Git operations
   - MCP tools tests

4. **Configuration & CLI**
   - CLI subcommands: all git commands?
   - Configuration options

5. **Dependencies**
   - GitPython usage
   - Analysis libraries

#### Specific Checks
- [ ] `cli.py` → git/cli.py - all commands?
- [ ] `services/cache.py` → git services?
- [ ] `services/complexity.py` → git services?
- [ ] `services/file_analyzer.py` → git services?
- [ ] `services/git_service.py` → git services?
- [ ] `services/llm_summarizer.py` → git services?
- [ ] `services/tag_generator.py` → git services?
- [ ] `mcp/tools.py` → MCP integration?
- [ ] All services migrated?

#### Acceptance Criteria
- [ ] 100% feature parity documented
- [ ] All tests migrated and passing
- [ ] All documentation migrated
- [ ] Gaps documented (if any)

---

### AUDIT-VERSION-004: Version Module Migration Validation

**Source:** `incoming/crampus/version-management/`
**Destination:** `src/dot_work/version/`
**Migration Range:** MIGRATE-041 through MIGRATE-046
**Priority:** CRITICAL

#### Audit Scope
1. **Feature Parity Analysis**
   - version-management CLI → version CLI commands
   - Changelog generation: changelog_generator.py
   - Commit parsing: commit_parser.py
   - Project parsing: project_parser.py
   - Version management: version_manager.py
   - Auto-detection of project types

2. **Documentation Migration**
   - version-management README
   - Changelog format docs
   - Supported project types

3. **Test Coverage**
   - Unit tests: version-management tests/ → version tests/
   - Project parser tests
   - Commit parser tests

4. **Configuration & CLI**
   - CLI subcommands: all version commands?
   - Supported project types

#### Specific Checks
- [ ] `cli.py` → version/cli.py - all commands?
- [ ] `changelog_generator.py` → version/changelog.py?
- [ ] `commit_parser.py` → version/commit.py?
- [ ] `project_parser.py` → version/project.py?
- [ ] `version_manager.py` → version/manager.py?
- [ ] All project types supported?
- [ ] Auto-detection logic complete?

#### Acceptance Criteria
- [ ] 100% feature parity documented
- [ ] All tests migrated and passing
- [ ] All documentation migrated
- [ ] Gaps documented (if any)

---

### AUDIT-ZIP-005: Zip Module Migration Validation

**Source:** `incoming/zipparu/zipparu/`
**Destination:** `src/dot_work/zip/`
**Migration Range:** MIGRATE-021 through MIGRATE-026
**Priority:** CRITICAL

#### Audit Scope
1. **Feature Parity Analysis**
   - zipparu CLI → zip CLI commands
   - Main functionality: main.py logic
   - Archive creation/extraction
   - File filtering patterns

2. **Documentation Migration**
   - zipparu README
   - Usage examples

3. **Test Coverage**
   - Unit tests: any in zipparu?
   - Integration tests for zip operations

4. **Dependencies**
   - zipfile stdlib usage
   - External dependencies

#### Specific Checks
- [ ] `__init__.py` (85 bytes) → zip/__init__.py?
- [ ] `main.py` (1.8KB) → zip module - all features?
- [ ] All CLI commands available?
- [ ] Documentation migrated?

#### Acceptance Criteria
- [ ] 100% feature parity documented
- [ ] All tests migrated and passing (if any existed)
- [ ] All documentation migrated
- [ ] Gaps documented (if any)

---

### AUDIT-OVERVIEW-006: Overview Module Migration Validation

**Source:** `incoming/crampus/birdseye/`
**Destination:** `src/dot_work/overview/`
**Migration Range:** MIGRATE-058 through MIGRATE-063
**Priority:** CRITICAL

#### Audit Scope
1. **Feature Parity Analysis**
   - birdseye → overview CLI
   - Code scanning: scanner.py logic
   - Code parsing: code_parser.py
   - Markdown parsing: markdown_parser.py
   - Pipeline: pipeline.py
   - Reporter: reporter.py
   - Models: models.py

2. **Documentation Migration**
   - birdseye README
   - Sample project outputs
   - Usage instructions

3. **Test Coverage**
   - Unit tests: birdseye tests?
   - Integration tests: codebase scanning

4. **Configuration & CLI**
   - CLI subcommands: all overview commands?
   - Output formats

#### Specific Checks
- [ ] `cli.py` → overview/cli.py - all commands?
- [ ] `code_parser.py` → overview/code_parser.py?
- [ ] `markdown_parser.py` → overview/markdown_parser.py?
- [ ] `scanner.py` → overview/scanner.py?
- [ ] `pipeline.py` → overview/pipeline.py?
- [ ] `reporter.py` → overview/reporter.py?
- [ ] `models.py` → overview/models.py?
- [ ] All code parsers supported?
- [ ] All report formats?

#### Acceptance Criteria
- [ ] 100% feature parity documented
- [ ] All tests migrated and passing (if any existed)
- [ ] All documentation migrated
- [ ] Gaps documented (if any)

---

### AUDIT-PYBUILD-007: Python Build Module Migration Validation

**Source:** `incoming/crampus/builder/`
**Destination:** `src/dot_work/python/build/`
**Migration Range:** MIGRATE-053 through MIGRATE-057
**Priority:** CRITICAL

#### Audit Scope
1. **Feature Parity Analysis**
   - builder → python/build CLI
   - BuildRunner class: build.py → runner.py
   - Pipeline steps: formatting, linting, type-checking, testing, security
   - Configuration options
   - Auto-fix capabilities
   - Coverage thresholds

2. **Documentation Migration**
   - builder README/docs
   - Build pipeline documentation
   - Quality gate documentation

3. **Test Coverage**
   - Unit tests: builder tests?
   - Integration tests: build pipeline

4. **Configuration & CLI**
   - CLI options: pybuilder → python build
   - Config file support

#### Specific Checks
- [ ] build.py BuildRunner → runner.py
- [ ] All pipeline steps implemented?
- [ ] ruff format, ruff check, mypy, pytest integration?
- [ ] Auto-fix --fix flag works?
- [ ] Coverage threshold enforcement?
- [ ] Security scanning step?
- [ ] Clean --clean flag?

#### Acceptance Criteria
- [ ] 100% feature parity documented
- [ ] All tests migrated and passing (if any existed)
- [ ] All documentation migrated
- [ ] Gaps documented (if any)

---

### AUDIT-KGTOOL-008: KGTool Module - Migration Gap Analysis

**Source:** `incoming/crampus/kgtool/`
**Destination:** NOT FOUND (potentially lost functionality)
**Priority:** CRITICAL

#### Analysis Scope
1. **Feature Discovery**
   - kgtool functionality: build, discover-topics, extract
   - Knowledge graph extraction from markdown
   - Topic discovery (unsupervised clustering)
   - Context extraction by topic
   - TF-IDF and YAKE algorithms

2. **Integration Assessment**
   - Should this be migrated to dot-work?
   - Is functionality redundant with knowledge_graph?
   - Would it complement existing modules?

3. **Test Coverage**
   - kgtool has tests for: benchmarks, chunking, context_extraction, edge_cases, graph_building
   - Are these tests relevant?

4. **Documentation**
   - kgtool usage documentation
   - Algorithm documentation

#### Specific Checks
- [ ] `kgtool/cli.py` - build, discover-topics, extract commands
- [ ] `kgtool/pipeline.py` - build_graph, discover_topics, extract_topic_context
- [ ] Test files: 9 test files with various scenarios
- [ ] Is this needed in dot-work?
- [ ] Should it be integrated into knowledge_graph?

#### Acceptance Criteria
- [ ] Feature parity assessed (not migrated)
- [ ] Recommendation made: migrate, integrate, or deprecate
- [ ] Justification documented

---

### AUDIT-REGGUARD-009: Regression Guard Module - Migration Gap Analysis

**Source:** `incoming/crampus/regression-guard/`
**Destination:** NOT FOUND (potentially lost functionality)
**Priority:** CRITICAL

#### Analysis Scope
1. **Feature Discovery**
   - regression-guard CLI: start, validate, finalize, status, list
   - Orchestrator: orchestration logic
   - Baseline capture: capture_baseline.py
   - Decomposition: decompose.py
   - Incremental validation: validate_incremental.py
   - Integration validation: validate_integration.py

2. **Integration Assessment**
   - Should this be migrated to dot-work?
   - Is functionality useful for dot-work workflow?
   - Would it complement existing modules?

3. **Test Coverage**
   - regression-guard has tests for orchestrator
   - Integration test scenarios

4. **Documentation**
   - regression-guard README
   - Workflow documentation

#### Specific Checks
- [ ] `cli.py` - start, validate, finalize, status, list commands
- [ ] `orchestrator.py` - orchestration logic
- [ ] `capture_baseline.py` - baseline capture functionality
- [ ] `decompose.py` - task decomposition
- [ ] `validate_incremental.py` - incremental validation
- [ ] `validate_integration.py` - integration validation
- [ ] Is this needed in dot-work?
- [ ] Should it be a standalone tool or integrated?

#### Acceptance Criteria
- [ ] Feature parity assessed (not migrated)
- [ ] Recommendation made: migrate, integrate, or deprecate
- [ ] Justification documented

### AUDIT-DBISSUES-010: DB-Issues Module Migration Validation

**Source:** `incoming/glorious/src/glorious_agents/skills/issues/src/issue_tracker/`
**Destination:** `src/dot_work/db_issues/`
**Migration Range:** MIGRATE-034 through MIGRATE-085 (52 issues)
**Priority:** CRITICAL - This is the largest and most complex migration

#### Context
The original "issues" skill from the glorious agents main project is a complete SQLite-backed issue tracking system. This migration represents **~70% of all migration work** in the project. The source project was renamed from "issues" to "db_issues" during migration to avoid naming conflicts.

#### Audit Scope

**1. Core Issue Operations (8 commands)**
- `create`, `list`, `show`, `update`, `close`, `reopen`, `delete`, `restore`
- Soft delete with restore functionality
- Issue status transitions
- Hash-based IDs with child IDs (bd-a1b2.1 format)

**2. Issue Status Management (3 commands)**
- `ready`, `blocked`, `stale`
- Additional status values: resolved, in_progress
- Ready queue calculation (issues with no open blockers)

**3. Bulk Operations (CRITICAL - 5 commands)**
- `bulk-create` from CSV/JSON
- `bulk-close`, `bulk-update`
- `bulk-label-add`, `bulk-label-remove`
- Batch transaction handling

**4. Dependency Management (ADVANCED - 5 commands)**
- `dependencies add`, `remove`, `list`
- `dependencies list-all` (global view)
- `dependencies tree` (ASCII visualization)
- `dependencies cycles` (detection + fix suggestions)
- Dependency types: blocks, depends-on, related-to, discovered-from

**5. Epic Management (6 commands)**
- `epics add`, `remove`, `list`, `set`, `clear`
- `epics all` (list all with counts)
- `epics tree` (hierarchical visualization)

**6. Label Management (6 commands)**
- `labels add`, `remove`, `set`, `list`, `all`
- `labels bulk-add`, `labels bulk-remove`
- Global label management

**7. Comment System (3 commands)**
- `comments add`, `list`, `delete`
- Comment entity with timestamps
- Full CRUD on comments

**8. Template Systems**

**A. JSON Templates (4 commands)**
- `template save`, `list`, `show`, `delete`
- Predefined issue configurations

**B. Instruction Templates (MAJOR - 3 commands)**
- `instructions list`, `show`, `apply`
- Markdown-based complex task workflows
- Multi-issue creation from single template
- Task definitions with priorities, efforts, subtasks, acceptance criteria
- Hierarchical template support

**9. Search and Analytics**

**A. Full-Text Search (FTS5)**
- BM25 ranking algorithm
- Snippet highlighting with `<mark>` tags
- Field-specific searches (title:, description:)
- Proximity searches (NEAR operator)

**B. Statistics and Analytics**
- Issue counts by status and priority
- Blocked issues analysis
- Longest dependency chain calculation
- Completion rate tracking
- Resolution rate metrics

**10. System Operations (10 commands)**
- `init` - Initialize issue tracker
- `sync` - Git integration (JSONL export/import)
- `export`, `import` - JSONL format handling
- `rename-prefix` - Bulk ID renaming
- `cleanup` - Archive old issues
- `duplicates` - Find/manage duplicates
- `merge` - Merge duplicate issues
- `edit` - External editor ($EDITOR integration)
- `compact` - Database compaction
- `info` - System information

**11. Advanced Features**
- ASCII tree rendering
- Mermaid diagram generation
- Multi-project support
- Multi-assignee tracking
- Rich console output
- Visualization tools

**12. Data Model**
- Status values: open, closed, resolved, blocked, in_progress
- Priority levels: critical (0), high (1), medium (2), low (3), backlog (4)
- Issue types: task, bug, feature, epic, story
- Time tracking: created, updated, closed timestamps
- Hash-based ID system: prefix + 6-char hash + optional child ID

**13. Database Features**
- SQLite with proper indexing
- Unit of Work pattern
- Transaction management
- FTS5 virtual table for search
- Schema migrations
- Data integrity constraints

#### Documentation Migration
- [ ] README from glorious agents/issues
- [ ] CLI reference documentation (50+ commands)
- [ ] API docs for domain, services, adapters
- [ ] Usage examples and tutorials
- [ ] Template format specifications
- [ ] Database schema documentation

#### Test Coverage
- [ ] Unit tests: issues tests/ → db_issues tests/
- [ ] Domain entity tests
- [ ] Service layer tests (11 services)
- [ ] Adapter tests (SQLite)
- [ ] Integration tests: full workflows
- [ ] Edge cases: empty DB, large datasets, circular dependencies
- [ ] Performance tests: FTS5 search, bulk operations

#### Configuration & CLI
- [ ] CLI subcommands: all 50+ commands available?
- [ ] `.work/db-issues/` configuration handling
- [ ] Environment variables migrated?
- [ ] Editor integration ($EDITOR)
- [ ] Git integration (sync command)

#### Dependencies
- [ ] pyproject.toml: all issues dependencies in dot-work?
- [ ] SQLite/SQLAlchemy usage
- [ ] Rich for CLI formatting
- [ ] Click/Typer for CLI
- [ ] Optional dependencies

#### Specific File Checks
- [ ] `cli.py` (source) → db_issues/cli.py
- [ ] `domain/entities.py` → db_issues/domain/entities.py
- [ ] `domain/enums.py` → db_issues/domain/enums.py
- [ ] `adapters/sqlite.py` → db_issues/adapters/sqlite.py
- [ ] `services/issue_service.py` → db_issues/services/issue_service.py
- [ ] `services/dependency_service.py` → db_issues/services/dependency_service.py
- [ ] `services/epic_service.py` → db_issues/services/epic_service.py
- [ ] `services/label_service.py` → db_issues/services/label_service.py
- [ ] `services/comment_service.py` → db_issues/services/comment_service.py
- [ ] `services/bulk_service.py` → db_issues/services/bulk_service.py
- [ ] `services/search_service.py` → db_issues/services/search_service.py
- [ ] `services/stats_service.py` → db_issues/services/stats_service.py
- [ ] `services/template_service.py` → db_issues/services/template_service.py
- [ ] `templates/instruction_template.py` → db_issues/templates/instruction_template.py
- [ ] `templates/template_manager.py` → db_issues/templates/template_manager.py

#### Acceptance Criteria
- [ ] 100% feature parity documented (all 13 feature categories)
- [ ] All 50+ CLI commands verified
- [ ] All tests migrated and passing (target: 259+ tests)
- [ ] All documentation migrated
- [ ] No regressions identified
- [ ] Gaps documented (if any)
- [ ] Template systems fully functional
- [ ] FTS5 search verified
- [ ] Dependency cycle detection verified
- [ ] Bulk operations verified
- [ ] Git sync verified

#### Success Metrics
- **Total CLI Commands:** 50+
- **Total Services:** 11
- **Test Count:** 259+
- **Feature Categories:** 13
- **Migration Issues:** 52 (MIGRATE-034 through MIGRATE-085)

---

## DB-Issues Migration

**Status:** ✅ COMPLETE (MIGRATE-034 through MIGRATE-085 - 52 issues)

All 52 DB-Issues migration issues have been completed and moved to history.md.

Key achievements:
- Domain entities, enums, and services
- Complete CLI with 50+ commands
- Bulk operations, search, FTS5
- Git integration (sync, export/import)
- Statistics and analytics
- Multi-project support
- Soft delete with restore
- Duplicate detection and merging
- 259 tests passing

See history.md for complete migration summary dated 2024-12-24.
