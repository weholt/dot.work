# 🚀 Transform Discussion to Python Project

Convert a loose discussion (markdown or pasted text) into a **production-ready Python project** with proper structure, tooling, and best practices.

---

## 📥 Input

Provide one of:
- A markdown file containing project discussion/requirements
- Pasted text describing the project idea

---

## 🎯 Instructions

You are an expert Python architect. Analyze the provided discussion and generate a complete, idiomatic Python project following these specifications:

### 1. Project Structure

```
project-name/
├── pyproject.toml          # All config, dependencies, tool settings
├── README.md               # Overview, install, usage, dev setup
├── scripts/
│   └── build.py            # Build pipeline (lint, type-check, test)
├── src/
│   └── <package>/
│       ├── __init__.py
│       ├── cli.py          # Thin CLI layer (typer)
│       ├── config.py       # Configuration management
│       └── <modules>.py    # Core logic modules
└── tests/
    ├── conftest.py
    ├── unit/
    └── integration/
```

### 2. pyproject.toml Template

```toml
[project]
name = "<package-name>"
version = "0.1.0"
description = "<extracted from discussion>"
readme = "README.md"
requires-python = ">=3.11"
authors = [{ name = "Author", email = "author@example.com" }]
dependencies = [
  "typer>=0.12.3",
  "rich>=13.9.0",
  "pyyaml>=6.0.0",
  "python-dotenv>=1.0.1",
  # Additional dependencies extracted from discussion
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
  "pytest-cov>=4.1.0",
  "pytest-mock>=3.12.0",
  "pytest-timeout>=2.4.0",
  "ruff>=0.6.0",
  "mypy>=1.11.0",
  "types-PyYAML>=6.0.0",
]

[project.scripts]
<cli-name> = "<package>.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/<package>"]

[tool.hatch.build.targets.sdist]
include = ["src/<package>"]

[tool.uv]
package = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
timeout = 30
addopts = ["-v", "--tb=short", "--strict-markers"]
markers = [
  "slow: marks tests as slow (deselect with '-m \"not slow\"')",
  "integration: marks tests as integration tests",
]

[tool.coverage.run]
source = ["src/<package>"]
branch = true
omit = [
  "*/tests/*",
  "*/__pycache__/*",
  "src/<package>/cli.py",  # CLI is thin orchestration layer
]

[tool.coverage.report]
fail_under = 75
show_missing = true
exclude_lines = [
  "pragma: no cover",
  "def __repr__",
  "raise NotImplementedError",
  "if __name__ == .__main__.:",
  "if TYPE_CHECKING:",
]

[tool.coverage.html]
directory = "htmlcov"

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "B", "C4", "UP", "PT"]
ignore = ["E501", "B008", "B904"]

[tool.mypy]
python_version = "3.11"
warn_unused_ignores = true
warn_redundant_casts = true
exclude = ["tests/"]
```

### 3. Build Script (scripts/build.py)

**IMPORTANT**: Generate this build script almost verbatim, only changing the project name and package path references.

