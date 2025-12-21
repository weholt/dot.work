# Python Project Builder Documentation

## Overview

Python Project Builder is a comprehensive build pipeline tool that automates quality checks for Python projects. It combines multiple tools into a single, easy-to-use command that ensures code quality, test coverage, and documentation standards.

## Installation

See [README.md](../README.md#installation) for installation instructions.

## Usage Guide

### Basic Usage

The simplest way to use Python Project Builder:

```bash
cd your-project
pybuilder
```

This runs all quality checks with default settings.

### Command-Line Options

#### Verbose Mode

Get detailed output for each step:

```bash
pybuilder --verbose
```

This shows:
- Full command output
- Detailed error messages
- Progress for each sub-step

#### Auto-Fix Mode

Automatically fix formatting and linting issues:

```bash
pybuilder --fix
```

This will:
- Format code with ruff
- Fix auto-fixable linting issues
- Leave manual fixes for review

#### Custom Project Root

Run on a different project:

```bash
pybuilder --project-root /path/to/project
```

#### Custom Source Directories

Specify which directories to check:

```bash
pybuilder --source-dirs src mypackage lib
```

By default, the builder auto-detects source directories by looking for:
1. Directories with `__init__.py` files
2. Directories with Python files (excluding tests, docs, etc.)

#### Custom Test Directories

Specify test directories:

```bash
pybuilder --test-dirs tests integration_tests
```

Default is `tests/`.

#### Custom Coverage Threshold

Set minimum required coverage percentage:

```bash
pybuilder --coverage-threshold 80
```

Default is 70%. The build fails if coverage is below this threshold.

#### Using UV Package Manager

If you use the [uv](https://github.com/astral-sh/uv) package manager:

```bash
pybuilder --use-uv
```

This prefixes all commands with `uv run`, which:
- Uses uv's faster resolver
- Handles virtual environments automatically
- Ensures consistent dependency versions

#### Cleaning Build Artifacts

Remove all build artifacts:

```bash
pybuilder --clean
```

This removes:
- `__pycache__` directories
- `.pytest_cache`, `.mypy_cache`, `.ruff_cache`
- `.coverage`, `htmlcov/`, `coverage.xml`
- `.work/`, `reports/`, `site/`
- `*.egg-info` directories

### Build Pipeline Steps

#### 1. Dependency Check

Verifies required tools are installed:
- ruff (linter and formatter)
- mypy (type checker)
- pytest (test runner)
- uv (if `--use-uv` is specified)

**Output:**
```
[✓] ruff: ruff 0.1.9
[✓] mypy: mypy 1.7.1
[✓] pytest: pytest 7.4.3
```

#### 2. Code Formatting

Formats code with ruff according to project settings.

**With `--fix`:**
- Automatically formats all files

**Without `--fix`:**
- Checks if files need formatting
- Fails if unformatted code found

**Configuration:**
```toml
# pyproject.toml
[tool.ruff]
line-length = 120
target-version = "py310"
```

#### 3. Code Linting

Checks code quality with ruff.

**Checks include:**
- Unused imports
- Unused variables
- Code complexity
- Style violations
- Best practices

**With `--fix`:**
- Auto-fixes safe issues

**Configuration:**
```toml
# pyproject.toml
[tool.ruff.lint]
select = ["E", "F", "I", "B", "C4", "UP"]
ignore = ["E501"]
```

#### 4. Type Checking

Static type analysis with mypy.

**Checks:**
- Type annotations
- Type consistency
- Return types
- Function signatures

**Configuration:**
```toml
# pyproject.toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
```

#### 5. Security Check

Scans for security issues with ruff's security rules.

**Checks for:**
- SQL injection vulnerabilities
- Command injection
- Hardcoded passwords
- Insecure crypto usage
- Path traversal

#### 6. Static Analysis (Optional)

Advanced code analysis with optional tools.

**Tools (install with `[analysis]` extra):**

- **radon**: Complexity and maintainability metrics
  - Cyclomatic complexity
  - Maintainability index
  - Lines of code

- **vulture**: Dead code detection
  - Unused functions
  - Unused variables
  - Unused imports

- **jscpd**: Code duplication detection
  - Duplicate code blocks
  - Copy-paste detection

- **import-linter**: Architecture enforcement
  - Layer violations
  - Import dependencies

- **bandit**: Security scanning
  - Security issues
  - Vulnerability assessment

**Output:**
Results saved to `.work/analysis/`:
- `complexity.json`
- `maintainability.json`
- `deadcode.txt`
- `duplication.json`
- `dependencies.txt`
- `bandit.json`

#### 7. Tests

Runs test suite with coverage reporting.

**Features:**
- Parallel test execution
- Coverage measurement
- HTML and XML reports
- Timeout enforcement (5 seconds per test)

**Configuration:**
```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
timeout = 5

[tool.coverage.run]
source = ["mypackage"]

[tool.coverage.report]
exclude_lines = ["pragma: no cover"]
```

**Output:**
```
[i] Code Coverage: 85%
[✓] Coverage HTML report: htmlcov/index.html
[✓] Coverage XML report: coverage.xml
```

#### 8. Documentation Building (Optional)

Builds documentation with MkDocs if `mkdocs.yml` exists.

**Output:**
- Documentation site in `site/` directory

**Configuration:**
```yaml
# mkdocs.yml
site_name: My Project
docs_dir: docs
site_dir: site
theme:
  name: material
```

#### 9. Report Generation

Generates summary reports.

**Reports:**
- Coverage HTML: `htmlcov/index.html`
- Coverage XML: `coverage.xml` (for CI)
- Static analysis: `.work/analysis/` (if enabled)

## Configuration Files

### pyproject.toml

Main configuration file for the project:

```toml
[project]
name = "myproject"
version = "0.1.0"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
timeout = 5

[tool.coverage.run]
source = ["mypackage"]
omit = ["*/tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if __name__ == .__main__.:",
]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
disallow_untyped_defs = true

[tool.ruff]
target-version = "py310"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "B", "C4", "UP"]
ignore = ["E501"]
```

### .contracts (Import Linter)

Define architecture contracts:

```ini
[importlinter]
root_package = mypackage

[importlinter:contract:layers]
name = Layer independence
type = layers
layers =
    api
    business
    data
```

## Integration Examples

See [README.md](../README.md#usage-examples) for CI/CD integration examples.

## Troubleshooting

### Tests Not Found

Make sure:
- Tests are in `tests/` directory (or specified with `--test-dirs`)
- Test files are named `test_*.py`
- Test functions are named `test_*`

### Coverage Below Threshold

Options:
1. Write more tests
2. Lower threshold: `pybuilder --coverage-threshold 60`
3. Exclude untestable code with `# pragma: no cover`

### Type Checking Failures

Options:
1. Add type annotations
2. Fix type inconsistencies
3. Ignore specific issues with `# type: ignore`
4. Configure mypy to be less strict in `pyproject.toml`

### Static Analysis Not Running

Static analysis tools are optional. Install them:

```bash
pip install python-project-builder[analysis]
```

Or individually:
```bash
pip install radon vulture jscpd import-linter bandit
```

## Best Practices

1. **Run locally before committing:**
   ```bash
   pybuilder --fix
   ```

2. **Use in CI/CD:**
   Add to your CI pipeline to catch issues early

3. **Set appropriate coverage threshold:**
   - 70-80% for most projects
   - 80-90% for critical code
   - 60-70% for legacy code

4. **Configure tool settings:**
   Customize behavior in `pyproject.toml`

5. **Review reports:**
   Check `htmlcov/index.html` for detailed coverage analysis

## Advanced Usage

### Custom Build Script

Create a custom script using the BuildRunner API:

```python
from pathlib import Path
from builder.runner import BuildRunner

# Create custom builder
builder = BuildRunner(
    project_root=Path.cwd(),
    verbose=True,
    fix=True,
    source_dirs=["src", "lib"],
    coverage_threshold=85,
)

# Run specific steps
builder.check_dependencies()
builder.format_code()
builder.lint_code()
builder.type_check()
builder.run_tests()

# Or run full build
success = builder.run_full_build()
```

### Selective Step Execution

Run only specific steps:

```python
from builder.runner import BuildRunner

builder = BuildRunner()

# Only format and lint
builder.format_code()
builder.lint_code()

# Only run tests
builder.run_tests()
```

## FAQ

**Q: Do I need to install all optional tools?**

A: No, the builder works with just the core tools (ruff, mypy, pytest). Optional tools enhance analysis but aren't required.

**Q: Can I use this with other test frameworks?**

A: Currently only pytest is supported. Other frameworks may work but aren't tested.

**Q: Does this work with monorepos?**

A: Yes, use `--project-root` and `--source-dirs` to specify paths.

**Q: Can I skip certain checks?**

A: Not directly, but you can create a custom script using the BuildRunner API.

**Q: How do I make it faster?**

A: Use `--use-uv` for faster dependency management, or skip optional static analysis tools.
