# SEC-007 Investigation: Missing HTTPS validation in file upload

**Issue:** SEC-007@94eb69
**Started:** 2024-12-27T02:40:00Z
**Completed:** 2024-12-27T02:45:00Z
**Status**: ✅ Complete

---

## Problem Analysis

**Root Cause:** The `upload_zip()` function in `src/dot_work/zip/uploader.py` did not explicitly set SSL verification parameters or validate URL scheme.

### Existing Code (line 45)

```python
# BEFORE (INSECURE):
response = requests.post(api_url, files=files, timeout=30)
```

**Security Issues:**
1. No explicit `verify=True` parameter makes security policy unclear
2. No timeout for SSL handshake (30s timeout only applies to request)
3. No validation of `api_url` scheme (could be http:// in testing)
4. Default behavior is secure but not explicit

**CVSS Score:** 4.3 (Medium)
- Attack Vector: Network
- Attack Complexity: High
- Privileges Required: None
- Impact: Low (integrity of upload only)

---

## Solution Implemented

### 1. Added URL Scheme Validation

```python
# Validate URL scheme - require HTTPS for secure uploads
if not api_url.startswith("https://"):
    raise ValueError(
        f"Only HTTPS URLs are supported for secure uploads. Got: {api_url}"
    )
```

### 2. Added Explicit SSL Verification

```python
response = requests.post(
    api_url,
    files=files,
    timeout=(10, 30),  # (connect timeout, read timeout)
    verify=True,  # Explicit SSL certificate verification
)
```

### 3. Added Separate Connection Timeout

```python
timeout=(10, 30)  # 10s for connection, 30s for read
```

---

## Affected Files
- `src/dot_work/zip/uploader.py` (lines 15-61: upload_zip function)
- `tests/unit/zip/test_uploader.py` (updated 2 tests, added 2 new tests)

---

## Changes Made

### File: `src/dot_work/zip/uploader.py`
1. Added HTTPS URL validation before upload
2. Changed `timeout=30` to `timeout=(10, 30)` for separate connect/read timeouts
3. Added explicit `verify=True` parameter
4. Updated docstring to reflect HTTPS requirement

### File: `tests/unit/zip/test_uploader.py`
1. Updated existing tests to expect new timeout format
2. Added `assert kwargs["verify"] is True` to verify SSL parameter
3. Added `test_upload_zip_rejects_http_url()` test
4. Added `test_upload_zip_rejects_non_http_url()` test

---

## Outcome

**Validation Results:**
- All 11 uploader tests pass
- Memory growth: +19.4 MB (normal for test module)
- Test runtime: 0.37s

**Security Improvements:**
1. Explicit SSL certificate verification (`verify=True`)
2. HTTPS-only URLs enforced (rejects http://, ftp://, etc.)
3. Separate connection timeout (10s) from read timeout (30s)
4. Clear security intent through code and documentation

---

## Acceptance Criteria
- [x] SSL verification explicitly set to `verify=True`
- [x] URL scheme validated to be HTTPS
- [x] Separate connection timeout from read timeout
- [x] Tests verify HTTP URLs are rejected
- [x] Tests verify invalid schemes are rejected
- [x] All tests still pass

---

## Notes
- While `requests` defaults to `verify=True`, explicit is better for security-critical code
- HTTPS-only enforcement prevents accidental misconfiguration
- Separate connection timeout prevents hanging on SSL handshake
- Related: SEC-004, SEC-005, SEC-006 (other security fixes)
