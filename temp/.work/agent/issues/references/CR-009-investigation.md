# CR-009 Investigation: Module naming conflict in dot_work.python.build.cli

**Investigation started:** 2024-12-26T22:30:00Z

## Reproduction

```bash
$ uv run python -m dot_work.python.build.cli --help
<frozen runpy>:128: RuntimeWarning: 'dot_work.python.build.cli' found in sys.modules after
import of package 'dot_work.python.build', but prior to execution of 'dot_work.python.build.cli';
this may result in unpredictable behaviour
```

The command still works but produces the warning.

## Analysis

### Current Module Structure
```
src/dot_work/python/build/
├── __init__.py        (imports from runner, not cli)
├── cli.py             (standalone CLI module)
└── runner.py          (BuildRunner class)
```

### Root Cause

The warning occurs because:
1. Running `python -m dot_work.python.build.cli` causes Python to import `dot_work.python.build` package first
2. Python's runpy module detects the package was imported before executing the submodule as a script
3. This is a known Python pitfall with `-m package.module` execution pattern

**Important:** The `__init__.py` currently imports from `runner`, NOT from `cli`. This means:
- The original issue description may have been written when the import pattern was different
- Or this is a general Python limitation with the `-m` pattern

### Why This Matters

While the command works, the warning indicates:
1. Unpredictable behavior risk
2. Fragile import pattern
3. Not following Python's recommended module execution patterns

## Investigation Checklist

- [x] Can I reproduce the issue? YES - warning appears on every run
- [x] Do I understand the root cause? YES - Python runpy limitation with `-m package.module`
- [x] Do I know which files need changes? YES - need `__main__.py`
- [x] Is my proposed solution clear? YES - use `__main__.py` pattern
- [x] Are there edge cases? Need to ensure CLI entry point still works

## Proposed Solution: Option A - `__main__.py` pattern (Recommended)

Create `src/dot_work/python/build/__main__.py`:

```python
"""Main entry point for python -m dot_work.python.build"""

from dot_work.python.build.cli import main

if __name__ == "__main__":
    main()
```

Then users run:
```bash
python -m dot_work.python.build
```

Instead of:
```bash
python -m dot_work.python.build.cli
```

### Files to Change
1. **Create:** `src/dot_work/python/build/__main__.py` (new file)
2. **No changes needed:** `__init__.py` (already doesn't import from cli)
3. **No changes needed:** `cli.py` (already has `main()` function)
4. **Update:** Documentation to use new invocation pattern

### Acceptance Criteria
- [ ] `python -m dot_work.python.build --help` works without warning
- [ ] `dot-work python build` command still works (via entry point)
- [ ] All imports resolve correctly
- [ ] Tests still pass

### Alternative Solutions Considered

**Option B:** Rename `cli.py` → `runner_cli.py` and use `-m dot_work.python.build.runner_cli`
- Pro: No new files
- Con: Changes module name, less clean

**Option C:** Document warning as known limitation
- Pro: No code changes
- Con: Doesn't fix the problem

## Notes

- The `__init__.py` already imports from `runner` (not `cli`), which is good
- This is a Python design limitation with `-m package.module` pattern
- The `__main__.py` pattern is Python's recommended approach for package executables
