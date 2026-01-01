# High Priority Issues (P1)

Core functionality broken or missing documented features.

---
---
id: "SEC-002@security-review-2026"
title: "Review server binds to 127.0.0.1 without authentication"
description: "FastAPI review server has no authentication mechanism, exposing code review comments to anyone with local access"
created: 2026-01-01
section: "security"
tags: [security, authentication, fastapi, owasp]
type: security
priority: high
status: proposed
references:
  - src/dot_work/review/server.py
---

### Problem
The review server (`src/dot_work/review/server.py`) has several security concerns:

1. **No Authentication**: The FastAPI server at line 174-198 has no authentication mechanism. Anyone who can access localhost:8765 can:
   - View all file diffs
   - Add comments with arbitrary content
   - Access the `/api/state` endpoint
   - Modify review data via `/api/comment`

2. **Path Traversal Risk**: The `path` query parameter (line 78) is used to construct file paths without validation:
   ```python
   @app.get("/", response_class=HTMLResponse)
   def index(request: Request, path: str | None = None) -> HTMLResponse:
   ```
   While `read_file_text()` may handle errors, there's no validation that `path` stays within the repository root.

3. **No Rate Limiting**: Comment submission endpoint (line 131) has no rate limiting, allowing spam attacks.

### Affected Files
- `src/dot_work/review/server.py`

### Security Impact
- **OWASP Top 10**: Broken Access Control (A01:2021)
- Unauthorized access to code review data
- Potential for data tampering (malicious comments)
- Local attackers could exploit shared development environments

### Proposed Solution
1. Add authentication (at minimum, a shared secret token via headers)
2. Implement path validation to prevent directory traversal
3. Add rate limiting to comment submission
4. Consider adding CORS headers if accessed from browser
5. Add option to bind to specific interfaces (currently hardcodes 127.0.0.1)

### Acceptance Criteria
- [ ] Authentication mechanism added (Bearer token or API key)
- [ ] Path traversal protection implemented
- [ ] Rate limiting on comment submission (10-100 requests/minute)
- [ ] Security headers added (CORS, CSP if applicable)
- [ ] Documentation for secure deployment

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
