Review subpackage for dot-work.

Provides code review UI with inline comments and AI agent export.
"""

CLI_GROUP = "review"

from dot_review.models import DiffHunk, DiffLine, FileDiff, ReviewComment

__all__ = [
    "DiffHunk",
    "DiffLine",
    "FileDiff",
    "ReviewComment",
]
