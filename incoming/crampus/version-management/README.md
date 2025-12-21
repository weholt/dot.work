# Version Management Tool

A reusable date-based version management tool with automatic changelog generation from conventional commits.

## Features

- **Date-based versioning**: `YYYY.MM.build-number` format
- **Conventional commits**: Parse and categorize git commits
- **Automatic changelogs**: Generate comprehensive release notes
- **Project metadata**: Auto-detects project name from `pyproject.toml`
- **Git integration**: Create tags, track commits
- **Optional LLM summaries**: Enhanced changelogs via Ollama
- **CLI interface**: Simple commands for version management

## Installation

### From Source

```bash
cd tools/version-management
uv pip install -e .
```

### With LLM Support

```bash
uv pip install -e ".[llm]"
```

## Quick Start

### Initialize Version

```bash
# Create initial version.json
version-management init

# Or with specific version
version-management init --version 2025.10.001
```

### Freeze New Version

```bash
# Create new version with changelog
version-management freeze

# With LLM-enhanced summary
version-management freeze --llm

# Dry run (preview without changes)
version-management freeze --dry-run
```

### View Version Info

```bash
# Show current version
version-management show

# Show version history
version-management history

# Show git commits since last tag
version-management commits
```

## Configuration

Create `.version-management.yaml` in your project root:

```yaml
format: "YYYY.MM.build-number"
tag_prefix: "version-"

changelog:
  file: "CHANGELOG.md"
  template: null  # Use default or specify custom template path
  include_authors: true
  group_by_type: true

commit_types:
  feat: "Features"
  fix: "Bug Fixes"
  docs: "Documentation"
  chore: "Internal Changes"
  test: "Tests"
  refactor: "Refactoring"
  perf: "Performance"
  ci: "CI/CD"
  build: "Build System"
  style: "Code Style"

highlights:
  enabled: true
  min_commits: 5
  keywords:
    - "breaking"
    - "security"
    - "performance"

statistics:
  enabled: true

llm:
  enabled: false
  ollama_url: "http://localhost:11434"
  model: "llama3.2:3b"
```

## Project Metadata

The tool automatically detects your project name and metadata from `pyproject.toml`:

```toml
[project]
name = "my-awesome-project"
version = "1.0.0"
description = "My project description"
```

This information is used in:
- Changelog headers: `# my-awesome-project - Version 2025.10.001`
- Version metadata tracking
- Git tag messages

If no `pyproject.toml` is found, the tool falls back to using the current directory name.

## Environment Variables

```env
VERSION_LLM_ENABLED=false
VERSION_LLM_MODEL=llama3.2:3b
VERSION_AUTO_PUSH=false
```

## Version Format

The tool uses date-based versioning:

- `YYYY` - 4-digit year
- `MM` - 2-digit month (01-12)
- `build-number` - 5-digit build number (00001-99999)

Examples:
- `2025.10.00001` - First build in October 2025
- `2025.10.00042` - 42nd build in October 2025
- `2025.11.00001` - Resets to 1 in November 2025

## Conventional Commits

The tool parses conventional commit messages:

```
type(scope): subject

body

footer
```

Supported types:
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `chore`: Maintenance tasks
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `ci`: CI/CD changes
- `build`: Build system changes
- `style`: Code style changes

## Integration with Build Systems

### Python (build.py)

```python
from version_management import VersionManager

def version_freeze_step():
    """Freeze new version as part of build pipeline."""
    manager = VersionManager(project_root=Path.cwd())
    result = manager.freeze_version(
        use_llm=False,
        dry_run=False
    )
    return result.success
```

### CI/CD (GitHub Actions)

```yaml
name: Release
on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - name: Install version-management
        run: pip install version-management
      - name: Freeze version
        run: version-management freeze
      - name: Push tags
        run: git push --tags
```

## Development

### Setup

```bash
cd tools/version-management
uv pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Format Code

```bash
black .
ruff check --fix .
```

## License

MIT License - See LICENSE file for details
