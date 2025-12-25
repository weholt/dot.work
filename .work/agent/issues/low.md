# Low Priority Issues (P3)

Cosmetic, incremental improvements.

---

---
id: "PERF-008@h0c2d7"
title: "Performance: String concatenation in loops for metrics collection"
description: "String concatenation creates intermediate strings"
created: 2025-12-25
section: "python_scan"
tags: [performance, micro-optimization, string-operations]
type: performance
priority: low
status: proposed
references:
  - src/dot_work/python/scan/service.py
---

### Problem
In `service.py` line 168, string concatenation in a list comprehension:
```python
index.metrics.high_complexity_functions = [
    f"{f.name} ({f.file_path}:{f.line_no})" for f in all_functions if f.complexity > 10
]
```

While f-strings are efficient, creating many formatted strings still has overhead. For large codebases with many complex functions, this creates N string objects.

### Affected Files
- `src/dot_work/python/scan/service.py` (line 168)

### Importance
Minor optimization - the number of high-complexity functions is typically small (<100). The impact is negligible for most use cases.

### Proposed Solution
This is a micro-optimization that may not be worth pursuing unless profiling shows it's a bottleneck. The current implementation is readable and Pythonic.

### Acceptance Criteria
- [ ] Only optimize if profiling shows significant overhead
- [ ] Consider lazy evaluation or string joining if needed

### Notes
Marked as low priority because this is unlikely to be a measurable bottleneck in practice. The current code is clear and Pythonic.

---
id: "PERF-009@i1d3e8"
title: "Performance: Multiple dict lookups in repository deserialization"
description: "Repeated .get() calls with same key could be cached"
created: 2025-12-25
section: "python_scan"
tags: [performance, micro-optimization]
type: performance
priority: low
status: proposed
references:
  - src/dot_work/python/scan/repository.py
---

### Problem
In `repository.py`, methods like `_deserialize_function` (lines 151-172) use multiple `.get()` calls on the same dictionary:
```python
name=data["name"]
file_path=Path(data["file_path"])
line_no=data["line_no"]
end_line_no=data.get("end_line_no")
is_async=data.get("is_async", False)
# ... more get() calls
```

Each `get()` involves dictionary lookup overhead. For deserializing thousands of entities, this adds up.

### Affected Files
- `src/dot_work/python/scan/repository.py` (all _deserialize_* methods)

### Importance
Minor optimization - dictionary lookups are very fast in Python. This is only worth addressing if profiling shows deserialization as a bottleneck.

### Proposed Solution
Could use local variables or unpacking to reduce lookups, but current code is more readable. Only optimize if profiling shows this as a hotspot.

### Acceptance Criteria
- [ ] Only optimize if profiling shows deserialization is a bottleneck
- [ ] Maintain code readability

### Notes
Marked as low priority because dictionary lookups are O(1) and very fast in CPython. The readability of the current code likely outweighs any micro-optimization benefits.

---
(No low priority issues - CR-001 completed 2025-12-25)
