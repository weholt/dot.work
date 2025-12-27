# SEC-006 Investigation: Incomplete error handling exposes system paths

**Issue:** SEC-006@94eb69
**Started:** 2024-12-27T00:25:00Z
**Status:** In Progress

---

## Problem Analysis

**Root Cause:** Error messages leak internal information (project names, topic names) that could assist attackers.

### Location 1: search_semantic.py

**Line 357:**
```python
raise ValueError(f"Project not found: {scope.project}")
```

**Lines 367, 374:**
```python
raise ValueError(f"Topic not found: {topic_name}")
```

### Location 2: search_fts.py

**Line 406:**
```python
raise ValueError(f"Project not found: {scope.project}")
```

**Lines 416, 423:**
```python
raise ValueError(f"Topic not found: {topic_name}")
```

---

## Security Impact

**Information Disclosure:**
- Attacker learns which project names exist (by trying different names)
- Attacker learns which topics are being used in the system
- Could reveal internal project structure or naming conventions
- Could assist in social engineering attacks

**OWASP ASVS 2023 v5.0:**
- V5.4: "Verify that the application does not leak internal information in error messages"

---

## Proposed Solution

Use generic error messages for users, log detailed errors for debugging:

```python
import logging

logger = logging.getLogger(__name__)

# Instead of:
raise ValueError(f"Project not found: {scope.project}")

# Use:
logger.debug(f"Project not found: {scope.project}", exc_info=True)
raise ValueError("Project not found")

# Instead of:
raise ValueError(f"Topic not found: {topic_name}")

# Use:
logger.debug(f"Topic not found: {topic_name}", exc_info=True)
raise ValueError("Topic not found")
```

---

## Affected Files
- `src/dot_work/knowledge_graph/search_semantic.py` (lines 357, 367, 374)
- `src/dot_work/knowledge_graph/search_fts.py` (lines 406, 416, 423)

---

## Acceptance Criteria
- [ ] All user-facing errors use generic messages
- [ ] Detailed errors logged but not shown to users
- [ ] Tests verify error messages don't leak sensitive data
- [ ] All existing tests pass

---

## Next Steps
1. Add logging import to affected files
2. Replace leaking error messages with generic versions
3. Add debug logging for detailed information
4. Run validation
