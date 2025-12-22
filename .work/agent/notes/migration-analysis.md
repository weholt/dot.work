# Migration Tasks Analysis

**Generated:** 2025-12-22
**Analysis of:** All MIGRATE issues in .work/agent/issues/

---

## Executive Summary

**Total Migration Tasks:** 69 (MIGRATE-001 through MIGRATE-069)
- **Completed:** 20 (MIGRATE-001 through MIGRATE-020)
- **Proposed/Pending:** 49 (MIGRATE-021 through MIGRATE-069)
- **Completion Rate:** 29%

**Status by Priority:**
- **High (P1):** 6 tasks - ALL COMPLETED ✅ (MIGRATE-013 through MIGRATE-018)
- **Medium (P2):** 63 tasks - 14 completed, 49 proposed

---

## Completed Migrations (20 tasks) ✅

### Review Subsystem (MIGRATE-001 through MIGRATE-012)
Complete migration of agent-review into dot-work/review/ subsystem.

| ID | Title | Status |
|----|----|--------|
| MIGRATE-001@a1b2c3 | Create dot_work/review subpackage structure | ✅ |
| MIGRATE-002@b2c3d4 | Update all import paths in review subpackage | ✅ |
| MIGRATE-003@c3d4e5 | Copy static assets and templates for review UI | ✅ |
| MIGRATE-004@d4e5f6 | Add new dependencies for review functionality | ✅ |
| MIGRATE-005@e5f6a7 | Integrate review command into dot-work CLI | ✅ |
| MIGRATE-006@f6a7b8 | Migrate review unit tests | ✅ |
| MIGRATE-007@a7b8c9 | Add review integration tests | ✅ |
| MIGRATE-008@b8c9d0 | Update Python version requirement to 3.11+ | ✅ |
| MIGRATE-009@c9d0e1 | Update storage path to .work/reviews/ | ✅ |
| MIGRATE-010@d0e1f2 | Add review command documentation to README | ✅ |
| MIGRATE-011@e1f2a3 | Add review CLI tests | ✅ |
| MIGRATE-012@f2a3b4 | Clean up incoming/review after successful migration | ✅ |

### Knowledge Graph (kg) Subsystem (MIGRATE-013 through MIGRATE-020)
Complete migration of kgshred into dot-work/knowledge_graph/ subsystem.

| ID | Title | Status |
|----|----|--------|
| MIGRATE-013@a7f3b2 | Create knowledge_graph module structure in dot-work | ✅ |
| MIGRATE-014@b8c4d3 | Update all imports in knowledge_graph module | ✅ |
| MIGRATE-015@c9d5e4 | Update knowledge_graph config to use .work/kg/ | ✅ |
| MIGRATE-016@d0e6f5 | Register kg as subcommand group in dot-work CLI | ✅ |
| MIGRATE-017@e1f7a6 | Add standalone 'kg' command entry point | ✅ |
| MIGRATE-018@f2a8b7 | Add kg optional dependencies to pyproject.toml | ✅ |
| MIGRATE-019@a3b9c8 | Migrate kg tests to dot-work test suite | ✅ |
| MIGRATE-020@b4c0d9 | Verify kg migration with full build and testing | ✅ |

---

## Proposed/Pending Migrations (49 tasks) 🔄

### 1. ZIP Module (MIGRATE-021 through MIGRATE-026) - 6 tasks
**Source:** `incoming/zipparu/`
**Destination:** `src/dot_work/zip/`
**Purpose:** Archive projects with optional upload capability

| # | ID | Task | Dependencies |
|---|----|----|---|
| 1 | MIGRATE-021@c5d6e7 | Create zip module structure | — |
| 2 | MIGRATE-022@d6e7f8 | Update zip imports and config | MIGRATE-021 |
| 3 | MIGRATE-023@e7f8a9 | Register zip as subcommand | MIGRATE-022 |
| 4 | MIGRATE-024@f8a9b0 | Add zip dependencies (gitignore_parser, requests) | — |
| 5 | MIGRATE-025@a9b0c1 | Add zip module tests | MIGRATE-023 |
| 6 | MIGRATE-026@b0c1d2 | Verify zip migration | MIGRATE-025 |

**Expected CLI:** `dot-work zip <folder>` or `dot-work zip <folder> --upload`

---

