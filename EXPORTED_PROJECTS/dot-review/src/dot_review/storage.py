"""Comment storage for review functionality."""

from __future__ import annotations

import json
import time
from pathlib import Path

from dot_review.config import get_config
from dot_review.models import ReviewComment


def ensure_store(root: str) -> Path:
    """Ensure the storage directory structure exists.

    Args:
        root: Repository root directory.

    Returns:
        Path to the storage base directory.
    """
    config = get_config()
    base = Path(root) / config.storage_dir
    base.mkdir(parents=True, exist_ok=True)
    (base / "reviews").mkdir(parents=True, exist_ok=True)
    (base / "exports").mkdir(parents=True, exist_ok=True)
    return base


def new_review_id() -> str:
    """Generate a new sortable review ID.

    Returns:
        Timestamp-based review ID with millisecond precision to avoid collisions.
    """
    # Use milliseconds to prevent collision on rapid successive calls
    return time.strftime("%Y%m%d-%H%M%S") + f"-{int(time.time() * 1000) % 1000:03d}"


def review_dir(root: str, review_id: str) -> Path:
    """Get or create a review directory.

    Args:
        root: Repository root directory.
        review_id: Review identifier.

    Returns:
        Path to the review directory.
    """
    base = ensure_store(root)
    rd = base / "reviews" / review_id
    rd.mkdir(parents=True, exist_ok=True)
    return rd


def append_comment(root: str, comment: ReviewComment) -> None:
    """Append a comment to the review storage.

    Args:
        root: Repository root directory.
        comment: Comment to store.
    """
    rd = review_dir(root, comment.review_id)
    fp = rd / "comments.jsonl"
    with fp.open("a", encoding="utf-8") as f:
        f.write(comment.model_dump_json())
        f.write("\n")


def load_comments(root: str, review_id: str, path: str | None = None) -> list[ReviewComment]:
    """Load comments from storage.

    Args:
        root: Repository root directory.
        review_id: Review identifier.
        path: Optional file path filter.

    Returns:
        List of matching comments.
    """
    rd = review_dir(root, review_id)
    fp = rd / "comments.jsonl"

    if not fp.exists():
        return []

    comments: list[ReviewComment] = []
    with fp.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            comment = ReviewComment(**obj)
            if path is None or comment.path == path:
                comments.append(comment)

    return comments


def latest_review_id(root: str) -> str | None:
    """Get the most recent review ID.

    Args:
        root: Repository root directory.

    Returns:
        Latest review ID or None if no reviews exist.
    """
    base = ensure_store(root)
    reviews = sorted((base / "reviews").glob("*"))

    if not reviews:
        return None

    return reviews[-1].name
