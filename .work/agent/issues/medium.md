# Medium Priority Issues (P2)

Enhancements, technical debt, code quality improvements.

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
