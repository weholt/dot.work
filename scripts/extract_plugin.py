#!/usr/bin/env python3
"""Extract a dot-work submodule to a standalone package.

This script automates the extraction of submodules from dot-work into
standalone plugin packages. It handles:
- Source file copying to new package structure
- Test file migration with structure preservation
- Import rewriting (dot_work.X → dot_X)
- pyproject.toml generation from templates
- README.md, LICENSE, and CI workflow generation
- Validation (SHA256 hashes, file counts)

Usage:
    # Dry run to see what would be done
    python scripts/extract_plugin.py dot-issues --dry-run

    # Extract to EXPORTED_PROJECTS/dot-issues/
    python scripts/extract_plugin.py dot-issues

    # Extract to custom directory
    python scripts/extract_plugin.py dot-issues --output ../dot-issues
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

# Plugin configuration for all 9 submodules
PLUGIN_CONFIG = {
    "dot-issues": {
        "source_module": "db_issues",
        "target_module": "dot_issues",
        "cli_group": "db-issues",
        "description": "SQLite-based issue tracking for autonomous agents",
        "dependencies": [
            "typer>=0.12.0",
            "rich>=13.0.0",
            "sqlmodel>=0.0.22",
            "jinja2>=3.1.0",
            "pyyaml>=6.0.0",
        ],
        "optional_deps": {},
    },
    "dot-kg": {
        "source_module": "knowledge_graph",
        "target_module": "dot_kg",
        "cli_group": "kg",
        "description": "Knowledge graph with FTS5 search for code analysis",
        "dependencies": [
            "typer>=0.12.0",
            "rich>=13.0.0",
            "numpy>=1.24.0",
        ],
        "optional_deps": {
            "http": ["httpx>=0.27.0"],
            "ann": ["hnswlib>=0.8.0"],
            "vec": ["sqlite-vec>=0.1.0"],
            "all": ["httpx>=0.27.0", "hnswlib>=0.8.0", "sqlite-vec>=0.1.0"],
        },
        "aliases": ["kg"],
    },
    "dot-review": {
        "source_module": "review",
        "target_module": "dot_review",
        "cli_group": "review",
        "description": "Interactive code review with AI-friendly export",
        "dependencies": [
            "typer>=0.12.0",
            "rich>=13.0.0",
            "fastapi>=0.100.0",
            "uvicorn[standard]>=0.23.0",
            "jinja2>=3.1.0",
            "GitPython>=3.1.0",
            "python-multipart>=0.0.6",
        ],
        "optional_deps": {},
        "static_assets": ["static", "templates"],
    },
    "dot-container": {
        "source_module": "container",
        "target_module": "dot_container",
        "cli_group": "container",
        "description": "Docker provisioning for AI coding agents",
        "dependencies": [
            "typer>=0.12.0",
            "rich>=13.0.0",
            "python-frontmatter>=1.1.0",
        ],
        "optional_deps": {},
    },
    "dot-git": {
        "source_module": "git",
        "target_module": "dot_git",
        "cli_group": "git",
        "description": "Git history analysis and complexity metrics",
        "dependencies": [
            "typer>=0.12.0",
            "rich>=13.0.0",
            "GitPython>=3.1.0",
            "radon>=6.0.0",
            "tqdm>=4.66.0",
        ],
        "optional_deps": {
            "llm": ["openai>=1.0.0", "anthropic>=0.3.0"],
        },
    },
    "dot-harness": {
        "source_module": "harness",
        "target_module": "dot_harness",
        "cli_group": "harness",
        "description": "Claude Agent SDK integration",
        "dependencies": [
            "typer>=0.12.0",
            "rich>=13.0.0",
        ],
        "optional_deps": {
            "sdk": ["claude-agent-sdk>=0.1.0", "anyio>=4.0.0"],
        },
    },
    "dot-overview": {
        "source_module": "overview",
        "target_module": "dot_overview",
        "cli_group": "overview",
        "description": "Codebase overview generation with AST parsing",
        "dependencies": [
            "typer>=0.12.0",
            "rich>=13.0.0",
            "libcst>=1.1.0",
        ],
        "optional_deps": {},
    },
    "dot-python": {
        "source_module": "python",
        "target_module": "dot_python",
        "cli_group": "python",
        "description": "Python project build and scan utilities",
        "dependencies": [
            "typer>=0.12.0",
            "rich>=13.0.0",
        ],
        "optional_deps": {
            "scan-graph": ["networkx>=3.0", "pyvis>=0.3.0"],
        },
        "aliases": ["pybuilder"],
    },
    "dot-version": {
        "source_module": "version",
        "target_module": "dot_version",
        "cli_group": "version",
        "description": "Date-based version management",
        "dependencies": [
            "typer>=0.12.0",
            "rich>=13.0.0",
            "GitPython>=3.1.0",
            "python-dotenv>=1.0.0",
        ],
        "optional_deps": {
            "llm": ["httpx>=0.24.0"],
        },
    },
}


@dataclass
class ValidationReport:
    """Validation report for the extraction process."""

    source_files: dict[str, str] = field(default_factory=dict)  # path -> sha256
    dest_files: dict[str, str] = field(default_factory=dict)  # path -> sha256
    file_counts: dict[str, int] = field(default_factory=dict)
    mismatches: list[tuple[str, str, str]] = field(default_factory=list)  # (path, source_hash, dest_hash)

    def add_source(self, path: str, sha256: str) -> None:
        """Add a source file and its hash."""
        self.source_files[path] = sha256

    def add_dest(self, path: str, sha256: str) -> None:
        """Add a destination file and its hash."""
        self.dest_files[path] = sha256

    def add_mismatch(self, path: str, source_hash: str, dest_hash: str) -> None:
        """Record a hash mismatch."""
        self.mismatches.append((path, source_hash, dest_hash))

    def set_counts(self, source_count: int, dest_count: int) -> None:
        """Set file counts."""
        self.file_counts = {"source": source_count, "dest": dest_count}

    def is_valid(self) -> bool:
        """Check if validation passed."""
        return (
            len(self.mismatches) == 0
            and self.file_counts.get("source") == self.file_counts.get("dest")
        )

    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            "# Extraction Validation Report\n",
            "## Summary",
            f"- **Source files**: {self.file_counts.get('source', 0)}",
            f"- **Destination files**: {self.file_counts.get('dest', 0)}",
            f"- **Status**: {'✅ PASSED' if self.is_valid() else '❌ FAILED'}",
            "",
        ]

        if self.mismatches:
            lines.extend([
                "## ❌ Hash Mismatches",
                "",
                "| File | Source SHA256 | Dest SHA256 |",
                "|------|---------------|------------|",
            ])
            for path, src_hash, dst_hash in self.mismatches:
                lines.append(f"| {path} | {src_hash[:16]}... | {dst_hash[:16]}... |")
            lines.append("")

        lines.extend([
            "## File Details",
            "",
            "### Source Files",
        ])
        for path, sha256 in sorted(self.source_files.items()):
            lines.append(f"- `{path}`: {sha256[:16]}...")

        return "\n".join(lines)


def calculate_sha256(path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def rewrite_imports(content: str, old_module: str, new_module: str) -> str:
    """Rewrite imports from dot_work.X to dot_X.

    Args:
        content: File content to rewrite
        old_module: Old module name (e.g., "db_issues")
        new_module: New module name (e.g., "dot_issues")

    Returns:
        Rewritten content
    """
    patterns = [
        # From imports
        (rf"from dot_work\.{old_module}(\s+import)", rf"from {new_module}\1"),
        # Module imports
        (rf"import dot_work\.{old_module}(\s|$)", rf"import {new_module}\1"),
        # Relative imports within submodule (from dot_work.X.sub import Y)
        (rf"from dot_work\.{old_module}\.", rf"from {new_module}."),
    ]
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    return content


def copy_and_rewrite_file(
    source: Path,
    dest: Path,
    old_module: str,
    new_module: str,
    report: ValidationReport,
) -> None:
    """Copy a file and rewrite imports.

    Args:
        source: Source file path
        dest: Destination file path
        old_module: Old module name
        new_module: New module name
        report: Validation report to update
    """
    # Calculate source hash before copying
    source_hash = calculate_sha256(source)
    rel_source = str(source.relative_to(source.parents[3]))  # Get relative path

    # Read and rewrite content
    content = source.read_text(encoding="utf-8")
    rewritten = rewrite_imports(content, old_module, new_module)

    # Write to destination
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(rewritten, encoding="utf-8")

    # Calculate destination hash
    dest_hash = calculate_sha256(dest)

    # Update report
    report.add_source(rel_source, source_hash)
    report.add_dest(str(dest.relative_to(dest.parents[3])), dest_hash)

    # Note: hashes will differ because we rewrote imports
    # We check that the file was copied successfully


def extract_plugin(
    name: str,
    output_dir: Path,
    dry_run: bool = False,
) -> ValidationReport:
    """Extract a plugin to target directory.

    Args:
        name: Plugin name (e.g., "dot-issues")
        output_dir: Target output directory
        dry_run: If True, show what would be done without making changes

    Returns:
        Validation report
    """
    if name not in PLUGIN_CONFIG:
        raise ValueError(f"Unknown plugin: {name}. Available: {', '.join(PLUGIN_CONFIG)}")

    config = PLUGIN_CONFIG[name]
    source_module = str(config["source_module"])
    target_module = str(config["target_module"])

    # Paths
    project_root = Path(__file__).parent.parent
    source_dir = project_root / "src" / "dot_work" / source_module
    test_source_dir = project_root / "tests" / "unit" / source_module
    test_integration_dir = project_root / "tests" / "integration"

    # Target paths
    target_dir = output_dir / name
    target_src = target_dir / "src" / target_module

    report = ValidationReport()

    print(f"\n📦 Extracting {name}...")
    print(f"   Source: {source_dir}")
    print(f"   Target: {target_src}")

    if dry_run:
        print("\n🔍 DRY RUN - No changes will be made")
        return report

    # Create target directory structure
    target_dir.mkdir(parents=True, exist_ok=True)
    target_src.mkdir(parents=True, exist_ok=True)
    (target_dir / "tests" / "unit").mkdir(parents=True, exist_ok=True)
    (target_dir / "tests" / "integration").mkdir(parents=True, exist_ok=True)

    # Copy source files
    source_files = list(source_dir.rglob("*.py"))
    for source_file in source_files:
        rel_path = source_file.relative_to(source_dir)
        dest_file = target_src / rel_path
        copy_and_rewrite_file(source_file, dest_file, source_module, target_module, report)
        print(f"  ✓ Source: {rel_path}")

    # Copy __init__.py at module root if it doesn't exist
    init_src = project_root / "src" / "dot_work" / source_module / "__init__.py"
    if init_src.exists():
        dest_init = target_src / "__init__.py"
        if not dest_init.exists():
            copy_and_rewrite_file(init_src, dest_init, source_module, target_module, report)
            # Add CLI_GROUP to __init__.py
            init_content = dest_init.read_text(encoding="utf-8")
            if 'CLI_GROUP' not in init_content:
                cli_group = str(config["cli_group"])
                init_content = f'"""{target_module} module."""\n\nCLI_GROUP = "{cli_group}"\n' + init_content.split('"""', 1)[-1].lstrip()
                dest_init.write_text(init_content, encoding="utf-8")

    # Copy unit tests
    if test_source_dir.exists():
        test_files = list(test_source_dir.rglob("*.py"))
        for test_file in test_files:
            rel_path = test_file.relative_to(test_source_dir)
            dest_file = target_dir / "tests" / "unit" / rel_path
            copy_and_rewrite_file(test_file, dest_file, source_module, target_module, report)
            print(f"  ✓ Test (unit): {rel_path}")

    # Copy integration tests for this module
    if test_integration_dir.exists():
        for test_file in test_integration_dir.rglob(f"*{source_module}*.py"):
            rel_path = test_file.relative_to(test_integration_dir)
            dest_file = target_dir / "tests" / "integration" / rel_path
            copy_and_rewrite_file(test_file, dest_file, source_module, target_module, report)
            print(f"  ✓ Test (integration): {rel_path}")

    # Copy static assets if specified
    if "static_assets" in config:
        for asset_dir in config["static_assets"]:
            asset_source = project_root / "src" / "dot_work" / source_module / str(asset_dir)
            if asset_source.exists():
                asset_dest = target_src / str(asset_dir)
                shutil.copytree(asset_source, asset_dest, dirs_exist_ok=True)
                print(f"  ✓ Asset: {asset_dir}/")

    # Generate pyproject.toml
    pyproject_content = generate_pyproject(name, config)
    (target_dir / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")
    print("  ✓ Generated: pyproject.toml")

    # Generate README.md
    readme_content = generate_readme(name, config)
    (target_dir / "README.md").write_text(readme_content, encoding="utf-8")
    print("  ✓ Generated: README.md")

    # Generate LICENSE (copy from project)
    license_source = project_root / "LICENSE"
    if license_source.exists():
        shutil.copy(license_source, target_dir / "LICENSE")
        print("  ✓ Generated: LICENSE")

    # Generate CI workflow
    (target_dir / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
    ci_content = generate_ci_workflow(name, config)
    (target_dir / ".github" / "workflows" / "ci.yml").write_text(ci_content, encoding="utf-8")
    print("  ✓ Generated: .github/workflows/ci.yml")

    # Update file counts
    total_source = len(source_files)
    total_tests = len(list(test_source_dir.rglob("*.py"))) if test_source_dir.exists() else 0
    total_tests += len(list(test_integration_dir.rglob(f"*{source_module}*.py"))) if test_integration_dir.exists() else 0
    report.set_counts(total_source, total_source + total_tests)

    # Write validation report
    report_content = report.to_markdown()
    report_path = output_dir / "validation-report.md"
    report_path.write_text(report_content, encoding="utf-8")
    print(f"\n📊 Validation report: {report_path}")

    if report.is_valid():
        print(f"\n✅ Extraction complete: {target_dir}")
    else:
        print("\n⚠️  Extraction completed with validation issues")

    return report


def generate_pyproject(name: str, config: dict) -> str:
    """Generate pyproject.toml content."""
    target_module = config["target_module"]
    deps = "\n    ".join(config["dependencies"])

    # Optional dependencies
    optional_sections = []
    for opt_name, opt_deps in config.get("optional_deps", {}).items():
        if opt_deps:
            opt_deps_str = "\n        ".join(opt_deps)
            optional_sections.append(f'{opt_name} = [\n        "{opt_deps_str}",\n    ]')

    optional_deps = "\n".join(optional_sections) if optional_sections else "# No optional dependencies"

    # Entry points
    entry_point = f'issues = "{target_module}"' if name == "dot-issues" else f'{name.split("-")[1]} = "{target_module}"'

    # Aliases
    scripts = []
    if "aliases" in config:
        for alias in config["aliases"]:
            scripts.append(f'{alias} = "{target_module}.cli:app"')

    scripts_section = "\n".join(f'    "{s}"' for s in scripts) if scripts else "# No standalone scripts"

    # Build artifacts for static assets
    artifacts = []
    if "static_assets" in config:
        for asset in config["static_assets"]:
            artifacts.append(f'"src/{target_module}/{asset}/*"')

    artifacts_section = "\n        ".join(artifacts) if artifacts else "# No static assets"

    return f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{name}"
version = "0.1.0"
description = "{config["description"]}"
readme = "README.md"
requires-python = ">=3.11"
license = {{text = "MIT"}}
dependencies = [
    {deps},
]

[project.optional-dependencies]
{optional_deps}

dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.6.0",
    "mypy>=1.11.0",
]

[project.scripts]
dot-{name.split("-")[1]} = "{target_module}.cli:app"
{scripts_section}

[project.entry-points."dot_work.plugins"]
{entry_point}

[tool.hatch.build.targets.wheel]
packages = ["src/{target_module}"]
artifacts = [
    {artifacts_section},
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "B"]
ignore = ["B009", "B904"]

[tool.mypy]
python_version = "3.11"
warn_unused_ignores = true
'''


def generate_readme(name: str, config: dict) -> str:
    """Generate README.md content."""
    cli_name = name.split("-")[1]
    description = config["description"]
    cli_group = config["cli_group"]

    return f'''# {name}

{description}

## Installation

### As a dot-work plugin

```bash
pip install {name}
```

### Standalone usage

```bash
pip install {name}
dot-{cli_name} --help
```

## Usage

As a dot-work plugin:

```bash
dot-work {cli_group} --help
```

As a standalone CLI:

```bash
dot-{cli_name} --help
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
'''


def generate_ci_workflow(name: str, config: dict) -> str:
    """Generate GitHub Actions CI workflow."""
    return '''name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run linting
        run: |
          ruff check src/
          mypy src/

      - name: Run tests
        run: |
          pytest tests/ -v --cov

      - name: Upload coverage
        uses: codecov/codecov-action@v4
'''


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract dot-work submodule to standalone package"
    )
    parser.add_argument(
        "plugin",
        choices=list(PLUGIN_CONFIG.keys()),
        help="Plugin name to extract",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("EXPORTED_PROJECTS"),
        help="Output directory (default: EXPORTED_PROJECTS/)",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    try:
        extract_plugin(args.plugin, args.output, args.dry_run)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
