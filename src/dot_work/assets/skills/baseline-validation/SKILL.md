---
name: baseline-validation
description: Skill for validating code changes against the established baseline
license: MIT
compatibility: Works with all AI coding assistants

environments:
  claude:
    target: ".claude/skills/"
    filename_suffix: "/baseline-validation/SKILL.md"
---

# Baseline Validation Skill

You have expertise in validating that code changes do not regress the established baseline. This includes test count, coverage, linting, type checking, and build integrity.

---

## Baseline File Location

The baseline is stored in `.work/baseline.md` with this structure:

```markdown
# Project Baseline

## Tests
- Total: 156
- Passed: 156
- Failed: 0
- Skipped: 2

## Coverage
- Line coverage: 78.5%
- Branch coverage: 72.1%

## Linting
- Errors: 0
- Warnings: 3

## Type Checking
- Errors: 0

## Build
- Status: success
- Duration: 12.3s

---
Captured: 2026-01-05T10:00:00Z
Command: uv run python scripts/build.py
```

---

## Validation Checks

### 1. Test Count Validation

```yaml
check: test_count
rule: current.tests.total >= baseline.tests.total
severity: error

failure_message: |
  Test count regression detected.
  Baseline: {baseline.tests.total} tests
  Current: {current.tests.total} tests
  Missing: {difference} tests
  
  This indicates tests were deleted. All tests must be preserved.
```

### 2. Test Pass Rate

```yaml
check: test_pass_rate
rule: current.tests.failed == 0
severity: error

failure_message: |
  Tests are failing.
  Failed: {current.tests.failed}
  
  All tests must pass before completion.
```

### 3. Coverage Validation

```yaml
check: coverage
rule: current.coverage.line >= baseline.coverage.line - 1.0
tolerance: 1.0%  # Allow 1% variance for edge cases
severity: warning (if < 2% drop), error (if >= 2% drop)

failure_message: |
  Coverage regression detected.
  Baseline: {baseline.coverage.line}%
  Current: {current.coverage.line}%
  Drop: {difference}%
  
  Add tests to maintain coverage.
```

### 4. Lint Check

```yaml
check: lint
rule: current.lint.errors == 0
severity: error

failure_message: |
  Lint errors detected.
  Errors: {current.lint.errors}
  
  Fix all lint errors before completion.
```

### 5. Type Check

```yaml
check: type_check
rule: current.type_check.errors <= baseline.type_check.errors
severity: error

failure_message: |
  Type checking regression.
  Baseline errors: {baseline.type_check.errors}
  Current errors: {current.type_check.errors}
  New errors: {difference}
  
  Fix type errors introduced by changes.
```

### 6. Build Success

```yaml
check: build
rule: current.build.status == "success"
severity: error

failure_message: |
  Build failed.
  Status: {current.build.status}
  
  Build must succeed before completion.
```

---

## Validation Workflow

### Step 1: Load Baseline

```yaml
steps:
  1. Read .work/baseline.md
  2. Parse YAML sections
  3. Extract metrics
  4. If baseline missing:
     - STOP with error
     - "Baseline not established. Run establish-baseline first."
```

### Step 2: Run Verification Command

```yaml
steps:
  1. Read constitution for commands
  2. Execute build/test command
  3. Capture output
  4. Parse metrics from output
```

### Step 3: Compare Metrics

```yaml
comparison_order:
  1. build (must succeed first)
  2. test_count (no test deletion)
  3. test_pass_rate (all must pass)
  4. type_check (no new errors)
  5. lint (no errors)
  6. coverage (minimal regression)
```

### Step 4: Generate Report

```yaml
report_format:
  validation_result: pass | fail | warn
  
  checks:
    - name: build
      status: pass
      details: "Build succeeded in 12.5s"
      
    - name: test_count
      status: pass
      details: "158 tests (baseline: 156, +2 new)"
      
    - name: coverage
      status: warn
      details: "77.8% (baseline: 78.5%, -0.7%)"
      recommendation: "Coverage dropped slightly. Consider adding tests."
  
  summary:
    passed: 5
    failed: 0
    warnings: 1
    
  recommendation: |
    Validation passed with warnings.
    Consider addressing: coverage
```

