# Gaps and Questions: dot-work

**Generated:** 2024-12-28
**Last Updated:** 2024-12-28 (post-review)

---

## Critical Gaps (Block Dogfooding)

### 1. `init` vs `init-work` Difference

**Context:** Both commands exist, purpose unclear
**Where discovered:** CLI help, baseline.md
**User feedback:** "Investigate and clarify the difference by looking at the implementation"

**Questions:**
- What does `init` do that `init-work` doesn't?
- Does `init` call `init-work` internally?
- When should I use one vs the other?

**Proposed doc addition:**
```markdown
## init vs init-work

- `dot-work init` – Install prompts + initialize .work/ (combined)
- `dot-work init-work` – Initialize .work/ only (prompts already installed)

Use `init` for new projects. Use `init-work` if you've already run `install`.
```

**Priority:** CRITICAL
**Status:** User requested implementation investigation

---

### 2. AI Prompt Commands vs CLI Commands

**Context:** Some commands are referenced in prompts but not in CLI help
**Where discovered:** setup-issue-tracker.prompt.md, do-work.prompt.md
**User feedback:**
- `generate-baseline`: "Should only be a slash command/prompt"
- `continue`, `status`, `focus on`: "Prompt instruction, but should be implemented as CLI command reading the prompt"

**Commands affected:**
| Command | Type | Should be | Action needed |
|---------|------|-----------|---------------|
| `generate-baseline` | AI prompt only | AI prompt only | ✓ Correct |
| `continue` | AI prompt only | CLI command | Implement CLI |
| `status` | AI prompt only | CLI command | Implement CLI |
| `focus on` | AI prompt only | CLI command | Implement CLI |

**Proposed implementation:**
```bash
# These should be implemented as CLI commands:
dot-work continue              # Read do-work prompt and execute
dot-work status                # Show focus.md + issue counts
dot-work focus-on <topic>      # Create issues in shortlist.md
```

**Priority:** HIGH (user explicitly requested)
**Status:** Feature request – "would be nice to have"

---

### 3. Non-Goals Not Explicitly Stated

**Context:** No section on what dot-work does NOT do
**Where discovered:** baseline.md analysis

**Questions:**
- What problems are out of scope?
- What won't dot-work help with?

**Proposed doc addition:**
```markdown
## Non-Goals

dot-work does NOT:

- Replace full project management tools (Jira, Linear, etc.)
- Provide team collaboration features
- Host prompts or provide cloud services
- Manage dependencies or build systems
- Replace git workflow tools
- Provide CI/CD integration

It is a local development tool for AI-assisted coding workflows.
```

**Priority:** MEDIUM
**Status:** Missing documentation

---

### 4. Priority File Editing

**Context:** How do users/edit-AI tools edit issues?
**Where discovered:** setup-issue-tracker.prompt.md
**User feedback:** "The tools and AI should edit the issue files, not humans"

**Questions:**
- Are there CLI commands to add/edit/move issues?
- Should humans ever edit `.work/agent/issues/*.md` directly?
- How to move issues between priority files?
- How to update issue status without AI?

**Proposed doc addition:**
```markdown
## Editing Issues

Issues are edited by AI agents via prompts:

- `/new-issue` – Create issue with generated ID
- `/do-work` – Move issue through workflow states
- `/focus on <topic>` – Create issues in shortlist.md

Direct file editing is NOT recommended. The AI manages issue state.
```

**Priority:** MEDIUM
**Status:** Clarification needed

---

## High-Priority Gaps

### 5. Review Storage Location

**Context:** `dot-work review` stores data somewhere
**Where discovered:** `review --help`

**Questions:**
- Where are reviews stored?
- What is the review ID format?
- How to list all reviews?

**Proposed doc addition:**
```markdown
## Review Storage

Reviews are stored in: `.work/reviews/`

Review ID format: `YYYYMMDD-HHMMSS` (timestamp)

## Listing reviews
dot-work review list  # (if this command exists)
```

**Priority:** HIGH
**Status:** Missing documentation

---

### 6. KG Database Location

**Context:** `dot-work kg` stores data in SQLite
**Where discovered:** docs/db-issues/

**Questions:**
- Where is the database stored?
- What is the schema?
- How to migrate/copy knowledge graphs?

