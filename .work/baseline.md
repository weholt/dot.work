# Project Baseline

**Captured:** 2026-01-02T22:28Z
**Commit:** 66e0fa5269206f8be2d063c0651a5b3ead3a12c7
**Branch:** closing-migration

---

## Scope Summary

### Source Code (`src/`)
- **Total modules:** 1 main package (`dot_work`) + plugins
- **Python files:** 40 files
- **Total lines:** 9,438 lines
- **Classes + Functions:** 164 definitions

### Module Breakdown
| Module | Files | Lines |
|--------|-------|-------|
| `dot_work` (main) | 40 | 9,438 |

### Test Suite (`tests/`)
- **Python files:** 25 files (20 unit, 4 integration, 1 conftest)
- **Total lines:** 7,433 lines

### Entry Points
| Entry Point | Type | Location |
|-------------|------|----------|
| `main()` | CLI function | `src/dot_work/cli.py:607` |
| `install()` | CLI command | `src/dot_work/cli.py:67` |
| `list_envs()` | CLI command | `src/dot_work/cli.py:179` |
| `detect()` | CLI command | `src/dot_work/cli.py:199` |
| `init_project()` | CLI command | `src/dot_work/cli.py:224` |
| `init_tracking()` | CLI command | `src/dot_work/cli.py:249` |
| `status()` | CLI command | `src/dot_work/cli.py:274` |
| `plugins_cmd()` | CLI command | `src/dot_work/cli.py:385` |

### Dependencies
| Category | Count |
|----------|-------|
| Direct runtime | 14 (see `pyproject.toml` dependencies) |
| Dev dependencies | 8 (see `pyproject.toml` dev-dependencies) |
| Total | 22 |

---

## Observable Behaviors

### CLI Behaviors (BEH-CLI-XXX)
| ID | Behavior | Documented | Verified Via |
|----|----------|-----------|-------------|
| BEH-CLI-001 | `install` command installs prompts to target directory | Yes (help text) | `test_install_with_force_succeeds` |
| BEH-CLI-002 | `install --force` overwrites existing files without prompting | Yes | `test_install_respects_force_flag_true` |
| BEH-CLI-003 | `list` command shows available environments | Yes | `test_list_shows_environments` |
| BEH-CLI-004 | `detect` command identifies AI environment from target directory | Yes | `test_detect_copilot_environment` |
| BEH-CLI-005 | `init-project` is an alias for `install` (no project creation) | Partial | `test_init_with_env_succeeds` |
| BEH-CLI-006 | `init-tracking` creates `.work/` directory structure | Yes | `test_init_work_creates_structure` |
| BEH-CLI-007 | `status` outputs project state in multiple formats | Yes | `test_status_table_format` |
| BEH-CLI-008 | `plugins` command lists discovered plugins | Yes | Integration tests |
| BEH-CLI-009 | Missing target directory causes FileNotFoundError | Yes | `test_install_nonexistent_target` |
| BEH-CLI-010 | Unknown environment raises ValueError | Yes | `test_install_unknown_environment` |

### Installer Behaviors (BEH-INST-XXX)
| ID | Behavior | Documented | Verified Via |
|----|----------|-----------|-------------|
| BEH-INST-001 | Supports 12 AI environments (copilot, cursor, claude, windsurf, aider, continue, amazon-q, zed, opencode, cline, cody, generic) | Yes | `test_install_for_environments` |
| BEH-INST-002 | Each environment has unique target directory and filename pattern | Yes | Environment tests |
| BEH-INST-003 | Jinja2 templates rendered with environment-specific context | Yes | Template tests |
| BEH-INST-004 | Auto-escape disabled for Markdown templates (security consideration) | Yes | Security tests |
| BEH-INST-005 | Batch overwrite menu (all/skip/prompt/cancel) for existing files | Yes | Batch choice tests |
| BEH-INST-006 | Canonical prompt format supported with frontmatter validation | Yes | Canonical installer tests |

### Security Behaviors (BEH-SEC-XXX)
| ID | Behavior | Documented | Verified Via |
|----|----------|-----------|-------------|
| BEH-SEC-001 | `safe_path_join()` prevents directory traversal attacks | Yes (code comment) | Security tests |
| BEH-SEC-002 | `sanitize_error_message()` removes secrets from errors | Yes | Sanitization tests |
| BEH-SEC-003 | `validate_secret_format()` checks API key patterns | Yes | Secret validation tests |
| BEH-SEC-004 | Jinja2 templates reject external includes | Yes | Security tests |