```python
#!/usr/bin/env python3
"""Build script for <PROJECT_NAME>."""

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


class BuildRunner:
    """Handles the build process for the project."""

    def __init__(self, verbose: bool = False, fix: bool = False, run_integration: bool = False):
        self.verbose = verbose
        self.fix = fix
        self.run_integration = run_integration
        self.project_root = Path(__file__).parent.parent
        self.src_path = self.project_root / "src" / "<package>"  # UPDATE THIS
        self.tests_path = self.project_root / "tests"
        self.failed_steps: list[str] = []

    def run_command(
        self,
        cmd: list[str],
        description: str,
        check: bool = True,
        capture_output: bool = True,
    ) -> tuple[bool, str, str]:
        """Run a command and return success status and output."""
        if self.verbose:
            print(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                cwd=self.project_root,
                check=check,
                encoding="utf-8",
                errors="replace",
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout or "", e.stderr or ""
        except FileNotFoundError:
            return False, "", f"Command not found: {cmd[0]}"

    def print_step(self, step: str) -> None:
        """Print a build step header."""
        print(f"\n{'=' * 60}")
        print(f"[TOOL] {step}")
        print(f"{'=' * 60}")

    def print_result(self, success: bool, step: str, output: str = "", error: str = "") -> None:
        """Print the result of a build step."""
        if success:
            print(f"[OK] {step} - PASSED")
        else:
            print(f"[FAIL] {step} - FAILED")
            self.failed_steps.append(step)
            if error:
                print(f"Error: {error}")
            if output:
                print(f"Output: {output}")

    def check_dependencies(self) -> bool:
        """Check if all required tools are available."""
        self.print_step("Checking Dependencies")

        tools = [
            ("uv", ["uv", "--version"]),
            ("ruff", ["uv", "run", "ruff", "--version"]),
            ("mypy", ["uv", "run", "mypy", "--version"]),
            ("pytest", ["uv", "run", "pytest", "--version"]),
        ]

        all_available = True
        for tool_name, cmd in tools:
            success, output, _error = self.run_command(cmd, f"Check {tool_name}")
            if success:
                version = output.strip().split("\n")[0] if output else "unknown"
                print(f"[OK] {tool_name}: {version}")
            else:
                print(f"[FAIL] {tool_name}: Not available")
                all_available = False

        return all_available

    def sync_dependencies(self) -> bool:
        """Sync project dependencies."""
        self.print_step("Syncing Dependencies")
        success, output, error = self.run_command(
            ["uv", "sync", "--all-extras"], "Sync dependencies"
        )
        self.print_result(success, "Dependency Sync", output, error)
        return success

    def format_code(self) -> bool:
        """Format code with ruff."""
        self.print_step("Code Formatting")

        if not self.src_path.exists():
            print(f"[WARN] Source directory not found at {self.src_path}")
            return False

        cmd = ["uv", "run", "ruff", "format"]
        if self.fix:
            cmd.append(str(self.src_path))
        else:
            cmd.extend(["--check", str(self.src_path)])

        success_format, output_format, error_format = self.run_command(cmd, "ruff format")

        check_cmd = ["uv", "run", "ruff", "check"]
        if self.fix:
            check_cmd.append("--fix")
        check_cmd.append(str(self.src_path))

        success_check, output_check, error_check = self.run_command(check_cmd, "ruff check")

        self.print_result(success_format, "ruff format", output_format, error_format)
        self.print_result(success_check, "ruff check", output_check, error_check)

        return success_format and success_check

    def lint_code(self) -> bool:
        """Lint code with ruff."""
        self.print_step("Code Linting")

        if not self.src_path.exists():
            print(f"[WARN] Source directory not found at {self.src_path}")
            return False

        cmd = ["uv", "run", "ruff", "check"]
        if self.fix:
            cmd.append("--fix")
        cmd.append(str(self.src_path))

        success, output, error = self.run_command(cmd, "ruff linting")
        self.print_result(success, "ruff", output, error)
        return success

    def type_check(self) -> bool:
        """Type check with mypy."""
        self.print_step("Type Checking")

        if not self.src_path.exists():
            print(f"[WARN] Source directory not found at {self.src_path}")
            return False

        success, output, error = self.run_command(
            ["uv", "run", "mypy", str(self.src_path)],
            f"mypy {self.src_path}",
        )

        self.print_result(success, f"mypy {self.src_path}", output, error)
        return success

    def run_unit_tests(self) -> bool:
        """Run unit tests with coverage."""
        self.print_step("Unit Tests")

        coverage_files = [".coverage", "htmlcov", "coverage.xml"]
        for file_name in coverage_files:
            path = self.project_root / file_name
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

        if not self.tests_path.exists():
            print(f"[WARN] Test directory not found at {self.tests_path}")
            return False

        if not self.src_path.exists():
            print(f"[WARN] Source directory not found at {self.src_path}")
            return False

        cmd = [
            "uv",
            "run",
            "pytest",
            str(self.tests_path),
            f"--cov={self.src_path}",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml",
            "--cov-fail-under=75",
            "--durations=20",
            "-vv" if self.verbose else "-v",
        ]

        # Exclude integration tests unless explicitly requested
        if not self.run_integration:
            cmd.extend(["-m", "not integration"])
        else:
            print("[INFO] Including integration tests")

        if self.verbose:
            cmd[cmd.index("--durations=20")] = "--durations=50"

        success, output, error = self.run_command(
            cmd,
            "pytest with coverage",
            capture_output=False,
        )

        self.print_result(success, "Unit Tests with Coverage", "", "")

        if success:
            coverage_xml = self.project_root / "coverage.xml"
            if coverage_xml.exists():
                import xml.etree.ElementTree as ET

                try:
                    tree = ET.parse(coverage_xml)
                    root = tree.getroot()
                    coverage_elem = root.find(".//coverage")
                    if coverage_elem is not None:
                        line_rate = float(coverage_elem.get("line-rate", "0"))
                        coverage_pct = int(line_rate * 100)
                        print(f"Code Coverage: {coverage_pct}%")
                        if coverage_pct < 75:
                            print("WARNING: Coverage below 75% threshold!")
                            return False
                except Exception as e:
                    print(f"Warning: Could not parse coverage.xml: {e}")
            else:
                print("Warning: coverage.xml not found")

        return success

    def step_security(self) -> bool:
        """Run security checks."""
        self.print_step("Security Checks")

        if not self.src_path.exists():
            print(f"[WARN] Source directory not found at {self.src_path}")
            return False

        success, output, error = self.run_command(
            ["uv", "run", "ruff", "check", str(self.src_path), "--select", "S"],
            "Security linting",
        )

        self.print_result(success, "Security Check", output, error)
        return success

    def generate_reports(self) -> bool:
        """Generate build reports."""
        self.print_step("Generating Reports")

        coverage_html = self.project_root / "htmlcov"
        if coverage_html.exists():
            print("[OK] Coverage HTML report: htmlcov/index.html")

        coverage_xml = self.project_root / "coverage.xml"
        if coverage_xml.exists():
            print("[OK] Coverage XML report: coverage.xml")

        return True

    def clean_artifacts(self) -> bool:
        """Clean build artifacts."""
        self.print_step("Cleaning Artifacts")

        artifacts = [
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "*.egg-info",
            ".coverage",
        ]

        for pattern in artifacts:
            if pattern.startswith("*"):
                for path in self.project_root.glob(pattern):
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
            else:
                path = self.project_root / pattern
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()

        print("[OK] Cleaned build artifacts")
        return True

    def run_full_build(self) -> bool:
        """Run the complete build pipeline."""
        print("<PROJECT_NAME> - Build Pipeline")  # UPDATE THIS
        print(f"{'=' * 60}")

        start_time = time.time()

        steps = [
            ("Check Dependencies", self.check_dependencies),
            ("Sync Dependencies", self.sync_dependencies),
            ("Format Code", self.format_code),
            ("Lint Code", self.lint_code),
            ("Type Check", self.type_check),
            ("Security Check", self.step_security),
            ("Unit Tests", self.run_unit_tests),
            ("Generate Reports", self.generate_reports),
        ]

        success_count = 0
        total_steps = len(steps)

        for step_name, step_func in steps:
            try:
                if step_func():
                    success_count += 1
            except Exception as e:
                print(f"[FAIL] {step_name} failed with exception: {e}")
                self.failed_steps.append(step_name)

        end_time = time.time()
        duration = end_time - start_time

        print(f"\n{'=' * 60}")
        print("[STAT] Build Summary")
        print(f"{'=' * 60}")
        print(f"[OK] Successful steps: {success_count}/{total_steps}")
        print(f"[TIME]  Build duration: {duration:.2f} seconds")

        if self.failed_steps:
            print(f"[FAIL] Failed steps: {', '.join(self.failed_steps)}")

        if success_count == total_steps:
            print("\n[SUCCESS] BUILD SUCCESSFUL - All quality checks passed!")
            print("[PKG] Ready for deployment")
            return True
        elif success_count >= total_steps - 1:
            print(
                f"\n[WARN]  BUILD MOSTLY SUCCESSFUL - {total_steps - success_count} minor issues"
            )
            print("[TOOL] Consider addressing failed steps before deployment")
            return True
        else:
            print(f"\n[FAIL] BUILD FAILED - {total_steps - success_count} critical issues")
            print("[FIX]  Please fix the failed steps before proceeding")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build script for <PROJECT_NAME>")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--fix", action="store_true", help="Auto-fix formatting and linting issues")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts and exit")
    parser.add_argument(
        "--integration",
        choices=["all", "none"],
        default="none",
        help="Run integration tests: 'all' to include them, 'none' to skip (default: none)",
    )

    args = parser.parse_args()

    builder = BuildRunner(
        verbose=args.verbose,
        fix=args.fix,
        run_integration=args.integration == "all",
    )

    if args.clean:
        builder.clean_artifacts()
        return 0

    success = builder.run_full_build()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
```

