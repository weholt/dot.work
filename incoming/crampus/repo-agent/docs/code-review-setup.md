# Code Review Configuration

This repository uses CodeRabbit for automated code reviews. The configuration is defined in `.coderabbit.yaml` at the repository root.

## Overview

The configuration enables:

- **Assertive review profile**: Comprehensive code analysis with detailed feedback
- **Automated PR reviews**: Automatically reviews pull requests with AI-powered insights
- **Python-specific guidelines**: Special rules for Python code including typing, dataclasses, EAFP, context managers, and pathlib usage
- **Pre-merge checks**: Validates docstrings, PR titles, descriptions, and custom rules
- **Custom quality checks**: 
  - Single Responsibility Principle (SRP) enforcement
  - Layer boundary violation detection
  - Magic values detection

## Configuration Sections

### Reviews

The review section controls how CodeRabbit analyzes pull requests:

- High-level summaries of key changes
- Automatic title generation following `<area>: <action>` format
- Change file summaries and sequence diagrams
- Code review effort estimation
- Related issues and PRs detection
- Suggested labels and reviewers

### Pre-merge Checks

Quality gates that run before merging:

1. **Docstrings**: Warns if docstring coverage is below 80%
2. **PR Title**: Validates title format (`<area>: <action>`, under 50 chars)
3. **Description**: Checks for adequate PR description
4. **Custom Checks**:
   - **SRP enforcement** (error): Ensures single responsibility principle
   - **Layer boundary violation** (error): Prevents cross-layer imports
   - **Magic values** (warning): Detects hardcoded values

### Tools Integration

The configuration enables these tools:

- **ruff**: Python linter and formatter
- **shellcheck**: Shell script analysis
- **markdownlint**: Markdown formatting
- **ast-grep**: Advanced code pattern matching
- **github-checks**: GitHub native checks integration

### Code Generation

Automated generation capabilities:

- **Docstrings**: Generates Google-style docstrings for Python code
- **Unit tests**: Creates pytest tests for source code with edge cases and error handling

## Path-specific Instructions

### Python Files (`**/*.py`)

Apply Python best practices:
- Type hints and annotations
- Dataclasses for data structures
- EAFP (Easier to Ask for Forgiveness than Permission) pattern
- Context managers for resource handling
- pathlib for file operations

### Infrastructure (`infra/**`)

Special rules for infrastructure code:
- Use abstractions and interfaces
- Avoid mixing domain logic with infrastructure concerns

## Knowledge Base

CodeRabbit can use external resources:

- Web search for up-to-date information
- Custom code guidelines from `.prompt.md` files:
  - `best-practices-check.prompt.md`
  - `code-analysis.prompt.md`
  - `pythonic-code.prompt.md`

## Usage

CodeRabbit automatically reviews pull requests when:

1. A new PR is opened
2. New commits are pushed to an existing PR
3. A reviewer requests changes

### Triggering Reviews

Use these commands in PR comments:

- `@coderabbitai summary` - Generate high-level summary
- `@coderabbitai` - Trigger manual review or re-review

### Review Output

CodeRabbit provides:

- Line-by-line code comments
- Overall PR summary
- Detected issues with severity levels
- Suggestions for improvements
- Links to related issues/PRs

## Customization

To modify the configuration:

1. Edit `.coderabbit.yaml`
2. Validate changes locally (see validation script below)
3. Create a PR with your changes
4. CodeRabbit will use the new configuration after merge

### Validation Script

```python
import yaml

with open('.coderabbit.yaml', 'r') as f:
    config = yaml.safe_load(f)
    print("✓ Configuration is valid")
```

## References

- [CodeRabbit Documentation](https://docs.coderabbit.ai/)
- [CodeRabbit Configuration Schema](https://docs.coderabbit.ai/guides/configure-coderabbit/)
