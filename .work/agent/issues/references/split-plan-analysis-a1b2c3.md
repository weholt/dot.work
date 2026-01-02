# Split Plan Analysis & Clarifications

Reference note for SPLIT-* issues.

Created: 2026-01-02
Related: split.md, SPLIT-001 through SPLIT-015

## Summary

The split.md plan is comprehensive but has several gaps that need clarification before implementation.

## Open Clarifications (2 questions)

### Q1: GitHub Organization Name (SPLIT-003)

**Issue**: What GitHub organization should host the extracted plugin repositories?

**Context**: The split.md plan references `github.com/<org>/dot-container`, etc. but doesn't specify the organization name.

**Options**:
- A) Same user account (e.g., `github.com/username/dot-issues`)
- B) New organization (e.g., `github.com/dot-work-plugins/dot-issues`)
- C) Existing organization (specify name)

**Impact**: Affects pyproject.toml URLs, README links, CI workflows, and publishing credentials.

**Decision Required**: User must specify organization name.

---

### Q2: Duplicate Test Files for Review Module (SPLIT-005)

**Issue**: The review module has duplicate test files in two locations:
- `tests/unit/review/test_*.py` (3 files)
- `tests/unit/test_review_*.py` (5 files)

**Context**: Some files may have overlapping test cases, or they may test different aspects.

**Options**:
- A) Merge them (review all tests, remove true duplicates)
- B) Keep both (copy all files to new package)

**Impact**: Affects test count and maintenance burden.

**Decision Required**: User preference on handling duplicates.

---

## Resolved Decisions (from split.md)

| Decision | Resolution |
|----------|------------|
| Entry point group name | `dot_work.plugins` |
| Package naming | `dot-<name>` (pip), `dot_<name>` (Python) |
| CLI registration | Via `CLI_GROUP` constant in plugin `__init__.py` |
| Standalone vs plugin | Both - plugins register with dot-work AND have standalone CLI |
| Version bump | 0.2.0 for breaking change |
| Optional deps pattern | Preserved (e.g., `llm`, `all`) |

---

## Dependency Graph

```
SPLIT-001 (plugin discovery)
    ├── SPLIT-002 (cli refactor)
    │   ├── SPLIT-003 (dot-issues) ─────┐
    │   ├── SPLIT-004 (dot-kg) ─────────┤
    │   ├── SPLIT-005 (dot-review) ─────┤
    │   ├── SPLIT-008 (dot-container) ──┤
    │   ├── SPLIT-009 (dot-git) ────────┼── SPLIT-007 (pyproject.toml)
    │   ├── SPLIT-010 (dot-harness) ────┤       │
    │   ├── SPLIT-011 (dot-overview) ───┤       ├── SPLIT-014 (integration tests)
    │   ├── SPLIT-012 (dot-python) ─────┤       │
    │   └── SPLIT-013 (dot-version) ────┘       └── SPLIT-015 (documentation)
    │
SPLIT-006 (automation script) ─ accelerates all extractions
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Circular imports after split | Medium | High | Analyze cross-module deps before extraction |
| CI/CD credential management | Low | Medium | Use GitHub org secrets for PyPI |
| Plugin version conflicts | Medium | Medium | Pin minimum versions in optional-deps |
| Test isolation failures | Low | High | Run full integration tests before release |
| User migration friction | Medium | Medium | Provide `dot-work[all]` for backward compat |

---

## Cross-Module Import Analysis

Checked for cross-module dependencies that would complicate extraction:

| Module | Imports from other submodules? | Status |
|--------|-------------------------------|--------|
| db_issues | No | Clean extraction |
| knowledge_graph | No | Clean extraction |
| container | No | Clean extraction |
| git | No | Clean extraction |
| harness | No | Clean extraction |
| overview | No | Clean extraction |
| python | No | Clean extraction |
| review | No | Clean extraction |
| version | No | Clean extraction |

**Finding**: All submodules are self-contained. No circular dependencies exist.

---

## Implementation Order Recommendation

Based on dependencies and complexity:

1. **Week 1**: SPLIT-001, SPLIT-006 (infrastructure)
2. **Week 2**: SPLIT-002 (cli refactor, enables all extractions)
3. **Week 2-3**: SPLIT-003 (db_issues - largest, most complex)
4. **Week 3**: SPLIT-004 (kg), SPLIT-005 (review - needs attention)
5. **Week 4**: SPLIT-008, SPLIT-009, SPLIT-010 (container, git, harness)
6. **Week 4-5**: SPLIT-011, SPLIT-012, SPLIT-013 (overview, python, version)
7. **Week 5-6**: SPLIT-007, SPLIT-014, SPLIT-015 (integration, docs)

---

## Notes

- The plan correctly identifies that `zip` and `utils` should remain in core
- The `skills`, `subagents`, and `tools` folders are correctly retained
- The prompts folder is critical for AI agent functionality
- Consider a monorepo approach if managing 9 separate repos becomes burdensome
