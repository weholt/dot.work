# Backlog: Orchestration & Autonomy

Prompts and infrastructure for autonomous agent operation.

Issues: FEAT-029, FEAT-030, FEAT-031, FEAT-032, FEAT-033, FEAT-034
Split from: backlog.md
Created: 2026-01-01

---
id: "FEAT-029@j6k2l8"
title: "Create agent-loop orchestrator prompt for infinite autonomous operation"
description: "Add dedicated orchestrator prompt that manages the full agent-loop.md cycle with state persistence and recovery"
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
---

### Problem
The current `agent-loop.md` is a **human-readable document**, not a **machine-optimized orchestration prompt**. Issues:

1. **Not a prompt**: agent-loop.md describes the loop but isn't structured for autonomous execution
2. **State loss**: No mechanism for persisting loop state across session boundaries
3. **No recovery**: If agent fails mid-loop, no resume mechanism
4. **Manual decisions**: Step 10 says "If ANYTHING at all to do without human intervention - go to step 1" but agents can't evaluate this
5. **Unclear exit**: "AGENT DONE" is undefined behavior
6. **Token inefficiency**: do-work.md is 1256 lines but includes examples not needed every iteration

**Critical gap for infinite agent harness:**
- No state machine definition
- No checkpoint mechanism
- No error recovery strategy
- No resource limit awareness

### Affected Files
- NEW: `src/dot_work/prompts/orchestrator.md` (main orchestrator)
- NEW: `src/dot_work/prompts/orchestrator-state.md` (state schema)
- MODIFIED: `agent-loop.md` (reference orchestrator)
- MODIFIED: `src/dot_work/prompts/do-work.md` (extract minimal iteration logic)

### Importance
**CRITICAL**: This enables:
- True infinite agent operation without human intervention
- Session-resilient autonomous workflows
- Crash recovery and state restoration
- Resource-aware operation (token/time limits)
- Clear termination conditions and reporting

### Proposed Solution

**1. Orchestrator State Schema (.work/agent/orchestrator-state.yaml)**
```yaml
version: "1.0"
session_id: "uuid"
started: "ISO8601"
last_checkpoint: "ISO8601"

loop_state:
  current_phase: baseline | select | investigate | implement | validate | complete | learn | housekeeping
  iteration_count: 42
  issues_completed_this_session: 5
  
current_work:
  issue_id: "BUG-003@a9f3c2"
  phase: implement
  progress:
    - investigation: completed
    - implementation: in_progress (60%)
    - validation: pending

resource_tracking:
  tokens_used_estimate: 150000
  time_elapsed_minutes: 45
  issues_since_baseline: 3

exit_conditions:
  no_actionable_issues: false
  resource_limit_reached: false
  human_intervention_needed: false
  critical_error: null

checkpoints:
  - timestamp: "ISO8601"
    phase: investigate
    issue_id: "BUG-003"
    snapshot: "checkpoint-001.json"
```

**2. Orchestrator Prompt Structure**

```markdown
# Agent Orchestrator

## Role
You are the Loop Controller responsible for:
1. Managing iteration state
2. Checkpointing progress
3. Recovering from failures
4. Enforcing exit conditions
5. Delegating to specialized prompts

## State Management
- Read state from .work/agent/orchestrator-state.yaml
- Update state after each phase transition
- Create checkpoints at configurable intervals

## Recovery Protocol
On session start:
1. Check for existing state file
2. If found, verify integrity
3. Resume from last checkpoint
4. If corrupted, attempt last-known-good

## Exit Conditions (MANDATORY CHECK)
Before each iteration:
- Token budget remaining?
- Time limit reached?
- No actionable issues AND clean build?
- Critical error requiring human?

## Phase Delegation
| Phase | Delegate To |
|-------|-------------|
| baseline | baseline.md mode:establish |
| select | (inline logic) |
| investigate | (inline logic) |
| implement | (inline logic) |
| validate | baseline.md mode:compare + unified-review.md |
| complete | (inline logic) |
| learn | (inline logic) |
| housekeeping | housekeeping.md |
```

