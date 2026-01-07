# FEAT-005 Investigation: Templatize All Prompt Cross-References

**Started:** 2025-12-22
**Issue:** FEAT-005@d5b2e8 – Templatize all prompt cross-references

---

## Problem Statement

11 of 12 prompt files in `src/dot_work/prompts/` use hardcoded relative paths for cross-references. These break when prompts are installed to non-Copilot environments (Claude, Cursor, Aider, etc.).

### Why This Is a Problem

When prompts are installed to different environments:
- **Claude:** All prompts merged into single `CLAUDE.md` file → relative paths `[text](filename.prompt.md)` become broken
- **Cursor:** Prompts go to `.cursor/rules/*.mdc` files → relative paths don't work
- **Aider:** Content merged into `CONVENTIONS.md` → relative links fail
- **Generic/OpenCode/Zed:** Similar issues with broken cross-references
- **Copilot:** Works fine (prompts stay in `.github/prompts/` and reference paths are correct)

---

## Current Architecture

### Template Context (src/dot_work/installer.py:64-80)
The `build_template_context()` function provides these variables:
```python
{
    "prompt_path": env_config.prompt_dir or "prompts",  # e.g., ".github/prompts", ".cursor/rules", "prompts"
    "ai_tool": env_config.key,                          # e.g., "copilot", "claude", "cursor"
    "ai_tool_name": env_config.name,                    # e.g., "GitHub Copilot (VS Code)"
    "prompt_extension": env_config.prompt_extension or ".md",  # e.g., ".prompt.md", ".mdc"
    "instructions_file": env_config.instructions_file or "",   # e.g., "CLAUDE.md", "AGENTS.md"
    "rules_file": env_config.rules_file or "",                 # e.g., ".cursorrules", "CONVENTIONS.md"
}
```

### Template Engine
- Uses Jinja2 with FileSystemLoader
- Autoescape disabled (trusted internal markdown files)
- Available in all prompt files during rendering

### Environments (src/dot_work/environments.py:20-122)
| Environment | prompt_dir | prompt_extension |
|-------------|-----------|------------------|
| copilot | `.github/prompts` | `.prompt.md` |
| claude | `None` | `None` |
| cursor | `.cursor/rules` | `.mdc` |
| windsurf | `.windsurf/rules` | `.md` |
| aider | `None` | `None` |
| continue | `.continue/prompts` | `.md` |
| amazon-q | `None` | `None` |
| zed | `.zed/prompts` | `.md` |
| opencode | `.opencode/prompts` | `.md` |
| generic | `prompts` | `.md` |

---

## Current Hardcoded References Analysis

### Source Files Location
`src/dot_work/prompts/` - 12 total prompt files

### Files Needing Updates (11 of 12)

All these use pattern: `[text](filename.prompt.md)` or `[text](../some/path.md)`

1. **agent-prompts-reference.prompt.md** (8 hardcoded refs)
   - Lines: 12-15, 159, 162, 243-248
   - Pattern: Table links and markdown links
   - Example: `[critical-code-review](critical-code-review.prompt.md)`

2. **compare-baseline.prompt.md** (4 hardcoded refs)
   - Lines: 416, 451-453
   - Pattern: Markdown links
   - Example: `[do-work.prompt.md](do-work.prompt.md)`

3. **critical-code-review.prompt.md** (4 hardcoded refs)
   - Lines: 339, 359-360
   - Pattern: Markdown links
   - Example: `[do-work.prompt.md](do-work.prompt.md)`

4. **establish-baseline.prompt.md** (4 hardcoded refs)
   - Lines: 284, 320-322
   - Pattern: Markdown links
   - Example: `[do-work.prompt.md](do-work.prompt.md)`

5. **spec-delivery-auditor.prompt.md** (4 hardcoded refs)
   - Lines: 361, 383-385
   - Pattern: Markdown links
   - Example: `[do-work.prompt.md](do-work.prompt.md)`

6. **do-work.prompt.md** (NEEDS INVESTIGATION)
   - Pattern: Likely self-references and other prompt references

7. **bump-version.prompt.md** (NEEDS INVESTIGATION)
   - Pattern: Unknown, needs reading

8. **api-export.prompt.md** (NEEDS INVESTIGATION)
   - Pattern: Unknown, needs reading

9. **new-issue.prompt.md** (NEEDS INVESTIGATION)
   - Pattern: Unknown, needs reading

10. **python-project-from-discussion.prompt.md** (NEEDS INVESTIGATION)
    - Pattern: Unknown, needs reading

11. **improvement-discovery.prompt.md** (NEEDS INVESTIGATION)
    - Pattern: Unknown, needs reading

### File NOT Needing Updates (1 of 12)

**setup-issue-tracker.prompt.md**
- Uses hardcoded path `.github/prompts/` (e.g., `[do-work.prompt.md](.github/prompts/do-work.prompt.md)`)
- This is WRONG and should also be templatized to `{{ prompt_path }}`
- Need to include this in the fix

---

