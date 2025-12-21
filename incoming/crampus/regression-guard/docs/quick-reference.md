# Regression Prevention System - Quick Reference

## Cheat Sheet

```bash
# Start new task
uv run python scripts/prevent_regressions.py start "Task description"

# Show task status
uv run python scripts/prevent_regressions.py status <task-id>

# Validate subtask (after implementing)
uv run python scripts/prevent_regressions.py validate <subtask-id>

# Finalize task (after all subtasks)
uv run python scripts/prevent_regressions.py finalize <task-id>

# List all tasks
uv run python scripts/prevent_regressions.py list
```

## Workflow

```
1. START    → Decompose + Capture Baseline
2. IMPLEMENT → Code subtask
3. VALIDATE  → Test subtask
4. REPEAT    → Steps 2-3 for each subtask
5. FINALIZE  → Integration validation
6. COMMIT    → If all validations pass
```

## Validation Checks

Each subtask validation checks:
- ✅ Baseline tests still pass (no regressions)
- ✅ New tests exist and pass
- ✅ Coverage doesn't decrease
- ✅ Build passes (lint, format, type check)

## Status Icons

- ⏳ Pending (not started)
- ✅ Passed (validated successfully)
- ❌ Failed (needs fixing)
- ⏭️ Skipped (optional)

## Risk Levels

- **LOW** - Isolated change, well-tested
- **MEDIUM** - Multiple files, moderate impact
- **HIGH** - Core functionality, many dependencies

## Reports Location

```
.work/tasks/<task-id>/
  manifest.json                    # Task plan
  baseline.json                    # Before state
  <subtask-id>/report.md          # Subtask results
  final_report.md                  # Overall results
```

## Common Issues

| Problem | Solution |
|---------|----------|
| Validation fails | Check report.md, fix issues, re-run |
| Missing tests | Create required test files |
| Coverage drops | Add tests to increase coverage |
| Build fails | Run `uv run build.py --fix` |

## Best Practices

1. Keep subtasks < 1 hour
2. Validate after EVERY subtask
3. Fix failures before proceeding
4. Review reports carefully
5. Don't skip integration validation

## Integration with Build System

```bash
# Full build with regression prevention
uv run build.py --fix --verbose

# Then finalize your task
uv run python scripts/prevent_regressions.py finalize <task-id>
```

## Example Session

```bash
$ uv run python scripts/prevent_regressions.py start "Add user authentication"
[+] Task ID: task-20251125-120000
[+] Baseline captured successfully
[*] Next: Implement subtasks

$ uv run python scripts/prevent_regressions.py status task-20251125-120000
Task Status: task-20251125-120000
Description: Add user authentication
Subtasks: 5

Progress:
  ⏳ subtask-0-plan: Plan implementation approach
  ⏳ subtask-1-create: Create new files/functions
  ⏳ subtask-2-modify: Modify existing files
  ⏳ subtask-3-test: Add/update tests
  ⏳ subtask-final-integration: Validate system integration

$ # Implement subtask-1-create...
$ uv run python scripts/prevent_regressions.py validate subtask-1-create
[+] Subtask subtask-1-create validation PASSED

$ # Continue with remaining subtasks...

$ uv run python scripts/prevent_regressions.py finalize task-20251125-120000
[+] Task task-20251125-120000 integration validation PASSED
[+] All changes validated successfully!
```
