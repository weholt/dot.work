# Container Provisioning

The container provisioning module enables running LLM-powered code agents in Docker containers to modify GitHub repositories and create pull requests.

## Usage

```bash
# Initialize a new instruction template
dot-work container provision init instructions.md

# Validate instruction file
dot-work container provision validate instructions.md

# Run provisioning on a repository
dot-work container provision instructions.md

# With custom options
dot-work container provision instructions.md \
    --repo-url https://github.com/user/repo \
    --branch feature/new \
    --dry-run \
    --docker-image custom-image:latest
```

## Features

- **Template Generation**: Create instruction templates with proper frontmatter
- **Validation**: Verify instruction files have required fields
- **Docker Integration**: Run agents in isolated containers
- **Git Operations**: Clone repositories, create branches, submit PRs
- **Dry Run Mode**: Preview changes without executing

## Module Structure

```
container/
├── __init__.py          # Package exports
├── provision/           # Main provisioning logic
│   ├── cli.py          # CLI commands (run, init, validate)
│   ├── core.py         # Docker and Git operations
│   ├── templates.py    # Instruction templates
│   └── validation.py   # Frontmatter validation
└── README.md           # This file
```