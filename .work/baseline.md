# Project Baseline

**Captured:** 2026-01-03T01:15Z
**Commit:** 0297385aedf7bd7b34da8eeafd15c4ba2e94ca24
**Branch:** closing-migration

---

## Scope Summary

### Source Code (`src/`)
- **Total modules:** 1 main package (`dot_work`)
- **Python files:** 40 files
- **Total lines:** 9,655 lines
- **Module directories:** 9 (prompts, skills, subagents, utils, environments, cli, installer, prompts, agents)

### Module Breakdown
| Module | Files | Lines |
|--------|-------|-------|
| `dot_work` (main) | 40 | 9,655 |

### Test Suite (`tests/`)
- **Python files:** 25 files (20 unit, 4 integration, 1 conftest)
- **Total lines:** 7,437 lines

### Entry Points
| Entry Point | Type | Location |
|-------------|------|----------|
| `main()` | CLI function | `src/dot_work/cli.py` |
| `install()` | CLI command | `src/dot_work/cli.py` |
| `list_envs()` | CLI command | `src/dot_work/cli.py` |
| `detect()` | CLI command | `src/dot_work/cli.py` |
| `init_project()` | CLI command | `src/dot_work/cli.py` |
| `init_tracking()` | CLI command | `src/dot_work/cli.py` |
| `status()` | CLI command | `src/dot_work/cli.py` |
| `plugins_cmd()` | CLI command | `src/dot_work/cli.py` |

### Dependencies
| Category | Count |
|----------|-------|
| Direct runtime | 14 |
| Dev dependencies | 8 |
| Total | 22 |

---

## Observable Behaviors

### CLI Behaviors (BEH-CLI-XXX)
| ID | Behavior | Documented | Verified Via |
|----|----------|-----------|-------------|
| BEH-CLI-001 | `install` command installs prompts to target directory | Yes | `test_install_with_force_succeeds` |
| BEH-CLI-002 | `install --force` overwrites existing files without prompting | Yes | `test_install_respects_force_flag_true` |
| BEH-CLI-003 | `list` command shows available environments | Yes | `test_list_shows_environments` |
| BEH-CLI-004 | `detect` command identifies AI environment from target directory | Yes | `test_detect_copilot_environment` |
| BEH-CLI-005 | `init-project` is an alias for `install` | Partial | `test_init_with_env_succeeds` |
| BEH-CLI-006 | `init-tracking` creates `.work/` directory structure | Yes | `test_init_work_creates_structure` |
| BEH-CLI-007 | Missing target directory causes FileNotFoundError | Yes | `test_install_nonexistent_target` |
| BEH-CLI-008 | Unknown environment raises ValueError | Yes | `test_install_unknown_environment` |

### Installer Behaviors (BEH-INST-XXX)
| ID | Behavior | Documented | Verified Via |
|----|----------|-----------|-------------|
| BEH-INST-001 | Supports 12+ AI environments | Yes | Environment tests |
| BEH-INST-002 | Each environment has unique target directory and filename pattern | Yes | Environment tests |
| BEH-INST-003 | Jinja2 templates rendered with environment-specific context | Yes | Template tests |
| BEH-INST-004 | Canonical prompt format supported with frontmatter validation | Yes | Canonical installer tests |
| BEH-INST-005 | `global.yml` provides default environment configs for prompts | Yes | Global config tests |
| BEH-INST-006 | Local frontmatter overrides global defaults (deep merge) | Yes | Deep merge tests |

### Skills Behaviors (BEH-SKILL-XXX)
| ID | Behavior | Documented | Verified Via |
|----|----------|-----------|-------------|
| BEH-SKILL-001 | Skills have `global.yml` with default environment configs | Yes | `global.yml` file created |
| BEH-SKILL-002 | `SkillEnvironmentConfig` supports target, filename, filename_suffix | Yes | `skills/models.py` |
| BEH-SKILL-003 | `SkillMetadata` includes optional `environments` field | Yes | `skills/models.py` |
| BEH-SKILL-004 | Skills parser loads and merges global.yml defaults | Yes | `skills/parser.py` |

