# dot-git

Git history analysis and complexity metrics

## Installation

### As a dot-work plugin

```bash
pip install dot-git
```

### Standalone usage

```bash
pip install dot-git
dot-git --help
```

## Usage

As a dot-work plugin:

```bash
dot-work git --help
```

As a standalone CLI:

```bash
dot-git --help
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
