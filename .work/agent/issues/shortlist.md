# Shortlist (User-Directed Priority)

This file represents **explicit user intent**. Agent may only modify when explicitly instructed.

---

## Active Work

All shortlist items have been addressed. See Completed Items section below.

---

### Shortlist Items (2025-12-30)

- TEST-041@7a8b9c - Add incoming and .work to scan ignore lists (COMPLETED)
  - Added "incoming" to exclude list in _detect_source_dirs() (runner.py)
  - Verified pyproject.toml already has norecursedirs for both incoming and .work

- TEST-042@8b9c0d - Handle git history integration tests safely (COMPLETED)
  - Added @pytest.mark.skip to all 18 git history integration tests
  - Added clear safety notices in file header with AGENT NOTICE

- TEST-043@9c0d1e - Fix SQLAlchemy engine accumulation (COMPLETED)
  - Fixed test_cycle_detection_n_plus_one.py to use session-scoped db_engine
  - Changed integration test conftest to use session-scoped engine
  - Fixed _reset_database_state to include dependencies table
  - Added proper engine.dispose() calls in test_sqlite.py
  - Results: 337 db_issues unit tests pass with +16.4 MB memory growth

- TEST-044@0d1e2f - Refactor test_pipeline.py (DEFERRED)
  - Medium priority, requires larger refactor to extract parser logic
  - Existing tests are functional but slow (run full pipeline)

### Previous Completed Items

All migration validation audits and FEAT-022 have been completed and archived to history.md:
- AUDIT-KG-001: Knowledge Graph Module Migration Validation
- AUDIT-REVIEW-002: Container Provision Module Migration Validation
- AUDIT-GIT-003: Git Module Migration Validation
- AUDIT-VERSION-004: Version Module Migration Validation
- AUDIT-ZIP-005: Zip Module Migration Validation
- AUDIT-OVERVIEW-006: Overview Module Migration Validation
- AUDIT-PYBUILD-007: Python Build Module Migration Validation
- AUDIT-DBISSUES-010: DB-Issues Module Migration Validation
- FEAT-022: Interactive Prompt Wizard for Canonical Prompts

See history.md for detailed investigation reports dated 2025-12-25 through 2025-12-26.

---
