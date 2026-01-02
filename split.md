# dot-work Submodule Split Plan

## Executive Summary

Split 8 submodules from `dot-work` into standalone GitHub projects that can be installed independently or as optional dependencies. The core `dot-work` package retains prompt installation, AI agent integration, and orchestration capabilities.

## Goals

1. **Reduce core package size** - Core dot-work becomes lightweight (~100KB)
2. **Independent versioning** - Each project can release independently
3. **Selective installation** - Users install only what they need
4. **Plugin architecture** - Dynamic discovery of installed plugins
5. **Maintainability** - Smaller, focused codebases

---

## Submodules to Extract (8 projects)

| Current Module | New Project Name | CLI Command | Description |
|---------------|------------------|-------------|-------------|
| `container/` | `dot-container` | `dot-container` | Docker provisioning for LLM agents |
| `db_issues/` | `dot-issues` | `dot-issues` | SQLite-based issue tracking |
| `git/` | `dot-git` | `dot-git` | Git history analysis with LLM summaries |
| `harness/` | `dot-harness` | `dot-harness` | Claude Agent SDK integration |
| `knowledge_graph/` | `dot-kg` | `dot-kg` | Knowledge graph for markdown |
| `overview/` | `dot-overview` | `dot-overview` | Codebase bird's-eye overview |
| `python/` | `dot-python` | `dot-python` | Python build/scan utilities |
| `review/` | `dot-review` | `dot-review` | Code review UI with comments |
| `version/` | `dot-version` | `dot-version` | Date-based version management |

## Modules Retained in dot-work (6 folders)

| Module | Reason |
|--------|--------|
| `prompts/` | Core functionality - AI prompt templates |
| `subagents/` | Core functionality - AI subagent definitions |
| `skills/` | Core functionality - AI skill definitions |
| `tools/` | Core functionality - AI tool definitions |
| `zip/` | Lightweight utility, few dependencies |
| `utils/` | Shared utilities used by installer |
| `installer.py` | Core functionality - prompt installation |
| `environments.py` | Core functionality - environment detection |
| `cli.py` | Core CLI - but will be refactored |

---

## Phase 1: Infrastructure Setup (Week 1)

### 1.1 Create Plugin Discovery System

Add to `dot-work` core:

```python
# src/dot_work/plugins.py
"""Plugin discovery for dot-work ecosystem."""

import importlib.metadata
from dataclasses import dataclass


@dataclass
class DotWorkPlugin:
    """Discovered plugin metadata."""
    name: str
    module: str
    cli_group: str | None
    version: str


def discover_plugins() -> list[DotWorkPlugin]:
    """Discover installed dot-work plugins via entry points."""
    plugins = []
    for ep in importlib.metadata.entry_points(group="dot_work.plugins"):
        try:
            module = ep.load()
            plugins.append(DotWorkPlugin(
                name=ep.name,
                module=ep.value,
                cli_group=getattr(module, "CLI_GROUP", None),
                version=getattr(module, "__version__", "0.0.0"),
            ))
        except ImportError:
            pass  # Plugin not installed
    return plugins


def register_plugin_cli(app, plugin: DotWorkPlugin) -> None:
    """Register a plugin's CLI commands with the main app."""
    if plugin.cli_group:
        try:
            module = importlib.import_module(f"{plugin.module}.cli")
            if hasattr(module, "app"):
                app.add_typer(module.app, name=plugin.cli_group)
        except ImportError:
            pass
```

### 1.2 Update Core pyproject.toml

```toml
[project]
name = "dot-work"
version = "0.2.0"
description = "Portable AI coding prompts for project scaffolding"
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "pyyaml>=6.0.0",
    "jinja2>=3.1.0",
    "gitignore-parser>=0.1.0",  # for zip
]

[project.optional-dependencies]
# Install all plugins
all = [
    "dot-container",
    "dot-issues",
    "dot-git",
    "dot-harness",
    "dot-kg",
    "dot-overview",
    "dot-python",
    "dot-review",
    "dot-version",
]
# Individual plugin groups
container = ["dot-container"]
issues = ["dot-issues"]
git = ["dot-git"]
harness = ["dot-harness"]
kg = ["dot-kg"]
overview = ["dot-overview"]
python = ["dot-python"]
review = ["dot-review"]
version = ["dot-version"]

[project.scripts]
dot-work = "dot_work.cli:app"

[project.entry-points."dot_work.plugins"]
# Core plugins are registered here when installed
```

### 1.3 Refactor cli.py

