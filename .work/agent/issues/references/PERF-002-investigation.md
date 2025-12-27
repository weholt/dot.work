# PERF-002 Investigation: File scanner nested fnmatch loop

**Issue:** PERF-002@b4e7d2
**Started:** 2024-12-26T23:15:00Z
**Status:** In Progress

---

## Problem Analysis

**Location:** `src/dot_work/python/scan/scanner.py:77`

```python
if self.include_patterns:
    if not any(fnmatch.fnmatch(file, pattern) for pattern in self.include_patterns):
        continue
```

### Root Cause
The nested loop at line 77 calls `fnmatch.fnmatch()` for **every pattern** against **every file**:

```python
for file in files:                           # N files
    for pattern in self.include_patterns:   # M patterns
        fnmatch.fnmatch(file, pattern)      # String parsing + regex compilation
```

### Why This Is Slow
1. **fnmatch.fnmatch() is expensive** - Each call does string parsing and potentially compiles a regex
2. **O(N*M) complexity** - Where N = files, M = patterns
3. **Called for every file** - Even when patterns don't match

### Example Impact
- 10,000 files × 10 patterns = 100,000 fnmatch calls
- 10,000 files × 50 patterns = 500,000 fnmatch calls
- Each call involves string parsing and regex compilation

---

## Proposed Solution

Use `fnmatch.translate()` to pre-compile patterns into regex objects **once** before the file loop:

```python
import fnmatch
import re
from typing import Pattern

class ASTScanner:
    def __init__(self, ...):
        self.include_patterns = include_patterns or ["*.py"]
        # Pre-compile patterns into regex objects
        self._compiled_patterns: list[Pattern] = [
            re.compile(fnmatch.translate(pattern))
            for pattern in self.include_patterns
        ]

    def _find_python_files(self) -> list[Path]:
        for file in files:
            if self._compiled_patterns:
                if not any(pattern.match(file) for pattern in self._compiled_patterns):
                    continue
```

### Benefits
1. **Patterns compiled once** - Not recompiled for every file
2. **O(N) complexity** - Where N = files (patterns are pre-compiled)
3. **Regex matching is faster** - Pre-compiled regex objects
4. **Same behavior** - fnmatch.translate() produces equivalent regex patterns

---

## Affected Code
- `src/dot_work/python/scan/scanner.py:77` (nested fnmatch loop)
- `src/dot_work/python/scan/scanner.py:34` (include_patterns assignment - needs compiled patterns)

---

## Acceptance Criteria
- [ ] Patterns compiled once in `__init__`
- [ ] Line 77 uses pre-compiled regex objects
- [ ] Time complexity reduced to O(N) where N = files
- [ ] Tests verify filtering behavior unchanged
- [ ] Benchmark shows improvement

---

## Next Steps
1. Implement pre-compiled patterns in `__init__`
2. Update line 77 to use compiled patterns
3. Add unit tests for pattern matching
4. Run validation tests
5. Benchmark performance improvement
