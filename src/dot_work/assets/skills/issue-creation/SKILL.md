---
name: issue-creation
description: Skill for creating well-formed issues from discoveries during implementation or validation
license: MIT
compatibility: Works with all AI coding assistants
---

# Issue Creation Skill

You have expertise in creating well-formed issues from discoveries during code review, security audit, implementation, or any other phase. This skill ensures consistent issue formatting and proper prioritization.

---

## When to Create Issues

### Validation Findings

```yaml
code_review_findings:
  - Code duplication detected
  - Missing error handling
  - Unclear variable names
  - Complex functions needing refactor
  - Missing documentation

security_audit_findings:
  - Input validation gaps
  - Potential injection points
  - Hardcoded credentials
  - Missing authentication checks
  - Insecure dependencies

performance_findings:
  - N+1 query patterns
  - Missing indexes
  - Inefficient algorithms
  - Memory leaks
  - Unnecessary computations
```

### Implementation Discoveries

```yaml
while_implementing:
  - Found related bug while fixing issue
  - Technical debt discovered
  - Test coverage gap identified
  - Documentation outdated
  - Dependency needs update
```

### Scope Management

```yaml
out_of_scope:
  - Enhancement ideas during bug fix
  - Refactoring opportunities
  - "While I'm here" improvements
  
action: Create issue, don't implement now
reason: Stay focused on current issue
```

---

## Issue ID Format

```yaml
format: "{TYPE}-{NUM}@{HASH}"

components:
  TYPE: BUG | FEAT | REFACTOR | DOC | PERF | SEC | TEST | CHORE
  NUM: Sequential number (001-999)
  HASH: First 6 chars of SHA256(title + timestamp)

examples:
  - BUG-003@a9f3c2
  - SEC-001@7d8e4f
  - REFACTOR-012@c3b2a1
```

### ID Generation

```python
import hashlib
from datetime import datetime

def generate_id(issue_type: str, title: str) -> str:
    # Get next number from issue files
    num = get_next_issue_number(issue_type)
    
    # Generate hash
    content = f"{title}{datetime.now().isoformat()}"
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:6]
    
    return f"{issue_type}-{num:03d}@{hash_val}"
```

---

## Issue Template

```markdown
---
id: "{TYPE}-{NUM}@{HASH}"
title: "{Clear, specific title}"
description: "{One-line summary}"
created: {ISO-8601 timestamp}
type: {bug|feature|refactor|doc|perf|security|test|chore}
priority: {critical|high|medium|low}
status: proposed
source: {code-review|security-audit|implementation|user-report|automated}
affected_files:
  - {path/to/file1.py}
  - {path/to/file2.py}
tags:
  - {relevant-tag}
---

### Problem

{Detailed description of the problem or need}

### Evidence

{Code snippets, error messages, or test failures that demonstrate the issue}

```{language}
{relevant code or output}
```

### Acceptance Criteria

- [ ] {Specific, verifiable criterion 1}
- [ ] {Specific, verifiable criterion 2}
- [ ] {Tests added/updated}
- [ ] {Documentation updated if needed}

### Notes

{Additional context, potential approaches, related issues}
```

---

## Priority Assignment

### Critical (P0)

```yaml
criteria:
  - Security vulnerability (exploitable)
  - Data loss or corruption
  - System crash or unavailability
  - Blocks other critical work

response_time: Immediate
file: critical.md
```

### High (P1)

```yaml
criteria:
  - Core functionality broken
  - Significant user impact
  - No workaround available
  - Performance degradation >50%

response_time: Same day
file: high.md
```

### Medium (P2)

```yaml
criteria:
  - Feature partially broken
  - Workaround exists
  - Moderate user impact
  - Code quality issues

response_time: This week
file: medium.md
```

### Low (P3)

```yaml
criteria:
  - Minor inconvenience
  - Cosmetic issues
  - Nice-to-have improvements
  - Technical debt (non-urgent)

response_time: When convenient
file: low.md
```

---

## Type Classification

