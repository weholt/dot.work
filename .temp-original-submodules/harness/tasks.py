"""
Task file parsing and management for the harness.

Handles reading and writing markdown checkbox task files.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Regex to match markdown checkbox tasks: - [ ] Task text or - [x] Task text
TASK_RE = re.compile(r"^\s*-\s*\[\s*(?P<state>[xX ])\s*\]\s*(?P<text>.+?)\s*$")


class TaskFileError(Exception):
    """Exception raised when a task file is invalid or cannot be found."""

    pass


@dataclass(frozen=True)
class Task:
    """A single task from the markdown file."""

    line_no: int
    done: bool
    text: str


def load_tasks(md_path: Path) -> tuple[str, list[Task]]:
    """Load tasks from a markdown file.

    Args:
        md_path: Path to the markdown task file

    Returns:
        Tuple of (file content, list of Task objects)
    """
    content = md_path.read_text(encoding="utf-8")
    tasks: list[Task] = []

    for i, line in enumerate(content.splitlines()):
        m = TASK_RE.match(line)
        if m:
            tasks.append(
                Task(
                    line_no=i,
                    done=(m.group("state").lower() == "x"),
                    text=m.group("text").strip(),
                )
            )

    return content, tasks


def count_done(tasks: list[Task]) -> int:
    """Count completed tasks.

    Args:
        tasks: List of Task objects

    Returns:
        Number of completed tasks
    """
    return sum(1 for t in tasks if t.done)


def next_open_task(tasks: list[Task]) -> Task | None:
    """Get the first incomplete task.

    Args:
        tasks: List of Task objects

    Returns:
        The first incomplete Task, or None if all are done
    """
    for t in tasks:
        if not t.done:
            return t
    return None


def validate_task_file(md_path: Path) -> None:
    """Validate that the task file exists and has tasks.

    Args:
        md_path: Path to the markdown task file

    Raises:
        TaskFileError: If file doesn't exist or has no tasks
    """
    if not md_path.exists():
        raise TaskFileError(f"Task file not found: {md_path}")

    _, tasks = load_tasks(md_path)
    if not tasks:
        raise TaskFileError(f"No tasks found in: {md_path}")
