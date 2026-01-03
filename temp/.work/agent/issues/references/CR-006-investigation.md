# CR-006 Investigation: Scan service doesn't validate input paths before scanning

**Issue:** CR-006@b935c0
**Started:** 2024-12-27T04:00:00Z
**Completed:** 2024-12-27T04:05:00Z
**Status**: Complete

---

## Problem Analysis

**Root Cause:** `ScanService.scan()` accepted a `root_path: Path` parameter but didn't validate:
1. The path exists
2. The path is a directory (not a file)

### Existing Code (lines 31-59)

```python
# BEFORE (no validation):
def scan(self, root_path: Path, ...) -> CodeIndex:
    """Scan a Python codebase."""
    scanner = ASTScanner(root_path)  # No validation!
    index = scanner.scan(incremental=incremental)
    # ...
```

**Issues:**
1. **Poor user experience**: Generic errors from scanner instead of clear "path not found"
2. **Performance**: Scanner starts walking directory tree before discovering path doesn't exist
3. **Security**: No validation of path bounds before scanning

---

## Solution Implemented

### Path Validation at Entry Point

```python
# AFTER (with validation):
def scan(self, root_path: Path, ...) -> CodeIndex:
    """Scan a Python codebase.

    Raises:
        FileNotFoundError: If root_path does not exist.
        NotADirectoryError: If root_path is not a directory.
    """
    # Validate path before scanning to provide clear error messages
    if not root_path.exists():
        raise FileNotFoundError(f"Scan path does not exist: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Scan path is not a directory: {root_path}")

    scanner = ASTScanner(root_path)
    # ...
```

**Key Changes:**
1. Added `root_path.exists()` check with `FileNotFoundError`
2. Added `root_path.is_dir()` check with `NotADirectoryError`
3. Clear error messages include the invalid path
4. Updated docstring to document exceptions

---

## Affected Files

- `src/dot_work/python/scan/service.py` (lines 31-69: `scan` method)
- `tests/unit/python/scan/test_service.py` (NEW: 3 validation tests)

---

## Changes Made

### File: `src/dot_work/python/scan/service.py`

**Before:**
```python
def scan(self, root_path: Path, ...) -> CodeIndex:
    """Scan a Python codebase."""
    scanner = ASTScanner(root_path)
    index = scanner.scan(incremental=incremental)
    # ...
```

**After:**
```python
def scan(self, root_path: Path, ...) -> CodeIndex:
    """Scan a Python codebase.

    Raises:
        FileNotFoundError: If root_path does not exist.
        NotADirectoryError: If root_path is not a directory.
    """
    # Validate path before scanning to provide clear error messages
    if not root_path.exists():
        raise FileNotFoundError(f"Scan path does not exist: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Scan path is not a directory: {root_path}")

    scanner = ASTScanner(root_path)
    index = scanner.scan(incremental=incremental)
    # ...
```

### File: `tests/unit/python/scan/test_service.py` (NEW)

Created 3 new tests:
1. `test_scan_rejects_nonexistent_path()` - verifies FileNotFoundError for missing paths
2. `test_scan_rejects_file_instead_of_directory()` - verifies NotADirectoryError for files
3. `test_scan_accepts_valid_directory()` - verifies valid directories work

---

## Outcome

**Validation Results:**
- All 44 python/scan tests pass (41 existing + 3 new)
- Memory growth: +23.9 MB (normal for test module)
- Test runtime: 1.69s
- New tests verify validation behavior

**User Experience Improvements:**
1. **Clear error messages**: "Scan path does not exist: /path/to/missing"
2. **Fail fast**: Validation happens before directory walking
3. **Correct exception types**: FileNotFoundError vs generic errors
4. **Documented behavior**: Docstring lists exceptions

**Security Improvements:**
1. Early validation prevents unintended scanning operations
2. Clear errors help users identify configuration issues

---

## Acceptance Criteria

- [x] Service validates path exists before scanning
- [x] Service validates path is directory
- [x] Clear error messages for invalid paths
- [x] Tests verify validation behavior (3 new tests)
- [x] All existing tests still pass

---

## Notes

- Related: CR-005 (Environment path validation), SEC-004 (Path.relative_to security)
- This is a simple "fail fast" validation pattern that should be applied to all user-facing APIs
- The scanner.py already handles errors gracefully (lines 94-105), but service-level validation is better UX
- Pattern: Validate inputs at service layer, defer to lower layers for internal error handling
