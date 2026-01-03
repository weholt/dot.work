# Critical Issues (P0)

Blockers, security issues, data loss risks.

---
---
id: "CR-002@d9b4c3"
title: "Add test coverage for skills/subagents global defaults and parser changes"
description: "Zero test coverage for new parser features (_deep_merge, _load_global_defaults, SkillEnvironmentConfig)"
created: 2026-01-03
section: "tests"
tags: [tests, coverage, skills, subagents, parser]
type: test
priority: critical
status: proposed
references:
  - src/dot_work/skills/parser.py
  - src/dot_work/subagents/parser.py
  - src/dot_work/skills/models.py
  - tests/unit/
---

### Problem
Recent changes to skills/subagents parsers introduced significant new functionality with **zero test coverage**:

1. **No tests** for `_deep_merge()` function (complex merge logic with special behaviors)
2. **No tests** for `_load_global_defaults()` function
3. **No tests** for `SkillEnvironmentConfig` validation
4. **No tests** for merged defaults behavior
5. **No tests** for empty string validation (CR-001)
6. **No tests** for mutual exclusion logic (filename vs filename_suffix)
7. **No integration tests** for parser with global defaults
8. **No tests** for bundled_*/ directories

### Affected Files
- `src/dot_work/skills/parser.py` (_deep_merge, _load_global_defaults)
- `src/dot_work/subagents/parser.py` (_deep_merge, _load_global_defaults)
- `src/dot_work/skills/models.py` (SkillEnvironmentConfig)
- `tests/unit/` (needs new test files)

### Importance
**CRITICAL:** The lack of test coverage creates several risks:

1. **CR-001 (empty string bug)** would have been caught by tests
2. **Regressions** will occur when modifying parser logic
3. **Undefined behavior** in edge cases (malformed global.yml, etc.)
4. **No safety net** for refactoring
5. **Violates project requirement**: Test coverage >= 75%

The `_deep_merge()` function in particular has complex logic (deep merge, empty-dict-preservation, mutual-exclusion cleanup) that MUST be tested.

### Proposed Solution
Create comprehensive test coverage for the new parser functionality:

**New test files:**
- `tests/unit/skills/test_models.py` - Test SkillEnvironmentConfig
- `tests/unit/skills/test_parser.py` - Test parser functions
- `tests/unit/subagents/test_models.py` - Test SubagentEnvironmentConfig
- `tests/unit/subagents/test_parser.py` - Test parser functions

**Required tests:**

```python
# tests/unit/skills/test_models.py
def test_skill_environment_config_valid_with_target():
    """Valid config with only target."""

def test_skill_environment_config_valid_with_filename():
    """Valid config with target and filename."""

def test_skill_environment_config_valid_with_filename_suffix():
    """Valid config with target and filename_suffix."""

def test_skill_environment_config_mutual_exclusion():
    """Cannot specify both filename and filename_suffix."""

def test_skill_environment_config_empty_filename():
    """Empty filename should raise ValueError (or be treated as None based on fix)."""

def test_skill_environment_config_empty_filename_suffix():
    """Empty filename_suffix should raise ValueError (or be treated as None based on fix)."""

# tests/unit/skills/test_parser.py
def test_deep_merge_basic():
    """Basic deep merge behavior."""

def test_deep_merge_empty_dict_preserves_defaults():
    """Empty local dict should preserve global defaults."""

def test_deep_merge_local_overrides_global():
    """Local values override global values."""

def test_deep_merge_filename_mutual_exclusion():
    """Specifying filename removes filename_suffix from global."""

def test_deep_merge_filename_suffix_mutual_exclusion():
    """Specifying filename_suffix removes filename from global."""

def test_load_global_defaults_file_exists():
    """Load global.yml when file exists."""

def test_load_global_defaults_file_missing():
    """Return empty dict when global.yml missing."""

def test_load_global_defaults_malformed_yaml():
    """Handle malformed YAML gracefully."""

def test_parse_skill_with_global_defaults():
    """Skill parsing should merge global defaults."""

def test_parse_skill_local_override_global():
    """Local frontmatter overrides global defaults."""

def test_parse_skill_empty_environments_preserves_global():
    """Empty environments dict in skill should preserve global defaults."""
```

### Acceptance Criteria
- [ ] `tests/unit/skills/test_models.py` created with all SkillEnvironmentConfig tests
- [ ] `tests/unit/skills/test_parser.py` created with all parser tests
- [ ] `tests/unit/subagents/test_models.py` created
- [ ] `tests/unit/subagents/test_parser.py` created
- [ ] All new tests pass
- [ ] Test coverage >= 75% (project requirement)
- [ ] CR-001 bug would be caught by new tests

### Notes
This is a quality gate failure. The parser changes should not have been merged without tests. Adding tests now is critical to prevent regressions and catch bugs like CR-001.

