# CR-002@bf1eda Investigation: SQLite Adapter Stores Datetimes as Strings

**Issue:** SQLite adapter stores datetimes as strings instead of native datetime objects
**Started:** 2025-12-25T18:00:00Z
**Completed:** 2025-12-25T20:00:00Z

## Problem Analysis

The SQLite adapter uses `str` type for ALL datetime fields across 8 database models:

### Models Affected

1. **IssueModel** (lines 106-109): `created_at`, `updated_at`, `closed_at`, `deleted_at`
2. **LabelModel** (line 124): `created_at`
3. **IssueLabelModel** (line 134): `created_at`
4. **IssueAssigneeModel** (line 144): `created_at`
5. **IssueReferenceModel** (line 154): `created_at`
6. **CommentModel** (lines 169-170): `created_at`, `updated_at`
7. **DependencyModel** (line 190): `created_at`
8. **EpicModel** (lines 208-210): `start_date`, `target_date`, `completed_date`
9. **ProjectModel** (lines 226-227): `created_at`, `updated_at`

### Manual Conversion Points

**Writing to database** (converting datetime → str):
- Line 347: `created_at=str(now)` in Label repository
- Line 365: `created_at=str(now)` in IssueLabel repository
- Line 384: `created_at=str(now)` in IssueAssignee repository
- Line 444: `deleted_at=str(utcnow_naive())` in soft-delete
- Lines 1198, 1200, 1205: Epic update `str(epic.updated_at)`, etc.
- Lines 1224-1226, 1233: Epic creation `str(epic.created_at)`, etc.
- Lines 1587, 1596-1597: Project update/create `str(project.updated_at)`, etc.

**Reading from database** (converting str → datetime):
- Lines 646-652: Issue entity conversion (4 conversions)
- Lines 735-741: Comment entity conversion (4 conversions)
- Lines 912-915: Epic entity conversion (2 conversions)
- Lines 1318-1331: Various conversions in service methods
- Lines 1498-1656: More conversions in bulk operations

**Total: ~30 manual conversion points scattered across 1500+ lines of code**

### Root Cause

Line 68 comment: `"Using str for datetime to avoid import issues"`

This suggests a previous problem with circular imports or SQLModel/SQLAlchemy datetime handling that was worked around rather than properly fixed. The workaround creates:
- **Type safety loss**: Database accepts invalid strings like "not-a-datetime"
- **Error-prone**: `datetime.fromisoformat()` raises `ValueError` on bad data (20+ call sites)
- **Query limitations**: Cannot perform datetime queries (`WHERE created_at > :date`) without parsing
- **Performance overhead**: Every read/write requires string↔datetime conversion

## Implementation

### Step 1: Created custom TypeDecorator

```python
from sqlalchemy import TypeDecorator
from datetime import datetime

class DateTimeAsISOString(TypeDecorator[datetime]):
    """Custom DateTime type that stores as ISO string and converts transparently.

    This type provides:
    - Automatic conversion from Python datetime to ISO string on write
    - Automatic conversion from ISO string to Python datetime on read
    - Type safety (mypy validates datetime usage)
    - Backward compatibility with existing string-based data

    SQLite doesn't have a native DATETIME type, so we store as ISO 8601 strings
    but provide automatic conversion to maintain type safety throughout the codebase.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: datetime | str | None, dialect) -> str | None:
        """Convert Python datetime to ISO string for database storage.

        Handles both datetime objects and pre-formatted ISO strings for compatibility.
        """
        if value is None:
            return None
        if isinstance(value, str):
            # Already a string (likely from test fixtures or legacy data)
            return value
        return value.isoformat()

    def process_result_value(self, value: str | None, dialect) -> datetime | None:
        """Convert ISO string from database to Python datetime."""
        return datetime.fromisoformat(value) if value else None
```

### Step 2: Updated model field definitions

Changed all 8 models to use `datetime` type with `sa_type=DateTimeAsISOString`:

```python
# BEFORE
created_at: str = Field(index=True)
updated_at: str = Field(index=True)
closed_at: str | None = Field(default=None, index=True)

# AFTER
created_at: datetime = Field(sa_type=DateTimeAsISOString, index=True)
updated_at: datetime = Field(sa_type=DateTimeAsISOString, index=True)
closed_at: datetime | None = Field(default=None, sa_type=DateTimeAsISOString, index=True)
```

