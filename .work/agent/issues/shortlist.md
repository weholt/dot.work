# Shortlist (User-Directed Priority)

This file represents **explicit user intent**. Agent may only modify when explicitly instructed.

---

## Active Work

---

All previous shortlist items (ENH-025, ENH-026, REFACTOR-003, TEST-041, TEST-042, TEST-043) have been completed and moved to history.md.

---

## Skills & Subagents

---
All previous shortlist items (ENH-025, ENH-026, REFACTOR-003, TEST-041, TEST-042, TEST-043, FEAT-023, FEAT-024) have been completed and moved to history.md.
---

## Docker / Containers

---
All previous shortlist items (ENH-025, ENH-026, REFACTOR-003, TEST-041, TEST-042, TEST-043, FEAT-023, FEAT-024, FEAT-025, FEAT-026, FEAT-027) have been completed and moved to history.md.
---
id: "FEAT-028@f2g8h4"
title: "File upload/download utilities for OpenCode containers"
description: "Add optional file transfer utilities for easy uploading and downloading files to and from running containers"
created: 2025-12-30
section: "container/docker/file-transfer"
tags: [feature, docker, containerization, opencode, file-transfer, upload, download, has-deps]
type: enhancement
priority: medium
status: proposed
references:
  - .work/agent/issues/shortlist.md:FEAT-025@c9d5e1
  - README.md
  - src/dot_work/container/provision/core.py

### Problem
Transferring files to/from running containers requires manual `docker cp` commands. Users need convenient utilities for file exchange during agent sessions.

### Affected Files
- Create: `src/dot_work/container/provision/transfer.py` (wrapper around docker cp)
- Modify: `src/dot_work/container/provision/cli.py` (add `upload`/`download` subcommands)
- Create: `tests/integration/container/test_transfer.py`

### Importance
Medium priority. Convenience feature for interactive use. Builds on FEAT-025 containers.

### Proposed Solution
1. **Implementation**: Wrapper around `docker cp` (simple, recommended)
2. **Upload Command**: `dot-work container upload <container-id> <local-path> <container-path>`
   - Requires both paths (no defaults)
   - Container ID must be full match (exact)
3. **Download Command**: `dot-work container download <container-id> <container-path> <local-path>`
   - Requires both paths (no defaults)
4. **Batch Operations**: Support glob patterns for multiple files
5. **Progress Indication**: Show progress for large files (>1MB)
6. **Conflict Resolution**: `--force` flag to skip overwrite prompt

### Acceptance Criteria
- [ ] `upload` command copies local files to container via docker cp
- [ ] `download` command copies container files to local via docker cp
- [ ] Glob patterns expand for batch operations
- [ ] Progress bar shown for files >1MB
- [ ] Overwrite prompt or `--force` skips prompt
- [ ] Container ID must be exact match (full ID required)
- [ ] Integration tests with real container

### Validation Plan
```bash
# Upload single file (exact container ID required)
uv run dot-work container upload abc123def456 /local/file.txt /root/in-container.txt

# Download directory
uv run dot-work container download abc123def456 /root/workspace/ ./local-workspace/

# Batch upload with glob
uv run dot-work container upload abc123def456 "src/**/*.py" /root/src/

# Force overwrite
uv run dot-work container upload abc123def456 file.txt /root/file.txt --force
```

### Dependencies
Blocked by: FEAT-025@c9d5e1 (container provisioning)
Blocks: None

### Clarifications Needed
None. All decisions resolved:
- Implementation: Wrapper around `docker cp`
- Container ID: Require full container ID (exact match)
- Default paths: No defaults, require both paths

### Notes
Consider adding `--interactive` flag for TUI-based file browser (future enhancement).

---

## Orchestration

---
All previous shortlist items (FEAT-029) have been completed and moved to history.md.
---
id: "FEAT-030@k7l3m9"
title: "Create pre-flight check prompt for autonomous operation readiness"
description: "Add prompt that validates environment, dependencies, and configuration before autonomous agent operation begins"
created: 2025-12-30
section: "prompts/orchestration"
tags: [feature, prompts, pre-flight, validation, autonomy, safety]
type: enhancement
priority: high
status: proposed
references:
  - agent-loop.md
  - src/dot_work/prompts/do-work.md
  - src/dot_work/prompts/establish-baseline.md

### Problem
Autonomous agents may fail mid-cycle due to missing dependencies, invalid config, or environment issues. Pre-flight checks catch problems before starting the agent-loop.

### Affected Files
- Create: `src/dot_work/prompts/preflight-check.md`
- Modify: `agent-loop.md` (add pre-flight step at start)

### Importance
High priority. Prevents wasted cycles on doomed agent runs. Catches environmental issues early.

