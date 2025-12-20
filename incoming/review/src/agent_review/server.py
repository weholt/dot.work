"""FastAPI web server for agent-review UI."""

from __future__ import annotations

import socket
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from agent_review.git import (
    changed_files,
    ensure_git_repo,
    get_unified_diff,
    list_all_files,
    list_tracked_files,
    parse_unified_diff,
    read_file_text,
    repo_root,
)
from agent_review.models import ReviewComment
from agent_review.storage import append_comment, load_comments, new_review_id


class AddCommentIn(BaseModel):
    """Input model for adding a comment."""

    path: str
    side: str = "new"
    line: int
    message: str
    suggestion: str | None = None


def _free_port() -> int:
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def create_app(workdir: str, base_ref: str = "HEAD") -> tuple[FastAPI, str]:
    """Create the FastAPI application.

    Args:
        workdir: Working directory (must be inside a git repo).
        base_ref: Git ref to diff against.

    Returns:
        Tuple of (FastAPI app, review_id).
    """
    ensure_git_repo(workdir)
    root = repo_root(workdir)
    review_id = new_review_id()

    app = FastAPI(title="agent-review", version="0.1.0")

    pkg_dir = Path(__file__).parent
    templates = Jinja2Templates(directory=str(pkg_dir / "templates"))
    static_dir = pkg_dir / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    files = list_all_files(root)
    tracked = set(list_tracked_files(root))
    changed = changed_files(root, base=base_ref)
    # Include untracked files as "changed" for visibility
    untracked = {f for f in files if f not in tracked}
    all_changed = changed | untracked

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, path: str | None = None) -> HTMLResponse:
        """Render the main review UI."""
        if not path and files:
            path = next((p for p in files if p in all_changed), files[0])

        file_is_changed = (path in changed) if path else False

        file_text = ""
        file_lines: list[str] = []
        fd = None

        if path:
            if file_is_changed:
                diff_txt = get_unified_diff(root, path, base=base_ref)
                fd = parse_unified_diff(path, diff_txt)
            try:
                file_text = read_file_text(root, path)
            except Exception:
                file_text = ""
            file_lines = file_text.splitlines()

        comments = load_comments(root, review_id, path=path) if path else []
        by_line: dict[tuple[str, int], list[ReviewComment]] = defaultdict(list)
        for c in comments:
            by_line[(c.side, c.line)].append(c)

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "review_id": review_id,
                "base_ref": base_ref,
                "files": files,
                "changed": all_changed,
                "path": path,
                "file_is_changed": file_is_changed,
                "file_lines": file_lines,
                "file_diff": fd,
                "comments_by_line": by_line,
            },
        )

    @app.get("/api/state")
    def state() -> dict:
        """Get current review state."""
        return {
            "review_id": review_id,
            "base_ref": base_ref,
            "tracked_files": len(files),
            "changed_files": len(changed),
        }

    @app.post("/api/comment")
    def add_comment(inp: AddCommentIn) -> JSONResponse:
        """Add a new comment."""
        # Collect context around the target line
        try:
            text = read_file_text(root, inp.path)
            lines = text.splitlines()
        except Exception:
            lines = []

        i = max(0, inp.line - 1)  # 0-based index
        before = lines[max(0, i - 3) : i]
        after = lines[i : min(len(lines), i + 3)]

        comment = ReviewComment(
            review_id=review_id,
            path=inp.path,
            side="old" if inp.side == "old" else "new",
            line=int(inp.line),
            message=inp.message,
            suggestion=inp.suggestion,
            context_before=before,
            context_after=after,
        )
        append_comment(root, comment)
        return JSONResponse({"ok": True, "id": comment.id})

    return app, review_id


def pick_port(port: int | None) -> int:
    """Pick a port for the server.

    Args:
        port: Requested port, or 0/None for auto-pick.

    Returns:
        Port number to use.
    """
    return int(port) if port else _free_port()
