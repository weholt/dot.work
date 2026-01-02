# dot-container

Docker provisioning for AI coding agents

## Installation

### As a dot-work plugin

```bash
pip install dot-container
```

### Standalone usage

```bash
pip install dot-container
dot-container --help
```

## Usage

As a dot-work plugin:

```bash
dot-work container --help
```

As a standalone CLI:

```bash
dot-container --help
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