**Build Script Customization Notes:**
- Replace `<PROJECT_NAME>` with actual project name
- Replace `<package>` in `self.src_path` with actual package name
- The script runs these steps in order:
  1. **Check Dependencies** - Verify uv, ruff, mypy, pytest available
  2. **Sync Dependencies** - `uv sync --all-extras`
  3. **Format Code** - `ruff format` + `ruff check --fix`
  4. **Lint Code** - `ruff check`
  5. **Type Check** - `mypy src/<package>`
  6. **Security Check** - `ruff check --select S`
  7. **Unit Tests** - `pytest --cov --cov-fail-under=75`
  8. **Generate Reports** - Coverage HTML/XML

**Usage:**
```bash
uv run python scripts/build.py           # Run full build
uv run python scripts/build.py --fix     # Auto-fix formatting/linting
uv run python scripts/build.py --verbose # Verbose output
uv run python scripts/build.py --clean   # Clean artifacts only
uv run python scripts/build.py --integration all  # Include integration tests
```

---

## 📐 Code Quality Standards

### Design Principles
- **SRP**: Each module/function has one responsibility
- **DRY**: No duplicated logic
- **KISS**: Simple over clever
- **Dependency Injection**: Accept dependencies as parameters
- **Separation of Concerns**: Logic ≠ I/O ≠ UI

