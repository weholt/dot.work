# Medium Priority Issues (P2)

Enhancements, technical debt.

---


---
id: "FEAT-006@e6c3f9"
title: "Add Cline and Cody environments"
description: "Popular AI coding tools not currently supported"
created: 2024-12-20
section: "environments"
tags: [environments, cline, cody]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/environments.py
  - src/dot_work/installer.py
---

### Problem
Cline (VS Code extension) and Cody (Sourcegraph) are popular AI coding assistants not currently supported by dot-work.

### Affected Files
- `src/dot_work/environments.py` (add environment configs)
- `src/dot_work/installer.py` (add installer functions)

### Importance
Users of these tools cannot use dot-work to install prompts, limiting adoption.

### Proposed Solution
1. Research Cline and Cody prompt/rules file conventions:
   - Cline: likely `.cline/` or similar
   - Cody: likely `.cody/` or `.sourcegraph/`
2. Add Environment entries with appropriate detection markers
3. Add `install_for_cline()` and `install_for_cody()` functions
4. Add to INSTALLERS dispatch table
5. Add tests for new environments

### Acceptance Criteria
- [ ] `dot-work list` shows cline and cody environments
- [ ] `dot-work install --env cline` creates correct structure
- [ ] `dot-work install --env cody` creates correct structure
- [ ] `dot-work detect` recognizes cline/cody markers
- [ ] Tests cover new installer functions

### Notes
May need to verify exact conventions by checking official documentation or popular repos using these tools.

---

---
id: "REFACTOR-001@f7d4a1"
title: "Extract common installer logic to reduce duplication"
description: "10 install_for_* functions share ~80% identical code"
created: 2024-12-20
section: "installer"
tags: [refactor, dry, maintainability]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/installer.py
---

### Problem
The 10 `install_for_*` functions in installer.py contain ~200 lines of repetitive code. Each function:
1. Creates destination directory
2. Gets environment config
3. Iterates prompts, renders, writes
4. Prints status messages

Adding a new environment requires copying ~20 lines of near-duplicate code.

### Affected Files
- `src/dot_work/installer.py`

### Importance
Violates DRY principle. Bug fixes must be applied to 10 places. Adding new environments is error-prone. The `force` flag implementation will need to be duplicated 10 times without this refactor.

### Proposed Solution
1. Create generic `install_prompts_generic()` function
2. Define environment-specific behavior via configuration:
   - Destination path pattern
   - Whether to create auxiliary files (.cursorrules, etc.)
   - Auxiliary file content template
   - Console messaging
3. Keep simple dispatch: `INSTALLERS[env_key] = lambda: install_prompts_generic(config)`
4. Special cases (claude, aider combining into single file) handled via config flag

### Acceptance Criteria
- [ ] Single generic installer function handles all environments
- [ ] No more than 5 lines of environment-specific code per environment
- [ ] All existing tests pass
- [ ] Adding new environment requires only config, not code
- [ ] `force` flag implemented in one place

### Notes
Do this AFTER implementing the force flag to avoid conflicts. Consider config-as-data pattern using dataclass or dict.

---

---
id: "FEAT-007@a8e5b2"
title: "Add --dry-run flag to install command"
description: "Allow previewing changes before writing files"
created: 2024-12-20
section: "cli"
tags: [cli, install, ux]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/cli.py
  - src/dot_work/installer.py
---

### Problem
Users cannot preview what files will be created or modified before running `dot-work install`. This makes it difficult to understand the impact of installation, especially when files might be overwritten.

### Affected Files
- `src/dot_work/cli.py` (add --dry-run option)
- `src/dot_work/installer.py` (add dry_run parameter)

### Importance
Improves user confidence and reduces surprises. Useful for CI/CD integration where destructive changes should be previewed.

### Proposed Solution
1. Add `--dry-run` / `-n` flag to install command
2. Pass through to installer functions
3. When dry_run=True:
   - Print what would be created/modified
   - Show file paths and whether new/overwrite
   - Do not write any files
4. Output format: `[CREATE] .github/prompts/do-work.prompt.md` or `[OVERWRITE] .github/prompts/do-work.prompt.md`

### Acceptance Criteria
- [ ] `dot-work install --dry-run` shows planned changes without writing
- [ ] Output distinguishes between new files and overwrites
- [ ] Exit code 0 even in dry-run mode
- [ ] Tests verify no files written in dry-run mode

### Notes
Implement after force flag and ideally after refactor to avoid duplication.

---

---
id: "FEAT-008@f7d4a2"
title: "Add batch overwrite option when files exist during install"
description: "Provide 'overwrite all' choice instead of only file-by-file prompting"
created: 2024-12-20
section: "cli"
tags: [cli, install, ux, prompting]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/cli.py
  - src/dot_work/installer.py
---

### Problem
When running `dot-work install` without `--force` and files already exist, the user is prompted for each file individually. For projects with many prompt files (8+), this becomes tedious.

Current behavior:
```
  ⚠ File already exists: do-work.prompt.md
    Overwrite? [y/N]: y
  ⚠ File already exists: setup-issue-tracker.prompt.md
    Overwrite? [y/N]: y
  ... (repeated for each file)
```

### Affected Files
- `src/dot_work/installer.py` (modify `should_write_file()` and install functions)
- `src/dot_work/cli.py` (potentially add `--update-all` flag)
- `tests/unit/test_installer.py` (add tests for batch behavior)

### Importance
User experience improvement. Power users reinstalling/updating prompts shouldn't need to answer the same question 8+ times. This is especially painful when updating to a new version of dot-work.

