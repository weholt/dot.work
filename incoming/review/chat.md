Skip to content
Chat history




You said:
I want to have a local way to look at diffs in a git-tracked folder, but I want to do a code-review-like process where I can add comments and code suggestions like i can in github. I want the comments to be stored in a specified folder, prefixed with ., and then be able to say to the agentic coder run "uv run diff-monster-cli" and the comments and suggested code are presented in some format easy for agentic coders to use to change code. I want it to be python based, but if react is better for the front end so be it. I want to process the current folder and present all the files and content, including the changes visualized like in github, in a web-browser or similar, be able to add my comments and suggestions, close the window, and hand over the result to the agent for further work.

is there such a tool already? if not, create a proof-of-concept.
ChatGPT said:

Thought for 1m 26s
Existing tools (closest matches)
git-appraise (Go CLI): local/distributed code review stored in git notes; supports per-file and per-line comments and can show diffs for a review. No GitHub-like browser UI, but the storage model is very close to what you described.

Gerrit Code Review: full web UI with inline comments and side-by-side diffs, but it’s a server and expects a Gerrit workflow (push-for-review, patchsets).

CodeReview (Python/Qt): local Git diff viewer (side-by-side, staging/unstaging). It’s not a PR-review system; it’s focused on local diffs.

VS Code extension “Diff Comments for VS Code”: adds GitHub-like comments on diff views inside VS Code. Storage/export isn’t designed around “agent bundles”, but it’s the closest “works today” UX if you accept VS Code as the UI.

If you specifically want: browser-based diff UI + inline comments + comments saved under a dot-folder + CLI export for agentic coders, there isn’t a widely-used, purpose-built tool that cleanly matches that end-to-end (the closest building blocks are git-appraise + a custom UI/export layer).

Proof-of-concept: diff-monster (Python CLI + local web UI + dot-folder storage + agent export)
One-line commands
Create venv and install (editable): uv venv && uv pip install -e .

Launch review UI: uv run diff-monster-cli review

Export latest review for agent: uv run diff-monster-cli export --latest --format agent-md

# filename: pyproject.toml
[project]
name = "diff-monster"
version = "0.1.0"
description = "Local Git diff review UI with inline comments stored under .diff-monster and CLI export for agentic coders"
requires-python = ">=3.10"
dependencies = [
  "fastapi>=0.110",
  "uvicorn>=0.27",
  "jinja2>=3.1",
  "typer>=0.12",
  "pydantic>=2.6",
]

[project.scripts]
diff-monster-cli = "diff_monster.cli:app"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.package-data]
diff_monster = ["templates/*.html", "static/*"]
# filename: src/diff_monster/__init__.py
__all__ = []
# filename: src/diff_monster/models.py
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal, Optional
import time
import uuid


LineKind = Literal["meta", "context", "add", "del"]


class DiffLine(BaseModel):
    kind: LineKind
    text: str
    old_lineno: Optional[int] = None
    new_lineno: Optional[int] = None


class DiffHunk(BaseModel):
    header: str
    old_start: int
    old_len: int
    new_start: int
    new_len: int
    lines: list[DiffLine] = Field(default_factory=list)


class FileDiff(BaseModel):
    path: str
    is_binary: bool = False
    hunks: list[DiffHunk] = Field(default_factory=list)