### Proposed Solution
Create preflight-check.md prompt that validates:
1. **Build status**: `uv run python scripts/build.py` passes with no errors
2. **Tests pass**: All tests pass at baseline (no regressions)
3. **Git clean**: No uncommitted changes (if `--strict` flag applied)
4. **Disk space**: Minimum 1GB free
5. **Python version**: Correct version installed
6. **Dependencies**: All required packages importable
7. **Issue tracker**: All issue files exist and are valid YAML

Configurable strictness:
- `--strict`: All checks required (any failure aborts), require clean git
- `--lenient`: Core required (build, tests), optional warnings (disk space, git clean)

Auto-fix capability: Auto-fix ALL fixable issues (install missing deps, fix formatting, etc.)

### Acceptance Criteria
- [ ] Pre-flight runs all checks before agent-loop
- [ ] Each check outputs PASS/FAIL with details
- [ ] `--strict` flag: Any failure aborts, clean git required
- [ ] `--lenient` flag: Core aborts, optional warn only
- [ ] Auto-fix attempts to fix all fixable issues
- [ ] Checks are fast (<10 seconds total)
- [ ] Integration test with failure scenarios
- [ ] Configurable check list via flags

### Validation Plan
```bash
# Unit test for each check function
uv run pytest tests/unit/prompts/test_preflight.py -v

# Integration test with induced failures
# - Create failing test, verify pre-flight catches it
# - Remove git config, verify pre-flight catches it

# Strict mode (requires clean git)
uv run dot-work preflight-check --strict

# Lenient mode (warns on dirty git)
uv run dot-work preflight-check --lenient
```

### Dependencies
Blocked by: None
Blocks: None (but should run before FEAT-029 orchestrator)

### Clarifications Needed
None. All decisions resolved:
- Required vs optional: Configurable via `--strict` and `--lenient` flags
- Git state: Require clean git if `--strict` flag applied
- Auto-fix: Auto-fix ALL fixable issues

### Notes
Pre-flight should be callable standalone: `/preflight-check` for manual use.

---
id: "FEAT-031@m9n5o1"
title: "Create error-recovery prompt for autonomous operation failures"
description: "Add prompt specialized in diagnosing and recovering from errors during autonomous agent operation"
created: 2025-12-30
section: "prompts/orchestration"
tags: [feature, prompts, error-recovery, autonomy, resilience]
type: enhancement
priority: high
status: proposed
references:
  - agent-loop.md
  - src/dot_work/prompts/do-work.md

### Problem
When autonomous agents fail (build errors, test failures, OOM), they currently stop. Error-recovery prompt should diagnose and attempt automatic recovery before aborting.

### Affected Files
- Create: `src/dot_work/prompts/error-recovery.md`
- Modify: `agent-loop.md` (add error recovery step after failures)
- Create: `.work/agent/error-log.txt` (escalation destination)

### Importance
High priority. Improves agent resilience. Reduces need for manual intervention.

### Proposed Solution
Create error-recovery.md prompt that:
1. **Analyzes error**: Parse error type by priority (critical, high, medium, low)
   - Critical: Build errors, syntax errors (cannot continue)
   - High: Test failures, import errors (blocks progress)
   - Medium: OOM, resource limits (recoverable)
   - Low: Warnings, lint issues (non-blocking)
2. **Selects strategy**:
   - Critical: Log and abort (no recovery)
   - High: Attempt fix then escalate (install deps, add imports)
   - Medium: Retry with exponential backoff (1s, 2s, 4s)
   - Low: Log and continue
3. **Retry behavior**: Exponential backoff (1s, 2s, 4s) for medium priority
4. **Escalation**: Append to `.work/agent/error-log.txt` with details

### Acceptance Criteria
- [ ] Error-recovery classifies errors into critical/high/medium/low
- [ ] Each priority level has recovery strategy
- [ ] Exponential backoff (1s, 2s, 4s) for medium priority errors
- [ ] Failed recovery appends to `.work/agent/error-log.txt`
- [ ] Integration tests for each error type
- [ ] Max retry limit (3 attempts before escalate)

### Validation Plan
```bash
# Integration test with induced failures
uv run pytest tests/integration/prompts/test_error_recovery.py -v

# Test scenarios:
# - Introduce syntax error (critical), verify abort
# - Break a test (high), verify fix attempt + escalation
# - Remove import (high), verify package install attempt
# - OOM (medium), verify exponential backoff retries

# Check error log
cat .work/agent/error-log.txt
```

### Dependencies
Blocked by: None
Blocks: None

### Clarifications Needed
None. All decisions resolved:
- Error classification: critical, high, medium, low priority levels
- Retry behavior: Exponential backoff (1s, 2s, 4s)
- Escalation destination: Append to error log file

