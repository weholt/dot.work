# Project Baseline

**Captured:** 2026-01-03T18:15Z
**Commit:** f2e37eb36924ec158ecd8d2f7e91f61a0d4dab39
**Branch:** closing-migration

---

## Scope Summary

### Source Code (`src/`)
- **Total modules:** 1 main package (`dot_work`)
- **Python files:** 42 files
- **Total lines:** ~13,000 lines
- **Module directories:** 11 (prompts, skills, subagents, utils, environments, cli, installer, agents, assets, bundled_skills, bundled_subagents)

### Module Breakdown
| Module | Files | Lines |
|--------|-------|-------|
| `dot_work` (main) | 42 | ~13,000 |

### Test Suite (`tests/`)
- **Python files:** 34 files (29 unit, 4 integration, 1 conftest)
- **Total lines:** ~9,500 lines

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
| `skills_app` | Skills CLI | `src/dot_work/skills/cli.py` |
| `subagents_app` | Subagents CLI | `src/dot_work/subagents/cli.py` |

### Dependencies
| Category | Count |
|----------|-------|
| Direct runtime | 7 |
| Dev dependencies | 10 |
| Total | 17 |

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
| BEH-INST-001 | Supports 14+ AI environments (including Cursor, Windsurf) | Yes | Environment tests |
| BEH-INST-002 | Each environment has unique target directory and filename pattern | Yes | Environment tests |
| BEH-INST-003 | Jinja2 templates rendered with environment-specific context | Yes | Template tests |
| BEH-INST-004 | Canonical prompt format supported with frontmatter validation | Yes | Canonical installer tests |
| BEH-INST-005 | `global.yml` provides default environment configs for prompts | Yes | Global config tests |
| BEH-INST-006 | Local frontmatter overrides global defaults (deep merge) | Yes | Deep merge tests |
| BEH-INST-007 | Cursor environment uses .mdc format with YAML frontmatter | Yes | FEAT-100 tests |
| BEH-INST-008 | Windsurf environment uses plain markdown AGENTS.md | Yes | FEAT-100 tests |

### Skills Behaviors (BEH-SKILL-XXX)
| ID | Behavior | Documented | Verified Via |
|----|----------|-----------|-------------|
| BEH-SKILL-001 | `bundled_skills/` directory exists with global.yml | Yes | `src/dot_work/bundled_skills/global.yml` |
| BEH-SKILL-002 | `SkillEnvironmentConfig` supports target, filename, filename_suffix | Yes | `skills/models.py` |
| BEH-SKILL-003 | `SkillMetadata` includes optional `environments` field | Yes | `skills/models.py` |
| BEH-SKILL-004 | Skills parser loads and merges global.yml defaults | Yes | `skills/parser.py` |
| BEH-SKILL-005 | Empty strings in global.yml are treated as None | Yes | Fixed in CR-001 |
| BEH-SKILL-006 | Skills CLI provides list, validate, show, prompt, install commands | Yes | QA-002 tests |

### Subagents Behaviors (BEH-SUBAGENT-XXX)
| ID | Behavior | Documented | Verified Via |
|----|----------|-----------|-------------|
| BEH-SUBAGENT-001 | `bundled_subagents/` directory exists with global.yml | Yes | `src/dot_work/bundled_subagents/global.yml` |
| BEH-SUBAGENT-002 | Subagents parser loads and merges global.yml defaults | Yes | `subagents/parser.py` |
| BEH-SUBAGENT-003 | Subagents can be synced to multiple environments (claude, cursor, windsurf, etc.) | Yes | QA-001 tests |
| BEH-SUBAGENT-004 | Subagents CLI provides list, validate, show, generate, sync, init, envs commands | Yes | QA-001 tests |

### Undocumented Behaviors
- None identified

---

## Test Evidence

### Test Summary
| Metric | Value |
|--------|-------|
| Total tests | 670 (collected) |
| Executed | 652 |
| Skipped | 18 |
| Passed | 652 |
| Failed | 0 |
| Build time | ~47s |
| Test execution time | ~36s |

### Coverage
| Metric | Value |
|--------|-------|
| Overall coverage | 59% |
| Lines covered | ~4,100 |
| Lines uncovered | ~1,400 |

