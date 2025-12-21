# Prompt Builder

A comprehensive multi-agent validation system that prevents code regressions by breaking tasks into atomic subtasks and validating each incrementally.

## Features

- **Task Decomposition** - Automatically breaks complex changes into atomic, testable subtasks
- **Multi-Agent Validation** - Six specialized agents working together:
  - **Planner Agent** - Decomposes tasks and creates validation contracts
  - **Static Validator Agent** - Checks syntax, imports, typing, and conventions
  - **Behavior Validator Agent** - Runs tests and validates runtime behavior
  - **Regression Sentinel Agent** - Detects regressions by comparing with previous behavior
  - **Synthetic Test Agent** - Generates tests for uncovered code paths
  - **PR Generator Agent** - Creates pull requests when all validations pass
- **Incremental Validation** - Tests each subtask independently
- **Comprehensive Reporting** - Detailed validation reports with metrics and issue tracking
- **Git Integration** - Works with existing git workflows
- **Configurable** - Flexible configuration for different project needs

## Installation

```bash
pip install prompt-builder
```

Or for development:

```bash
git clone https://github.com/your-username/prompt-builder.git
cd prompt-builder
pip install -e ".[dev]"
```

## Quick Start

### 1. Initialize Project

```bash
prompt-builder init
```

This creates a `prompt-builder.toml` configuration file and necessary directories.

### 2. Start a Validation Task

```bash
prompt-builder start "Add user authentication with JWT tokens"
```

### 3. Monitor Progress

The system will:
1. Decompose your task into atomic subtasks
2. Run validation agents for each subtask
3. Generate synthetic tests for uncovered code
4. Check for regressions
5. Create a pull request if all validations pass

### 4. Check Results

```bash
prompt-builder list-tasks
prompt-builder status TASK-20231125-143000
```

## Command Line Interface

### Basic Commands

```bash
# Start a new validation task
prompt-builder start "Task description" --title "Brief Title"

# Check task status
prompt-builder status TASK-20231125-143000

# List all tasks
prompt-builder list-tasks

# Run validation on existing task
prompt-builder validate TASK-20231125-143000 --create-pr

# Initialize configuration
prompt-builder init
```

### Advanced Options

```bash
# Specify git references for comparison
prompt-builder start "Fix login bug" --base HEAD~2 --head HEAD

# Run specific agents only
prompt-builder validate TASK-ID --agent static_validator --agent behavior_validator

# Enable verbose logging
prompt-builder start "Add feature" --verbose

# Dry run (show what would happen)
prompt-builder start "Add feature" --dry-run
```

## Configuration

Create a `prompt-builder.toml` file:

```toml
[agents.planner]
enabled = true
timeout = 300
max_retries = 3

[agents.static_validator]
enabled = true
timeout = 180
max_retries = 3

[agents.behavior_validator]
enabled = true
timeout = 600
max_retries = 3

[agents.regression_sentinel]
enabled = true
timeout = 240
max_retries = 3

[agents.synthetic_test]
enabled = true
timeout = 300
max_retries = 3

[agents.pr_generator]
enabled = true
timeout = 120
max_retries = 3

[git]
auto_push = false
pr_auto_merge = false
default_base = "main"

[notifications]
on_failure = true
on_success = false

[paths]
tasks_dir = ".prompt-builder/tasks"
snapshots_dir = ".prompt-builder/snapshots"
synthetic_tests_dir = "tests/synthetic"
logs_dir = ".prompt-builder/logs"
```

## Agent Details

### Planner Agent

Decomposes high-level tasks into atomic subtasks with validation contracts.

**Example output:**
```json
{
  "subtask_id": "TASK-001-ST-001",
  "summary": "Implement JWT token validation middleware",
  "preconditions": ["Authentication system exists"],
  "postconditions": ["JWT tokens are validated", "Invalid tokens are rejected"],
  "test_cases": ["Test valid token", "Test expired token", "Test malformed token"]
}
```

