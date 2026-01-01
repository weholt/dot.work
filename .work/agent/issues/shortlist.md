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
All previous shortlist items (ENH-025, ENH-026, REFACTOR-003, TEST-041, TEST-042, TEST-043, FEAT-023, FEAT-024, FEAT-025) have been completed and moved to history.md.
---
id: "FEAT-026@d0e6f2"
title: "Context and file injection for Dockerized OpenCode containers"
description: "Add support for injecting additional context, files, documentation, and configuration into OpenCode containers at runtime or build time"
created: 2025-12-30
section: "container/docker/context"
tags: [feature, docker, containerization, opencode, context-injection, volumes, configuration, has-deps]
type: enhancement
priority: medium
status: proposed
references:
  - .work/agent/issues/shortlist.md:FEAT-025@c9d5e1
  - README.md
  - src/dot_work/container/provision/core.py

### Problem
OpenCode containers need project-specific context (docs, configs, code samples) to be effective. Manual copy into containers is tedious; automatic injection improves UX.

### Affected Files
- Modify: `src/dot_work/container/provision/core.py` (add context injection logic)
- Modify: `src/dot_work/container/provision/cli.py` (add `--context` and `--override` options)
- Create: `src/dot_work/container/provision/context.py` (context resolution and mounting)

### Importance
Medium priority. Improves container UX but not blocking for basic functionality. Builds on FEAT-025.

### Proposed Solution
1. **Context Specification**: Support `--context <path>` for files/directories to inject
2. **Mount Point Strategy**: Mount to `/root/.context/` inside container
3. **Configuration Auto-detection**: Configurable allowlist/denylist with defaults:
   - Default allowlist: `.claude/`, `.opencode.json`, GitHub Copilot CLI configs
   - Configured via `.env` file: `CONTEXT_ALLOWLIST` and `CONTEXT_DENYLIST`
4. **Conflict Handling**: User flag `--override` to control behavior
   - Default: Skip mount if target exists (preserve defaults)
   - With `--override`: Always mount over (shadow container defaults)
5. **Build-time Context**: Build custom images with `docker build` before provisioning
   - Use `--build-context <path>` to trigger custom image build
   - Generates Dockerfile on-the-fly with COPY instructions

### Acceptance Criteria
- [ ] CLI `--context` flag mounts files/directories into container
- [ ] Auto-detection finds and mounts `.claude/`, `.opencode.json`, Copilot configs
- [ ] Allowlist/denylist configurable via `.env` file
- [ ] `--override` flag forces mount over existing files
- [ ] Build-time context via `--build-context` creates custom image
- [ ] Integration tests verify mounted files accessible in container
- [ ] Documentation shows usage examples

### Validation Plan
```bash
# Runtime context injection
uv run dot-work container provision --context README.md --context .claude/

# With override
uv run dot-work container provision --context .claude/ --override

# Build-time context
uv run dot-work container provision --build-context ./custom-context/

# Verify mount inside container
docker exec <container-id> ls -la /root/.context/
docker exec <container-id> cat /root/.context/README.md
```

### Dependencies
Blocked by: FEAT-025@c9d5e1 (Docker provisioning foundation)
Blocks: FEAT-027 (remote URL injection)

### Clarifications Needed
None. All decisions resolved:
- Auto-detection: Configurable allowlist/denylist with `.claude`, `.opencode`, Copilot CLI defaults
- Conflict handling: `--override` flag controls behavior
- Build-time: Custom images via `docker build` before provisioning

### Notes
Context injection complements FEAT-027 (remote URLs). Unified `--context` API handles both local paths and URLs.

---
id: "FEAT-027@e1f7g3"
title: "Runtime URL-based context injection for OpenCode containers"
description: "Add support for injecting context files, directories, and archives from remote URLs into running containers"
created: 2025-12-30
section: "container/docker/context"
tags: [feature, docker, containerization, opencode, context-injection, urls, remote-content, has-deps]
type: enhancement
priority: medium
status: proposed
references:
  - .work/agent/issues/shortlist.md:FEAT-026@d0e6f2
  - README.md
  - src/dot_work/container/provision/core.py

### Problem
Users need to fetch remote context (docs, examples, configs) and inject into containers without manual download. URLs may point to files or archives.

### Affected Files
- Create: `src/dot_work/container/provision/fetch.py` (URL fetching and extraction)
- Modify: `src/dot_work/container/provision/core.py` (integrate fetch into mount logic)
- Modify: `src/dot_work/container/provision/cli.py` (add `--url` and `--url-token` options)

### Importance
Medium priority. Convenience feature for remote resources. Builds on FEAT-026 context injection.