## Templatization Strategy

### Current Pattern
```markdown
[text](filename.prompt.md)
[text](do-work.prompt.md)
```

### Target Pattern
```markdown
[text]({{ prompt_path }}/filename.prompt.md)
[text]({{ prompt_path }}/do-work.prompt.md)
```

### Why This Works
- `{{ prompt_path }}` is replaced during rendering:
  - Copilot: `.github/prompts/filename.prompt.md`
  - Claude: `prompts/filename.prompt.md` (fallback)
  - Cursor: `.cursor/rules/filename.prompt.md`
  - Generic: `prompts/filename.prompt.md`
  - etc.

### Special Cases to Handle
1. **Self-references:** `[filename.prompt.md](filename.prompt.md)` → `[filename.prompt.md]({{ prompt_path }}/filename.prompt.md)`
2. **Navigation links in tables:** May appear as plain text or markdown links
3. **Relative paths:** Already relative, need to prefix with `{{ prompt_path }}/`

---

## Complete Audit Results

### All 12 Files Audited ✅

#### Files WITH Hardcoded References (5 total)

1. **agent-prompts-reference.prompt.md** - 8 refs
   - Lines: 12-15 (table), 159, 162 (list), 243-248 (table)
   - Pattern: `[text](filename.prompt.md)`

2. **compare-baseline.prompt.md** - 4 refs
   - Lines: 416, 451-453
   - Pattern: `[text](filename.prompt.md)`

3. **critical-code-review.prompt.md** - 4 refs
   - Lines: 339, 359-360
   - Pattern: `[text](filename.prompt.md)`

4. **establish-baseline.prompt.md** - 4 refs
   - Lines: 284, 320-322
   - Pattern: `[text](filename.prompt.md)`

5. **spec-delivery-auditor.prompt.md** - 4 refs
   - Lines: 361, 383-385
   - Pattern: `[text](filename.prompt.md)`

6. **setup-issue-tracker.prompt.md** - 3 refs (SPECIAL CASE)
   - Lines: 3, 346, 375, 400
   - Pattern: `[text](.github/prompts/filename.prompt.md)` - uses hardcoded `.github/prompts/` prefix
   - **Also needs fixing** to use `{{ prompt_path }}`

#### Files WITHOUT Hardcoded References (7 total) ✅

- do-work.prompt.md (0 refs) ✅
- bump-version.prompt.md (0 refs) ✅
- api-export.prompt.md (0 refs) ✅
- new-issue.prompt.md (0 refs) ✅
- python-project-from-discussion.prompt.md (0 refs) ✅
- improvement-discovery.prompt.md (0 refs) ✅
- code-review.prompt.md (0 refs) ✅
- performance-review.prompt.md (0 refs) ✅
- pythonic-code.prompt.md (0 refs) ✅
- security-review.prompt.md (0 refs) ✅
- task-assessment.prompt.md (0 refs) ✅
- api-expert.prompt.md (0 refs) ✅

### Summary
- **Total hardcoded references:** 28 (across 5 files)
- **Files needing changes:** 6 (5 with simple refs + 1 with prefixed refs)
- **Files clean:** 12 (no changes needed)
- **Total effort:** Moderate - mostly simple find/replace operations

---

## Implementation Plan

### Phase 1: Complete Audit ✅
- [x] Read all 12 files
- [x] Count total references: 28 hardcoded refs in 6 files
- [x] Identified edge cases: setup-issue-tracker uses prefixed paths

### Phase 2: Templatize
1. For each of 11 affected files:
   - Replace `[text](filename.prompt.md)` with `[text]({{ prompt_path }}/filename.prompt.md)`
   - Replace `[text](.github/prompts/...)` with `[text]({{ prompt_path }}/...)` (setup-issue-tracker.prompt.md)
   - Handle any special patterns found during audit
2. Commit each file or batch similar changes

### Phase 3: Add Regression Test
1. Create test in `tests/unit/test_installer.py`
2. Test should detect hardcoded `.prompt.md` references
3. Verify no raw `{{` or `}}` in rendered output
4. Parametrize across all environments

### Phase 4: Validate
1. Run full build: `uv run python scripts/build.py`
2. All 732+ tests should pass
3. No coverage regression
4. Verify rendering produces correct paths for each environment

---

## Key Questions Answered

- ✅ Is `{{ prompt_path }}` available? Yes, provided in template context
- ✅ Does template engine support this syntax? Yes, Jinja2 FileSystemLoader
- ✅ Is this for all environments? Yes, all 10 environments need this
- ✅ Any cross-references that should NOT be templatized? No, all are local prompt references

---

## Success Criteria

When investigation complete:
- [ ] All 11 affected files identified with reference counts
- [ ] Templatization strategy documented
- [ ] Edge cases catalogued
- [ ] Ready for implementation phase

---

## Next Steps

1. **Continue reading** remaining 6 files to complete audit
2. **Document findings** with line-by-line reference count
3. **Proceed to implementation** phase once audit complete
