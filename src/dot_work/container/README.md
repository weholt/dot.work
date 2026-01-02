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
- **Context Injection**: Mount project files and configs into containers

## Context Injection (FEAT-026)

Context injection allows you to automatically mount project-specific files, documentation, and configuration into the container at runtime. This helps agents work with your project's context without manual file copying.

### Auto-Detection

When no explicit context is specified, the system auto-detects common configuration files:

- `.claude/` - Claude Code configuration directory
- `.opencode.json` - OpenCode configuration
- `.github/copilot-instructions.md` - GitHub Copilot instructions

```bash
# Auto-detect context files from current directory
dot-work container provision instructions.md
```

### Explicit Context

Mount specific files or directories:

```bash
# Mount specific files
dot-work container provision instructions.md \
    --context README.md \
    --context CONTRIBUTING.md

# Mount directories
dot-work container provision instructions.md \
    --context docs/ \
    --context .claude/

# Combine files and directories
dot-work container provision instructions.md \
    --context README.md \
    --context docs/
```

### Allowlist/Denylist

Control which files are auto-detected using glob patterns:

```bash
# Via CLI flags
dot-work container provision instructions.md \
    --context-allowlist "*.md:*.json" \
    --context-denylist "*.pyc:node_modules/"

# Via environment variables
export CONTEXT_ALLOWLIST="*.md:*.json"
export CONTEXT_DENYLIST="*.pyc:node_modules/"
dot-work container provision instructions.md
```

### Override Behavior

By default, context mounts skip if the target exists in the container. Use `--context-override` to force mounting over existing files:

```bash
# Override existing container files
dot-work container provision instructions.md \
    --context .claude/ \
    --context-override
```

### Custom Mount Point

By default, context files are mounted to `/root/.context/` inside the container. Customize this with:

```bash
dot-work container provision instructions.md \
    --context README.md \
    --context-mount-point /workspace/context/
```

### Verification

Verify mounted files inside a running container:

```bash
# List mounted context files
docker exec <container-id> ls -la /root/.context/

# View a mounted file
docker exec <container-id> cat /root/.context/README.md
```

## Module Structure

```
container/
├── __init__.py          # Package exports
├── provision/           # Main provisioning logic
│   ├── cli.py          # CLI commands (run, init, validate)
│   ├── core.py         # Docker and Git operations
│   ├── templates.py    # Instruction templates
│   ├── validation.py   # Frontmatter validation
│   └── context.py      # Context injection (FEAT-026)
└── README.md           # This file
```