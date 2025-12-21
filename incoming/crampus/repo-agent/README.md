# repo-agent

A configurable tool that runs LLM-powered code agents in Docker to automatically modify GitHub repositories and create pull requests.

## Features

- **Fully configurable**: Use any LLM-based code tool (OpenCode, Claude Code, Copilot CLI, Gemini CLI, etc.)
- **Docker-based**: Isolated execution environment with ephemeral workspaces
- **Markdown-driven**: Define everything in a single markdown file with frontmatter
- **Flexible authentication**: Support for GitHub tokens or SSH keys
- **Auto-branching**: Automatically creates feature branches
- **Auto-repository creation**: Optionally create GitHub repositories if they don't exist
- **PR automation**: Creates pull requests with customizable titles and descriptions
- **CLI and frontmatter**: Override any setting via command line
- **Validation tools**: Validate instruction files before running
- **Template generation**: Generate valid instruction templates

## Installation

### Using uvx (recommended)

```bash
uvx repo-agent run instructions.md
```

### Install with uv

```bash
uv tool install repo-agent
```

### Install with pip

```bash
pip install repo-agent
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/repo-agent.git
cd repo-agent

# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest tests/ --cov=src/repo_agent
```

## Quick Start

### 1. Generate an instruction template

```bash
repo-agent init instructions.md
```

### 2. Edit the instruction file

Edit `instructions.md` with your repository URL, model, and instructions.

### 3. Validate the instruction file

```bash
repo-agent validate instructions.md
```

### 4. Run the agent

```bash
repo-agent run instructions.md
```

## Docker Images

### Ubuntu-based (default)

```bash
docker build -t repo-agent:latest -f Dockerfile .
```

With optional tools:

```bash
# All tools
docker build -t repo-agent:all \
  --build-arg INSTALL_NODE_TOOLS=1 \
  --build-arg INSTALL_OPENCODE=1 \
  -f Dockerfile .

# Node tools only
docker build -t repo-agent:node \
  --build-arg INSTALL_NODE_TOOLS=1 \
  -f Dockerfile .
```

### Alpine-based (minimal)

Smallest possible image (~60-180MB depending on tools):

```bash
# Minimal (Python + Git only)
docker build -t repo-agent:alpine -f Dockerfile.smart-alpine .

# With Node.js
docker build -t repo-agent:alpine-node \
  --build-arg ENABLE_NODE=1 \
  -f Dockerfile.smart-alpine .

# Full featured
docker build -t repo-agent:alpine-full \
  --build-arg ENABLE_NODE=1 \
  --build-arg ENABLE_NODE_TOOLS=1 \
  --build-arg ENABLE_GH=1 \
  --build-arg ENABLE_PY_EXTRAS=1 \
  -f Dockerfile.smart-alpine .
```

## Instruction File Format

```markdown
---
# Required
repo_url: "https://github.com/your/repo.git"
model: "openai/gpt-4.1-mini"

# Branching
base_branch: "main"
branch: "auto/feature"

# Docker
docker_image: "repo-agent:latest"

# Authentication
use_ssh: false
github_token_env: "GITHUB_TOKEN"

# Strategy
strategy: "agentic"   # or "direct"

# Tool configuration
tool:
  name: "opencode"
  entrypoint: "opencode run"
  args:
    strategy: "agentic"

# Git / PR
auto_commit: true
create_pr: true
create_repo_if_missing: false  # Auto-create repo if it doesn't exist
pr_title: "Automated update"
---

# Your instructions here

Describe the changes you want made...
```

## CLI Commands

### run

Run the agent with an instruction file:

```bash
repo-agent run instructions.md
```

Override settings:

```bash
repo-agent run instructions.md \
  --repo-url https://github.com/user/repo.git \
  --branch feature/new-feature \
  --model openai/gpt-4 \
  --strategy direct \
  --dry-run
```

### init

Generate a template instruction file:

```bash
repo-agent init instructions.md
```

Force overwrite existing file:

```bash
repo-agent init instructions.md --force
```

### validate

Validate an instruction file:

```bash
repo-agent validate instructions.md
```

## Supported Tools

The agent is tool-agnostic. Configure any tool via frontmatter:

### OpenCode

```yaml
tool:
  name: "opencode"
  entrypoint: "opencode run"
  args:
    strategy: "agentic"
```

### Claude Code

```yaml
tool:
  name: "claude-code"
  entrypoint: "claude-code"
  args:
    model: "claude-3.7-sonnet"
```

### GitHub Copilot CLI

```yaml
tool:
  name: "copilot"
  entrypoint: "github-copilot-cli edit"
  args:
    model: "gpt-5.1"
```

### Gemini CLI

```yaml
tool:
  name: "gemini"
  entrypoint: "gemini code"
```

## Authentication

### GitHub Token (HTTPS)

Set via environment variable:

```bash
export GITHUB_TOKEN=ghp_xxxxx
repo-agent run instructions.md
```

Or in frontmatter:

```yaml
github_token_env: "GITHUB_TOKEN"
```

### SSH Keys

```yaml
use_ssh: true
ssh_key_dir: "~/.ssh"
```

## Repository Creation

The agent can automatically create a GitHub repository if it doesn't exist. This is useful for:

- Setting up new projects from scratch
- Creating repositories in CI/CD pipelines
- Automated project scaffolding

Enable this feature in frontmatter:

```yaml
create_repo_if_missing: true
```

Or via CLI:

```bash
repo-agent run instructions.md --create-repo
```

**Note**: Requires a valid GitHub token with `repo` scope permissions. The repository will be created as **private** by default.

## GitHub Actions Integration

```yaml
name: repo-agent

on:
  workflow_dispatch:
    inputs:
      instructions:
        description: "Path to instructions file"
        required: true
        default: ".github/repo-agent/instructions.md"

permissions:
  contents: write
  pull-requests: write

jobs:
  run-repo-agent:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
        
      - name: Run repo-agent
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          uvx repo-agent "${{ github.workspace }}/${{ github.event.inputs.instructions }}"
```

## Testing

The project has comprehensive test coverage:

- **96% code coverage** (exceeds 80% target)
- **87 tests** covering unit and integration scenarios
- **Fast execution** with mocked external dependencies

Run tests:

```bash
# Set PYTHONPATH and run all tests
$env:PYTHONPATH="$PWD\src"
pytest tests/ -v

# Run with coverage report
$env:PYTHONPATH="$PWD\src"
pytest tests/ --cov=src/repo_agent --cov-report=html

# Quick test run
$env:PYTHONPATH="$PWD\src"
pytest tests/ -q
```

See [TEST_COVERAGE.md](TEST_COVERAGE.md) for detailed coverage information.

## Code Review

This repository uses CodeRabbit for automated code reviews. The configuration is in `.coderabbit.yaml` and provides:

- **Assertive review profile**: Comprehensive code analysis with detailed feedback
- **Python-specific guidelines**: Type hints, dataclasses, EAFP, context managers, pathlib
- **Custom quality checks**: SRP enforcement, layer boundary violations, magic values detection
- **Pre-merge validation**: Docstring coverage (80%), PR title/description format
- **Tool integration**: ruff, shellcheck, markdownlint, github-checks

See [docs/code-review-setup.md](docs/code-review-setup.md) for detailed configuration and usage.

## Examples

See the [examples/](examples/) directory for complete examples.

## License

MIT
