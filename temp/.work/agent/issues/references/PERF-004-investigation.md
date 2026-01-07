# PERF-004 Investigation: Scan metrics creates unnecessary intermediate lists

**Issue:** PERF-004@d6e8f3
**Started:** 2024-12-27T03:15:00Z
**Completed:** 2024-12-27T03:20:00Z
**Status**: Complete

---

## Problem Analysis

**Root Cause:** `_update_metrics()` method created an O(N) intermediate list of all functions, then another O(N) list of complexities.

### Existing Code (lines 156-169)

```python
# BEFORE (O(N) memory):
all_functions: list[Any] = []
for file_entity in index.files.values():
    all_functions.extend(file_entity.functions)
    for cls in file_entity.classes:
        all_functions.extend(cls.methods)

if all_functions:
    complexities = [f.complexity for f in all_functions]  # Another O(N) list!
    index.metrics.avg_complexity = sum(complexities) / len(complexities)
    index.metrics.max_complexity = max(complexities)
```

**Performance Issues:**
1. `all_functions` list holds ALL function objects (O(N) memory)
2. `complexities` list duplicates complexity values (O(N) memory)
3. For large codebases (10k+ functions), this adds significant memory pressure
4. Garbage collection pressure from large temporary lists

**Memory Impact:**
- Function object ~200-500 bytes each
- Complexity value ~24 bytes each
- For 10k functions: ~2-5 MB for all_functions + ~240 KB for complexities
- For 100k functions: ~20-50 MB + ~2.4 MB

---

## Solution Implemented

### Streaming Calculation (O(1) additional memory)

```python
# AFTER (O(1) additional memory):
sum_complexity = 0
max_complexity = 0
high_complexity_functions: list[str] = []

for file_entity in index.files.values():
    for func in file_entity.functions:
        sum_complexity += func.complexity
        max_complexity = max(max_complexity, func.complexity)
        if func.complexity > 10:
            high_complexity_functions.append(
                f"{func.name} ({func.file_path}:{func.line_no})"
            )
    for cls in file_entity.classes:
        for method in cls.methods:
            sum_complexity += method.complexity
            max_complexity = max(max_complexity, method.complexity)
            if method.complexity > 10:
                high_complexity_functions.append(
                    f"{method.name} ({method.file_path}:{method.line_no})"
                )

if index.metrics.total_functions > 0:
    index.metrics.avg_complexity = sum_complexity / index.metrics.total_functions
    index.metrics.max_complexity = max_complexity
    index.metrics.high_complexity_functions = high_complexity_functions
```

**Key Changes:**
1. No intermediate `all_functions` list
2. No `complexities` list - calculate `sum` and `max` incrementally
3. Only `high_complexity_functions` list remains (typically small)
4. Calculate `avg` from `sum / count` (no list needed)

---

## Affected Files

- `src/dot_work/python/scan/service.py` (lines 145-184: `_update_metrics` method)

---

## Changes Made

### File: `src/dot_work/python/scan/service.py`

**Before:**
```python
def _update_metrics(self, index: CodeIndex) -> None:
    # ...
    all_functions: list[Any] = []
    for file_entity in index.files.values():
        all_functions.extend(file_entity.functions)
        for cls in file_entity.classes:
            all_functions.extend(cls.methods)

    if all_functions:
        complexities = [f.complexity for f in all_functions]
        index.metrics.avg_complexity = sum(complexities) / len(complexities)
        index.metrics.max_complexity = max(complexities)
        index.metrics.high_complexity_functions = [
            f"{f.name} ({f.file_path}:{f.line_no})" for f in all_functions if f.complexity > 10
        ]
```

**After:**
```python
def _update_metrics(self, index: CodeIndex) -> None:
    """Calculate metrics incrementally to avoid O(N) memory usage."""
    # ...
    sum_complexity = 0
    max_complexity = 0
    high_complexity_functions: list[str] = []

    for file_entity in index.files.values():
        for func in file_entity.functions:
            sum_complexity += func.complexity
            max_complexity = max(max_complexity, func.complexity)
            if func.complexity > 10:
                high_complexity_functions.append(f"{func.name} ({func.file_path}:{func.line_no})")
        for cls in file_entity.classes:
            for method in cls.methods:
                sum_complexity += method.complexity
                max_complexity = max(max_complexity, method.complexity)
                if method.complexity > 10:
                    high_complexity_functions.append(f"{method.name} ({method.file_path}:{method.line_no})")

    if index.metrics.total_functions > 0:
        index.metrics.avg_complexity = sum_complexity / index.metrics.total_functions
        index.metrics.max_complexity = max_complexity
        index.metrics.high_complexity_functions = high_complexity_functions
```

---

## Outcome

**Validation Results:**
- All 56 scan/metrics tests pass
- Memory growth: +93.5 MB (full test suite, includes other tests)
- Test runtime: 11.59s
- Same metrics values produced (verified by tests)

**Performance Improvements:**
1. O(N) → O(1) additional memory for complexity calculation
2. No large intermediate lists created
3. Reduced GC pressure
4. Same correctness - all tests pass

**Memory Savings (estimated):**
| Codebase Size | Before (all_functions + complexities) | After |
|---------------|----------------------------------------|------|
| 1k functions  | ~250 KB + ~24 KB = ~274 KB           | ~1 KB |
| 10k functions | ~2.5 MB + ~240 KB = ~2.7 MB         | ~1 KB |
| 100k functions| ~25 MB + ~2.4 MB = ~27.4 MB        | ~1 KB |

---

## Acceptance Criteria

- [x] Metrics calculation uses O(1) additional memory
- [x] No intermediate list of all functions created
- [x] Tests verify same metrics values produced
- [x] All scan/metrics tests pass (56 tests)

---

## Notes

- This is a common optimization pattern: replace "collect all, then process" with "process incrementally"
- For aggregations (sum, max, avg, count), streaming is always more memory-efficient
- The `high_complexity_functions` list remains because it's output, not intermediate state
- Related: PERF-005 (JSON formatting), PERF-006 (Git file scanner), PERF-007 (Batch operations)
