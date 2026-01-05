---
name: git-workflow
description: Skill for atomic commits, branch management, and clean git history
license: MIT
compatibility: Works with all AI coding assistants

environments:
  claude:
    target: ".claude/skills/"
    filename_suffix: "/git-workflow/SKILL.md"
---

# Git Workflow Skill

You have expertise in maintaining clean git history with atomic commits, proper branch management, and conventional commit messages.

---

## Commit Philosophy

### Atomic Commits

Each commit should:
- Represent ONE logical change
- Build successfully on its own
- Pass all tests on its own
- Be revertable without side effects

```yaml
atomic_examples:
  good:
    - "Add user authentication model"
    - "Implement password hashing"
    - "Add login endpoint"
    
  bad:
    - "Add auth" (too vague, too big)
    - "WIP" (meaningless)
    - "Fix stuff" (unexplained)
```

---

## Conventional Commits

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(auth): add password reset flow` |
| `fix` | Bug fix | `fix(api): handle null user in response` |
| `docs` | Documentation | `docs(readme): add setup instructions` |
| `style` | Formatting | `style: apply black formatting` |
| `refactor` | Code restructure | `refactor(db): extract connection pool` |
| `test` | Tests | `test(auth): add login edge cases` |
| `chore` | Maintenance | `chore(deps): update pytest to 8.0` |
| `perf` | Performance | `perf(query): add index for user lookup` |

### Scope

```yaml
scope_guidelines:
  - Use module/feature name: auth, api, db, cli
  - Use file for single-file changes: (config), (readme)
  - Omit if change spans many areas
```

### Description

```yaml
description_rules:
  - Imperative mood: "add" not "adds" or "added"
  - Lowercase start
  - No period at end
  - Max 72 characters
  - Be specific: "add login" → "add email/password login endpoint"
```

---

## Commit Workflow for Issues

### Single-Issue Commit Sequence

For issue `BUG-003@a9f3c2`:

```yaml
commit_sequence:
  1. Write failing test(s):
     message: "test(config): add Windows path handling test"
     
  2. Implement fix:
     message: "fix(config): use pathlib for cross-platform paths"
     
  3. (Optional) Cleanup/refactor:
     message: "refactor(config): extract path normalization helper"

  final_state:
    - All commits reference same issue
    - Each commit builds and passes tests
    - Clear progression of work
```

### Issue Reference in Footer

```
fix(config): use pathlib for cross-platform paths

Replace os.path with pathlib.Path for consistent behavior
across Windows and Unix systems.

Fixes: BUG-003@a9f3c2
```

---

## Branch Strategy

### Branch Naming

```yaml
patterns:
  feature: "feat/{issue-id}-{short-description}"
  bugfix: "fix/{issue-id}-{short-description}"
  refactor: "refactor/{issue-id}-{short-description}"

examples:
  - feat/FEAT-012-user-auth
  - fix/BUG-003-windows-paths
  - refactor/REFACTOR-005-db-connection
```

### Branch Workflow

```yaml
workflow:
  1. Start from main:
     git checkout main && git pull
     
  2. Create feature branch:
     git checkout -b fix/BUG-003-windows-paths
     
  3. Work with atomic commits
  
  4. Rebase before merge (if needed):
     git fetch origin && git rebase origin/main
     
  5. Merge or PR:
     Depends on project conventions
```

---

## Pre-Commit Checklist

Before each commit:

```yaml
checklist:
  - [ ] Tests pass
  - [ ] Linter passes
  - [ ] Type checker passes
  - [ ] Only intended files staged
  - [ ] Commit message follows convention
  - [ ] No debug code or print statements
  - [ ] No unintended file changes
```

### Automated Check Command

```bash
# Quick pre-commit validation
git diff --cached --name-only  # Review staged files
# Run project test command from constitution
```

---

## Staging Best Practices

### Selective Staging

```yaml
prefer:
  - git add -p (patch mode for fine control)
  - git add <specific-files>
  
