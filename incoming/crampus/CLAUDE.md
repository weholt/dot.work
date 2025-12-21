# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This is a multi-project Python workspace called "crampus" containing several independent tools:

### Project Overview

- **birdseye** (`/birdseye/`) - Project scanning tool that generates concise overviews and structured JSON datasets from codebases
- **builder** (`/builder/`) - Comprehensive build pipeline for Python projects with quality checks (formatter, linter, type checker, testing, security scanning)
- **regression-guard** (`/regression-guard/`) - Multi-agent iterative validation system that prevents code regressions by breaking tasks into atomic subtasks
- **kgtool** (`/kgtool/`) - Knowledge graph extraction tool for converting markdown documentation into topic-based context for LLMs
- **repo-agent** (`/repo-agent/`) - Configurable tool that runs LLM-powered code agents in Docker to automatically modify repositories and create pull requests

Each project is a separate Python package with its own `pyproject.toml` and can be developed and tested independently.

## Common Development Commands

### Testing

All projects use pytest for testing:

```bash
# Run tests for any project
cd <project-directory>
pytest

# Run tests with coverage
pytest --cov=<package_name> --cov-report=html

# Run specific test file
pytest tests/test_specific.py
```

### Code Quality

All projects are configured with ruff (linting + formatting) and mypy (type checking):

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy <package_name>/

# Auto-fix linting issues
ruff check . --fix
```

### Installation

Each project can be installed in development mode:

```bash
cd <project-directory>
pip install -e ".[dev]"

# Or with uv if available
uv sync --extra test
```

## Project-Specific Commands

### Birdseye

```bash
# Install and run
pip install .
birdseye <path-to-project> <path-to-output>

# Run demo
birdseye samples/demo_project samples/demo_output
```

### Builder (Python Project Builder)

```bash
# Install and run
pip install .
pybuilder

# With options
pybuilder --verbose --fix --coverage-threshold 80

# Clean build artifacts
pybuilder --clean
```

### Regression Guard

```bash
# Install and run
pip install .
regression-guard start "Task description"
regression-guard validate <subtask-id>
regression-guard finalize <task-id>
```

### KGTool (Knowledge Graph Tool)

```bash
# Install and run
pip install .
kgtool build --input doc.md --output kg_output
kgtool extract --topic frontend --graph kg_output/graph.json --output context.md

# Discover topics
kgtool discover-topics --input doc.md --output topics.json --num-topics 5
```

### Repo-Agent

```bash
# Install and run
pip install .
repo-agent init instructions.md
repo-agent validate instructions.md
repo-agent run instructions.md
```

## Development Workflow

1. **Navigate to the specific project directory** you want to work on
2. **Install dependencies** with `pip install -e ".[dev]"`
3. **Run tests** to ensure everything works: `pytest`
4. **Make your changes**
5. **Run linting and formatting**: `ruff check . --fix && ruff format .`
6. **Run tests again**: `pytest`
7. **Type check**: `mypy <package_name>/`

## Architecture Notes

### Common Patterns
- All projects use Python 3.10+ with modern typing
- Typer for CLI interfaces (where used)
- Pydantic for data validation and configuration
- Structured logging and error handling
- Comprehensive test coverage with pytest

### Tool Integration
- The tools can work together: use `birdseye` to analyze a project, `kgtool` to extract context from documentation, `repo-agent` to make automated changes, and `regression-guard` to validate those changes
- `builder` can be used to ensure code quality across all projects

## Configuration Files

Each project has standardized configuration in their `pyproject.toml`:
- **ruff** - Line length: 120, Python 3.10+ target
- **mypy** - Strict type checking enabled
- **pytest** - Coverage reporting, timeout handling
- **coverage** - Excludes tests and build artifacts

## Testing Data

- `birdseye/` - Contains sample projects for testing
- `kgtool/tests/data/` - Comprehensive test documents including enterprise specs and edge cases