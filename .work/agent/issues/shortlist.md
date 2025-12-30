# Shortlist (User-Directed Priority)

This file represents **explicit user intent**. Agent may only modify when explicitly instructed.

---

## Active Work

---

### New Issues (2025-12-30)

---
id: "ENH-025@4a8f2c"
title: "Global YAML frontmatter configuration for prompts"
description: "Create global.yml for default frontmatter values with per-prompt override capability"
created: 2025-12-30
section: "prompts"
tags: [enhancement, prompts, configuration, yaml-frontmatter]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/prompts/global.yml
  - src/dot_work/prompts/canonical.py
  - src/dot_work/installer.py
---

### Problem
Currently, each prompt file in `src/dot_work/prompts/` has its own YAML frontmatter configuration. This results in duplication and makes it difficult to maintain consistent settings across all prompts.

**Current state:**
- Each `.prompt.md` file has its own YAML frontmatter
- Common values (like `id_prefix`, `extension`, etc.) are duplicated
- Changes to shared defaults require updating every file

### Affected Files
- `src/dot_work/prompts/*.prompt.md` (21 prompt files)
- `src/dot_work/prompts/canonical.py` (parser logic)
- `src/dot_work/installer.py` (installation logic)

### Importance
**MEDIUM**: Global configuration improves maintainability:
- Single source of truth for default values
- Reduces duplication across prompt files
- Easier to maintain consistent settings
- Allows per-prompt customization when needed

### Proposed Solution

1. **Create `src/dot_work/prompts/global.yml`**
   - Define default YAML frontmatter values
   - Common settings like `id_prefix`, `extension`, default environment configs

2. **Modify `canonical.py` parser**
   - Load global.yml at startup
   - Merge global frontmatter with each prompt's frontmatter
   - Local values override global values (deep merge)

3. **Update installer.py**
   - Read global configuration when installing prompts
   - Apply merged frontmatter during installation

**Example global.yml:**
```yaml
# Default frontmatter for all prompts
defaults:
  id_prefix: "prompt"
  extension: ".md"
  environments:
    - copilot
    - claude
    - cursor
    - windsurf
```

**Example prompt with local override:**
```yaml
---
# Inherits from global.yml, but overrides extension
extension: ".prompt.md"
---
```

### Acceptance Criteria
- [ ] `src/dot_work/prompts/global.yml` created with default values
- [ ] `canonical.py` loads and merges global.yml with prompt frontmatter
- [ ] Local prompt values override global values (deep merge)
- [ ] All existing prompts work without modification
- [ ] Installer uses merged configuration
- [ ] Tests for merge behavior (global + local override)

### Notes
- Deep merge strategy: local values completely override global for same keys
- Consider adding `!reset` or `!clear` syntax if needed
- Global config should be optional (fall back to current behavior if missing)

---

---
id: "ENH-026@5b9g3d"
title: "Rename .prompt.md files to .md"
description: "Remove .prompt.md suffix, update installer and documentation references"
created: 2025-12-30
section: "prompts"
tags: [enhancement, refactoring, file-naming, prompts]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/prompts/*.prompt.md
  - src/dot_work/installer.py
  - src/dot_work/environments.py
  - src/dot_work/prompts/canonical.py
  - src/dot_work/prompts/wizard.py
---

### Problem
Prompt files use `.prompt.md` extension which is redundant since they live in a `prompts/` directory. The `.prompt` suffix adds unnecessary verbosity to filenames and references.

**Current state:**
- 21 prompt files with `.prompt.md` extension
- Code references to `.prompt.md` pattern throughout codebase
- Longer filenames than necessary

### Affected Files
- `src/dot_work/prompts/*.prompt.md` (21 files to rename)
- `src/dot_work/installer.py` (glob patterns, file discovery)
- `src/dot_work/environments.py` (pattern references)
- `src/dot_work/prompts/canonical.py` (file reading)
- `src/dot_work/prompts/wizard.py` (file references)
- Documentation files referencing `.prompt.md`

### Importance
**LOW**: Simplification and cleanup:
- Shorter, cleaner filenames
- Redundant `.prompt` suffix removed (directory already indicates type)
- Consistent with markdown convention (`.md` extension)
- Easier to reference files in code

### Proposed Solution

1. **Rename all `.prompt.md` files to `.md`**
   ```bash
   agent-prompts-reference.prompt.md → agent-prompts-reference.md
   api-export.prompt.md → api-export.md
   # ... (21 files total)
   ```

2. **Update installer.py**
   - Change glob patterns from `*.prompt.md` to `*.md`
   - Update `get_prompts_dir()` logic

3. **Update environments.py**
   - Change pattern references for prompt discovery

4. **Update canonical.py and wizard.py**
   - Change file extension references

5. **Update documentation**
   - Update any docs referencing `.prompt.md` format

### Acceptance Criteria
- [ ] All 21 `.prompt.md` files renamed to `.md`
- [ ] `installer.py` uses `*.md` pattern for prompt discovery
- [ ] `environments.py` updated for new pattern
- [ ] `canonical.py` and `wizard.py` updated
- [ ] Documentation references updated
- [ ] Tests pass with new filenames
- [ ] No broken references to old `.prompt.md` files

### Notes
- This is a pure refactoring - no behavior changes
- Consider doing this after ENH-025 (global config) to avoid conflicts
- Git mv should preserve history if done carefully
- May need to update templates in `src/dot_work/db_issues/templates/`

All previous shortlist items have been addressed. See Completed Items section below.

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