### Notes
Error-recovery should be idempotent (can run multiple times safely).

---
id: "FEAT-032@o1p7q3"
title: "Create issue-to-implementation prompt for zero-ambiguity task execution"
description: "Add prompt that transforms any issue into explicit, deterministic implementation steps with validation"
created: 2025-12-30
section: "prompts/execution"
tags: [feature, prompts, implementation, determinism, autonomy]
type: enhancement
priority: high
status: proposed
references:
  - src/dot_work/prompts/do-work.md
  - src/dot_work/prompts/issue-readiness.md

### Problem
Issues in the tracker are often under-specified (missing acceptance criteria, vague steps). Implementation fails due to ambiguity. Issue-to-implementation prompt should transform any issue into executable steps.

### Affected Files
- Create: `src/dot_work/prompts/issue-to-implementation.md`
- Modify: `src/dot_work/prompts/issue-readiness.md` (reference new prompt)
- Create: `.work/agent/implementation-plan.md` (output file)

### Importance
High priority. Reduces implementation failures. Complements issue-readiness.md by generating implementation plans from existing issues.

### Proposed Solution
Create issue-to-implementation.md prompt that:
1. **Reads issue**: Supports three input methods via CLI arguments
   - By issue ID: `--issue RES-001`
   - By file path + search: `--file medium.md --search "resource leak"`
   - From stdin: pipe from grep
2. **Validates completeness**: Check for required sections (Problem, Solution, Acceptance Criteria)
3. **Handles ambiguity**: Refuse underspecified issues (require issue-readiness first)
4. **Generates steps**: Convert Proposed Solution into numbered list of actions
5. **Adds validation**: Derive test commands from Affected Files and Acceptance Criteria
6. **Output format**: Both (stdout + file)
   - Print to stdout (for piping to agents)
   - Write to `.work/agent/implementation-plan.md`

### Acceptance Criteria
- [ ] CLI supports all three input methods (--issue, --file+--search, stdin)
- [ ] Prompt reads issue from file path or issue ID
- [ ] Underspecified issues trigger refusal (require issue-readiness first)
- [ ] Generates step-by-step implementation plan
- [ ] Each step has deterministic validation (command, expected output)
- [ ] Output both to stdout and `.work/agent/implementation-plan.md`
- [ ] Output format matches existing prompts (markdown with code blocks)
- [ ] Integration test with sample issues

### Validation Plan
```bash
# Unit test with sample issue
uv run pytest tests/integration/prompts/test_issue_to_implementation.py -v

# By issue ID
uv run dot-work prompt issue-to-implementation --issue RES-001

# By file and search
uv run dot-work prompt issue-to-implementation --file medium.md --search "resource leak"

# From stdin
grep "FEAT-025" .work/agent/issues/shortlist.md | uv run dot-work prompt issue-to-implementation

# Check both outputs
cat .work/agent/implementation-plan.md
```

### Dependencies
Blocked by: None
Blocks: None

### Clarifications Needed
None. All decisions resolved:
- Issue selection: All three options with CLI arguments
- Ambiguity handling: Refuse underspecified issues (require issue-readiness first)
- Output format: Both (stdout + file)

### Notes
This prompt is the "executor" complement to issue-readiness.md (the "planner").

---
id: "FEAT-033@p2q8r4"
title: "Add resource-aware prompt loading for token optimization"
description: "Implement progressive prompt loading based on available context window and task requirements"
created: 2025-12-30
section: "prompts/optimization"
tags: [feature, prompts, tokens, optimization, progressive-loading]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/prompts/
  - agent-loop.md

### Problem
Long prompts (e.g., agent-loop.md with all sub-prompts) can exceed context windows. Progressive loading would load only essential content first, then append details as needed.

### Affected Files
- Create: `src/dot_work/prompts/loader.py` (token-aware prompt loader)
- Modify: `src/dot_work/prompts/__init__.py` (export loader)
- Modify: `agent-loop.md` (add progressive frontmatter to sections)

### Importance
Medium priority. Optimizes token usage for large prompts. Not blocking for basic functionality.

### Proposed Solution
1. **Marker format**: YAML frontmatter in prompt sections
   ```yaml
   ---
   progressive: critical
   ---
   ```
2. **Priority levels**: 5 levels for load ordering
   - `critical`: Always load (required sections)
   - `high`: Load if space permits
   - `medium`: Load if space permits
   - `low`: Load only if abundant space
   - `discard`: Never load (debug/verbose content)
3. **Token estimation**: Actual tokenizer (tiktoken) for accuracy
   - Add `tiktoken` to dependencies
4. **Progressive loading**: Load by priority until context window reached
5. **Context window detection**: Read from `CONTEXT_WINDOW` env var or `--context-window` flag