### 2. Python Scan Module (MIGRATE-027 through MIGRATE-033) - 7 tasks
**Source:** `incoming/glorious/src/glorious_agents/skills/code-atlas/`
**Destination:** `src/dot_work/python/scan/`
**Purpose:** Analyze Python projects for metrics and issues

| # | ID | Task | Dependencies |
|---|----|----|---|
| 1 | MIGRATE-027@c1d2e3 | Create python scan module structure | — |
| 2 | MIGRATE-028@d2e3f4 | Update scan imports (code_atlas → dot_work.python.scan) | MIGRATE-027 |
| 3 | MIGRATE-029@e3f4a5 | Register scan as subcommand (dot-work python scan) | MIGRATE-028 |
| 4 | MIGRATE-030@f4a5b6 | Add scan dependencies (radon, pyyaml) | — |
| 5 | MIGRATE-031@a5b6c7 | Configure scan storage in .work/scan/ | MIGRATE-029 |
| 6 | MIGRATE-032@b6c7d8 | Add scan module tests | MIGRATE-031 |
| 7 | MIGRATE-033@c7d8e9 | Verify scan migration | MIGRATE-032 |

**Expected CLI:** `dot-work python scan <cmd>`

---

### 3. Database Issues Module (MIGRATE-034 through MIGRATE-040) - 7 tasks
**Source:** `incoming/glorious/src/glorious_agents/skills/issues/`
**Destination:** `src/dot_work/db_issues/`
**Purpose:** Database-backed issue tracking and CRUD operations

| # | ID | Task | Dependencies |
|---|----|----|---|
| 1 | MIGRATE-034@d8e9f0 | Create db-issues module structure | — |
| 2 | MIGRATE-035@e9f0a1 | Update db-issues imports | MIGRATE-034 |
| 3 | MIGRATE-036@f0a1b2 | Register db-issues as subcommand | MIGRATE-035 |
| 4 | MIGRATE-037@a1b2c3 | Add db-issues dependencies (sqlmodel, gitpython) | — |
| 5 | MIGRATE-038@b2c3d4 | Configure db-issues storage in .work/db-issues/ | MIGRATE-036 |
| 6 | MIGRATE-039@c3d4e5 | Add db-issues module tests | MIGRATE-038 |
| 7 | MIGRATE-040@d4e5f6 | Verify db-issues migration | MIGRATE-039 |

**Expected CLI:** `dot-work db-issues <cmd>`

---

### 4. Version Management Module (MIGRATE-041 through MIGRATE-046) - 6 tasks
**Source:** `incoming/crampus/version-management/`
**Destination:** `src/dot_work/version/`
**Purpose:** Semantic version management with bump automation

| # | ID | Task | Dependencies |
|---|----|----|---|
| 1 | MIGRATE-041@e5f6a7 | Create version module structure | — |
| 2 | MIGRATE-042@f6a7b8 | Update version imports (version_management → dot_work.version) | MIGRATE-041 |
| 3 | MIGRATE-043@a7b8c9 | Register version as subcommand | MIGRATE-042 |
| 4 | MIGRATE-044@b8c9d0 | Add version dependencies (GitPython, Jinja2, pydantic) | — |
| 5 | MIGRATE-045@c9d0e1 | Add version module tests | MIGRATE-043 |
| 6 | MIGRATE-046@d0e1f2 | Verify version migration | MIGRATE-045 |

**Expected CLI:** `dot-work version <cmd>`

---

### 5. Container Provisioning Module (MIGRATE-047 through MIGRATE-052) - 6 tasks
**Source:** `incoming/crampus/repo-agent/`
**Destination:** `src/dot_work/container/provision/`
**Purpose:** Provision Docker containers from frontmatter specifications

| # | ID | Task | Dependencies |
|---|----|----|---|
| 1 | MIGRATE-047@e1f2a3 | Create container provision module structure | — |
| 2 | MIGRATE-048@f2a3b4 | Update container provision imports | MIGRATE-047 |
| 3 | MIGRATE-049@a3b4c5 | Register container provision as subcommand | MIGRATE-048 |
| 4 | MIGRATE-050@b4c5d6 | Add container dependencies (python-frontmatter) | — |
| 5 | MIGRATE-051@c5d6e7 | Add container provision tests | MIGRATE-049 |
| 6 | MIGRATE-052@d6e7f8 | Verify container provision migration | MIGRATE-051 |

**Expected CLI:** `dot-work container provision <files>`

---

