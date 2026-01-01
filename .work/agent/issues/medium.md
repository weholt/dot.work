# Medium Priority Issues (P2)

Enhancements, technical debt, code quality improvements.

---
---


---
id: "TEST-001@cov001"
title: "Add targeted tests to reach 15% coverage threshold"
description: "Focus on git/, review/, and db_issues/ modules to increase coverage"
created: 2025-12-31
section: "testing"
tags: [coverage, testing]
type: test
priority: medium
status: proposed
references:
  - scripts/build.py
  - .work/agent/issues/references/medium-issue-clarifications-2025-01-01.md
---

### Problem
Unit tests run successfully but the coverage threshold of 15% is not being met. The build reports "Unit Tests with Coverage - FAILED" even though no individual tests are failing.

**Decision (2025-01-01):** Focus on adding module-specific tests rather than blanket coverage increase. Priority: git/ (5 tests), review/ (5 tests), db_issues/ (3 tests).

### Affected Files
- `tests/unit/git/` - add tests for tag_generator, file_analyzer, git_service
- `tests/unit/review/` - add tests for git, server modules
- `tests/unit/db_issues/` - add tests for cli, adapters

### Importance
Build fails coverage check. Targeted tests to key modules more effective than random additions.

### Proposed Solution
1. Add 5 tests to src/dot_work/git/services/ (tag_generator, file_analyzer, git_service)
2. Add 5 tests to src/dot_work/review/ (git, server modules)
3. Add 3 tests to src/dot_work/db_issues/ (cli, adapters)
4. Run coverage report to verify 15% threshold met

### Acceptance Criteria
- [ ] 5 tests added to tests/unit/git/services/
- [ ] 5 tests added to tests/unit/review/
- [ ] 3 tests added to tests/unit/db_issues/
- [ ] Coverage reaches 15% threshold
- [ ] All tests pass (including new tests)

### Validation Plan
1. Run `uv run pytest tests/unit/git/services/ tests/unit/review/ tests/unit/db_issues/ -v --cov=src --cov-report=term-missing`
2. Verify coverage >= 15%
3. Verify all tests pass

### Dependencies
None.

### Clarifications Needed
None. Decision documented: focus on specific modules with targeted test additions.

### Notes
See `.work/agent/issues/references/medium-issue-clarifications-2025-01-01.md` for full analysis.

---
---
id: "SEC-004@security-review-2026"
title: "Error handling may expose sensitive information in stack traces"
description: "Verbose error messages could reveal internal paths, database structure, or implementation details"
created: 2026-01-01
section: "security"
tags: [security, error-handling, information-disclosure, owasp]
type: security
priority: medium
status: proposed
references:
  - src/dot_work/cli.py
  - src/dot_work/git/cli.py
  - src/dot_work/db_issues/cli.py
  - .work/agent/issues/references/medium-issue-clarifications-2025-01-01.md
---

### Problem
Multiple CLI modules have verbose error handling that could expose sensitive information:

1. **`src/dot_work/cli.py`**: Lines 108-114, 146-152, 173-179, 200-205, 229-234, 264-270 show patterns like:
   ```python
   except Exception as e:
       console.print(f"[red]Error:[/red] {e}")
       if verbose:
           import traceback
           console.print(traceback.format_exc())
   ```
   While traceback is only shown in verbose mode, the base exception `e` could still contain sensitive paths or implementation details.

2. **`src/dot_work/git/cli.py`**: Similar patterns in exception handlers (lines 108-114, 146-152, etc.)

3. **`src/dot_work/db_issues/cli.py`**: Likely similar patterns in CLI commands

**Decision (2025-01-01):** Verbose mode can show tracebacks (developer-facing, opt-in). Base exception messages should be sanitized for non-verbose output.

### Affected Files
- `src/dot_work/cli.py`
- `src/dot_work/git/cli.py`
- `src/dot_work/db_issues/cli.py`

### Security Impact
- **OWASP Top 10**: Security Logging and Monitoring Failures (A09:2021)
- Information disclosure in error messages
- Could reveal file paths, database structure, or library versions
- Aids attackers in reconnaissance

### Proposed Solution
1. Create a sanitization function for user-facing error messages
2. Log detailed errors server-side while showing generic messages to users
3. Use specific exception types instead of broad `Exception` catches
4. Keep verbose mode traceback display (opt-in developer feature)
5. Use `sanitize_log_message()` from `git/utils.py` (lines 105-127) more broadly

