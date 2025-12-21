# Contributing to Python Project Builder

We welcome contributions! This guide will help you get started.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/python-project-builder
cd python-project-builder
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
mypy builder/

# Run tests
pytest --cov=builder
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Run the builder on itself: `pybuilder`
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Testing Guidelines

- Write tests for all new features
- Maintain test coverage above 70%
- Use descriptive test names
- Include both positive and negative test cases
- Test edge cases

## Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Update usage guides in `docs/` as needed
- Include examples in docstrings

## Adding New Build Steps

To add a new build step:

1. Add a method to `BuildRunner` class in `builder/runner.py`:
```python
def new_check(self) -> bool:
    """Description of the new check."""
    self.print_step("New Check Name")

    # Your check logic here
    success = True

    self.print_result(success, "New Check Name")
    return success
```

2. Add the step to `run_full_build()`:
```python
steps = [
    # ... existing steps ...
    ("New Check", self.new_check),
]
```

3. Add tests in `tests/test_runner.py`
4. Update documentation in `README.md`

## Release Process

1. Update version in `pyproject.toml` and `builder/__init__.py`
2. Update CHANGELOG.md
3. Create a git tag
4. Push to PyPI (maintainers only)

## Questions?

Open an issue or start a discussion on GitHub.
