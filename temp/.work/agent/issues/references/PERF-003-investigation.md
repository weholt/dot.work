# PERF-003 Investigation: Issue service loads all issues for stale/epic queries

**Issue:** PERF-003@c5d9e1
**Started:** 2024-12-26T23:40:00Z
**Status:** In Progress

---

## Problem Analysis

### Location 1: `get_stale_issues()` at line 744

```python
# Get all issues (limit high to get all)
all_issues = self.list_issues(limit=100000)

# Filter stale issues
stale_issues = [issue for issue in all_issues if issue.updated_at < cutoff]
```

**Problem:** Fetches ALL issues from database, then filters by `updated_at < cutoff` in Python.

### Location 2: `get_epic_issues()` at line 666

```python
# Get all issues with this epic_id
all_issues = self.uow.issues.list_all(limit=1000000)
epic_issues = [issue for issue in all_issues if issue.epic_id == epic_id]
```

**Problem:** Fetches ALL issues from database, then filters by `epic_id` in Python.

**BUT:** Repository already has `list_by_epic()` method at sqlite.py:572!
The service is NOT using the existing efficient method.

---

## Root Cause

1. **Stale issues**: No repository method for date-based filtering → Need to add `list_updated_before()`
2. **Epic issues**: Repository method exists but service doesn't use it → Simple fix

---

## Proposed Solution

### Fix 1: `get_epic_issues()` - Use existing repository method

**Current (inefficient):**
```python
all_issues = self.uow.issues.list_all(limit=1000000)
epic_issues = [issue for issue in all_issues if issue.epic_id == epic_id]
```

**Proposed (efficient):**
```python
epic_issues = self.uow.issues.list_by_epic(epic_id, limit=100000)
```

The `list_by_epic()` method already exists and does SQL filtering:
```python
statement = select(IssueModel).where(IssueModel.epic_id == epic_id)
```

### Fix 2: `get_stale_issues()` - Add new repository method

**Add to sqlite.py:**
```python
def list_updated_before(self, cutoff: datetime, limit: int = 100, offset: int = 0) -> list[Issue]:
    """List issues updated before a cutoff date.

    Args:
        cutoff: Cutoff datetime - only return issues updated before this time
        limit: Maximum number of issues to return
        offset: Number of issues to skip

    Returns:
        List of issues updated before cutoff
    """
    statement = (
        select(IssueModel)
        .where(IssueModel.updated_at < cutoff)
        .order_by(IssueModel.updated_at)
        .limit(limit)
        .offset(offset)
    )
    models = self.session.exec(statement).all()
    return self._models_to_entities(models)
```

**Then update service:**
```python
# Before (inefficient):
all_issues = self.list_issues(limit=100000)
stale_issues = [issue for issue in all_issues if issue.updated_at < cutoff]

# After (efficient):
stale_issues = self.uow.issues.list_updated_before(cutoff, limit=100000)
```

---

## Affected Files
- `src/dot_work/db_issues/services/issue_service.py:666` (get_epic_issues - simple fix)
- `src/dot_work/db_issues/services/issue_service.py:744` (get_stale_issues - needs new repo method)
- `src/dot_work/db_issues/adapters/sqlite.py` (add list_updated_before method)

---

## Acceptance Criteria
- [ ] get_epic_issues() uses list_by_epic() instead of list_all() + Python filter
- [ ] Add list_updated_before() method to IssueRepository
- [ ] get_stale_issues() uses list_updated_before() instead of list_issues() + Python filter
- [ ] Tests verify behavior unchanged
- [ ] Performance measurable with 1000+ issues

---

## Next Steps
1. Fix get_epic_issues() to use existing list_by_epic()
2. Add list_updated_before() to repository
3. Update get_stale_issues() to use new method
4. Add tests for new repository method
5. Run validation
