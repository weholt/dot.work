# Shortlist

High-priority issues ready for implementation.

---
id: "QA-003@e3f4g5"
title: "Improve test coverage for subagents generator"
description: "Add tests for subagents generator (currently 16% coverage)"
created: 2026-01-03
section: "testing"
tags: [testing, coverage, generator, subagents]
type: quality
priority: high
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
