# CR-003 Investigation: Missing Logging in Container/Provision

**Issue:** CR-003@c4f8a2
**Started:** 2025-12-27T14:45:00Z
**Status:** In Progress

---

## Problem Analysis

**Current State:**
- `container/provision/core.py`: 889 lines, **zero logging statements**
- Uses `print()` for dry-run output (violates AGENTS.md)
- No visibility into configuration resolution
- No debugging info for Docker/git failures

**Key Functions Needing Logging:**

### 1. Configuration Resolution (`_resolve_config`)
- Log resolved configuration at DEBUG level
- Mask sensitive values (tokens, API keys)
- Show CLI overrides vs frontmatter values

### 2. Docker Operations
- Log Docker build commands at INFO level
- Log Docker run commands at INFO level
- Log container ID after start

### 3. Git Operations
- Log repo clone operations
- Log branch checkout
- Log commit/push operations

### 4. Error Paths
- Log exceptions with context
- Log validation failures with details

---

## Implementation Plan

### Step 1: Add Logger
Add module-level logger following project conventions:
```python
import logging
logger = logging.getLogger(__name__)
```

### Step 2: Add Logging to Key Functions

**`_resolve_config()`:**
- DEBUG: Log configuration resolution (with masked secrets)
- DEBUG: Show CLI overrides applied
- DEBUG: Show frontmatter values parsed

**`run_from_markdown()`:**
- INFO: Starting repo-agent run
- DEBUG: Resolved configuration
- INFO: Docker command being executed
- INFO: Container started with ID
- INFO: Operations completed

**Error handling:**
- ERROR: Log exceptions with full context
- WARNING: Log validation failures

### Step 3: Mask Sensitive Values
Create helper function to mask secrets:
```python
def _mask_config_for_logging(config: RunConfig) -> dict[str, Any]:
    """Create a copy of config with sensitive values masked."""
    masked = {
        **dataclasses.asdict(config),
        "github_token": "***MASKED***" if config.github_token else None,
        "api_key": "***MASKED***" if config.api_key else None,
    }
    return masked
```

---

## Affected Code
- `src/dot_work/container/provision/core.py` - Add logging throughout
- All major functions need logging statements

---

## Acceptance Criteria
- [ ] Logger added to module
- [ ] Configuration resolution logged (DEBUG, masked)
- [ ] Docker commands logged (INFO)
- [ ] Git operations logged (INFO)
- [ ] Errors logged with context (ERROR)
- [ ] Sensitive values masked in logs
- [ ] Tests pass

---

## Next Steps
1. Add logger import and setup
2. Add `_mask_config_for_logging()` helper
3. Add logging to `_resolve_config()`
4. Add logging to `run_from_markdown()`
5. Add logging to error handlers
6. Run tests to verify
