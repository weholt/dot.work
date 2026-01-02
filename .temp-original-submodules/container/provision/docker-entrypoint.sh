#!/bin/bash
# Docker container entrypoint script for repo-agent.
# This script runs inside the container and handles:
# 1. Validates required environment variables
# 2. Optionally creates the GitHub repository if it doesn't exist
# 3. Clones the repository
# 4. Configures git credentials and identity
# 5. Creates/checks out the target branch
# 6. Constructs and runs the tool prompt
# 7. Commits and pushes changes if auto_commit is enabled
# 8. Creates a pull request if create_pr is enabled
#
# Environment Variables (set by Python host):
#   REPO_URL: GitHub repository URL
#   CREATE_REPO_IF_MISSING: Create repo if it doesn't exist (0/1)
#   BASE_BRANCH: Base branch to checkout from (optional)
#   TARGET_BRANCH: Target branch name (auto-generated if not set)
#   GIT_USER_NAME: Git user name (default: repo-agent)
#   GIT_USER_EMAIL: Git user email (default: repo-agent@example.com)
#   MODEL: Model to use for the tool
#   STRATEGY: Strategy to use (direct or agentic)
#   TOOL_NAME: Name of the tool (echo, opencode, etc.)
#   TOOL_ENTRYPOINT: Path to the tool executable
#   TOOL_EXTRA_ARGS: Extra arguments to pass to the tool
#   AUTO_COMMIT: Commit and push changes (0/1, default: 1)
#   COMMIT_MESSAGE: Commit message (default: chore: automated changes via repo-agent)
#   CREATE_PR: Create pull request (0/1, default: 1)
#   PR_TITLE: PR title (default: Automated changes via repo-agent)
#   PR_BODY: PR body (default: This PR was generated automatically by repo-agent.)
#   PROMPT_HEADER_AGENTIC: Prompt header for agentic strategy
#   PROMPT_HEADER_DIRECT: Prompt header for direct strategy
#   GITHUB_TOKEN: GitHub token for authentication
#   OPENROUTER_API_KEY: OpenRouter API key for OpenCode

set -euo pipefail

cd /workspace

if [ -z "${REPO_URL:-}" ]; then
  echo "REPO_URL is not set" >&2
  exit 1
fi

