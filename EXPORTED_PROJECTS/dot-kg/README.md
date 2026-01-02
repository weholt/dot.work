# dot-kg

Knowledge graph with FTS5 search for code analysis

## Installation

### As a dot-work plugin

```bash
pip install dot-kg
```

### Standalone usage

```bash
pip install dot-kg
dot-kg --help
```

## Usage

As a dot-work plugin:

```bash
dot-work kg --help
```

As a standalone CLI:

```bash
dot-kg --help
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
