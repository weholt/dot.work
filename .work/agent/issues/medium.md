# Medium Priority Issues (P2)

Enhancements, technical debt, code quality improvements.

---
---
id: "CR-030@c6d8e0"
title: "TagGenerator is over-engineered at 695 lines"
description: "Elaborate emoji mappings and priority systems for simple tag generation"
created: 2024-12-27
section: "git"
tags: [refactor, simplification]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/git/services/tag_generator.py
---

### Problem
`TagGenerator` (695 lines) has elaborate emoji-to-tag mappings, redundancy filtering, and priority systems. Consider if simpler keyword matching (50-100 lines) would suffice for commit tagging.

### Affected Files
- `src/dot_work/git/services/tag_generator.py`

### Importance
Complexity proportional to value delivered. Simpler code is easier to maintain.

### Proposed Solution
1. Evaluate if elaborate logic is actually needed
2. Consider simplifying to basic keyword matching
3. Remove unused sophistication

### Acceptance Criteria
- [ ] Complexity evaluated against requirements
- [ ] Unnecessary complexity removed
- [ ] Tag quality maintained or improved



---
id: "TEST-001@cov001"
title: "Test coverage below 15% threshold"
description: "Unit tests pass but coverage threshold not met"
created: 2025-12-31
section: "testing"
tags: [coverage, testing]
type: bug
priority: medium
status: proposed
references:
  - scripts/build.py
---

### Problem
Unit tests run successfully but the coverage threshold of 15% is not being met. The build reports "Unit Tests with Coverage - FAILED" even though no individual tests are failing.

### Affected Files
- Test suite (tests/ directory)

### Importance
Build fails coverage check despite passing tests. Need to either:
1. Add more tests to increase coverage
2. Identify why coverage is below 15%

### Proposed Solution
Investigate current coverage percentage and add tests for uncovered code paths.

### Acceptance Criteria
- [ ] Test coverage meets 15% threshold
- [ ] All tests pass

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
4. Consider using `sanitizelog_message()` from `git/utils.py` (lines 105-127) more broadly

### Acceptance Criteria
- [ ] User-facing error messages sanitized (no paths, internal details)
- [ ] Detailed errors logged to file only
- [ ] Generic error messages for unexpected exceptions
- [ ] Sensitive data filtered from all CLI output

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
---

### Problem
The codebase has numerous file operations without path traversal validation:

1. **`src/dot_work/installer.py`**:
   - Line 348: `combined_path.write_text()` - writes to user-specified path
   - Line 430: `dest_path.write_text()` - writes to potentially user-controlled path
   - No validation that paths stay within target directory

2. **`src/dot_work/review/git.py`**: File read operations based on user-provided paths
   - `read_file_text()` could be vulnerable to `../../etc/passwd` attacks

3. **`src/dot_work/zip/uploader.py`**:
   - Line 36: `zip_path.exists()` check, but no validation that it's a zip file (could be symlink)

### Affected Files
- `src/dot_work/installer.py`
- `src/dot_work/review/git.py`
- `src/dot_work/zip/uploader.py`
- Any file using `Path.write_text()` or `Path.read_text()` with user input

### Security Impact
- **OWASP Top 10**: Path Traversal (A01:2021)
- Directory traversal attacks could read arbitrary files
- Symlink attacks could write to unintended locations
- In shared environments, users could read each other's data

### Proposed Solution
1. Add path validation utility to ensure paths are within expected directories
2. Resolve symlinks and validate before file operations
3. Use `Path.resolve()` and check result is within expected base directory
4. Add tests for path traversal attempts

### Acceptance Criteria
- [ ] Path validation utility created and used
- [ ] All write operations validate paths stay within target directory
- [ ] Symlinks resolved before validation
- [ ] Path traversal tests added (proving mitigation)
- [ ] Documentation for safe file operations

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

### Affected Files
- `src/dot_work/installer.py`

### Security Impact
- **OWASP Top 10**: Cross-Site Scripting (A03:2021)
- Currently low risk (markdown output), but creates debt for future web features
- Template injection if users can modify prompt files

### Proposed Solution
1. Add documentation explaining why autoescape is disabled
2. Consider using a custom autoescape function for markdown
3. Add tests to verify template content is sanitized
4. Review if any templates could output HTML in the future

### Acceptance Criteria
- [ ] Documentation added explaining autoescape decision
- [ ] Tests verify template content is safe
- [ ] Security review if HTML output is planned
- [ ] Template source validation (if user-modifiable)

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
  - src/dot_work/knowledge_graph/embed/ollama.py
---

### Problem
The codebase lacks a comprehensive secrets management strategy:

1. **No validation**: Environment variables for API keys are used without validation
2. **No rotation strategy**: No mechanism for key rotation or expiry
3. **Potential leakage**: Secrets could be logged or exposed in error messages
4. **No encryption at rest**: Database credentials or API keys stored in plain text

While the project is a developer tool (reducing exposure), proper secrets handling is still important for:
- LLM API keys (OpenAI, Anthropic) used in knowledge graph embedding
- Git tokens (if used for authenticated operations)
- Database credentials

### Affected Files
- Any file using `os.getenv()` for sensitive data
- `src/dot_work/knowledge_graph/embed/openai.py`
- `src/dot_work/knowledge_graph/embed/ollama.py`

### Security Impact
- **OWASP Top 10**: Cryptographic Failures (A02:2021)
- API keys could be leaked in logs or error messages
- No mechanism to detect compromised keys
- Credentials stored in plain text

### Proposed Solution
1. Create a secrets management utility with validation
2. Ensure secrets are never logged (use `sanitize_log_message()`)
3. Add `.env` file support with proper gitignore
4. Document secrets management in CONTRIBUTING.md
5. Consider adding key rotation support

### Acceptance Criteria
- [ ] Secrets validation utility created
- [ ] Secrets never appear in logs or error messages
- [ ] .env.example file provided (without actual secrets)
- [ ] Documentation for secrets management
- [ ] Tests verify secrets aren't leaked in output

---