class ReviewComment(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    review_id: str
    path: str
    side: Literal["new", "old"] = "new"
    line: int
    created_unix: float = Field(default_factory=lambda: time.time())
    message: str
    suggestion: Optional[str] = None
    context_before: list[str] = Field(default_factory=list)
    context_after: list[str] = Field(default_factory=list)
# filename: src/diff_monster/git.py
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import Optional

from .models import FileDiff, DiffHunk, DiffLine


class GitError(RuntimeError):
    pass


def _run_git(args: list[str], cwd: Optional[str] = None) -> str:
    p = subprocess.run(
        ["git", *args],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if p.returncode != 0:
        raise GitError(p.stderr.strip() or f"git {' '.join(args)} failed")
    return p.stdout


def ensure_git_repo(cwd: str) -> None:
    _run_git(["rev-parse", "--is-inside-work-tree"], cwd=cwd)


def repo_root(cwd: str) -> str:
    return _run_git(["rev-parse", "--show-toplevel"], cwd=cwd).strip()


def list_tracked_files(cwd: str) -> list[str]:
    out = _run_git(["ls-files", "-z"], cwd=cwd)
    parts = [p for p in out.split("\x00") if p]
    return parts


def changed_files(cwd: str, base: str = "HEAD") -> set[str]:
    out = _run_git(["diff", "--name-only", base, "--"], cwd=cwd)
    return {line.strip() for line in out.splitlines() if line.strip()}


def read_file_text(root: str, path: str) -> str:
    full = os.path.join(root, path)
    # simple guard against traversal
    norm = os.path.normpath(full)
    if not norm.startswith(os.path.normpath(root) + os.sep) and norm != os.path.normpath(root):
        raise GitError("invalid path")
    with open(norm, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def get_unified_diff(cwd: str, path: str, base: str = "HEAD") -> str:
    # --no-color ensures stable parsing
    return _run_git(["diff", "--no-color", "--unified=3", base, "--", path], cwd=cwd)


@dataclass
class _HunkHeader:
    old_start: int
    old_len: int
    new_start: int
    new_len: int


def _parse_hunk_header(line: str) -> _HunkHeader:
    # @@ -a,b +c,d @@ optional
    # b or d may be omitted (meaning 1)
    try:
        inside = line.split("@@")[1].strip()
        # inside starts with -old +new
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
    if not diff_text.strip():
        return FileDiff(path=path, hunks=[])

    # crude binary detection
    if "GIT binary patch" in diff_text or "Binary files" in diff_text:
        return FileDiff(path=path, is_binary=True, hunks=[])

    lines = diff_text.splitlines()
    hunks: list[DiffHunk] = []
    cur_hunk: Optional[DiffHunk] = None

    old_ln = None
    new_ln = None

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
            # file headers (diff --git, ---/+++), index lines, etc.
            continue

        if raw.startswith("+") and not raw.startswith("+++"):
            cur_hunk.lines.append(DiffLine(kind="add", text=raw[1:], old_lineno=None, new_lineno=new_ln))
            new_ln = (new_ln + 1) if new_ln is not None else None
        elif raw.startswith("-") and not raw.startswith("---"):
            cur_hunk.lines.append(DiffLine(kind="del", text=raw[1:], old_lineno=old_ln, new_lineno=None))
            old_ln = (old_ln + 1) if old_ln is not None else None
        elif raw.startswith(" "):
            cur_hunk.lines.append(DiffLine(kind="context", text=raw[1:], old_lineno=old_ln, new_lineno=new_ln))
            old_ln = (old_ln + 1) if old_ln is not None else None
            new_ln = (new_ln + 1) if new_ln is not None else None
        else:
            # fallback for unexpected lines inside hunk
            cur_hunk.lines.append(DiffLine(kind="meta", text=raw, old_lineno=old_ln, new_lineno=new_ln))

    return FileDiff(path=path, hunks=hunks)
# filename: src/diff_monster/storage.py
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

from .models import ReviewComment


def ensure_store(root: str) -> Path:
    base = Path(root) / ".diff-monster"
    base.mkdir(parents=True, exist_ok=True)
    (base / "reviews").mkdir(parents=True, exist_ok=True)
    (base / "exports").mkdir(parents=True, exist_ok=True)
    return base


def new_review_id() -> str:
    # sortable-ish id
    return time.strftime("%Y%m%d-%H%M%S")


def review_dir(root: str, review_id: str) -> Path:
    base = ensure_store(root)
    rd = base / "reviews" / review_id
    rd.mkdir(parents=True, exist_ok=True)
    return rd


def append_comment(root: str, comment: ReviewComment) -> None:
    rd = review_dir(root, comment.review_id)
    fp = rd / "comments.jsonl"
    with fp.open("a", encoding="utf-8") as f:
        f.write(comment.model_dump_json())
        f.write("\n")


def load_comments(root: str, review_id: str, path: Optional[str] = None) -> list[ReviewComment]:
    rd = review_dir(root, review_id)
    fp = rd / "comments.jsonl"
    if not fp.exists():
        return []
    out: list[ReviewComment] = []
    with fp.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            c = ReviewComment(**obj)
            if path is None or c.path == path:
                out.append(c)
    return out


def latest_review_id(root: str) -> Optional[str]:
    base = ensure_store(root)
    reviews = sorted((base / "reviews").glob("*"))
    if not reviews:
        return None
    # directories are timestamp ids
    return reviews[-1].name
# filename: src/diff_monster/exporter.py
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Literal

from .models import ReviewComment
from .storage import ensure_store, load_comments


def export_agent_md(root: str, review_id: str) -> Path:
    base = ensure_store(root)
    out_dir = base / "exports" / review_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "agent-review.md"

    comments = load_comments(root, review_id)
    by_file: dict[str, list[ReviewComment]] = defaultdict(list)
    for c in comments:
        by_file[c.path].append(c)

    def _fmt_ctx(lines: list[str]) -> str:
        return "\n".join(lines).rstrip("\n")

    md: list[str] = []
    md.append(f"# diff-monster review bundle: {review_id}")
    md.append("")
    md.append("## Instructions")
    md.append("- Apply changes based on comments below.")
    md.append("- Prefer using the provided context and line numbers; re-locate if the file shifted.")
    md.append("")

    for path in sorted(by_file.keys()):
        md.append(f"## {path}")
        md.append("")
        for c in sorted(by_file[path], key=lambda x: (x.line, x.created_unix)):
            md.append(f"### L{c.line} ({c.side}) — {c.id}")
            md.append("")
            if c.context_before or c.context_after:
                md.append("**Context**")
                md.append("```text")
                if c.context_before:
                    md.append(_fmt_ctx(c.context_before))
                md.append(f">>> TARGET LINE: {c.line} ({c.side})")
                if c.context_after:
                    md.append(_fmt_ctx(c.context_after))
                md.append("```")
                md.append("")
            md.append("**Comment**")
            md.append("")
            md.append(c.message.strip())
            md.append("")
            if c.suggestion:
                md.append("**Suggested change**")
                md.append("```suggestion")
                md.append(c.suggestion.rstrip("\n"))
                md.append("```")
                md.append("")
        md.append("")

    out_path.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    return out_path
# filename: src/diff_monster/server.py
from __future__ import annotations

import os
import socket
from collections import defaultdict
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .git import (
    ensure_git_repo,
    repo_root,
    list_tracked_files,
    changed_files,
    get_unified_diff,
    parse_unified_diff,
    read_file_text,
)
from .models import ReviewComment
from .storage import new_review_id, append_comment, load_comments


class AddCommentIn(BaseModel):
    path: str
    side: str = "new"
    line: int
    message: str
    suggestion: Optional[str] = None


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def create_app(workdir: str, base_ref: str = "HEAD") -> tuple[FastAPI, str]:
    ensure_git_repo(workdir)
    root = repo_root(workdir)
    review_id = new_review_id()

    app = FastAPI()
    templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    files = list_tracked_files(root)
    changed = changed_files(root, base=base_ref)

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, path: Optional[str] = None):
        if not path and files:
            path = next((p for p in files if p in changed), files[0])

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
        by_line = defaultdict(list)
        for c in comments:
            by_line[(c.side, c.line)].append(c)

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "review_id": review_id,
                "base_ref": base_ref,
                "files": files,
                "changed": changed,
                "path": path,
                "file_is_changed": file_is_changed,
                "file_lines": file_lines,
                "file_diff": fd,
                "comments_by_line": by_line,
            },
        )

    @app.get("/api/state")
    def state():
        return {
            "review_id": review_id,
            "base_ref": base_ref,
            "tracked_files": len(files),
            "changed_files": len(changed),
        }

    @app.post("/api/comment")
    def add_comment(inp: AddCommentIn):
        # collect small context around the target line from current working tree
        try:
            text = read_file_text(root, inp.path)
            lines = text.splitlines()
        except Exception:
            lines = []

        i = max(0, inp.line - 1)  # 0-based
        before = lines[max(0, i - 3): i]
        after = lines[i: min(len(lines), i + 3)]

        c = ReviewComment(
            review_id=review_id,
            path=inp.path,
            side="old" if inp.side == "old" else "new",
            line=int(inp.line),
            message=inp.message,
            suggestion=inp.suggestion,
            context_before=before,
            context_after=after,
        )
        append_comment(root, c)
        return JSONResponse({"ok": True, "id": c.id})

    return app, review_id


