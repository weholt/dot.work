# Investigation: TEST-001@c4a9f6 – Add installer integration tests

Investigation started: 2025-12-22T16:10:00Z

## Issue Summary
The installer module currently has 41% coverage. The 10 `install_for_*` functions lack comprehensive integration tests. CLI tests (TEST-002) cover entry points but don't test the core installer functionality.

## Current State Analysis

### Functions to Test (10 total)
All in `src/dot_work/installer.py`:
1. `install_for_copilot()` - line 154
2. `install_for_claude()` - line 183  
3. `install_for_cursor()` - line 214
4. `install_for_windsurf()` - line 255
5. `install_for_aider()` - line 288
6. `install_for_continue()` - line 316
7. `install_for_amazon_q()` - line 341
8. `install_for_zed()` - line 370
9. `install_for_opencode()` - line 394
10. `install_for_generic()` - line 456

### Existing Tests
**File:** `tests/unit/test_installer.py` (383 lines, 29 tests)

**Current Test Classes:**
- `TestShouldWriteFile` - 5 tests (helper function)
- `TestInstallPrompts` - 2 tests (main install function)
- `TestInstallForCopilotWithForce` - 2 tests (only copilot tested)
- `TestCreateJinjaEnv` - 2 tests (template environment)
- `TestRenderPrompt` - 3 tests (template rendering)
- `TestDetectProjectContext` - 7 tests (context detection)
- `TestInitializeWorkDirectory` - 8 tests (work directory setup)

**Coverage Gap:** `install_for_*` functions (except copilot) are **UNTESTED**

### Environment Configuration
From `src/dot_work/environments.py`, each environment has:
- `target_dir` - destination directory path
- `filename_pattern` - output file naming convention
- `language` - language identifier
- `language_tag` - additional tagging info

### Test Strategy

#### Step 1: Test Helpers
Create parametrized test fixtures for:
- Sample prompt content
- Environment-specific target directories
- Mock console objects

#### Step 2: Individual Function Tests
For each `install_for_*` function:
- Verify correct target directory is created
- Verify prompt files are installed to correct location
- Verify filenames follow environment-specific patterns
- Verify template variables are substituted correctly
- Test with force=True and force=False

#### Step 3: Edge Cases
- Missing prompts directory
- Permission errors when creating directories
- Existing files with/without force flag
- Empty prompt files
- Prompts with special characters

#### Step 4: Parametrized Coverage
Use pytest parametrize to test all 10 environments:
```python
@pytest.mark.parametrize("env_key,env_name", [
    ("copilot", "Copilot"),
    ("claude", "Claude"),
    ...
])
def test_install_for_environment(env_key, env_name, ...):
    # Generic test that works for all environments
```

## Acceptance Criteria
- [ ] Each `install_for_*` function has at least one test
- [ ] Parametrized tests cover all 10 environments
- [ ] Tests verify:
  - Correct target directories created
  - Files have expected content
  - Template variables substituted correctly
- [ ] Coverage for installer.py ≥ 80% (currently 41%)
- [ ] All tests pass with no regressions
- [ ] Build passes (8/8 checks)

## Baseline Comparison
**Current Baseline (b251889):**
- Tests: 721/721 passing
- Coverage: 76.26% overall
- Installer module: Not directly measured (coverage tool issue)
- Lint: 0 errors
- Types: 0 errors

**Expected After Implementation:**
- Tests: 721 + ~20-30 new = 745-750+ passing
- Coverage: 76.26% → ~77-78% (installer fixes should help)
- Installer module coverage: 41% → 80%+
- No regressions in other modules

## Investigation Complete
Ready for implementation phase. Will add comprehensive tests using existing patterns from the codebase.

Key files to modify:
- `tests/unit/test_installer.py` - Add new test classes
- Consider: `tests/conftest.py` - May need new fixtures

No new source files needed - only test additions.