**3. Minimal Iteration Extraction from do-work.md**
Extract ~200 lines of core iteration logic into `iteration-core.md`, removing:
- Examples (move to examples.md)
- ASCII diagrams
- Detailed explanations (reference docs)

### Acceptance Criteria
- [ ] orchestrator-state.yaml schema defined
- [ ] Orchestrator prompt handles all loop phases
- [ ] State persisted after each phase transition
- [ ] Recovery from last checkpoint works
- [ ] Exit conditions evaluated each iteration
- [ ] Resource tracking (tokens, time) implemented
- [ ] Clean integration with do-work.md
- [ ] agent-loop.md updated to reference orchestrator
- [ ] Test: simulate session crash and recovery

### Notes
- Consider YAML vs JSON for state (YAML more human-readable for debugging)
- Checkpoint frequency configurable (every phase vs every N issues)
- Exit condition "no actionable issues" must check ALL issue files
- Resource limits should be configurable via environment or config

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
---

### Problem
Agent-loop.md assumes environment is ready, but autonomous operation can fail due to:

1. **Missing prerequisites**:
   - .work/ structure not initialized
   - No baseline exists
   - Build system broken
   - Tests failing before work starts

2. **Configuration issues**:
   - Missing API keys for LLM features
   - Incorrect paths in config
   - Memory.md missing project context

3. **State corruption**:
   - Orphaned issues in wrong state
   - focus.md inconsistent with issue files
   - Baseline stale or missing

4. **Resource constraints**:
   - Insufficient disk space
   - Rate limits on APIs

**Current gap**: Agent discovers these mid-loop, wasting tokens and creating confusing error states.

### Affected Files
- NEW: `src/dot_work/prompts/pre-flight.md`
- MODIFIED: `agent-loop.md` (add step 0: pre-flight)

### Importance
**HIGH**: Pre-flight checks:
- Fail fast before wasting tokens
- Provide clear remediation steps
- Ensure reproducible starting state
- Required for reliable infinite operation

### Proposed Solution

**Pre-flight Check Categories:**

```markdown
# Pre-Flight Checklist

## 1. Structure Validation
- [ ] .work/ directory exists
- [ ] All required issue files exist
- [ ] focus.md has valid structure
- [ ] memory.md exists and readable

## 2. Build System
- [ ] Build command runs without error
- [ ] All tests pass
- [ ] No lint errors (warnings OK)
- [ ] Type checking passes

## 3. Baseline Status
- [ ] baseline.md exists
- [ ] baseline.md age < threshold (configurable)
- [ ] Baseline matches current commit

## 4. Issue State Consistency
- [ ] No completed issues in active files
- [ ] focus.md.current matches issue status
- [ ] No duplicate issue IDs
- [ ] All references resolve

## 5. Configuration
- [ ] Project context in memory.md
- [ ] Build commands documented
- [ ] Test commands documented

## 6. Resources (if autonomous)
- [ ] Token budget configured
- [ ] Time limit configured
- [ ] API keys available (if needed)
```

**Output:**
```yaml
pre_flight:
  status: ready | blocked | needs_action
  blockers:
    - category: build
      issue: "Tests failing (3 failures)"
      remediation: "Fix failing tests before autonomous operation"
  warnings:
    - category: baseline
      issue: "Baseline 3 days old"
      remediation: "Consider regenerating baseline"
  ready_at: "ISO8601"
```

### Acceptance Criteria
- [ ] Pre-flight prompt covers all 6 categories
- [ ] Clear pass/fail for each check
- [ ] Remediation steps for all failures
- [ ] Output format parseable
- [ ] Integration with orchestrator
- [ ] Can auto-fix some issues (init structure, move completed)

### Notes
- Some checks can auto-remediate (housekeeping before starting)
- Consider `--fix` mode that attempts auto-remediation
- Baseline age threshold should be configurable

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
---

### Problem
When errors occur during autonomous operation, agents have no systematic recovery process:

1. **Build failures**: Agent may loop trying same fix
2. **Test failures**: No strategy for isolating cause
3. **Validation failures**: May create duplicate issues
4. **State corruption**: No recovery mechanism
5. **Resource exhaustion**: No graceful degradation

