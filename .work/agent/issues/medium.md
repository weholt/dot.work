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
