# SEC-003@94eb69 Investigation: Unvalidated git command argument

## Issue
Git ref parameters not validated before subprocess execution, allowing potential git option injection.

## Vulnerability Location
- **File:** `src/dot_work/review/git.py`
- **Function:** `_run_git()` (lines 18-40), `changed_files()` (line 128), `get_unified_diff()` (line 177)

## Root Cause

### The Vulnerable Code (lines 31-32)
```python
def _run_git(args: list[str], cwd: str | None = None) -> str:
    cmd = ["git", *args]  # User-controlled args directly inserted
    result = subprocess.run(cmd, ...)  # No validation
```

### Specific User-Controlled Parameters

**1. `changed_files()` function (line 128):**
```python
def changed_files(cwd: str, base: str = "HEAD") -> set[str]:
    # Line 139: base parameter used directly
    out = _run_git(["diff", "--name-only", base, "--"], cwd=cwd)
```

**2. `get_unified_diff()` function (line 177):**
```python
def get_unified_diff(cwd: str, path: str, base: str = "HEAD") -> str:
    # Line 188: base and path parameters used directly
    return _run_git(["diff", "--no-color", "--unified=3", base, "--", path], cwd=cwd)
```

## Attack Vectors

Git allows passing options via ref names. Git treats certain patterns as options rather than refs:

### 1. Remote Code Execution via `--upload-pack`
```python
changed_files(cwd, base="--upload-pack=|touch /tmp/pwned|")
# Result: Executes arbitrary command via git's upload-pack feature
```

### 2. Arbitrary File Read via `--git-dir`
```python
changed_files(cwd, base="--git-dir=/etc/passwd")
# Result: Attempts to read /etc/passwd as git repository
```

### 3. Repository Escape via `--work-tree`
```python
changed_files(cwd, base="--work-tree=/tmp")
# Result: Changes git's working directory to arbitrary location
```

### 4. Config Injection via ref names
```python
changed_files(cwd, base="-c core.sshCommand=/tmp/evil.sh")
# Result: Injects git config with arbitrary command
```

### 5. Option Breakout via double dash
```python
# Even with "--" separator, certain git options bypass it
changed_files(cwd, base="./evil-file --option")
```

## Why This Is Critical

1. **CVSS 8.5 (High)** - Local attack, low complexity, high impact
2. **RCE possible** via `--upload-pack` with pipe command
3. **File access** via `--git-dir` and `--work-tree`
4. **CI/CD exposure** - If used in PR-controlled workflows
5. **Developer tool** - Often run with elevated permissions

## Existing Protections

**Path traversal protection exists in `read_file_text()` (lines 166-172):**
```python
def read_file_text(root: str, path: str) -> str:
    full = Path(root) / path
    norm = full.resolve()
    root_norm = Path(root).resolve()
    if not str(norm).startswith(str(root_norm)):
        raise GitError("invalid path")
```

But this only protects file reads, not git command arguments.

## Proposed Solution

### 1. Git Ref Validation Pattern

According to [git-check-ref-format(1)](https://git-scm.com/docs/git-check-ref-format), valid refs can only contain:
- Uppercase and lowercase ASCII letters
- Digits (0-9)
- Special characters: `. - _ / : ~ ^ @`
- Must not start with dot (`.`) or hyphen (`-`)
- Must not contain `..` (double dot)
- Must not contain `@{` (reflog syntax)
- Must not end with `.lock`
- Must not contain special sequences like `:` (except for branches/tags with specific format)

**Safe regex for git refs:**
```python
import re

# Allow: branch names, tag names, commit hashes, HEAD
REF_PATTERN = re.compile(
    r'^[a-zA-Z0-9_\-./~^:]+'  # Basic ref characters
    r'|[a-fA-F0-9]{40,64}'      # Full commit hash
    r'|HEAD'                    # HEAD reference
    r'|@[a-zA-Z0-9_\-]+$'       # @annotation syntax
)
```

### 2. Block Git Options

Reject any argument that starts with `--`:
```python
def _validate_git_arg(arg: str) -> str:
    if arg.startswith("--"):
        raise ValueError(f"Git options not allowed: {arg}")
    if not REF_PATTERN.match(arg):
        raise ValueError(f"Invalid git reference: {arg}")
    return arg
```

### 3. Use `git rev-parse` for Validation

Resolve refs to commit hashes before using:
```python
def _resolve_ref(cwd: str, ref: str) -> str:
    """Resolve a git ref to commit hash."""
    try:
        return _run_git(["rev-parse", ref], cwd=cwd).strip()
    except GitError:
        raise ValueError(f"Invalid git reference: {ref}")
```

### 4. Alternative: Use GitPython

The project already has GitPython available (used in other modules):
```python
import git

repo = git.Repo(cwd)
commit = repo.commit(base)  # Validates ref automatically
```

## Implementation Plan

1. **Add ref validation function** with whitelist pattern
2. **Validate `base` parameter** in `changed_files()` and `get_unified_diff()`
3. **Validate `path` parameter** for git command injection (ensure it's a file path, not an option)
4. **Add tests** for malicious ref names
5. **Consider GitPython migration** for safer abstraction (future improvement)

## Acceptance Criteria

- [ ] All git refs validated with strict regex
- [ ] Git options (args starting with `--`) blocked
- [ ] Tests verify malicious ref names are rejected
- [ ] Security audit passes all git command constructions
- [ ] All existing tests still pass

## Related Issues

- SEC-002: SQL injection in FTS5 (similar pattern - unvalidated user input)
- memory_leak.md: Security patterns for input validation
