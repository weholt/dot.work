# Installation Guide

## Requirements

- Python 3.10 or higher
- pytest (for running tests)
- A Python project with tests

## Installation Methods

### Option 1: Install from PyPI (Recommended)

```bash
pip install regression-guard
```

### Option 2: Install from Source

```bash
git clone https://github.com/your-username/regression-guard
cd regression-guard
pip install .
```

### Option 3: Development Installation

For contributing to Regression Guard:

```bash
git clone https://github.com/your-username/regression-guard
cd regression-guard
pip install -e ".[dev]"
```

This installs in "editable" mode with development dependencies.

## Verifying Installation

Test that installation was successful:

```bash
# Check the command is available
regression-guard --help

# Check version
python -c "import regression_guard; print(regression_guard.__version__)"
```

You should see the help message and version number.

## Project Setup

### 1. Navigate to Your Project

```bash
cd /path/to/your/python/project
```

### 2. Ensure pytest is Installed

Regression Guard requires pytest to run tests:

```bash
pip install pytest pytest-cov
```

### 3. Verify Tests Run

Make sure your existing tests work:

```bash
pytest tests/
```

### 4. Optional: Coverage Configuration

Create `pytest.ini` or add to `pyproject.toml`:

```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "--cov=your_package --cov-report=xml"
```

### 5. Start Using Regression Guard

```bash
regression-guard start "Your first task"
```

This creates the `.work/tasks/` directory structure.

## Troubleshooting

### Command Not Found

If `regression-guard` command isn't found:

1. Check pip installation location:
```bash
pip show regression-guard
```

2. Add pip's bin directory to PATH:
```bash
# On Unix/Linux/macOS
export PATH="$HOME/.local/bin:$PATH"

# On Windows
set PATH=%APPDATA%\Python\Scripts;%PATH%
```

3. Or use as Python module:
```bash
python -m regression_guard.cli start "Task"
```

### Import Errors

If you get import errors:

1. Verify installation:
```bash
pip list | grep regression-guard
```

2. Reinstall:
```bash
pip uninstall regression-guard
pip install regression-guard
```

### Permission Errors

On Unix systems, you may need user installation:

```bash
pip install --user regression-guard
```

Or use a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install regression-guard
```

## Next Steps

- Read the [Usage Guide](usage-guide.md)
- Check [Integration Examples](integration-examples.md)
- See [Quick Reference](quick-reference.md)

## Uninstallation

```bash
pip uninstall regression-guard
```

Note: This doesn't remove `.work/` directory - remove manually if desired:

```bash
rm -rf .work/  # Unix/Linux/macOS
rmdir /s .work  # Windows
```
