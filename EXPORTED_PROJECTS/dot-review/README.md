# dot-review

Interactive code review with AI-friendly export

## Installation

### As a dot-work plugin

```bash
pip install dot-review
```

### Standalone usage

```bash
pip install dot-review
dot-review --help
```

## Usage

As a dot-work plugin:

```bash
dot-work review --help
```

As a standalone CLI:

```bash
dot-review --help
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
