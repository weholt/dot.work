# Loop Optimization Plan for Autonomous Agents

**Version:** 0.1.0  
**Created:** 2025-01-05  
**Status:** Proposed

---

## Executive Summary

This plan optimizes the autonomous agent loop for long-running operations without human intervention. The core strategy is **context window optimization through specialization**: decompose the monolithic orchestrator into focused subagents, each with minimal context and specific skills.

Key principles from [Anthropic's research](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) and the [Ralph Wiggum technique](https://www.atcyrus.com/stories/ralph-wiggum-technique-claude-code-autonomous-loops):

1. **Incremental progress** — One issue at a time, leave clean state
2. **State persistence** — Resume seamlessly across context windows
3. **Clear success criteria** — Objective completion markers
4. **Stop hooks** — Automated loop continuation decisions
5. **Specialized agents** — Different prompts for different phases

---

## Problem Statement

### Current Issues

1. **Bloated context window**: The orchestrator loads all prompts (do-work.md, critical-code-review.md, etc.) into a single context, wasting tokens on irrelevant instructions
2. **Language/platform coupling**: Prompts contain Python/Unix-specific assumptions
3. **Serial validation**: Code review, security audit, performance review run sequentially
4. **No stop hook integration**: Manual loop detection vs. Claude Code's native stop hooks
5. **Constitution not generated**: create-constitution.md exists but doesn't produce project-specific rules
6. **Skill underutilization**: Skills exist but aren't integrated into the workflow

### Impact

- **Token waste**: ~40-60% of context is irrelevant per phase
- **Slower iterations**: Sequential validation adds latency
- **Platform friction**: Unix-specific paths, Python-specific commands
- **Lost learnings**: No project-specific constitution captures accumulated decisions

---

## Proposed Architecture

### Phase-Based Subagent Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AUTONOMOUS LOOP PHASES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────┐                                                      │
│   │  INITIALIZATION  │  One-time setup (constitution, baseline)             │
│   └────────┬─────────┘                                                      │
│            │                                                                 │
│            ▼                                                                 │
│   ┌──────────────────┐     Skills:                                          │
│   │  PRE-ITERATION   │  • issue-management                                  │
│   │    Subagent      │  • focus-selector                                    │
│   └────────┬─────────┘                                                      │
│            │  Produces: focus.md, prepared-context.json                     │
│            ▼                                                                 │
│   ┌──────────────────┐     Skills:                                          │
│   │  IMPLEMENTATION  │  • test-driven-development                           │
│   │    Subagent      │  • debugging                                         │
│   └────────┬─────────┘  • code-review (self-review)                         │
│            │  Produces: code changes, tests, commit                          │
│            ▼                                                                 │
│   ┌──────────────────────────────────────────────────────┐                  │
│   │              VALIDATION (Parallel Subagents)          │                  │
│   ├──────────────┬──────────────┬──────────────┬─────────┤                  │
│   │ code-review  │ security-    │ performance- │ spec-   │                  │
│   │ subagent     │ auditor      │ reviewer     │ auditor │                  │
│   └──────────────┴──────────────┴──────────────┴─────────┘                  │
│            │  Produces: issues (if any)                                      │
│            ▼                                                                 │
│   ┌──────────────────┐                                                      │
│   │  LOOP EVALUATOR  │  Stop hook integration                               │
│   │    Subagent      │  Decides: continue | done | blocked                  │
│   └────────┬─────────┘                                                      │
│            │                                                                 │
│       ┌────┴────┐                                                            │
│       │         │                                                            │
│   CONTINUE   DONE/BLOCKED                                                    │
│       │         │                                                            │
│       └─► PRE-ITERATION                                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Context Window Optimization

| Phase | Context Size | Contains |
|-------|--------------|----------|
| Pre-Iteration | ~3K tokens | Issue files, focus.md, issue-management skill |
| Implementation | ~8K tokens | Current issue, constitution, relevant skills, affected files only |
| Validation (each) | ~4K tokens | Changed files only, single review focus |
| Loop Evaluator | ~2K tokens | State summary, issue counts, completion criteria |

**Estimated savings**: 50-70% token reduction per iteration

---

## Detailed Issue Breakdown

### Phase 1: Foundation (Prerequisites)

---

#### ISSUE: OPT-001 — Platform-Agnostic Constitution Generator

**Priority:** Critical  
**Type:** Enhancement  
**Estimated Effort:** Medium

**Problem:**
- `create-constitution.md` describes what to generate but doesn't actually create `.work/constitution.md`
- No project-specific language/platform detection
- Constitution is conceptual, not operational

**Proposed Solution:**

1. Update `create-constitution.md` to:
   - Detect project language(s) from: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `*.csproj`, etc.
   - Detect platform from: CI configs, Dockerfiles, build scripts
   - Generate `.work/constitution.md` with platform-specific rules

2. Constitution structure:
   ```markdown
   # Project Constitution
   Generated: YYYY-MM-DD | Project: <name> | Version: <semver>
   
   ## 1. Project Identity
   - Languages: [Python 3.11+, TypeScript 5.x]
   - Platforms: [Linux, macOS, Windows]
   - Package Manager: uv | npm | cargo
   - Build System: pybuilder | vite | cargo
   
   ## 2. Build Contract
   - Build command: `<detected>`
   - Test command: `<detected>`
   - Lint command: `<detected>`
   - Type check command: `<detected>`
   
   ## 3. Quality Gates
   - Coverage threshold: X%
   - Allowed lint warnings: N
   - Required checks: [list]
   
   ## 4. Invariants
   - [Project-specific rules discovered during work]
   - [User-stated preferences from memory.md]
   
   ## 5. Agent Constraints
   - Memory limit: <detected or default>
   - Timeout per issue: <configurable>
   - Max files per commit: <configurable>
   ```

3. Make constitution the single source of truth for:
   - Build/test/lint commands (no hardcoded `uv run pytest`)
   - Platform-specific path handling
   - Quality thresholds

**Acceptance Criteria:**
- [ ] Constitution generated from project files
- [ ] Multiple language detection works
- [ ] Commands are platform-agnostic (use constitution values)
- [ ] Constitution regenerates on `init work` or explicit request

**Files to Create/Modify:**
- `src/dot_work/assets/prompts/create-constitution.md` (major update)
- `src/dot_work/assets/prompts/establish-baseline.md` (read constitution)
- `src/dot_work/assets/prompts/do-work.md` (read constitution for commands)

---

#### ISSUE: OPT-002 — Stop Hook Integration for Claude Code

**Priority:** High  
**Type:** Enhancement  
**Estimated Effort:** Medium

**Problem:**
- Current loop detection is manual (check issue files, count cycles)
- No integration with Claude Code's native stop hooks
- Can't use Ralph Wiggum-style completion promises

**Proposed Solution:**

1. Create `.claude/hooks/` directory structure:
   ```
   .claude/
     hooks/
       pre-loop.sh       # Pre-iteration setup
       post-iteration.sh  # After each issue
       stop-hook.sh       # Loop continuation decision
   ```

2. Define completion promise protocol:
   ```markdown
   ## Completion Promises
   
   The agent outputs these markers for stop hook detection:
   
   - `<promise>ISSUE_COMPLETE</promise>` — Current issue finished
   - `<promise>LOOP_CONTINUE</promise>` — More issues to process
   - `<promise>LOOP_DONE</promise>` — All issues complete
   - `<promise>LOOP_BLOCKED</promise>` — Requires human intervention
   ```

3. Stop hook script checks:
   - Issue files for remaining work
   - State file for cycle count
   - Error log for blocking issues

**Acceptance Criteria:**
- [ ] Stop hooks directory created
- [ ] Completion promise markers defined in orchestrator
- [ ] Hooks work with Claude Code's `/ralph-loop` style invocation
- [ ] Graceful fallback for non-Claude Code environments

**Files to Create:**
- `src/dot_work/assets/hooks/stop-hook.md` (hook logic)
- `src/dot_work/assets/prompts/agent-orchestrator.md` (add promises)

---

### Phase 2: Subagent Decomposition

---

#### ISSUE: OPT-003 — Pre-Iteration Subagent

**Priority:** High  
**Type:** Enhancement  
**Estimated Effort:** Medium

**Problem:**
- Issue management logic is embedded in `do-work.md`
- Focus selection uses full orchestrator context
- No prepared context for implementation phase

**Proposed Solution:**

1. Create `subagents/pre-iteration.md`:
   ```markdown
   # Pre-Iteration Subagent
   
   ## Role
   Prepare the next iteration with minimal context.
   
   ## Inputs
   - Issue files (shortlist.md, critical.md, high.md, medium.md, low.md)
   - focus.md (current state)
   - memory.md (relevant entries only)
   
   ## Outputs
   - Updated focus.md (previous/current/next)
   - prepared-context.json (minimal context for implementation)
   
   ## Skills Used
   - issue-management
   - focus-selector
   ```

2. Create `skills/issue-management/SKILL.md`:
   - Moving completed issues to history
   - Scanning for proposed issues
   - Priority ordering logic
   - Deduplication

3. Create `skills/focus-selector/SKILL.md`:
   - Shortlist-first priority
   - Context continuity (prefer related issues)
   - Blocked issue detection

4. Output `prepared-context.json`:
   ```json
   {
     "issue": {
       "id": "BUG-003@a9f3c2",
       "title": "...",
       "affected_files": ["src/config.py"],
       "acceptance_criteria": ["..."]
     },
     "constitution_extract": {
       "language": "python",
       "build_cmd": "uv run python scripts/build.py",
       "test_cmd": "./scripts/pytest-with-cgroup.sh"
     },
     "memory_relevant": [
       "Use pathlib for cross-platform paths"
     ],
     "baseline_for_files": {
       "src/config.py": {"coverage": "92%", "lint_warnings": 3}
     }
   }
   ```

**Acceptance Criteria:**
- [ ] Pre-iteration subagent created
- [ ] issue-management skill created
- [ ] focus-selector skill created
- [ ] prepared-context.json format defined
- [ ] Integration with orchestrator

**Files to Create:**
- `src/dot_work/assets/subagents/pre-iteration.md`
- `src/dot_work/assets/skills/issue-management/SKILL.md`
- `src/dot_work/assets/skills/focus-selector/SKILL.md`

---

#### ISSUE: OPT-004 — Implementation Subagent

**Priority:** High  
**Type:** Enhancement  
**Estimated Effort:** Medium

**Problem:**
- Implementation phase loads entire `do-work.md` (massive prompt)
- No skill composition for implementation
- Context includes irrelevant validation logic

**Proposed Solution:**

1. Create `subagents/implementer.md`:
   ```markdown
   # Implementation Subagent
   
   ## Role
   Implement a single issue with focused context.
   
   ## Inputs
   - prepared-context.json (from pre-iteration)
   - Affected files only (not entire codebase)
   - constitution.md (build/test commands)
   
   ## Skills Used (compose based on issue type)
   - test-driven-development (for all)
   - debugging (for bugs)
   - code-review (self-review before commit)
   
   ## Outputs
   - Code changes
   - Test changes
   - Git commit
   - implementation-report.json
   ```

2. Skill composition logic:
   ```yaml
   issue_type_skills:
     bug:
       - debugging
       - test-driven-development
     feature:
       - test-driven-development
     refactor:
       - code-review
       - test-driven-development
     security:
       - security-auditor (self-check)
       - test-driven-development
   ```

3. Implementation report for validation phase:
   ```json
   {
     "issue_id": "BUG-003@a9f3c2",
     "files_changed": ["src/config.py", "tests/test_config.py"],
     "tests_added": 2,
     "commit_sha": "abc1234",
     "self_review_passed": true
   }
   ```

**Acceptance Criteria:**
- [ ] Implementer subagent created
- [ ] Skill composition based on issue type
- [ ] Minimal context loading
- [ ] Implementation report generated

**Files to Create:**
- `src/dot_work/assets/subagents/implementer.md`

---

#### ISSUE: OPT-005 — Parallel Validation Subagents

**Priority:** High  
**Type:** Enhancement  
**Estimated Effort:** Medium

**Problem:**
- Validation runs sequentially (code-review → security → performance → spec)
- Each validation loads full context
- Duplicate file reading

**Proposed Solution:**

1. Update existing validation subagents for parallel execution:
   - `subagents/code-reviewer.md` (exists, update for parallel)
   - `subagents/security-auditor.md` (exists, update for parallel)
   - Create `subagents/performance-reviewer.md`
   - Create `subagents/spec-auditor.md`

2. Parallel execution model:
   ```markdown
   ## Validation Orchestration
   
   After implementation:
   1. Read implementation-report.json
   2. Spawn parallel subagents (each gets only changed files):
      - code-reviewer: focuses on quality, abstractions
      - security-auditor: focuses on vulnerabilities
      - performance-reviewer: focuses on complexity, efficiency
      - spec-auditor: focuses on requirement coverage
   3. Collect findings from all
   4. Create issues for all findings (new-issue.md format)
   5. Aggregate into validation-report.json
   ```

3. Each subagent output format:
   ```json
   {
     "subagent": "security-auditor",
     "findings": [
       {
         "severity": "high",
         "file": "src/config.py",
         "line": 45,
         "issue": "Potential path traversal",
         "recommendation": "Validate path is within allowed directory"
       }
     ],
     "passed": false
   }
   ```

**Acceptance Criteria:**
- [ ] All four validation subagents ready for parallel execution
- [ ] Each receives only changed files
- [ ] Findings auto-create issues
- [ ] Validation report aggregates results

**Files to Create/Modify:**
- `src/dot_work/assets/subagents/performance-reviewer.md` (new)
- `src/dot_work/assets/subagents/spec-auditor.md` (new)
- `src/dot_work/assets/subagents/code-reviewer.md` (update)
- `src/dot_work/assets/subagents/security-auditor.md` (update)

---

#### ISSUE: OPT-006 — Loop Evaluator Subagent

**Priority:** High  
**Type:** Enhancement  
**Estimated Effort:** Small

**Problem:**
- Loop continuation logic is embedded in orchestrator
- No single point of decision for stop hooks
- Infinite loop detection is cycle-based, not progress-based

**Proposed Solution:**

1. Create `subagents/loop-evaluator.md`:
   ```markdown
   # Loop Evaluator Subagent
   
   ## Role
   Decide whether the loop should continue, stop, or is blocked.
   
   ## Inputs
   - validation-report.json
   - Issue file counts (proposed, in-progress, blocked)
   - Cycle count and progress metrics
   - Error log summary
   
   ## Decision Logic
   
   ### LOOP_DONE conditions (all must be true):
   - No proposed issues in any file
   - No issues created by validation
   - Build passes without warnings
   - All quality gates met
   
   ### LOOP_BLOCKED conditions (any):
   - Issue requires human input (tagged: needs-input)
   - 3+ cycles with same issue failing
   - Critical security finding
   - Unrecoverable error
   
   ### LOOP_CONTINUE (default):
   - Proposed issues exist
   - Validation created new issues
   - Work remains
   
   ## Output
   - Decision: DONE | CONTINUE | BLOCKED
   - Completion promise marker
   - State update for orchestrator
   ```

2. Integrate with stop hooks:
   ```bash
   # stop-hook.sh reads evaluator output
   if grep -q "LOOP_DONE" /tmp/evaluator-decision.txt; then
     exit 0  # Stop the loop
   fi
   # Re-inject prompt for next iteration
   ```

**Acceptance Criteria:**
- [ ] Loop evaluator subagent created
- [ ] Clear decision criteria
- [ ] Outputs completion promise markers
- [ ] Integrates with stop hooks

**Files to Create:**
- `src/dot_work/assets/subagents/loop-evaluator.md`

---

### Phase 3: Workflow Refactoring

---

#### ISSUE: OPT-007 — Refactor do-work.md for Subagent Architecture

**Priority:** Critical  
**Type:** Refactor  
**Estimated Effort:** Large

**Problem:**
- `do-work.md` is 600+ lines containing all workflow logic
- Mixes orchestration with implementation details
- Not designed for subagent delegation

**Proposed Solution:**

1. Split `do-work.md` into:
   - `do-work.md` — Orchestration overview only (~100 lines)
   - `subagents/pre-iteration.md` — Issue selection (extracted)
   - `subagents/implementer.md` — Implementation (extracted)
   - `skills/*` — Reusable patterns (extracted)

2. New `do-work.md` structure:
   ```markdown
   # Do Work — Orchestration Overview
   
   ## Workflow
   1. Invoke pre-iteration subagent
   2. Invoke implementer subagent with prepared context
   3. Invoke validation subagents (parallel)
   4. Invoke loop-evaluator subagent
   5. Process evaluator decision
   
   ## State Files
   - prepared-context.json
   - implementation-report.json
   - validation-report.json
   - evaluator-decision.json
   
   ## Subagent Invocation
   (How to call each subagent with minimal context)
   ```

3. Extract to skills:
   - Baseline comparison logic → `skills/baseline-validation/SKILL.md`
   - Git operations → `skills/git-workflow/SKILL.md`
   - Issue creation → `skills/issue-creation/SKILL.md`

**Acceptance Criteria:**
- [ ] do-work.md reduced to <150 lines
- [ ] All implementation logic in implementer subagent
- [ ] All issue management in pre-iteration subagent
- [ ] Skills extracted and reusable
- [ ] No functionality regression

**Files to Modify:**
- `src/dot_work/assets/prompts/do-work.md` (major refactor)

---

#### ISSUE: OPT-008 — Refactor agent-orchestrator.md for New Architecture

**Priority:** Critical  
**Type:** Refactor  
**Estimated Effort:** Medium

**Problem:**
- Orchestrator embeds step logic instead of delegating
- No subagent invocation patterns
- State schema doesn't support new workflow

**Proposed Solution:**

1. Update orchestrator to invoke subagents:
   ```markdown
   ## Orchestrator Flow
   
   ### Step 1: Pre-Iteration
   Invoke: subagents/pre-iteration.md
   Input: issue files, focus.md
   Output: prepared-context.json
   
   ### Step 2: Implementation
   Invoke: subagents/implementer.md
   Input: prepared-context.json, constitution.md
   Output: implementation-report.json
   
   ### Step 3: Validation (Parallel)
   Invoke: subagents/code-reviewer.md, security-auditor.md, 
           performance-reviewer.md, spec-auditor.md
   Input: implementation-report.json, changed files
   Output: validation-report.json
   
   ### Step 4: Evaluation
   Invoke: subagents/loop-evaluator.md
   Input: validation-report.json, issue counts, state
   Output: decision + completion promise
   ```

2. Update state schema:
   ```json
   {
     "phase": "implementation",
     "subagent": "implementer",
     "current_issue": "BUG-003@a9f3c2",
     "prepared_context_hash": "abc123",
     "cycles": 2,
     "issues_completed_this_session": ["BUG-001", "BUG-002"],
     "last_decision": "CONTINUE"
   }
   ```

3. Add completion promises to output:
   ```markdown
   After each step, output appropriate promise:
   - After implementation: <promise>ISSUE_COMPLETE</promise>
   - After evaluation (continue): <promise>LOOP_CONTINUE</promise>
   - After evaluation (done): <promise>LOOP_DONE</promise>
   ```

**Acceptance Criteria:**
- [ ] Orchestrator delegates to subagents
- [ ] State schema updated
- [ ] Completion promises integrated
- [ ] Resume from any phase

**Files to Modify:**
- `src/dot_work/assets/prompts/agent-orchestrator.md`

---

### Phase 4: New Skills

---

#### ISSUE: OPT-009 — Create Baseline Validation Skill

**Priority:** Medium  
**Type:** Enhancement  
**Estimated Effort:** Small

**Problem:**
- Baseline comparison logic is duplicated in multiple prompts
- File-level regression tracking is complex
- Not reusable across subagents

**Proposed Solution:**

Create `skills/baseline-validation/SKILL.md`:
```markdown
# Baseline Validation Skill

## Purpose
Compare current state against baseline at file level.

## Capabilities
- Read baseline.md and parse file metrics
- Compare current lint/type/coverage per file
- Identify regressions vs. pre-existing issues
- Generate regression report

## Usage
When validating changes, use this skill to:
1. Load baseline for affected files
2. Run validation commands (from constitution)
3. Compare results
4. Report: new issues, regressions, improvements
```

**Acceptance Criteria:**
- [ ] Skill created
- [ ] Integrated with implementer subagent
- [ ] Integrated with validation subagents

**Files to Create:**
- `src/dot_work/assets/skills/baseline-validation/SKILL.md`

---

#### ISSUE: OPT-010 — Create Git Workflow Skill

**Priority:** Medium  
**Type:** Enhancement  
**Estimated Effort:** Small

**Problem:**
- Git operations scattered across prompts
- No consistent commit message format
- Branch handling varies

**Proposed Solution:**

Create `skills/git-workflow/SKILL.md`:
```markdown
# Git Workflow Skill

## Purpose
Consistent git operations across all subagents.

## Capabilities
- Commit with conventional format: type(scope): description
- Branch management (create, switch, merge)
- Stash handling for context switches
- Log reading for context recovery

## Commit Format
<type>(<scope>): <description>

type: fix | feat | refactor | test | docs | chore
scope: issue ID or area
description: imperative, <50 chars
```

**Acceptance Criteria:**
- [ ] Skill created
- [ ] Commit format standardized
- [ ] Integrated with implementer

**Files to Create:**
- `src/dot_work/assets/skills/git-workflow/SKILL.md`

---

#### ISSUE: OPT-011 — Create Issue Creation Skill

**Priority:** Medium  
**Type:** Enhancement  
**Estimated Effort:** Small

**Problem:**
- `new-issue.md` is a full prompt, not a skill
- Validation subagents need to create issues inline
- Duplication of issue schema knowledge

**Proposed Solution:**

Create `skills/issue-creation/SKILL.md`:
```markdown
# Issue Creation Skill

## Purpose
Create properly formatted issues from any subagent.

## Capabilities
- Generate unique IDs (TYPE-NUM@HASH)
- Determine correct priority file
- Format with full schema
- Deduplicate against existing issues

## Quick Issue Format
For validation findings, create minimal issues:
- ID, title, description, affected file, acceptance criteria
- Skip verbose sections if finding is straightforward
```

**Acceptance Criteria:**
- [ ] Skill created
- [ ] Used by validation subagents
- [ ] Maintains compatibility with new-issue.md format

**Files to Create:**
- `src/dot_work/assets/skills/issue-creation/SKILL.md`

---

### Phase 5: Platform Agnosticism

---

#### ISSUE: OPT-012 — Remove Hardcoded Commands from Prompts

**Priority:** High  
**Type:** Refactor  
**Estimated Effort:** Medium

**Problem:**
- Prompts contain hardcoded `uv run pytest`, `./scripts/pytest-with-cgroup.sh`
- Path separators assume Unix (`/`)
- Python-specific assumptions throughout

**Proposed Solution:**

1. All commands reference constitution:
   ```markdown
   ## Before (hardcoded)
   Run: `uv run python scripts/build.py`
   
   ## After (constitution reference)
   Run: `${constitution.build_cmd}`
   
   Or in prose:
   "Run the build command defined in .work/constitution.md"
   ```

2. Replace path hardcoding:
   ```markdown
   ## Before
   Check `.work/agent/issues/critical.md`
   
   ## After  
   Check the critical issues file (path from constitution)
   ```

3. Language-agnostic phrasing:
   ```markdown
   ## Before
   "Add pytest fixtures for..."
   
   ## After
   "Add test fixtures using the project's test framework..."
   ```

**Acceptance Criteria:**
- [ ] No hardcoded shell commands in prompts
- [ ] All paths use constitution or platform-agnostic references
- [ ] Language-specific terms replaced with generic equivalents

**Files to Modify:**
- `src/dot_work/assets/prompts/*.md` (audit all)

---

#### ISSUE: OPT-013 — Create Language Detection Module

**Priority:** Medium  
**Type:** Enhancement  
**Estimated Effort:** Medium

**Problem:**
- Constitution generator needs to detect project language/platform
- No existing detection logic
- Multiple languages per project possible

**Proposed Solution:**

1. Detection markers:
   ```yaml
   python:
     files: [pyproject.toml, setup.py, requirements.txt, Pipfile]
     indicators: ["*.py"]
   
   javascript:
     files: [package.json, yarn.lock, pnpm-lock.yaml]
     indicators: ["*.js", "*.ts", "*.jsx", "*.tsx"]
   
   rust:
     files: [Cargo.toml]
     indicators: ["*.rs"]
   
   go:
     files: [go.mod, go.sum]
     indicators: ["*.go"]
   
   csharp:
     files: ["*.csproj", "*.sln"]
     indicators: ["*.cs"]
   ```

2. Build system detection:
   ```yaml
   python:
     pyproject.toml (hatch): "hatch build"
     pyproject.toml (setuptools): "pip install -e ."
     pyproject.toml (uv): "uv run python -m build"
   
   javascript:
     package.json: "npm run build" or scripts.build
   ```

3. Output to constitution with detected values

**Acceptance Criteria:**
- [ ] Multi-language detection works
- [ ] Build commands auto-detected
- [ ] Test commands auto-detected
- [ ] Constitution populated correctly

**Files to Create:**
- `src/dot_work/assets/prompts/detect-project.md` (or in constitution generator)

---

### Phase 6: Documentation & Integration

---

#### ISSUE: OPT-014 — Update AGENTS.md for New Architecture

**Priority:** Medium  
**Type:** Documentation  
**Estimated Effort:** Small

**Problem:**
- AGENTS.md documents old monolithic workflow
- No subagent invocation guidance
- No skill usage patterns

**Proposed Solution:**

Update AGENTS.md with:
1. Subagent invocation patterns
2. Skill composition examples
3. Context window optimization notes
4. Stop hook usage

**Acceptance Criteria:**
- [ ] AGENTS.md updated
- [ ] Examples for each subagent
- [ ] Skill usage documented

---

#### ISSUE: OPT-015 — Create Subagent Invocation Guide

**Priority:** Medium  
**Type:** Documentation  
**Estimated Effort:** Small

**Problem:**
- No documentation on how to invoke subagents
- Environment-specific patterns (Claude vs OpenCode vs Copilot)
- Skill composition not documented

**Proposed Solution:**

Create `docs/subagent-guide.md`:
```markdown
# Subagent Invocation Guide

## Claude Code
Use Task tool or direct @agent mention

## OpenCode
Use subagent mode configuration

## Copilot
Use .github/agents/ directory

## Skill Composition
Load skills based on issue type...
```

**Acceptance Criteria:**
- [ ] Guide created
- [ ] Environment-specific examples
- [ ] Skill composition documented

---

## Implementation Order

### Critical Path (Blocks Everything)
1. **OPT-001**: Constitution generator (foundation)
2. **OPT-007**: Refactor do-work.md (enables subagents)
3. **OPT-008**: Refactor orchestrator (enables subagents)

### Parallel Track A (Subagents)
4. **OPT-003**: Pre-iteration subagent
5. **OPT-004**: Implementation subagent
6. **OPT-005**: Validation subagents (parallel)
7. **OPT-006**: Loop evaluator

### Parallel Track B (Skills)
8. **OPT-009**: Baseline validation skill
9. **OPT-010**: Git workflow skill
10. **OPT-011**: Issue creation skill

### Parallel Track C (Platform)
11. **OPT-002**: Stop hook integration
12. **OPT-012**: Remove hardcoded commands
13. **OPT-013**: Language detection

### Final (Documentation)
14. **OPT-014**: Update AGENTS.md
15. **OPT-015**: Subagent invocation guide

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Context tokens per iteration | ~15K | ~5K |
| Validation latency | Sequential (4x) | Parallel (1x) |
| Platform support | Python/Unix | Any/Any |
| Issue completion rate | Manual tracking | Automated metrics |
| Loop continuation accuracy | Cycle-based | Progress-based |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Subagent coordination failures | Medium | High | State files + resume logic |
| Skill not loaded correctly | Low | Medium | Explicit skill references |
| Parallel validation race conditions | Low | Low | Independent file outputs |
| Constitution misdetects project | Medium | Medium | Manual override option |
| Stop hooks break on non-Claude | High | Low | Graceful fallback |

---

## Appendix: File Mapping

### New Files to Create
```
src/dot_work/assets/
  subagents/
    pre-iteration.md
    implementer.md
    loop-evaluator.md
    performance-reviewer.md
    spec-auditor.md
  skills/
    issue-management/SKILL.md
    focus-selector/SKILL.md
    baseline-validation/SKILL.md
    git-workflow/SKILL.md
    issue-creation/SKILL.md
  hooks/
    stop-hook.md
  prompts/
    detect-project.md (or merged into constitution)
```

### Files to Modify
```
src/dot_work/assets/
  prompts/
    create-constitution.md (major)
    do-work.md (major)
    agent-orchestrator.md (major)
    establish-baseline.md (minor)
    *.md (audit for hardcoded commands)
  subagents/
    code-reviewer.md (minor)
    security-auditor.md (minor)
```

---

## Next Steps

1. Review this plan with stakeholders
2. Convert issues to `.work/agent/issues/` format
3. Prioritize based on dependencies
4. Begin implementation with OPT-001 (constitution)
