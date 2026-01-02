"""Git operations and diff parsing for review functionality."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from dot_review.models import DiffHunk, DiffLine, FileDiff

# Pattern for validating git references (refs, tags, branches, commit hashes)
# Allows: alphanumeric, underscore, hyphen, dot, forward slash, tilde, caret, colon, at
# Also allows full commit hashes (40+ hex characters)
# Blocks: git options (starting with --), shell metacharacters, path traversal
_REF_PATTERN = re.compile(
    r"^[a-zA-Z0-9_\-./~^:@]+$"  # Standard ref characters
    r"|^[a-fA-F0-9]{40,64}$"  # Full commit hash
    r"|^HEAD$"  # HEAD reference
    r"|^@\{-[0-9]+\}$"  # @annotation syntax (e.g., @{-1})
)


class GitError(RuntimeError):
    """Error from git operations."""

    pass


class GitRefValidationError(GitError):
    """Error when a git reference fails validation."""

    pass


def _validate_git_ref(ref: str) -> str:
    """Validate a git reference for security.

    This function validates git references (branches, tags, commit hashes, etc.)
    to prevent git option injection attacks.

    Args:
        ref: Git reference to validate.

    Returns:
        The validated ref.

    Raises:
        GitRefValidationError: If the ref contains invalid characters or patterns.
    """
    if not ref:
        raise GitRefValidationError("Git reference cannot be empty")

    # Block git options (most dangerous attack vector)
    if ref.startswith("--"):
        raise GitRefValidationError(
            f"Git options are not allowed: '{ref}'. Only valid git references are permitted."
        )

    # Block shell metacharacters that could enable command injection
    dangerous_chars = ["|", "&", ";", "$", "`", "(", ")", "<", ">", "\n", "\r"]
    if any(char in ref for char in dangerous_chars):
        raise GitRefValidationError(f"Git reference contains dangerous characters: '{ref}'")

    # Block path traversal attempts
    if ".." in ref:
        raise GitRefValidationError(f"Git reference contains path traversal sequence: '{ref}'")

    # Validate against whitelist pattern
    if not _REF_PATTERN.match(ref):
        raise GitRefValidationError(
            f"Invalid git reference: '{ref}'. "
            "Valid references include branch names, tags, commit hashes, and HEAD."
        )

    return ref


def _validate_git_path(path: str) -> str:
    """Validate a file path for use in git commands.

    This function validates file paths to prevent git option injection.

    Args:
        path: File path to validate.

    Returns:
        The validated path.

    Raises:
        GitRefValidationError: If the path contains dangerous patterns.
    """
    if not path:
        raise GitRefValidationError("Path cannot be empty")

    # Block git options
    if path.startswith("--"):
        raise GitRefValidationError(f"Git options are not allowed in paths: '{path}'")

    # Block shell metacharacters
    dangerous_chars = ["|", "&", ";", "$", "`", "\n", "\r"]
    if any(char in path for char in dangerous_chars):
        raise GitRefValidationError(f"Path contains dangerous characters: '{path}'")

    return path


def _run_git(args: list[str], cwd: str | None = None) -> str:
    """Run a git command and return stdout.

    Args:
        args: Git command arguments (without 'git' prefix).
        cwd: Working directory for the command.

    Returns:
        Standard output from the command.

    Raises:
        GitError: If the git command fails.
    """
    cmd = ["git", *args]  # noqa: S607
    result = subprocess.run(  # noqa: S603
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def ensure_git_repo(cwd: str) -> None:
    """Verify the directory is inside a git repository.

    Args:
        cwd: Directory to check.

    Raises:
        GitError: If not inside a git repository.
    """
    _run_git(["rev-parse", "--is-inside-work-tree"], cwd=cwd)


def repo_root(cwd: str) -> str:
    """Get the root directory of the git repository.

    Args:
        cwd: Directory inside the repository.

    Returns:
        Absolute path to the repository root.
    """
    return _run_git(["rev-parse", "--show-toplevel"], cwd=cwd).strip()


def list_tracked_files(cwd: str) -> list[str]:
    """List all tracked files in the repository.

    Args:
        cwd: Directory inside the repository.

    Returns:
        List of tracked file paths relative to repo root.
    """
    out = _run_git(["ls-files", "-z"], cwd=cwd)
    return [p for p in out.split("\x00") if p]


def list_all_files(root: str) -> list[str]:
    """List all files in the directory tree, excluding common ignore patterns.

    Uses os.walk() with directory pruning to avoid creating Path objects
    for files in ignored directories (e.g., node_modules, .git).

    Args:
        root: Root directory to scan.

    Returns:
        List of file paths relative to root.
    """
    root_path = Path(root).resolve()
    ignore_dirs = {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        ".venv",
        "venv",
        "env",
        ".tox",
        ".nox",
        "dist",
        "build",
        ".work",
        "htmlcov",
    }
    ignore_files = {".DS_Store", "Thumbs.db"}

    result: list[str] = []

    # Use os.walk() with directory pruning for efficiency
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Modify dirnames in-place to prune ignored directories
        # This prevents os.walk() from recursing into them
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.endswith(".egg-info")]

        for filename in filenames:
            if filename in ignore_files:
                continue

            # Get relative path from root
            full_path = Path(dirpath) / filename
            rel_path = full_path.relative_to(root_path)
            result.append(str(rel_path).replace("\\", "/"))

    return sorted(result)


def changed_files(cwd: str, base: str = "HEAD") -> set[str]:
    """Get files with uncommitted changes.

    Args:
        cwd: Directory inside the repository.
        base: Base reference to compare against.

    Returns:
        Set of changed file paths.

    Raises:
        GitRefValidationError: If base contains invalid characters.
    """
    # Validate the base reference to prevent git option injection
    _validate_git_ref(base)

    try:
        out = _run_git(["diff", "--name-only", base, "--"], cwd=cwd)
        return {line.strip() for line in out.splitlines() if line.strip()}
    except GitError as e:
        # Handle empty repo (no commits yet) - treat all staged files as changed
        if "bad revision" in str(e):
            # For empty repos, check staged files instead
            try:
                out = _run_git(["diff", "--name-only", "--cached"], cwd=cwd)
                return {line.strip() for line in out.splitlines() if line.strip()}
            except GitError:
                return set()
        raise


def read_file_text(root: str, path: str) -> str:
    """Read file contents safely.

    Args:
        root: Repository root directory.
        path: File path relative to root.

    Returns:
        File contents as string.

    Raises:
        GitError: If path escapes the repository.
    """
    full = Path(root) / path
    norm = full.resolve()
    root_norm = Path(root).resolve()

    # Prevent path traversal using relative_to() for robust checking
    try:
        norm.relative_to(root_norm)
    except ValueError:
        raise GitError("invalid path") from None

    return norm.read_text(encoding="utf-8", errors="replace")


def get_unified_diff(cwd: str, path: str, base: str = "HEAD") -> str:
    """Get unified diff for a file.

    Args:
        cwd: Directory inside the repository.
        path: File path to diff.
        base: Base reference to compare against.

    Returns:
        Unified diff output.

    Raises:
        GitRefValidationError: If base or path contains invalid characters.
    """
    # Validate both base reference and path to prevent injection
    _validate_git_ref(base)
    _validate_git_path(path)

    return _run_git(["diff", "--no-color", "--unified=3", base, "--", path], cwd=cwd)


@dataclass
class _HunkHeader:
    """Parsed hunk header information."""

    old_start: int
    old_len: int
    new_start: int
    new_len: int


def _parse_hunk_header(line: str) -> _HunkHeader:
    """Parse a hunk header line.

    Args:
        line: Line starting with @@.

    Returns:
        Parsed hunk header.

    Raises:
        GitError: If the header cannot be parsed.
    """
    try:
        inside = line.split("@@")[1].strip()
        parts = inside.split()
        old_part = parts[0]  # -a,b
        new_part = parts[1]  # +c,d

        old_nums = old_part[1:].split(",")
        new_nums = new_part[1:].split(",")

        old_start = int(old_nums[0])
        old_len = int(old_nums[1]) if len(old_nums) > 1 else 1
        new_start = int(new_nums[0])
        new_len = int(new_nums[1]) if len(new_nums) > 1 else 1

        return _HunkHeader(old_start, old_len, new_start, new_len)
    except Exception as e:
        raise GitError(f"failed to parse hunk header: {line}") from e


def parse_unified_diff(path: str, diff_text: str) -> FileDiff:
    """Parse unified diff output into structured model.

    Args:
        path: File path being diffed.
        diff_text: Raw unified diff text.

    Returns:
        Parsed FileDiff model.
    """
    if not diff_text.strip():
        return FileDiff(path=path, hunks=[])

    # Detect binary files
    if "GIT binary patch" in diff_text or "Binary files" in diff_text:
        return FileDiff(path=path, is_binary=True, hunks=[])

    lines = diff_text.splitlines()
    hunks: list[DiffHunk] = []
    cur_hunk: DiffHunk | None = None
    old_ln: int | None = None
    new_ln: int | None = None

    for raw in lines:
        if raw.startswith("@@"):
            hh = _parse_hunk_header(raw)
            cur_hunk = DiffHunk(
                header=raw,
                old_start=hh.old_start,
                old_len=hh.old_len,
                new_start=hh.new_start,
                new_len=hh.new_len,
                lines=[],
            )
            hunks.append(cur_hunk)
            old_ln = hh.old_start
            new_ln = hh.new_start
            continue

        if cur_hunk is None:
            # Skip file headers
            continue

        if raw.startswith("+") and not raw.startswith("+++"):
            cur_hunk.lines.append(
                DiffLine(kind="add", text=raw[1:], old_lineno=None, new_lineno=new_ln)
            )
            new_ln = (new_ln + 1) if new_ln is not None else None
        elif raw.startswith("-") and not raw.startswith("---"):
            cur_hunk.lines.append(
                DiffLine(kind="del", text=raw[1:], old_lineno=old_ln, new_lineno=None)
            )
            old_ln = (old_ln + 1) if old_ln is not None else None
        elif raw.startswith(" "):
            cur_hunk.lines.append(
                DiffLine(kind="context", text=raw[1:], old_lineno=old_ln, new_lineno=new_ln)
            )
            old_ln = (old_ln + 1) if old_ln is not None else None
            new_ln = (new_ln + 1) if new_ln is not None else None
        else:
            cur_hunk.lines.append(
                DiffLine(kind="meta", text=raw, old_lineno=old_ln, new_lineno=new_ln)
            )

    return FileDiff(path=path, hunks=hunks)