**Proposed doc addition:**
```markdown
## Knowledge Graph Storage

Database location: `.work/kg/graph.db`

To back up:
cp .work/kg/graph.db backup/

To migrate:
dot-work kg export > backup.json
dot-work kg ingest --import backup.json  # (if supported)
```

**Priority:** HIGH
**Status:** Missing documentation

---

### 7. Migration: File-Based ↔ db-issues

**Context:** Two issue tracking systems exist
**Where discovered:** baseline.md
**User feedback:** "There should be an issue for making a unified interface for the issue handling with file-based, database or api as optional, pluggable storage options"

**Questions:**
- How to migrate from file-based to db-issues?
- Can both systems coexist?
- Which one should I use?

**Proposed doc addition:**
```markdown
## Issue Tracking Options

dot-work provides two issue tracking systems:

**File-based (.work/agent/issues/)**
- Use for: AI-driven workflows, git-tracked issues
- Best for: Individual developers, AI-heavy workflows
- Migrate to db-issues: (command not documented)

**db-issues (.work/db-issues/issues.db)**
- Use for: Complex queries, relational data
- Best for: Teams, complex dependencies, epics
- Migrate from file-based: (command not documented)

## Migration

# File-based → db-issues (if supported)
dot-work db-issues import --from-files .work/agent/issues/

# db-issues → File-based (if supported)
dot-work db-issues export --to-files .work/agent/issues/
```

**Priority:** HIGH
**Status:** User requested unified interface issue be created

---

### 8. Canonical Prompt Validation

**Context:** How to validate .canon.md without installing?
**Where discovered:** docs/prompt-authoring.md

**Questions:**
- Is there a `validate` command for canonical prompts?
- What validation is performed?

**Proposed doc addition:**
```markdown
## Validating Canonical Prompts

# Validate without installing
dot-work canonical validate my-prompt.canon.md

# Or check during install
dot-work prompts install my-prompt.canon.md --target copilot --dry-run
```

**Priority:** MEDIUM
**Status:** Not documented

---

## Medium-Priority Gaps

### 9. Prompt Trigger Format

**Context:** How to use prompts after install?
**Where discovered:** README.md

**Questions:**
- Are all prompts slash commands?
- How does Claude Code use prompts (no slash commands)?

**Proposed doc addition:**
```markdown
## Using Installed Prompts

| Environment | How to Use |
|-------------|------------|
| GitHub Copilot | Type `/prompt-name` in chat |
| Claude Code | Automatically reads CLAUDE.md |
| Cursor | Select from `@` menu |
| Windsurf | Automatically reads .windsurf/rules/ |
| Aider | Automatically reads CONVENTIONS.md |
| Continue.dev | Type `/prompt-name` |
| Amazon Q | Automatically reads .amazonq/rules.md |
| Zed AI | Select from prompts menu |
| OpenCode | Automatically reads AGENTS.md |
| Generic | Manually reference prompt files |
```

**Priority:** MEDIUM
**Status:** Partially documented

---

### 10. Undocumented Commands

**Context:** Some commands in `--help` have no documentation
**Where discovered:** main `--help` output

**Commands needing docs:**
| Command | Description | Priority |
|---------|-------------|----------|
| `canonical` | Validate/install canonical prompts | HIGH |
| `zip` | Zip folders respecting .gitignore | LOW |
| `container` | Container operations | MEDIUM |
| `python` | Python utilities | MEDIUM |
| `git` | Git analysis tools | MEDIUM |
| `harness` | Claude Agent SDK harness | LOW |

**Priority:** MEDIUM
**Status:** Missing documentation

---

### 11. Version Format Conventions

**Context:** `dot-work version` uses date-based format
**Where discovered:** `version init --help`

**Questions:**
- What is the version format?
- Why date-based instead of semantic?

**Proposed doc addition:**
```markdown
## Version Format

dot-work uses date-based versioning: `YYYY.MM.PATCH`

Example: `2025.10.001`
- `2025` – Year
- `10` – Month (October)
- `001` – Patch/sequence

This format aligns with CalVer (Calendar Versioning).
```

**Priority:** LOW
**Status:** Missing documentation

---

### 12. Integration Testing