### Pythonic Patterns
- Use `pathlib.Path` for all file operations
- Use `@dataclass` for structured data
- Use `typing` annotations on all functions
- Use context managers (`with`) for resources
- Use generators/iterators for streaming data
- Use comprehensions over verbose loops
- Use `logging` module, not `print()`
- Prefer functions over classes when state isn't needed

### Architecture Rules
- **Thin CLI**: Parse input/format output only, delegate to core modules
- **No imports from `src/`**: Use `from <package> import X`, never `from src.<package>`
- **Config via environment**: Use `.env`/`python-dotenv`, no hardcoded secrets
- **Layered design**: CLI → Services → Domain → Infrastructure

### Function Guidelines
- Max 15 lines per function (excluding docstrings)
- Max 3 levels of nesting
- Single return type per function
- Clear, descriptive names (snake_case)

### Documentation
- Google-style docstrings on all public functions/classes
- Type hints on all parameters and return values
- README with: overview, install, usage, dev setup

---

## 📤 Output Requirements

Generate these files:

1. **pyproject.toml** - Complete with all dependencies and tool configs
2. **README.md** - Project overview, installation, usage examples (MUST emphasize `uv run` for all commands)
3. **AGENTS.md** - AI agent guidelines for maintaining code quality (MUST include mandatory `uv run` section)
4. **.gitignore** - Standard Python gitignore
5. **scripts/build.py** - Full build pipeline script
6. **src/<package>/__init__.py** - Package exports
7. **src/<package>/cli.py** - CLI entry point (typer-based)
8. **src/<package>/config.py** - Configuration management
9. **src/<package>/<core_modules>.py** - Core logic modules
10. **tests/conftest.py** - Pytest fixtures
11. **tests/unit/test_<modules>.py** - Unit tests for each module

### README.md Requirements

The generated README.md **MUST** include:

1. A prominent section explaining that `uv run` is **MANDATORY** for all Python commands
2. All code examples using `uv run python ...` or `uv run <command>`
3. Installation instructions using `uv sync`

Example sections to include:

```markdown
## ⚠️ Important: Always Use `uv run`

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.
**All Python commands MUST be run using `uv run`.**

```bash
# ✅ CORRECT
uv run python scripts/build.py
uv run pytest
uv run mypy src/