**Current behavior**: Errors create issues and continue, potentially cascading failures.

### Affected Files
- NEW: `src/dot_work/prompts/error-recovery.md`
- MODIFIED: `src/dot_work/prompts/do-work.md` (reference recovery prompt)

### Importance
**HIGH**: Error recovery enables:
- Autonomous operation without human intervention on recoverable errors
- Reduced cascading failures
- Clear escalation path for unrecoverable errors
- Session continuity despite issues

### Proposed Solution

**Error Classification:**
```yaml
error_types:
  recoverable:
    - build_failure
    - test_failure
    - validation_regression
    - lint_error
    - type_error
  
  needs_context:
    - ambiguous_error
    - dependency_failure
    - configuration_issue
  
  unrecoverable:
    - critical_data_loss
    - security_breach_detected
    - infinite_loop_detected
    - state_corruption
```

**Recovery Strategies:**
```markdown
## Build Failure Recovery
1. Parse error message
2. Identify affected file(s)
3. Check if recently modified (our change)
4. If our change: revert and create issue
5. If not our change: create issue, mark blocked

## Test Failure Recovery
1. Identify failing test(s)
2. Check if new tests (we added)
3. If new test fails: review test logic
4. If existing test fails: regression, create issue
5. Isolate: run single test to confirm

## Infinite Loop Detection
- Track: same error > 3 times in N minutes
- Action: checkpoint state, create meta-issue, STOP
```

### Acceptance Criteria
- [ ] Error classification schema
- [ ] Recovery strategy for each recoverable type
- [ ] Escalation path for unrecoverable
- [ ] Integration with orchestrator
- [ ] Loop detection mechanism
- [ ] State checkpoint before risky recovery

### Notes
- Consider "confidence score" for recovery attempts
- Max recovery attempts configurable
- Recovery actions should be logged for debugging

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
---

### Problem
`do-work.md` defines the iteration loop but implementation phase is vague:

```markdown
### Phase 4: IMPLEMENT
Actions:
  1. Update focus.md phase to "Implementation"
  2. Make code changes as planned
  3. Add/update tests as needed
  ...
```

**Issues:**
- "Make code changes as planned" is not deterministic
- No structured approach to transforming issue into code
- Agents may interpret issues differently
- No verification that implementation matches issue intent

**Gap**: Issues are well-specified (via issue-readiness.md) but translation to code is undefined.

### Affected Files
- NEW: `src/dot_work/prompts/implement.md`
- MODIFIED: `src/dot_work/prompts/do-work.md` (reference implement.md)

### Importance
**HIGH**: Deterministic implementation:
- Reduces variation in agent behavior
- Ensures issue acceptance criteria are met
- Provides traceability from issue to code
- Enables validation against original intent

### Proposed Solution

**Implementation Protocol:**

```markdown
# Implementation Protocol

## Input
- Issue with acceptance criteria
- Investigation notes
- Baseline state of affected files

## Step 1: Decompose into atomic changes
For each acceptance criterion:
1. Identify required code change
2. Identify required test change
3. Identify required doc change
4. Map to specific file:line

## Step 2: Sequence changes
Order changes to maintain working state:
- Dependencies first
- Tests before implementation (TDD optional)
- Docs last

## Step 3: For each atomic change
1. State the change in plain language
2. Identify the exact location
3. Write the minimal diff
4. Verify no unintended effects

## Step 4: Trace to acceptance criteria
| Criterion | Change | File:Line | Test |
|-----------|--------|-----------|------|
| AC-1 | Add validation | src/x.py:45 | test_x.py:23 |

## Step 5: Checkpoint
After each atomic change:
- Run relevant tests
- Check lint
- Update progress in focus.md
```

### Acceptance Criteria
- [ ] Implementation decomposition protocol
- [ ] Change sequencing rules
- [ ] Traceability matrix template
- [ ] Checkpoint requirements
- [ ] Integration with do-work.md

### Notes
- Consider TDD mode where tests written first
- Atomic changes enable easier rollback
- Traceability enables spec-delivery-auditor validation

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
---

### Problem
Current approach loads full prompts regardless of:
- Available context window
- Specific task requirements
- Already-known information

