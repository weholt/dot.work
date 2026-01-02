# dot-version

Date-based version management

## Installation

### As a dot-work plugin

```bash
pip install dot-version
```

### Standalone usage

```bash
pip install dot-version
dot-version --help
```

## Usage

As a dot-work plugin:

```bash
dot-work version --help
```

As a standalone CLI:

```bash
dot-version --help
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
