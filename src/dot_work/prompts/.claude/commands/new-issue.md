---
meta:
  title: "Create New Issue"
  description: "This prompt creates a properly formatted issue in the file-based issue tracking system"
  version: "0.1.1"
---
---

This prompt creates a properly formatted issue in the file-based issue tracking system.

**MANDATORY RULE** : Always do an investigation to flesh out the new issue details, then create the issue in the correct format and location, BEFORE doing ANY other changes. If nothing else is said, your ONLY TASK is to create the issue, not do any fixes.

---

## 📋 Issue Schema

Every issue MUST include YAML frontmatter with these fields:

```yaml
---
id: "<TYPE>-<NUM>@<HASH>"    # e.g., "BUG-003@a9f3c2", "FEAT-012@b2c3d4"
title: "Short descriptive title"
description: "One-line summary of the issue"
created: YYYY-MM-DD
section: "affected-area"      # e.g., "cli", "installer", "tests", "docs"
tags: [tag1, tag2, tag3]      # relevant keywords
type: bug|enhancement|refactor|test|docs|security
priority: critical|high|medium|low
status: proposed|in-progress|blocked|completed
references:                   # files related to this issue
  - path/to/file1.py
  - path/to/file2.py
---
```

### ID Format

Generate IDs as: `<TYPE>-<NUM>@<SHORT_HASH>`

| Type | Prefix | Example |
|------|--------|---------|
| Bug fix | BUG | BUG-003@a9f3c2 |
| Feature | FEAT | FEAT-012@b2c3d4 |
| Refactor | REFACTOR | REFACTOR-001@c3d4e5 |
| Test | TEST | TEST-005@d4e5f6 |
| Documentation | DOCS | DOCS-002@e5f6a7 |
| Security | SEC | SEC-001@f6a7b8 |

- `<NUM>`: Sequential number (check existing issues to avoid duplicates)
- `<SHORT_HASH>`: 6-character random hex string for uniqueness

---

## 📝 Issue Body Template

After the frontmatter, include these sections:

```markdown
### Problem
Clear description of what's wrong or what's needed.
Include specific symptoms, error messages, or gaps.

### Affected Files
- `path/to/file.py` (brief note about what's affected)
- `path/to/another.py` (line numbers if known)

### Importance
Why this matters. Impact on users, quality, or development.

### Proposed Solution
1. Step-by-step approach
2. Key changes needed
3. Dependencies or prerequisites

### Acceptance Criteria
- [ ] Specific, testable outcome 1
- [ ] Specific, testable outcome 2
- [ ] Tests verify the fix/feature
- [ ] Documentation updated (if applicable)

### Notes
Optional: additional context, related issues, warnings, or constraints.
```

---

## 📁 File Destinations

Place issues in the appropriate priority file:

| Priority | File | Criteria |
|----------|------|----------|
| **P0 Critical** | `.work/agent/issues/critical.md` | System broken, security issues, data loss |
| **P1 High** | `.work/agent/issues/high.md` | Core functionality broken or missing |
| **P2 Medium** | `.work/agent/issues/medium.md` | Important improvements, quality issues |
| **P3 Low** | `.work/agent/issues/low.md` | Nice-to-have, minor improvements |
| **Backlog** | `.work/agent/issues/backlog.md` | Future work, not yet prioritized |
| **User Priority** | `.work/agent/issues/shortlist.md` | User-specified priority (always checked first) |

---

## 🔄 Workflow Integration

After creating an issue:

1. **Report to user**: Confirm creation with ID and destination file
2. **Update focus.md**: If this should be next, update the "Next" section
3. **Link related issues**: If this blocks or is blocked by other issues, note it

---

## 📊 Example: Complete Issue

```markdown
---
id: "BUG-007@f2a3b4"
title: "Config file not found error on Windows with spaces in path"
description: "Windows paths with spaces fail to load config"
created: 2024-12-20
section: "config"
tags: [windows, paths, bug, cross-platform]
type: bug
priority: high
status: proposed
references:
  - src/dot_work/config.py
  - tests/unit/test_config.py
---

### Problem
When the project directory path contains spaces (e.g., `C:\Users\John Doe\Projects\`), 
the config loader fails with `FileNotFoundError`. This only affects Windows.

Error message:
```
FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\John'
```

### Affected Files
- `src/dot_work/config.py` (line 45: path string splitting)
- `tests/unit/test_config.py` (needs Windows path test cases)

### Importance
Windows users with spaces in usernames cannot use the tool. This affects a 
significant portion of Windows installations (default user folders have spaces).

### Proposed Solution
1. Replace string-based path handling with `pathlib.Path`
2. Use `shlex.quote()` for any shell operations
3. Add test cases with spaces in paths
4. Test on Windows CI if available

### Acceptance Criteria
- [ ] Config loads from paths with spaces on Windows
- [ ] Config loads from paths with spaces on Linux/macOS
- [ ] Tests cover space-in-path scenarios
- [ ] No regression in normal path handling

### Notes
Related to pathlib standardization effort. Consider auditing other path 
operations in the codebase.
```

---

## ⚡ Quick Issue (Minimal Format)

For simple issues, a minimal format is acceptable:

```markdown
---
id: "BUG-008@a1b2c3"
title: "Fix typo in error message"
description: "Misspelled 'configuration' in CLI output"
created: 2024-12-20
section: "cli"
tags: [typo, cli]
type: bug
priority: low
status: proposed
references:
  - src/dot_work/cli.py
---

### Problem
Error message says "configration" instead of "configuration" at cli.py:234.

### Acceptance Criteria
- [ ] Typo fixed
- [ ] No other typos in nearby messages
```

---

## 🚫 Anti-Patterns

| Don't | Do |
|-------|-----|
| Vague titles: "Fix bug" | Specific: "Fix null pointer in user auth" |
| Missing acceptance criteria | Always include testable outcomes |
| No file references | List affected files with line numbers |
| Duplicate IDs | Check existing issues before creating |
| Wrong priority file | Match priority to impact/urgency |
| Skip the frontmatter | YAML frontmatter is required |

---

## 🎯 Usage

When the user says something like:
- "Create an issue for X"
- "Log this bug"
- "Add to backlog: feature Y"
- "Track this: Z is broken"

1. Gather details (ask if needed)
2. Generate proper ID (check for duplicates)
3. Write issue with full schema
4. Place in correct priority file
5. Report creation to user
6. Update focus.md if appropriate
