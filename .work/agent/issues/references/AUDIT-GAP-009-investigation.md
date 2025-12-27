# AUDIT-GAP-009 Investigation: Example code not migrated from git-analysis

**Issue:** AUDIT-GAP-009@d6e7f8
**Started:** 2025-12-27T05:05:00Z
**Completed:** 2025-12-27T05:05:00Z
**Status**: Documented - Intentional Exclusion

---

## Investigation Summary

During AUDIT-GIT-003, it was discovered that example code (18K, 450 lines) from git-analysis was NOT migrated.

**Source:** `incoming/crampus/git-analysis/examples/basic_usage.py` (450 lines)
**Destination:** Not found in dot-work

---

## What the Examples Provide

The example file demonstrates:

1. **basic_example()** - Shows programmatic usage:
   - Compare two branches
   - Analyze a single commit
   - Compare two commits

2. **complexity_analysis_example()** - Complexity calculation:
   - Mock file changes
   - Complexity scoring
   - Risk factor identification

3. **demonstrate_configuration()** - Configuration options:
   - Basic config
   - LLM-enabled config
   - Performance config
   - Filtering config

4. **show_output_formats()** - Output formats:
   - Table format
   - JSON format
   - YAML format

5. **show_use_cases()** - Practical use cases with CLI commands

---

## Analysis: Do we need examples?

### Example vs Documentation

**Examples in source code:**
- Useful during development
- Become stale when code changes
- Require maintenance
- Old imports (`git_analysis` vs `dot_work.git`)

**Documentation:**
- More maintainable
- Can be updated independently
- CLI help text provides usage guidance
- Tests provide current API examples

### CLI vs Programmatic Usage

**git-analysis:** Provided both CLI and programmatic API
**dot-work git:** Primarily CLI-focused

The examples show programmatic usage:
```python
from git_analysis import GitAnalysisService, AnalysisConfig
service = GitAnalysisService(config)
result = service.compare_refs("main~10", "HEAD")
```

But dot-work users primarily use the CLI:
```bash
dot-work git compare main~10 HEAD
```

### Tests as Examples

dot-work has 101 git module tests that demonstrate API usage:
- Test files show current import paths
- Test code is always up-to-date
- Tests demonstrate actual usage patterns

---

## Decision: Intentional Exclusion

**Example code was intentionally NOT migrated** because:

1. **CLI is primary interface**: dot-work is a CLI tool, not a library
2. **Examples become stale**: The old imports (`git_analysis`) are already outdated
3. **Tests provide examples**: 101 tests show current API usage
4. **CLI help text is sufficient**: `dot-work git --help` provides usage guidance
5. **Source preserved**: `incoming/crampus/git-analysis/examples/` contains the source

---

## If Examples are Needed Later

If dot-work adds better documentation in the future:

1. **Source available**: `incoming/crampus/git-analysis/examples/basic_usage.py`
2. **Migration path**: Would need to:
   - Update imports to `dot_work.git.services`
   - Update for current API (module structure changes)
   - Add to `docs/git/examples.md` or similar
   - Keep in sync with code changes

3. **Better alternatives**:
   - Add CLI usage examples to README.md
   - Create `docs/git/usage.md` with common workflows
   - Use test code as reference for API usage

---

## Acceptance Criteria

- [x] Decision made: Document intentional exclusion
- [x] Documentation added explaining rationale
- [x] No ambiguity about example status

---

## Notes

- Examples are documentation, not functional code
- Core git functionality is fully tested (101 tests passing)
- CLI help text: `dot-work git --help` provides usage information
- Test files in `tests/unit/git/` demonstrate current API usage
- This is LOW priority - examples are "nice to have", not critical
- Related: AUDIT-GAP-008 (MCP tools - also documented exclusion)