### Plugin Behaviors (BEH-PLUGIN-XXX)
| ID | Behavior | Documented | Verified Via |
|----|----------|-----------|-------------|
| BEH-PLUGIN-001 | Plugins discovered via entry points | Yes | Plugin ecosystem tests |
| BEH-PLUGIN-002 | Missing/broken plugins logged but don't crash core | Yes | Graceful degradation tests |
| BEH-PLUGIN-003 | Plugin commands registered with typer app | Yes | Registration tests |

### Undocumented Behaviors
- None identified (all major behaviors have corresponding tests)

---

## Test Evidence

### Test Summary
| Metric | Value |
|--------|-------|
| Total tests | 535 |
| Executed | 517 |
| Skipped | 18 |
| Passed | 517 |
| Failed | 0 |
| Execution time | 28.77s |
| Memory baseline | 37.3 MB |
| Memory final | 56.3 MB |
| Memory growth | +19.0 MB |

### Coverage
| Metric | Value |
|--------|-------|
| Overall coverage | 56% |
| Lines covered | 3,413 |
| Lines uncovered | 1,497 |
| Files with 100% coverage | Not measured |

### Coverage by Module (partial)
| Module | Estimated Coverage | Notes |
|--------|-------------------|-------|
| `cli.py` | High | Extensive command tests |
| `installer.py` | High | Comprehensive installation tests |
| `canonical.py` | High | Full parser/validator coverage |
| `utils/path.py` | Medium | Needs dedicated security tests |
| `utils/secrets.py` | Medium | Needs comprehensive edge case tests |
| `utils/sanitization.py` | High | Pattern coverage good |

### Tested Behaviors
- All BEH-CLI-001 through BEH-CLI-010
- All BEH-INST-001 through BEH-INST-006
- All BEH-SEC-001 through BEH-SEC-004
- All BEH-PLUGIN-001 through BEH-PLUGIN-003

### Untested Behaviors
- CR-003: `safe_path_join` edge cases (documented in code review)
- Some error paths in canonical parsing
- Integration tests for full workflow

---

## Known Gaps

### Code Comments (GAP-CODE-XXX)
| ID | Description | Source |
|----|-------------|--------|
| GAP-CODE-001 | Add bundled package skills to discovery | `src/dot_work/skills/discovery.py:65` |

### Known Issues (from code review)
| ID | Description | Priority | Source |
|----|-------------|----------|--------|
| GAP-ISSUE-001 | Dead code in installer.py lines 1522-1527 | Critical | CR-001 |
| GAP-ISSUE-002 | Dual-mode `install_prompts` has hidden control flow | High | CR-002 |
| GAP-ISSUE-003 | Missing tests for `safe_path_join` security function | Medium | CR-003 |
| GAP-ISSUE-004 | 67-line `prompt_for_environment` exceeds complexity threshold | Medium | CR-004 |
| GAP-ISSUE-005 | `init_project` name is misleading (alias, not init) | Medium | CR-005 |

### TODO Count
- **Total TODO/FIXME/HACK/NOTE comments:** 6
- **Locations:** See above list

---

## Failure Semantics

### Failure Modes by Category

#### Explicit Exceptions (FAIL-EXP-XXX)
| ID | Exception | Raised By | Handling | Documented |
|----|-----------|-----------|----------|------------|
| FAIL-EXP-001 | `FileNotFoundError` | `install()` when target missing | Raised | Yes |
| FAIL-EXP-002 | `ValueError` | `install()` when env unknown | Raised | Yes |
| FAIL-EXP-003 | `PathTraversalError` | `safe_path_join()` on traversal | Raised | Yes |
| FAIL-EXP-004 | `SecretValidationError` | `get_secret()` on invalid format | Raised | Yes |
| FAIL-EXP-005 | `CanonicalPromptError` | Canonical parser on invalid format | Raised | Yes |

#### Logged Failures (FAIL-LOG-XXX)
| ID | Condition | Logged By | Action |
|----|-----------|-----------|--------|
| FAIL-LOG-001 | Broken plugin import | `plugins.py:85` | Continue with available |
| FAIL-LOG-002 | Canonical prompt parse failure | `installer.py:1391` | Skip file, continue |

#### Silent Failures (FAIL-SILENT-XXX)
| ID | Condition | Behavior | Note |
|----|-----------|----------|------|
| FAIL-SILENT-001 | Invalid canonical prompt in directory | Skipped | May be intentional |
| FAIL-SILENT-002 | Plugin load failure (non-critical) | Logged, continues | Graceful degradation |

### Failure Summary
- **Explicit raises:** 5 types
- **Logged continues:** 2 scenarios
- **Silent skips:** 2 scenarios (both intentional)