| Type | Description | ID Prefix |
|------|-------------|-----------|
| bug | Something broken | BUG |
| feature | New functionality | FEAT |
| refactor | Code improvement | REFACTOR |
| doc | Documentation | DOC |
| perf | Performance | PERF |
| security | Security issue | SEC |
| test | Test coverage | TEST |
| chore | Maintenance | CHORE |

---

## Source Tracking

Track where issue originated:

```yaml
sources:
  code-review: "Found during code review subagent validation"
  security-audit: "Found during security audit subagent validation"
  implementation: "Discovered while implementing another issue"
  user-report: "Reported by user"
  automated: "Detected by CI/linting/tests"
  performance-review: "Found during performance review"
  spec-audit: "Found during specification compliance check"
```

---

## Quality Checklist

Before creating issue:

```yaml
checklist:
  - [ ] Title is specific and actionable
  - [ ] Problem clearly described
  - [ ] Evidence provided (code, logs, errors)
  - [ ] Acceptance criteria are verifiable
  - [ ] Priority matches severity guidelines
  - [ ] Type correctly classified
  - [ ] Affected files identified
  - [ ] Not a duplicate of existing issue
```

---

## Duplicate Detection

Before creating, check for duplicates:

```yaml
duplicate_check:
  1. Search existing issues for similar title
  2. Check affected files overlap
  3. Compare problem description
  
if_duplicate_found:
  - Add reference to existing issue instead
  - Update existing issue if new info available
  - Don't create duplicate
```

---

## Batch Issue Creation

When validation finds multiple issues:

```yaml
batch_workflow:
  1. Collect all findings
  2. Deduplicate within batch
  3. Prioritize each
  4. Create issues in priority order (critical first)
  5. Return summary:
     - Total issues created: N
     - By priority: {critical: 1, high: 2, medium: 3}
     - Files written: [critical.md, high.md, medium.md]
```

---

## Issue Relationships

### Link Related Issues

```yaml
frontmatter:
  related:
    - blocks: ["BUG-005@xyz123"]
    - blocked_by: ["FEAT-001@abc456"]
    - duplicates: []
    - related_to: ["REFACTOR-003@def789"]
```

### Epic/Parent Tracking

```yaml
frontmatter:
  parent: "EPIC-001@master-id"
  part_of: "Q1-2026 Security Hardening"
```

---

## Validation Subagent Integration

How validation subagents use this skill:

```yaml
code_reviewer:
  findings_to_issues:
    - duplication → REFACTOR issue
    - complexity → REFACTOR issue
    - missing tests → TEST issue
    - unclear code → REFACTOR issue

security_auditor:
  findings_to_issues:
    - vulnerability → SEC issue (critical/high)
    - weak pattern → SEC issue (medium)
    - missing validation → SEC issue (medium/low)

performance_reviewer:
  findings_to_issues:
    - slow query → PERF issue
    - memory issue → PERF issue
    - algorithm → PERF issue
```

---

## Issue File Appending

Append new issue to appropriate file:

```yaml
workflow:
  1. Determine target file from priority
  2. Read current file content
  3. Append separator: "\n---\n\n"
  4. Append new issue block
  5. Write file
  6. Report: "Created {id} in {file}"
```

---

## Example: Security Issue

```markdown
---
id: "SEC-001@7d8e4f"
title: "SQL injection vulnerability in user search"
description: "User input not sanitized in search query"
created: 2026-01-05T10:30:00Z
type: security
priority: critical
status: proposed
source: security-audit
affected_files:
  - src/api/search.py
tags:
  - sql-injection
  - security
  - user-input
---

### Problem

The user search endpoint directly interpolates user input into SQL query without parameterization, allowing SQL injection attacks.

### Evidence

```python
# src/api/search.py:45
query = f"SELECT * FROM users WHERE name LIKE '%{user_input}%'"
cursor.execute(query)  # VULNERABLE
```

### Acceptance Criteria

- [ ] Use parameterized queries
- [ ] Add input validation
- [ ] Add test for SQL injection attempt
- [ ] Security audit passes

### Notes

This is a critical security vulnerability that could expose all user data. Should be fixed immediately before next deployment.
```

---

## See Also

**Related Skills:** `issue-management`

**Used By:** `code-reviewer`, `security-auditor`, `spec-auditor`, `performance-reviewer` subagents

