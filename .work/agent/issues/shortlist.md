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

### AUDIT-KG-001: Knowledge Graph Module Migration Validation ✅ COMPLETED

**Status:** ✅ COMPLETE - See history.md for detailed investigation report

**Summary:**
- ✅ PASS with Minor Issues - Clean migration with enhancements
- Zero type errors, zero lint errors
- All tests migrated (12 unit + 2 integration)
- Destination has improvements: sqlite-vec support, memory-bounded streaming
- Created 2 gap issues: AUDIT-GAP-004 (test bugs), AUDIT-GAP-005 (documentation)

---

### AUDIT-REVIEW-002: Review Module Migration Validation ✅ COMPLETED

**Status:** ✅ COMPLETE - See history.md for detailed investigation report

**Summary:**
- 🔴 **CRITICAL FINDING**: repo-agent was NOT migrated to review
- These are **completely different codebases** with different purposes
- Source: CLI Docker-based LLM agent runner (run/init/validate commands)
- Destination: Web-based code review comment management system (FastAPI server)
- **Zero feature overlap** - no CLI, no Docker, no agent runner in destination
- Created 2 gap issues: AUDIT-GAP-006 (CRITICAL), AUDIT-GAP-007 (HIGH)
- Destination quality: ✅ Zero type/lint errors, ✅ 56 tests passing
- **Implication:** MIGRATE-001 through MIGRATE-012 are based on false premise

#### Acceptance Criteria
- [ ] 100% feature parity documented
- [ ] All tests migrated and passing
- [ ] All documentation migrated
- [ ] Docker workflows verified
- [ ] Gaps documented (if any)

---

### AUDIT-GIT-003: Git Module Migration Validation ✅ COMPLETED

**Status:** ✅ COMPLETE - See history.md for detailed investigation report

**Summary:**
- ✅ CLEAN MIGRATION - All 9 core Python files successfully migrated
- 5 files enhanced with additional functionality (+10K total)
- 4 files identical (exact migrations)
- Zero type/lint errors
- 101 tests passing
- Only MCP tools (26K) and examples (18K) not migrated (both LOW priority)
- Created 2 gap issues: AUDIT-GAP-008 (MCP tools), AUDIT-GAP-009 (examples)

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

### AUDIT-DBISSUES-010: DB-Issues Module Migration Validation ✅ COMPLETED

**Status:** ✅ COMPLETE - See history.md for detailed investigation report

**Summary:**
- 100% feature parity achieved (excluding intentionally excluded daemon/MCP/factories)
- All 50+ CLI commands present (reorganized into logical groups: io, labels, instructions, search-index)
- Documentation expanded from 2 to 4 files
- 277 unit tests passing (integration tests not migrated - documented gap)
- 50 pre-existing type errors (from migration, documented)
- Migration size: 52 issues (MIGRATE-034 through MIGRATE-085)

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