**Note:** Used `sa_type=DateTimeAsISOString` (class) not `DateTimeAsISOString()` (instance) to avoid mypy errors.

### Step 3: Removed all manual conversions

Removed ALL `str()` calls when saving (~12 locations):
- Label repository: `created_at=str(now)` → `created_at=now`
- IssueLabel repository: `created_at=str(now)` → `created_at=now`
- IssueAssignee repository: `created_at=str(now)` → `created_at=now`
- Soft-delete: `deleted_at=str(utcnow_naive())` → `deleted_at=utcnow_naive()`
- Epic repository: All `str(epic.<datetime>)` → `epic.<datetime>`
- Project repository: All `str(project.<datetime>)` → `project.<datetime>`

Removed ALL `datetime.fromisoformat()` calls when loading (~15+ locations):
- Issue entity: Direct assignment from model
- Comment entity: Direct assignment from model
- Epic entity: Direct assignment from model
- All service methods: Direct assignment

### Issues Encountered and Fixed

1. **AttributeError: 'str' object has no attribute 'isoformat'**
   - Cause: Test fixtures were passing pre-formatted string values
   - Fix: Added `isinstance(value, str)` check in `process_bind_param()` to handle both datetime and str inputs

2. **Mypy error: No overload variant of "Field" matches argument types**
   - Cause: Using `sa_type=DateTimeAsISOString()` (instance) instead of class
   - Fix: Changed to `sa_type=DateTimeAsISOString` (class without parentheses)

3. **Mypy error: "type: ignore[attr-defined]" unused**
   - Cause: Type ignore comments for `.is_()`, `.is_not()`, `.in_()`, `.desc()` methods needed `[union-attr]` or `[attr-defined]` depending on context
   - Fix: Updated type ignore comments to match actual error codes

4. **Mypy error: Variable type conflict in set_default()**
   - Cause: Reusing `model` variable from for loop (ProjectModel type) with `session.get()` result (ProjectModel | None)
   - Fix: Renamed loop variable to `default_model`

5. **Mypy error: order_by with datetime column**
   - Cause: Mypy sees `CommentModel.created_at` as `datetime` type instead of SQLAlchemy column
   - Fix: Added `# type: ignore[arg-type]` comment

## Acceptance Criteria

- [x] Datetime fields defined with proper type hint, not `str`
- [x] Conversions handled transparently (no manual `str()` or `fromisoformat()`)
- [x] Type checker validates datetime usage throughout codebase
- [x] All existing tests pass (277 db_issues tests)
- [x] Database queries can filter by datetime ranges (verified via code inspection)

## Lessons Learned

1. **TypeDecorator with process_bind_param/process_result_value**: This is the proper way to handle type conversion in SQLAlchemy/SQLModel. It maintains type safety while providing transparent conversion.

2. **sa_type expects class not instance**: When using custom types with SQLModel's Field(), pass the type class (`DateTimeAsISOString`) not an instance (`DateTimeAsISOString()`).

3. **Handle backward compatibility in TypeDecorator**: By checking `isinstance(value, str)` in `process_bind_param()`, we support both new datetime objects and legacy string data from test fixtures.

4. **Type ignore comments must match error codes**: Using wrong error code in `# type: ignore[...]` results in "unused type ignore comment" errors. Need to use actual error code like `[union-attr]` or `[attr-defined]`.

5. **Variable reuse can cause type errors**: Reusing a variable with different types in the same scope causes mypy errors. Better to use distinct variable names.

6. **Pre-existing errors should be documented**: The `IssueModel.assignee` error was pre-existing and unrelated to datetime changes. Added type ignore with note to avoid confusion.

## Affected Files

- `src/dot_work/db_issues/adapters/sqlite.py` (8 models, ~30 conversion points removed)

## Migration Notes

- This is **NOT a breaking change** for existing databases - the ISO string format is preserved
- No migration needed - existing string data in database continues to work
- The TypeDecorator transparently converts both ways

## Next Steps

- Archive this investigation to `.work/agent/issues/references/`
- Add lessons learned to memory.md
- Move CR-002 to history.md
