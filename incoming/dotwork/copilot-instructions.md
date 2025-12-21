# Solace Development Guide

## General instructions
- **IMPORTANT** Do not create summaries or explainations. 
- **NO FUCKING SUMMARY DOCUMENTS**
- Focus on writing code, not talking.
- **NEVER** use `python -c` commands with multi-line code in terminal - it hangs the terminal
- Use separate Python files or simple single-line commands only
- **NEVER** print code to the terminal that should go into a file. Write directly to file. It hangs the terminal and stops the process.

## Project Architecture

Solace is a unified **MCP (Model Context Protocol) server** with **RAG (Retrieval-Augmented Generation)** capabilities, plus **HTML-to-Markdown** conversion tools. Key components:

- **`solace/server.py`** - Unified FastMCP server with automatic local/Docker environment detection
- **`solace/rag_index.py`** - ChromaDB-based vector indexing (with fallback to `minimal_rag.py`)
- **`solace/cli.py`** - Command-line interface using Typer
- **`build.py`** - Comprehensive quality pipeline (formatting, linting, tests, coverage)
- **Docker multi-stage build** - Optimized Python 3.13-slim with uv package manager
- **`solace/docs`** - The sole folder for solace markdown documentation. `/docs` are used for generated html by the build script. **DO NOT** write markdown files into `/docs` directly.

## Development Workflows

### Essential Commands (ALWAYS use `uv`)
```bash
uv sync                    # Install dependencies
uv run python build.py    # Full quality pipeline (format, lint, type-check, test)
uv run python build.py --fix --verbose  # Auto-fix issues with detailed output
uv run solace server      # Start MCP server locally
uv run pytest tests/      # Run tests only
```

### Docker Development
```bash
docker-compose up -d       # Start containerized server
# Exposes ports 8000 (MCP) and 8001 (web interface)
```

## Key Patterns & Conventions

### Environment-Aware Configuration
- Server automatically detects Docker vs local environment
- Uses different RAG implementations based on available dependencies
- Configuration via `.env` file with sensible Docker defaults

### Quality Standards (Enforced by build.py)
- **70%+ test coverage** required
- **5-second test timeout** for all tests
- **Ruff** for linting + formatting (replaces black/isort)
- **MyPy** type checking with relaxed config for BeautifulSoup complexity
- Security checks via `ruff --select S`

### MCP Tool Pattern
Tools follow this structure in `server.py`:
```python
@mcp.tool()
def tool_name(param: str) -> str:
    """Tool description for MCP client."""
    # Implementation here
```

Current tools: `ping`, `search_docs`, `answer_question`, `add_document`, `refresh_index`, `list_indexed_docs`

### Error Handling & Fallbacks
- RAG system gracefully degrades: full → minimal → TF-IDF based on dependencies
- Docker builds with minimal dependency set using `[docker]` extra
- Test imports handle missing optional dependencies

## File Organization Logic

- **`solace/`** - Main package
- **`data/`** - Markdown documents for RAG indexing
- **`tests/`** - All tests with strict timeout enforcement
- **`.env`** - Environment config (copied to Docker if exists)

## Integration Points

- **MCP Protocol** - FastMCP framework handles routing and tool registration
- **ChromaDB** - Vector storage with sentence-transformers embedding
- **FastAPI** - HTTP endpoints alongside MCP interface
- **Docker Health Checks** - Built-in `curl` probes on port 8000

## Common Pitfalls

- Always use `uv run` prefix for Python commands (never direct python)
- Tests must complete within 5 seconds (use minimal fixtures)
- MyPy ignores `solace.html2markdown.converter` due to BeautifulSoup complexity
- Docker uses different defaults (HOST=0.0.0.0 vs localhost)

## Development guide
- Run `uv run build.py` after each substantial change
    - Iterate until all checks pass
    - Write tests until coverage is 70%+
- Use `uv run build.py --fix` to auto-fix formatting/linting issues
- Add tests for new features in `tests/`
- Follow existing code style and patterns
- **PORTS** should be configurable from `.env`.
    - Provide good defaults, but never hardcode values
- **MANDATORY** **IMPORTS** ALWAYS at the top of the file, NEVER inline
    - Use conditional imports at module level if needed (try/except at top)
    - Never use inline imports inside functions or methods

**IMPORTANT** ALL documentation and summaries aimed at human readers written to file MUST be in the `./docs` folder. ALL documentation meant for the agent or temporary notes MUST be created in the `./project-docs/agent` folder.