### 6. Python Build Module (MIGRATE-053 through MIGRATE-057) - 5 tasks
**Source:** `incoming/crampus/builder/`
**Destination:** `src/dot_work/python/build/`
**Purpose:** Build pipeline automation for Python projects

| # | ID | Task | Dependencies |
|---|----|----|---|
| 1 | MIGRATE-053@e7f8a9 | Create python build module structure | — |
| 2 | MIGRATE-054@f8a9b0 | Update python build imports and convert CLI (argparse→typer) | MIGRATE-053 |
| 3 | MIGRATE-055@a9b0c1 | Register build as subcommand and standalone entry point | MIGRATE-054 |
| 4 | MIGRATE-056@b0c1d2 | Add build module tests | MIGRATE-055 |
| 5 | MIGRATE-057@c1d2e3 | Verify python build migration | MIGRATE-056 |

**Expected CLI:** `dot-work python build` or standalone `pybuilder`

---

### 7. Overview/Analysis Module (MIGRATE-058 through MIGRATE-063) - 6 tasks
**Source:** `incoming/crampus/birdseye/`
**Destination:** `src/dot_work/overview/`
**Purpose:** Project structure and complexity analysis

| # | ID | Task | Dependencies |
|---|----|----|---|
| 1 | MIGRATE-058@d2e3f4 | Create overview module structure | — |
| 2 | MIGRATE-059@e3f4a5 | Update overview imports (birdseye → dot_work.overview) | MIGRATE-058 |
| 3 | MIGRATE-060@f4a5b6 | Register overview as top-level subcommand | MIGRATE-059 |
| 4 | MIGRATE-061@a5b6c7 | Add overview dependencies (libcst, radon) | — |
| 5 | MIGRATE-062@b6c7d8 | Add overview module tests | MIGRATE-060 |
| 6 | MIGRATE-063@c7d8e9 | Verify overview migration | MIGRATE-062 |

**Expected CLI:** `dot-work overview <input> <output>`

---

### 8. Git History Analysis Module (MIGRATE-064 through MIGRATE-069) - 6 tasks
**Source:** `incoming/crampus/git-analysis/`
**Destination:** `src/dot_work/git/history/`
**Purpose:** Git commit history analysis and reporting

| # | ID | Task | Dependencies |
|---|----|----|---|
| 1 | MIGRATE-064@8f2a1b | Create git history module structure | — |
| 2 | MIGRATE-065@9c3b2d | Update git history imports and dependencies | MIGRATE-064 |
| 3 | MIGRATE-066@a4d3e5 | Register git history as git subcommand | MIGRATE-065 |
| 4 | MIGRATE-067@b5e4f6 | Add unit tests for git history | MIGRATE-066 |
| 5 | MIGRATE-068@c6f5a7 | Add integration tests (with real git repo) | MIGRATE-067 |
| 6 | MIGRATE-069@d7a6b8 | Verify git history migration end-to-end | MIGRATE-068 |

**Expected CLI:** `dot-work git history <cmd>`

---

## Migration Chains & Dependencies

### Sequential Dependency Graph

```
MIGRATE-001 → MIGRATE-002 → MIGRATE-003 → MIGRATE-004 → MIGRATE-005 → MIGRATE-006 → MIGRATE-007 → MIGRATE-008 → MIGRATE-009 → MIGRATE-010 → MIGRATE-011 → MIGRATE-012
     (Review subsystem - completed ✅)

MIGRATE-013 → MIGRATE-014 → MIGRATE-015 → MIGRATE-016 → MIGRATE-017 → MIGRATE-018 → MIGRATE-019 → MIGRATE-020
     (kg subsystem - completed ✅)

MIGRATE-021 → MIGRATE-022 → MIGRATE-023 ← MIGRATE-024 → MIGRATE-025 → MIGRATE-026 (zip)
MIGRATE-027 → MIGRATE-028 → MIGRATE-029 ← MIGRATE-030 → MIGRATE-031 → MIGRATE-032 → MIGRATE-033 (python/scan)
MIGRATE-034 → MIGRATE-035 → MIGRATE-036 ← MIGRATE-037 → MIGRATE-038 → MIGRATE-039 → MIGRATE-040 (db-issues)
MIGRATE-041 → MIGRATE-042 → MIGRATE-043 ← MIGRATE-044 → MIGRATE-045 → MIGRATE-046 (version)
MIGRATE-047 → MIGRATE-048 → MIGRATE-049 ← MIGRATE-050 → MIGRATE-051 → MIGRATE-052 (container)
MIGRATE-053 → MIGRATE-054 → MIGRATE-055 → MIGRATE-056 → MIGRATE-057 (python/build)
MIGRATE-058 → MIGRATE-059 → MIGRATE-060 ← MIGRATE-061 → MIGRATE-062 → MIGRATE-063 (overview)
MIGRATE-064 → MIGRATE-065 → MIGRATE-066 → MIGRATE-067 → MIGRATE-068 → MIGRATE-069 (git/history)
```

