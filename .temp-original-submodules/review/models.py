"""Pydantic data models for review functionality."""

from __future__ import annotations

import time
import uuid
from typing import Literal

from pydantic import BaseModel, Field

LineKind = Literal["meta", "context", "add", "del"]


class DiffLine(BaseModel):
    """A single line in a diff hunk."""

    kind: LineKind
    text: str
    old_lineno: int | None = None
    new_lineno: int | None = None


class DiffHunk(BaseModel):
    """A hunk within a file diff."""

    header: str
    old_start: int
    old_len: int
    new_start: int
    new_len: int
    lines: list[DiffLine] = Field(default_factory=list)


class FileDiff(BaseModel):
    """Diff information for a single file."""

    path: str
    is_binary: bool = False
    hunks: list[DiffHunk] = Field(default_factory=list)


class ReviewComment(BaseModel):
    """A review comment attached to a specific line."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    review_id: str
    path: str
    side: Literal["new", "old"] = "new"
    line: int
    created_unix: float = Field(default_factory=lambda: time.time())
    message: str
    suggestion: str | None = None
    context_before: list[str] = Field(default_factory=list)
    context_after: list[str] = Field(default_factory=list)
