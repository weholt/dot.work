id: "FEAT-099@d4e5f6"
title: "Skills and Subagents marketplace/registry"
description: "Create a community registry for sharing skills and subagents with search, install, and version management"
created: 2026-01-03
section: "ecosystem"
tags: [marketplace, registry, skills, subagents, community, future]
type: enhancement
priority: low
status: proposed
references:
  - src/dot_work/marketplace/ (potential new module)
  - src/dot_work/cli.py (add marketplace commands)
---

### Problem
After implementing skills and subagents, users will want to share their creations with the community. Currently there's no central way to discover, install, and update community-contributed skills and subagents.

### Affected Files
- **Potential new**: `src/dot_work/marketplace/` module
- **Modify**: `src/dot_work/cli.py` (add marketplace commands)

### Importance
A marketplace/registry enables:
- Community contribution and sharing
- Discovery of useful skills/subagents
- Version management and updates
- Quality ratings and reviews
- Reduced duplication of effort

### Proposed Solution

**Future Considerations (from subagents spec):**
1. **Subagent Marketplace**: Registry of community subagents
2. **Skills Registry**: Central repository for skills
3. **Version Management**: Track versions across environments
4. **Metrics/Analytics**: Track usage and effectiveness
5. **Quality Assurance**: Validation, testing, ratings

**Implementation approaches:**
- Simple: Git-based registry (GitHub organization with repos)
- Medium: JSON index with HTTP fetching
- Complex: Full marketplace backend with API, auth, reviews

**CLI commands:**
```bash
dot-work marketplace search <query>
dot-work marketplace install <skill|subagent> [--version]
dot-work marketplace publish <path>
dot-work marketplace list [--installed]
dot-work marketplace update [name]
dot-work marketplace info <name>
```

### Acceptance Criteria
- [ ] Marketplace architecture designed
- [ ] Search functionality working
- [ ] Install from registry working
- [ ] Publish/submit process defined
- [ ] Version management implemented
- [ ] Documentation for contributors

### Validation Plan
**Deferred** - This is a future enhancement. Validation plan to be determined when implementation begins.

### Dependencies
**Blocked by:** FEAT-023, FEAT-030, FEAT-031 must be complete (skills/subagents infrastructure must be stable first).

### Clarifications Needed
**User decision required:**
1. Which implementation approach to pursue (git-based vs JSON index vs full marketplace)?
2. Should this be hosted or self-hosted?
3. What authentication/authorization model for publishing?

### Notes
This is a future enhancement, not immediate priority. Should wait until skills/subagents are stable and in use. Consider starting with simple git-based approach. Could leverage existing package managers (npm, pypi) as inspiration. Estimated effort: 20-40 days (depending on scope).

---
---
id: "FEAT-100@e5f6a7"
title: "Cursor/Windsurf subagent support"
description: "Add subagent support for Cursor and Windsurf AI editors (both use VS Code extension format)"
created: 2026-01-03
section: "subagents"
tags: [subagents, cursor, windsurf, vscode, future]
type: enhancement
priority: low
status: proposed
references:
  - src/dot_work/subagents/environments/ (add cursor.py, windsurf.py)
  - src/dot_work/subagents/adapter.py (may need updates)
---

### Problem
The subagents specification (FEAT-030) initially supports Claude Code, OpenCode, and GitHub Copilot. Cursor and Windsurf are popular AI editors that also support custom agents but may have slightly different formats.

### Affected Files
- **New**: `src/dot_work/subagents/environments/cursor.py`
- **New**: `src/dot_work/subagents/environments/windsurf.py`
- `src/dot_work/subagents/adapter.py` (may need updates for shared code)
- `src/dot_work/subagents/__init__.py` (register new environments)
- Tests for new adapters

### Importance
Adding Cursor/Windsurf support:
- Covers more popular AI editors
- May share Copilot adapter (both VS Code-based)
- Completes coverage of major AI coding tools

### Proposed Solution
Investigate Cursor and Windsurf subagent formats:
1. ~~Document their file formats and locations~~ ✅ **RESEARCH COMPLETE**
2. Determine if Copilot adapter can be reused ~~→ ❌ Cannot reuse (different formats)~~
3. If different, create separate adapters
4. Add to `environments:` frontmatter support

**Research completed:**
- Cursor: `.cursor/rules/*.mdc` format with frontmatter (description, globs)
- Windsurf: `AGENTS.md` plain markdown (no frontmatter)
- Copilot adapter: ❌ **NOT compatible** - different frontmatter structures
- See `.work/agent/issues/references/FEAT-100-research.md` for details

**Next steps (awaiting user decision on priority):**
1. Create `CursorAdapter` for `.cursor/rules/*.mdc` format
2. Create `WindsurfAdapter` for `AGENTS.md` format
3. Register environments in `subagents/__init__.py`
4. Add CLI support for `--env cursor` and `--env windsurf`
5. Write tests

### Acceptance Criteria
- [x] Cursor subagent format documented → `.cursor/rules/*.mdc` with frontmatter
- [x] Windsurf subagent format documented → `AGENTS.md` plain markdown
- [x] Adapter approach determined → Separate adapters required (Copilot incompatible)
- [ ] Implement CursorAdapter class
- [ ] Implement WindsurfAdapter class
- [ ] CLI supports `--env cursor` and `--env windsurf`
- [ ] Tested with actual Cursor/Windsurf installations

### Validation Plan
**Deferred** - Requires research into Cursor/Windsurf formats first. Validation plan to be determined after research phase.

### Dependencies
**Blocked by:** FEAT-030 must be complete (subagent infrastructure).

### Clarifications Needed
**User decision required:**
1. Is Cursor/Windsurf support a priority for the near term?
2. Should we validate the VS Code extension format assumption before implementation?

### Notes
Marked as future consideration in subagents spec. May be simple if VS Code extension format is compatible. Estimated effort: 2-4 days (if similar to Copilot).

---
