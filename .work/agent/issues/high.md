# High Priority Issues (P1)

Core functionality broken or missing documented features.

---

---
id: "TEST-001@c4a9f6"
title: "Add installer integration tests"
description: "Installer install_for_* functions lack comprehensive tests"
created: 2024-12-20
section: "tests"
tags: [testing, coverage, installer]
type: test
priority: high
status: proposed
references:
  - tests/unit/test_installer.py
  - src/dot_work/installer.py
---

### Problem
The installer module has 41% coverage. The 10 `install_for_*` functions are not individually tested. CLI command tests (TEST-002) now cover the entry points, but installer internals need more coverage.

### Remaining Work
(CLI tests completed in TEST-002@d8c4e1)

1. Add tests for each `install_for_*` function:
   - Verify correct directories created per environment
   - Verify files have expected content
   - Verify template variables substituted correctly
2. Add parametrized tests across environments
3. Test edge cases (missing prompts, permission errors)

### Acceptance Criteria
- [ ] Each `install_for_*` function has at least one test
- [ ] Coverage for installer.py ≥ 80% (currently 41%)
- [ ] Parametrized tests for all 10 environments

### Notes
CLI tests in TEST-002 now cover:
- ✅ CLI commands (80% coverage)
- ✅ `detect_environment()`
- ✅ `initialize_work_directory()`

Focus remaining effort on `install_for_*` functions.

---

---
id: "FEAT-005@d5b2e8"
title: "Templatize all prompt cross-references"
description: "11 of 12 prompts use hardcoded paths that break in non-Copilot environments"
created: 2024-12-20
section: "prompts"
tags: [prompts, templates, broken-links]
type: bug
priority: high
status: proposed
references:
  - src/dot_work/prompts/
---

### Problem
Prompts use hardcoded relative paths like `[do-work.prompt.md](do-work.prompt.md)` instead of template variables. Only `setup-issue-tracker.prompt.md` uses `{{ prompt_path }}` correctly.

### Impact
Links break when installed to:
- **Claude**: All content merged into CLAUDE.md - relative links point nowhere
- **Cursor**: Prompts in .cursor/rules/*.mdc - links incorrect
- **Aider**: Content in CONVENTIONS.md - relative links broken
- **Amazon Q**: Content in .amazonq/rules.md - links broken
- **All 9 non-Copilot environments** have broken cross-references

### Affected Files (11 of 12 prompts)
- do-work.prompt.md
- critical-code-review.prompt.md
- establish-baseline.prompt.md
- compare-baseline.prompt.md
- spec-delivery-auditor.prompt.md
- agent-prompts-reference.prompt.md
- improvement-discovery.prompt.md
- bump-version.prompt.md
- api-export.prompt.md
- new-issue.prompt.md
- python-project-from-discussion.prompt.md

### Proposed Solution
1. Audit all prompt files for cross-references
2. Replace hardcoded paths with `{{ prompt_path }}/filename.prompt.md`
3. Add test to detect hardcoded `.prompt.md` references
4. Verify rendering produces correct paths for each environment

### Acceptance Criteria
- [ ] All prompt cross-references use `{{ prompt_path }}` variable
- [ ] Links render correctly for copilot, claude, cursor, generic environments
- [ ] Test added to detect hardcoded prompt references
- [ ] No raw `{{` or `}}` in rendered output

### Priority Justification
Elevated to P1 because broken links affect 9/10 environments immediately upon install.