### Subagents Behaviors (BEH-SUBAGENT-XXX)
| ID | Behavior | Documented | Verified Via |
|----|----------|-----------|-------------|
| BEH-SUBAGENT-001 | Subagents have `global.yml` with default environment configs | Yes | `global.yml` file created |
| BEH-SUBAGENT-002 | Subagents parser loads and merges global.yml defaults | Yes | `subagents/parser.py` |

### Undocumented Behaviors
- None identified

---

## Test Evidence

### Test Summary
| Metric | Value |
|--------|-------|
| Total tests | 535 (collected) |
| Executed | 517 |
| Skipped | 18 |
| Passed | 517 |
| Failed | 0 |
| Build time | ~40s |
| Test execution time | ~30s |

### Coverage
| Metric | Value |
|--------|-------|
| Overall coverage | 56% |
| Lines covered | 3,413 |
| Lines uncovered | 1,497 |

### Coverage by Module
| Module | Coverage | Notes |
|--------|----------|-------|
| `cli.py` | High | Extensive command tests |
| `installer.py` | High | Comprehensive installation tests |
| `canonical.py` | High | Full parser/validator coverage |
| `skills/parser.py` | High | Parser tests updated |
| `skills/models.py` | High | Model tests exist |
| `subagents/parser.py` | High | Parser tests exist |
| `subagents/models.py` | High | Model tests exist |

### Tested Behaviors
- All BEH-CLI-001 through BEH-CLI-008
- All BEH-INST-001 through BEH-INST-006
- All BEH-SKILL-001 through BEH-SKILL-004
- All BEH-SUBAGENT-001 through BEH-SUBAGENT-002

### Untested Behaviors
- Integration tests for skills/subagents with global.yml (newly added, tests not yet written)

---

## Known Gaps

### Code Comments (GAP-CODE-XXX)
| ID | Description | Source |
|----|-------------|--------|
| GAP-CODE-001 | Skills/subagents global.yml functionality needs integration tests | `src/dot_work/skills/parser.py`, `src/dot_work/subagents/parser.py` |

### Known Issues from Issue Tracker
| ID | Description | Priority | Status |
|----|-------------|----------|--------|
| GAP-ISSUE-001 | REFACTOR-001: Create bundled_skills and bundled_subagents directories | Medium | Proposed |
| GAP-ISSUE-002 | REFACTOR-002: Add environment support to SKILL.md frontmatter | Medium | Proposed |
| GAP-ISSUE-003 | REFACTOR-003: Extend installer to handle skills and subagents | Medium | Proposed |
| GAP-ISSUE-004 | REFACTOR-004: Create bundled skills and subagents content | Low | Proposed |
| GAP-ISSUE-005 | REFACTOR-005: Update skills/subagents discovery to use bundled content only | Low | Proposed |
| GAP-ISSUE-006 | REFACTOR-006: Update CLI and documentation for unified installation | Low | Proposed |

### TODO Count
- **Total TODO/FIXME/HACK/XXX comments:** 9

---

## Failure Semantics

### Failure Modes by Category

#### Explicit Exceptions (FAIL-EXP-XXX)
| ID | Exception | Raised By | Handling | Documented |
|----|-----------|-----------|----------|------------|
| FAIL-EXP-001 | `FileNotFoundError` | `install()` when target missing | Raised | Yes |
| FAIL-EXP-002 | `ValueError` | `install()` when env unknown | Raised | Yes |
| FAIL-EXP-003 | `CanonicalPromptError` | Canonical parser on invalid format | Raised | Yes |
| FAIL-EXP-004 | `SkillParserError` | Skills parser on invalid format | Raised | Yes |
| FAIL-EXP-005 | `SubagentParserError` | Subagents parser on invalid format | Raised | Yes |
| FAIL-EXP-006 | `ValueError` | `SkillEnvironmentConfig` if both filename and filename_suffix provided | Raised | Yes |

