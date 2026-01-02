"""FastAPI web server for review UI."""

from __future__ import annotations

import logging
import os
import socket
import time
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from dot_review.git import (
    changed_files,
    ensure_git_repo,
    get_unified_diff,
    list_all_files,
    list_tracked_files,
    parse_unified_diff,
    read_file_text,
    repo_root,
)
from dot_review.models import ReviewComment
from dot_review.storage import append_comment, load_comments, new_review_id

logger = logging.getLogger(__name__)

# Rate limiting: store request timestamps by client
_rate_limit_store: dict[str, list[float]] = {}
# Default rate limit: 60 requests per minute
RATE_LIMIT_REQUESTS = 60
RATE_LIMIT_WINDOW = 60


def _get_auth_token() -> str | None:
    """Get the authentication token from environment."""
    return os.getenv("REVIEW_AUTH_TOKEN")


def _verify_path_safe(root: Path | str, path: str) -> None:
    """Verify that a path doesn't escape the repository root.

    Args:
        root: Repository root path.
        path: File path to validate.

    Raises:
        HTTPException: If path escapes repository root.
    """
    if not path:
        return

    # Convert to Path if needed
    if isinstance(root, str):
        root = Path(root)

    # Resolve paths to their absolute form
    root_resolved = root.resolve()
    try:
        path_resolved = (root_resolved / path).resolve()
    except (OSError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path",
        )

    # Check if the resolved path is within root
    try:
        path_resolved.relative_to(root_resolved)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Path outside repository root not allowed",
        )


def _check_rate_limit(
    client_id: str, max_requests: int = RATE_LIMIT_REQUESTS, window: int = RATE_LIMIT_WINDOW
) -> bool:
    """Check if client has exceeded rate limit.

    Args:
        client_id: Unique identifier for the client.
        max_requests: Maximum requests allowed in window.
        window: Time window in seconds.

    Returns:
        True if request is allowed, False if rate limited.
    """
    now = time.time()

    # Clean old entries for this client
    if client_id in _rate_limit_store:
        _rate_limit_store[client_id] = [
            ts for ts in _rate_limit_store[client_id] if now - ts < window
        ]
    else:
        _rate_limit_store[client_id] = []

    # Check if limit exceeded
    if len(_rate_limit_store[client_id]) >= max_requests:
        return False

    # Record this request
    _rate_limit_store[client_id].append(now)
    return True


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

    app = FastAPI(title="dot-work-review", version="0.1.0")

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
        # Check authentication
        token = _get_auth_token()
        if token:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer ") or auth_header[7:] != token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token",
                )

        if not path and files:
            path = next((p for p in files if p in all_changed), files[0])

        file_is_changed = (path in changed) if path else False

        file_text = ""
        file_lines: list[str] = []
        fd = None

        if path:
            # Path traversal protection
            _verify_path_safe(root, path)

            if file_is_changed:
                diff_txt = get_unified_diff(root, path, base=base_ref)
                fd = parse_unified_diff(path, diff_txt)
            try:
                file_text = read_file_text(root, path)
            except (FileNotFoundError, PermissionError, OSError) as e:
                logger.warning("Failed to read file %s: %s", path, e)
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
    def state(request: Request) -> dict:
        """Get current review state."""
        # Check authentication
        token = _get_auth_token()
        if token:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer ") or auth_header[7:] != token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token",
                )

        return {
            "review_id": review_id,
            "base_ref": base_ref,
            "tracked_files": len(files),
            "changed_files": len(changed),
        }

    @app.post("/api/comment")
    def add_comment(request: Request, inp: AddCommentIn) -> JSONResponse:
        """Add a new comment."""
        # Check authentication
        token = _get_auth_token()
        if token:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer ") or auth_header[7:] != token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token",
                )

        # Path traversal protection
        _verify_path_safe(root, inp.path)

        # Rate limiting by client IP
        client_id = request.client.host if request.client else "unknown"
        if not _check_rate_limit(client_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: max {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds",
            )

        # Collect context around the target line
        try:
            text = read_file_text(root, inp.path)
            lines = text.splitlines()
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.warning("Failed to read file %s for comment context: %s", inp.path, e)
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


def run_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    base: str | None = None,
    head: str | None = None,
) -> None:
    """Run the review server.

    Args:
        host: Host to bind to.
        port: Port to bind to (0 for auto-pick).
        base: Base git ref to diff against (default: HEAD~1).
        head: Head git ref (default: working tree, ignored for now).
    """
    import uvicorn

    base_ref = base or "HEAD~1"
    workdir = "."
    actual_port = pick_port(port if port != 0 else None)

    app, review_id = create_app(workdir, base_ref=base_ref)
    print(f"Starting review server (review_id: {review_id})")
    print(f"Base ref: {base_ref}")

    uvicorn.run(app, host=host, port=actual_port)