### Proposed Solution
1. **URL Fetching**: Support HTTP/HTTPS URLs for files and archives
2. **Archive Support**: `.zip` format only (extract to `/root/.context/<name>/`)
3. **Security**: Validate URL scheme (HTTPS only, reject http://, file://)
4. **Caching**: ETag/Last-Modified support for HTTP conditional GET
   - Cache directory: `~/.cache/dot-work/context/`
5. **Authentication**: Bearer token via `--url-token` flag or `URL_TOKEN` env var
6. **Error Handling**: Fail fast on network errors, invalid URLs, or size limits (max 100MB)

### Acceptance Criteria
- [ ] CLI `--url` flag fetches and injects remote files
- [ ] `.zip` archives auto-extracted to context directory
- [ ] HTTPS-only enforcement (reject http://, file://)
- [ ] ETag/Last-Modified support for conditional GET (cache validation)
- [ ] Bearer token auth via `--url-token` or env var
- [ ] Size limit enforced (100MB max) with clear error message
- [ ] Integration tests with mock HTTP server

### Validation Plan
```bash
# Fetch and inject single file with auth
uv run dot-work container provision --url https://example.com/config.json --url-token $TOKEN

# Fetch and extract archive
uv run dot-work container provision --url https://example.com/context.zip

# Verify inside container
docker exec <container-id> ls -la /root/.context/
```

### Dependencies
Blocked by: FEAT-026@d0e6f2 (local context injection)
Blocks: None

### Clarifications Needed
None. All decisions resolved:
- Archive support: `.zip` only
- Cache policy: ETag/Last-Modified support (HTTP conditional GET)
- Authentication: Bearer token via `--url-token` or env var

### Notes
Consider using `requests` library with streaming for large files. Add `requests` to dependencies if not present.

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
id: "FEAT-029@j6k2l8"
title: "Create agent-loop orchestrator prompt for infinite autonomous operation"
description: "Add dedicated orchestrator prompt that manages full agent-loop.md cycle with state persistence and recovery"
created: 2025-12-30
section: "prompts/orchestration"
tags: [feature, prompts, agent-loop, orchestration, autonomy, state-machine]
type: enhancement
priority: critical
status: proposed
references:
  - agent-loop.md
  - src/dot_work/prompts/do-work.md
  - src/dot_work/prompts/housekeeping.md

### Problem
Current agent-loop.md requires manual execution of each step. Autonomous agents need a single orchestrator prompt that can run the full cycle indefinitely with state persistence across interruptions.

### Affected Files
- Create: `src/dot_work/prompts/agent-orchestrator.md`
- Modify: `agent-loop.md` (add reference to orchestrator)
- Create: `tests/integration/prompts/test_orchestrator.py`

### Importance
Critical. Enables true autonomous operation. Without this, agents cannot self-manage the full issue lifecycle.

### Proposed Solution
Create agent-orchestrator.md prompt that:
1. Follows agent-loop.md steps (move completed issues, establish baseline, work on issues, validate)
2. Persists minimal state to `.work/agent/orchestrator-state.json` after each step
   - Schema: `{"step": 5, "last_issue": "FEAT-025", "cycles": 1}`
3. Resumes from last step on restart (reads state file)
4. Detects infinite loops (no progress after 3 cycles with no completed issues)
5. Handles interruption gracefully (finally block writes state)
6. Loop termination: Stop when all issues completed OR stop after N cycles (configurable via `--max-cycles` flag)
7. Error recovery: Configurable with fail-fast as default
   - Default: Abort on error (fail-fast)
   - With `--resilient` flag: Skip failed step, continue to next

### Acceptance Criteria
- [ ] Orchestrator executes all agent-loop.md steps sequentially
- [ ] State file saves minimal schema: step, last_issue, cycles
- [ ] Resume from step after interruption
- [ ] Infinite loop detection (abort after 3 cycles with no completed issues)
- [ ] `--max-cycles N` flag limits execution to N cycles
- [ ] `--resilient` flag enables skip-and-continue on errors
- [ ] Integration test simulates interruption and recovery
- [ ] Documentation in agent-loop.md references orchestrator

### Validation Plan
```bash
# Integration test with simulated interruption
uv run pytest tests/integration/prompts/test_orchestrator.py::test_interruption_recovery -v

# Manual smoke test (short run)
# Start agent, kill mid-cycle, restart, verify resume

# Test cycle limit
uv run dot-work agent-orchestrator --max-cycles 1
```

### Dependencies
Blocked by: None
Blocks: FEAT-030, FEAT-031 (depend on orchestrator)

### Clarifications Needed
None. All decisions resolved:
- State schema: Minimal (step, last_issue, cycles)
- Loop termination: Stop when all issues completed OR configurable `--max-cycles`
- Error recovery: Fail-fast default, `--resilient` flag for skip-and-continue

### Notes
Orchestrator should call existing prompts (do-work.md, housekeeping.md, etc.) via slash commands or include their content inline.

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
