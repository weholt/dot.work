# AUDIT-GAP-003 Investigation: Large consolidated files reduce modularity

**Issue:** AUDIT-GAP-003@c3d5f2
**Started:** 2024-12-27T04:30:00Z
**Completed:** 2024-12-27T04:35:00Z
**Status**: Documented for focused refactor

---

## Problem Analysis

**Root Cause:** During AUDIT-DBISSUES-010 migration, multiple smaller source files were consolidated into single large destination files for simpler directory structure.

### File Sizes and Impact

| File | Size | Lines | Content |
|------|-------|-------|---------|
| `cli.py` | 209KB | 5718 | 50+ CLI commands, 11 typer sub-apps, utilities |
| `sqlite.py` | 62KB | ~1800 | All repositories + UnitOfWork |
| `entities.py` | 16KB | ~450 | All domain entities |

**cli.py Breakdown:**
- Lines 1-185: Imports, app setup, typer sub-apps
- Lines 186-520: Core commands (create, list, search, ready)
- Lines 520-1090: Utility functions (_sort, _get_field_value, _output_*, _generate_*)
- Lines 1091-1650: Core commands continued (show, update, edit)
- Lines 1651-1890: Epic commands (epic_create, epic_list, etc.)
- Lines 1891-2340: Project commands
- Lines 2341-2585: Child epic commands
- Lines 2586-2910: IO commands (export, import, sync)
- Lines 2911-3125: Dependency commands
- Lines 3126-3395: Label commands
- Lines 3396-3655: Comment commands
- Lines 3656-3840: Instruction/template commands
- Lines 3841-4015: Template commands
- Lines 4016-4300: Bulk commands
- Lines 4301-4400+: Other commands

**Utility Functions (extractable):**
| Function | Lines | Purpose |
|----------|-------|---------|
| `_sort_issues` | 520-547 | Sort issues by field |
| `_get_field_value` | 548-574 | Get issue field value |
| `_parse_fields` | 575-588 | Parse field list |
| `_output_table` | 589-628 | Table output |
| `_output_json` | 629-673 | JSON output |
| `_output_jsonl` | 674-706 | JSONL output |
| `_output_csv` | 707-734 | CSV output |
| `_output_markdown` | 735-764 | Markdown output |
| `_output_show_json` | 765-798 | Show single issue JSON |
| `_output_search_table` | 799-826 | Search results table |
| `_output_search_json` | 827-865 | Search results JSON |
| `_output_search_jsonl` | 866-892 | Search results JSONL |
| `_output_ready_table` | 893-935 | Ready report table |
| `_output_ready_json` | 936-979 | Ready report JSON |
| `_generate_issue_template` | 1094-1130 | Generate edit template |
| `_parse_edited_issue` | 1131-1208 | Parse edited issue |
| `_validate_editor` | 1209-1271 | Validate editor command |
| `_get_text_from_editor` | 1272-1324 | Get text from editor |
| `_generate_epic_mermaid` | 1989-2056 | Generate Mermaid diagram |
| `_output_stats_table` | 4801-4831 | Stats table |
| `_output_stats_json` | 4832-4860+ | Stats JSON |

---

## Consolidation Trade-offs

**Benefits (Current Structure):**
- ✅ Fewer files to navigate
- ✅ Simpler imports (single import point)
- ✅ Related code co-located
- ✅ Easier to find things initially

**Drawbacks:**
- ⚠️ 209KB cli.py file is difficult to review
- ⚠️ 5718 lines creates cognitive load
- ⚠️ More merge conflicts (single file contention)
- ⚠️ Harder to understand at a glance
- ⚠️ Reduced modularity (can't import subsets)

---

## Proposed Solution

### Recommended Split Strategy

Given the size, a **phased approach** is recommended:

**Phase 1: Extract Output Utilities** (Quick Win, ~400 lines)
- Create `cli_output.py` with all `_output_*` functions
- Create `cli_utils.py` with `_sort_issues`, `_get_field_value`, `_parse_fields`
- Import from new modules in cli.py
- **Impact:** Reduces cli.py by ~400 lines, separates presentation logic

**Phase 2: Extract Editor Functions** (~200 lines)
- Create `cli_editor.py` with editor-related utilities:
  - `_generate_issue_template`
  - `_parse_edited_issue`
  - `_validate_editor`
  - `_get_text_from_editor`
- **Impact:** Cleaner separation of concerns

**Phase 3: Group Command Modules** (Larger Refactor)
- Keep core commands in `cli.py` (create, show, list, update, delete, close)
- Create `cli_epic.py` for epic commands
- Create `cli_project.py` for project commands
- Create `cli_deps.py` for dependency commands
- Create `cli_io.py` for import/export
- **Impact:** More focused, reviewable command modules

### File Structure After Split

```
src/dot_work/db_issues/
├── __init__.py
├── cli.py                 # Main app, core commands (~1000 lines)
├── cli_output.py          # Output formatting utilities (~400 lines)
├── cli_utils.py           # General utilities (~200 lines)
├── cli_editor.py          # Editor functions (~200 lines)
├── cli_epic.py            # Epic commands (~300 lines)
├── cli_project.py         # Project commands (~350 lines)
├── cli_deps.py            # Dependency commands (~400 lines)
├── cli_io.py              # Import/export commands (~250 lines)
├── cli_labels.py          # Label commands (~400 lines)
├── cli_comments.py        # Comment commands (~200 lines)
├── cli_templates.py       # Template/instruction commands (~300 lines)
├── cli_bulk.py            # Bulk operations commands (~400 lines)
├── cli_search.py          # Search index commands (~200 lines)
```

---

## Implementation Considerations

**Import Strategy:**
```python
# In cli.py
from dot_work.db_issues.cli_output import (
    _output_table,
    _output_json,
    # ... other output functions
)
from dot_work.db_issues.cli_utils import (
    _sort_issues,
    _get_field_value,
    _parse_fields,
)
```

**Typer App Re-exports:**
```python
# Sub-apps need to be accessible
from dot_work.db_issues.cli import app, epic_app, project_app, deps_app, etc.
```

**Testing:**
- All existing tests should pass without modification
- CLI commands should work identically
- Test that all sub-apps are accessible

---

## Estimated Effort

| Phase | Lines Changed | Complexity | Time |
|-------|---------------|------------|------|
| Phase 1: Output Utils | ~400 | Low | 1-2 hours |
| Phase 2: Editor Utils | ~200 | Low | 1 hour |
| Phase 3: Command Groups | ~3000 | Medium | 4-6 hours |
| **Total** | **~3600** | **Medium** | **6-9 hours** |

---

## Acceptance Criteria

- [ ] cli.py reduced from 5718 to ~2000 lines (Phase 1-3)
- [ ] Output utilities extracted to cli_output.py
- [ ] Editor utilities extracted to cli_editor.py
- [ ] Command groups separated into focused modules
- [ ] All imports work correctly
- [ ] All existing tests pass
- [ ] CLI commands work identically
- [ ] Documentation updated with new structure

---

## Notes

- Related: PERF-007 (batch operations), other refactors
- This is **low priority** - current structure works but has trade-offs
- Recommend doing as **focused feature branch** due to scope
- Can be done incrementally (Phase 1 provides value immediately)
- Consider using `ruff check --select I` to check for import issues after split

**Status:** Documented for future implementation. Not implemented in this session due to scope.