# Extract repo owner/name from URL for repo creation
if [[ "${REPO_URL}" =~ github\.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
  REPO_OWNER="${BASH_REMATCH[1]}"
  REPO_NAME="${BASH_REMATCH[2]}"
else
  echo "Could not parse GitHub repo from URL: ${REPO_URL}" >&2
  exit 1
fi

# Check if repo exists and create if needed
if [ "${CREATE_REPO_IF_MISSING:-0}" = "1" ]; then
  echo "Checking if repository exists..."
  if ! gh repo view "${REPO_OWNER}/${REPO_NAME}" >/dev/null 2>&1; then
    echo "Repository does not exist. Creating ${REPO_OWNER}/${REPO_NAME}..."
    gh repo create "${REPO_OWNER}/${REPO_NAME}" --private --confirm
    echo "Repository created successfully."
    # Wait a moment for GitHub to fully provision the repo
    sleep 2
  else
    echo "Repository already exists."
  fi
fi

echo "Cloning ${REPO_URL}..."
# Use gh repo clone which handles authentication via GH_TOKEN
gh repo clone "${REPO_OWNER}/${REPO_NAME}" repo
cd repo

# Configure git credentials using GIT_ASKPASS (no credentials written to disk)
# This is more secure than writing to ~/.git-credentials in plaintext
cat > /tmp/git-askpass.sh << 'EOF'
#!/bin/sh
echo "${GITHUB_TOKEN}"
EOF
chmod +x /tmp/git-askpass.sh
export GIT_ASKPASS=/tmp/git-askpass.sh
export GIT_TERMINAL_PROMPT=0  # Don't prompt interactively

git config user.name "${GIT_USER_NAME:-repo-agent}"
git config user.email "${GIT_USER_EMAIL:-repo-agent@example.com}"

BASE_BRANCH="${BASE_BRANCH:-}"
TARGET_BRANCH="${TARGET_BRANCH:-auto/repo-agent-$(date +%s)}"

if [ -n "${BASE_BRANCH}" ]; then
  echo "Fetching base branch ${BASE_BRANCH}..."
  if git fetch origin "${BASE_BRANCH}" 2>/dev/null; then
    git checkout -B "${TARGET_BRANCH}" "origin/${BASE_BRANCH}"
  else
    echo "Base branch ${BASE_BRANCH} not found (empty repo?). Creating new branch..."
    git checkout -b "${TARGET_BRANCH}"
  fi
else
  echo "Creating new branch ${TARGET_BRANCH} from current HEAD..."
  git checkout -B "${TARGET_BRANCH}" || git checkout -b "${TARGET_BRANCH}"
fi

if [ -z "${MODEL:-}" ]; then
  echo "MODEL is not set" >&2
  exit 1
fi

INSTRUCTIONS_BODY="$(cat /workspace/instructions_body.md)"

if [ "${STRATEGY:-agentic}" = "direct" ]; then
  PROMPT_HEADER="${PROMPT_HEADER_DIRECT}"
else
  PROMPT_HEADER="${PROMPT_HEADER_AGENTIC}"
fi

FULL_PROMPT="${PROMPT_HEADER}

${INSTRUCTIONS_BODY}"

printf "%s" "${FULL_PROMPT}" > /workspace/full_prompt.txt

TOOL_ENTRYPOINT="${TOOL_ENTRYPOINT:-}"
if [ -z "${TOOL_ENTRYPOINT}" ]; then
  echo "TOOL_ENTRYPOINT not set. Check frontmatter 'tool.entrypoint'." >&2
  exit 1
fi

TOOL_EXTRA_ARGS="${TOOL_EXTRA_ARGS:-}"

echo "Running tool: ${TOOL_ENTRYPOINT}"
echo "Strategy: ${STRATEGY}, Model: ${MODEL}"

# Setup OpenCode authentication and config if needed
if [[ "${TOOL_NAME}" == "opencode" ]] && [ -n "${OPENROUTER_API_KEY:-}" ]; then
  echo "Setting up OpenCode authentication..."
  mkdir -p ~/.local/share/opencode
  cat > ~/.local/share/opencode/auth.json << EOF
{
  "openrouter": {
    "type": "api",
    "key": "${OPENROUTER_API_KEY}"
  }
}
EOF
  # Copy opencode.json to current directory if it exists in /workspace
  if [ -f /workspace/opencode.json ]; then
    cp /workspace/opencode.json opencode.json
    echo "OpenCode config copied to repo directory."
  fi
  echo "OpenCode auth configured."
fi

# For testing: just echo the prompt to verify workflow
if [[ "${TOOL_NAME}" == "echo" ]]; then
  echo "=== PROMPT ==="
  cat /workspace/full_prompt.txt
  echo "=== END PROMPT ==="
  # Create a test file to verify file operations work
  echo "# Hello World" > README.md
  echo "" >> README.md
  echo "Welcome to test-haiku! This is a test repository." >> README.md
elif [[ "${TOOL_NAME}" == "opencode" ]]; then
  # OpenCode requires provider prefix in model name (e.g., openrouter/anthropic/claude-3.5-haiku)
  # If model doesn't start with openrouter/, prepend it
  if [[ "${MODEL}" != openrouter/* ]]; then
    OPENCODE_MODEL="openrouter/${MODEL}"
  else
    OPENCODE_MODEL="${MODEL}"
  fi
  ${TOOL_ENTRYPOINT} --model "${OPENCODE_MODEL}" "${FULL_PROMPT}"
else
  ${TOOL_ENTRYPOINT} --model "${MODEL}" --input /workspace/full_prompt.txt ${TOOL_EXTRA_ARGS}
fi

if [ "${AUTO_COMMIT:-1}" != "1" ]; then
  echo "AUTO_COMMIT=0, skipping commit and PR."
  exit 0
fi

# Check if there are any changes (staged, unstaged, or untracked)
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  echo "No changes detected after tool run, skipping commit and PR."
  exit 0
fi

echo "Committing and pushing changes..."
git add .
git commit -m "${COMMIT_MESSAGE:-chore: automated changes via repo-agent}"

git push origin "${TARGET_BRANCH}"

if [ "${CREATE_PR:-1}" != "1" ]; then
  echo "CREATE_PR=0, skipping PR creation."
  exit 0
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found in container, cannot create PR." >&2
  exit 0
fi

echo "Creating pull request via gh..."
if [ -n "${BASE_BRANCH}" ]; then
  gh pr create \
    --head "${TARGET_BRANCH}" \
    --base "${BASE_BRANCH}" \
    --title "${PR_TITLE:-Automated changes via repo-agent}" \
    --body "${PR_BODY:-This PR was generated automatically by repo-agent.}"
else
  gh pr create \
    --head "${TARGET_BRANCH}" \
    --title "${PR_TITLE:-Automated changes via repo-agent}" \
    --body "${PR_BODY:-This PR was generated automatically by repo-agent.}"
fi