### Static Validator Agent

Performs compile-time safety checks:
- Syntax validation
- Import checking
- Type hint validation
- Code convention adherence

### Behavior Validator Agent

Validates runtime behavior:
- Runs test suites
- Checks acceptance criteria
- Validates postconditions
- Monitors behavior invariants

### Regression Sentinel Agent

Detects regressions by:
- Analyzing git changes
- Comparing with behavior snapshots
- Checking semantic invariants
- Risk assessment

### Synthetic Test Agent

Generates additional tests for:
- Uncovered code paths
- Edge cases
- Boundary values
- Error conditions

### PR Generator Agent

Creates pull requests when:
- All validations pass
- No critical issues found
- Task is complete
- Tests are passing

## Integration with CI/CD

### GitHub Actions

```yaml
name: Prompt Builder Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install prompt-builder
        run: pip install prompt-builder

      - name: Run validation
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            prompt-builder start "Validate PR changes" \
              --base ${{ github.base_ref }} \
              --head ${{ github.head_ref }}
          else
            prompt-builder start "Validate push" \
              --base HEAD~1 \
              --head HEAD
          fi
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### GitLab CI

```yaml
validation:
  stage: test
  image: python:3.11
  before_script:
    - pip install prompt-builder
  script:
    - prompt-builder start "Validate changes" --base $CI_COMMIT_BEFORE_SHA --head $CI_COMMIT_SHA
  artifacts:
    reports:
      junit: .prompt-builder/reports/*.xml
```

## Examples

### Example 1: Feature Development

```bash
# Start a new feature
prompt-builder start "Add user profile page with avatar upload"

# The system will:
# 1. Break it into subtasks:
#    - Create profile model
#    - Implement avatar upload service
#    - Create profile page component
#    - Add profile API endpoints
#    - Write tests for profile functionality
#
# 2. Validate each subtask with all agents
# 3. Generate additional tests for edge cases
# 4. Check for regressions in existing functionality
# 5. Create PR if everything passes
```

### Example 2: Bug Fix

```bash
# Fix a specific bug
prompt-builder start "Fix memory leak in data processing pipeline"

# The system will:
# 1. Decompose the fix into manageable changes
# 2. Validate that the fix actually resolves the issue
# 3. Ensure no new regressions are introduced
# 4. Generate regression tests
# 5. Create PR with comprehensive validation
```

### Example 3: Refactoring

```bash
# Refactor existing code
prompt-builder start "Refactor authentication service for better testability"

# The system will:
# 1. Identify atomic refactoring steps
# 2. Validate each step preserves functionality
# 3. Generate new tests for refactored code
# 4. Check for subtle behavior changes
# 5. Ensure performance is maintained
```

## Troubleshooting

### Common Issues

1. **Git Repository Required**
   ```bash
   error: Not in a git repository - cannot create PR
   ```
   Ensure you're in a git repository.

2. **Missing Test Runner**
   ```bash
   warning: Test runner not found - skipping test execution
   ```
   Install pytest or configure your test runner.

3. **Permission Issues**
   ```bash
   error: Failed to create .prompt-builder directory
   ```
   Check directory permissions.

### Debug Mode

Enable verbose logging for detailed output:

```bash
prompt-builder start "Task description" --verbose
```

### Log Files

Check log files for detailed error information:

```bash
tail -f .prompt-builder/logs/prompt-builder.log
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/your-username/prompt-builder.git
cd prompt-builder
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
pytest --cov=src/prompt_builder
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy src/prompt_builder/
```

### Build and Install

```bash
pip install build
python -m build
pip install dist/prompt_builder-*.whl
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: https://github.com/your-username/prompt-builder/issues
- **Discussions**: https://github.com/your-username/prompt-builder/discussions
- **Documentation**: https://github.com/your-username/prompt-builder/wiki

## Acknowledgments

Built with inspiration from:
- Multi-agent validation patterns
- Git workflow best practices
- Continuous integration methodologies
- Modern Python development practices