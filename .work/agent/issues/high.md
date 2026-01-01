# High Priority Issues (P1)

Core functionality broken or missing documented features.

---
---
id: "SEC-003@security-review-2026"
title: "SQLite operations use text() with potential SQL injection in search"
description: "Custom SQL text() calls in knowledge graph search could be vulnerable if user input is not properly sanitized"
created: 2026-01-01
section: "security"
tags: [security, sql-injection, sqlite, owasp]
type: security
priority: high
status: proposed
references:
  - src/dot_work/knowledge_graph/search_fts.py
  - src/dot_work/db_issues/adapters/sqlite.py
---

### Problem
The codebase uses SQLAlchemy/SQLModel which provides good SQL injection protection through parameterized queries. However, there are some areas using raw SQL:

1. **`src/dot_work/db_issues/adapters/sqlite.py`** uses `text()` for custom queries:
   - Lines 374-375: DELETE statements with parameterized placeholders (safe)
   - Lines 392-393: DELETE statements with parameterized placeholders (safe)
   - Lines 603-614: Complex GROUP BY query with proper parameterization (safe)

   While these current usages appear safe (using named parameters like `:issue_id`), the pattern is fragile and future modifications could introduce vulnerabilities.

2. **`src/dot_work/knowledge_graph/search_fts.py:160`** mentions "strict security validation to prevent SQL injection" but needs verification that all FTS queries properly sanitize user input.

### Affected Files
- `src/dot_work/db_issues/adapters/sqlite.py`
- `src/dot_work/knowledge_graph/search_fts.py`

### Security Impact
- **OWASP Top 10**: Injection (A03:2021)
- SQL injection could lead to data exfiltration or corruption
- While current code appears safe, the pattern needs verification

### Proposed Solution
1. Audit all `text()` usages to ensure proper parameterization
2. Add linter rules to detect string concatenation in SQL queries
3. Add unit tests specifically testing SQL injection attempts
4. Document safe patterns for custom SQL queries

### Acceptance Criteria
- [ ] All `text()` calls audited and verified safe
- [ ] SQL injection tests added (proving inputs are sanitized)
- [ ] Documentation created for safe query patterns
- [ ] Bandit/S601 checks pass for all database code

---
