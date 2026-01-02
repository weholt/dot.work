"""
Git metadata extraction for Python files.

Provides blame and history information for scanned files.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from subprocess import CalledProcessError, check_output


@dataclass
class GitInfo:
    """Git metadata for a file."""

    file_path: Path
    author: str | None = None
    commit_hash: str | None = None
    commit_date: datetime | None = None
    lines_changed: int = 0


class GitAnalyzer:
    """Analyzer for extracting Git metadata."""

    def __init__(self, repo_root: Path) -> None:
        """Initialize the Git analyzer.

        Args:
            repo_root: Root of the Git repository.
        """
        self.repo_root = repo_root.resolve()
        self._is_repo = self._check_is_repo()

    def _check_is_repo(self) -> bool:
        """Check if the path is a Git repository.

        Returns:
            True if inside a Git repo.
        """
        git_dir = self.repo_root / ".git"
        return git_dir.exists() or git_dir.is_dir()

    def is_available(self) -> bool:
        """Check if Git analysis is available.

        Returns:
            True if Git is available.
        """
        return self._is_repo

    def get_file_info(self, file_path: Path) -> GitInfo:
        """Get Git metadata for a file.

        Args:
            file_path: Path to the file.

        Returns:
            GitInfo with metadata.
        """
        if not self.is_available():
            return GitInfo(file_path=file_path)

        try:
            rel_path = file_path.relative_to(self.repo_root)
        except ValueError:
            return GitInfo(file_path=file_path)

        return GitInfo(
            file_path=file_path,
            author=self._get_author(rel_path),
            commit_hash=self._get_commit_hash(rel_path),
            commit_date=self._get_commit_date(rel_path),
            lines_changed=self._get_lines_changed(rel_path),
        )

    def _get_author(self, rel_path: Path) -> str | None:
        """Get the last author for a file.

        Args:
            rel_path: Relative path to file.

        Returns:
            Author name or None.
        """
        try:
            output = check_output(  # noqa: S603, S607
                ["git", "log", "-1", "--pretty=format:%an", str(rel_path)],  # noqa: S607
                cwd=self.repo_root,
                text=True,
            )
            return output.strip() or None
        except (CalledProcessError, FileNotFoundError):
            return None

    def _get_commit_hash(self, rel_path: Path) -> str | None:
        """Get the last commit hash for a file.

        Args:
            rel_path: Relative path to file.

        Returns:
            Commit hash or None.
        """
        try:
            output = check_output(  # noqa: S603, S607
                ["git", "log", "-1", "--pretty=format:%H", str(rel_path)],  # noqa: S607
                cwd=self.repo_root,
                text=True,
            )
            return output.strip() or None
        except (CalledProcessError, FileNotFoundError):
            return None

    def _get_commit_date(self, rel_path: Path) -> datetime | None:
        """Get the last commit date for a file.

        Args:
            rel_path: Relative path to file.

        Returns:
            Commit date or None.
        """
        try:
            output = check_output(  # noqa: S603, S607
                ["git", "log", "-1", "--pretty=format:%ct", str(rel_path)],  # noqa: S607
                cwd=self.repo_root,
                text=True,
            )
            timestamp = output.strip()
            if timestamp:
                return datetime.fromtimestamp(int(timestamp))
        except (CalledProcessError, FileNotFoundError, ValueError):
            pass
        return None

    def _get_lines_changed(self, rel_path: Path) -> int:
        """Get the number of lines changed in the last commit.

        Args:
            rel_path: Relative path to file.

        Returns:
            Number of lines changed.
        """
        try:
            output = check_output(  # noqa: S603, S607
                ["git", "log", "-1", "--numstat", "--pretty=format:", str(rel_path)],  # noqa: S607
                cwd=self.repo_root,
                text=True,
            )
            lines = output.strip().split()
            if len(lines) >= 2:
                return int(lines[0]) + int(lines[1])
        except (CalledProcessError, FileNotFoundError, ValueError, IndexError):
            pass
        return 0
