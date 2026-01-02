# dot-overview

Codebase overview generation with AST parsing

## Installation

### As a dot-work plugin

```bash
pip install dot-overview
```

### Standalone usage

```bash
pip install dot-overview
dot-overview --help
```

## Usage

As a dot-work plugin:

```bash
dot-work overview --help
```

As a standalone CLI:

```bash
dot-overview --help
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
