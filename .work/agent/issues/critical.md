# Critical Issues (P0)

Blockers, security issues, data loss risks.

---
id: "BUG-001@fe313e"
title: "Installed dot-work tool missing python.build module"
description: "UV tool installation outdated - missing build/ submodule that exists in source"
created: 2025-12-26
section: "installation"
tags: [installation, uv-tool, module-not-found, python]
type: bug
priority: critical
status: proposed
references:
  - src/dot_work/python/__init__.py
  - src/dot_work/python/build/cli.py
  - src/dot_work/python/build/runner.py
---

### Problem
When running `dot-work install` (or any dot-work command), the installed tool fails with:

```
ModuleNotFoundError: No module named 'dot_work.python.build'
```

The import occurs at `dot_work/python/__init__.py:12`:
```python
from dot_work.python.build.cli import run_build
```

### Root Cause Analysis

**Source Code State (Current Repository):**
- The `build/` module EXISTS at `src/dot_work/python/build/`
- Files present: `cli.py`, `runner.py`, `__init__.py`
- Git shows recent commits: "Build clean", "Fucking agents ...."
- Working tree is clean - build module is tracked

**Installed Package State:**
- Location: `~/.local/share/uv/tools/dot-work/lib/python3.13/site-packages/dot_work/python/`
- Directories present: `__pycache__`, `scan`
- **MISSING:** `build/` directory
- Install timestamp: Dec 26 02:36 (likely outdated)

**Conclusion:** The installed uv tool version predates the addition of the `build/` module to the codebase.

### Affected Files
- Installed package: `~/.local/share/uv/tools/dot-work/lib/python3.13/site-packages/dot_work/python/` (missing build/)
- Source import: `src/dot_work/python/__init__.py` (line 12)

### Importance
**CRITICAL:** The `dot-work` command is completely broken. All commands fail with `ModuleNotFoundError` because the top-level `__init__.py` imports the missing module during package initialization.

This blocks all dot-work functionality until resolved.

### Error / Exception Details
```
Traceback (most recent call last):
  File "/home/thomas/.local/bin/dot-work", line 4, in <module>
    from dot_work.cli import app
  File "/home/thomas/.local/share/uv/tools/dot-work/lib/python3.13/site-packages/dot_work/cli.py", line 16, in <module>
    from dot_work.python import python_app
  File "/home/thomas/.local/share/uv/tools/dot-work/lib/python3.13/site-packages/dot_work/python/__init__.py", line 12, in <module>
    from dot_work.python.build.cli import run_build
ModuleNotFoundError: No module named 'dot_work.python.build'
```

### Proposed Solution
1. **Reinstall the tool from current source:**
   ```bash
   cd /home/thomas/Workspace/dot.work
   uv tool uninstall dot-work
   uv tool install .
   ```

2. **Alternatively, use `uv tool upgrade` if supported:**
   ```bash
   uv tool upgrade dot-work
   ```

3. **Prevent future issues:** Consider adding a post-commit hook or CI check to verify tool installation is up-to-date after commits that add new submodules.

### Acceptance Criteria
- [ ] Tool reinstalled from current source code
- [ ] `dot-work --help` runs without ModuleNotFoundError
- [ ] `dot-work python build` command works (build module functional)
- [ ] All existing subcommands (scan, etc.) still work
- [ ] Note added to README about reinstalling after major updates

### Notes
- This issue highlights a gap: no automated verification that installed tool matches source
- Consider adding `uv tool install . --reinstall` to development workflow
- The branch `migrating-using-opencode` is 13 commits ahead of origin - these new features aren't in the installed version

Investigation completed using systematic debugging process:
- Phase 1: Root cause identified (outdated installation vs current source)
- Evidence: Git history shows build module exists; installed package missing it
- No code fix needed - reinstallation required

---
---