**Token waste examples:**
- `do-work.md` (1256 lines) loaded every iteration
- Examples in prompts not needed after first use
- ASCII diagrams repeated unnecessarily
- Schema definitions duplicated across prompts

### Affected Files
- ALL prompts in src/dot_work/prompts/
- NEW: `src/dot_work/prompts/manifest.yaml` (prompt metadata)

### Importance
**MEDIUM**: Token optimization:
- Extends effective context window
- Reduces cost
- Enables more complex operations
- Supports smaller models

### Proposed Solution

**1. Prompt Manifest:**
```yaml
# manifest.yaml
prompts:
  do-work:
    full_path: do-work.md
    tokens: ~3000
    sections:
      core: [philosophy, checklist, loop-diagram]
      examples: [transcript-1, transcript-2]
      reference: [baseline-content, focus-template]
    
    loading_strategy:
      first_iteration: full
      subsequent: core_only
      on_error: core + relevant_reference
```

**2. Section Markers in Prompts:**
```markdown
<!-- @section:core -->
## 🎯 Workflow Philosophy
...
<!-- @end:core -->

<!-- @section:examples -->
## 🎬 Example: Complete Iteration Transcript
...
<!-- @end:examples -->
```

**3. Loader Logic:**
```python
def load_prompt(name: str, context: LoadContext) -> str:
    manifest = load_manifest()
    prompt_meta = manifest.prompts[name]
    
    if context.first_iteration:
        return load_full(prompt_meta.full_path)
    elif context.error_recovery:
        return load_sections(prompt_meta, ['core', 'reference'])
    else:
        return load_sections(prompt_meta, ['core'])
```

### Acceptance Criteria
- [ ] Prompt manifest with section metadata
- [ ] Section markers in prompts
- [ ] Progressive loader implementation
- [ ] Token savings >40% for subsequent iterations
- [ ] Examples loadable on-demand

### Notes
- Start with do-work.md (biggest savings)
- Consider caching computed prompts
- Section markers should be invisible in normal rendering

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
---

### Problem
`agent-prompts-reference.md` lists prompts but doesn't explain:
- Which prompts work together
- Optimal ordering for combined use
- Input/output compatibility
- When to use compositions vs single prompts

**Missing guidance:**
- Can spec-delivery-auditor use baseline for comparison?
- Does critical-code-review output feed into issue-readiness?
- What's the optimal review sequence?

### Affected Files
- MODIFIED: `src/dot_work/prompts/agent-prompts-reference.md`
- NEW: `src/dot_work/prompts/symbiosis-map.md`

### Importance
**MEDIUM**: Symbiosis documentation:
- Enables effective prompt composition
- Reduces trial-and-error
- Improves autonomous decision-making
- Documents architectural intent

### Proposed Solution

**Symbiosis Map Structure:**

```markdown
# Prompt Symbiosis Map

## Workflow Compositions

### Code Review + Issue Creation
```
unified-review.md mode:critical
    ↓ (findings)
new-issue.md
    ↓ (issues)
issue-readiness.md
```

### Full Validation Pipeline
```
baseline.md mode:compare
    + unified-review.md mode:full
    + spec-delivery-auditor.md
    ↓ (all findings merged)
new-issue.md (if failures)
```

## Input/Output Compatibility Matrix

| Producer | Output | Consumer | Input Match |
|----------|--------|----------|-------------|
| unified-review | findings | new-issue | ✓ direct |
| baseline:compare | regressions | new-issue | ✓ direct |
| spec-delivery | gaps | new-issue | ✓ direct |
| issue-readiness | refined issues | do-work | ✓ direct |

## Anti-Patterns
- Don't run all 4 reviews separately (use unified mode:full)
- Don't establish baseline after changes (defeats purpose)
```

### Acceptance Criteria
- [ ] Workflow compositions documented
- [ ] Input/output compatibility matrix
- [ ] Anti-patterns listed
- [ ] Integration with agent-prompts-reference.md
- [ ] Mermaid diagrams for visual workflows

### Notes
- This documents the intended architecture
- Should be updated when prompts change
- Consider auto-generating from prompt metadata
