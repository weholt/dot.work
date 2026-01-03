# Shortlist

High-priority issues ready for implementation.

---
id: "QA-002@d2e3f4"
title: "Improve test coverage for skills CLI"
description: "Add tests for skills CLI commands (currently 14% coverage)"
created: 2026-01-03
section: "testing"
tags: [testing, coverage, cli, skills]
type: quality
priority: high
status: proposed
references:
  - src/dot_work/skills/cli.py
  - tests/unit/skills/test_cli.py (to be created)
---

### Problem
The skills CLI module has only 14% test coverage, below the 75% target. High-risk user-facing code.

### Affected Files
- **New**: `tests/unit/skills/test_cli.py`

### Coverage Details
Current: 14% (139 of 162 lines missing)

### Proposed Tests
Similar to QA-001, covering all skills CLI commands.

### Acceptance Criteria
- [ ] Test file created with comprehensive coverage
- [ ] Coverage for cli.py increased to 75%+
- [ ] All tests passing

### Estimated Effort
4-6 hours

---
id: "QA-003@e3f4g5"
title: "Improve test coverage for subagents generator"
description: "Add tests for subagents generator (currently 16% coverage)"
created: 2026-01-03
section: "testing"
tags: [testing, coverage, generator, subagents]
type: quality
priority: medium
status: proposed
references:
  - src/dot_work/subagents/generator.py
  - tests/unit/subagents/test_generator.py (to be created)
---

### Problem
The subagents generator has only 16% coverage. Core functionality needs better testing.

### Affected Files
- **New**: `tests/unit/subagents/test_generator.py`

### Coverage Details
Current: 16% (71 of 85 lines missing)

### Acceptance Criteria
- [ ] Test file created
- [ ] Coverage increased to 75%+
- [ ] All tests passing

### Estimated Effort
3-4 hours

---