Current `cli.py` is 40KB. Refactor to:
1. Keep only core commands (install, list, detect, init, validate)
2. Move module-specific commands to their respective plugins
3. Add plugin discovery and registration

```python
# src/dot_work/cli.py (refactored)
"""dot-work CLI - Core commands only."""

import typer
from dot_work.plugins import discover_plugins, register_plugin_cli

app = typer.Typer(help="Portable AI prompts for project scaffolding")

# Core commands remain here:
# - install
# - list
# - detect
# - init
# - init-work
# - validate
# - canonical
# - prompt

# Dynamic plugin registration
for plugin in discover_plugins():
    register_plugin_cli(app, plugin)
```

---

## Phase 2: Extract Each Submodule (Weeks 2-5)

### Template: New Project Structure

Each extracted project follows this structure:

```
dot-<name>/
├── src/
│   └── dot_<name>/
│       ├── __init__.py
│       ├── cli.py           # Typer app with CLI_GROUP
│       └── ... (module files)
├── tests/
│   ├── unit/
│   │   └── ... (unit tests)
│   └── integration/
│       └── ... (integration tests)
├── pyproject.toml
├── README.md
├── LICENSE
└── CHANGELOG.md
```

### Template: pyproject.toml

```toml
[project]
name = "dot-<name>"
version = "0.1.0"
description = "<description>"
requires-python = ">=3.11"
license = { text = "MIT" }
dependencies = [
    # Module-specific dependencies only
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.6.0",
    "mypy>=1.11.0",
]

[project.scripts]
dot-<name> = "dot_<name>.cli:app"

[project.entry-points."dot_work.plugins"]
<name> = "dot_<name>"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## Phase 2.1: Extract dot-container

**Source:** `src/dot_work/container/`
**Target:** `github.com/<org>/dot-container`

### Files to Move

```
src/dot_work/container/
├── __init__.py
└── provision/
    ├── __init__.py
    ├── cli.py
    ├── core.py
    └── validation.py

tests/unit/container/
└── provision/
    ├── test_*.py

tests/integration/container/
└── provision/
    ├── test_*.py
```

### Dependencies (pyproject.toml)

```toml
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "python-frontmatter>=1.1.0",
]
```

### CLI Entry Point

```python
# src/dot_container/cli.py
CLI_GROUP = "container"  # Registers as `dot-work container`
```

### Test Migration

| Source | Destination |
|--------|-------------|
| `tests/unit/container/provision/` | `dot-container/tests/unit/provision/` |
| `tests/integration/container/provision/` | `dot-container/tests/integration/provision/` |

---

## Phase 2.2: Extract dot-issues

**Source:** `src/dot_work/db_issues/`
**Target:** `github.com/<org>/dot-issues`

### Files to Move

```
src/dot_work/db_issues/
├── __init__.py
├── adapters.py
├── cli.py
├── config.py
├── domain.py
├── services.py
└── templates/
```

### Dependencies (pyproject.toml)

```toml
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "sqlmodel>=0.0.22",
    "jinja2>=3.1.0",
    "pyyaml>=6.0.0",
]
```

### CLI Entry Point

```python
# src/dot_issues/cli.py
CLI_GROUP = "db-issues"  # Registers as `dot-work db-issues`
```

### Test Migration

| Source | Destination |
|--------|-------------|
| `tests/unit/db_issues/` (17 files) | `dot-issues/tests/unit/` |
| `tests/integration/db_issues/` (6 files) | `dot-issues/tests/integration/` |

---

## Phase 2.3: Extract dot-git

**Source:** `src/dot_work/git/`
**Target:** `github.com/<org>/dot-git`

### Files to Move

```
src/dot_work/git/
├── __init__.py
├── cli.py
├── complexity.py
├── file_analyzer.py
├── models.py
└── services.py
```

### Dependencies (pyproject.toml)

```toml
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "GitPython>=3.1.0",
    "radon>=6.0.0",
    "tqdm>=4.66.0",
]