**Pattern:** Each subsystem has a chain:
1. Create module structure (no deps)
2. Update imports (depends on step 1)
3. Register CLI (depends on step 2)
4. Add dependencies (no deps - parallel)
5. Config/Storage (depends on step 3)
6. Tests (depends on step 5)
7. Verification (depends on step 6)

---

## Recommended Focus Order

### Next Priority (MIGRATE-021+)

**Option A: ZIP First (Smallest/Quickest)**
- **Effort:** 6 tasks, ~4-6 hours
- **Start:** MIGRATE-021@c5d6e7
- **Rationale:** Simplest subsystem, good warm-up, can be done quickly
- **Dependencies:** gitignore_parser (new), requests (optional)

**Option B: Python Scan (Medium/High Impact)**
- **Effort:** 7 tasks, ~6-8 hours
- **Start:** MIGRATE-027@c1d2e3
- **Rationale:** Part of larger python group, useful for project analysis
- **Dependencies:** radon (new), pyyaml (exists)
- **Note:** Pairs well with MIGRATE-053+ (python/build) later

**Option C: Version Management (Strategic)**
- **Effort:** 6 tasks, ~5-7 hours
- **Start:** MIGRATE-041@e5f6a7
- **Rationale:** Critical for project versioning, enables bump-version workflow
- **Dependencies:** GitPython (new), Jinja2 (exists), pydantic (exists)
- **Value:** Unlocks automated versioning across all projects

**Option D: Git History (Integration Value)**
- **Effort:** 6 tasks, ~6-8 hours
- **Start:** MIGRATE-064@8f2a1b
- **Rationale:** Provides git analysis for CI/CD pipelines
- **Dependencies:** Likely already has git support
- **Value:** Enables commit history reporting

---

## Key Observations

### Completed Subsystems Status
✅ **Review (MIGRATE-001-012)** - agent-review fully integrated
✅ **Knowledge Graph (MIGRATE-013-020)** - kgshred fully integrated

### Pattern Recognition
All pending migrations follow the same pattern:
1. **Create structure** - Copy files
2. **Refactor imports** - Change package references
3. **CLI registration** - Add to dot-work command tree
4. **Dependencies** - Update pyproject.toml
5. **Configuration** - Set up storage paths
6. **Testing** - Unit + integration tests
7. **Verification** - Full build validation

### Parallel Opportunity
- Steps 1, 3, 4 can run in parallel across subsystems
- Steps 2, 5, 6, 7 are more tightly coupled

### Total Remaining Effort
- **Quick estimate:** 49 tasks × 30-45 min average = **24-36 hours**
- **Optimistic:** With batching/parallelism: **16-20 hours**
- **Conservative:** With thorough testing: **40-50 hours**

---

## Recommended Starting Task

**RECOMMENDATION: Start with MIGRATE-021 (ZIP Module)**

**Why:**
1. **Shortest chain** - Only 6 tasks
2. **Clear scope** - Single, well-defined purpose
3. **Good learning** - Establishes migration pattern
4. **Low risk** - Small subsystem, easy to verify
5. **Quick win** - Can complete in 1-2 sessions
6. **Foundation** - Prepares for larger migrations

**Command to start:**
```bash
focus on "Migrate zip module: copy zipparu to src/dot_work/zip/"
```

This will create MIGRATE-021 through MIGRATE-026 in shortlist.md for immediate work.

---

## Alternative: Fast-Track Strategy

For maximum impact with moderate effort:

1. **MIGRATE-041+** (Version Management) - Strategic value
2. **MIGRATE-027+** (Python Scan) - Enables code analysis
3. **MIGRATE-053+** (Python Build) - Completes python tooling
4. Result: `dot-work python` command suite fully functional

This 18-task sequence (3 subsystems × 6 tasks) could be done in ~10-12 hours and provides complete Python development workflow.

