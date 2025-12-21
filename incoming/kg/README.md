# kgshred

CLI knowledge-graph "shredder" for plain text/Markdown with lossless reconstruction.

## Features

- **Span-based graph storage**: Content is stored once with byte-offset references
- **SQLite FTS5 search**: Built-in full-text search with zero extra dependencies
- **Optional semantic search**: Pluggable embedding backends (HTTP-based)
- **Lossless reconstruction**: Render any node back to original text
- **4-character IDs**: Human-friendly short IDs for quick reference

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

## Installation

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <repo-url>
cd kgtool-2
uv sync
```

### Optional Dependencies

```bash
# HTTP embedders support
uv sync --extra http

# ANN (approximate nearest neighbor) support
uv sync --extra ann

# YAML frontmatter parsing
uv sync --extra yaml

# All optional dependencies
uv sync --extra all

# Development dependencies
uv sync --extra dev
```

## Usage

```bash
# Show version
uv run kg --version

# Check database status
uv run kg status

# More commands coming soon...
```

## Development

```bash
# Run the full build pipeline
uv run python scripts/build.py

# Run with auto-fix for formatting/linting
uv run python scripts/build.py --fix

# Run tests only
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/kgshred

# Type checking
uv run mypy src/kgshred

# Include integration tests
uv run python scripts/build.py --integration all
```

## Project Structure

```
kgtool-2/
├── src/kgshred/          # Main package
│   ├── __init__.py       # Package metadata
│   ├── cli.py            # CLI entry point (thin layer)
│   └── config.py         # Configuration management
├── tests/
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── scripts/
│   └── build.py          # Build pipeline
├── pyproject.toml        # Project configuration
└── AGENTS.md             # AI agent guidelines
```

## Architecture

kgshred uses a **span-based graph** design:

1. **Documents**: Raw source files stored as BLOBs
2. **Nodes**: Spans into documents (headings, paragraphs, code blocks)
3. **Edges**: Relationships between nodes (contains, next, ref)
4. **FTS5**: Full-text search index on node content
5. **Embeddings**: Optional vector storage for semantic search

See `chat.md` for detailed architecture discussion.

## License

MIT