[project.optional-dependencies]
llm = [
    "openai>=1.0.0",
    "anthropic>=0.3.0",
]
```

### CLI Entry Point

```python
# src/dot_git/cli.py
CLI_GROUP = "git"  # Registers as `dot-work git`
```

### Test Migration

| Source | Destination |
|--------|-------------|
| `tests/unit/git/` (6 files) | `dot-git/tests/unit/` |
| `tests/integration/test_git_history.py` | `dot-git/tests/integration/` |

---

## Phase 2.4: Extract dot-harness

**Source:** `src/dot_work/harness/`
**Target:** `github.com/<org>/dot-harness`

### Files to Move

```
src/dot_work/harness/
├── __init__.py
├── cli.py
├── client.py
└── tasks.py
```

### Dependencies (pyproject.toml)

```toml
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
sdk = [
    "claude-agent-sdk>=0.1.0",
    "anyio>=4.0.0",
]
```

### CLI Entry Point

```python
# src/dot_harness/cli.py
CLI_GROUP = "harness"  # Registers as `dot-work harness`
```

### Test Migration

| Source | Destination |
|--------|-------------|
| `tests/unit/harness/` (2 files) | `dot-harness/tests/unit/` |

---

## Phase 2.5: Extract dot-kg

**Source:** `src/dot_work/knowledge_graph/`
**Target:** `github.com/<org>/dot-kg`

### Files to Move

```
src/dot_work/knowledge_graph/
├── __init__.py
├── cli.py
├── config.py
├── db.py
├── graph.py
├── ids.py
├── parse_md.py
├── render.py
├── search_fts.py
├── search_semantic.py
├── search_scope.py
├── collections.py
└── embed/
    ├── __init__.py
    ├── base.py
    ├── ollama.py
    └── openai.py
```

### Dependencies (pyproject.toml)

```toml
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "numpy>=1.24.0",
]

[project.optional-dependencies]
http = ["httpx>=0.27.0"]
ann = ["hnswlib>=0.8.0"]
vec = ["sqlite-vec>=0.1.0"]
all = [
    "httpx>=0.27.0",
    "hnswlib>=0.8.0",
    "sqlite-vec>=0.1.0",
]
```

### CLI Entry Point

```python
# src/dot_kg/cli.py
CLI_GROUP = "kg"  # Registers as `dot-work kg`
```

### Standalone Script

Additionally, `kg` is registered as a standalone command:

```toml
[project.scripts]
dot-kg = "dot_kg.cli:app"
kg = "dot_kg.cli:app"  # Keep existing alias
```

### Test Migration

| Source | Destination |
|--------|-------------|
| `tests/unit/knowledge_graph/` (14 files) | `dot-kg/tests/unit/` |
| `tests/integration/knowledge_graph/` (2 files) | `dot-kg/tests/integration/` |

---

## Phase 2.6: Extract dot-overview

**Source:** `src/dot_work/overview/`
**Target:** `github.com/<org>/dot-overview`

### Files to Move

```
src/dot_work/overview/
├── __init__.py
├── cli.py
├── code_parser.py
├── markdown_parser.py
├── models.py
├── pipeline.py
├── reporter.py
└── scanner.py
```

### Dependencies (pyproject.toml)

```toml
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "libcst>=1.1.0",
]
```

### CLI Entry Point

```python
# src/dot_overview/cli.py
CLI_GROUP = "overview"  # Registers as `dot-work overview`
```

### Test Migration

| Source | Destination |
|--------|-------------|
| `tests/unit/overview/` (5 files) | `dot-overview/tests/unit/` |

---

## Phase 2.7: Extract dot-python

**Source:** `src/dot_work/python/`
**Target:** `github.com/<org>/dot-python`

### Files to Move

```
src/dot_work/python/
├── __init__.py
├── build/
│   ├── __init__.py
│   └── cli.py
└── scan/
    ├── __init__.py
    └── cli.py
```

### Dependencies (pyproject.toml)

```toml
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
scan-graph = ["networkx>=3.0", "pyvis>=0.3.0"]
```

### CLI Entry Point

```python
# src/dot_python/cli.py
CLI_GROUP = "python"  # Registers as `dot-work python`
```

### Standalone Script

```toml
[project.scripts]
dot-python = "dot_python.cli:app"
pybuilder = "dot_python.build.cli:main"  # Keep existing alias
```

### Test Migration

| Source | Destination |
|--------|-------------|
| `tests/unit/python/build/` | `dot-python/tests/unit/build/` |
| `tests/unit/python/scan/` | `dot-python/tests/unit/scan/` |

---

## Phase 2.8: Extract dot-review

**Source:** `src/dot_work/review/`
**Target:** `github.com/<org>/dot-review`

### Files to Move

```
src/dot_work/review/
├── __init__.py
├── cli.py
├── config.py
├── exporter.py
├── git.py
├── models.py
├── server.py
├── storage.py
├── static/
│   └── ... (JS/CSS assets)
└── templates/
    └── ... (Jinja2 templates)
