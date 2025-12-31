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