### Acceptance Criteria
- [ ] YAML frontmatter `progressive: <level>` marks sections
- [ ] Five priority levels: critical, high, medium, low, discard
- [ ] Token estimation using tiktoken (accurate)
- [ ] Progressive sections load by priority order
- [ ] Context window from `CONTEXT_WINDOW` env var or `--context-window` flag
- [ ] Integration test with large prompt
- [ ] Documentation for adding progressive markers

### Validation Plan
```bash
# Unit test for token estimation
uv run pytest tests/unit/prompts/test_loader.py::test_token_estimation -v

# Integration test
CONTEXT_WINDOW=8000 uv run dot-work prompt load agent-loop.md

# With flag
uv run dot-work prompt load agent-loop.md --context-window 16000
```

### Dependencies
Blocked by: None
Blocks: None

### Clarifications Needed
None. All decisions resolved:
- Marker format: YAML frontmatter `progressive: true`
- Priority levels: 5 levels (critical, high, medium, low, discard)
- Estimation method: Actual tokenizer (tiktoken)

### Notes
Cache token counts to avoid re-parsing prompts. Add tiktoken to project dependencies.

---
id: "FEAT-034@q3r9s5"
title: "Create symbiosis map for prompt composition and workflow optimization"
description: "Document how prompts work together and optimal composition patterns for different workflows"
created: 2025-12-30
section: "prompts/documentation"
tags: [feature, prompts, documentation, symbiosis, workflows]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/prompts/
  - agent-loop.md
  - src/dot_work/prompts/agent-prompts-reference.md

### Problem
Prompts have complex interdependencies (orchestrator calls do-work, do-work calls new-issue). No central document explains how they compose. Users don't know optimal prompt combinations for workflows.

### Affected Files
- Create: `.work/prompts-symbiosis.md` (project documentation)
- Update: `src/dot_work/prompts/agent-prompts-reference.md` (add cross-references)

### Importance
Medium priority. Documentation improves discoverability and correct usage. Not blocking for functionality.

### Proposed Solution
Create symbiosis map document at `.work/prompts-symbiosis.md` that:
1. **Lists all prompts** with purpose and trigger conditions
2. **Shows relationships**: Call graph (orchestrator → do-work → new-issue, etc.)
3. **Defines 10 workflows** covering all agent-loop scenarios:
   - Fix bug
   - Add feature
   - Refactor code
   - Run tests
   - Code review
   - Performance review
   - Security review
   - Generate baseline
   - Pre-flight check
   - Error recovery
4. **Documents outputs**: What each prompt produces (files, state, side effects)
5. **Optimization notes**: When to skip prompts, combine prompts, or use alternatives
6. **Format style**: Both Mermaid graph + ASCII table fallback

### Acceptance Criteria
- [ ] Symbiosis map created at `.work/prompts-symbiosis.md`
- [ ] Lists all prompts in `src/dot_work/prompts/` with descriptions
- [ ] Call graph shows prompt relationships (Mermaid + ASCII fallback)
- [ ] 10 workflow recipes for common tasks
- [ ] agent-prompts-reference.md updated with cross-references
- [ ] Documentation link check passes (no dead links)

### Validation Plan
```bash
# Documentation link check (no dead links)
uv run pytest tests/unit/prompts/test_symbiosis_links.py -v

# Manual verification
# View Mermaid graph in renderer
# Verify ASCII fallback is readable
cat .work/prompts-symbiosis.md
```

### Dependencies
Blocked by: None
Blocks: None

### Clarifications Needed
None. All decisions resolved:
- Document location: `.work/prompts-symbiosis.md` (project documentation)
- Format style: Both (graph + table fallback)
- Workflow scope: 10 workflows covering all agent-loop scenarios

### Notes
Symbiosis map should be auto-generated from prompt frontmatter (if `calls` field added). For now, maintain manually.

---

## Module Split / Plugin Architecture

This section tracks the implementation of the dot-work submodule split plan (split.md). The goal is to extract 8 submodules into standalone packages with a plugin discovery system.

**Related Issues in high.md and medium.md:**
- SPLIT-001: Plugin discovery system (high.md)
- SPLIT-002: Refactor cli.py for plugins (high.md)
- SPLIT-003: Extract dot-issues (high.md)
- SPLIT-004: Extract dot-kg (high.md)
- SPLIT-005: Extract dot-review (high.md)
- SPLIT-006: Extraction automation script (high.md)
- SPLIT-007: Update pyproject.toml (high.md)
- SPLIT-008: Extract dot-container (medium.md)
- SPLIT-009: Extract dot-git (medium.md)
- SPLIT-010: Extract dot-harness (medium.md)
- SPLIT-011: Extract dot-overview (medium.md)
- SPLIT-012: Extract dot-python (medium.md)
- SPLIT-013: Extract dot-version (medium.md)
- SPLIT-014: Integration test suite (medium.md)
- SPLIT-015: Documentation updates (medium.md)

