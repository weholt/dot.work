id: "QA-001@b1c2d3"
title: "Improve test coverage for subagents CLI"
description: "Add tests for subagents CLI commands (currently 15% coverage)"
created: 2026-01-03
section: "testing"
tags: [testing, coverage, cli, subagents]
type: quality
priority: high
status: proposed
references:
  - src/dot_work/subagents/cli.py
  - tests/unit/subagents/test_cli.py (to be created)
---

### Problem
The subagents CLI module has only 15% test coverage, which is below the project's 75% target. This is a high-risk area since it's user-facing code.

### Affected Files
- **New**: `tests/unit/subagents/test_cli.py`
- Modify: None (test addition only)

### Coverage Details
Current: 15% (155 of 183 lines missing)
Missing:
- list_subagents command (lines 57-105)
- validate_subagent command (lines 129-173)
- show_subagent command (lines 200-252)
- generate_native command (lines 290-321)
- sync_subagents command (lines 341-375)
- init_subagent command (lines 421-460)
- list_environments command (lines 470-490)

### Proposed Tests
1. Test list_subagents with various environments
2. Test validate_subagent with valid/invalid files
3. Test show_subagent with existing/nonexistent agents
4. Test generate_native with canonical subagent
5. Test sync_subagents with multi-environment config
6. Test init_subagent template generation
7. Test list_environments output
8. Test error handling for each command

### Acceptance Criteria
- [ ] Test file created with comprehensive coverage
- [ ] All commands have at least one happy path test
- [ ] All commands have error path tests
- [ ] Coverage for cli.py increased to 75%+
- [ ] All tests passing

### Estimated Effort
4-6 hours

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