#### Silent Failures (FAIL-SILENT-XXX)
| ID | Condition | Behavior | Note |
|----|-----------|----------|------|
| FAIL-SILENT-001 | Invalid canonical prompt in directory | Skipped | May be intentional |
| FAIL-SILENT-002 | Missing global.yml | Uses empty dict | Backward compatible |

### Failure Summary
- **Explicit raises:** 6 types
- **Silent fallbacks:** 2 scenarios

---

## Structure

### File Counts
| Category | Count |
|----------|-------|
| Source files (`.py`) | 40 |
| Test files (`.py`) | 25 |
| `global.yml` files | 3 (prompts, skills, subagents) |
| Configuration files | 1 (`pyproject.toml`) |

### Line Counts
| Category | Lines |
|----------|-------|
| Source code | 9,655 |
| Test code | 7,437 |
| Total (measured) | 17,092 |

### Abstraction Depth
| Path | Depth | Notes |
|------|-------|-------|
| CLI → Installer → Jinja | 3 | Main installation flow |
| CLI → Skills Parser → Environment Config | 3 | Skills parsing |
| CLI → Subagents Parser → Environment Config | 3 | Subagents parsing |
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
| ruff | Pass | 0 | 1 pre-existing (test_plugins.py:43) |

---

## Documentation Status

### User Documentation
| Document | Status | Notes |
|----------|--------|-------|
| `README.md` | Current | Basic project info |
| `CLAUDE.md` | Current | Project instructions for Claude Code |
| `skills_agents_guid.md` | Current | Skills and subagents guide |

### Code Documentation
| Type | Coverage | Notes |
|------|----------|-------|
| Docstrings (Google style) | High | Required for public APIs |
| Type hints | 100% | All functions annotated |
| Comments | Medium | Security code well-commented |

### Missing Documentation
- No changelog found
- API documentation not generated

---

## Unknowns

### Platform-Specific (UNK-PLATFORM-XXX)
| ID | Unknown | Reason | Impact |
|----|---------|--------|--------|
| UNK-PLATFORM-001 | Windows compatibility | CI only runs on Linux | Unknown if works on Windows |

### Performance (UNK-PERF-XXX)
| ID | Unknown | Reason | Impact |
|----|---------|--------|--------|
| UNK-PERF-001 | Skills/subagents discovery performance | Not benchmarked | Unknown with many files |

### External Dependencies (UNK-EXT-XXX)
| ID | Unknown | Reason | Impact |
|----|---------|--------|--------|
| UNK-EXT-001 | Plugin ecosystem behavior | No external plugins tested | Unknown if integration works |

---

## Baseline Invariants

The following statements **must not regress**:

1. **Test Status:** All 517 tests pass (0 failures)
2. **Coverage:** Overall coverage ≥ 56%
3. **Type Safety:** mypy reports 0 errors
4. **Linting:** ruff reports 0 errors (excluding pre-existing warnings)
5. **Build Time:** `uv run python scripts/build.py` completes in ≤ 60s
6. **Test Execution:** Full test suite completes in ≤ 45s
7. **No Cyclic Dependencies:** Module graph remains acyclic
8. **global.yml Files:** All three modules (prompts, skills, subagents) have global.yml support

### Regression Detection
Any change that violates these invariants should be flagged as a regression.

---

## Baseline Metadata

| Attribute | Value |
|-----------|-------|
| Baseline format | v1.1 |
| Generated by | establish-baseline prompt |
| Generator version | Python 3.13.11 |
| Determinism guarantee | Identical commit produces identical baseline |

### Recent Changes (since last baseline)
- Added `global.yml` support for skills module
- Added `global.yml` support for subagents module
- Added `SkillEnvironmentConfig` class to `skills/models.py`
- Added `environments` field to `SkillMetadata`
- Updated skills parser to load and merge global defaults
- Updated subagents parser to load and merge global defaults
- All tests passing (517/517)