### Acceptance Criteria
- [ ] Non-verbose error messages are generic (no paths, internal details)
- [ ] Verbose mode keeps traceback display for debugging
- [ ] Sensitive data filtered from all exception messages
- [ ] Detailed errors logged to file only
- [ ] Sanitization function created and used across all CLI modules

### Validation Plan
1. Create error messages with paths/secrets
2. Verify non-verbose output shows generic message only
3. Verify verbose output shows full traceback
4. Verify log file contains full details

### Dependencies
None.

### Clarifications Needed
None. Decision documented: verbose mode tracebacks OK, sanitize base messages.

### Notes
See `.work/agent/issues/references/medium-issue-clarifications-2025-01-01.md` for full analysis.

---
---
id: "SEC-005@security-review-2026"
title: "File operations lack path validation throughout codebase"
description: "Multiple file read/write operations don't validate paths are within expected directories"
created: 2026-01-01
section: "security"
tags: [security, path-traversal, file-operations, owasp]
type: security
priority: medium
status: proposed
references:
  - src/dot_work/installer.py
  - src/dot_work/review/git.py
  - src/dot_work/zip/uploader.py
  - .work/agent/issues/references/medium-issue-clarifications-2025-01-01.md
---

### Problem
The codebase has numerous file operations without path traversal validation:

1. **`src/dot_work/installer.py`**:
   - Line 348: `combined_path.write_text()` - combined_path = target / config.combined_path
   - Line 430: `dest_path.write_text()` - dest_path = dest_dir / dest_name
   - Line 450: `aux_full_path.write_text()` - auxiliary files
   - `target` comes from user CLI argument; config paths are hardcoded but no validation against `../`

2. **`src/dot_work/review/git.py`**: File read operations based on user-provided paths
   - `read_file_text()` could be vulnerable to `../../etc/passwd` attacks

3. **`src/dot_work/zip/uploader.py`**:
   - Line 36: `zip_path.exists()` check, but no validation that it's a zip file (could be symlink)

**Decision (2025-01-01):** Add path validation utility to ensure all write paths stay within target directory. While config paths are currently trusted, future modifications could introduce vulnerabilities. Path traversal is a critical security issue (OWASP A01:2021).

### Affected Files
- `src/dot_work/installer.py`
- `src/dot_work/review/git.py`
- `src/dot_work/zip/uploader.py`
- Create `src/dot_work/utils/path.py` for validation utility

### Security Impact
- **OWASP Top 10**: Path Traversal (A01:2021)
- Directory traversal attacks could read arbitrary files
- Symlink attacks could write to unintended locations
- In shared environments, users could read each other's data

### Proposed Solution
1. Create `safe_path_join(target, path)` utility in `src/dot_work/utils/path.py`
2. Utility resolves symlinks and validates result is within target directory
3. All installer.py write operations use safe_path_join
4. Add tests for path traversal attempts

### Acceptance Criteria
- [ ] Path validation utility created (`src/dot_work/utils/path.py`)
- [ ] All installer.py write operations use safe_path_join
- [ ] Symlinks resolved before validation
- [ ] Path traversal tests added (proving mitigation)
- [ ] Documentation for safe file operations

### Validation Plan
1. Test path with `../` sequences - verify rejected
2. Test symlink to file outside target - verify rejected
3. Test normal paths within target - verify accepted
4. Run all installer tests to verify no regression

### Dependencies
None.

### Clarifications Needed
None. Decision documented: add path validation utility for all user-controlled paths.

### Notes
See `.work/agent/issues/references/medium-issue-clarifications-2025-01-01.md` for full analysis.

---
---
id: "SEC-006@security-review-2026"
title: "Jinja2 autoescape disabled for markdown templates"
description: "Jinja2 environment created with autoescape=False, trusting all template content"
created: 2026-01-01
section: "security"
tags: [security, xss, jinja2, owasp]
type: security
priority: medium
status: proposed
references:
  - src/dot_work/installer.py
  - .work/agent/issues/references/medium-issue-clarifications-2025-01-01.md
---

### Problem
In `src/dot_work/installer.py:106-112`:
```python
return JinjaEnvironment(  # noqa: S701 - autoescape disabled for markdown
    loader=FileSystemLoader(prompts_dir),
    keep_trailing_newline=True,
    trim_blocks=False,
    lstrip_blocks=False,
    autoescape=False,  # Markdown templates, not HTML
)
```

While the comment notes this is for markdown (not HTML), there are concerns:
1. **Future HTML generation**: If the templates ever generate HTML (e.g., for web UI), XSS is possible
2. **Template injection**: If template files can be modified by users, they could inject arbitrary code
3. **Comment notes**: The `noqa: S701` suppresses security linter without ongoing validation