def pick_port(port: Optional[int]) -> int:
    return int(port) if port else _free_port()
# filename: src/diff_monster/cli.py
from __future__ import annotations

import webbrowser
import uvicorn
import typer

from .git import ensure_git_repo
from .server import create_app, pick_port
from .storage import latest_review_id
from .exporter import export_agent_md

app = typer.Typer(add_completion=False)


@app.command()
def review(
    base: str = typer.Option("HEAD", "--base", help="Base ref to diff against (default: HEAD)"),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(0, "--port", help="0 = auto-pick a free port"),
):
    """Launch local web UI for reviewing git diffs and adding inline comments."""
    ensure_git_repo(".")
    fastapi_app, review_id = create_app(".", base_ref=base)
    p = pick_port(port)
    url = f"http://{host}:{p}/"
    webbrowser.open(url)
    uvicorn.run(fastapi_app, host=host, port=p, log_level="warning")


@app.command()
def export(
    latest: bool = typer.Option(True, "--latest", help="Export latest review"),
    review_id: str = typer.Option("", "--review-id", help="Explicit review id (overrides --latest)"),
    format: str = typer.Option("agent-md", "--format", help="agent-md (only format in PoC)"),
):
    """Export review comments to a bundle suitable for agentic coders."""
    if format != "agent-md":
        raise typer.BadParameter("only --format agent-md is supported in this PoC")

    rid = review_id.strip()
    if not rid:
        rid = latest_review_id(".") if latest else ""
    if not rid:
        raise typer.Exit(code=2)

    out = export_agent_md(".", rid)
    typer.echo(str(out))
