# SEC-001@94eb69 - Investigation Notes

## Issue: Command injection via unvalidated editor in subprocess.run

Investigation started: 2025-12-25T17:05:00Z

### Affected Locations

1. **src/dot_work/db_issues/cli.py:1220** - `_get_text_from_editor()` function
   - Uses `os.environ.get("EDITOR", "vi")` without validation
   - Executes: `subprocess.run([editor, str(temp_path)])`

2. **src/dot_work/db_issues/cli.py:1294** - `edit()` command
   - Takes `--editor` CLI option OR uses `$EDITOR` environment variable
   - Executes: `subprocess.run([editor, str(temp_path)])`

3. **src/dot_work/db_issues/cli.py:5431** - `import_()` command (git import workflow)
   - Takes `editor_cmd` from prompt input
   - Has partial special-case handling for `code`, `vim`, `vi`, `nano`
   - Falls back to `.split()` for unknown commands: `editor_args = parts + [temp_path]`

### Root Cause Analysis

**Primary Issue:** No whitelist validation for editor commands

The code allows ANY editor command to be executed, accepting input from:
1. CLI arguments (`--editor`)
2. Environment variables (`$EDITOR`)
3. User prompts (`editor_cmd`)

**Why it's vulnerable:**

1. **No validation**: Editor command is never validated against a whitelist
2. **Arbitrary execution**: Any executable on the system can be run
3. **Social engineering**: Users could be tricked into setting malicious `$EDITOR`
4. **Split behavior**: Line 5425 `.split()` allows argument injection

**Attack Scenarios:**

| Scenario | Input | Result |
|----------|-------|--------|
| CLI option | `--editor "malicious-script"` | Runs malicious script |
| Env variable | `EDITOR="/path/to/exploit"` | Runs exploit program |
| Split injection | `editor_cmd = "code; exploit"` | Tries to run `code;` (fails), but demonstrates attempt |

**Current Protections (Mitigating but not sufficient):**

- `shell=False` is used (good - prevents shell injection)
- No shell metacharacters work directly
- But: Arbitrary executables can still be run

**What ISN'T vulnerable (false alarms):**

- `shell=True` is NOT used, so `;` and `|` don't work as command separators
- Backticks and `$()` don't work for command substitution

**What IS vulnerable (real risks):**

1. Running any executable on the system by name
2. If attacker has write access to PATH, they could place malicious executables
3. Social engineering: "Set EDITOR=/tmp/fix-issue to auto-fix your issues"

### Proposed Solution

**Implement a strict editor whitelist validation:**

```python
ALLOWED_EDITORS = {
    "vi", "vim", "nvim", "neovim",
    "emacs", "emacsclient",
    "nano",
    "code", "code-server", "codium",
    "subl", "sublime_text",
    "atom", "mate",
    "kak", "micro", "xed",
}

def validate_editor(editor_cmd: str) -> tuple[str, list[str]]:
    """Validate editor command and return (executable, args).

    Raises:
        ValueError: If editor is not in whitelist

    Returns:
        Tuple of (executable_name, additional_args)
    """
    if not editor_cmd:
        editor_cmd = os.environ.get("EDITOR", "vi")

    parts = editor_cmd.strip().split()
    executable = parts[0]

    # Extract base name (remove path)
    base_name = Path(executable).name

    if base_name not in ALLOWED_EDITORS:
        raise ValueError(
            f"Editor '{executable}' is not allowed. "
            f"Allowed editors: {', '.join(sorted(ALLOWED_EDITORS))}"
        )

    # Special handling for editors with known args
    if base_name == "code" and "--wait" not in parts:
        parts.insert(1, "--wait")

    return base_name, parts[1:]
```

### Affected Code Changes

1. **_get_text_from_editor()** (line 1195)
   - Add validation before subprocess.run
   - Whitelist check on `editor` variable

2. **edit()** (line 1246)
   - Add validation after line 1276
   - Whitelist check on `editor` option/env var

3. **import_()** (line ~5400)
   - Replace the special-case if/elif chain with whitelist validation
   - Remove the `.split()` fallback

### Risks of Fix

- User experience impact: Users with custom editors will need to use allowlist
- Migration: Existing workflows with non-standard editors will break
- Mitigation: Document how to add editors to allowlist

### Acceptance Criteria

- [ ] All three locations use the same validation function
- [ ] Only whitelisted editors can be executed
- [ ] Clear error message when disallowed editor is used
- [ ] Tests cover validation with allowed/disallowed editors
- [ ] Documentation updated with allowed editors list
- [ ] Code review verification passes
