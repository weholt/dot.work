# FEAT-012 Investigation: Installer hard errors for invalid or missing environments

Investigation started: 2025-12-21

## Issue Summary
The installer must fail with clear errors if:
1. The target environment does not exist in the canonical prompt
2. `target.path` is missing or empty
3. `target.filename` or `target.filename_suffix` is missing
4. More than one environment is selected

## Current State Analysis

### Functions to update:
1. **`generate_environment_prompt()` in canonical.py** (lines 321-373)
   - Currently calls `prompt.get_environment(env_name)` which raises KeyError
   - Need to convert to CanonicalPromptError with clear message

2. **`install_canonical_prompt()` in installer.py** (lines 816-908)
   - Has some error handling (line 847-851)
   - But missing validation for:
     - Empty/missing target path (line 857)
     - Empty/missing filename/filename_suffix (line 870-882)

3. **`install_canonical_prompt_directory()` in installer.py** (lines 911-964)
   - Has catch-all exception handling (line 958-959)
   - Error message is ambiguous (line 962) - doesn't distinguish between "no files processed" vs "environment not found"

### Error Handling Requirements

#### A. Missing Environment
- **Where**: `generate_environment_prompt()` and `install_canonical_prompt()`
- **Current**: KeyError from line 92 in canonical.py, or ValueError with list of available
- **Expected**: Clear CanonicalPromptError or ValueError with available environments

#### B. Missing target path
- **Where**: `install_canonical_prompt()` line 857
- **Current**: `startswith()` check may pass on empty string
- **Expected**: Validate that target is non-empty and valid before using

#### C. Missing filename/filename_suffix
- **Where**: `install_canonical_prompt()` line 870-882
- **Current**: Raises ValueError at line 882 ("must specify...")
- **Expected**: This is already implemented ✓

#### D. Multiple environments selected (invalid use case)
- **Where**: Not currently applicable - env_key is single string
- **Expected**: Document that only one environment can be selected per call

## Key Insights

From tests in `test_installer_canonical.py`:
- Line 181: Expects `ValueError` with message "Environment 'invalid' not found in canonical prompt"
- Line 198: Expects `ValueError` with "Canonical prompt validation failed"
- Line 300: Expects `ValueError` with "Environment 'invalid' not found in canonical prompt"

## Implementation Plan

1. **Update `EnvironmentConfig` validation** (canonical.py)
   - Strengthen validation in `__post_init__()` 
   - Ensure target is never empty string
   - Done already via checks in lines 54-65

2. **Update `generate_environment_prompt()`** (canonical.py)
   - Change KeyError to CanonicalPromptError
   - Add clear message listing available environments
   - Validate target path is not empty

3. **Update `install_canonical_prompt()`** (installer.py)
   - Validate target path before use (line 857-865)
   - Add validation for filename/filename_suffix matching EnvironmentConfig
   - Improve error messages

4. **Update `install_canonical_prompt_directory()`** (installer.py)
   - Better error message at line 962
   - Track which environments were found vs requested

## Tests Needed

From `test_installer_canonical.py`:
- ✓ test_install_canonical_prompt_invalid_environment (line 165-183)
- ✓ test_install_canonical_prompt_invalid_file (line 185-199)
- ✓ test_install_canonical_prompt_directory_with_invalid_environment (line 282-302)

Need to add:
- Test for missing/empty target path
- Test for missing filename AND filename_suffix
- Test for CanonicalPromptError with available environments listed

## Files to Modify

1. `src/dot_work/prompts/canonical.py`:
   - Update `get_environment()` to provide better error message
   - Update `generate_environment_prompt()` to validate target path

2. `src/dot_work/installer.py`:
   - Update `install_canonical_prompt()` to validate target path
   - Improve error messages in both install functions

3. `tests/unit/test_installer_canonical.py`:
   - Add test for missing target path
   - Add test for empty target path
   - Add test for missing both filename and filename_suffix

## Success Criteria

- ✓ Installer fails with clear error if environment missing
- ✓ Error messages list available environments
- ✓ Installer fails if target path is empty/missing
- ✓ Installer fails if filename/filename_suffix are both missing
- ✓ All existing tests pass
- ✓ New tests verify error handling
