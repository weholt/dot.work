# dot-work Plugin Architecture

This document describes the plugin architecture for dot-work, including available plugins, installation instructions, and usage examples.

## Overview

dot-work has been split into a **core package** and **optional plugins**. The core package provides essential functionality (prompt installation, environment detection, validation), while plugins provide specialized features like issue tracking, knowledge graphs, code review, and more.

## Available Plugins

| Plugin | Description | CLI Command |
|--------|-------------|-------------|
| **dot-issues** | SQLite-based issue tracking for autonomous agents | `dot-work db-issues` |
| **dot-kg** | Knowledge graph with FTS5 search for code analysis | `dot-work kg` |
| **dot-review** | Interactive code review with AI-friendly export | `dot-work review` |
| **dot-container** | Docker provisioning for AI coding agents | `dot-work container` |
| **dot-git** | Git history analysis and complexity metrics | `dot-work git` |
| **dot-harness** | Claude Agent SDK integration | `dot-work harness` |
| **dot-overview** | Codebase overview generation with AST parsing | `dot-work overview` |
| **dot-python** | Python project build and scan utilities | `dot-work python` |
| **dot-version** | Date-based version management | `dot-work version` |

## Installation

### Core Package

Install the core dot-work package (includes prompt installation, environment detection, validation):

```bash
# With uv
uv tool install dot-work

# With pip
pip install dot-work
```

### Installing Plugins

Each plugin is a separate package that can be installed independently:

```bash
# Install individual plugins
pip install dot-issues     # Issue tracking
pip install dot-kg         # Knowledge graph
pip install dot-review     # Code review

# Install multiple plugins
pip install dot-issues dot-kg dot-review

# Install all plugins
pip install dot-issues dot-kg dot-review dot-container dot-git dot-harness dot-overview dot-python dot-version
```

### Installing Plugins with uv

```bash
# With uv tool
uv tool install dot-issues
uv tool install dot-kg
uv tool install dot-review
```

### Optional Plugin Features

Some plugins have optional dependencies for additional features:

```bash
# dot-kg: HTTP embeddings, ANN, vector search
pip install "dot-kg[http,ann,vec]"

# dot-git: LLM-based commit summarization
pip install "dot-git[llm]"

# dot-python: Dependency graph visualization
pip install "dot-python[scan-graph]"

# dot-version: LLM-enhanced changelog
pip install "dot-version[llm]"

# dot-harness: Claude Agent SDK
pip install "dot-harness[sdk]"
```

## Usage

After installing plugins, they automatically register with the dot-work CLI:

```bash
# List installed plugins
dot-work plugins

# Use plugin commands
dot-work db-issues create --title "Fix bug" --priority high
dot-work kg init
dot-work review start
dot-work git analyze
dot-work version freeze
```

### Standalone Plugin Usage

Plugins can also be used as standalone CLIs:

```bash
# Use dot-issues standalone
dot-issues create --title "Fix bug" --priority high

# Use dot-kg standalone
kg init

# Use dot-review standalone
dot-review start

# Use dot-git standalone
dot-git analyze

# Use dot-version standalone
dot-version freeze
```

## Plugin Discovery

The `dot-work plugins` command lists all installed plugins:

```bash
$ dot-work plugins

Installed Plugins:
┏━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Name       ┃ Command   ┃ Version ┃ Module           ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ dot-issues │ db-issues │ 0.1.0   │ dot_issues      │
│ dot-kg     │ kg        │ 0.1.0   │ dot_kg          │
│ dot-review │ review    │ 0.1.0   │ dot_review      │
└────────────┴───────────┴─────────┴─────────────────┘

✓ 3 plugin(s) installed
```

## Architecture

### Core Package

The core dot-work package includes:

- **Prompt installation**: Install AI agent prompts to various environments (Copilot, Claude, Cursor, etc.)
- **Environment detection**: Auto-detect AI coding environment
- **Validation**: JSON/YAML file validation
- **Plugin discovery**: Dynamic plugin registration via entry points

### Plugin Structure

Each plugin is a standalone package with:

- `pyproject.toml` with `[project.entry-points."dot_work.plugins"]` registration
- `src/<package>/__init__.py` with `CLI_GROUP` variable
- Typer-based CLI app exposed as `app`
- Tests in `tests/unit/` and `tests/integration/`
- README.md with usage examples

### Plugin Registration

Plugins register themselves via Python entry points:

```toml
[project.entry-points."dot_work.plugins"]
issues = "dot_issues"
```

The `CLI_GROUP` variable in `__init__.py` specifies the command name:

```python
"""dot_issues module."""

CLI_GROUP = "db-issues"
```

## Migration Guide

### For Existing Users

If you were using dot-work before the plugin split:

1. **Core functionality remains the same**: `install`, `list`, `detect`, `validate`, `prompt` commands work as before
2. **Plugin commands require plugin installation**: Commands like `db-issues`, `kg`, `review` now require installing the corresponding plugin
3. **Backward compatibility**: The current dot-work package still includes all submodules during the migration period

### Migration Steps

1. **Install core dot-work**:
   ```bash
   pip install --upgrade dot-work
   ```

2. **Install your required plugins**:
   ```bash
   pip install dot-issues dot-kg dot-review
   ```

3. **Verify plugin installation**:
   ```bash
   dot-work plugins
   ```

### Breaking Changes

- **Removed submodule dependencies**: The core dot-work package no longer includes dependencies for extracted plugins (e.g., `sqlmodel`, `numpy`, `fastapi`)
- **Plugin installation required**: Plugin-specific commands will show a "command not found" error if the plugin is not installed

## Development

### Creating a Plugin

To create a new dot-work plugin:

1. **Create package structure**:
   ```
   my-plugin/
   ├── src/
   │   └── my_plugin/
   │       ├── __init__.py  # Define CLI_GROUP and app
   │       └── cli.py
   ├── tests/
   │   └── unit/
   └── pyproject.toml
   ```

2. **Configure entry points** in `pyproject.toml`:
   ```toml
   [project.entry-points."dot_work.plugins"]
   myplugin = "my_plugin"
   ```

3. **Define CLI_GROUP** in `__init__.py`:
   ```python
   """my_plugin module."""

   CLI_GROUP = "my-cmd"

   from typer import Typer
   app = Typer()
   ```

4. **Install and test**:
   ```bash
   pip install -e my-plugin
   dot-work plugins  # Should show my-plugin
   dot-work my-cmd --help
   ```

### Extracting a Plugin

Use the provided extraction script to extract a submodule from dot-work:

```bash
# Dry run
python scripts/extract_plugin.py my-plugin --dry-run

# Extract to EXPORTED_PROJECTS/
python scripts/extract_plugin.py my-plugin

# Extract to custom directory
python scripts/extract_plugin.py my-plugin --output ../my-plugin
```

## Status

The plugin architecture migration is **in progress**:

- ✅ Core infrastructure: Plugin discovery and registration (SPLIT-100)
- ✅ High-priority extractions: dot-issues, dot-kg, dot-review (SPLIT-101)
- ✅ Medium-priority extractions: dot-container, dot-git, dot-harness, dot-overview, dot-python, dot-version (SPLIT-102)
- ✅ Integration testing: Plugin ecosystem tests (SPLIT-103)
- ⏳ Documentation: Plugin docs and migration guide (SPLIT-104 - in progress)
- ⏳ Publishing: Plugins will be published to PyPI after documentation is complete

## Resources

- [Main dot-work README](../README.md)
- [Extraction script](../scripts/extract_plugin.py)
- [Plugin tests](../tests/integration/test_plugin_ecosystem.py)
