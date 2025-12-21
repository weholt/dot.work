---
# Required
repo_url: "https://github.com/your/repo.git"
model: "openai/gpt-4.1-mini"

# Branching (optional)
base_branch: "main"
branch: "auto/repo-agent-task"

# Docker (optional)
docker_image: "repo-agent:latest"
# dockerfile: "./Dockerfile"

# Authentication
use_ssh: false
github_token_env: "GITHUB_TOKEN"

# Strategy
strategy: "agentic"   # or "direct"

# Tool configuration — fully generic
tool:
  name: "opencode"
  entrypoint: "opencode run"
  args:
    strategy: "agentic"
    commit: false

  prompt_header_agentic: |
    You are an autonomous coding agent working on this repository.
    Plan your approach, then execute cohesive changes.

  prompt_header_direct: |
    Apply the following edits directly with minimal diffs.

# Git / PR
git_user_name: "Repo Agent"
git_user_email: "repo-agent@example.com"
auto_commit: true
create_pr: true
create_repo_if_missing: false  # Set to true to auto-create repo if it doesn't exist
commit_message: "chore: automated changes via repo-agent"
pr_title: "Automated update"
pr_body: |
  This PR was generated automatically by repo-agent.

---

# Instructions
Describe the changes you want made to the repository here.

Example:

Refactor network utilities, extract duplicate logic, and update documentation.