```

### Dependencies (pyproject.toml)

```toml
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "fastapi>=0.115.0",
    "uvicorn>=0.32.0",
    "pydantic>=2.6.0",
    "GitPython>=3.1.0",
    "jinja2>=3.1.0",
]
```

### CLI Entry Point

```python
# src/dot_review/cli.py
CLI_GROUP = "review"  # Registers as `dot-work review`
```

### Test Migration

| Source | Destination |
|--------|-------------|
| `tests/unit/review/` (3 files) | `dot-review/tests/unit/` |
| `tests/unit/test_review_*.py` (5 files) | `dot-review/tests/unit/` |
| `tests/integration/test_server.py` | `dot-review/tests/integration/` |

---

## Phase 2.9: Extract dot-version

**Source:** `src/dot_work/version/`
**Target:** `github.com/<org>/dot-version`

### Files to Move

```
src/dot_work/version/
├── __init__.py
├── changelog.py
├── cli.py
├── commit_parser.py
├── config.py
├── manager.py
└── project_parser.py
```

### Dependencies (pyproject.toml)

```toml
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "GitPython>=3.1.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
llm = ["httpx>=0.24.0"]
```

### CLI Entry Point

```python
# src/dot_version/cli.py
CLI_GROUP = "version"  # Registers as `dot-work version`
```

### Test Migration

| Source | Destination |
|--------|-------------|
| `tests/unit/version/` (6 files) | `dot-version/tests/unit/` |

---

## Phase 3: Core Tests Remaining in dot-work

These tests remain in the main `dot-work` repository:

```
tests/unit/
├── test_canonical.py      # Core installer tests
├── test_cli.py            # Core CLI tests
├── test_environments.py   # Core environment detection
├── test_installer.py      # Core installer tests
├── test_installer_canonical.py
├── test_jinja_templates.py
├── test_json_validator.py # validate command
├── test_yaml_validator.py # validate command
├── test_wizard.py         # init wizard
├── utils/                 # Utils module tests
└── zip/                   # Zip module tests (retained)
```

---

## Phase 4: Migration Automation Script

Create a migration script to automate the extraction:

```python
#!/usr/bin/env python3
"""Automated submodule extraction script."""

import shutil
import subprocess
from pathlib import Path

EXTRACTIONS = {
    "dot-container": {
        "source_dirs": ["src/dot_work/container"],
        "test_unit": ["tests/unit/container"],
        "test_integration": ["tests/integration/container"],
        "package": "dot_container",
    },
    "dot-issues": {
        "source_dirs": ["src/dot_work/db_issues"],
        "test_unit": ["tests/unit/db_issues"],
        "test_integration": ["tests/integration/db_issues"],
        "package": "dot_issues",
    },
    # ... (other extractions)
}


def extract_project(name: str, config: dict, target_dir: Path) -> None:
    """Extract a submodule to a new project."""
    project_dir = target_dir / name
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Create directory structure
    src_dir = project_dir / "src" / config["package"]
    src_dir.mkdir(parents=True, exist_ok=True)
    
    tests_unit = project_dir / "tests" / "unit"
    tests_unit.mkdir(parents=True, exist_ok=True)
    
    tests_integration = project_dir / "tests" / "integration"
    tests_integration.mkdir(parents=True, exist_ok=True)
    
    # Copy source files
    for source in config["source_dirs"]:
        src_path = Path(source)
        if src_path.exists():
            for item in src_path.iterdir():
                if item.is_file():
                    shutil.copy2(item, src_dir / item.name)
                elif item.is_dir() and item.name != "__pycache__":
                    shutil.copytree(item, src_dir / item.name)
    
    # Copy unit tests
    for test_dir in config.get("test_unit", []):
        test_path = Path(test_dir)
        if test_path.exists():
            for item in test_path.iterdir():
                if item.name.startswith("test_") and item.suffix == ".py":
                    shutil.copy2(item, tests_unit / item.name)
                elif item.is_dir() and item.name != "__pycache__":
                    shutil.copytree(item, tests_unit / item.name)
    
    # Copy integration tests
    for test_dir in config.get("test_integration", []):
        test_path = Path(test_dir)
        if test_path.exists():
            for item in test_path.iterdir():
                if item.name.startswith("test_") and item.suffix == ".py":
                    shutil.copy2(item, tests_integration / item.name)
                elif item.is_dir() and item.name != "__pycache__":
                    shutil.copytree(item, tests_integration / item.name)
    
    print(f"Extracted {name} to {project_dir}")


if __name__ == "__main__":
    target = Path("../dot-work-plugins")
    target.mkdir(exist_ok=True)
    
    for name, config in EXTRACTIONS.items():
        extract_project(name, config, target)
