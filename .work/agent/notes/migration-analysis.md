# Migration Issues Analysis

All migration issues organized by source project, with current status.

## Executive Summary

- **Total migration issues**: 74 (MIGRATE-001 through MIGRATE-069)
- **Completed**: 30 issues (40.5%)
- **Pending**: 44 issues (59.5%)

## Completed Migrations ✅

### 1. **agent-review** (12 issues)
- Source: incoming/review
- Issues: MIGRATE-001 through MIGRATE-012
- Status: All completed
- Result: Review functionality fully integrated

### 2. **kgshred/knowledge_graph** (8 issues)
- Source: incoming/glorious/src/glorious_agents/skills/kgshred/
- Issues: MIGRATE-013 through MIGRATE-020
- Status: All completed
- Result: Knowledge graph functionality fully integrated

### 3. **zipparu** (6 issues)
- Source: incoming/zipparu/
- Issues: MIGRATE-021 through MIGRATE-026
- Status: All completed
- Result: Zip functionality fully integrated

### 4. **version-management** (6 issues)
- Source: incoming/crampus/version-management/
- Issues: MIGRATE-041 through MIGRATE-046
- Status: All completed
  - MIGRATE-041: Module structure created ✅
  - MIGRATE-042: Imports updated ✅
  - MIGRATE-043: CLI integration ✅
  - MIGRATE-044: Dependencies added ✅
  - MIGRATE-045: Tests created (need API fixes) ⚠️
  - MIGRATE-046: Verification completed ✅
- Result: Version module functional, tests need minor fixes

## Pending Migrations 📋

### 1. **code-atlas/python-scan** (7 issues)
- Source: incoming/glorious/src/glorious_agents/skills/code-atlas/
- Issues: MIGRATE-027 through MIGRATE-033
- Status: All proposed
- Features: AST parsing, Radon metrics, dependency graphs

### 2. **issue-tracker/db-issues** (7 issues)
- Source: incoming/glorious/src/glorious_agents/skills/issues/
- Issues: MIGRATE-034 through MIGRATE-040
- Status: All proposed
- Features: SQLite-backed issue management

### 3. **repo-agent/container-provision** (6 issues)
- Source: incoming/crampus/repo-agent/
- Issues: MIGRATE-047 through MIGRATE-052
- Status: All proposed
- Features: LLM-powered code agents in Docker

### 4. **builder/python-build** (5 issues)
- Source: incoming/crampus/builder/
- Issues: MIGRATE-053 through MIGRATE-057
- Status: All proposed
- Features: Python build pipeline (format, lint, test, security, docs)

### 5. **birdseye/overview** (6 issues)
- Source: incoming/crampus/birdseye/
- Issues: MIGRATE-058 through MIGRATE-063
- Status: All proposed
- Features: Project overview analysis and markdown generation

### 6. **git-analysis/git-history** (6 issues)
- Source: incoming/crampus/git-analysis/
- Issues: MIGRATE-064 through MIGRATE-069
- Status: All proposed
- Features: Git repository history analysis

## Migration Pattern

Each migration follows this 7-step pattern:
1. Create module structure
2. Update imports
3. Register CLI command
4. Add dependencies
5. Configure storage paths
6. Add tests
7. Verify with full build

## Key Observations

1. **4 of 10 projects fully migrated** (40%)
2. **ZIP migration was the quickest** (small utility)
3. **Version management partially complete** (tests need fixes)
4. **All pending issues are medium priority**
5. **Python ecosystem heavily represented** (scan, build, overview)

## Recommendation

Start with the smallest remaining project:
- **Python scan (MIGRATE-027)** - 7 issues, features Python code analysis
- Or **Git history (MIGRATE-064)** - 6 issues, provides git analytics

Both provide high value with manageable scope.

## Note on FEAT-002

FEAT-002@b8d4e1 (YAML validation) has been marked as **won't-fix** because:
- YAML specification is too complex for stdlib-only implementation
- PyYAML is already a project dependency
- Current yaml_validator.py using PyYAML is functional
- Cost/benefit of implementing YAML from scratch is prohibitive