---

## Quick Validation Mode

For rapid feedback during implementation:

```yaml
quick_mode:
  skip:
    - Full coverage calculation
    - Lint warnings (only errors)
  run:
    - Build
    - Tests (fail-fast)
    - Type check
    
  use_case: "After each file save during implementation"
  duration_target: "<30 seconds"
```

---

## Full Validation Mode

For completion verification:

```yaml
full_mode:
  run:
    - Complete build
    - All tests with coverage
    - Full type check
    - Complete lint check
    - Coverage report generation
    
  use_case: "Before marking issue complete"
  duration_target: "~2-5 minutes"
```

---

## Baseline Metrics Extraction

### From pytest output:

```python
# Pattern matching for pytest output
patterns = {
    "total": r"(\d+) passed",
    "failed": r"(\d+) failed",
    "skipped": r"(\d+) skipped",
    "coverage": r"TOTAL\s+\d+\s+\d+\s+(\d+)%"
}
```

### From mypy output:

```python
# Pattern matching for mypy output
patterns = {
    "errors": r"Found (\d+) errors?",
    "success": r"Success: no issues found"
}
```

### From ruff output:

```python
# Pattern matching for ruff output
patterns = {
    "errors": r"Found (\d+) errors?",
    "warnings": r"Found (\d+) warnings?"
}
```

---

## Validation Report File

Output to `.work/agent/validation-report.json`:

```json
{
  "timestamp": "2026-01-05T10:35:00Z",
  "iteration": 5,
  "issue_id": "BUG-003@a9f3c2",
  
  "baseline": {
    "tests_total": 156,
    "coverage_line": 78.5,
    "lint_errors": 0,
    "type_errors": 0
  },
  
  "current": {
    "tests_total": 158,
    "tests_passed": 158,
    "tests_failed": 0,
    "coverage_line": 77.8,
    "lint_errors": 0,
    "type_errors": 0
  },
  
  "checks": [
    {"name": "build", "status": "pass"},
    {"name": "test_count", "status": "pass"},
    {"name": "test_pass_rate", "status": "pass"},
    {"name": "type_check", "status": "pass"},
    {"name": "lint", "status": "pass"},
    {"name": "coverage", "status": "warn", "delta": -0.7}
  ],
  
  "result": "pass",
  "warnings": ["coverage"],
  "errors": []
}
```

---

## Integration Points

### With Implementer Subagent

```yaml
implementer_integration:
  - Implementer runs quick validation after changes
  - If quick validation fails, implementer fixes immediately
  - Full validation run by validation subagent after implementation
```

### With Loop Evaluator

```yaml
evaluator_integration:
  - Loop evaluator checks validation_report.json
  - If validation.result == "fail": issue not complete
  - If validation.result == "warn": complete but note warnings
  - If validation.result == "pass": fully complete
```

---

## Baseline Update Rules

When baseline should be updated:

```yaml
update_conditions:
  - After adding new tests (test count increases)
  - After improving coverage (coverage increases)
  - After fixing type errors (error count decreases)
  
update_forbidden:
  - After removing tests (NEVER update to hide deletion)
  - After introducing failures
  - After coverage regression
  
update_command: "establish-baseline (from constitution)"
```

---

## Error Recovery

### Missing Baseline

```yaml
error: baseline_missing
action:
  - Report error to orchestrator
  - Recommend: "Run establish-baseline before starting work"
  - Block implementation until baseline exists
```

### Baseline Parse Error

```yaml
error: baseline_parse_error
action:
  - Report specific parse error
  - Show expected format
  - Recommend: "Regenerate baseline with establish-baseline"
```

### Validation Command Failure

```yaml
error: command_failure
action:
  - Capture stderr
  - Report command that failed
  - Do NOT mark as validation pass
  - Let implementer see error and fix
```

---

## See Also

**Related Prompts:** `establish-baseline`

**Used By:** `loop-evaluator`, `implementer` subagents