<!-- filename: src/diff_monster/templates/index.html -->
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>diff-monster</title>
  <link rel="stylesheet" href="/static/app.css" />
</head>
<body>
  <div class="topbar">
    <div class="brand">diff-monster</div>
    <div class="meta">review: <code>{{ review_id }}</code> · base: <code>{{ base_ref }}</code></div>
  </div>

  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-title">Files</div>
      <div class="filelist">
        {% for f in files %}
          <a class="file {% if f == path %}active{% endif %}" href="/?path={{ f }}">
            <span class="fname">{{ f }}</span>
            {% if f in changed %}<span class="badge">changed</span>{% endif %}
          </a>
        {% endfor %}
      </div>
      <div class="hint">
        Export bundle: <code>uv run diff-monster-cli export --latest --format agent-md</code>
      </div>
    </aside>

    <main class="main">
      {% if not path %}
        <div class="empty">No file selected</div>
      {% else %}
        <div class="header">
          <div class="path"><code>{{ path }}</code></div>
          {% if file_is_changed %}<div class="state changed">changed</div>{% else %}<div class="state clean">clean</div>{% endif %}
        </div>

        {% if file_is_changed and file_diff and not file_diff.is_binary %}
          <div class="panel">
            <div class="panel-title">Diff (unified)</div>

            {% for h in file_diff.hunks %}
              <div class="hunk">
                <div class="hunk-header"><code>{{ h.header }}</code></div>
                <div class="lines">
                  {% for ln in h.lines %}
                    <div class="line kind-{{ ln.kind }}"
                         data-path="{{ path }}"
                         data-side="{{ 'new' if ln.new_lineno else 'old' }}"
                         data-line="{{ ln.new_lineno if ln.new_lineno else ln.old_lineno }}"
                         onclick="openComment(this)">
                      <div class="ln">
                        <span class="old">{{ ln.old_lineno if ln.old_lineno else '' }}</span>
                        <span class="new">{{ ln.new_lineno if ln.new_lineno else '' }}</span>
                      </div>
                      <pre class="code">{{ ln.text }}</pre>
                    </div>

                    {% set key = (('new' if ln.new_lineno else 'old'), (ln.new_lineno if ln.new_lineno else ln.old_lineno)) %}
                    {% if key in comments_by_line %}
                      <div class="comments">
                        {% for c in comments_by_line[key] %}
                          <div class="comment">
                            <div class="comment-id"><code>{{ c.id }}</code></div>
                            <div class="comment-body">{{ c.message }}</div>
                            {% if c.suggestion %}
                              <pre class="suggestion">{{ c.suggestion }}</pre>
                            {% endif %}
                          </div>
                        {% endfor %}
                      </div>
                    {% endif %}
                  {% endfor %}
                </div>
              </div>
            {% endfor %}
          </div>
        {% elif file_is_changed and file_diff and file_diff.is_binary %}
          <div class="panel"><div class="panel-title">Binary diff</div><div class="empty">Binary file; diff not shown.</div></div>
        {% endif %}

        <div class="panel">
          <div class="panel-title">File content</div>
          <div class="lines">
            {% for i in range(file_lines|length) %}
              {% set lineno = i + 1 %}
              <div class="line kind-context"
                   data-path="{{ path }}"
                   data-side="new"
                   data-line="{{ lineno }}"
                   onclick="openComment(this)">
                <div class="ln">
                  <span class="old"></span>
                  <span class="new">{{ lineno }}</span>
                </div>
                <pre class="code">{{ file_lines[i] }}</pre>
              </div>

              {% set key = ('new', lineno) %}
              {% if key in comments_by_line %}
                <div class="comments">
                  {% for c in comments_by_line[key] %}
                    <div class="comment">
                      <div class="comment-id"><code>{{ c.id }}</code></div>
                      <div class="comment-body">{{ c.message }}</div>
                      {% if c.suggestion %}
                        <pre class="suggestion">{{ c.suggestion }}</pre>
                      {% endif %}
                    </div>
                  {% endfor %}
                </div>
              {% endif %}
            {% endfor %}
          </div>
        </div>

      {% endif %}
    </main>
  </div>

  <div id="modal" class="modal hidden" onclick="closeIfBackdrop(event)">
    <div class="modal-card">
      <div class="modal-title">Add comment</div>
      <div class="modal-meta" id="modalMeta"></div>

      <label class="lbl">Comment</label>
      <textarea id="msg" class="ta" placeholder="Comment..."></textarea>

      <label class="lbl">Suggestion (optional)</label>
      <textarea id="sug" class="ta" placeholder="Suggested code..."></textarea>

      <div class="modal-actions">
        <button class="btn" onclick="submitComment()">Save</button>
        <button class="btn secondary" onclick="hideModal()">Cancel</button>
      </div>
    </div>
  </div>

  <script src="/static/app.js"></script>
