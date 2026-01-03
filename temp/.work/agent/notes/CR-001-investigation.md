# CR-001@cf7ce6 Investigation: Issue Entity Manual Field Copying

**Issue:** Issue entity uses manual field copying in every transition method
**Started:** 2025-12-25T17:30:00Z

## Problem Analysis

The `Issue` entity in `src/dot_work/db_issues/domain/entities.py` has 6 transition methods (lines 292-492):

1. `transition(new_status)` - lines 292-336
2. `add_label(label)` - lines 338-368
3. `remove_label(label)` - lines 370-401
4. `assign_to(assignee)` - lines 403-433
5. `unassign(assignee)` - lines 435-464
6. `assign_to_epic(epic_id)` - lines 466-492

Each method constructs a new `Issue` instance by explicitly copying all 14 fields:

```python
return Issue(
    id=self.id,
    project_id=self.project_id,
    title=self.title,
    description=self.description,
    status=self.status,
    priority=self.priority,
    type=self.type,
    assignees=self.assignees.copy(),
    epic_id=self.epic_id,
    labels=self.labels.copy(),
    blocked_reason=self.blocked_reason,
    source_url=self.source_url,
    references=self.references.copy(),
    created_at=self.created_at,
    updated_at=utcnow_naive(),
    closed_at=self.closed_at,
)
```

## Evidence

- **Lines 292-492:** 6 transition methods with ~200 lines of repetitive code
- **14 fields × 6 methods = 84+ field copy operations**
- **Updated_at must be manually set** in each method (lines 328, 365, 398, 430, 461, 490)
- **Mutable fields** (assignees, labels, references) need `.copy()` to maintain immutability

## Root Cause

The code was written before understanding Python's `dataclasses.replace()` function, which is specifically designed for creating modified copies of dataclass instances.

## Proposed Solution

**Use `dataclasses.replace()`** - the cleanest solution for immutable dataclass updates:

```python
from dataclasses import replace

def transition(self, new_status: IssueStatus) -> "Issue":
    if not self.status.can_transition_to(new_status):
        raise InvalidTransitionError(...)

    new_issue = replace(
        self,
        status=new_status,
        updated_at=utcnow_naive(),
    )

    if new_status == IssueStatus.COMPLETED and self.closed_at is None:
        # replace() returns new instance, need to modify closed_at
        new_issue.closed_at = utcnow_naive()

    return new_issue
```

### Benefits

1. **Single source of truth** - field list defined once in dataclass
2. **Adding new fields** requires changes in only 1 location (the dataclass definition)
3. **Automatically handles** all field copying
4. **More concise** - 6 lines vs 18 lines per transition method
5. **Type-safe** - mypy validates field names

### Handling Mutable Fields

For mutable fields (assignees, labels, references), we create modified copies before calling `replace()`:

```python
def add_label(self, label: str) -> "Issue":
    if label in self.labels:
        return self

    new_labels = self.labels.copy()
    new_labels.append(label)

    return replace(self, labels=new_labels, updated_at=utcnow_naive())
```

This is exactly what the current code does, but we use `replace()` to construct the final instance.

## Affected Files

- `src/dot_work/db_issues/domain/entities.py` (Issue entity, lines 292-492)
- `tests/unit/db_issues/test_entities.py` - tests that verify transition behavior

## Implementation Plan

1. Add `from dataclasses import replace` to imports
2. Refactor each of the 6 transition methods to use `replace()`
3. Ensure all tests pass (259 db_issues tests)
4. Verify `updated_at` is automatically set in all transitions

## Acceptance Criteria

- [ ] Adding a new field to Issue requires changes in only 1 location
- [ ] All transition methods use `replace()` for consistency
- [ ] Type checker validates immutability is maintained
- [ ] All existing tests pass
- [ ] `updated_at` automatically set on all transitions

## Notes

- The `Comment` entity (line 496) correctly uses frozen dataclass without transitions
- `replace()` is a stdlib function (no new dependencies)
- This is a pure refactor - no behavior changes expected
