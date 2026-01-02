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