avoid:
  - git add . (too broad)
  - git add -A (even broader)
```

### Review Before Commit

```bash
git diff --cached          # See exactly what will be committed
git diff --cached --stat   # Overview of changed files
```

---

## Common Patterns

### Implement Then Test (Reorder)

If you wrote code then tests, reorder for cleaner history:

```yaml
workflow:
  1. Stash current changes
  2. Checkout fresh
  3. Apply and commit test first
  4. Apply and commit implementation
  
  # Or use interactive rebase after the fact
  git rebase -i HEAD~2  # Reorder commits
```

### Fix Previous Commit

```yaml
immediate_fix:
  git add <files>
  git commit --amend --no-edit
  
earlier_fix:
  git add <files>
  git commit --fixup <commit-hash>
  git rebase -i --autosquash <base-commit>
```

### Split Large Commit

```yaml
workflow:
  1. git reset HEAD~1 (undo commit, keep changes)
  2. Stage and commit in smaller pieces
  3. Each piece should build/test independently
```

---

## Integration with Issue Tracker

### Commit Footer References

```yaml
references:
  - "Fixes: BUG-003@a9f3c2"     # Closes bug
  - "Implements: FEAT-012@xyz" # Implements feature
  - "Refs: DOC-001@abc"        # Related to docs issue
  - "Part-of: EPIC-001@def"    # Part of larger epic
```

### Automation Hooks

These footers can trigger automation:
- "Fixes:" → Move issue to completed
- "Refs:" → Link in issue history
- "Part-of:" → Update epic progress

---

## Session Commit Summary

At end of implementation phase:

```yaml
summary_format:
  commits_made: 3
  
  commits:
    - hash: a1b2c3d
      message: "test(config): add Windows path handling test"
      files: 1
      
    - hash: e4f5g6h
      message: "fix(config): use pathlib for cross-platform paths"
      files: 2
      
    - hash: i7j8k9l
      message: "refactor(config): extract path normalization helper"
      files: 1
  
  issue: BUG-003@a9f3c2
  status: ready_for_validation
```

---

## Error Recovery

### Accidental Commit

```yaml
undo_last_commit:
  git reset --soft HEAD~1  # Keep changes, undo commit
```

### Wrong Branch

```yaml
move_commits:
  1. Note commit hashes
  2. git checkout correct-branch
  3. git cherry-pick <hash> (for each commit)
  4. git checkout wrong-branch
  5. git reset --hard origin/wrong-branch
```

### Committed Secrets (EMERGENCY)

```yaml
emergency:
  - DO NOT PUSH
  - git reset --soft HEAD~1
  - Remove secrets from files
  - git add <files>
  - git commit
  - Consider: git filter-branch if already pushed
  - Rotate any exposed credentials immediately
```

---

## Clean History Guidelines

### Squash When Appropriate

```yaml
squash_candidates:
  - Multiple "fix typo" commits
  - WIP commits during development
  - Commits that only make sense together

preserve_separate:
  - Test commits (show TDD process)
  - Logically distinct changes
  - Changes that might need individual revert
```

### Rebase vs Merge

```yaml
rebase_when:
  - Updating feature branch from main
  - Cleaning up local history
  - Preparing for merge

merge_when:
  - Final integration to main
  - Preserving branch history is important
  - Team convention requires it
```

---

## Commands Reference

```bash
# View staged changes
git diff --cached

# Interactive staging
git add -p

# Commit with message
git commit -m "type(scope): description"

# Amend last commit
git commit --amend

# View commit history
git log --oneline -10

# Interactive rebase
git rebase -i HEAD~N

# Create branch
git checkout -b branch-name

# Switch branch
git checkout branch-name

# Stash changes
git stash push -m "description"
git stash pop
```

---

## See Also

**Used By:** `implementer`, `pre-iteration` subagents

**Project Conventions:** `.work/constitution.md`

