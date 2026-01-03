# Backlog

Untriaged ideas and future work.

---

---
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

### Notes
- This is a future enhancement, not immediate priority
- Should wait until skills/subagents are stable and in use
- Consider starting with simple git-based approach
- Could leverage existing package managers (npm, pypi) as inspiration
- Estimated effort: 20-40 days (depending on scope)
- Dependencies: FEAT-023, FEAT-030, FEAT-031 must be complete

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
---

### Problem
The subagents specification (FEAT-030) initially supports Claude Code, OpenCode, and GitHub Copilot. Cursor and Windsurf are popular AI editors that also support custom agents but may have slightly different formats.

### Affected Files
- **New**: `src/dot_work/subagents/environments/cursor.py`
- **New**: `src/dot_work/subagents/environments/windsurf.py`

### Importance
Adding Cursor/Windsurf support:
- Covers more popular AI editors
- May share Copilot adapter (both VS Code-based)
- Completes coverage of major AI coding tools

### Proposed Solution
Investigate Cursor and Windsurf subagent formats:
1. Document their file formats and locations
2. Determine if Copilot adapter can be reused
3. If different, create separate adapters
4. Add to `environments:` frontmatter support

### Acceptance Criteria
- [ ] Cursor subagent format documented
- [ ] Windsurf subagent format documented
- [ ] Adapter implemented (new or shared with Copilot)
- [ ] CLI supports `--env cursor` and `--env windsurf`
- [ ] Tested with actual Cursor/Windsurf installations

### Notes
- Marked as future consideration in subagents spec
- May be simple if VS Code extension format is compatible
- Estimated effort: 2-4 days (if similar to Copilot)
- Dependencies: FEAT-030 must be complete

---