# ❌ WRONG - Never run Python directly  
python scripts/build.py
pytest
```

## Installation

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <repo-url>
cd <project>
uv sync
```

## Development

```bash
# Run the build pipeline
uv run python scripts/build.py

# Run with auto-fix
uv run python scripts/build.py --fix

# Run tests only
uv run pytest

# Type checking
uv run mypy src/<package>
```
```

### .gitignore Template

**IMPORTANT**: Generate this .gitignore file to exclude build artifacts, caches, and sensitive files.

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Testing
.coverage
coverage.xml
htmlcov/
.pytest_cache/
.tox/
.hypothesis/

# Type checking
.mypy_cache/

# Linting
.ruff_cache/

# IDEs
.vscode/settings.json
.idea/
*.swp
*.swo
*~

# Environment
.env
.env.local
.env.*.local
.venv/
venv/
ENV/
env/
env.bak/
venv.bak/

# UV (package manager)
.uv/

# OS
.DS_Store
Thumbs.db

# Project-specific (customize as needed)
# temp/
# logs/
# *.log
```

### 5. AGENTS.md Template

**IMPORTANT**: Generate this file to ensure AI agents maintain code quality standards during development.

```markdown
# AI Agent Guidelines for <PROJECT_NAME>

This document provides instructions for AI agents (GitHub Copilot, Claude, GPT, etc.) working on this codebase.
**Read this file before making any changes.**

## 🔒 Quality Gates

Before submitting any code, ensure:

1. **Run the build script**: `uv run python scripts/build.py`
2. **All checks must pass**: formatting, linting, type-checking, tests
3. **Coverage ≥75%**: Add tests for new functionality
4. **No new warnings**: Fix all mypy and ruff warnings

## ⚠️ MANDATORY: Use `uv run` for ALL Python Commands

**NEVER run Python directly. ALWAYS use `uv run`.**

```bash
# ✅ CORRECT - Always use uv run
uv run python scripts/build.py
uv run python -m pytest
uv run mypy src/
uv run ruff check .

# ❌ WRONG - Never run Python directly
python scripts/build.py
python -m pytest
mypy src/
```

This ensures:
- Correct virtual environment is always used
- Dependencies are automatically synced
- Consistent behavior across all environments

## 🏗️ Project Structure

```
<project>/
├── src/<package>/      # Main source code
│   ├── cli.py          # CLI entry point (THIN - no business logic)
│   ├── config.py       # Configuration management
│   └── *.py            # Core modules
├── tests/
│   ├── unit/           # Unit tests (fast, isolated)
│   └── integration/    # Integration tests (marked with @pytest.mark.integration)
└── scripts/
    └── build.py        # Build pipeline - run this before committing
```

## 📏 Code Standards

### Mandatory Rules

1. **Type annotations on ALL functions**
   ```python
   def process_item(item: str, count: int = 1) -> list[str]:
   ```

2. **Google-style docstrings on public APIs**
   ```python
   def fetch_data(url: str) -> dict[str, Any]:
       """Fetch data from the specified URL.

       Args:
           url: The endpoint URL to fetch from.

       Returns:
           Parsed JSON response as a dictionary.

       Raises:
           ConnectionError: If the request fails.
       """
   ```

3. **Use `pathlib.Path` for all file operations**
   ```python
   from pathlib import Path
   config_path = Path("config") / "settings.yaml"
   ```

4. **Use `@dataclass` for data structures**
   ```python
   from dataclasses import dataclass

   @dataclass
   class Task:
       id: str
       title: str
       completed: bool = False
   ```

### Forbidden Patterns

- ❌ Running Python directly — **ALWAYS use `uv run python ...`**, never `python ...`
- ❌ `from src.<package> import X` — use `from <package> import X`
- ❌ Business logic in `cli.py` — delegate to service modules
- ❌ Hardcoded secrets, paths, or config values — use environment variables
- ❌ Bare `except:` blocks — always specify exception types
- ❌ `print()` for logging — use `logging` module
- ❌ Mutable default arguments — use `field(default_factory=...)`
- ❌ Global mutable state
- ❌ Functions >15 lines (excluding docstrings)
- ❌ Nesting >3 levels deep
- ❌ Classes >200 lines or >10 methods

## 🧪 Testing Requirements

### Unit Tests
- Test each public function
- Cover happy path AND edge cases
- Use `pytest` fixtures for common setup
- Mock external dependencies

### Test Naming
```python
def test_<function_name>_<scenario>_<expected_result>():
    # test_parse_config_missing_file_raises_error
    # test_process_items_empty_list_returns_empty