---
id: "SPLIT-100@a1b2c3"
title: "Phase 1: Plugin infrastructure foundation"
description: "Implement plugin discovery system and refactor core CLI for plugin architecture"
created: 2026-01-02
section: "split/phase1/infrastructure"
tags: [split, phase1, infrastructure, plugins, blocking]
type: refactor
priority: critical
status: proposed
references:
  - split.md
  - .work/agent/issues/high.md:SPLIT-001
  - .work/agent/issues/high.md:SPLIT-002
  - .work/agent/issues/high.md:SPLIT-006

### Problem
Before extracting any submodules, the plugin infrastructure must be in place. Without a discovery system and CLI refactoring, extracted packages cannot be registered or used.

### Affected Files
- CREATE: `src/dot_work/plugins.py` (plugin discovery and registration)
- MODIFY: `src/dot_work/cli.py` (remove submodule imports, add plugin discovery)
- MODIFY: `pyproject.toml` (add entry-points group)
- CREATE: `scripts/extract_plugin.py` (automation script for extractions)
- CREATE: `EXPORTED_PROJECTS/` (target directory for all extracted projects)

### Importance
**CRITICAL**: This is the foundation for the entire split. All 15 SPLIT-* issues depend on this phase being completed first.

### Proposed Solution
Execute in order:
1. **SPLIT-001** (high.md): Create plugin discovery system
   - Implement `DotWorkPlugin` dataclass
   - Implement `discover_plugins()` using `importlib.metadata.entry_points()`
   - Implement `register_plugin_cli()` for Typer integration
   - Add error handling for missing/broken plugins
2. **SPLIT-002** (high.md): Refactor cli.py
   - Identify core commands to keep (install, list, detect, init, validate, canonical, prompt)
   - Remove direct imports from submodules
   - Add plugin discovery loop
   - Add `dot-work plugins` command
3. **SPLIT-006** (high.md): Create extraction automation script
   - Implement `scripts/extract_plugin.py`
   - Target all extractions to `EXPORTED_PROJECTS/` folder in project root
   - Add import rewriting logic (`dot_work.X` → `dot_X`)
   - Add pyproject.toml generation from templates
   - Add test file copying with structure preservation
   - **Add validation**: Byte-for-byte comparison of source vs copied files
   - **Add validation**: Hash verification (SHA256) for all copied Python files
   - **Add validation**: File count matching (source vs destination)

### Acceptance Criteria
- [ ] `src/dot_work/plugins.py` created with discover/register functions
- [ ] `discover_plugins()` returns empty list when no plugins installed
- [ ] `discover_plugins()` returns plugin info for installed plugins
- [ ] `register_plugin_cli()` adds Typer subcommand for plugins
- [ ] Broken/missing plugins logged as warning, don't crash CLI
- [ ] `dot-work plugins` command shows installed plugins
- [ ] cli.py reduced to <15KB (core commands only)
- [ ] All submodule imports removed from cli.py
- [ ] Core commands work without any plugins installed
- [ ] `scripts/extract_plugin.py` automates extraction with --dry-run
- [ ] `EXPORTED_PROJECTS/` folder created in project root
- [ ] **Validation**: Byte-for-byte comparison passes for all copied files
- [ ] **Validation**: SHA256 hashes match for all Python files
- [ ] **Validation**: File count matches between source and destination
- [ ] Unit tests cover discovery, registration, and error cases
- [ ] Existing tests pass (may need updates for mocking)

### Dependencies
Blocked by: None
Blocks: SPLIT-101 (Phase 2 extractions)

### Related Issues
- SPLIT-001@a1b2c3 in high.md
- SPLIT-002@b2c3d4 in high.md
- SPLIT-006@f6g7h8 in high.md

### Notes
This phase establishes the plugin infrastructure. Once complete, all extractions can proceed in parallel.

**EXPORTED_PROJECTS Folder Structure:**
```
dot-work/
├── EXPORTED_PROJECTS/
│   ├── dot-issues/
│   ├── dot-kg/
│   ├── dot-review/
│   ├── dot-container/
│   ├── dot-git/
│   ├── dot-harness/
│   ├── dot-overview/
│   ├── dot-python/
│   └── dot-version/
└── ... (existing dot-work files)
```

**Validation Approach:**
The extraction script (`scripts/extract_plugin.py`) will:
1. Calculate SHA256 hashes of all source files before copying
2. Copy files to `EXPORTED_PROJECTS/<package>/`
3. Calculate SHA256 hashes of copied files
4. Compare hashes and report any mismatches
5. Output validation report with file counts and hash verification

