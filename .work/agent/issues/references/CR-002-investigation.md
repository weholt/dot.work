# CR-002 Investigation: Missing Test Coverage for Container/Provision

**Issue:** CR-002@b3d5e7
**Started:** 2025-12-27T14:30:00Z
**Status:** In Progress

---

## Problem Analysis

**Current State:**
- `container/provision/core.py`: 889 lines of critical Docker orchestration code
- `tests/unit/container/provision/test_core.py`: Only 39 lines testing `RepoAgentError`
- **Coverage**: ~0% for actual business logic

**Functions Needing Tests:**

### 1. Validation Functions (Easy to Test)
- `validate_docker_image(image: str)` - Lines 58-70
- `validate_dockerfile_path(dockerfile, project_root)` - Lines 73-89

### 2. Helper Functions (Medium Complexity)
- `_bool_meta(meta, key, default)` - Lines 179-201
- `_load_frontmatter(path)` - Lines 204-217

### 3. Core Configuration (High Complexity)
- `_resolve_config(instructions_path, cli_overrides)` - Lines 220-392 (~172 lines)

### 4. Docker Command Building
- `_build_env_args(config)` and `_build_volume_args(config)`

---

## Implementation Plan

### Phase 1: Validation Functions (Quick Win)
Add tests for validation functions with various edge cases

### Phase 2: Helper Functions
Add tests for boolean parsing and frontmatter loading

### Phase 3: Configuration Resolution (Most Important)
Add comprehensive tests for config resolution with all scenarios

---

## Acceptance Criteria
- [ ] Validation functions have 100% coverage
- [ ] Helper functions have 90%+ coverage
- [ ] `_resolve_config()` has 80%+ coverage
- [ ] Overall module coverage ≥70%
