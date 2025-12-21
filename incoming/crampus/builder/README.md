# Python Project Builder

**Comprehensive build pipeline for Python projects with quality checks**

A standalone build tool that automates code quality checks, testing, and documentation building for Python projects. Perfect for CI/CD pipelines and local development workflows.

## Features

- 🎨 **Code Formatting** - Automatic formatting with ruff
- 🔍 **Linting** - Code quality checks with ruff
- 🔒 **Type Checking** - Static type analysis with mypy
- 🧪 **Testing** - Comprehensive test suite with pytest and coverage
- 📊 **Static Analysis** - Optional advanced analysis (complexity, dead code, duplication)
- 🔐 **Security Scanning** - Security vulnerability detection
- 📚 **Documentation** - Automatic documentation building with MkDocs
- 🎯 **Configurable** - Flexible configuration options
- 🚀 **Fast** - Optimized for speed with parallel execution where possible

## Installation

### From PyPI (when published)

```bash
pip install python-project-builder
```

### From Source

```bash
git clone https://github.com/your-username/python-project-builder
cd python-project-builder
pip install .
```

### Development Installation

```bash
git clone https://github.com/your-username/python-project-builder
cd python-project-builder
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage

Navigate to your Python project and run:

```bash
pybuilder
```

This will:
1. ✅ Check dependencies
2. ✅ Format code
3. ✅ Lint code
4. ✅ Type check
5. ✅ Run security checks
6. ✅ Run tests with coverage
7. ✅ Build documentation
8. ✅ Generate reports

### Common Options

```bash
# Run with verbose output
pybuilder --verbose

# Auto-fix formatting and linting issues
pybuilder --fix

# Use with uv package manager
pybuilder --use-uv

# Set custom coverage threshold
pybuilder --coverage-threshold 80

# Clean build artifacts
pybuilder --clean

# Specify source directories
pybuilder --source-dirs src mypackage
```

## Configuration

### Project Structure

Python Project Builder auto-detects your project structure. It works best with:

```
your-project/
├── your_package/          # Your Python package
│   ├── __init__.py
│   └── module.py
├── tests/                 # Test directory
│   ├── __init__.py
│   └── test_module.py
├── pyproject.toml        # Project configuration
└── README.md
```

### pyproject.toml

Configure tools in your `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]

[tool.coverage.run]
source = ["your_package"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true

[tool.ruff]
target-version = "py310"
line-length = 120
```

### Optional Features

Install additional static analysis tools:

```bash
pip install python-project-builder[analysis]
```

This adds:
- **radon** - Complexity and maintainability metrics
- **vulture** - Dead code detection
- **jscpd** - Code duplication detection
- **import-linter** - Architecture enforcement
- **bandit** - Security vulnerability scanning

Install documentation tools:

```bash
pip install python-project-builder[docs]
```

## Usage Examples

### In CI/CD Pipelines

#### GitHub Actions

```yaml
name: Build

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install python-project-builder
          pip install -r requirements.txt

      - name: Run build pipeline
        run: pybuilder --verbose

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```

#### GitLab CI

```yaml
build:
  image: python:3.11
  before_script:
    - pip install python-project-builder
    - pip install -r requirements.txt
  script:
    - pybuilder
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

### As a Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: python-project-builder
        name: Python Project Builder
        entry: pybuilder
        language: system
        pass_filenames: false
        stages: [commit]
```

### In a Makefile

```makefile
.PHONY: build test clean

build:
	pybuilder

test:
	pybuilder --verbose

clean:
	pybuilder --clean

fix:
	pybuilder --fix
```

### With UV Package Manager

If you use [uv](https://github.com/astral-sh/uv):

```bash
pybuilder --use-uv
```

This prefixes all commands with `uv run`, which is faster and handles dependencies better.

## Command-Line Options

```
usage: pybuilder [-h] [--verbose] [--fix] [--clean] [--use-uv]
                 [--project-root PROJECT_ROOT]
                 [--source-dirs SOURCE_DIRS [SOURCE_DIRS ...]]
                 [--test-dirs TEST_DIRS [TEST_DIRS ...]]
                 [--coverage-threshold COVERAGE_THRESHOLD]

Options:
  -h, --help            Show help message
  --verbose, -v         Enable verbose output
  --fix                 Auto-fix formatting and linting issues
  --clean               Clean build artifacts and exit
  --use-uv              Use 'uv run' prefix for commands
  --project-root PATH   Project root directory (default: current)
  --source-dirs DIRS    Source directories to check (default: auto-detect)
  --test-dirs DIRS      Test directories (default: tests)
  --coverage-threshold N Minimum coverage % required (default: 70)
```

## Build Pipeline Steps

1. **Dependency Check** - Verifies all required tools are installed
2. **Code Formatting** - Formats code with ruff
3. **Code Linting** - Checks code quality with ruff
4. **Type Checking** - Static type analysis with mypy
5. **Security Check** - Scans for security issues
6. **Static Analysis** - Advanced code analysis (if tools installed)
7. **Tests** - Runs test suite with coverage reporting
8. **Documentation** - Builds documentation with MkDocs (if configured)
9. **Reports** - Generates coverage and quality reports

## Output

### Success

```
Python Project Builder - Comprehensive Build Pipeline
================================================================================
Project: myproject
Source directories: mypackage
Coverage threshold: 70%
================================================================================

[✓] Check Dependencies - PASSED
[✓] Format Code - PASSED
[✓] Lint Code - PASSED
[✓] Type Check - PASSED
[✓] Security Check - PASSED
[✓] Static Analysis - PASSED
[✓] Run Tests - PASSED
[i] Code Coverage: 85%
[✓] Build Documentation - PASSED
[✓] Generate Reports - PASSED

================================================================================
[SUMMARY] Build Results
================================================================================
[✓] Successful steps: 9/9
[⏱] Build duration: 12.34 seconds

[SUCCESS] BUILD SUCCESSFUL - All quality checks passed!
[✓] Ready for deployment
```

### Reports Generated

- `htmlcov/index.html` - HTML coverage report
- `coverage.xml` - XML coverage report (for CI)
- `.work/analysis/` - Static analysis results (if enabled)

## Requirements

- Python 3.10 or higher
- pip or uv package manager

Core dependencies (auto-installed):
- ruff
- mypy
- pytest
- pytest-cov
- pytest-timeout

## Troubleshooting

### Command Not Found

If `pybuilder` command isn't found after installation:

```bash
# Use as Python module instead
python -m builder.cli

# Or reinstall with --user flag
pip install --user python-project-builder
```

### Import Errors

Make sure you've installed the package:

```bash
pip list | grep python-project-builder
```

### Tests Fail

Check that your project has:
- A `tests/` directory with test files
- Test files named `test_*.py`
- pytest installed

## Development

### Setup Development Environment

```bash
git clone https://github.com/your-username/python-project-builder
cd python-project-builder
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/
```

### Run Builder on Itself

```bash
pybuilder --verbose
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Support

- **Issues**: https://github.com/your-username/python-project-builder/issues
- **Discussions**: https://github.com/your-username/python-project-builder/discussions
- **Documentation**: https://github.com/your-username/python-project-builder/tree/main/docs

## Related Projects

- [ruff](https://github.com/astral-sh/ruff) - Fast Python linter and formatter
- [mypy](https://github.com/python/mypy) - Static type checker
- [pytest](https://github.com/pytest-dev/pytest) - Testing framework
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager

## Acknowledgments

Built with inspiration from:
- Modern Python build tools
- Best practices from the Python community
- CI/CD pipeline patterns