```

### Running Tests
```bash
uv run python scripts/build.py                    # Full build with tests
uv run python scripts/build.py --integration all  # Include integration tests
uv run pytest tests/unit -v                       # Unit tests only
```

## 🔄 Workflow

### Before Making Changes
1. Run `python scripts/build.py` to verify clean state
2. Understand the existing architecture
3. Check for similar patterns in the codebase

### When Making Changes
1. Keep functions small and focused (SRP)
2. Add type hints immediately
3. Write tests alongside implementation
4. Use dependency injection for testability

### Before Committing
1. Run `uv run python scripts/build.py --fix` to auto-fix formatting
2. Run `uv run python scripts/build.py` to verify all checks pass
3. Ensure no decrease in test coverage
4. Update docstrings if API changed

## 🎯 Design Principles

| Principle | Application |
|-----------|-------------|
| **SRP** | One reason to change per module/function |
| **DRY** | Extract common logic into utilities |
| **KISS** | Simplest solution that works |
| **YAGNI** | Don't build features "just in case" |
| **Dependency Inversion** | Depend on abstractions, not concretions |

## 📦 Adding Dependencies

1. Add to `pyproject.toml` under `[project.dependencies]`
2. Run `uv sync` to install
3. Add type stubs if available (e.g., `types-PyYAML`)
4. Document why the dependency is needed

## 🚫 What NOT to Do

- Don't skip the build script
- Don't ignore type errors (fix them or use `# type: ignore` with comment)
- Don't add untested code
- Don't put logic in the CLI layer
- Don't use `os.path` (use `pathlib`)
- Don't commit with failing tests
- Don't decrease test coverage

## 📝 Commit Messages

Follow conventional commits:
```
feat: add user authentication
fix: handle empty config file
refactor: extract validation logic
test: add edge cases for parser
docs: update API documentation
```

---

**Remember**: Run `uv run python scripts/build.py` before every commit!
```

**AGENTS.md Customization Notes:**
- Replace `<PROJECT_NAME>` with actual project name
- Replace `<package>` with actual package name
- Add project-specific rules as needed
- This file should be read by AI agents before making changes

---

## 🔍 Analysis Steps

1. **Extract Requirements**: Identify features, behaviors, data models from discussion
2. **Identify Dependencies**: Map features to PyPI packages
3. **Design Modules**: Break down into cohesive, loosely-coupled modules
4. **Define Interfaces**: Establish public APIs for each module
5. **Plan Tests**: Identify test cases for each feature
6. **Generate Code**: Produce complete, runnable implementation

---

## ⚠️ Anti-Patterns to Avoid

- ❌ `from src.package import X` — use `from package import X`
- ❌ Class names with library prefixes (e.g., `SQLModelUser`) — use `User`
- ❌ Business logic in CLI handlers
- ❌ Hardcoded paths, secrets, or config values
- ❌ Catch-all `except:` blocks
- ❌ Magic strings/numbers without constants
- ❌ Global mutable state
- ❌ Inline imports inside functions
- ❌ HTML/templates mixed with logic

---

## 📋 Checklist Before Output

- [ ] All functions have type annotations
- [ ] All public APIs have docstrings
- [ ] No circular imports
- [ ] Tests cover core logic (≥75% target)
- [ ] Config externalized to environment
- [ ] CLI is thin orchestration layer
- [ ] build.py runs all quality checks
- [ ] pyproject.toml is complete and valid
- [ ] README explains setup and usage
- [ ] AGENTS.md contains quality guidelines for AI agents
- [ ] .gitignore excludes build artifacts, caches, and secrets

---

## 🎬 Example Usage

> "Here's a discussion about building a task management CLI tool..."
> *(Paste discussion or reference markdown file)*

**Output**: Complete project structure with all files ready to run `uv sync && uv run python scripts/build.py`
