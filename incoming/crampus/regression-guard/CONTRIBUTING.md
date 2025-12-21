# Contributing to Regression Guard

We welcome contributions! This guide will help you get started.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/regression-guard
cd regression-guard
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
```

4. Run tests:
```bash
pytest
```

## Code Style

We use:
- **ruff** for linting and formatting
- **mypy** for type checking
- **pytest** for testing

Run quality checks:
```bash
# Format code
ruff format .

# Check linting
ruff check .

# Type check
mypy regression_guard/

# Run tests
pytest --cov=regression_guard
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Testing Guidelines

- Write tests for all new features
- Maintain test coverage above 80%
- Use descriptive test names
- Include both positive and negative test cases

## Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Update usage guides in `docs/` as needed

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a git tag
4. Push to PyPI (maintainers only)

## Questions?

Open an issue or start a discussion on GitHub.
