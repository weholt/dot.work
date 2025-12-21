# Regression Guard

A multi-agent iterative validation system that prevents code regressions by breaking tasks into atomic subtasks and validating each incrementally.

## Features

- **Task Decomposition** - Breaks complex changes into atomic, testable subtasks
- **Baseline Capture** - Records system state before changes
- **Incremental Validation** - Tests each subtask independently
- **Integration Validation** - Ensures system-wide compatibility
- **Automated Reporting** - Generates detailed validation reports
- **Risk Assessment** - Identifies high-risk changes requiring extra scrutiny

## Installation

```bash
pip install regression-guard
```

Or for development:

```bash
git clone https://github.com/your-username/regression-guard
cd regression-guard
pip install -e ".[dev]"
```

## Quick Start

### 1. Start a New Task

```bash
regression-guard start "Add new feature X"
```

This will:
- Generate a unique task ID
- Decompose your task into subtasks
- Capture baseline system state
- Create a task manifest

### 2. Implement and Validate Subtasks

```bash
# Implement your first subtask
# ... make code changes ...

# Validate the subtask
regression-guard validate subtask-1-create

# Continue with remaining subtasks
```

### 3. Finalize the Task

```bash
regression-guard finalize task-20251125-120000
```

This runs full integration validation and generates a final report.

## Usage

### Commands

```bash
# Start new task
regression-guard start "Task description"

# Show task status
regression-guard status <task-id>

# Validate subtask
regression-guard validate <subtask-id>

# Finalize task
regression-guard finalize <task-id>

# List all tasks
regression-guard list
```

### Workflow

```
START → Decompose + Baseline → IMPLEMENT → VALIDATE → REPEAT → FINALIZE
```

### Validation Checks

Each subtask validation verifies:
- ✅ Baseline tests still pass (no regressions)
- ✅ New tests exist and pass
- ✅ Coverage doesn't decrease
- ✅ Build passes (lint, format, type check)

## Configuration

Regression Guard works with any Python project. It expects:

1. **pytest** for running tests
2. **Standard project structure** with `tests/` directory
3. **.work/tasks/** directory for task tracking (auto-created)

## Integration

### With CI/CD

```yaml
# .github/workflows/regression-check.yml
name: Regression Check

on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install regression-guard
        run: pip install regression-guard
      
      - name: Find task
        run: |
          TASK_ID=$(ls .work/tasks/ | head -n 1)
          echo "TASK_ID=$TASK_ID" >> $GITHUB_ENV
      
      - name: Run validation
        run: regression-guard finalize ${{ env.TASK_ID }}
```

### With Pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: regression-guard
        name: Regression Guard Validation
        entry: regression-guard validate
        language: system
        pass_filenames: false
```

## Architecture

### Components

1. **Orchestrator** (`cli.py`) - Main entry point, coordinates workflow
2. **Decomposer** (`decompose.py`) - Breaks tasks into subtasks
3. **Baseline Capturer** (`capture_baseline.py`) - Records pre-change state
4. **Incremental Validator** (`validate_incremental.py`) - Tests subtasks
5. **Integration Validator** (`validate_integration.py`) - System-wide tests

### Task Structure

```
.work/tasks/<task-id>/
  manifest.json           # Task decomposition
  baseline.json           # Pre-change state
  <subtask-id>/
    validation.json       # Validation results
    report.md            # Human-readable report
  integration/
    validation.json
  final_report.md        # Overall summary
```

## Best Practices

1. **Keep subtasks atomic** - < 1 hour each
2. **Validate frequently** - After every subtask
3. **Fix failures immediately** - Before proceeding
4. **Review reports** - Understand what changed
5. **Don't skip integration** - Always finalize

## Examples

See `docs/` directory for:
- [Usage Guide](docs/usage-guide.md)
- [Quick Reference](docs/quick-reference.md)
- [Integration Examples](docs/integration-examples.md)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy regression_guard/
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: https://github.com/your-username/regression-guard/issues
- **Discussions**: https://github.com/your-username/regression-guard/discussions
- **Documentation**: https://github.com/your-username/regression-guard/tree/main/docs
