## IDEA-019: Automated Version Management

---
id: "IDEA-019"
title: "Semantic Version Management System"
description: "Automated versioning with changelog generation"
created: 2025-10-13
section: build-system
tags: [versioning, automation, changelog, git, semver]
type: enhancement
priority: medium
status: proposed
references: build.py
---

Add automated version management to `build.py` with changelog generation and git tagging.

**Version Format:** `YYYY.MM.build-number`
Example: `2025.10.00004` (4th build in October 2025)

**Implementation:**

1. **Version File:**
```json
{
  "version": "2025.10.00004",
  "build_date": "2025-10-13T14:30:00Z",
  "git_commit": "abc123...",
  "previous_version": "2025.10.00003"
}
```

2. **Build Command:**
```bash
uv run python build.py --version-freeze

# What it does:
# 1. Read current version from version.json
# 2. Increment build number (or reset if new month)
# 3. Create git tag: version-2025.10.00004
# 4. Generate changelog since last tag
# 5. Update version.json
# 6. Commit changes
```

3. **Changelog Generation:**
```python
def generate_changelog(from_tag: str, to_tag: str) -> str:
    # Get all commits between tags
    commits = git.get_commits(from_tag, to_tag)
    
    # Group by type (feat, fix, docs, etc.)
    grouped = group_commits_by_type(commits)
    
    # Generate summary with LLM
    summary = llm.generate_summary(commits)
    
    # Extract highlights
    highlights = extract_highlights(commits)
    
    # Format as markdown
    return format_changelog(summary, highlights, grouped)
```

4. **Changelog Template:**
```markdown
# Version 2025.10.00004 (2025-10-13)

## Summary
Brief overview of changes in this release...

## Highlights
- Major feature added
- Critical bug fixed
- Performance improvement

## Changes

### Features
- [feat] Add YouTube import support (#123) @johndoe
- [feat] Implement version management (#124) @janedoe

### Bug Fixes
- [fix] Resolve indexing issue (#125) @johndoe

### Documentation
- [docs] Update installation guide (#126) @contributor

### Internal
- [chore] Refactor service layer (#127) @johndoe

## Contributors
- @johndoe (5 commits)
- @janedoe (3 commits)
- @contributor (1 commit)
```

5. **Features:**
- Automatic build number increment
- Git tag creation
- Changelog generation with commit grouping
- LLM-powered summaries and highlights
- Contributor attribution
- Link to commits and PRs
- Version comparison

**Configuration:**
```yaml
# .solace/config/versioning.yaml
format: "YYYY.MM.build-number"
changelog:
  generate: true
  include_authors: true
  group_by_type: true
  use_llm_summary: true
commit_types:
  - feat: Features
  - fix: Bug Fixes
  - docs: Documentation
  - chore: Internal
  - test: Tests
```