# agent-review 📝

Local Git diff review UI with inline comments stored under `.agent-review/` and CLI export for agentic coders.

## ⚠️ Important: Always Use `uv run`

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.
**All Python commands MUST be run using `uv run`.**

```bash
# ✅ CORRECT
uv run python scripts/build.py
uv run pytest
uv run mypy src/

# ❌ WRONG - Never run Python directly
python scripts/build.py
pytest
```

## Features

- **Browser-based diff UI** - View file changes with GitHub-like diff visualization
- **Inline comments** - Add comments and code suggestions on any line
- **Persistent storage** - Comments stored in `.agent-review/` folder within your repo
- **Agent export** - Export review bundles in markdown format optimized for AI coding assistants

## Installation

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <repo-url>
cd agent-review
uv sync
```

## Quick Start

### 1. Start a Review Session

```bash
# Launch the review UI in your browser
uv run agent-review review

# Review changes against a specific commit/branch
uv run agent-review review --base main
```

### 2. Add Comments

- Click any line in the diff view to add a comment
- Optionally include a code suggestion
- Comments are saved automatically

### 3. Export for Agent

```bash
# Export the latest review as agent-friendly markdown
uv run agent-review export --latest --format agent-md

# Hand the exported file to your AI coding assistant
```

## CLI Commands

```bash
# Start review UI
uv run agent-review review [--base HEAD] [--host 127.0.0.1] [--port 0]

# Export review comments
uv run agent-review export [--latest] [--review-id ID] [--format agent-md]
```

## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run the build pipeline (lint, type-check, test)
uv run python scripts/build.py

# Run with auto-fix for formatting/linting
uv run python scripts/build.py --fix

# Run tests only
uv run pytest

# Type checking
uv run mypy src/agent_review

# Linting
uv run ruff check src/agent_review
```

## Project Structure

```
agent-review/
├── src/agent_review/
│   ├── cli.py          # Typer CLI entry point
│   ├── config.py       # Configuration management
│   ├── models.py       # Pydantic data models
│   ├── git.py          # Git operations and diff parsing
│   ├── storage.py      # Comment persistence
│   ├── exporter.py     # Agent export functionality
│   ├── server.py       # FastAPI web server
│   ├── templates/      # Jinja2 HTML templates
│   └── static/         # CSS and JavaScript
├── tests/
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
├── scripts/
│   └── build.py        # Build pipeline
└── pyproject.toml      # Project configuration
```

## Storage Format

Comments are stored in `.agent-review/` within your repository:

```
.agent-review/
├── reviews/
│   └── 20241220-143025/
│       └── comments.jsonl
└── exports/
    └── 20241220-143025/
        └── agent-review.md
```

## License

MIT