```

---

## Phase 5: Import Path Updates

### 5.1 Update Imports in Extracted Projects

Each extracted project needs import path updates:

**Before (in dot-work):**
```python
from dot_work.db_issues import Issue, IssueService
from dot_work.db_issues.config import get_db_url
```

**After (in dot-issues):**
```python
from dot_issues import Issue, IssueService
from dot_issues.config import get_db_url
```

### 5.2 Script for Import Replacement

```bash
#!/bin/bash
# Run in each extracted project directory

# Example for dot-issues
find src/ tests/ -name "*.py" -exec sed -i 's/from dot_work\.db_issues/from dot_issues/g' {} \;
find src/ tests/ -name "*.py" -exec sed -i 's/import dot_work\.db_issues/import dot_issues/g' {} \;
```

---

## Phase 6: CI/CD Setup for Each Project

### GitHub Actions Workflow Template

```yaml
# .github/workflows/ci.yml
name: CI

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
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: uv sync --all-extras --dev
      
      - name: Run linting
        run: |
          uv run ruff check .
          uv run mypy src/
      
      - name: Run tests
        run: uv run pytest tests/ -v --cov=src/ --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml

  publish:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/')
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Build package
        run: uv build
      
      - name: Publish to PyPI
        run: uv publish
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}
```

---

## Phase 7: Documentation Updates

### 7.1 Main dot-work README

Update to document plugin system:

```markdown
## Installation

### Core Only (Minimal)
```bash
pip install dot-work
```

### With All Plugins
```bash
pip install dot-work[all]
```

### Selective Installation
```bash
pip install dot-work[issues,review,version]
```

### Individual Plugins
```bash
pip install dot-issues dot-review dot-version
```
```

### 7.2 Plugin Discovery Command

Add to CLI:

```bash
$ dot-work plugins
Installed Plugins:
  dot-issues v0.1.0   - SQLite-based issue tracking
  dot-review v0.1.0   - Code review UI
  dot-version v0.1.0  - Date-based versioning

Available (not installed):
  dot-container       - Docker provisioning
  dot-git             - Git history analysis
  ...
```

---

## Rollout Schedule

| Week | Phase | Deliverable |
|------|-------|-------------|
| 1 | Infrastructure | Plugin discovery system, core pyproject.toml refactor |
| 2 | Extract 1-3 | dot-container, dot-issues, dot-git |
| 3 | Extract 4-6 | dot-harness, dot-kg, dot-overview |
| 4 | Extract 7-9 | dot-python, dot-review, dot-version |
| 5 | Integration | CI/CD setup, import testing, documentation |
| 6 | Release | Publish all packages to PyPI |

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing installations | Provide `dot-work[all]` meta-package with same functionality |
| Import path changes break users | Major version bump (0.2.0), clear migration docs |
| Plugin discovery overhead | Cache discovered plugins, lazy import |
| Circular dependencies | Careful dependency analysis before extraction |
| Test isolation failures | Run full integration tests before each release |

---

## Success Criteria

1. All 9 extracted projects pass their own test suites
2. `pip install dot-work[all]` provides identical functionality to current
3. Each plugin can be installed and used independently
4. Core dot-work package size reduced by >80%
5. No import errors when mixing installed/not-installed plugins
6. Documentation updated with new installation patterns

---

## Appendix A: Dependency Matrix

| Project | typer | rich | sqlmodel | fastapi | GitPython | numpy | libcst |
|---------|-------|------|----------|---------|-----------|-------|--------|
| dot-work (core) | X | X | - | - | - | - | - |
| dot-container | X | X | - | - | - | - | - |
| dot-issues | X | X | X | - | - | - | - |
| dot-git | X | X | - | - | X | - | - |
| dot-harness | X | X | - | - | - | - | - |
| dot-kg | X | X | - | - | - | X | - |
| dot-overview | X | X | - | - | - | - | X |
| dot-python | X | X | - | - | - | - | - |
| dot-review | X | X | - | X | X | - | - |
| dot-version | X | X | - | - | X | - | - |

---

## Appendix B: Test File Counts

| Project | Unit Tests | Integration Tests | Total |
|---------|------------|-------------------|-------|
| dot-container | 2 dirs | 1 dir | ~10 files |
| dot-issues | 17 files | 6 files | 23 files |
| dot-git | 6 files | 1 file | 7 files |
| dot-harness | 2 files | 0 | 2 files |
| dot-kg | 14 files | 2 files | 16 files |
| dot-overview | 5 files | 0 | 5 files |
| dot-python | 2 dirs | 0 | ~4 files |
| dot-review | 8 files | 1 file | 9 files |
| dot-version | 6 files | 0 | 6 files |
| **Total** | **~60 files** | **~10 files** | **~70 files** |
