# dot-issues

SQLite-based issue tracking for autonomous agents

## Installation

### As a dot-work plugin

```bash
pip install dot-issues
```

### Standalone usage

```bash
pip install dot-issues
dot-issues --help
```

## Usage

As a dot-work plugin:

```bash
dot-work db-issues --help
```

As a standalone CLI:

```bash
dot-issues --help
```

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linting
ruff check src/
mypy src/

# Build package
hatch build
```

## License

MIT
