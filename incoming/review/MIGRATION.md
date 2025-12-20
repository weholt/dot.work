# agent-review Migration Guide

> **Purpose**: Integrate agent-review as a `review` subcommand in the target project.

---

## Table of Contents

1. [Overview](#overview)
2. [Main Goal](#main-goal)
3. [Feature Deep Dive](#feature-deep-dive)
   - [CLI Interface](#cli-interface)
   - [Web UI](#web-ui)
   - [Git Integration](#git-integration)
   - [Comment System](#comment-system)
   - [Export System](#export-system)
4. [Architecture](#architecture)
5. [Migration Plan](#migration-plan)
6. [Dependencies](#dependencies)
7. [Configuration](#configuration)

---

## Overview

**agent-review** is a local Git diff review tool designed for AI-assisted development workflows. It provides:

- A **web-based UI** for reviewing uncommitted Git changes
- **Inline commenting** with optional code suggestions
- **Markdown export** optimized for AI agents to consume and act upon

The tool bridges the gap between human code review and AI code modification by capturing structured feedback that AI agents can parse and apply.

### Key Value Proposition

| For Humans | For AI Agents |
|------------|---------------|
| Visual diff review in browser | Structured markdown bundle |
| Click-to-comment interface | Line numbers + context |
| Side-by-side or unified diff | Code suggestions ready to apply |
| Syntax highlighting | File-grouped, sorted output |

---

## Main Goal

**Transform human review feedback into machine-actionable instructions.**

The workflow:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Git Changes   │────▶│   Web Review    │────▶│  Export Bundle  │
│  (uncommitted)  │     │   (comments)    │     │  (agent-md)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │   AI Agent      │
                                                │  applies fixes  │
                                                └─────────────────┘
```

### Target Integration

In the target project, this becomes:

```bash
# Launch review UI
myproject review

# Export comments for AI consumption
myproject review export
```

---

## Feature Deep Dive

### CLI Interface

#### Command: `review` (default)

Launches the web-based review interface.

```bash
review [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--base-ref` | string | `HEAD` | Git ref to diff against |
| `--host` | string | `127.0.0.1` | Server bind address |
| `--port` | int | `0` | Port (0 = auto-select free port) |

**Behavior:**
1. Validates current directory is a Git repository
2. Creates new review session with timestamp ID (e.g., `20251220-143052`)
3. Starts FastAPI server on specified host/port
4. Auto-opens browser to the UI
5. Runs until terminated (Ctrl+C)

#### Command: `review export`

Exports review comments to a markdown bundle.

```bash
review export [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--latest` | flag | `True` | Export most recent review |
| `--id` | string | `""` | Specific review ID to export |
| `--format` | choice | `agent-md` | Export format (only `agent-md` supported) |

**Exit Codes:**
- `0`: Success
- `1`: Unsupported format
- `2`: No reviews found

---

### Web UI

The web interface is a single-page application with three main sections:

#### Header Bar

| Element | Purpose |
|---------|---------|
| Review ID | Shows current session identifier |
| Base Ref | Shows the Git ref being compared against |
| Keyboard Hints | Displays navigation shortcuts |
| Theme Toggle | Cycles through Catppuccin color schemes |

#### File Browser (Left Sidebar)

A hierarchical tree view of all repository files:

- **Folder nodes**: Collapsible, show aggregate change indicator
- **File nodes**: Show file type icon + modification badge
- **Change indicators**: Blue dot on folders, "M" badge on files
- **State persistence**: Expansion state saved to localStorage

**File Type Icons** (emoji-based):
```
.py    → 🐍    .js/.ts  → 📜    .html   → 🌐
.css   → 🎨    .json    → 📋    .md     → 📝
.yaml  → ⚙️    .sh      → 💻    default → 📄
```

#### Main Content Panel

Two view modes available:

**1. Diff View** (for changed files)
- Unified view: Single column with `+`/`-` line prefixes
- Split view: Side-by-side old/new columns
- Hunk headers displayed (e.g., `@@ -10,5 +10,7 @@`)
- Line statistics: `+5 / -3` in header

**2. File View** (for unchanged files)
- Full file content display
- Syntax highlighting via highlight.js
- Catppuccin Mocha color theme

**Supported Languages for Syntax Highlighting:**
Python, JavaScript, TypeScript, HTML, CSS, JSON, Markdown, YAML, TOML, Bash, SQL, Rust, Go, Java, Ruby, PHP, C, C++, Swift, Kotlin

#### Comment Interface

- **Trigger**: Click line number or hover `+` button
- **Modal**: Appears with form fields
- **Fields**:
  - Message (required): Free-text comment
  - Suggestion (optional): Code to replace the line
- **Display**: Comments appear inline below the target line

#### Keyboard Navigation

| Key | Action |
|-----|--------|
| `j` | Next file in list |
| `k` | Previous file in list |
| `n` | Next changed file |
| `p` | Previous changed file |
| `Escape` | Close modal dialog |

#### Theming

Four Catppuccin themes available:
1. **Mocha** (default) - Dark, warm
2. **Macchiato** - Dark, neutral
3. **Frappé** - Medium, cool
4. **Latte** - Light

Theme preference persisted in localStorage.

---

### Git Integration

Core module: `git.py`

#### Repository Operations

| Function | Purpose |
|----------|---------|
| `ensure_git_repo(path)` | Validate path is inside a Git repo |
| `repo_root(path)` | Get repository root directory |

#### File Listing

| Function | Purpose |
|----------|---------|
| `list_tracked_files(root)` | All Git-tracked files |
| `list_all_files(root)` | All files (with ignore patterns) |
| `changed_files(root, base_ref)` | Files with uncommitted changes |

**Ignored Patterns** (for `list_all_files`):
```python
IGNORE_DIRS = {
    ".git", ".hg", ".svn",           # VCS
    "__pycache__", ".pytest_cache",   # Python
    ".mypy_cache", ".ruff_cache",     # Linters
    "node_modules",                   # Node.js
    ".venv", "venv", "env",           # Virtual envs
    ".tox", ".nox",                   # Test runners
    "dist", "build", "*.egg-info",    # Build outputs
    ".agent-review", "htmlcov",       # Tool outputs
    ".coverage"
}
```

#### File Content

| Function | Purpose |
|----------|---------|
| `read_file_text(root, path)` | Read file with path traversal protection |

**Security**: Blocks paths containing `..` or starting with `/`.

#### Diff Operations

| Function | Purpose |
|----------|---------|
| `get_unified_diff(root, path, base)` | Raw unified diff string |
| `parse_unified_diff(diff_text)` | Parse into structured `FileDiff` model |

**Diff Parsing Features:**
- Extracts hunk headers with line numbers
- Classifies lines: `add`, `del`, `context`, `meta`
- Tracks both old and new line numbers
- Handles binary file markers

---

### Comment System

#### Data Model

```python
class ReviewComment(BaseModel):
    id: str                           # 12-char hex (auto-generated)
    review_id: str                    # Session ID (e.g., "20251220-143052")
    path: str                         # Relative file path
    side: Literal["new", "old"]       # Which diff side
    line: int                         # Line number
    created_unix: float               # Unix timestamp (auto-generated)
    message: str                      # Comment text
    suggestion: str | None            # Optional code replacement
    context_before: list[str]         # 3 lines before target
    context_after: list[str]          # 3 lines after target
```

#### Storage Format

**Directory Structure:**
```
.agent-review/
└── reviews/
    └── {review_id}/
        └── comments.jsonl
```

**JSONL Format** (one JSON object per line):
```json
{"id":"abc123def456","review_id":"20251220-143052","path":"src/main.py","side":"new","line":42,"created_unix":1734712252.123,"message":"Add error handling","suggestion":"try:\n    result = process()\nexcept Error:\n    handle()","context_before":["def foo():","\treturn bar",""],"context_after":["\tpass","","# end"]}
```

**Benefits:**
- Append-only writes (no corruption on crash)
- Easy to parse line-by-line
- Human-readable when formatted

#### Storage Operations

| Function | Purpose |
|----------|---------|
| `ensure_store(root)` | Create directory structure |
| `new_review_id()` | Generate timestamp-based ID |
| `review_dir(root, review_id)` | Get/create review directory |
| `append_comment(root, comment)` | Add comment to JSONL |
| `load_comments(root, review_id, path?)` | Load comments (optional filter) |
| `latest_review_id(root)` | Get most recent review ID |

---

### Export System

Core module: `exporter.py`

#### Export Format: `agent-md`

A structured markdown format designed for AI agent consumption.

**Structure:**
```markdown
# agent-review bundle: {review_id}

## Instructions

- Apply changes based on comments below.
- Prefer using the provided context and line numbers.
- Re-locate if the file has shifted since the review.

## {file_path}

### L{line} ({side}) — {comment_id}

**Context**
```text
# line N-3
# line N-2
# line N-1
>>> TARGET LINE: {line} ({side})
# line N+1
# line N+2
# line N+3
```

**Comment**

{message}

**Suggested change**
```suggestion
{suggestion}
```
```

**Features:**
- Groups comments by file path
- Sorts by line number within each file
- Includes 3 lines of context before/after
- Target line marked with `>>>` prefix
- Code suggestions in fenced blocks
- Unique comment ID for tracking

#### Export Output Location

```
.agent-review/
└── exports/
    └── {review_id}/
        └── agent-review.md
```

---

## Architecture

### Module Dependency Graph

```
┌─────────┐
│  cli.py │  Entry point (thin layer)
└────┬────┘
     │
     ▼
┌─────────────┐     ┌──────────────┐
│  server.py  │────▶│  storage.py  │
└──────┬──────┘     └──────┬───────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌──────────────┐
│   git.py    │     │  models.py   │
└─────────────┘     └──────────────┘
       │                   ▲
       └───────────────────┘

┌──────────────┐
│ exporter.py  │────▶ storage.py, models.py
└──────────────┘

┌──────────────┐
│  config.py   │  (used by all modules)
└──────────────┘
```

### File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `cli.py` | ~50 | Typer CLI entry point |
| `server.py` | ~150 | FastAPI web server + API |
| `git.py` | ~300 | Git operations |
| `models.py` | ~50 | Pydantic data models |
| `storage.py` | ~100 | Comment persistence |
| `exporter.py` | ~60 | Markdown export |
| `config.py` | ~30 | Configuration |
| `templates/index.html` | ~600 | Web UI template |
| `static/app.css` | ~200 | Custom styles |
| `static/app.js` | ~100 | UI interactions |

---

## Migration Plan

### Step 1: Copy Core Modules

Copy these files to target project's source directory:

```
src/agent_review/
├── git.py         → src/{target}/review/git.py
├── models.py      → src/{target}/review/models.py
├── storage.py     → src/{target}/review/storage.py
├── exporter.py    → src/{target}/review/exporter.py
├── server.py      → src/{target}/review/server.py
├── config.py      → src/{target}/review/config.py
└── __init__.py    → src/{target}/review/__init__.py (new)
```

### Step 2: Copy Static Assets

```
src/agent_review/
├── templates/
│   └── index.html → src/{target}/review/templates/index.html
└── static/
    ├── app.css    → src/{target}/review/static/app.css
    └── app.js     → src/{target}/review/static/app.js
```

### Step 3: Update Import Paths

In all copied files, replace:
```python
# Before
from agent_review.models import ReviewComment
from agent_review import git

# After
from {target}.review.models import ReviewComment
from {target}.review import git
```

### Step 4: Integrate CLI Commands

Add to target project's CLI (e.g., `cli.py`):

```python
import typer
from {target}.review import server, exporter, storage

app = typer.Typer()
review_app = typer.Typer(help="Code review with AI export")
app.add_typer(review_app, name="review")

@review_app.callback(invoke_without_command=True)
def review_main(
    ctx: typer.Context,
    base_ref: str = typer.Option("HEAD", help="Base ref to diff against"),
    host: str = typer.Option("127.0.0.1", help="Server host"),
    port: int = typer.Option(0, help="Server port"),
):
    """Launch review UI for uncommitted changes."""
    if ctx.invoked_subcommand is None:
        server.main(base_ref=base_ref, host=host, port=port)

@review_app.command()
def export(
    latest: bool = typer.Option(True, help="Export latest review"),
    review_id: str = typer.Option("", "--id", help="Specific review ID"),
    fmt: str = typer.Option("agent-md", "--format", help="Export format"),
):
    """Export review comments for AI consumption."""
    if fmt != "agent-md":
        raise typer.Exit(1)
    
    root = git.repo_root(Path.cwd())
    rid = review_id or storage.latest_review_id(root)
    if not rid:
        raise typer.Exit(2)
    
    output = exporter.export_agent_md(root, rid)
    print(output)
```

### Step 5: Add Dependencies

Add to `pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing ...
    "fastapi>=0.115.0",
    "uvicorn>=0.32.0",
    "jinja2>=3.1.0",
]
```

### Step 6: Update Configuration

Rename environment variables (optional):

| Current | Target |
|---------|--------|
| `AGENT_REVIEW_STORAGE_DIR` | `{PROJECT}_REVIEW_STORAGE_DIR` |
| `AGENT_REVIEW_BASE_REF` | `{PROJECT}_REVIEW_BASE_REF` |
| `AGENT_REVIEW_HOST` | `{PROJECT}_REVIEW_HOST` |
| `AGENT_REVIEW_PORT` | `{PROJECT}_REVIEW_PORT` |

Update `config.py` accordingly.

### Step 7: Update Storage Path (Optional)

To integrate with `.work/` structure:

```python
# config.py
@dataclass
class Config:
    storage_dir: str = ".work/reviews"  # Changed from ".agent-review"
    ...
```

### Step 8: Register Package Data

Ensure templates and static files are included in the package:

```toml
# pyproject.toml
[tool.hatch.build.targets.wheel]
packages = ["src/{target}"]

[tool.hatch.build.targets.wheel.force-include]
"src/{target}/review/templates" = "{target}/review/templates"
"src/{target}/review/static" = "{target}/review/static"
```

Or with setuptools:

```toml
[tool.setuptools.package-data]
"{target}.review" = ["templates/*.html", "static/*.css", "static/*.js"]
```

---

## Dependencies

### Runtime Dependencies

| Package | Version | Purpose | Notes |
|---------|---------|---------|-------|
| `typer` | ≥0.12.3 | CLI framework | Likely already present |
| `rich` | ≥13.9.0 | Terminal formatting | Typer dependency |
| `pydantic` | ≥2.6.0 | Data models | Likely already present |
| `python-dotenv` | ≥1.0.1 | Env config | Likely already present |
| `fastapi` | ≥0.115.0 | Web framework | **New** |
| `uvicorn` | ≥0.32.0 | ASGI server | **New** |
| `jinja2` | ≥3.1.0 | HTML templates | **New** |
| `pyyaml` | ≥6.0.0 | YAML support | Optional |

### External CDN Dependencies

The web UI loads these from CDN:

| Resource | URL | Purpose |
|----------|-----|---------|
| Tailwind CSS | `cdn.tailwindcss.com` | Styling |
| highlight.js | `cdnjs.cloudflare.com/.../highlight.min.js` | Syntax highlighting |
| Catppuccin theme | `cdn.jsdelivr.net/.../catppuccin-mocha.min.css` | Editor colors |

**Considerations:**
- Works offline? No (requires internet for first load, then cached)
- Bundle locally? Optional, increases package size (~200KB)
- Alternative? Use pre-built CSS instead of Tailwind browser build

### Python Version

- **Minimum**: Python 3.11
- **Reason**: Uses `tomllib` (3.11+), type syntax features

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_REVIEW_STORAGE_DIR` | `.agent-review` | Where to store reviews |
| `AGENT_REVIEW_BASE_REF` | `HEAD` | Default comparison ref |
| `AGENT_REVIEW_HOST` | `127.0.0.1` | Default server host |
| `AGENT_REVIEW_PORT` | `0` | Default server port |

### Config Class

```python
from dataclasses import dataclass
from python_dotenv import load_dotenv
import os

@dataclass
class Config:
    storage_dir: str = ".agent-review"
    default_base_ref: str = "HEAD"
    server_host: str = "127.0.0.1"
    server_port: int = 0

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        return cls(
            storage_dir=os.getenv("AGENT_REVIEW_STORAGE_DIR", ".agent-review"),
            default_base_ref=os.getenv("AGENT_REVIEW_BASE_REF", "HEAD"),
            server_host=os.getenv("AGENT_REVIEW_HOST", "127.0.0.1"),
            server_port=int(os.getenv("AGENT_REVIEW_PORT", "0")),
        )
```

### Storage Structure

```
{storage_dir}/
├── reviews/
│   ├── 20251220-143052/
│   │   └── comments.jsonl
│   └── 20251220-150000/
│       └── comments.jsonl
└── exports/
    └── 20251220-143052/
        └── agent-review.md
```

---

## Testing Considerations

### Unit Tests to Migrate

| Test File | Coverage |
|-----------|----------|
| `test_git.py` | 17 tests |
| `test_models.py` | 16 tests |
| `test_storage.py` | 12 tests |
| `test_exporter.py` | 6 tests |
| `test_config.py` | 5 tests |

### Integration Tests

| Test File | Coverage |
|-----------|----------|
| `test_server.py` | 10 tests (5 require integration marker) |

### Fixtures to Migrate

- `tmp_git_repo`: Creates temporary Git repository
- `sample_comments`: Generates test comment data

---

## Checklist

### Pre-Migration

- [ ] Verify target project has Python ≥3.11
- [ ] Check for dependency conflicts (especially pydantic version)
- [ ] Decide on storage location strategy
- [ ] Decide on CDN vs local asset bundling

### Migration

- [ ] Copy core Python modules
- [ ] Copy templates and static files
- [ ] Update all import paths
- [ ] Add CLI integration
- [ ] Add new dependencies to pyproject.toml
- [ ] Register package data for templates/static
- [ ] Update configuration variables

### Post-Migration

- [ ] Run full test suite
- [ ] Verify web UI loads correctly
- [ ] Test comment creation and persistence
- [ ] Test export command
- [ ] Update documentation
- [ ] Remove standalone agent-review references

---

*Generated: 2025-12-20*
