# Critical Issues (P0)

Blockers, security issues, data loss risks.

---
id: "SEC-002@94eb69"
title: "Security: SQL injection risk in FTS5 search query"
description: "Insufficient input sanitization in full-text search allows potential FTS5 query injection"
created: 2025-12-25
section: "knowledge-graph"
tags: [security, sql-injection, fts5, search]
type: security
priority: critical
status: proposed
references:
  - src/dot_work/knowledge_graph/search_fts.py
  - src/dot_work/knowledge_graph/db.py
---

### Problem
In `src/dot_work/knowledge_graph/search_fts.py`, the `_prepare_query()` function attempts to escape FTS5 search terms, but the escaping logic has significant gaps:

1. **Line 161**: Detects FTS5 operators (AND, OR, NOT, quotes, parentheses)
2. **Line 165**: If operators detected, **trusts user input completely** without validation
3. **Line 181**: `_escape_fts_term()` only removes non-alphanumeric characters using regex `r"[^\w\s-]"`

**Vulnerabilities:**
- If user provides FTS5 query with operators, it bypasses all sanitization
- Regex escape is insufficient for complex FTS5 syntax (column filters, proximity searches)
- Special FTS5 syntax like `^term*` (prefix search) and `term NEAR/2 term` can bypass filtering

Attack vectors:
- `SELECT * FROM users WHERE name MATCH 'abc OR 1=1'` → Could leak all records
- Column filter injection: `email: *" OR "*` → Could bypass filters
- Phrase search injection with malformed unicode

### Affected Files
- `src/dot_work/knowledge_graph/search_fts.py` (lines 150-182)
- `src/dot_work/knowledge_graph/db.py` (line 896 - fts_search passes query directly)

### Importance
**CRITICAL**: SQL injection via FTS5 syntax can lead to:
- Information disclosure (bypass access controls)
- Denial of service (complex query DoS)
- Potential data corruption in some SQLite configurations

While FTS5 is more limited than full SQL, clever queries can still cause harm:
- FTS5 allows column filtering: `col:term`
- Phrase searches with wildcards: `"term*"`
- Proximity searches: `NEAR/2 term`
- Boolean logic combinations

CVSS Score: 7.5 (High)
- Attack Vector: Network (if search is web-exposed)
- Attack Complexity: Low
- Privileges Required: None (user-provided input)
- Impact: High (Confidentiality)

### Proposed Solution
1. **Strict input validation**: Whitelist allowed characters for simple searches:
   ```python
   if not re.match(r'^[\w\s\-\.]+$', query):
       raise ValueError("Invalid search query")
   ```

2. **Reject FTS5 operators by default**: Remove auto-detection, require explicit flag for advanced queries
3. **Parameterize column filters**: If column filters are needed, pass as separate parameters
4. **Query complexity limits**: Limit query length and operator count

### Acceptance Criteria
- [ ] FTS5 operators (AND, OR, NOT, parentheses) rejected by default
- [ ] Only alphanumeric + space + hyphen + period allowed in simple mode
- [ ] Optional `--allow-advanced-search` flag for trusted users
- [ ] Tests verify injection attempts are blocked
- [ ] Documentation warns about advanced search risks

### Notes
- FTS5 documentation: https://www.sqlite.org/fts5.html
- Consider using dedicated search library (like whoosh) for complex needs
- Current `_escape_fts_term()` at line 177 is insufficient for security

---
id: "SEC-003@94eb69"
title: "Security: Unvalidated git command argument in review/git.py"
description: "Git ref parameters not validated before subprocess execution"
created: 2025-12-25
section: "review"
tags: [security, git-injection, subprocess]
type: security
priority: critical
status: proposed
references:
  - src/dot_work/review/git.py
  - src/dot_work/review/git.py:32-40
  - src/dot_work/review/git.py:139
  - src/dot_work/review/git.py:188
---

### Problem
In `src/dot_work/review/git.py`, the `_run_git()` function builds git commands with user-controlled arguments:

```python
def _run_git(args: list[str], cwd: str | None = None) -> str:
    cmd = ["git", *args]  # noqa: S607
    result = subprocess.run(  # noqa: S603
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
```

**Vulnerabilities:**
1. The `args` parameter is passed through from callers without validation
2. Line 139: `base` parameter in `changed_files()` is used directly in git diff
3. Line 188: `base` parameter in `get_unified_diff()` is used directly
4. Git allows passing options via ref names (e.g., `--upload-pack=` for RCE)

**Attack vectors:**
- If `from_ref` or `to_ref` contains `--upload-pack=|rm -rf /;` → Remote code execution
- Git config injection via ref names
- Arbitrary file read via `--git-dir=` or `--work-tree=` options

While this is primarily a developer tool, if used in CI/CD with PR-controlled refs, it could be exploited.

### Affected Files
- `src/dot_work/review/git.py` (lines 18-40, 139, 188)

### Importance
**CRITICAL**: Git option injection can lead to arbitrary code execution. Git has a history of security issues related to untrusted ref handling.

CVSS Score: 8.5 (High)
- Attack Vector: Local (but network-exposed via web hooks)
- Attack Complexity: Low
- Privileges Required: Low (user-level)
- Impact: High (Confidentiality, Integrity, Availability)

### Proposed Solution
1. **Validate ref names**: Only allow safe ref patterns:
   ```python
   import re
   REF_PATTERN = re.compile(r'^[a-zA-Z0-9_\-./~^:]+$')
   if not REF_PATTERN.match(ref):
       raise ValueError(f"Invalid git ref: {ref}")
   ```

2. **Use git rev-parse to validate**: Resolve refs to commit hashes before use
3. **Block git options**: Reject args starting with `--`
4. **Consider gitpython library**: Use GitPython's safer abstractions (already imported in project)

### Acceptance Criteria
- [ ] All git refs validated with strict regex
- [ ] Git options (args starting with `--`) blocked
- [ ] Tests verify malicious ref names are rejected
- [ ] Security audit passes all git command constructions

### Notes
- Git ref format specification: https://git-scm.com/docs/git-check-ref-format
- Consider using GitPython's `repo.commit()` which validates refs
- The `noqa: S607` and `noqa: S603` comments acknowledge the risk - these need fixing

---