**Context:** How to verify prompts work across AI tools?
**Where discovered:** baseline.md

**Questions:**
- How to test if prompts are installed correctly?
- How to test if AI tools use prompts correctly?

**Proposed doc addition:**
```markdown
## Testing Installation

# Verify files exist
ls -la .github/prompts/  # Copilot
ls -la CLAUDE.md         # Claude

# Test with AI tool
# In GitHub Copilot: Type /agent-prompts-reference
# Should see list of available prompts
```

**Priority:** LOW
**Status:** Missing documentation
**User feedback:** "Requires human validation"

---

### 13. Changelog Format

**Context:** `dot-work version freeze` generates changelog
**Where discovered:** `version --help`

**Questions:**
- What is the changelog format?
- Where is it stored?
- How to customize?

**Proposed doc addition:**
```markdown
## Changelog Format

The changelog is generated in Keep a Changelog format:

# Changelog

## [2025.10.001] - 2025-10-15
### Added
- New feature X

### Fixed
- Bug Y

## [2025.09.003] - 2025-09-30
...
```

**Priority:** LOW
**Status:** Missing documentation

---

### 14. Environment Detection Signals

**Context:** `dot-work detect` identifies AI tool
**Where discovered:** `detect --help`

**Questions:**
- What files/signals are checked?
- What if multiple environments detected?
- What if none detected?

**Proposed doc addition:**
```markdown
## Detection Logic

dot-work detect checks for:

| Environment | Detection Signal |
|-------------|------------------|
| copilot | `.github/prompts/` or `.github/copilot-instructions.md` |
| claude | `CLAUDE.md` or `.claude/` |
| cursor | `.cursor/rules/` or `.cursorrules` |
| windsurf | `.windsurf/rules/` or `.windsurfrules` |
| aider | `.aider/` or `CONVENTIONS.md` |
| continue | `.continue/prompts/` |
| amazon-q | `.amazonq/rules.md` |
| zed | `.zed/prompts/` |
| opencode | `.opencode/prompts/` or `AGENTS.md` |

If multiple detected, uses first match.
If none detected, prompts user to select.
```

**Priority:** LOW
**Status:** Missing documentation

---

### 15. Delete/Uninstall Prompts

**Context:** How to remove installed prompts?
**Where discovered:** feature-inventory.md

**Questions:**
- Is there an uninstall command?
- How to remove specific prompts?
- How to remove all prompts?

**Proposed doc addition:**
```markdown
## Uninstalling Prompts

# Remove specific environment
rm .github/prompts/*.prompt.md  # Copilot
rm CLAUDE.md                    # Claude

# Or use uninstall command (if exists)
dot-work uninstall --env copilot
dot-work uninstall --all
```

**Priority:** LOW
**Status:** Not documented

---

## Feature Requests (from user review)

### FR-1: Unified Issue Interface

**Description:** "Unified interface for issue handling with file-based, database or api as optional, pluggable storage options"

**Proposed design:**
```bash
dot-work issues create "Fix bug" --storage file
dot-work issues create "Fix bug" --storage db
dot-work issues create "Fix bug" --storage api

# Config file: .work/config.yaml
storage:
  type: file  # or db, or api
  options:
    path: .work/agent/issues
```

**Priority:** HIGH (user requested)
**Status:** Needs issue to be created

---

## Summary Statistics

| Priority | Count | Status |
|----------|-------|--------|
| CRITICAL | 1 | Implementation investigation needed |
| HIGH | 6 | Documentation + 1 feature request |
| MEDIUM | 5 | Documentation |
| LOW | 5 | Documentation |

**Total gaps:** 17
**Feature requests:** 1

---

## Next Steps

1. **Immediate:**
   - [ ] Investigate `init` vs `init-work` implementation
   - [ ] Document issue editing workflow (AI-only)
   - [ ] Add review storage location to docs

2. **Short-term:**
   - [ ] Implement `continue`, `status`, `focus-on` as CLI commands
   - [ ] Document migration path between issue systems
   - [ ] Add kg database location to docs
   - [ ] Document all undocumented commands

3. **Long-term:**
   - [ ] Design unified issue interface (create issue)
   - [ ] Add non-goals section to main docs
   - [ ] Create integration testing guide