---
id: "SPLIT-101@b2c3d4"
title: "Phase 2A: Extract high-priority submodules (db-issues, knowledge-graph, review)"
description: "Extract the three largest submodules first to validate the extraction process"
created: 2026-01-02
section: "split/phase2/extractions"
tags: [split, phase2, extraction, high-priority, has-deps]
type: refactor
priority: high
status: proposed
references:
  - split.md
  - .work/agent/issues/high.md:SPLIT-003
  - .work/agent/issues/high.md:SPLIT-004
  - .work/agent/issues/high.md:SPLIT-005

### Problem
The high-priority submodules (db-issues, knowledge-graph, review) are the largest and most complex. Extracting them first validates the extraction process before tackling simpler modules.

### Affected Files
**Extraction targets (to `EXPORTED_PROJECTS/` folder):**
- `src/dot_work/db_issues/` → `EXPORTED_PROJECTS/dot-issues/`
- `src/dot_work/knowledge_graph/` → `EXPORTED_PROJECTS/dot-kg/`
- `src/dot_work/review/` → `EXPORTED_PROJECTS/dot-review/`

**Test migrations:**
- `tests/unit/db_issues/` → `EXPORTED_PROJECTS/dot-issues/tests/unit/`
- `tests/unit/knowledge_graph/` → `EXPORTED_PROJECTS/dot-kg/tests/unit/`
- `tests/unit/review/` → `EXPORTED_PROJECTS/dot-review/tests/unit/`
- Plus all integration tests for each module

### Importance
**HIGH**: These three extractions validate the full extraction pattern including complex dependencies, optional features, and static assets.

### Proposed Solution
Execute in order (can run in parallel after SPLIT-100):
1. **SPLIT-003** (high.md): Extract dot-issues
   - Extract to `EXPORTED_PROJECTS/dot-issues/`
   - Copy 17 unit tests + 6 integration tests
   - Add entry point for `dot_work.plugins`
   - Rewire imports: `dot_work.db_issues` → `dot_issues`
   - **Validate**: SHA256 hashes match for all copied files
   - **Validate**: File count matches (23 test files)
2. **SPLIT-004** (high.md): Extract dot-kg
   - Extract to `EXPORTED_PROJECTS/dot-kg/`
   - Copy 14 unit tests + 2 integration tests
   - Handle optional dependencies (http, ann, vec)
   - Preserve `kg` standalone command alias
   - **Validate**: SHA256 hashes match for all copied files
   - **Validate**: File count matches (16 test files)
3. **SPLIT-005** (high.md): Extract dot-review
   - Extract to `EXPORTED_PROJECTS/dot-review/`
   - Copy 9 test files (keep both sets - complementary coverage)
   - Handle static assets (JS/CSS) and Jinja2 templates
   - Verify assets included in wheel build
   - **Validate**: SHA256 hashes match for all copied files
   - **Validate**: Static assets (JS/CSS) present and identical
   - **Validate**: Templates directory structure preserved

### Acceptance Criteria
**dot-issues:**
- [ ] Extracted to `EXPORTED_PROJECTS/dot-issues/`
- [ ] Repository created with correct structure
- [ ] All 17 unit tests pass in new package
- [ ] All 6 integration tests pass in new package
- [ ] `pip install dot-issues` works
- [ ] `dot-work db-issues` works when plugin installed
- [ ] **Validation**: SHA256 hashes match for all Python files
- [ ] **Validation**: File count = 23 test files

**dot-kg:**
- [ ] Extracted to `EXPORTED_PROJECTS/dot-kg/`
- [ ] Repository created with correct structure
- [ ] All 14 unit tests pass
- [ ] All 2 integration tests pass
- [ ] `kg` command works standalone
- [ ] Optional dependencies work (http, ann, vec)
- [ ] **Validation**: SHA256 hashes match for all Python files
- [ ] **Validation**: File count = 16 test files

**dot-review:**
- [ ] Extracted to `EXPORTED_PROJECTS/dot-review/`
- [ ] Repository created with correct structure
- [ ] All 9 test files pass
- [ ] Static assets included in wheel package
- [ ] Templates included in wheel package
- [ ] Review UI loads in browser with CSS/JS
- [ ] **Validation**: SHA256 hashes match for all Python files
- [ ] **Validation**: Static assets (JS/CSS) identical to source
- [ ] **Validation**: Templates directory structure preserved

### Dependencies
Blocked by: SPLIT-100 (plugin infrastructure)
Blocks: SPLIT-102 (medium-priority extractions), SPLIT-103 (integration)

### Related Issues
- SPLIT-003@c3d4e5 in high.md
- SPLIT-004@d4e5f6 in high.md
- SPLIT-005@e5f6g7 in high.md

