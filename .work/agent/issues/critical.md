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
---
id: "BUG-001@fe313e"
title: "Installed dot-work tool missing python.build module"
description: "UV tool installation outdated - missing build/ submodule that exists in source"
created: 2025-12-26
section: "installation"
tags: [installation, uv-tool, module-not-found, python]
type: bug
priority: critical
status: proposed
references:
  - src/dot_work/python/__init__.py
  - src/dot_work/python/build/cli.py
  - src/dot_work/python/build/runner.py
---

### Problem
When running `dot-work install` (or any dot-work command), the installed tool fails with:

```
ModuleNotFoundError: No module named 'dot_work.python.build'
```

The import occurs at `dot_work/python/__init__.py:12`:
```python
from dot_work.python.build.cli import run_build
```

### Root Cause Analysis

**Source Code State (Current Repository):**
- The `build/` module EXISTS at `src/dot_work/python/build/`
- Files present: `cli.py`, `runner.py`, `__init__.py`
- Git shows recent commits: "Build clean", "Fucking agents ...."
- Working tree is clean - build module is tracked

**Installed Package State:**
- Location: `~/.local/share/uv/tools/dot-work/lib/python3.13/site-packages/dot_work/python/`
- Directories present: `__pycache__`, `scan`
- **MISSING:** `build/` directory
- Install timestamp: Dec 26 02:36 (likely outdated)

**Conclusion:** The installed uv tool version predates the addition of the `build/` module to the codebase.

### Affected Files
- Installed package: `~/.local/share/uv/tools/dot-work/lib/python3.13/site-packages/dot_work/python/` (missing build/)
- Source import: `src/dot_work/python/__init__.py` (line 12)

### Importance
**CRITICAL:** The `dot-work` command is completely broken. All commands fail with `ModuleNotFoundError` because the top-level `__init__.py` imports the missing module during package initialization.

This blocks all dot-work functionality until resolved.

### Error / Exception Details
```
Traceback (most recent call last):
  File "/home/thomas/.local/bin/dot-work", line 4, in <module>
    from dot_work.cli import app
  File "/home/thomas/.local/share/uv/tools/dot-work/lib/python3.13/site-packages/dot_work/cli.py", line 16, in <module>
    from dot_work.python import python_app
  File "/home/thomas/.local/share/uv/tools/dot-work/lib/python3.13/site-packages/dot_work/python/__init__.py", line 12, in <module>
    from dot_work.python.build.cli import run_build
ModuleNotFoundError: No module named 'dot_work.python.build'
```

### Proposed Solution
1. **Reinstall the tool from current source:**
   ```bash
   cd /home/thomas/Workspace/dot.work
   uv tool uninstall dot-work
   uv tool install .
   ```

2. **Alternatively, use `uv tool upgrade` if supported:**
   ```bash
   uv tool upgrade dot-work
   ```

3. **Prevent future issues:** Consider adding a post-commit hook or CI check to verify tool installation is up-to-date after commits that add new submodules.

### Acceptance Criteria
- [ ] Tool reinstalled from current source code
- [ ] `dot-work --help` runs without ModuleNotFoundError
- [ ] `dot-work python build` command works (build module functional)
- [ ] All existing subcommands (scan, etc.) still work
- [ ] Note added to README about reinstalling after major updates

### Notes
- This issue highlights a gap: no automated verification that installed tool matches source
- Consider adding `uv tool install . --reinstall` to development workflow
- The branch `migrating-using-opencode` is 13 commits ahead of origin - these new features aren't in the installed version

Investigation completed using systematic debugging process:
- Phase 1: Root cause identified (outdated installation vs current source)
- Evidence: Git history shows build module exists; installed package missing it
- No code fix needed - reinstallation required

---
---
