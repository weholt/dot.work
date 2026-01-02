# dot-python

Python project build and scan utilities

## Installation

### As a dot-work plugin

```bash
pip install dot-python
```

### Standalone usage

```bash
pip install dot-python
dot-python --help
```

## Usage

As a dot-work plugin:

```bash
dot-work python --help
```

As a standalone CLI:

```bash
dot-python --help
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