### Proposed Solution
1. When first existing file is encountered, offer expanded choices:
   ```
   ⚠ Found existing prompt files. How should I proceed?
     [a] Overwrite ALL existing files
     [s] Skip ALL existing files
     [p] Prompt for each file individually
     [c] Cancel installation
   Choice [a/s/p/c]:
   ```
2. Store user's choice for the session
3. Apply consistently to remaining files
4. Alternative: Add `--update-all` / `--skip-existing` CLI flags

### Acceptance Criteria
- [ ] First conflict offers batch choice (all/skip/prompt/cancel)
- [ ] Choice "a" overwrites all remaining without further prompts
- [ ] Choice "s" skips all existing files without further prompts
- [ ] Choice "p" maintains current file-by-file behavior
- [ ] Choice "c" aborts installation cleanly
- [ ] `--force` still works as before (silent overwrite all)
- [ ] Tests verify each batch mode behavior

### Notes
Consider interaction with `--force` flag:
- `--force` = silent overwrite (no prompts at all)
- No flag + batch "a" = overwrite after single confirmation
- No flag + batch "p" = current behavior

This builds on FEAT-003 (--force implementation). Could be combined with FEAT-007 (--dry-run) for a complete UX.

---
id: "RECONCILE-001@a1b2c3"
title: "Reconcile enum schemas between old and new issue-tracker"
description: "Differences between migrated enums and original issue-tracker spec need resolution"
created: 2024-12-23
section: "db-issues"
tags: [db-issues, enums, reconciliation, migration]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/domain/entities.py
  - .work/agent/issues/references/MIGRATE-034-investigation.md
---

### Problem
MIGRATE-041 updated enum values to match the issue-tracker project specification, but this introduced breaking changes from the original "Beads-compatible" schema that was initially migrated in MIGRATE-034.

Key differences:

**IssueStatus:**
- Old: OPEN, IN_PROGRESS, BLOCKED, RESOLVED, CLOSED, ARCHIVED
- New: PROPOSED, IN_PROGRESS, BLOCKED, COMPLETED, WONT_FIX
- Missing: RESOLVED, CLOSED, ARCHIVED
- Added: PROPOSED, WONT_FIX
- Mapping: OPEN→PROPOSED, RESOLVED→COMPLETED, CLOSED→COMPLETED (merge)

**IssueType:**
- Old: TASK, BUG, FEATURE, EPIC, CHORE
- New: BUG, FEATURE, TASK, ENHANCEMENT, REFACTOR, DOCS, TEST, SECURITY, PERFORMANCE
- Missing: EPIC, CHORE
- Added: ENHANCEMENT, REFACTOR, DOCS, TEST, SECURITY, PERFORMANCE
- Mapping: TASK→TASK, BUG→BUG, FEATURE→FEATURE, EPIC→removed, CHORE→removed

**DependencyType:**
- Old: BLOCKS, DEPENDS_ON, RELATED_TO, DISCOVERED_FROM
- New: BLOCKS, DEPENDS_ON, RELATED_TO, DUPLICATES, PARENT_OF, CHILD_OF
- Missing: DISCOVERED_FROM
- Added: DUPLICATES, PARENT_OF, CHILD_OF

**IssuePriority:**
- Old: CRITICAL, HIGH, MEDIUM, LOW, BACKLOG (5 values)
- New: CRITICAL, HIGH, MEDIUM, LOW (4 values)
- Removed: BACKLOG

### Affected Files
- `src/dot_work/db_issues/domain/entities.py` (enum definitions)
- `src/dot_work/db_issues/services/issue_service.py` (EPIC type removed, include_children disabled)
- All test files (updated to new enum values)

### Importance
The enum changes break backward compatibility with any code using the old schema. However, MIGRATE-041 explicitly chose to use the issue-tracker project's enum values for compatibility with the source.

Key concerns:
1. **Epic hierarchy** - The `IssueType.EPIC` was removed, breaking the `include_children` functionality in `get_epic_issues()`
2. **Status transitions** - `RESOLVED` vs `COMPLETED` semantic difference needs clarification
3. **Missing types** - `EPIC` and `CHORE` types from old schema are gone
4. **Priority** - `BACKLOG` priority removed

### Proposed Solution
**Option A: Support both schemas (recommended)**
1. Keep new enum values as primary (issue-tracker spec)
2. Add aliases/compatibility layer for old values
3. Restore EPIC support as a separate `IssueEntity` concept (not a type)

**Option B: Document breaking changes**
1. Keep new enum values as-is
2. Document migration path for users of old schema
3. Accept that EPIC hierarchy is removed

**Option C: Merge both schemas**
1. Add missing old values to new enums
2. Keep all values: both PROPOSED and OPEN, both COMPLETED and RESOLVED
3. Restore EPIC as a type

### Acceptance Criteria
- [ ] Decision made on which approach to take
- [ ] If Option A: Compatibility layer implemented
- [ ] If Option B: Migration documentation written
- [ ] If Option C: Enums expanded with union of both value sets
- [ ] Epic functionality restored if needed
- [ ] Tests updated to reflect final decision
- [ ] Memory.md updated with resolution

### Notes
This should be resolved before MIGRATE-085 (DB-Issues Integration) to avoid further compounding the issue.

The `include_children` functionality in `get_epic_issues()` was disabled in MIGRATE-041 because `IssueType.EPIC` no longer exists. This needs to be resolved either by:
- Restoring EPIC as a type
- Implementing epic hierarchy via the `Epic` entity (which still exists)
- Removing the feature entirely

---