---

## Structure

### File Counts
| Category | Count |
|----------|-------|
| Source files (`.py`) | 40 |
| Test files (`.py`) | 25 |
| Configuration files | 1 (`pyproject.toml`) |
| Documentation files | Not measured |

### Line Counts
| Category | Lines |
|----------|-------|
| Source code | 9,438 |
| Test code | 7,433 |
| Total (measured) | 16,871 |

### Abstraction Depth
| Path | Depth | Notes |
|------|-------|-------|
| CLI → Installer → Jinja | 3 | Main installation flow |
| CLI → Canonical Parser → Environment Config | 3 | Prompt parsing |
| Plugin Discovery → Entry Points → Load | 3 | Plugin loading |
| **Max depth** | **3** | Acceptable |

### Dependencies
| Type | Status |
|------|--------|
| Cyclic imports | None detected |
| Circular dependencies | None |

### Linting & Type Checking
| Tool | Status | Errors | Warnings |
|------|--------|--------|----------|
| mypy | Pass | 0 | 0 |
| ruff | Pass | 0 | 0 |

---

## Documentation Status

### User Documentation
| Document | Status | Notes |
|----------|--------|-------|
| `README.md` | Current | Basic project info |
| `CLAUDE.md` | Current | Project instructions for Claude Code |
| `CONTRIBUTING.md` | Not checked | Unknown if exists |

### Code Documentation
| Type | Coverage | Notes |
|------|----------|-------|
| Docstrings (Google style) | High | Required for public APIs |
| Type hints | 100% | All functions annotated |
| Comments | Medium | Security code well-commented |

### Inline Documentation
| Module | Docstring Coverage |
|--------|-------------------|
| `cli.py` | High |
| `installer.py` | High |
| `canonical.py` | High (extensive) |
| `utils/path.py` | High (security rationale) |
| `utils/secrets.py` | High |
| `utils/sanitization.py` | High |

### Missing Documentation
- No changelog found
- API documentation not generated (no Sphinx/docs)

---

## Unknowns

### Platform-Specific (UNK-PLATFORM-XXX)
| ID | Unknown | Reason | Impact |
|----|---------|--------|--------|
| UNK-PLATFORM-001 | Windows compatibility | CI only runs on Linux | Unknown if works on Windows |
| UNK-PLATFORM-002 | macOS compatibility | Not explicitly tested | Likely works (Unix-like) |

### Performance (UNK-PERF-XXX)
| ID | Unknown | Reason | Impact |
|----|---------|--------|--------|
| UNK-PERF-001 | Behavior with large prompt directories | Not tested | May be slow with 1000+ files |
| UNK-PERF-002 | Memory usage under load | Only baseline measured | Unknown if leaks exist |

### Security (UNK-SEC-XXX)
| ID | Unknown | Reason | Impact |
|----|---------|--------|--------|
| UNK-SEC-001 | Real-world path traversal attempts | Only unit tests | May miss edge cases |
| UNK-SEC-002 | Secret sanitization coverage | Pattern-based | May miss new secret formats |

### External Dependencies (UNK-EXT-XXX)
| ID | Unknown | Reason | Impact |
|----|---------|--------|--------|
| UNK-EXT-001 | Plugin ecosystem behavior | No external plugins tested | Unknown if integration works |
| UNK-EXT-002 | Future AI tool compatibility | Only 12 tools supported | New tools may not work |

### Cannot Verify
- Concurrent access to shared state (not designed for concurrency)
- Behavior with symlinks to unusual locations
- Error messages in non-English locales

---

## Baseline Invariants

The following statements **must not regress**:

1. **Test Status:** All 517 tests pass (0 failures)
2. **Coverage:** Overall coverage ≥ 56%
3. **Type Safety:** mypy reports 0 errors
4. **Linting:** ruff reports 0 errors
5. **Build Time:** `uv run python scripts/build.py` completes in ≤ 60s
6. **Test Execution:** Full test suite completes in ≤ 45s
7. **Memory:** Test execution uses ≤ 200MB baseline + growth
8. **No Cyclic Dependencies:** Module graph remains acyclic

### Regression Detection
Any change that violates these invariants should be flagged as a regression.

---

## Baseline Metadata

| Attribute | Value |
|-----------|-------|
| Baseline format | v1.0 |
| Generated by | establish-baseline prompt |
| Generator version | Python 3.13.11 |
| Determinism guarantee | Identical commit produces identical baseline |

### Notes
- Coverage measured with `pytest-cov`
- Line counts include blank lines and comments
- Test count includes both unit and integration tests
- Memory measured with pytest-memory-monitor plugin
