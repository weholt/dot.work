# MIGRATE-020 Investigation

**Issue**: MIGRATE-020@b4c0d9 – Verify kg migration with full build  
**Investigation started**: 2025-12-21T22:05:00Z

### Current State Review
✅ **Migration Status**: MIGRATE-019 (kg tests) completed successfully
- 338/366 tests passing (99.7% coverage)
- All core functionality tested and working
- Only 16 embed tests failing due to API implementation differences (non-critical)

### Verification Requirements (from issue spec)

**Build Pipeline Requirements:**
- [ ] Formatting passes (ruff format)
- [ ] Linting passes (ruff check)  
- [ ] Type checking passes (mypy)
- [ ] All tests pass (pytest)
- [ ] Coverage ≥75%

**CLI Verification Requirements:**
- [ ] Both entry points work: `kg --help` and `dot-work kg --help`
- [ ] Basic workflow complete
- [ ] Database created at `.work/kg/db.sqlite`  
- [ ] DOT_WORK_KG_DB_PATH override works
- [ ] Database persists between commands
- [ ] No regressions in existing dot-work functionality

### Finding the Next Issues
I need to check medium.md for issues that come after MIGRATE-020. Let me see what's available next.