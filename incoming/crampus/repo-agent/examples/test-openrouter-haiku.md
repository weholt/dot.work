---
# Repository Configuration
repo_url: "https://github.com/YOUR-USERNAME/test-repo.git"
base_branch: "main"
branch: "auto/test-haiku"

# Docker Configuration
docker_image: "repo-agent:latest"

# Authentication - reads from environment variables (load with: . .\load-env.ps1)
github_token_env: "GITHUB_TOKEN"  # Reads from $env:GITHUB_TOKEN
use_ssh: false

# Model Configuration - OpenRouter with Claude 3.5 Haiku
model: "anthropic/claude-3.5-haiku"  # OpenRouter model identifier
api_key_env: "OPENROUTER_API_KEY"  # Reads from $env:OPENROUTER_API_KEY
strategy: "agentic"

# Tool Configuration - OpenCode with OpenRouter
tool:
  name: "opencode"
  entrypoint: "opencode run"
  args:
    # OpenCode needs to be configured to use OpenRouter's endpoint
    # The OpenRouter API is OpenAI-compatible
    base-url: "https://openrouter.ai/api/v1"
    # OpenCode will read the API key from OPENROUTER_API_KEY env var

  prompt_header_agentic: |
    You are an autonomous coding agent using Claude 3.5 Haiku via OpenRouter.
    Plan your approach carefully, then execute the necessary code changes.
    Keep changes minimal and focused.

  prompt_header_direct: |
    Apply the following changes directly to this repository.
    Use Claude 3.5 Haiku's speed to make quick, focused edits.

# Git and Pull Request Configuration
git_user_name: "weholt"
git_user_email: "thomas@weholt.org"
auto_commit: true
create_pr: true
create_repo_if_missing: false
commit_message: "test: using Claude 3.5 Haiku via OpenRouter"
pr_title: "🧪 Test PR with Claude 3.5 Haiku"
pr_body: |
  This PR was generated automatically using **Claude 3.5 Haiku** via **OpenRouter**.
  
  ## Configuration
  - **Provider**: OpenRouter
  - **Model**: anthropic/claude-3.5-haiku
  - **Strategy**: agentic
  
  Testing the integration of OpenRouter with repo-agent.
---

# Instructions

## Objective

Add a simple README improvement or fix a typo.

## Task

Update the README.md file to:
1. Fix any obvious typos or grammar issues
2. Add or improve a short description if one is missing
3. Ensure the file has proper markdown formatting

Keep changes minimal and focused.
