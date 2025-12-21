# Development Guide

Guide for contributing to Regression Guard development.

## Setup Development Environment

### 1. Clone Repository

```bash
git clone https://github.com/your-username/regression-guard
cd regression-guard
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install in Development Mode

```bash
pip install -e ".[dev]"
```

This installs:
- The package in editable mode
- All development dependencies (pytest, ruff, mypy, etc.)

## Development Workflow

### Code Quality Tools

We use these tools to maintain code quality:

#### Ruff (Linting + Formatting)

```bash
# Check linting issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

#### MyPy (Type Checking)

```bash
# Check types
mypy regression_guard/

# Check specific file
mypy regression_guard/orchestrator.py
```

#### pytest (Testing)

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=regression_guard

# Run specific test file
pytest tests/test_orchestrator.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_orchestrator.py::test_orchestrator_init
```

### Pre-commit Checks

Before committing, run all checks:

```bash
# Format code
ruff format .

# Fix linting issues
ruff check --fix .

# Check types
mypy regression_guard/

# Run tests
pytest --cov=regression_guard
```

### Running All Checks

Use this command to run everything:

```bash
ruff format . && ruff check --fix . && mypy regression_guard/ && pytest --cov=regression_guard
```

## Project Structure

```
regression-guard/
├── regression_guard/          # Main package
│   ├── __init__.py           # Package init
│   ├── cli.py                # CLI entry point
│   ├── orchestrator.py       # Main workflow coordinator
│   ├── decompose.py          # Task decomposition
│   ├── capture_baseline.py   # Baseline state capture
│   ├── validate_incremental.py  # Subtask validation
│   └── validate_integration.py  # Integration validation
├── tests/                     # Test suite
│   ├── __init__.py
│   └── test_orchestrator.py  # Orchestrator tests
├── docs/                      # Documentation
│   ├── usage-guide.md
│   ├── quick-reference.md
│   ├── integration-examples.md
│   ├── installation.md
│   └── development.md         # This file
├── pyproject.toml            # Package configuration
├── README.md                 # Main documentation
├── LICENSE                   # MIT License
├── CONTRIBUTING.md           # Contribution guidelines
├── CHANGELOG.md              # Version history
└── .gitignore               # Git ignore rules
```

## Adding New Features

### 1. Create Feature Branch

```bash
git checkout -b feature/my-new-feature
```

### 2. Implement Feature

- Add code to appropriate module
- Follow existing code style
- Add type hints
- Add docstrings

### 3. Add Tests

Create tests in `tests/`:

```python
"""Tests for new feature."""

import pytest
from regression_guard.module import NewFeature


def test_new_feature():
    """Test the new feature works."""
    feature = NewFeature()
    assert feature.do_something() == expected_result
```

### 4. Run Tests

```bash
pytest tests/test_new_feature.py -v
```

### 5. Update Documentation

- Add to README.md if user-facing
- Update relevant docs in `docs/`
- Add docstrings to new code

### 6. Commit Changes

```bash
git add .
git commit -m "Add new feature: description"
```

### 7. Push and Create PR

```bash
git push origin feature/my-new-feature
```

Then create Pull Request on GitHub.

## Testing Guidelines

### Test Structure

```python
"""
Module docstring explaining what's being tested.
"""

import pytest
from your_module import YourClass


@pytest.fixture
def sample_data():
    """Fixture providing test data."""
    return {"key": "value"}


def test_basic_functionality():
    """Test description."""
    # Arrange
    instance = YourClass()
    
    # Act
    result = instance.method()
    
    # Assert
    assert result == expected
```

### Coverage Goals

- Aim for >80% coverage
- Test both success and failure cases
- Test edge cases
- Test error handling

### Running Coverage Reports

```bash
# Run with coverage
pytest --cov=regression_guard --cov-report=html

# View HTML report
open htmlcov/index.html  # On macOS
xdg-open htmlcov/index.html  # On Linux
start htmlcov/index.html  # On Windows
```

## Code Style Guidelines

### Python Style

- Follow PEP 8
- Use type hints for all functions
- Use docstrings for all public APIs
- Keep functions focused and small
- Prefer explicit over implicit

### Type Hints

```python
from typing import Any
from pathlib import Path


def process_file(file_path: Path, options: dict[str, Any]) -> bool:
    """
    Process a file with given options.
    
    Args:
        file_path: Path to file
        options: Processing options
        
    Returns:
        True if successful, False otherwise
    """
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def validate_task(task_id: str, strict: bool = False) -> dict[str, Any]:
    """
    Validate a task and return results.
    
    Args:
        task_id: Unique task identifier
        strict: If True, fail on warnings
        
    Returns:
        Dictionary containing validation results
        
    Raises:
        ValueError: If task_id is invalid
        FileNotFoundError: If task directory not found
    """
    ...
```

## Debugging

### Using pdb

```python
import pdb; pdb.set_trace()
```

### Using pytest debugging

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger at test start
pytest --trace
```

### Logging

Add debug logging:

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
```

Run with logging:

```bash
pytest -v --log-cli-level=DEBUG
```

## Release Process

### 1. Update Version

Edit `pyproject.toml`:

```toml
[project]
version = "0.2.0"
```

And `regression_guard/__init__.py`:

```python
__version__ = "0.2.0"
```

### 2. Update CHANGELOG.md

Document changes in CHANGELOG.md following Keep a Changelog format.

### 3. Commit Version Bump

```bash
git add pyproject.toml regression_guard/__init__.py CHANGELOG.md
git commit -m "Bump version to 0.2.0"
```

### 4. Create Tag

```bash
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

### 5. Build Package

```bash
pip install build
python -m build
```

### 6. Upload to PyPI

```bash
pip install twine
twine upload dist/*
```

## Common Tasks

### Adding a New CLI Command

1. Edit `regression_guard/cli.py`
2. Add new subparser
3. Add handler method in `RegressionOrchestrator`
4. Update help text
5. Add tests
6. Update documentation

### Adding a New Validation Check

1. Edit `regression_guard/validate_incremental.py` or `validate_integration.py`
2. Add validation method
3. Update report generation
4. Add tests
5. Document in usage guide

### Adding Integration Example

1. Create example in `docs/integration-examples.md`
2. Test the example
3. Link from README.md

## Getting Help

- Check existing issues on GitHub
- Review documentation in `docs/`
- Ask in GitHub Discussions
- Refer to CONTRIBUTING.md

## Additional Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