### Coverage by Module
| Module | Coverage | Notes |
|--------|----------|-------|
| `cli.py` | High | Extensive command tests |
| `installer.py` | High | Comprehensive installation tests |
| `canonical.py` | High | Full parser/validator coverage |
| `skills/parser.py` | High | Parser functions tested |
| `skills/models.py` | Medium | EnvironmentConfig partially tested |
| `skills/cli.py` | High | QA-002 added 19 tests |
| `skills/discovery.py` | High | Discovery tests exist |
| `subagents/parser.py` | High | Parser functions tested |
| `subagents/models.py` | Medium | EnvironmentConfig partially tested |
| `subagents/cli.py` | High | QA-001 added 15 tests |
| `subagents/generator.py` | Low (16%) | QA-003 needs tests |
| `subagents/environments/cursor.py` | High | FEAT-100 added tests |
| `subagents/environments/windsurf.py` | High | FEAT-100 added tests |

### Tested Behaviors
- All BEH-CLI-001 through BEH-CLI-008
- All BEH-INST-001 through BEH-INST-008
- All BEH-SKILL-001 through BEH-SKILL-006
- All BEH-SUBAGENT-001 through BEH-SUBAGENT-004

### Untested Behaviors
- QA-003: `SubagentGenerator` has only 16% coverage
- Some edge cases in environment configs remain untested

---

## Known Gaps

### Code Comments (GAP-CODE-XXX)
| ID | Description | Source |
|----|-------------|--------|
| GAP-CODE-001 | `SubagentGenerator.generate_all()` needs tests | `src/dot_work/subagents/generator.py` |
| GAP-CODE-002 | `SubagentGenerator.generate_native()` needs tests | `src/dot_work/subagents/generator.py` |

### Known Issues from Issue Tracker
| ID | Description | Priority | Status |
|----|-------------|----------|--------|
| GAP-ISSUE-001 | QA-003: Add test coverage for subagents generator (16% → 75%+) | High | Proposed |

### TODO Count
- **Total TODO/FIXME/HACK/XXX comments:** ~8

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
| FAIL-EXP-007 | `ValueError` | `SkillEnvironmentConfig` if filename or filename_suffix is empty string | Raised | Yes |

#### Silent Failures (FAIL-SILENT-XXX)
| ID | Condition | Behavior | Note |
|----|-----------|----------|------|
| FAIL-SILENT-001 | Invalid canonical prompt in directory | Skipped | May be intentional |
| FAIL-SILENT-002 | Missing global.yml | Uses empty dict | Backward compatible |

### Failure Summary
- **Explicit raises:** 7 types
- **Silent fallbacks:** 2 scenarios

---

## Structure

### File Counts
| Category | Count |
|----------|-------|
| Source files (`.py`) | 42 |
| Test files (`.py`) | 34 |
| `global.yml` files | 4 (prompts, skills, subagents, bundled_skills, bundled_subagents) |
| Configuration files | 1 (`pyproject.toml`) |

### Line Counts
| Category | Lines |
|----------|-------|
| Source code | ~13,000 |
| Test code | ~9,500 |
| Total (measured) | ~22,500 |

### Abstraction Depth
| Path | Depth | Notes |
|------|-------|-------|
| CLI -> Installer -> Jinja | 3 | Main installation flow |
| CLI -> Skills Parser -> Environment Config | 3 | Skills parsing |
| CLI -> Subagents Parser -> Environment Config | 3 | Subagents parsing |
| CLI -> Skills CLI -> Discovery | 3 | Skills management |
| CLI -> Subagents CLI -> Generator | 3 | Subagents generation |
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

1. **Test Status:** All 652 tests execute (0 failures, 18 skipped)
2. **Coverage:** Overall coverage ≥ 59%
3. **Type Safety:** mypy reports 0 errors
4. **Linting:** ruff reports 0 errors
5. **Build Time:** `uv run python scripts/build.py` completes in ≤ 60s
6. **Test Execution:** Full test suite completes in ≤ 45s
7. **No Cyclic Dependencies:** Module graph remains acyclic
8. **global.yml Files:** All modules have global.yml support (prompts, skills, subagents, bundled_*)
9. **bundled_* Directories:** bundled_skills/ and bundled_subagents/ exist with global.yml
10. **CLI Applications:** Both skills and subagents CLIs functional with all commands

### Regression Detection
Any change that violates these invariants should be flagged as a regression.

---

## Baseline Metadata

| Attribute | Value |
|-----------|-------|
| Baseline format | v1.2 |
| Generated by | establish-baseline prompt |
| Generator version | Python 3.13.11 |
| Determinism guarantee | Identical commit produces identical baseline |

### Recent Changes (since baseline 5392e34)
- **FEAT-100** completed: Cursor and Windsurf subagent support
- **QA-001** completed: Subagents CLI test coverage (15 tests)
- **QA-002** completed: Skills CLI test coverage (19 tests)
- **Test count increase:** 618 → 670 (+52 tests)
- **All tests passing:** 652 executed (18 skipped)
- **Build time stable:** ~47s
- **Coverage increase:** 56% → 59%