**Decision (2025-01-01):** No HTML output planned, markdown only. Templates are internal (from dot_work/prompts/), not user-specified. Add documentation explaining the security rationale.

### Affected Files
- `src/dot_work/installer.py`

### Security Impact
- **OWASP Top 10**: Cross-Site Scripting (A03:2021)
- Currently low risk (markdown output, internal templates)
- Template injection if users can modify prompt files (not the case)

### Proposed Solution
1. Add comprehensive docstring explaining why autoescape is disabled
2. Add comment warning if HTML output is ever added
3. Add tests to verify template content is treated as trusted
4. Document security decision in code

### Acceptance Criteria
- [ ] Comprehensive docstring added explaining autoescape decision
- [ ] Comment warning added if HTML output is ever planned
- [ ] Tests verify templates are from trusted internal source
- [ ] Security decision documented in code comments

### Validation Plan
1. Review create_jinja_env function
2. Verify documentation mentions trusted source and markdown-only output
3. Verify tests pass

### Dependencies
None.

### Clarifications Needed
None. Decision documented: no HTML output planned, add documentation.

### Notes
See `.work/agent/issues/references/medium-issue-clarifications-2025-01-01.md` for full analysis.

---
---
id: "SEC-007@security-review-2026"
title: "No secrets management strategy for API keys and tokens"
description: "Hardcoded or environment-based secrets handling lacks proper validation and rotation"
created: 2026-01-01
section: "security"
tags: [security, secrets-management, owasp]
type: security
priority: medium
status: proposed
references:
  - src/dot_work/knowledge_graph/embed/openai.py
  - src/dot_work/git/services/llm_summarizer.py
  - src/dot_work/container/provision/
  - .work/agent/issues/references/medium-issue-clarifications-2025-01-01.md
---

### Problem
The codebase lacks a comprehensive secrets management strategy:

1. **No validation**: Environment variables for API keys are used without validation
2. **No rotation strategy**: No mechanism for key rotation or expiry
3. **Potential leakage**: Secrets could be logged or exposed in error messages
4. **No encryption at rest**: Database credentials or API keys stored in plain text

**Actual secrets found (2025-01-01):**
- `OPENAI_API_KEY`: used in `knowledge_graph/embed/openai.py` and `git/services/llm_summarizer.py`
- `ANTHROPIC_API_KEY`: used in `git/services/llm_summarizer.py`
- `GITHUB_TOKEN`: used in `container/provision/` modules
- SQLite uses file-based database (no credentials)

**Decision (2025-01-01):** Scope secrets management to these three environment variables. Create focused validation utility.

### Affected Files
- `src/dot_work/knowledge_graph/embed/openai.py`
- `src/dot_work/git/services/llm_summarizer.py`
- `src/dot_work/container/provision/`
- Create `src/dot_work/utils/secrets.py` for validation utility

### Security Impact
- **OWASP Top 10**: Cryptographic Failures (A02:2021)
- API keys could be leaked in logs or error messages
- No mechanism to detect compromised keys
- Credentials stored in plain text

### Proposed Solution
1. Create `secrets.py` utility with validation for OPENAI_API_KEY, ANTHROPIC_API_KEY, GITHUB_TOKEN
2. Ensure secrets are never logged (use `sanitize_log_message()`)
3. Add `.env` file support with proper gitignore
4. Document secrets management in CONTRIBUTING.md

### Acceptance Criteria
- [ ] Secrets validation utility created (`src/dot_work/utils/secrets.py`)
- [ ] Validates OPENAI_API_KEY, ANTHROPIC_API_KEY, GITHUB_TOKEN format
- [ ] Secrets never appear in logs or error messages
- [ ] .env.example file provided (without actual secrets)
- [ ] Documentation for secrets management
- [ ] Tests verify secrets aren't leaked in output

### Validation Plan
1. Test with valid API key format - verify accepted
2. Test with empty/invalid format - verify rejected with clear error
3. Verify secrets don't appear in logs
4. Run all tests to verify no regression

### Dependencies
SEC-004 (error handling sanitization) - ensures secrets don't leak in error messages.

### Clarifications Needed
None. Decision documented: scope to OPENAI_API_KEY, ANTHROPIC_API_KEY, GITHUB_TOKEN.

### Notes
See `.work/agent/issues/references/medium-issue-clarifications-2025-01-01.md` for full analysis. SQLite is file-based (no credentials).

---
