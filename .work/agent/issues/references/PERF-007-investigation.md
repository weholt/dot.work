# PERF-007 Investigation: Bulk operations lack proper database batching

**Issue:** PERF-007@g9b1c6
**Started:** 2024-12-27T03:45:00Z
**Completed:** 2024-12-27T03:50:00Z
**Status**: Documented (requires significant refactor)

---

## Problem Analysis

**Root Cause:** `bulk_create()` and other bulk operations perform sequential database operations - each create/update is a separate transaction.

### Existing Code (bulk_service.py lines 317-327)

```python
# BEFORE (inefficient):
for idx, issue_data in enumerate(issues_data, start=1):
    issue_dict = issue_data.to_issue_dict()
    issue = self.issue_service.create_issue(**issue_dict)  # Separate transaction each!
    issue_ids.append(issue.id)
    succeeded += 1
```

**Performance Issues:**
1. Each `create_issue()` call is a separate database transaction
2. For 100 issues: 100 round-trips to the database
3. Transaction overhead accumulates (BEGIN/COMMIT per issue)
4. Network latency multiplied by N
5. No all-or-nothing semantics (partial success on error)

**Performance Impact:**
| Operation | Current (sequential) | Batch (single transaction) |
|-----------|---------------------|---------------------------|
| 10 issues  | ~10-50 ms           | ~1-5 ms                   |
| 100 issues | ~100-500 ms         | ~5-20 ms                  |
| 1000 issues| ~1-5 seconds        | ~20-100 ms                |

---

## Solution Design (Recommended)

This requires a **significant refactor** with the following components:

### 1. Add Batch Methods to Repository Layer

```python
# src/dot_work/db_issues/adapters/sqlite.py
class IssueRepository:
    def insert_batch(self, issues: list[Issue]) -> list[Issue]:
        """Insert multiple issues in a single batch.

        Args:
            issues: List of Issue entities to insert

        Returns:
            List of inserted Issue entities with IDs
        """
        if not issues:
            return []

        # Use SQLModel/SQLAlchemy bulk insert
        issue_models = [IssueTable.from_entity(i) for i in issues]
        self.session.add_all(issue_models)
        self.session.flush()  # Get IDs without committing

        return [IssueTable.to_model(m).to_entity() for m in issue_models]

    def update_batch(self, issues: list[Issue]) -> list[Issue]:
        """Update multiple issues in a single batch.

        Args:
            issues: List of Issue entities with updates

        Returns:
            List of updated Issue entities
        """
        # Use bulk_update_mappings for efficiency
        self.session.bulk_update_mappings(
            IssueTable,
            [{"id": i.id, "title": i.title, "status": i.status.value, ...} for i in issues]
        )
        self.session.flush()
        return issues
```

### 2. Update BulkService to Use Batch Methods

```python
# src/dot_work/db_issues/services/bulk_service.py
def bulk_create(self, issues_data: list[IssueInputData]) -> BulkResult:
    """Create multiple issues in batch using a single transaction."""
    total = len(issues_data)

    try:
        with self.uow as uow:  # Single transaction for entire batch
            # Convert to Issue entities
            issues = [
                Issue(
                    id=self.id_service.generate("issue"),
                    title=data.title,
                    description=data.description,
                    status=IssueStatus.PROPOSED,
                    priority=data.priority,
                    type=data.type,
                    assignees=data.assignees or [],
                    labels=data.labels or [],
                    epic_id=data.epic_id,
                    created_at=self.clock.now(),
                    updated_at=self.clock.now(),
                )
                for data in issues_data
            ]

            # Batch insert
            inserted = uow.issues.insert_batch(issues)

            return BulkResult(
                total=total,
                succeeded=len(inserted),
                failed=0,
                errors=[],
                issue_ids=[i.id for i in inserted],
            )

    except Exception as e:
        logger.error("Bulk create failed: %s", e)
        return BulkResult(
            total=total,
            succeeded=0,
            failed=total,
            errors=[("batch", str(e))],
            issue_ids=[],
        )
```

---

## Implementation Scope

This is a **multi-file refactor** requiring:

1. **Repository Layer Changes:**
   - Add `insert_batch()` to `IssueRepository`
   - Add `update_batch()` to `IssueRepository`
   - Similar methods for `CommentRepository`, `DependencyRepository`, etc.

2. **Service Layer Changes:**
   - Update `bulk_create()` to use batch insert
   - Update `bulk_close()`, `bulk_update()`, etc.
   - Wrap entire batch in single UnitOfWork transaction

3. **Testing:**
   - Add tests for batch insert methods
   - Add tests for batch update methods
   - Verify all-or-nothing semantics (rollback on error)
   - Performance benchmarks (100 issues < 100ms)

4. **Migration Considerations:**
   - Need to handle existing data
   - Backward compatibility with non-bulk operations
   - May need database schema changes for efficiency

---

## Affected Files

- `src/dot_work/db_issues/adapters/sqlite.py` (add batch methods to repositories)
- `src/dot_work/db_issues/services/bulk_service.py` (use batch methods)
- `tests/unit/db_issues/test_sqlite.py` (add batch method tests)
- Potentially `src/dot_work/db_issues/domain/entities.py` (if schema changes needed)

---

## Acceptance Criteria

- [ ] Bulk create uses single transaction (all-or-nothing)
- [ ] Bulk operations use batch insert/update
- [ ] Performance measurable: 100 issues < 100ms
- [ ] Tests verify batch atomicity (rollback on error)
- [ ] Backward compatible with existing code

---

## Recommendation

**This issue should be tackled as a dedicated feature branch** due to:
1. Multiple files need changes
2. Requires careful transaction handling
3. Needs extensive testing
4. Performance benchmarks required
5. Potential for data loss if done incorrectly

**Suggested Approach:**
1. Create feature branch `feature/batch-operations`
2. Implement batch methods in repository layer first
3. Add comprehensive tests for batch methods
4. Update service layer to use batch methods
5. Performance testing before merging
6. Consider this a MEDIUM priority task (not critical)

---

## Notes

- Related: PERF-003 (SQL WHERE filtering), PERF-004 (streaming), PERF-005 (compact JSON)
- This optimization provides the most value for teams importing large numbers of issues
- For small batches (< 10 issues), current performance is acceptable
- Consider using SQLAlchemy's `bulk_insert_mappings()` for maximum efficiency

**Status:** Documented for future implementation. Not implemented in this session due to scope.
