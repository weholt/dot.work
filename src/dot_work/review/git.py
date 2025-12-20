"""Git operations and diff parsing for review functionality."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from dot_work.review.models import DiffHunk, DiffLine, FileDiff


class GitError(RuntimeError):
    """Error from git operations."""

    pass


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
        "*.egg-info",
        ".work",
        "htmlcov",
        ".coverage",
    }
    ignore_files = {".DS_Store", "Thumbs.db"}

    result: list[str] = []
    for item in root_path.rglob("*"):
        if item.is_file():
            # Check if any parent directory should be ignored
            rel = item.relative_to(root_path)
            parts = rel.parts
            if any(part in ignore_dirs or part.endswith(".egg-info") for part in parts[:-1]):
                continue
            if parts[-1] in ignore_files:
                continue
            result.append(str(rel).replace("\\", "/"))

    return sorted(result)


def changed_files(cwd: str, base: str = "HEAD") -> set[str]:
    """Get files with uncommitted changes.

    Args:
        cwd: Directory inside the repository.
        base: Base reference to compare against.

    Returns:
        Set of changed file paths.
    """
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

    # Prevent path traversal
    if not str(norm).startswith(str(root_norm)):
        raise GitError("invalid path")

    return norm.read_text(encoding="utf-8", errors="replace")


def get_unified_diff(cwd: str, path: str, base: str = "HEAD") -> str:
    """Get unified diff for a file.

    Args:
        cwd: Directory inside the repository.
        path: File path to diff.
        base: Base reference to compare against.

    Returns:
        Unified diff output.
    """
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