### Notes
These are the "pilot extractions" - they will reveal any issues in the extraction automation script (SPLIT-006).

**EXPORTED_PROJECTS Structure (after SPLIT-101):**
```
dot-work/
├── EXPORTED_PROJECTS/
│   ├── dot-issues/
│   ├── dot-kg/
│   └── dot-review/
└── ... (existing dot-work files)
```

---
id: "SPLIT-102@c3d4e5"
title: "Phase 2B: Extract medium-priority submodules (container, git, harness, overview, python, version)"
description: "Extract the remaining six submodules after validating the extraction process"
created: 2026-01-02
section: "split/phase2/extractions"
tags: [split, phase2, extraction, medium-priority, has-deps]
type: refactor
priority: medium
status: proposed
references:
  - split.md
  - .work/agent/issues/medium.md:SPLIT-008
  - .work/agent/issues/medium.md:SPLIT-009
  - .work/agent/issues/medium.md:SPLIT-010
  - .work/agent/issues/medium.md:SPLIT-011
  - .work/agent/issues/medium.md:SPLIT-012
  - .work/agent/issues/medium.md:SPLIT-013

### Problem
After validating the extraction process with the high-priority submodules, extract the remaining six medium-priority submodules.

### Affected Files
**Extraction targets (to `EXPORTED_PROJECTS/` folder):**
- `src/dot_work/container/` → `EXPORTED_PROJECTS/dot-container/`
- `src/dot_work/git/` → `EXPORTED_PROJECTS/dot-git/`
- `src/dot_work/harness/` → `EXPORTED_PROJECTS/dot-harness/`
- `src/dot_work/overview/` → `EXPORTED_PROJECTS/dot-overview/`
- `src/dot_work/python/` → `EXPORTED_PROJECTS/dot-python/`
- `src/dot_work/version/` → `EXPORTED_PROJECTS/dot-version/`

### Importance
**MEDIUM**: These extractions complete the module split. Can proceed in parallel after SPLIT-101 validates the process.

### Proposed Solution
Execute in parallel (after SPLIT-101 completes):
1. **SPLIT-008** (medium.md): Extract dot-container
   - Extract to `EXPORTED_PROJECTS/dot-container/`
   - Active development coordination (FEAT-027, FEAT-028)
   - **Validate**: SHA256 hashes match for all copied files
2. **SPLIT-009** (medium.md): Extract dot-git
   - Extract to `EXPORTED_PROJECTS/dot-git/`
   - Handle LLM optional dependencies
   - **Validate**: SHA256 hashes match for all copied files
3. **SPLIT-010** (medium.md): Extract dot-harness
   - Extract to `EXPORTED_PROJECTS/dot-harness/`
   - Smallest submodule (2 test files)
   - **Validate**: SHA256 hashes match for all copied files
4. **SPLIT-011** (medium.md): Extract dot-overview
   - Extract to `EXPORTED_PROJECTS/dot-overview/`
   - Isolate libcst dependency (~50MB)
   - **Validate**: SHA256 hashes match for all copied files
5. **SPLIT-012** (medium.md): Extract dot-python
   - Extract to `EXPORTED_PROJECTS/dot-python/`
   - Preserve `pybuilder` alias
   - **Validate**: SHA256 hashes match for all copied files
6. **SPLIT-013** (medium.md): Extract dot-version
   - Extract to `EXPORTED_PROJECTS/dot-version/`
   - Handle LLM optional dep for changelog
   - **Validate**: SHA256 hashes match for all copied files

### Acceptance Criteria
- [ ] All 6 repositories created in `EXPORTED_PROJECTS/`
- [ ] All unit tests pass in each new package
- [ ] All integration tests pass in each new package
- [ ] Each package works standalone
- [ ] Each package registers as plugin correctly
- [ ] Optional dependencies work where applicable
- [ ] **Validation**: SHA256 hashes match for all copied files across all 6 packages
- [ ] **Validation**: File counts match between source and destination
- [ ] **Validation**: Validation report generated with no mismatches

### Dependencies
Blocked by: SPLIT-100, SPLIT-101 (validation of extraction process)
Blocks: SPLIT-103 (integration), SPLIT-104 (final packaging)

### Related Issues
- SPLIT-008@h8i9j0 in medium.md
- SPLIT-009@i9j0k1 in medium.md
- SPLIT-010@j0k1l2 in medium.md
- SPLIT-011@k1l2m3 in medium.md
- SPLIT-012@l2m3n4 in medium.md
- SPLIT-013@m3n4o5 in medium.md

### Notes
Coordinate with container module active development (FEAT-027, FEAT-028 in shortlist).

