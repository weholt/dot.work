"""Version management module for dot-work.

Provides date-based versioning (YYYY.MM.NNNNN) with automatic changelog
generation from conventional commits.
"""

from dot_work.version.changelog import ChangelogEntry, ChangelogGenerator
from dot_work.version.commit_parser import CommitInfo, ConventionalCommitParser
from dot_work.version.config import VersionConfig
from dot_work.version.manager import VersionInfo, VersionManager

__version__ = "0.1.0"

__all__ = [
    "VersionInfo",
    "VersionManager",
    "CommitInfo",
    "ConventionalCommitParser",
    "ChangelogEntry",
    "ChangelogGenerator",
    "VersionConfig",
]
