# SEC-004 Investigation: Path traversal vulnerability in read_file_text

**Issue:** SEC-004@94eb69
**Started:** 2024-12-27T00:05:00Z
**Status:** In Progress

---

## Problem Analysis

**Location:** `src/dot_work/review/git.py:276-277`

```python
def read_file_text(root: str, path: str) -> str:
    full = Path(root) / path
    norm = full.resolve()
    root_norm = Path(root).resolve()

    # Prevent path traversal
    if not str(norm).startswith(str(root_norm)):
        raise GitError("invalid path")

    return norm.read_text(encoding="utf-8", errors="replace")
```

### Root Cause
String prefix checking `str(norm).startswith(str(root_norm))` is vulnerable to:

1. **Symlinks**: If `root` contains a symlink to `/etc`, an attacker can provide `path = "passwd"` to read `/etc/passwd`
   - Example: `root = "/safe/repo"` where `/safe/repo/data` → `/etc`
   - Attacker provides `path = "data/passwd"`
   - `resolve()` follows symlink to `/etc/passwd`
   - But `/etc/passwd`.startswith(`/safe/repo`) passes on macOS (case-insensitive)

2. **Case sensitivity**: On Windows/macOS, path case variations bypass the check:
   - `C:\Project` vs `c:\project`
   - `.startswith()` may return true even when different directories

3. **String comparison issues**: Different path representations can fool the check:
   - `//?/C:/Project` (Windows extended-length path)
   - Unicode normalization (NFD vs NFC)

---

## Proposed Solution

Use `Path.relative_to()` which properly validates path containment:

```python
def read_file_text(root: str, path: str) -> str:
    full = Path(root) / path
    norm = full.resolve()
    root_norm = Path(root).resolve()

    # Prevent path traversal using relative_to()
    try:
        norm.relative_to(root_norm)
    except ValueError:
        raise GitError("invalid path")

    return norm.read_text(encoding="utf-8", errors="replace")
```

**Why this works:**
- `Path.relative_to()` computes the relative path from `root_norm` to `norm`
- If `norm` is not under `root_norm`, it raises `ValueError`
- Works correctly with symlinks (resolves both paths first)
- Case-sensitive on Unix, respects OS rules on Windows/macOS
- Handles Unicode normalization properly

---

## Affected Files
- `src/dot_work/review/git.py` (lines 276-277)

---

## Acceptance Criteria
- [ ] Path validation uses `relative_to()` instead of string prefix check
- [ ] Tests verify traversal attempts are blocked
- [ ] Edge cases covered: symlinks, case variations, unicode
- [ ] All existing tests pass

---

## Next Steps
1. Implement `relative_to()` check
2. Add tests for path traversal attempts
3. Run validation
