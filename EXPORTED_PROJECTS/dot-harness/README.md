# dot-harness

Claude Agent SDK integration

## Installation

### As a dot-work plugin

```bash
pip install dot-harness
```

### Standalone usage

```bash
pip install dot-harness
dot-harness --help
```

## Usage

As a dot-work plugin:

```bash
dot-work harness --help
```

As a standalone CLI:

```bash
dot-harness --help
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
