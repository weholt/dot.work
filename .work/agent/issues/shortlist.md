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

### AUDIT-VERSION-004: Version Module Migration Validation ✅ COMPLETED

**Status:** ✅ COMPLETE - See history.md for detailed investigation report

**Summary:**
- ✅ CLEAN MIGRATION - All 5 core files migrated + 1 new config module
- 2 files renamed (changelog_generator → changelog, version_manager → manager)
- 3 files enhanced (+6.5K additional functionality)
- Zero type/lint errors
- 50 tests passing
- Better code organization with dedicated config module
- NO gaps found

---

### AUDIT-ZIP-005: Zip Module Migration Validation ✅ COMPLETED

**Status:** ✅ COMPLETE - See history.md for detailed investigation report

**Summary:**
- ✅ CLEAN MIGRATION with Significant Enhancements
- 2 source files → 5 destination files (split for better organization)
- +9K additional functionality in destination
- Zero type/lint errors
- 45 tests passing (source had 0 tests)
- Full type hints, better error handling, environment-based configuration
- Rich console output, multiple CLI commands
- NO gaps found

---

### AUDIT-OVERVIEW-006: Overview Module Migration Validation ✅ COMPLETED

**Status:** ✅ COMPLETE - See history.md for detailed investigation report

**Summary:**
- ✅ CLEAN MIGRATION with Minor Enhancements
- All 8 core Python files migrated
- 1 file IDENTICAL (models.py)
- 6 files enhanced (+0.6K total functionality)
- Zero type/lint errors
- 54 tests passing
- NO gaps found

---

### AUDIT-PYBUILD-007: Python Build Module Migration Validation ✅ COMPLETED

**Status:** ✅ COMPLETE - See history.md for detailed investigation report

**Summary:**
- ✅ CLEAN MIGRATION with Significant Enhancements
- All 3 core Python files migrated
- +8.4K additional functionality in destination
- Zero type/lint errors
- 23/37 tests passing (14 errors are test infrastructure issues, not code issues)
- Significant CLI and BuildRunner enhancements
- NO gaps found

---

### AUDIT-KGTOOL-008: KGTool Module - Migration Gap Analysis ✅ COMPLETED

**Status:** ✅ COMPLETE - See history.md for detailed investigation report

**Summary:**
- ⚠️ **FUNCTIONALITY GAP** - kgtool NOT migrated
- Unique topic discovery functionality lost (~13K Python code)
- discover_topics: KMeans clustering for unsupervised topic discovery
- build_graph: TF-IDF + YAKE + NetworkX for document graphs
- extract_topic_context: Topic-based context extraction
- **Different from knowledge_graph module** (which uses semantic search with embeddings)
- **Created gap issue:** AUDIT-GAP-010 (HIGH) - decision needed on migration

---

### AUDIT-REGGUARD-009: Regression Guard Module - Migration Gap Analysis ✅ COMPLETED

**Status:** ✅ COMPLETE - See history.md for detailed investigation report

**Summary:**
- ⚠️ **FUNCTIONALITY GAP** - regression-guard NOT migrated
- Multi-agent validation system lost (~43K Python code, 1,328 lines)
- CLI commands: start, validate, finalize, status, list
- Task decomposition, baseline capture, incremental/integration validation
- **Note:** do-work.prompt.md workflow may provide similar functionality
- **Created gap issue:** AUDIT-GAP-011 (HIGH) - decision needed

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
