# Regression Prevention System - Usage Guide

## Overview

The Regression Prevention System breaks changes into atomic subtasks and validates each incrementally to prevent regressions.

## Quick Start

### 1. Start a New Task

```bash
uv run python scripts/prevent_regressions.py start "Add new feature X"
```

This will:
- Generate a task ID (e.g., `task-20251125-120000`)
- Decompose your task into atomic subtasks
- Capture baseline system state
- Create a task manifest with test requirements

### 2. Review the Task Manifest

```bash
uv run python scripts/prevent_regressions.py status task-20251125-120000
```

This shows:
- All subtasks that need to be completed
- Test requirements for each subtask
- Current completion status

### 3. Implement Each Subtask

Work through subtasks one at a time:

```bash
# Edit files for subtask-1-create
# Write new tests as required

# Validate your changes
uv run python scripts/prevent_regressions.py validate subtask-1-create

# If validation passes, move to next subtask
# If validation fails, fix issues and re-validate
```

### 4. Finalize the Task

After all subtasks are validated:

```bash
uv run python scripts/prevent_regressions.py finalize task-20251125-120000
```

This runs:
- Full unit test suite
- Build validation (formatting, linting, type checking)
- Generates final validation report

## Detailed Workflow

### Task Decomposition

The system breaks tasks into phases:

1. **Planning** - Analyze approach and identify affected files
2. **Creation** - Add new files/functions (if needed)
3. **Modification** - Change existing code (if needed)
4. **Testing** - Add/update tests
5. **Documentation** - Update docs
6. **Integration** - Validate system-wide integration

Each subtask includes:
- Clear description
- Dependency list
- Files affected
- Required tests
- Risk assessment (low/medium/high)

### Validation Levels

Each subtask validation checks:

1. **Baseline Tests** - All existing tests still pass
2. **New Tests** - Required tests exist and pass
3. **Coverage** - Code coverage doesn't decrease
4. **Risk Assessment** - High-risk changes require extra scrutiny

### Task Directory Structure

```
.work/tasks/task-20251125-120000/
  manifest.json           # Task decomposition
  baseline.json           # Pre-change system state
  subtask-1-create/
    validation.json       # Validation results
    report.md            # Human-readable report
  subtask-2-modify/
    validation.json
    report.md
  integration/
    validation.json
  final_report.md        # Summary of all validations
```

## Commands Reference

### start - Start New Task

```bash
uv run python scripts/prevent_regressions.py start "Task description"
```

Creates new task with decomposition and baseline capture.

### validate - Validate Subtask

```bash
# Auto-detect task ID
uv run python scripts/prevent_regressions.py validate subtask-1-create

# Explicit task ID
uv run python scripts/prevent_regressions.py validate subtask-1-create --task-id task-20251125-120000
```

Runs validation for specific subtask.

### finalize - Complete Task

```bash
uv run python scripts/prevent_regressions.py finalize task-20251125-120000
```

Runs full integration validation.

### status - Show Task Status

```bash
uv run python scripts/prevent_regressions.py status task-20251125-120000
```

Shows progress and completion status.

### list - List All Tasks

```bash
uv run python scripts/prevent_regressions.py list
```

Lists all tasks in the system.

## Validation Reports

### Subtask Validation Report

Each validated subtask generates a report showing:

- ✅/❌ Overall status
- Baseline regression check results
- New test validation results
- Coverage change (+/- percentage)
- Risk assessment
- Files affected
- Next steps

Example:

```markdown
# Validation Report: subtask-1-create

## Status: ✅ PASSED

## Subtask Description
Create new files/functions

## Validation Results

### Baseline Regression Tests
- Status: ✅ PASSED
- Message: All baseline tests passed

### New Tests
- Status: ✅ PASSED
- Message: New tests validated

### Coverage Change
- Baseline: 72.50%
- Current: 73.20%
- Change: +0.70%

## Risk Assessment: MEDIUM

## Next Steps
- ✅ Proceed to next subtask
- Run integration tests after all subtasks complete
```

### Final Integration Report

The final report includes:

- Overall task status
- Unit test results
- Build validation results
- Subtask completion checklist
- Baseline comparison
- Next steps (commit, PR, etc.)

## Best Practices

### 1. Keep Subtasks Atomic

Each subtask should:
- Do ONE thing
- Be independently testable
- Have clear success criteria
- Take < 1 hour to implement

### 2. Validate Frequently

Run validation after every subtask:
- Catches regressions early
- Provides fast feedback
- Makes debugging easier

### 3. Fix Failures Immediately

Don't proceed to next subtask if validation fails:
- Fix the issue
- Re-run validation
- Only move forward when passing

### 4. Maintain Test Coverage

- Add tests for all new functionality
- Don't decrease coverage percentage
- High-risk changes need more tests

### 5. Review Reports

Read validation reports to understand:
- What changed
- What was tested
- What might be risky

## Integration with Development Workflow

### For Individual Developers

```bash
# Daily workflow
git checkout -b feature/new-feature

# Start regression prevention
uv run python scripts/prevent_regressions.py start "Implement new feature"

# Implement and validate subtasks
# ... (edit code, run validations) ...

# Finalize
uv run python scripts/prevent_regressions.py finalize task-xxx

# Commit if validation passes
git commit -am "Add new feature"
git push
```

### For Code Reviews

Reviewers can check:
- Task manifest (clear decomposition?)
- Validation reports (all tests pass?)
- Final report (integration validated?)

### For CI/CD

The system can be integrated into GitHub Actions:

```yaml
- name: Validate Changes
  run: |
    # Find task for this PR
    TASK_ID=$(ls .work/tasks/ | head -n 1)
    
    # Run final validation
    uv run python scripts/prevent_regressions.py finalize $TASK_ID
```

## Troubleshooting

### "Task not found"

Task directory doesn't exist. Check:
- Correct task ID
- `.work/tasks/` directory exists
- Use `list` command to see all tasks

### "Baseline capture failed"

Test suite couldn't run. Check:
- Dependencies installed (`uv sync`)
- No syntax errors in code
- Tests can run manually

### "Validation failed"

Tests are failing. Check:
- Validation report for details
- Run tests manually to debug
- Review code changes

### "Missing tests"

Required tests don't exist. Check:
- Test files created
- Test paths correct in manifest
- Tests are runnable

## Advanced Usage

### Custom Test Selection

Edit manifest.json to specify exact tests:

```json
{
  "tests_required": [
    {
      "type": "unit",
      "path": "tests/test_feature.py::test_specific_function",
      "description": "Test new function works correctly"
    }
  ]
}
```

### Risk-Based Validation

High-risk subtasks automatically:
- Require more comprehensive tests
- Run longer test suites
- Need manual review

### Parallel Validation

Multiple developers can work on different subtasks simultaneously:
- Each validates independently
- Integration validation catches conflicts
- Merge carefully to avoid issues

## Future Enhancements

Planned improvements:

1. **Smart Test Selection** - Only run tests affected by changes
2. **LLM-Powered Decomposition** - Intelligent task breakdown
3. **Automated Rollback** - Revert changes if validation fails
4. **PR Integration** - Automatic validation reports in PRs
5. **Regression Database** - Track and prioritize tests that caught bugs

## Support

For issues or questions:
1. Check validation reports for details
2. Run with `--verbose` flag for more info
3. Review task manifest and baseline
4. Check test output manually

## Examples

See `.work/tasks/` directory for real examples of:
- Task manifests
- Validation reports
- Integration reports
