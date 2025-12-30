# Shortlist (User-Directed Priority)

This file represents **explicit user intent**. Agent may only modify when explicitly instructed.

---

## Active Work

---

All previous shortlist items (ENH-025, ENH-026, REFACTOR-003) have been completed and moved to history.md.

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