</body>
</html>
/* filename: src/diff_monster/static/app.css */
:root { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
body { margin: 0; background: #0b0d10; color: #e6e6e6; }
.topbar { display:flex; justify-content:space-between; padding:10px 12px; border-bottom:1px solid #222; background:#0f1217; position:sticky; top:0; z-index:10; }
.brand { font-weight:700; }
.meta code { color:#b9d4ff; }
.layout { display:flex; height: calc(100vh - 42px); }
.sidebar { width: 360px; border-right:1px solid #222; overflow:auto; background:#0f1217; }
.sidebar-title { padding:10px 12px; font-weight:700; border-bottom:1px solid #222; }
.filelist { display:flex; flex-direction:column; }
.file { padding:8px 12px; text-decoration:none; color:#e6e6e6; display:flex; gap:8px; align-items:center; border-bottom:1px solid rgba(255,255,255,0.03); }
.file:hover { background:#131824; }
.file.active { background:#151c2b; }
.badge { font-size:12px; padding:2px 6px; border:1px solid #2a3a52; border-radius:999px; color:#b9d4ff; }
.fname { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.hint { padding:12px; font-size:12px; color:#bdbdbd; border-top:1px solid #222; }
.hint code { color:#b9d4ff; }

.main { flex:1; overflow:auto; padding:12px; }
.header { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
.state { font-size:12px; padding:2px 8px; border-radius:999px; border:1px solid #333; }
.state.changed { color:#ffd479; border-color:#5a4a1e; }
.state.clean { color:#9cff9c; border-color:#1f4a1f; }

.panel { border:1px solid #222; border-radius:10px; margin-bottom:12px; overflow:hidden; background:#0f1217; }
.panel-title { padding:10px 12px; font-weight:700; border-bottom:1px solid #222; }
.hunk-header { padding:8px 12px; border-bottom:1px solid #222; color:#bdbdbd; }
.lines { width:100%; }
.line { display:flex; gap:10px; padding:2px 12px; cursor:pointer; }
.line:hover { background:#131824; }
.ln { width:80px; display:flex; justify-content:space-between; color:#6f7a8a; user-select:none; }
.code { margin:0; white-space:pre; overflow:auto; flex:1; }
.kind-add .code { color:#b6ffb6; }
.kind-del .code { color:#ffb6b6; }
.kind-meta .code { color:#c7c7c7; font-style:italic; }

.comments { padding:6px 12px 10px 92px; border-bottom:1px solid rgba(255,255,255,0.06); }
.comment { border:1px solid #222; border-radius:10px; padding:8px 10px; background:#0b0d10; margin-top:6px; }
.comment-id code { color:#b9d4ff; }
.comment-body { margin-top:6px; white-space:pre-wrap; }
.suggestion { margin-top:8px; background:#0f1217; border:1px solid #222; border-radius:10px; padding:8px; overflow:auto; }

.empty { padding:12px; color:#bdbdbd; }

.modal { position:fixed; inset:0; background:rgba(0,0,0,0.65); display:flex; align-items:center; justify-content:center; z-index:999; }
.modal.hidden { display:none; }
.modal-card { width:min(820px, calc(100vw - 24px)); background:#0f1217; border:1px solid #222; border-radius:14px; padding:12px; }
.modal-title { font-weight:700; margin-bottom:6px; }
.modal-meta { color:#bdbdbd; margin-bottom:10px; }
.lbl { display:block; margin-top:10px; margin-bottom:6px; color:#c7c7c7; }
.ta { width:100%; min-height:90px; resize:vertical; background:#0b0d10; color:#e6e6e6; border:1px solid #222; border-radius:10px; padding:8px; box-sizing:border-box; }
.modal-actions { display:flex; gap:10px; justify-content:flex-end; margin-top:12px; }
.btn { background:#1a2540; color:#e6e6e6; border:1px solid #2a3a52; padding:8px 12px; border-radius:10px; cursor:pointer; }
.btn.secondary { background:#0b0d10; border-color:#222; }
// filename: src/diff_monster/static/app.js
let current = { path: null, side: null, line: null };

function openComment(el) {
  const path = el.getAttribute("data-path");
  const side = el.getAttribute("data-side");
  const line = el.getAttribute("data-line");
  if (!path || !side || !line) return;

  current = { path, side, line: parseInt(line, 10) };
  document.getElementById("modalMeta").textContent = `${path} · ${side} · line ${line}`;
  document.getElementById("msg").value = "";
  document.getElementById("sug").value = "";
  document.getElementById("modal").classList.remove("hidden");
}

function hideModal() {
  document.getElementById("modal").classList.add("hidden");
}

function closeIfBackdrop(ev) {
  if (ev.target && ev.target.id === "modal") hideModal();
}

async function submitComment() {
  const message = document.getElementById("msg").value.trim();
  const suggestion = document.getElementById("sug").value;
  if (!message) return;

  const res = await fetch("/api/comment", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      path: current.path,
      side: current.side,
      line: current.line,
      message,
      suggestion: suggestion && suggestion.trim() ? suggestion : null
    })
  });

  if (res.ok) window.location.reload();
}
What this PoC covers
Shows tracked files + marks files changed vs --base (default HEAD).

Renders unified diff (for changed files) and full file content.

Click any line → add comment + optional suggestion.

Stores everything under .diff-monster/ in the repo root.

export produces a single Markdown bundle for agentic coders at: .diff-monster/exports/<review_id>/agent-review.md.

What you’d likely add next (still small)
Side-by-side diff view (old/new columns).

Stable “hunk anchoring” (hash of surrounding context) so comments survive rebases.

“Suggestions as patches” (emit git apply-ready diffs).

Multi-review management (name reviews, reopen, resolve threads, etc.).





Ingen fil valgtIngen fil valgt
ChatGPT can make mistakes. Check important info. See Cookie Preferences.