**Final EXPORTED_PROJECTS Structure (after SPLIT-102):**
```
dot-work/
├── EXPORTED_PROJECTS/
│   ├── dot-issues/        (from SPLIT-101)
│   ├── dot-kg/            (from SPLIT-101)
│   ├── dot-review/        (from SPLIT-101)
│   ├── dot-container/     (from SPLIT-102)
│   ├── dot-git/           (from SPLIT-102)
│   ├── dot-harness/       (from SPLIT-102)
│   ├── dot-overview/      (from SPLIT-102)
│   ├── dot-python/        (from SPLIT-102)
│   └── dot-version/       (from SPLIT-102)
└── ... (existing dot-work files)
```

**Validation Report:**
After each extraction, the script generates `EXPORTED_PROJECTS/validation-report.md` containing:
- Package name and version
- Source file paths and hashes
- Destination file paths and hashes
- File count comparison
- List of any mismatches (should be empty)

---
id: "SPLIT-103@d4e5f6"
title: "Phase 3: Integration testing and core package updates"
description: "Create integration tests and update core dot-work package for plugin architecture"
created: 2026-01-02
section: "split/phase3/integration"
tags: [split, phase3, integration, testing, has-deps]
type: test
priority: high
status: proposed
references:
  - split.md
  - .work/agent/issues/high.md:SPLIT-007
  - .work/agent/issues/medium.md:SPLIT-014

### Problem
After all extractions, need to verify the plugin ecosystem works correctly and update the core package dependencies.

### Affected Files
- CREATE: `tests/integration/test_plugin_ecosystem.py`
- MODIFY: `pyproject.toml` (remove submodule deps, add optional plugin groups)
- MODIFY: `src/dot_work/cli.py` (final cleanup)

### Importance
**HIGH**: Critical for release confidence. Verifies that the split maintains backward compatibility.

### Proposed Solution
Execute in order:
1. **SPLIT-014** (medium.md): Create integration test suite
   - Test core CLI with no plugins installed
   - Test plugin discovery with mocked plugins
   - Test graceful degradation
   - Test full ecosystem with all plugins
2. **SPLIT-007** (high.md): Update pyproject.toml
   - Reduce base dependencies to 5 packages
   - Add all 9 plugins as optional deps
   - Add `dot-work[all]` convenience group
   - Verify wheel size reduced by >50%

### Acceptance Criteria
- [ ] Integration tests pass for core without plugins
- [ ] Integration tests pass for plugin discovery
- [ ] Integration tests pass for plugin CLI registration
- [ ] Integration tests pass for mixed plugin scenarios
- [ ] Base dependencies reduced to 5 packages
- [ ] All 9 plugins available as optional deps
- [ ] `pip install dot-work` installs minimal package
- [ ] `pip install dot-work[all]` installs everything
- [ ] Wheel size reduced by >50%

### Dependencies
Blocked by: SPLIT-101, SPLIT-102 (all extractions complete)
Blocks: SPLIT-104 (documentation and release)

### Related Issues
- SPLIT-007@g7h8i9 in high.md
- SPLIT-014@n4o5p6 in medium.md

### Notes
Run full test suite in CI before proceeding to documentation.

---
id: "SPLIT-104@e5f6g7"
title: "Phase 4: Documentation updates and release preparation"
description: "Update all documentation and prepare for release of split packages"
created: 2026-01-02
section: "split/phase4/documentation"
tags: [split, phase4, documentation, release]
type: docs
priority: medium
status: proposed
references:
  - split.md
  - .work/agent/issues/medium.md:SPLIT-015
  - README.md

### Problem
After splitting, documentation must explain the new plugin installation patterns and migration path for existing users.

### Affected Files
- MODIFY: `README.md` (installation section)
- CREATE: `docs/plugins.md` (plugin documentation)
- CREATE: `docs/migration-to-plugins.md` (migration guide)
- CREATE: Each extracted package README.md

### Importance
**MEDIUM**: Documentation is essential for adoption but can be done near end.

### Proposed Solution
1. **SPLIT-015** (medium.md): Update main dot-work documentation
   - Update README.md installation section
   - Create docs/plugins.md
   - Create migration guide for existing users
2. **Create package READMEs**: Each extracted package needs:
   - Description and purpose
   - Installation instructions
   - Usage examples
   - Link to main dot-work repo

### Acceptance Criteria
- [ ] README.md reflects plugin architecture
- [ ] Installation examples for all patterns (core, all, selective)
- [ ] docs/plugins.md created with all plugins documented
- [ ] Migration guide created for existing users
- [ ] All doc links work (link check passes)
- [ ] Each extracted package has README.md

### Dependencies
Blocked by: SPLIT-103 (integration complete)
Blocks: None (this is the final step)

### Related Issues
- SPLIT-015@o5p6q7 in medium.md

### Notes
After this phase, all packages are ready for release to PyPI.

---
